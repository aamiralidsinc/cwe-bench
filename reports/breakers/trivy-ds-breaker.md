# trivy-ds — a task that DeepSeek V4.1 Flash and MiMo-V2.6-Pro both fail 3/3

**Status of 2026-10-20.** Sources: the task build and validation records (manifest, build notes, gate report), the pre-trial DeepSeek fairness review, and the pipeline's trial/verdict records (`build/pipeline/harden_solved.log`, `build/pipeline/AUTO-STATE.md`).

**Status note — read first.**
- **Fairness: strongest of the batch.** The pre-trial DeepSeek fairness review returned **GATE_A: READY** with **NEEDS_HUMAN_REVIEW: NO** — no correct-fix-fails mechanism found, and layered alternative fixes (including an `os.Root`-based design) all score 1.0. This is the cleanest fairness verdict in this candidate batch (protobuf.js-ds, seaweedfs-ds, summarize-ds all came back READY but NEEDS_HUMAN_REVIEW: YES).
- **Per-attempt audit NOT yet produced.** No transcript audit (`postmortem.py prepare/record`) has been run on the counted attempts, and no per-attempt audit rows exist for this task. Treat the audit dimension as provisional.
- **Per-run detail not recoverable.** The counted verdict (both models failed all 3, neither reached 1.0) is recorded in `harden_solved.log` and `AUTO-STATE.md`, but the per-run reward vectors and per-test security/functional breakdowns were **not retained** in a form found on the VM (no raw trial folders under `~/.tb-graders/cwe/jobs`, no `runs_*.log`/`auto_trial.out` under `build/trivy-ds`, and the task is not yet in the authoritative audit ledger `build/audit/trials.tsv`). §3 and §4 are therefore provisional and name the task's designed failure levers, not confirmed transcript findings.

## Summary

- **Result (per the pipeline verdict records): both target models failed all 3 counted attempts; neither reached reward 1.0.** Recorded as `[BREAKER trivy-ds 2026-10-20T16:14:46Z] both-fail 3/3 + fairness GATE_A READY, NEEDS_HUMAN_REVIEW:NO -> CLEAN both-model breaker`.
- The per-run reward vectors and the per-route pass/fail split for each attempt are **not available** on the VM; they are not yet in the audit ledger and no raw trial folders were retained. Everything numeric below the verdict line is provisional.
- The task is a real library with real gaps. It is aquasecurity/trivy at the commit before the published fix for GHSA-8RC5-4FR6-64PW. The advisory's own flaw (a plugin name that escapes the plugin directory) is combined with four further routes to the same rule — two of them injected siblings in the same code style. Nothing is planted in a way the review judged unfair.
- Why the task is hard (by design, not yet confirmed against transcripts): the same "a name must not escape the plugin directory" rule is reachable from six plugin-management operations and from four different origins of the name (packaged metadata, metadata stored on disk, a plugin-index entry, a command-line argument). A fix placed at the obvious install site leaves the far sites, the stored-name derivation and the index-cache loop open; each open route has a plausible reason to be dismissed.
- An earlier version of this same CVE (fewer routes) was solved by **both** models on the first run; adding the stored-name and index-cache routes is what turned it into a both-model failure (see §6).

## 1. The task

**Vulnerability (CWE-22, path traversal).** Trivy installs plugins into a plugin directory under its data home. A plugin ships a small metadata file that records its *name*; Trivy joins that name onto the plugin directory to decide where to create, clear, write, remove, read or execute files. At the pinned commit nothing confines that join, so a name such as `../escaped_plugin` reaches outside the plugin directory — creating a directory above it and deleting whatever was stored there. The crafted metadata is the attacker input; no unusual command-line option is needed.

**Base advisory:** GHSA-8RC5-4FR6-64PW / CVE-2026-63328 / GO-2026-6250. Vulnerable commit `246ee3ca`, upstream fix `d4213d77`. Track: **INJECTED** (two of the five routes are injected siblings of the same class; the rest are real unmodified pinned/published-fix code).

**Entry point.** The hidden tests drive the real `pkg/plugin.Manager` methods — `NewManager().Install / Uninstall / Information / Start / Repair / Update` — with `XDG_DATA_HOME` pointed at a temp directory and, for the index route, `WithIndexURL` pointed at a local `file://` index mirror. Nothing is stubbed. The attacker-controlled name arrives in packaged metadata, in metadata stored on disk from an earlier install, in a plugin-index entry, or as a command-line argument.

