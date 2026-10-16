# CWE-Bench — Results Ledger (internal)

_Audited verdicts as of 2026-10-16 05:28 from 186 raw trials by build/audit (ledger from `python3 build/audit_results.py`). Since 2026-10-16
**every counted run has passed an independent post-run audit**: a Claude Opus 5.5 (high effort)
sub-agent judged from the instruction, tests, grading output, final code and transcript whether
the reward can be trusted (`build/postmortem.py`, procedure in `build/TRIAL-PROCEDURE.md`).
Runs without a trusted audit are not counted. Earlier audit of the raw trials:
[build/RESULTS-AUDIT.md](build/RESULTS-AUDIT.md)._

**Breaker** = pass@3 = 0 on **both** DeepSeek V4.1 Flash (max) and MiMo-V2.6-Pro. A task is
rejected as soon as either model solves it once.

**Each model also gets its own verdict.** The two models fail on different things, so a
solve by one says nothing about the other. Per model:
- **SOLVED** = at least one graded run at 1.0 whose audit says trustworthy.
- **failed** = 3 graded runs, none at 1.0, each audited as a trustworthy model failure.
- **open** = not decided yet (fewer than 3 audited failures, or a solve still awaiting audit).

**What counts as a graded run:**
- **Counted:** graded runs with a trusted post-run audit, including runs cut by the time limit
  and graded on the code as it stood (as CWE-bench does).
- **Not counted:**
  - runs that were never graded;
  - runs that used hidden tests leaked into the image (`build/audit/contaminated.tsv`);
  - runs whose grading broke on our side (`build/audit/reviews.tsv`);
  - runs that failed a test later found faulty and cannot be regraded, or ended on a provider
    stop (`build/audit/excluded_runs.tsv`);
  - runs whose audit says untrusted.
- **Time limit:** 120 min since 2026-10-15. A non-solving run cut at the old 60-min limit is
  not counted.

## Executive summary

**Trial setting changed on 2026-10-16 to match CWE-bench: agents run OFFLINE**, with only the model
provider's API reachable. The CWE-bench paper (arXiv 2610.17020) says "Each attempt runs in an
isolated container whose only network access is the model provider's API". Enforcement is Harbor's
`[agent] network_mode = "allowlist"` with only `api.deepseek.com` and `api.xiaomimimo.com`, verified
by `harness/offline-check`.

**Effect on earlier runs:**
- All earlier runs had open internet, and agents often fetched the upstream fix.
- An earlier **solve counts only if the run did no internet lookup** (`build/internet_use.py`).
- An earlier **failure still counts**, since it had more access than CWE-bench allows.
- **Time limit:** stays 2 h. A non-solve that hits a limit under 3 h is not a failure; it is
  re-run with 3 h.

**Current audited state: 0 breakers.** 36 pairs SOLVED, 1 failed, 1 open.

| Track | Task | DeepSeek | MiMo | Who failed | How it failed |
|---|---|---|---|---|---|
| injection | jackson-databind-sib | **failed 0/6** (0.625, 0.625, 0, 0, 0, 0.625) | SOLVED 1/2 | DeepSeek | Missed the injected any-setter siblings in all 6 runs: it saw the path within a minute and dismissed it as out of scope; 3 runs also over-blocked a linked property. Each run audited trustworthy (high confidence); none used the internet. |

**Open pairs:** asyncssh / DeepSeek. Its only offline solve failed a test added in the
2026-10-16 repair (zero packet size advertised with a dropbear banner; an independent fairness
review judged it FAIR). Fresh offline runs wait for the user's go-ahead.

**Test repair (2026-10-16, all 16 tasks done, every gate PASSED).** Post-run audits flagged tests
that were too lenient or too strict; each was repaired under the fairness rule (only what the
instruction states or implies), proven with new wrong-fix patch checks, and saved solves were
regraded on the repaired tests. Outcomes: asyncssh / DeepSeek reopened (above); async-http-client
/ MiMo lost its old solve to a real defect, then solved 3 of 3 fresh offline runs; one filament
regrade and two cloudreve solves are held to the instruction they ran under (rules added after
the run do not count). Details per task: `build/<task>/notes.md`, section "2026-10-16 test repair".

