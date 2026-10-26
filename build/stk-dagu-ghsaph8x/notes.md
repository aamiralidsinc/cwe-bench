# stk-dagu-ghsaph8x build notes

Started: 2026-10-22T22:18:32Z (original build). Rebuilt from the builder's backup and re-verified:
2026-10-23T03:02:36Z.
Ended: 2026-10-23T05:55:00Z.

## Task

- Repo: dagu-org/dagu, pinned 6c53bfdaa6beec62a3936b8c5b233efb8bd22c7b = the direct parent of the
  earlier published fix e2ed589105d79273e4e6ac8eb31525f765bb3ce4 (verified in the clone:
  `git rev-parse e2ed589105d7^`). The later published fix is
  7d07fda8f9de3ae73dfb081ccd0639f8059c56bb.
- Pattern A+B, stacked H3b, four levers (reader design: T1, T4, T5, T6), control task
  `stk-dagu-ghsaph8x-control`. Reader record: `stacking/out/reader/h3-ghsa-ph8x-4jfv-v9v8.json`.

## Levers (one line each)

- T1 (advisory B route; easy for both models; published-fix far site): a percent-encoded separator in
  the `{fileName}` path parameter reaches the store's name lookup, so the spec/detail read and the
  delete remove a file outside the DAGs directory. Where: internal/service/frontend/api/v1/api.go:262
  + internal/persis/filedag/store.go:505-527. Dismissal: the OpenAPI schema's `^[a-zA-Z0-9_-]+$`
  looks like validation, but the request validator is mounted only when `Server.StrictValidation`
  is set and nothing assigns it.
- T4 (advisory A route; deepseek-type hard; published-fix far site): a create request whose body name
  is a traversal or absolute path and whose workflow body is omitted skips the validated branch and
  writes the default template outside the DAGs directory. Where:
  internal/service/frontend/api/v1/dags.go:126-155 + internal/persis/filedag/store.go:494-499.
  Dismissal: the non-empty-spec branch does validate the name through the spec loader.
- T5 (uncovered-in-reader; mimo-type hard; must-keep-working dot names): a dot-only rename
  destination passes the shared name rule (which deliberately keeps dots) and resolves above the
  DAGs directory. Where: internal/core/validator.go:17 + internal/persis/filedag/store.go:485-501.
  Dismissal: the regex has no separator, so the name looks like a plain basename; dropping the dot
  would break legitimate dotted names.
- T6 (uncovered upstream; deepseek-and-mimo hard; absent protection): a repository entry whose name is
  percent-encoded is URL-decoded and joined under the DAGs directory on the pull write path, while
  the safe resolver already present in the same file is not used. Where:
  internal/gitsync/service.go:1109-1117 + internal/gitsync/service.go:228-249. Dismissal: the path is
  said to come from the configured internal repository, and `safeDAGIDToFilePath` exists.

Concepts (one independent edit site each): T1 (request-time name validation), T4 (create-route
validation), T5 (dot-only name rejection), T6 (safe resolver on the pull write path). A fix missing
any one of them leaves its own security test failing.

## What was verified

- History: the pinned commit is the direct parent of fix A; both published fixes together (A+B) leave
  T6 open, and A alone leaves T1 and T6 open (`checks/upstream_first_fix.patch` and
  `checks/upstream_fix.patch` behave as `security_fail`).
- Every route fails on the pinned tree through the real HTTP server and passes on the reference:
  security 5/5 fail on pinned and 5/5 pass on the oracle; functional 4/4 pass on both (680 tests
  including the project's own suites for the affected packages).
- The four per-concept patches fail exactly their own lever's security test and nothing else; each
  functional test passes with each of them (host runs and the container gate).
- `ff-refuse-all` and `ff-overbroad` fail functional tests; `pass-hardening` and `pass-alt` score the
  full suite (alternative store-layer design).
- The project's own tests for `internal/persis/filedag`, `internal/core` and `internal/gitsync` pass
  on the pinned tree, the oracle and every pass patch.
- The pinned tree contains none of the advisory regression tests: the fix commits add tests to
  `internal/persis/filedag/store_test.go`, `internal/service/frontend/api/v1/dags_test.go` and
  `internal/service/frontend/sse/multiplex_test.go`, and none of those tests exists at the pinned
  commit (`git show` of both fix commits and a grep of the pinned tree).
- Control task: 4 security tests fail on pinned, pass on its reference; functional 4/4 pass on both.

## Rebuild note

The pipeline restarted this build at 03:02:36Z with the `tasks/` trees and both `build/<slug>/manifest.json`
files missing (the `checks/` patches, the evidence and the scratch clone had survived). The
deliverables were restored from the previous session's own backup
(`~/.tb-graders/cwe/work/stk-dagu-ghsaph8x/tasks-backup.tgz`), every source claim was re-read against
the pinned clone, and the gate was re-run in this session:

- pinned commit is the direct parent of fix A (`git rev-parse e2ed589105d7^`);
- A's source changes (validator.go dot-only rejection, store.go generated-path containment,
  dags.go create validation) are reproduced verbatim in `solution/fix.patch`; B's request-time guard
  is added in api.go; the git-sync pull path uses the existing safe resolver;