**Five real routes to the same rule** (none named in the instruction; no file, function or count is given):

| Route (trap id) | What leaks | Why a solver might dismiss it |
|---|---|---|
| 1. `base_install` — packaged-metadata name joined onto the plugin directory as the install destination (the report's example) | the destination is cleared and the plugin + its metadata are written outside the directory | none; it is the obvious write sink |
| 2. `symlink_install` — a plain relative name (`link/sub`) whose parent inside the plugin directory is an existing symlink pointing outside | the joined destination resolves and is written outside | the link lives in the user's own plugin directory, so it reads as local tampering, not attacker input; a lexical `filepath.IsLocal` check passes the name |
| 3. `far_cli_name` — `Uninstall` and `Information` join a command-line name onto the plugin directory to remove / read | a `..`-bearing or bare `..` argument removes or reads outside | the command-line argument is the local user's own input, so it reads as trusted |
| 4. `stored_name_dir` — `loadMetadata` derives a plugin's directory from the *stored* name; `Start` execs `Platform.Bin` from it and the injected `Repair` rewrites metadata through it | a hostile stored name makes a later `Start` execute, and `Repair` write, outside the directory | the stored metadata was written by Trivy itself at install time, so its recorded name reads as trusted; a fix on the install argument alone misses it |
| 5. `sibling_index_cache` (injected) — `Update` joins a plugin-index entry's name onto the plugin directory to write a per-plugin index cache, read back by `tryIndex` | a hostile entry name in a mirrored index creates a directory outside | the index is a curated feed and the operation only primes a cache; a guard on command-line names never sees a name that arrives only in index data |

**Report given to the agent** (`tasks/trivy-ds/instruction.md`). It is written as a real bug report: the system, one worked example (the `../escaped_plugin` install), then the rule — *no plugin name, however Trivy obtained it and whichever management operation uses it, may cause a file or directory outside the plugin directory to be created, written, removed, read or executed* — plus the contracts that an escaping name is refused or treated as absent (error or no-op, both acceptable) and that in-directory names keep working exactly as today, "including the files each management operation writes inside it and the programs it starts from there." Routes 2–5 are not named, and neither is any file, function or count. The instruction closes: "The command, the name and the values above are examples, not a complete list of the ways the problem can be reached."

**Hidden tests.** 10 security tests and 9 task functional tests, plus a deterministic subset of the project's own `pkg/plugin` suite (`Uninstall`, `Information`, `LoadAll`, `Run`). They drive the public `Manager` API and assert behaviour: that the outside sentinel survives / nothing is written-or-read outside, while a clean refusal (error or no-op) is accepted. Reward = the security pass fraction, or 0 if any functional test fails. 1.0 = solve.

## 2. How we know the task is fair

Before any model ran, the build gate and the DeepSeek fairness review both passed (`build/trivy-ds/notes.md`, `build/trivy-ds/FAIRNESS.md`):

| Check | Result |
|---|---|
| Vulnerable code (pinned + injected) | fails all 10 security tests; passes all functional tests (9 task + project subset) |
| Oracle (reference fix) | 1.0, three runs, identical results |
| Alternative correct fix (`alt_fix.patch`, an `os.Root`-based containment design, different from the reference) | 1.0 |
| Hardening fix (`hardening.patch`) | 1.0 |
| A fix that leaves each route out in turn | fails the matching security tests: `sec_miss_install` 0.6 (4 install tests), `sec_miss_symlink` 0.9 (link only), `sec_miss_cli` 0.7 (uninstall/info/bare-parent), `sec_miss_stored_dir` 0.8 (exec + repair), `sec_miss_index` 0.9 (index only) |
| A guard-reads-only fix (`reads_only.patch`) | 0.2 — the write-path tests fail, as designed |
| A prefix-only / lexical-only guard (`prefix_guard`, `weak_guard`) | fail the prefix-sibling and symlink/bare-parent tests |
| An over-broad fix that validates the install *source* or refuses everything (`func_overbroad`, `refuse_all`) | 0.0 — breaks legitimate install / uninstall, as designed |

All 12 check patches behaved exactly as declared; the project's own `pkg/plugin` suite (including `TestManager_Install` and `TestManager_Upgrade`) builds and passes on both the vulnerable tree and the oracle.

**The fairness review's own verdict (`FAIRNESS.md`).** Every one of the 23 graded tests is rated **low risk**: each is covered by the rule read literally ("however Trivy obtained it", "whichever plugin management operation uses it"), and no test can fail a correct fix. Security tests discard the returned error and assert only the outside effect, so every refusal form the instruction allows — error, nil, or silently doing nothing — passes, and a guard placed at any valid layer before the sink passes. Functional tests restate explicit legitimate use (path/URL sources keep working, a single-top-level wrapper is unwrapped, uninstalling a missing plugin returns nil, Update still stores an unparsable index) or behaviour visible in the repo. The review found **no correct-fix-fails mechanism**:

> **GATE_A: READY** / **NEEDS_HUMAN_REVIEW: NO**

The leniency section lists wrong fixes that *no* test catches (gate-B quality items, not fairness blockers) — e.g. symlink resolution applied only at install, or basename-sanitizing instead of refusing — and recommends extra hardening tests. None of these can make a *correct* fix fail; they only mean a *wrong* fix could occasionally score higher than it should.

**One fairness wording fix is required and not yet applied.** The review's "Required: generalize" item asks that instruction line L12 drop the clause *"including one that goes through a link that already exists inside the plugin directory"* — it exists only to point at the symlink trap (route 2) — and keep the general sentence "A name that leaves the plugin directory only after its path is interpreted is covered as well" (which still covers `TestSec_InstallSymlinkEscape`). As of this writing the instruction still carries the link clause, so this neutral-wording change should be made before the task is shipped. It removes a hint; it does not change what is tested.

## 3. Results, attempt by attempt (provisional — per-run detail not recoverable)

The pipeline recorded the counted trial as a **sound both-fail, 3 attempts per model, neither model reaching 1.0** (`AUTO-STATE.md` tick16: "summarize-ds + trivy-ds: sound both-fail -> fairness launched"; `harden_solved.log`: "both-fail 3/3"). That verdict is the authoritative result.

The per-attempt reward vector, the run durations, and the per-route security/functional split for each attempt were **not retained in any location found on the VM**: there are no `trivy-ds` trial folders under `~/.tb-graders/cwe/jobs`, no `runs_deepseek.log` / `runs_mimo.log` / `auto_trial.out` under `build/trivy-ds`, no `[trial-done trivy-ds …]` line in `build/pipeline/auto_trial.log`, and the task does not yet appear in the authoritative audit ledger `build/audit/trials.tsv` (which currently holds only the solved predecessor `trivy-path-traversal-inj`). So the per-attempt table that the jackson report carries cannot be reproduced here. It should be regenerated from the raw trial folders — or the trial re-run under the audit pipeline — before any per-run number is quoted.

## 4. Why both models fail (provisional — from the task design, not from a transcript audit)

No transcript audit has been recorded for this task, so the account below is the task's intended failure mechanism (from the manifest and build notes), not a confirmed reading of what the models did.

The task puts one rule — a plugin name must not escape the plugin directory — behind six operations and four origins of the name. The designed levers are:

- **The far command-line sites (route 3).** A fix naturally lands on the install path the report demonstrates; `Uninstall` and `Information` join the same kind of name onto the directory and are easy to leave on the plain join, because a command-line argument reads as the user's own trusted input.
- **The stored-name derivation (route 4).** `loadMetadata` derives the plugin's directory from the *stored* name, so a fix that only validates the install *argument* leaves `Start` (which execs from that directory) and the injected `Repair` (which writes through it) open. The correct fix derives the directory from where the metadata was read, not from the recorded name.
- **The index-cache loop (route 5, injected).** `Update` writes a per-plugin cache using the entry name taken from the downloaded index; a guard on command-line or metadata names never sees a name that only arrives in index data.
- **Resolution vs. lexical checks (route 2).** A lexical `filepath.IsLocal` check passes `link/sub`, whose parent is an existing symlink out of the directory; only a resolving containment check refuses it.
- **Coupled legitimate behaviour.** Over-broad fixes are penalised: validating the install *source* (a path/URL that legitimately contains `/`) breaks `TestFunc_InstallLocal`/`Nested`, and refusing any name with `/` breaks in-directory multi-component names — both score 0 because any functional failure zeroes the reward.

Whether the two models actually fell into these specific levers (and in what mix) is exactly what the per-attempt audit would establish; it has not been run.

## 5. Evaluation setup

- Harness: Harbor with the Claude Code agent.
- Models: DeepSeek V4.1 Flash and MiMo-V2.6-Pro; up to 3 counted attempts each, early-exit on a solve.
- Offline: the agent could reach only the model APIs; web tools were disabled, the repository has no git history, and the hidden tests are copied in only after the agent stops.
- Scoring: reward = the security pass fraction, 0 if any functional test fails; 1.0 is a solve.
- What counts: a 3-hour timeout counts as a FAIL; an attempt cut by a provider or network outage is not counted.
- Toolchain note: the repo imports `encoding/json/v2`, so the environment pins `go1.26.3` with `GOEXPERIMENT=jsonv2`; `NewManager` keeps its upstream signature so the project's own `pkg/plugin` tests compile and pass unchanged.
- **Audit status: prepared, not recorded.** The per-attempt transcript audit (the step the jackson report relies on) has not been produced for this task, and the task is not yet in the audit ledger.

## 6. Where this sits among our tasks

- It is a **clean both-model breaker** by the pipeline verdict, and the **cleanest fairness result in its batch**: GATE_A READY with NEEDS_HUMAN_REVIEW: NO, where the batch's other READY candidates (protobuf.js-ds, seaweedfs-ds, summarize-ds) were all flagged for human review.
- An **earlier version of the same CVE**, `trivy-path-traversal-inj` (the advisory route plus a prefetch sibling, fewer routes), was solved by **both** models on the first run (DeepSeek 1.0, MiMo 1.0 on 2026-10-18 — confirmed in `build/audit/trials.tsv`). Adding the stored-name derivation and the injected index-cache route, each with a coupled legitimate behaviour, is what turned it into a both-model failure. This mirrors the jackson-databind pattern: a v1 that one or both models solve, hardened by adding real routes to the same rule until both fail.
- Recipe confirmed again: one confinement rule, reachable from several operations and several origins of the tainted value, with at least one route the obvious fix does not reach and a legitimate value coupled to each guarded one.

## 7. Questions you may ask

**Is the failure the task's fault?** The fairness review found no correct-fix-fails mechanism and rated every graded test low risk; the oracle, an `os.Root`-based alternative fix, and a hardening fix all score 1.0, while five route-specific wrong-fix patches fail exactly the routes they skip. GATE_A: READY, NEEDS_HUMAN_REVIEW: NO.

**Can you show the per-attempt scores?** Not from the current records. The counted verdict (both models failed all 3, neither 1.0) is recorded in the pipeline logs, but the per-run reward vectors and per-route breakdown were not retained on the VM and the task is not yet in the audit ledger. They must be regenerated from raw trial folders, or the trial re-run under the audit pipeline, before any per-run number is cited. This is the main open item.

**Could the model have seen the answer?** The agent could not reach the internet, the git history, or the hidden tests, and the instruction bars looking up the advisory or fix. The stored-name and index-cache routes are injected siblings that are not in the published fix at all.

**What is still owed before this is a fully confirmed breaker on par with jackson?** (1) Apply the L12 wording generalization from §2. (2) Regenerate or re-run the counted trial under the audit pipeline so the per-attempt reward vectors land in `build/audit/trials.tsv`. (3) Run the per-attempt transcript audit (`postmortem.py prepare/record`) to confirm which routes each model left open. Until then the fairness is the strongest in the batch, but the results and failure-analysis dimensions are provisional.

## Appendix: what is in the task package

| What | Contents |
|---|---|
| Task | report (`tasks/trivy-ds/instruction.md`), environment (with `inject.patch` adding the Repair op and the index cache), reference fix, hidden tests (10 security + 9 functional + project subset) |
| Validation | gate report / build notes (`build/trivy-ds/notes.md`), the 12 check patches (`build/trivy-ds/checks/*.patch`), the DeepSeek fairness review (`build/trivy-ds/FAIRNESS.md`) |
| Manifest | routes, sites, traps and leak-terms (`build/trivy-ds/manifest.json`) |
| Attempts | counted verdict recorded in `build/pipeline/harden_solved.log` and `build/pipeline/AUTO-STATE.md`; per-attempt reward vectors, per-test breakdown and transcript audit **not yet produced** |