**Corrected since the 2026-10-15 report** (details under "Corrections"):
- **actualbudget / MiMo** and **stigmem / MiMo** were reported failed 0/3; both were test faults
  and both pairs are now **SOLVED**.
- **rclone-sib / MiMo** was reported SOLVED; it was a false solve and is now open.
- Many other "SOLVED" verdicts came from runs that looked the fix up online. CWE-bench would not
  allow that, so those pairs are open again.

## All trialed tasks (mined → stacking → injection)

| Track | Task | Language | DeepSeek | MiMo | Verdict | Image build (cached / longest) | Image size |
|---|---|---|---|---|---|---|---|
| mined | async-http-client | Java | SOLVED 1/1 (+1 solved using the internet) | SOLVED 3/3 (+1 ungraded) (+2 cut at 60 min) | rejected (both solved) | 2.2 min / 17.0 min | 1.54 GB |
| mined | hickory-dns | Rust | SOLVED 1/1 (+1 used leaked tests) (+1 solved using the internet) | SOLVED 1/1 | rejected (both solved) | 10 s / 4.1 min | not measured |
| mined | jackson-databind | Java | SOLVED 1/2 | SOLVED 1/1 | rejected (both solved) | 33 s / 7.0 min | not measured |
| mined | py-shiny | Python | SOLVED 1/1 (+3 ungraded) (+1 solved using the internet) | SOLVED 1/1 (+2 ungraded) | rejected (both solved) | 4 s / 3.5 min | not measured |
| mined | rclone | Go | SOLVED 1/1 (+3 task leaked the answer) | SOLVED 1/1 (+2 task leaked the answer) | rejected (both solved) | 18 s / 49.9 min | not measured |
| mined | russh | Rust | SOLVED 1/1 (+1 ungraded) (+1 solved using the internet) | SOLVED 1/1 (+1 ungraded) | rejected (both solved) | 3.0 min / 11.9 min | not measured |
| mined | webob | Python | SOLVED 1/1 (+3 task leaked the answer) | SOLVED 1/1 (+3 task leaked the answer) | rejected (both solved) | 25 s / 3.0 min | not measured |
| stacking | actualbudget | TypeScript | SOLVED 1/1 (+1 ungraded) (+1 solved using the internet) | SOLVED 1/1 (+3 test fault, not regradable) (+2 solved using the internet) | rejected (both solved) | 5 s / 1.3 min | not measured |
| stacking | argo-workflows | Go | SOLVED 1/1 (+1 solved using the internet) | SOLVED 1/1 (+1 test fault, not regradable) (+1 solved using the internet) | rejected (both solved) | 4 s / 10.7 min | not measured |
| stacking | asyncssh | Python | no graded run (+2 ungraded) (+1 awaiting audit) (+2 solved using the internet) | SOLVED 1/1 (+2 cut at 60 min) (+1 solved using the internet) | rejected (MiMo solved) | 6 s / 1.6 min | 811 MB |
| stacking | cloudreve | Go | SOLVED 1/1 | SOLVED 1/1 (+1 cut at 60 min) | rejected (both solved) | 2 s / 4.6 min | not measured |
| stacking | filament | PHP | SOLVED 1/1 (+2 ungraded) (+1 audit: untrusted) (+1 solved using the internet) | SOLVED 1/1 (+1 ungraded) (+1 cut at 60 min) (+1 solved using the internet) | rejected (both solved) | 8 s / 4.4 min | not measured |
| stacking | ruby-saml | Ruby | SOLVED 1/1 (+1 solved using the internet) | SOLVED 1/1 (+1 ungraded) (+1 solved using the internet) | rejected (both solved) | 4 s / 1.9 min | not measured |
| stacking | stigmem | Python | SOLVED 1/1 (+1 test fault, not regradable) (+1 solved using the internet) | SOLVED 1/1 (+2 cut at 60 min) (+1 test fault, not regradable) | rejected (both solved) | 5 s / 6.9 min | 876 MB |
| stacking | trigger-dev | TypeScript | SOLVED 1/1 (+2 ungraded) (+2 cut at 60 min) (+1 solved using the internet) (+1 grader fault) | SOLVED 1/1 (+1 cut at 60 min) (+1 solved using the internet) | rejected (both solved) | 36 s / 10.0 min | 5.96 GB |
| injection | jackson-databind-sib | Java | **failed 0/6** [0.625, 0.625, 0, 0, 0, 0.625] | SOLVED 1/2 (+1 provider stop) | rejected (MiMo solved) | 3 s / 1.3 min | not measured |
| injection | jackson-sib7 | Java | SOLVED 1/4 (+4 ungraded) | SOLVED 1/2 (+1 ungraded) | rejected (both solved) | 5 s / 5.4 min | not measured |
| injection | rclone-sib | Go | SOLVED 1/1 (+6 task leaked the answer) | SOLVED 1/1 (+6 task leaked the answer) | rejected (both solved) | 3 s / 5.3 min | not measured |
| injection | russh-sib | Rust | SOLVED 1/1 (+2 used leaked tests) (+1 solved using the internet) | SOLVED 1/1 (+1 ungraded) | rejected (both solved) | 7 s / 8.1 min | not measured |

