# Versioned releases

Tool: `common/util/release.py`. Tests: `python3 -m pytest common/util/tests/test_release.py`.

A release is a read-only copy of one commit's code. A `current` link names the active release. Rollback means
pointing `current` back at the previous release.

## Layout

```
~/cwe-bench-releases/
  <sha12>/            one commit's code, read-only, byte-compiled
    RELEASE.json      commit, commit date, subject, build time, data root, data links
    .cwe-bench-root   the repo-root marker (code root = this folder)
    .cwe-data-root    the data root (read by common/paths.py and common/paths.sh)
    build -> ~/cwe-bench/build          every folder in paths.DATA_PATHS is a link to the data root
    tasks -> ~/cwe-bench/tasks
    pipelines/router/out -> ~/cwe-bench/pipelines/router/out
    ...
  current -> <sha12>  the active release (swapped atomically)
  history.tsv         every activation: time, from, to, user, reason
~/cwe-bench/          the data root: build/, tasks/, reports/, the pipelines' out/ folders, ...
```

**Code and data split.**
- `common/paths.py` has `CODE_ROOT` (the folder the code runs from) and `DATA_ROOT`. `DATA_ROOT` comes from
  `$CWE_DATA_ROOT`, else from the release's `.cwe-data-root`, else from the code root itself.
- Data constants (`BUILD`, `TASKS`, `REPORTS`, `SIBLING_OUT`, `STACKING_OUT`, `ROUTER_OUT`, `EXPERIMENTS`,
  `CANDIDATES_DB`, `SCREENER_RECORDS`) use `DATA_ROOT`. `common/paths.sh` exports the same pair as `CWE_ROOT` /
  `CWE_CODE_ROOT` and `CWE_DATA_ROOT`.
- In a plain checkout (no `.cwe-data-root`), both roots are the checkout, so nothing changes.
- **Repo-relative paths.** Scripts that `cd "$CWE_ROOT"` and use paths such as `build/<slug>` or
  `pipelines/router/out/...` reach the shared data through the release's links.
- **Fingerprints.** The gate fingerprint hashes paths relative to `DATA_ROOT`, so a task's digest is the same from
  any release.

**Pinned code.**
- `common/paths.sh` sets `CWE_ROOT` with `pwd -P`. A script started through `current` keeps the physical release
  it started from, even if `current` is repointed while it runs.
- Python resolves its own file path, so a dispatcher started from a release spawns workers of that release until
  it is restarted.

**Jobs record their release.** `common/queue/identity.py` `code_version()` reads `RELEASE.json` (sha) first, then
`common/queue/DEPLOYED_FROM`, then `git rev-parse`. The `job_procs` row of every job and the `cwe.code_version`
container label carry it. Adoption records the same value.

## Commands

```
python3 common/util/release.py build <commit> [--repo ~/cwe-bench] [--create-missing-data]
python3 common/util/release.py verify <sha>
python3 common/util/release.py activate <sha>
python3 common/util/release.py rollback
python3 common/util/release.py list | current
python3 common/util/release.py remove <sha>     # never the current release or the rollback target
```

Options before the command:
- `--releases DIR` (default `$CWE_RELEASES` or `~/cwe-bench-releases`).
- `--data-root DIR` (default: the data root of the code running the tool).

**What each command does:**
- **`build`** runs `git archive` on the commit and leaves out every data folder. It then links each data folder to
  the data root, writes `RELEASE.json` and `.cwe-data-root`, byte-compiles the Python, makes the copy read-only and
  renames it into place.
  - A data folder the data root does not have yet stays a dangling link unless `--create-missing-data` is given.
    The sourcer index lives only on the Mac, for example.
  - `build` is idempotent.
- **`verify`** checks four things: no writable code, every link pointing at its data folder, `paths.py` and
  `paths.sh` resolving `CODE_ROOT` to the release and `DATA_ROOT` to the data root, and `.cwe-data-root` matching.

## First switch-over on the VM

The switch-over works like the queue handover: running work finishes on the code it started with, and every new
start comes from `current`.

1. **Build and check, with no effect on anything running.**
   - `git -C ~/cwe-bench fetch` (the VM checkout pulls from GitHub with its read-only deploy key).
   - `python3 common/util/release.py build <sha>`
   - `python3 common/util/release.py verify <sha>`
   - `cd ~/cwe-bench-releases/<sha> && python3 -I common/queue/cweq.py status`, read-only, against the live data.
2. **Activate:** `python3 common/util/release.py activate <sha>`. Nothing moves yet: no running process uses
   `current`.
3. **Move the queue loops.**
   - Stop `cweq.py reconcile`, `dispatch` and `monitor`.
   - Start them again from `~/cwe-bench-releases/current`, for example
     `cd ~/cwe-bench-releases/current && setsid nohup python3 -I -u common/queue/cweq.py dispatch >> ~/.tb-graders/cwe/queue-logs/dispatch.log 2>&1 < /dev/null &`.
   - Running workers, and the builds, gates and trials they started, finish on the code they started with.
   - Every new job starts from the new release: the dispatcher spawns workers from its own release path. So do the
     scripts those workers run.
4. **Move everything else that starts work.**
   - Hand-started scripts (repairs, re-gates) and the orchestrator's heartbeat commands run from
     `~/cwe-bench-releases/current` instead of `~/cwe-bench`.
   - New builder prompts carry `~/cwe-bench-releases/current` as `{{PROJECT_ROOT}}`.
   - Prompts prepared earlier carry `~/cwe-bench`, so `~/cwe-bench` keeps its code until those builds have ended.
5. **Freeze the checkout.**
   - No more file copies into `~/cwe-bench`: its code is frozen.
   - Its data stays the shared data root.
   - The DEPLOYED_FROM file is no longer needed.
6. **Verify.**
   - `cweq status` and the heartbeat work from `current`.
   - A newly started job's `job_procs.code_version` equals the release sha.
   - New containers carry `cwe.code_version=<sha>`.

**Rollback:** `python3 common/util/release.py rollback`, then restart the queue loops from `current`. To leave
releases entirely, start the loops from `~/cwe-bench` again: its code is the frozen last copy.

**Later deploys:** fetch, then `build`, `verify` and `activate`, then restart the three queue loops from
`current`.

## Risks to watch at the first switch-over

- **Writes next to code.** A release is read-only, so a script that writes next to its code fails with a
  permission error.
  - The known writers are covered: run data sits under `paths.DATA_PATHS`, `__pycache__` is precompiled, and the
    queue's `DEPLOYED_FROM` is no longer written.
  - An unknown writer fails loudly. Run one canary job of each kind (regate, regrade, trial_run, build) right
    after the loops move.
- **Stale code under `~/cwe-bench`.** Anything started with cwd `~/cwe-bench` runs the frozen checkout. That covers
  old prompts, cron entries and hand-typed commands. Step 4 moves them to `current`.
- **Paths compared across roots.** Code that resolves a data path, which lands under `~/cwe-bench`, and then
  computes it relative to `paths.ROOT` (the release) raises an error.
  - `fingerprint.py` and `router/route.py` already use `DATA_ROOT`.
  - Any new code should do the same.
