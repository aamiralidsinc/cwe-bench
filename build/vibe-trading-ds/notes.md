# vibe-trading-ds build notes (build-v1, pattern A+B, injected)

Start (UTC): 2026-10-18T19:18:00Z (plan); resumed 2026-10-19T18:12:38Z
End (UTC): 2026-10-19T20:24:00Z

Candidate: hkuds/vibe-trading, GHSA-5RMQ-CHC7-M22F, CWE-22/23/552.
Pinned: fd767f5c29c72cffe8e3f89c7ff006cb3041397f (verified earlier as the sole
parent of fix 9454d4a27a763b80e1d6eb5763b86c88e9e4e714).

This is a rebuild of `vibe-trading-path-read`, which both target models solved. The
published-fix levers are kept, and three injected siblings sit on surfaces a
tool-by-tool audit does not reach (an HTTP route, a value inside run data, and a
name joined inside a validated skill directory).

## Protected sink

The location a file read/write/serve actually touches. At the pinned commit, agent tools
and API routes take the caller's location and touch it; the legit areas are the upload
area, run storage, bundled skill documentation, and operator-configured import roots.
Refusal is the tool's usual error envelope / a client error, with no content and no side
effect.

## Levers (each with a different reason a solver would skip it)

1. T1 (A, landing). Document reader takes any path. Shapes: absolute in HOME, cwd-relative,
   `..` out of uploads, symlink in uploads, sibling of a configured root. Published.
   Reason: none.
2. T2 (A, far, second implementation). Shared broker-file validator admits HOME+CWD;
   reached by the trade-journal and shadow-profile tools. Shapes: elsewhere in HOME, `~`,
   cwd-relative, link in uploads. Published. Reason: "already validated; the docstring
   says broker exports live anywhere in HOME".
3. T3 (A + producer). `read/write/edit_file` trust the model's `run_dir`; the loop mapper
   passes absolute values through and resolves relative ones. Published. Reason: "the
   workspace root is system-supplied and the path is already confined to it".
4. T4 (A). Pattern scan and backtest take `run_dir` unchecked. Published. Reason:
   "analysis and engine tools, not file readers".
5. T5 (B, real upstream). Factor analysis reads caller CSVs and creates caller output_dir;
   the published fix did not touch it. Reason: "returns only aggregate statistics". Real,
   unmodified upstream code.
6. T6/T7 (shapes). Symlink resolution before containment; component-wise containment (a
   name prefix is not a directory). Standard expert knowledge.
7. T8 (injected S1). Stored-document preview route serves a caller-supplied absolute path
   (and `..`). New code in `agent/api_server.py`, next to the upload handler that returns
   absolute paths. Reason: it is an HTTP read route, not an agent tool; the report is
   about what the agent reads.
8. T9 (injected S2). Backtest accepts a local data override named inside `config.json`; the
   tool reads it and echoes a preview. The config lives inside the confined run directory,
   so the location arrives as a value in data, not as a tool argument. New code in
   `agent/src/tools/backtest_tool.py`. Reason: "the workspace is already confined, so
   data inside it is trusted".
9. T10 (injected S3). `load_skill` gains an optional supporting-file name read from the
   skill directory; the join is not resolved/contained. The skill name itself is
   registry-validated, so the call looks scoped. New code in `agent/src/agent/skills.py` +
   `agent/src/tools/load_skill_tool.py`. Reason: "skill documentation loading is
   legitimate and the skill list is validated".

Coupled must-keep-working: uploaded path -> read/analyse/preview; run workspace (relative,
subdir, absolute, default); bundled skill docs through read_file; configured roots
(comma list, spaces, `~`) read in a fresh process; skill supporting files by their names;
backtest local data inside the run; preview by the uploaded path with dot segments staying
inside; factor on run artifacts and uploads; pattern/backtest on the current run;
write+edit in the run.

## Tests

Security: T1 (5), T2 (5), T3 (5), T4 (2), T5 (2), T8 (2), T9 (2), T10 (2) = 25. Every
assertion is "tool error / 4xx, no content marker, no side effect" - never one exact
status.
Functional: 20 hidden tests covering every coupled behaviour above, plus pristine project
tests (doc reader, shadow account, upload API, loop helpers without the unsafe
pass-through class): 81 passed, 1 deselected, on both pinned+injected and oracle.

## Verification (local, frozen Python 3.11 venv)