Counts are audited, counted runs only. Extra solves of an already-SOLVED pair were not all
audited, because one trusted solve settles the pair. The full breakdown (ungraded, cut at
60 min, leaked, grader fault, test fault, awaiting audit) is in `build/audit/ledger.md`.

**Image columns:**
- **Build times** come from Harbor's environment-setup phase across all runs. "Cached" is the
  median; "longest" is the closest thing on record to a full build.
- **Image sizes** can only be read while an image exists. The 15 "not measured" were skipped by
  decision. Every reading is logged in `~/.tb-graders/cwe/archive/image-sizes.log`.

**Cleanup log (2026-10-15):** removed russh's Rust build output from its run folders (10.7 GB,
regenerable; all 6 runs archived first) and the `argo-wf-task` image (a manual builder image no
task uses; ~9 GB).

## Grading and evidence changes (2026-10-15)

- **Needs review, not fail.** A non-solving run whose grading setup broke is no longer counted as
  a model failure. Breakage means a build or server step failed, tests didn't report, every
  functional test failed, or a process crashed. Each such run is decided from saved evidence as
  `model` or `harness` (`build/review_flags.py`, `build/audit/reviews.tsv`).
- **Final code saved for every run:** `<trial>/final-code/` holds a diff of what the agent
  changed plus the grader's logs.
- **Containers kept for review.** Containers of non-solves are kept (`build/audit/kept_containers.tsv`);
  clean solves are removed. `build/release_container.py` removes a kept container after review.
- **Re-grading without a new model run.** `build/regrade.py` re-grades a run's final output
  inside its kept container. The result goes to `<trial>/regrade-<UTC>/`, and the original
  grading is never changed.
- **trigger-dev grader hardened:**
  - kills processes the agent leaves behind;
  - has timeouts on every setup step;
  - moves crash core dumps out of `/app`;
  - runs with 8 GB of memory (was 6).

  It was validated by the gate and by a fake-leftover-server test. trigger-dev/DeepSeek run 4
  was re-graded this way: a 4.5 GB core dump from a crashed type-check had broken its build.
- **Memory budget:** at most ~11 GB of task memory limits running at once on the 12 GB VM
  (`build/TRIAL-PROCEDURE.md`).

## Evidence archive

Every finished run is copied into **`~/.tb-graders/cwe/archive/`** (outside the repo) and locked
read-only: 140 runs as of 2026-10-15 18:47 UTC.
- **Naming:** each run folder is `<START-UTC>__<limit>m__<outcome>__<job>__<trial>`, so time
  order and the 60- vs 120-minute era show in the name.
- **Task versions:** every version a run used is archived and verified against the fingerprint
  Harbor recorded. That includes versions rebuilt after later edits.
