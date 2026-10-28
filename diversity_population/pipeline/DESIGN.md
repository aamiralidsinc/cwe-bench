# divq: the diversity experiment's pipeline on GitHub Actions

**Status:** design and first implementation, 2026-10-28. Nothing has been dispatched.

**Scope:** builds and trials of the diversity batch (264 tasks, 4 chunks) on GitHub-hosted runners, because the VM is
busy with the scale run.

**Not a merge.** The main pipeline's queue (`common/queue/`, `docs/WORK-QUEUE.md`, `docs/ARCHITECTURE-ROADMAP.md`)
is not touched or imported. divq re-implements the features listed below for a different executor: GitHub Actions
instead of local workers. It runs the main pipeline's own stage scripts, from a copy, on the runners.

**Internal only.** Never copied to the client repo.

## 1. The features, and how each maps to Actions

| Main pipeline feature | What it means there | divq on Actions |
|---|---|---|
| **One work queue** | SQLite job table; `(kind, task, args)` unique; states queued → leased → running → done/failed/blocked; attempts; a reconciler derives jobs from files on disk, so a deleted DB rebuilds the same jobs; never redo finished work | The same table and states. A job's "lease" is its GitHub run id. A job is `done` only when its artifact is fetched, decrypted and passes its checks. The reconciler reads `out/results/` (the decrypted artifacts), so a deleted DB re-plans only what is missing. |
| **Track record** | every job records its exit, log, code version and settings version; events; `explain` | every job records account, run id, release, settings hash, timings, result and check outcome; an events table; `divq explain TASK`; `divq report` writes the track record (Markdown and TSV) |
| **Zero-downtime updates (versioned releases)** | read-only release per commit; running work finishes on its release; rollback repoints a link | a release is an encrypted payload built from one cwe-bench commit plus the prepared prompts; its id is the payload's content hash. A run checks out the repo at dispatch time, so pushing a new release never touches a running job. New jobs use `current`; a retry keeps the release its job first ran on. Rollback repoints `current`. |
| **Dynamic concurrency** | the total job limit follows sustained CPU idle (`autolimit`) | the scarce resource is runner slots per account (precision_validation saw about 7, not the configured 20). The limit is per account and learned: down to the running count when a run waits more than `queued_wait_min` for a runner; up by one after `raise_window_min` with no waiting and work queued; a cooldown after each change, each change logged. Also disk-aware: no dispatch while the machine that receives the artifacts is below its disk floor. |
| **Settings history** | settings file in git; each loaded version recorded; each job records its version | `pipeline/settings.toml`; every loaded version recorded (hash, text); every job records the hash it was dispatched under |
| **Multi-pass candidate ranking** | 3 DeepSeek passes combined | already used: `select_per_pattern.py`, `topup_replace.py` (3 passes plus the rerank) |
| **Reliable grading** | containers report their real CPU count to node tools; regrades use the original network setting; a functional test that passed originally but fails on regrade raises an event | (1) runs use the current builder, whose agent layer caps node's CPU count. (2) **Runner fit:** a task whose `task.toml` asks for more CPU or memory than a standard runner has (4 CPUs, 16 GB) is not dispatched; it becomes an event (a hosted 4-CPU runner would under-provision a cpus=8 task). (3) Trials run `common/trial/trial.py`, the VM's own runner: the same network policy (model API only, no web tools), the same infra-versus-fail rules and the same job-folder format. (4) Post-condition checks per job; the functional-drop check from `common/queue/checks.py` is reused when a run is regraded. |
| **Preflight** | read-only setup checks before launch | `divq preflight`: per enabled account, the token works, the repo exists, the workflows are registered, and the three secrets are present (names only, never values); the payload key exists locally; local disk is above its floor; the release is built. The workflows also check their own secrets and fail in the first minute instead of grading 0.0. |
| **Events and decisions inbox** | events worked in order; one page of owner decisions | `events` table; `divq inbox` lists what waits on the owner: account approval, old repo cleanup, blocked jobs, tasks too big for a runner, breaker candidates |

## 2. precision_validation issues: fixed here, or still open

| # | Issue (`actions/README.md` §6) | State in divq |
|---|---|---|
| 1 | Only about 7 jobs per account got runners | **fixed:** learned per-account limit (§1) |
| 2 | A workflow never registered on one account | **fixed:** preflight checks `gh workflow view` per repo before any dispatch |
| 3 | Whole-run downloads died on big artifacts | **fixed:** per-artifact download with retries, smallest first; a job is done only after its artifact decrypts |
| 4 | `UnknownApiError` from the task's no-network agent phase | **fixed:** `trial.py` passes `--allow-agent-host` as on the VM |
| 5 | A missing `MIMO_API_KEY` produced fake fails | **fixed twice:** preflight checks secret names per repo; the workflow's first step fails the job if a secret is empty |
| 6 | The `SUMMARY` line was only on the console | **fixed:** the workflow writes `divq-result.json` into the encrypted artifact and prints one `DIVQ-RESULT` line; divq reads the file |
| 7 | The infra detector discarded clean runs (text grepping) | **fixed:** no grepping. `trial.py` decides infra (as on the VM), and divq reads the graded run folders (`result.json`, `verifier/reward.json`) |
| 8 | Phantom blind patch broke the gate | **fixed:** the payload carries the current gate (blind-skip) |
| 9 | Safety classifier blocked `git push` and secret writes | **open, handled by design:** `divq repo sync` prints the exact commands; the owner runs them if the agent is blocked |
| 10 | No agent transcript or final code in the artifact | **fixed:** the artifact carries the trial job folders (agent logs, trajectory) and the graded `/workspace` copy that `trial.py` keeps, size-capped |
| — | 7-day artifact retention | **fixed:** a job's artifact is fetched as soon as its run completes; `artifact.expiring` event at day 5 if not |
| — | VM-only settings on a runner (disk floors 150/250 GB, Harbor patches, `$HOME/.local/bin/claude`) | **fixed:** the workflow sets runner-sized disk floors, applies Harbor patches A and B to the installed copy, and installs Claude Code to the path the scripts call |
| — | A 5 h builder limit inside a 6 h job | **fixed:** `BUILD_TIMEOUT` = 4 h on runners, leaving the gate about 1.5 h |
| — | Slug and path visible in public logs | kept as before: opaque ids (`d001`…), `::add-mask::`, everything else encrypted |
| — | Accounts | **settled (owner, 2026-10-28):** two accounts the owner already holds — one company, one personal. Not a fan-out across many accounts, and no new accounts. Each is a normal separation of the owner's own work. Each is still `enabled = false` in `settings.toml` until the owner flips it, so dispatch is a deliberate step, not an accident. **No fake commit identity:** commits are the owner's, under each account's own GitHub no-reply address. |
| — | 10 old public repos still hold payloads and secrets | **open: owner action** (web UI); listed in the inbox |

