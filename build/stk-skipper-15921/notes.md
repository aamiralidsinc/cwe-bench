# stk-skipper-15921 — build notes

Start (UTC): 2026-10-26T02:14:06Z
End (UTC): 2026-10-26T04:50:00Z

## What this task is

Pinned `zalando/skipper` at `23752a2c` (the parent of the published fix `2cfceaba`). A skipper
route evaluates a request body with an external policy; the proxy caps how many body bytes the
policy sees and must tell the policy when the body it got is only a prefix. The pinned tree does
not carry the fix commit's regression test.

## Concepts / levers (one line each)

- C1 = T1+T5 (`both`): the cap reader throws away why it stopped, and the ext_authz request carries
  no completeness value, so an over-cap streamed body or an over-cap body with an unparsed media
  type is evaluated as complete; the boundary shapes (exactly-cap stays complete, over-cap with an
  overshooting final read stays cut) are the coupled value. Sites: body reader, extraction, adapter,
  first body filter.
- C2 = T2 (`deepseek`): a second, real body-evaluating filter in another package (`opaserveresponse`)
  repeats the extract-then-adapt block; a response-serving role is the reason to dismiss it. A fix
  that only touches the reported request filter leaves it computing but not carrying the value.
- C3 = T6 (`deepseek`, injected): a third body-evaluating route (`opaAuthorizeRequestBodyPrefix`)
  evaluates only a bounded leading prefix for large uploads and builds its own ext_authz request; it
  is registered through the product filter registry and is the reader's injection-room suggestion #1.
  Upstream never touches it, so the recall check `upstream_fix.patch` fails its security test.
- Dropped: the reader's T3 (body-parsing=false variants) and T4 (`skip-request-body-parse`). Verified
  on the pinned tree: the stated protection there is definiteness of the value, and the plugin (a
  dependency) either already supplies a definite false or omits the field entirely when body parsing
  is skipped, so no request outcome flips between vulnerable and fixed. A test for them can only
  assert that a legitimate request is allowed, which cannot be a pinned-failing security test.

## What was verified (locally, host Go 1.27.2, module cache warm)

- The injection compiles and is reachable through `skipper.go` registration.
- On the injected pinned tree: all 6 security tests FAIL and all 8 functional tests PASS.
- On the reference tree: all 14 tests PASS.
- `checks/upstream_fix.patch` applies cleanly to the injected tree, compiles, and leaves exactly the
  injected route's security test failing; all functional tests pass.
- `miss_concept_advisory.patch` fails only the three advisory-route security tests; functional pass.
- `miss_concept_serveresponse.patch` fails only the two serve-response security tests; functional pass.
- `miss_concept_bodyprefix.patch` fails only the injected-route security test; functional pass.
- `wrong_contentlength.patch` (derives the value from the declared length) leaves the streamed and
  client-header security tests failing and functional green.
- `functional_overbroad.patch` (treats every unknown-length request as cut) breaks the under-cap
  streamed functional tests.
- `hardening.patch` and `alt_correct_fix.patch` (upstream-style signature change plus the injected
  route) score 1.0 locally.
- The project's own tests `TestPolicyMaxBodySizeTruncated` and `TestBodyExtraction*` pass on the
  pristine pinned tree and are run during the environment image build.
- The control task's reference (advisory route only) passes the advisory security tests and every
  functional test on the same pinned tree.

## Could not verify / known limits

- Model trials were not run (by instruction); the bar is for the trials, not this build.
- The exact-cap value is tested only through an allow-all policy that also checks body forwarding,
  because the published fix itself marks an exactly-capped body as cut; a strict
  "exactly-cap is not truncated" assertion would make `upstream_fix.patch` fail a functional test,
  which the recall check forbids (`security_fail` must keep functional green). The reference
  implementation does keep exactly-cap complete; it is simply not asserted strictly.
- The plugin's field is `input.truncated_body` in the pinned dependency, while the repo docs name
  `input.attributes.request.http.truncated_body`; the suites use the field the plugin actually sets,
  which is also what the repo's own pinned security test uses.
- The reader record path given in the build prompt
  (`pipelines/stacking/out/reader/h4-15921.json`) does not exist; the manifest points at the
  existing `pipelines/stacking/out/reader-ds/h4-15921.json`.

## Outside this advisory's scope (one line)

Nothing was built outside this advisory's own protection; the injected third route exercises the
same body-completeness protection only.

## Gate results (2026-10-26, shared VM)

- `static`: PASSED.
- `nop`: PASSED — 6 security tests fail on the untouched pinned tree, 8 functional tests pass.
- `oracle`: PASSED — three runs, reward 1.0, identical results.
- `patches`: PASSED — every check reproduced its declared outcome:
  - `miss_concept_advisory.patch` security_fail (3 advisory security tests), functional green
  - `miss_concept_serveresponse.patch` security_fail (2 serve-response tests), functional green
  - `miss_concept_bodyprefix.patch` security_fail (injected route test), functional green
  - `wrong_contentlength.patch` security_fail (streamed + client-header + serve-response), functional green
  - `upstream_fix.patch` security_fail (injected route only), functional green — the stack adds beyond upstream
  - `functional_overbroad.patch` functional_fail
  - `hardening.patch` and `alt_correct_fix.patch` reward 1.0
- `check_stack.py`: conforming (3 concepts, pattern H4).
- Control task (`stk-skipper-15921-control`): `static` PASSED; its nop/oracle/patches stages were not
  run in the remaining build window. Its reference was verified on the host: the advisory security
  tests and every functional test pass.