- **Where to start:** the archive's `README.md` and `INDEX.tsv`. Rerun `build/archive_runs.py`
  to add new runs.

## Hidden tests leaked into 5 images (found and fixed 2026-10-15)

hickory-dns, rclone, rclone-sib, russh and russh-sib copied their hidden tests into the image at
`/opt/harness`. The agent shares that container, so in 7 runs it read or ran them. Those runs
are excluded (`build/audit/contaminated.tsv`).

**After excluding them, every pair has a clean verdict.** hickory-dns had none at first. It was
rerun on the fixed image and solved by both models: DeepSeek in 9 min, MiMo in 62.

**The grading is behavioural in all 19 tasks:** every security test runs the exploit against the
running code, and none pattern-matches the source.

**The fix:**
- the five images now hold only build stubs, and `test.sh` copies the real tests in at grading time;
- all five passed the full gate again;
- the gate now fails any task whose `environment/` holds test code, and BUILDER.md forbids it.

## Corrections to earlier tables

**2026-10-16 (network setting):**
- Our trials had open internet; CWE-bench runs offline (model API only). Solves that used any
  internet lookup no longer count.
- The webob image shipped this advisory's own regression tests: its vulnerable commit was
  upstream's "Add regression tests" commit. It moved to the parent commit `b240857`, and earlier
  webob runs do not count (`build/audit/task_defects.tsv`).

**2026-10-16 (post-run audit and own-runs analysis, `research/own-runs/FINDINGS.md`):**
- **actualbudget / MiMo:** "failed 0/3" was a **test fault**. The path-traversal test called
  `getPathForUserFile`, which MiMo had hardened, so the test crashed before sending a request.
  - The test was repaired; the gate now includes a hardened-helper patch.
  - The 3 runs are excluded (no saved code). Reruns on the repaired test: 2 of 3 scored 1.0,
    both audited trustworthy, so the pair is **SOLVED**.
- **stigmem / MiMo:** "failed 0/3" was a **test/instruction mismatch**. The instruction says
  "bound to a non-loopback address"; the tests varied `node_url` instead. The v4 test also used
  an internal call.
  - Tests repaired. Both saved-code runs regrade to 1.0, and the pair is **SOLVED** (audited).
- **rclone-sib / MiMo:** "SOLVED" was a **false solve**: proxy mode refused everyone, and the
  tests checked refusals only. It is now open, pending a test repair and new runs.
- **trigger-dev / DeepSeek:** its failures came from faulty tests (exact 405; a functional
  fixture outside the instruction's scope). The tests are repaired, and regrade plus audit are
  pending.
- **Harness:** Harbor does not kill the agent at timeout, and in 15 runs it kept working while
  the tests ran.
  - None of those runs changes a counted verdict: the agent was checked for activity during
    each grading window.
  - Every `test.sh` now kills the agent before grading.
- **Gate:** new checks fail on exact-status assertions and require "hardening" and "blind" pass
  patches (`builder/gate.py`, `builder/BUILDER.md` §3f–3g).

- **async-http-client:** MiMo did not fail; it solved (the solve was graded at the 60-min mark).
- **jackson-databind:** DeepSeek did not fail; it solved 2 of 3.
- **asyncssh / MiMo:** its 60-min failures were the time limit; at 120 min it solved (82 min).
- **"7 undecided tasks / voided by starvation"** (an earlier version of this file) was wrong. A
  file-reading bug in `build/trial.py` logged graded runs as `None`. It is fixed.
- **trigger-dev / DeepSeek run 1** (scored 0.0) was a grader fault, not a model failure: the
  grader's build failed and it tested the old server. It is excluded.
- **py-shiny** is a mined task (its task.toml says `source = "mined"`). It came from Task13.

## Not built / not trialed

- **Abandoned, single-sink base (no second site for a sibling):** async-sib, tomcat-sib.
- **Shortlisted, not built:** velocity.js, pyload, tomcat, gitpython, koel, gitea, coredns,
  phpmyfaq, mariadb-connector-j, loofah, webpack-dev-middleware, style-dictionary,
  graphql-tools, gradio.