## 3. Job kinds

| Kind | Task | Args | Runs on the runner | Done when |
|---|---|---|---|---|
| `build` | `diversity-<repo>` | `{}` | `pipelines/sibling/6-build/run_pipeline.sh deepseek <slug>` (build, then gate and blind fix in `postbuild.sh`) | artifact fetched; exactly one of `.sound` / `.unsound` / `.gate_error`, or a recorded BUILD-INCOMPLETE |
| `trial_run` | same | `{"model": m, "run": n, "fp": <gate fingerprint>}` | `common/trial/trial.py <slug> --models m --first-run n --max-runs 1 --no-verdict` | artifact fetched; the run folder has `result.json`, plus `verifier/reward.json` or a recorded infra reason |

**Trial policy** (owner rules: per-model verdicts; both models on every sound task):
- run 1 of each model starts as soon as the task is SOUND;
- a model that solves (reward 1.0) is done;
- after a failed run 1, runs 2 and 3 start together;
- 3 graded fails = model FAIL;
- both models FAIL = breaker candidate (event); fairness review and audit follow on the VM, as for every breaker.

One run per job keeps each job inside GitHub's 6 h limit.

**Priority:** chunk order first, then the candidate's score order inside the chunk, plus aging.

## 4. Layout

```
diversity_population/pipeline/
  DESIGN.md          this file
  settings.toml      accounts (all disabled), limits, adaptive concurrency, priorities, floors
  divq.py            CLI
  divq_core.py       DB, settings history, releases, reconciler, dispatcher, adaptive limits, events
  divq_gh.py         the GitHub executor (gh CLI with a per-account token read from .env)
  workflows/         build.yml, trial.yml (our versions of the reference workflows, with the fixes above)
  tests/             unit tests with a fake executor
diversity_population/out/
  divq.db            the queue (rebuildable from out/results/)
  releases/<id>/     staged root + RELEASE.json; <id>.tar.gz.gpg is what goes to the repos
  results/<slug>/    decrypted artifacts: build/, trials/<model>/run<n>/
```

The control plane runs anywhere that has `gh`, `gpg` and the tokens. The same code runs on the Mac or in
`~/diversity_population` on the VM. Its load is light: polling every 60 s, plus artifact downloads.

## Operate

Run with Python 3.11+ (`~/.venvs/kaggle/bin/python3.12` on the Mac, `python3` on the VM). The control plane is
light (poll + downloads); it can run on the Mac or in `~/diversity_population` on the VM. **The artifacts download
to wherever the control plane runs**, so prefer the VM (1.7 TB) over the Mac (tight on disk); `local_disk_floor_gb`
guards it either way.

**Go sequence (each step is the owner's, not automatic):**
1. Delete the 10 old precision_validation repos (web UI) and rotate the DeepSeek + MiMo keys.
2. Create the payload key: `openssl rand -base64 48 > ~/.tb-graders/cwe/diversity/payload.key; chmod 600 …`.
3. `divq release build <cwe-bench commit>` then `divq release activate <id>`.
4. In `settings.toml`, flip `enabled = true` for the accounts to use (company, personal).
5. `divq repo sync` prints the per-account commands (create the public repo, push the two workflows + the payload,
   set the three secrets). The owner runs them, since the safety classifier blocks the agent from pushing / writing
   secrets.
6. `divq preflight` — must be clean (exit 0).
7. `divq run` (reconcile → adapt limits → dispatch → poll, every `tick_sec`). Watch `divq status`, `divq inbox`.

**Breakers** that come back (`stage = breaker_candidate`) go to the VM for fairness + audit and the keep decision,
exactly as a VM-built breaker does; the artifact carries the transcript and graded workspace the audit needs.

## Tests

`~/.venvs/kaggle/bin/python3.12 -m pytest diversity_population/pipeline/tests -q` — 11 tests, offline, with a fake
GitHub executor: idempotent reconcile, enabled-chunk gating, rebuild-from-disk after the DB is deleted, per-account
dispatch limit, the dispatch gate, build completion → trials queued, the breaker / solved / too-big stages, fetch
failure → retry → blocked, and the adaptive limit lowering then raising.
