# CWE-bench pipeline — performance & throughput optimization

Status: 2026-10-19 (after the GCP in-place resize to 64 CPU / 251 GB / 5 TB).

## 1. The problem: spiky workload + docker-compose failures under concurrency

- A **build** = a model-driven agent that authors a task **and** builds its Docker image **and** runs
  the **gate** to verify it, iterating. The gate is the cost center.
- A **gate pass** validates the task against ~15 *different code states* — nop (vuln, 1 container),
  oracle (reference fix, ×3), patches (each wrong-fix/hardening/alt, N=9–15) — each a clean
  container + full test suite (+ a recompile per patch for Go/Java/Rust). So **one gate pass =
  ~13–19 container runs**, fired back-to-back, and re-run on each authoring iteration.
- Across many concurrent builds, these bursts overlap → load oscillates hard (measured: 1.9 when all
  agents are *reasoning*, 48 when several hit *gate*, 160 on the old 32-CPU box at ~40 builds).
- Above a threshold, `docker compose` commands start **failing**, producing false "unsound" gate
  verdicts we then have to detect and recover.

## 2. Root cause of the compose failures (debugged 2026-10-19, not guessed)

From `journalctl -u docker` and daemon/limits inspection:
- **It is NOT fd exhaustion** — dockerd's fd limit is 524288 (ample). (The `ulimit -n 1024` seen is
  only the interactive shell's soft limit; worth raising for the compose *CLI*, but not the daemon.)
- **Primary cause: dockerd overload under concurrency.** Repeated
  `Container failed to exit within 10s of kill — context deadline exceeded`: when too many container
  start/stop/compose ops fire at once, the daemon can't service them within its timeouts, so the
  `docker compose` command aborts → the gate check is recorded as failed/None.
- **Secondary cause: network-removal race.** `could not remove local network ... has active endpoints
  (…harbor-docker-egress-control-sidecar-1)`: compose tears down the network while the netguard
  sidecar still holds an endpoint → compose-down error + leftover networks.
- Earlier, separately fixed: Docker **network-address-pool exhaustion** → extended pool to
  `172.16.0.0/12 size 24` (4096 networks) in `daemon.json`. (Currently only ~8 in use, so not the
  current bottleneck.)

**Conclusion:** bounding concurrent compose ops is the *actual* fix for the daemon overload (not mere
avoidance); plus targeted config fixes let us raise the ceiling instead of staying conservative.

## 3. The fix: a global, resource-weighted container scheduler (semaphore)

Replace "cap the number of builds and hope gates don't collide" with **bound the heavy ops globally**:

- A **counting semaphore** (dependency-free, `flock` over N slot-files) that **every** gate/trial
  container launch must acquire before `docker compose up` and release when that check finishes.
- **Partial admission** (per Mara): a 15-check gate does NOT block as a unit — each container acquires
  a slot independently, so if there's headroom for 5, 5 run and the other 10 queue and start as slots
  free. The box runs at a **flat ~N**, maximally utilized, never spiking past N.
- **Resource-weighted, not a flat container count** (per Mara): we know each task's footprint upfront
  (the prebuilt base image size + its language). So a slot costs **weight by expected resource use**,
  not 1-per-container:
  - compiled-language gate check (Go/Java/Rust — recompiles per patch) = heavy weight;
  - interpreted (Python/JS — just runs tests) = light weight;
  - refine weights with measured per-task gate CPU/RSS/time (we have image sizes + can record run
    stats). Admission rule: start new containers while `sum(weights in flight) <= CAP`.
- **CAP is a tuned knob**, not hardcoded. Start conservative (~20–24 compose ops in flight on 64
  cores — the daemon-overload threshold), watch load + the `context deadline exceeded` rate, and
  raise. (Not 90 up front — that re-triggers the daemon overload above.)
- This **subsumes staggered starts**: if every container launch is semaphore-gated, build bursts
  self-throttle; no separate stagger needed.

## 4. Supporting fixes (so we can raise CAP and exploit the 64-core box)

- **Raise dockerd operation/kill timeouts** so a busy daemon doesn't abort ops prematurely
  (the `context deadline exceeded` → compose-fail path). Needs a daemon restart → do when idle.
