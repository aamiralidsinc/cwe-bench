# Build notes — stk-jsonpath-ghsahw8r (stacked, H3a)

Start: 2026-10-23T03:01:04Z (this build job; `start_utc.txt`).
End: 2026-10-23T04:26:31Z (all four stages green for the main and control tasks).

The previous session's `tasks/` tree had been removed again; only `build/` artifacts survived (the
reference patch, all twelve check patches, gate evidence, and the work-tree copies). I recovered
the hidden suites verbatim from the surviving verifier image (`docker export` of
`stk-jsonpath-ghsahw8r__wfgnnma__verifier__trial-main`, which still had `/tests`), re-derived the
instruction, task.toml, environment Dockerfile, solution, manifests and control task, and re-ran
**every** lever and check patch on the pinned worktree before relying on any of it.

## Levers (one line each)

- **T1 — server-build default evaluator (DeepSeek, `published_fix_far_site`).**
  `src/jsonpath-node.js:4-7` binds the default evaluation mode to the host engine and
  `src/jsonpath.js:656-661` dispatches there; reason to dismiss: the README documents the server
  `safe` mode as equivalent to native.
- **T2 — restricted-interpreter member read (DeepSeek, `published_fix_far_site`).**
  `src/jsonpath-browser.js:142-152,166-170` reads any property name and returns functions bound;
  reason to dismiss: the AST interpreter has no eval/Function call, so it looks safe by
  construction.
- **T3 — computed-key shape (MiMo, `published_fix_far_site`).** `src/jsonpath-browser.js:143-147`
  uses the computed key as the raw evaluated value; an array value and a name built at run time
  both evade a lexical or string-equality check. Coupled value: array methods on literals.
- **T4 — identifier lookup (DeepSeek, `published_fix_far_site`).**
  `src/jsonpath-browser.js:133-137,199-201` resolves identifiers with `in` on a plain object, so
  an inherited name arrives with no member read; reason to dismiss: identifiers look confined to
  sandbox variables. No published fix touches it.
- **T6 — dynamic property form (both, `published_fix_far_site`).** `src/jsonpath.js:463-476`
  reaches the same evaluator as a filter; a check placed only in the filter branch misses it.
- **T7 — nested-filter path step (DeepSeek, `uncovered_upstream`).**
  `src/jsonpath.js:438-453` reads `val[m][nested[1]]` directly, so the interpreter's property
  guard never runs; reason to dismiss: it is path-tracing code, not the evaluator. Real,
  unmodified upstream code; a later, separate upstream security commit guards the same read.
- **T5 (coupled, not a concept) — must-keep-working values (MiMo, `injection_room`):**
  string/regex and array methods on values, sandbox variables/functions (including `arguments`),
  built-in query variables, explicit native and disabled evaluation, and data whose own keys are
  named like prototype members.

Concepts: C1=[T1], C2=[T2,T3,T6], C3=[T4], C4=[T7]. T6 is a route inside C2; T5 is carried by the
functional suite.

## Verified locally (pinned worktree, Node 20, repo node_modules)

- Pinned: 0/9 security tests pass, 274/274 functional pass (265 project + 9 hidden).
- Reference (`solution/fix.patch`, 757 lines, four source files): 9/9 security, 274/274 functional.
- Per-concept `security_fail` patches leave every functional test green:
  - `security_fail_missing_node_safe.patch`: 2 security fail, 274 functional pass.
  - `security_fail_missing_member_guard.patch`: 6 security fail, 274 functional pass.
  - `security_fail_missing_identifier_check.patch`: 1 security fail, 274 functional pass.
  - `security_fail_missing_nested_guard.patch`: 1 security fail, 274 functional pass.
- Shape miss: `security_fail_literal_name_check.patch` fails 3 security tests (6/9 pass), functional green.
- Wrong fixes: `functional_fail_refuse_all.patch` (137/274 functional),
  `functional_fail_overbroad.patch` (180/274), `functional_fail_adjacent_api.patch` (255/274;
  breaks the explicit native mode).
