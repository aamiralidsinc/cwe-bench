# Fairness: stk-senaite-core-4280-control (2026-10-25 revision)

This control carries one concept (the advisory's own state-changing route). The
2026-10-25 audit (AUDIT-FIX-20261025.md) found a test-fault: the harness replaced
`bika.lims.api` with a fixed-function stub, so a correct fix that added a helper
to the product's own API module and called it from the record path failed with
`AttributeError`. Fixed by resolving undefined stub attributes from the real API
module source (dependencies replaced by placeholders) and by one functional
sanity test, `test_api_module.py::test_source_defined_helpers_are_reachable`.
No instruction sentence and no existing assertion changed.

## Stacking checks

| Check | Concept | Finding |
|---|---|---|
| S1 coupled traps | T1 (update authz) | `Remarks` (analyst) and `Title`/`Priority` (manager) must keep saving. Instruction: "Everything that works today keeps working: legitimate requests are not refused". Req. 1 forbids only data "the caller is not permitted to change"; the analyst holds the field permission and the manager the content permission. No rule forbids these values. No contradiction. |
| S2 shape traps | T1 | Refused shapes: an analyst writing `Title`/`Priority`, an anonymous caller, a workflow-restricted record. All lie outside the permitted set described by the field's write permission on the object; no keep-working clause or fixture calls them legitimate. |
| S3 fixtures and harness | T1 | States are product-legitimate (roles, a workflow-restricted record). The harness calls the real `Update.update` through its own route; a guard at the route, the shared field writer, or the product API module all pass. The 2026-10-25 fallback additionally admits a fix that puts its helper on `bika.lims.api` (verified with such a patch: security 4/4, functional 11/11). |
| S4 concept independence | T1 | Single concept; its tests do not depend on any other concept. No masking. |
| S5 history | T1 | The control's reference is the advisory's published in-repo authorization fix; no dependency bump and no upgrade is required by the instruction. |
| S6 contracts | T1 | No field or function name must be guessed; the protected object is named in product terms ("data", "a request's title") and the authority is the field's write permission on the object being written. |
| S7 decisive tests | T1 | No `trial_summary.md`; the archived control trials finished at reward 1.0 (deepseek run 1, mimo run 1), so no single test decided a failure. |