- **Fix the network-removal race**: ensure the netguard sidecar is down before the network is removed
  (compose-down ordering), or retry network removal with backoff. Removes the leftover-network churn.
- **Prune stale trial/gate containers** (283 kept) and the per-run `__hash` images: less daemon state
  to manage. With `keep_containers=true` we keep every non-solve; switch to prune-after-grading.
- **Raise the shell `ulimit -n`** (1024 → 1048576) for the compose CLI subprocesses, cheap safety.

## 5. Image / build efficiency (separate win)

- The heavy deps/toolchain/repo are **already built once** into a per-task prebuilt base
  (`*-env-prebuilt`, `*-dev:base`); tests are **copied in at grade time** (not baked); the solver
  edits `/app` at runtime. So we do **not** rebuild the heavy image per code edit for trials.
- Remaining win: **don't create a per-trial image at all** — `docker run` the cached base and
  **bind-mount** the solver's working copy + `/tests` at container start. Kills the ~172 throwaway
  `__hash-env-main` images + their disk, and shaves per-run startup. (Heavy base builds are
  one-per-task and unavoidable.)

## 6. Rollout

1. Build the `flock` semaphore + `with_slot` wrapper; wire into `builder/gate.py` (per-check compose)
   and `harness/run_trial.sh` (trial launch). Weighted admission by image-size/language.
2. Daemon fixes (timeouts, ulimit, network-race) — apply at the next idle window (needs docker
   restart; would kill running builds otherwise).
3. Prune stale containers/images.
4. Validate on a small batch (N low), then make it the default for the MiMo lane + leakage re-check +
   hardening (the big run goes through the scheduler from the start — flat load, no compose
   corruption), raising CAP while stability holds.

Targets to measure: per-build wall time, per-gate-pass time, sustained load at CAP, compose-failure
rate (should go to ~0), max stable concurrent tasks.

## 7. REVISED CONCLUSION (2026-10-19, after debugging the actual failures)

Evidence from the trial/daemon logs — the failures under load are **deadline/timeout misses, not
CPU-cap breakage**:
- trials: 14× `hit-agent-timeout`, `AgentTimeoutError` ×4, `EnvironmentStartTimeoutError` ×1,
  `UnknownApiError` ×3, `NonZeroAgentExitCodeError` ×6
- daemon: repeated `context deadline exceeded` killing/starting containers; network-removal races

This confirms: **CPU oversubscription alone does not corrupt anything** — the kernel time-slices and
tasks just run slower. What fails is **time-bounded operations that miss their deadline when the
system is slow**, and then get killed (→ "cancellation/contamination"). So throttling CPU to ~40%
just to avoid spikes is the wrong trade; it wastes the box.

**Builds vs trials — the key distinction:**
- **Builds** have no hard wall-clock deadline (only a 3h safety) → oversubscribe freely; a build just
  takes longer. CPU over 100% is fine.
- **Trials** have a **wall-clock agent timeout** that *defines the task*. Under CPU starvation the
  model's wall-clock inflates → false timeouts/cancellations. So trials are the one thing
  oversubscription genuinely corrupts (this is why 24 builds + 24 trials produced cancellations).

**Revised fix (supersedes the elaborate resource scheduler in §3 — we do NOT need it):**
1. **Raise the infra timeouts** (docker kill/op timeout, container-start, compose) so slow ≠ failed.
   This lets us run *over* CPU capacity toward ~100% utilization instead of throttling. (The daemon
   log already named it: `context deadline exceeded`.) — the "debug & fix", not avoid.
2. **Protect trials' wall-clock**: phase builds and trials, or run trials at modest concurrency / bump
   the agent timeout to absorb contention — because trial timeouts are the only real CPU-starvation
   casualty.
3. **One real hard cap — memory** (OOM kills, not slows). 251 GB is generous; a memory guard (not a
   CPU throttle) is the only limiter truly needed.
4. Keep **mount-code-into-cached-base** (§5) — removes image sprawl; unrelated to the above.
Rationale for dropping the weighted scheduler: per-task resource use is unpredictable (a
network-idle task can suddenly spike CPU), so weighting is false precision; the kernel already
schedules CPU fairly. Raised timeouts + a memory guard + build/trial phasing is simpler and actually
uses the 64 cores.