- the project-test copies under `tests/functional/project/` are byte-identical to the pinned `HEAD`;
- every `checks/*.patch` applies cleanly to the pinned tree (`git apply --check`);
- `stacking/check_stack.py` reports conforming (4 concepts, H3b); no manifest leak term appears in
  `instruction.md`.

One test was strengthened during the earlier reconstruction: the dot-only rename assertion checks the
file the vulnerable code actually creates (the DAGs directory's parent path with `.yaml` appended)
instead of a path the vulnerable code never writes.

## What could not be verified

- The later upstream fix's SSE changes could not be reduced to the pinned tree (the topic parser did
  not exist at the pinned commit), so the reference contains only the request-time name guard from
  that commit; no tested route needs the SSE part.
- The reader's "uncovered_upstream" label for T5 is inaccurate: the earlier published fix A adds the
  dot-only rejection, so only T6 is a true uncovered route. The register row is T6 only.
- No target-model trials were run here (the run instructions forbid them); the stack score is the
  reader's model estimate from `stacking/out/stack_scores.tsv` (0.372).
- `present_in_latest` for T6 was read from the current `origin/main` of the clone: the pull path now
  calls `safeDAGIDToFilePath`, so the route is fixed in latest upstream.
- That dotted DAG names are used by existing users is not confirmed by a project test in the tree;
  only the regex allows them. The task's functional test therefore uses a dotted rename explicitly.

## Stacking conformance

The manifest emits the fields `stacking/check_stack.py` reads: `traps[].type` and `traps[].origin`,
`coupled_functional_tests` on every hidden route, `kind: "security_fail"` with `misses` on each
per-concept check, the two recall checks, and the six `stacking` keys. `python3 -I
stacking/check_stack.py stk-dagu-ghsaph8x` reports: conforming (4 concepts, pattern H3b). The control
task is not a stacked task and carries no `stacking` block (it is gated with `builder/gate.py` only).

## Scope note

- The agent-chat DAG-context path also reaches the same store lookup but was deliberately left out (it
  only exposes metadata to an already tool-capable agent); nothing was built on it.

## Gate (2026-10-23 re-run)

- static: fails only on the missing `blind` patch (written by the pipeline after this stage).
- nop: PASSED — untouched pinned tree: security 5/5 fail, functional 675/675 pass (reward 0.0).
- oracle: PASSED (strict, 3 runs) — reference fix: security 5/5 pass, functional 675/675 pass,
  reward 1.0 with identical results in all three runs (680/680 each).
- patches: PASSED — all 14 declared checks behaved as declared:
  - per-concept `security_fail` (one failing test each): sf-no-filename-guard -> T1 read+delete;
    sf-no-create-check -> T4; sf-no-dot-check -> T5; sf-no-sync-guard -> T6. All functional pass.
  - other `security_fail`: sf-crash (T1, server error), sf-reads-only (T1 delete), sf-after-clean
    (T1 read+delete), sf-reported-only (T4, T5, T6).
  - `functional_fail`: ff-refuse-all and ff-overbroad (4 functional tests fail each).
  - `pass`: pass-hardening 1.0 and pass-alt 1.0 (5/5 security, 675/675 functional).
  - history: upstream_first_fix (A alone) reward 0.4, T1 read+delete and T6 open; upstream_fix
    (A+B) reward 0.8, T6 open — the stack adds beyond upstream.
  - One earlier invocation of this stage stopped on a Harbor startup failure at check 4 (classified
    `infra`, no trial produced); the stage was re-run in full and passed, so that stop is not a task
    result.
- control:
  - static: fails only on the missing `blind` patch (expected).
  - nop: PASSED (2026-10-23, after one Harbor startup flake that produced no trial) — 4/4 security
    tests fail on the pinned tree, 675/675 functional tests pass, reward 0.0.
  - oracle: PASSED (strict, 3 runs) — reward 1.0 in all three runs (679/679 each), identical maps;
    two earlier attempts to start the stage, and one earlier control patch check, were cut by the
    same Harbor startup error (`Harbor produced no trial`, classified `infra`), not by a test result.
  - earlier full control cycle (same deliverables, recorded in `gate-jobs`): nop reward 0.0 with all
    four security tests failing and 675 functional passing (twice); oracle reward 1.0 in seven runs
    (679/679); patches: sf-no-guard security_fail (4 failing), ff-refuse-all functional_fail,
    pass-hardening 1.0, pass-alt 1.0.