- pinned+injection -> 25 security fail, 20 functional pass; oracle -> 45 pass.
- Each `security_fail` variant: security fails, all functional (hidden and project) pass.
- The five functional_fail variants break functional tests (only `ff-refuse-all` and `ff-shared-helper-run-roots` are listed in the manifest).
- `pass-hardening` and `pass-alt-dispatch-guard`: 45 pass.
- Project tests on both trees: 81 passed, 1 deselected.

## Could not verify

- That both target models fail 3/3: no trials are run while building.
- Whether the MCP transport changes anything: same registry dispatch; not driven separately.
- Repo size in MB not measured.
- The `blind` patch and the fairness review are written downstream (static allows them).

## Gate results (Docker)

- static: FAIL only on `checks/blind.patch` missing and `build/<slug>/FAIRNESS.md` missing - the two
  artifacts written downstream; every other static check passes.
- nop (final test files): PASSED. 25 security tests fail on the vulnerable tree, 101 functional
  (20 hidden + 81 project) pass.
- oracle: PASSED, 3 identical runs at reward 1.0
  (jobs vibe-trading-ds-oracle{1,2,3}-1792435434/529/615).
- patches: PASSED, all 20 listed checks behave as declared
  (sf-* security fail with functional passing; ff-* functional fail; both pass patches 1.0).
- Environment flake: the Docker network-prune race on this shared 8-CPU VM ("network ... not found"
  during compose up) aborted three stage attempts; each stage was re-run until it completed. No
  task change was needed.

## Hardening pass (2026-10-22, v2)

The version above was solved by the graded solver, so two fair levers were added and the
delivery format was converted to Frontier schema 1.4 (separate verifier, /workspace,
uid-1000 non-root grading, artifacts restore, dual scoring).

New levers (different reasons to dismiss, independent of each other and of T1-T10):

11. T11 (B, real upstream route). `GET /runs/{run_id}/code`, `/runs/{run_id}/pine` and
    `/runs/{run_id}` build `RUNS_DIR / run_id` from a route identifier. `%2e%2e` as the
    identifier reads strategy code and chart files from the application directory.
    Reason to dismiss: a run id is an opaque server-minted value, not a path, and the
    published fix only added authentication to these routes. The instruction covers it
    literally as a request parameter. Coupled: a normal run's code and pine still serve.
12. T12 (injected, recorded location). A shadow profile records the journal it was built
    from (`extractor.py:124`, `storage.py:112`) and the backtest/report tools work from
    `profile.journal_path` without re-checking where it now resolves
    (`shadow_account_tool.py:188,256`). A link swapped into the upload area after
    extraction makes the attribution read a private statement and return its symbols.
    Reason to dismiss: the location was validated when the profile was created and the
    profile is application data. Coupled: attribution still runs from the recorded
    upload-area statement when the caller does not re-supply it.

Instruction changes: the general rule now also covers "a location the service records and
works from later"; the legit list names "a stored run's own strategy code and chart output";
"do not modify or add tests" was dropped and "There is no network access." added (B5).

Verification: locally (frozen Python 3.11 venv) the injected tree fails all 28 security
tests and passes all 23 functional tests; the oracle and the hardening/alternative/blind
pass trees pass all 51; each new security_fail patch fails only its own lever's tests while
all functional tests pass. Project tests: 81 passed, 1 deselected on both trees.

New checks: sf-no-run-route-id.patch (T11), sf-no-stored-journal.patch (T12); the three
pass patches were rebuilt on the new oracle. Gate stages: see harden3_*.log.

## Gate results (Frontier format, 2026-10-22)

- static: PASSED (conformance_check prints "conforming"; gate static passes).
- nop: PASSED. 28 security tests fail on the injected tree; 104 functional pass
  (23 hidden + 81 project).
- oracle: PASSED, 3 identical runs at reward 1.0 (jobs -oracle1/2/3-1792634xxx).
- patches: see harden3_patches*.log / eval of jobs; all 24 declared checks behave as declared
  (security_fail: at least one security test fails with every functional test passing;
  functional_fail: a functional test fails; pass: reward 1.0).

Harbor's Docker egress-control kernel probe (30 s `docker container run alpine`) flaked once
under the shared VM's load and aborted a patches attempt before any trial started
("network_mode='no-network' is not supported"); re-running the stage cleared it. No task change.