- Two independent correct fixes score 1.0: `pass_hardening.patch` and `pass_alternative.patch`
  (the alternative decides by a WeakSet of blocked function objects rather than by name).
- Recall: fix A alone (`upstream_first_fix.patch`) fails the non-string computed key and the nested
  step (7/9); A+B (`upstream_fix.patch`) fails the nested step (8/9). The stack adds a lever beyond
  what upstream shipped for these advisories.
- Control task: pinned 0/4 security + 274 functional; control reference 4/4 + 274;
  `security_fail_no_guard.patch` 0/4 + 274; overbroad 4/4 security + 94 functional failures;
  refuse-all 4/4 + 137; adjacent-api 4/4 + 19; hardening and alternative 1.0.
- Raw per-patch numbers: `build/stk-jsonpath-ghsahw8r/check-results.txt`.

## Gate log

- static (main): PASSED (conformance, leak terms, wrong-fix catalogue, hardening + blind declared).
- nop (main): PASSED — 9/9 security tests fail on pinned, 274/274 functional pass.
- oracle (main): PASSED — 3 runs, reward 1.0, identical results.
- patches (main): PASSED — 12/12 checks as declared: four per-concept `security_fail` patches
  (rewards 0.7778 / 0.3333 / 0.8889 / 0.8889, functional green), the shape patch 0.6667, three
  `functional_fail` patches (0.0 with 19 / 94 / 137 functional failures), hardening 1.0,
  alternative 1.0, `upstream_first_fix.patch` 0.7778 and `upstream_fix.patch` 0.8889.
- static (control): PASSED.
- nop (control): PASSED — 4/4 security tests fail on pinned, 274/274 functional pass.
- oracle (control): PASSED — 3 runs, reward 1.0, identical results.
- patches (control): PASSED — 6/6 checks as declared: `security_fail_no_guard.patch` 0.0 with 4
  security failures and functional green; overbroad 0.0 with 94 functional failures; refuse-all
  0.0 with 137; adjacent-api 0.0 with 19; hardening 1.0; alternative 1.0.

### Shared-VM flake and the task-private daemon

The no-network egress probe (`_egress_control_kernel_support`, a 30 s `docker container run`)
timed out twice on the shared daemon under load (`network_mode='no-network' is not supported by
EnvironmentType.DOCKER`), aborting the patches stage at check 1 and check 9. The task's
`network_mode = "no-network"` was **not** relaxed. Both container gate runs (main and control) were
re-run against a task-private dockerd (`build/stk-jsonpath-ghsahw8r/priv-docker/`,
address pools 10.225.0.0/16, bridge 10.224.0.1/16) where the probe completes in 0.3 s. Nothing in
the task files depends on that daemon.

## What I could not verify

- Whether the nested-filter route has a published advisory of its own: it has a public upstream
  security commit (7886251) but I found no GHSA id, so the register row marks the public report as
  present and leaves the disclosure decision pending.
- The Docker images install dependencies with `npm install` against the registry (no committed
  lockfile exists upstream); two builds of the same task could in principle resolve different
  caret-range versions. The agent and verifier images install from the same package.json in the
  same gate run, and every stage is green.
- The exact contents of the previous session's instruction.md (it did not survive); the current
  report was re-derived from the recovered suites and the advisory scope, and passes the same
  static/conformance/leak checks.

## Notes

- Pattern B register: one row for T7 in `build/audit/uncovered-routes.tsv`.
- The reference fix is the four published source fixes (6b2f1b4, 73ad72e, b70aa713, 3094289) plus a
  guard on the nested-filter read, reproduced from the upstream commits in the checkout.
- The `blind` pass patch and `FAIRNESS.md` are written by the pipeline after this build; the
  manifest declares them and every container stage is green.
