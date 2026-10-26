# stk-tonapi-439 build notes

- Start (UTC): 2026-10-26T02:11:32Z (build job start)
- End (UTC): 2026-10-26T04:52:51Z

## What the task is

`nessshon/tonapi` (pytonapi SDK), pinned at `e46c4a4b907cbb1f290ef73af299b5020ec9de71`, the
direct parent of the published fix `854222b7ee68d3fb7b4d6d899d200f388483bd86` ("Fix webhook auth
bypass on custom paths"). The dispatcher accepts a delivery when no secret was stored for the
request path it resolves to. The report is at product level (an application registers handlers and
the SDK is supposed to verify the TONAPI-issued secret); the hidden suites live in
`tasks/stk-tonapi-439/tests/` and the control is `tasks/stk-tonapi-439-control/`.

## Levers (one line each)

- T1 (advisory route, both): `pytonapi/webhook/dispatcher.py:106-112` stores a secret only under
  `self._path + DEFAULT_SUFFIXES[event_type]`, while routing uses the route the application
  registered; a custom route is routed and then verified against nothing.
- T2 (uncovered upstream, DeepSeek): `pytonapi/webhook/dispatcher.py:258-260,341-343` resets the
  routing table on registration but nothing issues a secret for a route added after provisioning;
  `286-288` skips verification because the lookup returns nothing. Still open in the published fix
  and in `origin/main` on 2026-10-26.
- T3 (published-fix far site, MiMo): `pytonapi/webhook/dispatcher.py:137-147` derives cleanup
  endpoints from the default suffixes, so a setup-only fix creates per-route webhooks that
  `teardown(cleanup=True)` never unsubscribes.
- T4 (injection room, MiMo): `pytonapi/webhook/dispatcher.py:163-170` and `180-182` keep only
  `handlers[0][2]` per event type, so a second registered route is unreachable even when a secret
  was issued for it.

## Concepts and patches

- Concepts: `[T1, T3]` (provisioning and its cleanup twin), `[T2]` (late registration), `[T4]`
  (every registered route). T3 has no independent security test on the pin (the route is
  fail-closed), so it is graded by the coupled functional test rather than as its own concept.
- `miss_T1.patch`: setup and teardown left on the default suffixes, routing and the fail-closed
  branch fixed. 3 security fail, 0 functional fail.
- `miss_T2.patch`: the published fix without the fail-closed branch. 2 security fail, 0 functional.
- `miss_T4.patch`: provisioning and checking fixed, routing table left truncated. 2 security fail,
  0 functional.
- `missing_teardown.patch`: reference minus the teardown change. 0 security fail, 1 functional fail.
- `upstream_fix.patch` (recall): the published fix alone. 2 security fail, 0 functional fail.
- `hardening.patch` (pass), `alternative.patch` (pass, provisioned/dirty design).
- `malformed_identity.patch` (security fail), `refuse_all.patch` and `adjacent_api.patch`
  (functional fail).
- Control: the same report and pinned code; security tests cover only T1 (4 cases) and the
  reference only provisions per-route secrets. `control_reference.patch`, plus
  `missing_custom_provisioning.patch` (security fail), `control_refuse_all.patch` (functional fail),
  `control_hardening.patch` and `control_alternative.patch` (pass).

## Gate results (container)

- static: PASSED (stacked and control).
- nop: PASSED on the stacked task (5 security fail, 16 functional pass).
- oracle: PASSED on the stacked task (3 runs, each reward 1.0, identical results).
- patches: PASSED on the stacked task (all 10 present checks matched their declared outcome;
  `miss_T1` 0.4, `miss_T2`/`miss_T4`/`upstream_fix` 0.6, `malformed_identity` 0.8, `missing_teardown`
  and `refuse_all`/`adjacent_api` functional failures as declared, `hardening` and `alternative` 1.0;
  the missing `blind` patch is skipped by the gate).
- `check_stack.py`: conforming (3 concepts, pattern H4).
- Control gate: static PASSED; nop PASSED (4 security fail, 15 functional pass); oracle PASSED (3 runs at 1.0); patches PASSED (missing_custom_provisioning 0.0 with 4 security fail / 0 functional, control_refuse_all functional fail, control_hardening and control_alternative 1.0).

## Verified

- Pinned tree, pytest 9.1.1 (Docker `python:3.13-slim`, aiohttp 3.14.5, pydantic 2.14.1):
  stacked security 0/5, functional 16/16; reference 5/5 and 16/16.
- Control: pinned 0/4 and 15/15; control reference 4/4 and 15/15.
- Every stacked and control check patch applied to a fresh pinned copy matched its declared
  outcome (counts in `manifest.json` `verified.local_runs`).
- `git rev-parse 854222b7ee68d3fb7b4d6d899d200f388483bd86^` is the pinned commit; the fix commit
  adds 55 lines of regression tests that the pinned tree does not contain.
- Project tests for the affected area: `tests/webhook/test_dispatcher.py` (9 tests) pass on the pin
  and with the reference; the file is copied into the hidden functional suite so a submitted fix
  cannot edit it.
- `python3 -I common/gate/gate.py stk-tonapi-439 --only static` and
  `python3 -I pipelines/stacking/3-build-gate/check_stack.py stk-tonapi-439` pass
  (3 concepts, pattern H4; the control instruction is byte-identical).

## Could not verify / unknowns

- No target-model trials were run here (the build prompt forbids them); `score_at_build` is copied
  from the job's row in `pipelines/stacking/out/stack_scores_ds.tsv` (score 0.551), not recomputed.
- The prompt names the reader record at `pipelines/stacking/out/reader/h4-439.json`; that path does
  not exist in this checkout. The record with the quoted design is
  `pipelines/stacking/out/reader-ds/h4-439.json`, which is what `stacking.reader_record` points at.
- Whether upstream will later close T2: `origin/main` on 2026-10-26 still has the fail-open lookup
  and the registration reset, so it is open in the latest tree I could reach.
- T4 has no independent security failure on the pinned code (the second route is rejected as
  unknown, which is fail-closed); its security test therefore pairs the refusal assertion with the
  positive case (a route carrying its issued secret must be reachable). A setup-only fix and a
  routing-only fix both fail it.
- `crash_as_refusal`, `wrong_resource`, `one_role_or_direction`, `reads_only` and
  `check_after_adjustment` are marked n/a in the manifests with reasons; the dispatcher is an
  in-process library with no roles, no reads and no adjusting step.

## Out of scope noticed

- The published fix's token comparison is not constant-time (CWE-208); not part of the advisory's
  mechanism list and not built on (the `hardening` patch only demonstrates that a constant-time
  fix still scores 1.0).
