# FAIRNESS — stk-senaite-core-4280

Reviewed: `instruction.md`, `tests/`, `solution/fix.patch`, `manifest.json`, `notes.md`, `checks/*.patch`. 21 hidden tests (11 security, 10 functional); reward 1.0 requires all 21 (`tests/score.py`). 3 concepts, 6 traps.

## 1. Test-by-test

| # | Test (file::name) | What it asserts | Covering sentence | Could a CORRECT fix fail it? | Risk |
|---|---|---|---|---|---|
| 1 | `security/test_update_authz.py::test_analyst_cannot_change_field_without_field_permission` | Analyst's `Title` write is refused (dict `success:false` or an exception) and `Title` is unchanged | Req. 1: "A caller must not be able to change data the caller is not permitted to change. Such a request is refused and leaves the stored data untouched." | no — check the field's write permission on the object before writing, then raise `Unauthorized` or return the route's own `error()` (`success:false`). A bare `{"error": ...}` without `success:false` is not accepted (quality item 6) | low |
| 2 | `security/test_update_authz.py::test_analyst_cannot_change_priority_field` | Analyst's `Priority` write is refused and the value unchanged | Req. 1 (same) | no — same per-field check; `Priority` uses the default content permission | low |
| 3 | `security/test_update_authz.py::test_anonymous_cannot_change_any_field` | Anonymous `Title` write is refused and unchanged | Req. 1 + report: "A caller who is not signed in can do the same." | no — the same check denies a user holding no roles | low |
| 4 | `security/test_update_authz.py::test_object_level_denial_is_respected` | A manager cannot write `Title` on `/ar-2`, whose own map removed the edit right, though its parent grants it | Req. 1 ("data the caller is not permitted to change") + standard expert knowledge: the permission is checked on the object being modified, not on its container | no — a per-object `field.checkPermission("edit", obj)` passes; a parent check is the wrong fix this targets | low |
| 5 | `security/test_update_many_authz.py::test_analyst_cannot_change_field_without_field_permission` | The batch route refuses an analyst's `Title` write and leaves it unchanged | Req. 1 (same), read literally over the batch form | no — a check in the shared writer covers this and the single route | low |
| 6 | `security/test_update_many_authz.py::test_anonymous_cannot_change_any_field` | The batch route refuses an anonymous write | Req. 1 + the anonymous report sentence | no — same | low |
| 7 | `security/test_read_methods.py::test_analyst_read_does_not_run_state_changing_method` | A read naming `refreshTotals` leaves `Priority` unchanged | Req. 1 read literally: the route runs a method that changes data the caller may not change; no route-naming sentence is required | no — skip or refuse names that are not read-only accessors; the test demands no refusal form, only no mutation | medium |
| 8 | `security/test_read_methods.py::test_anonymous_read_does_not_run_state_changing_method` | The same for an anonymous caller | Req. 1 + the anonymous report sentence | no — same | medium |
| 9 | `security/test_record_parsing.py::test_records_field_text_is_not_executed` | An expression payload sent as `Conditions` text is not executed (no marker file) and the stored value stays `[]` | Req. 2: "A record value supplied as text is data and must never be executed." + Contracts: a refusal "has no effect on the stored data" | no — literal-only parsing refuses the non-literal and the field keeps its value (the published a24d65e fix passes this) | medium |
| 10 | `security/test_record_parsing.py::test_record_field_text_is_not_executed` | The same for `Template` (exact `RecordField`) | Req. 2 (same) | no — same | medium |
| 11 | `security/test_record_parsing.py::test_record_subfield_text_is_not_executed` | The same for `PostalAddress` (`AddressField`, a derived field) | Req. 2 read literally: applies to every record value, derived classes included | no — safe parsing in both the API boundary and the record field classes | medium |
| 12 | `functional/test_updates_legit.py::test_analyst_can_save_remarks` | Analyst saves `Remarks`; `success` true and the value stored | Contracts: "Everything that works today keeps working: legitimate requests are not refused..." | no — the analyst holds the Remarks field permission, so a field-level check allows it; a blanket API gate is the wrong fix this catches | low |
| 13 | `functional/test_updates_legit.py::test_analyst_can_save_remarks_in_batch` | The same through `update_many` | Same keep-working contract | no — same | low |
| 14 | `functional/test_updates_legit.py::test_manager_can_save_ordinary_field` | A manager saves `Title` | Constraint: "Keep legitimate use working exactly as it works today." | no — the manager holds the content permission | low |
| 15 | `functional/test_updates_legit.py::test_manager_can_save_priority` | A manager saves `Priority` | Same keep-working clause | no — same | low |
| 16 | `functional/test_records_legit.py::test_address_record_text_saves` | A single-quoted dict literal sent to `PostalAddress` is stored as the dict | Same keep-working clause; the product's accepted format is visible in the repo | no — `ast.literal_eval`-style parsing accepts it; a JSON-only parser is a wrong fix this catches | low |
| 17 | `functional/test_records_legit.py::test_records_field_text_saves` | A literal string sent to `Conditions` is stored as `[dict]` | Same keep-working clause | no — same | low |
| 18 | `functional/test_records_legit.py::test_record_field_text_saves` | A literal string sent to `Template` is stored as a dict | Same keep-working clause | no — same | low |
| 19 | `functional/test_reads_legit.py::test_computed_values_are_returned` | An analyst's read returns `getPrintAddress` and `getVATAmount` | Same keep-working clause ("the product keeps returning the information it returns today") | no — a read-only accessor filter must keep get/is/has-style values | low |
| 20 | `functional/test_reads_legit.py::test_anonymous_can_still_read` | Anonymous can still read `Title` | Same keep-working clause | no — the authz fix touches writes, not reads | low |
| 21 | `functional/test_reads_legit.py::test_analyst_can_read_fields` | An analyst can still read `Title` | Same keep-working clause | no — same | low |

## 2. Leniency (quality; non-blocking)

| Property / trap | Most plausible wrong fix | Caught? |
|---|---|---|
| Req. 1 (single update) | Check the containing folder instead of the object | yes — `security/test_update_authz.py::test_object_level_denial_is_respected` (`checks/sf-wrong-object.patch`) |
| Req. 1 | Refuse anonymous callers only | yes — `test_analyst_cannot_change_field_without_field_permission` (`checks/sf-anonymous-only.patch`) |
| Req. 1 | Blanket `Access JSON API` gate on the write routes | yes — `functional/test_updates_legit.py::test_analyst_can_save_remarks` and `..._in_batch` (`checks/ff-blanket-access.patch`) |
| Req. 1 | Check after writing and rely on the transaction rollback | yes on the value assertions (`checks/sf-check-after-write.patch`), but only because the harness's `transaction.savepoint().rollback()` is a no-op |
| Req. 1 | Hardcode the example fields/roles (refuse `Title`/`Priority` for `Analyst`, allow the rest) | **NO** — no test uses a third write permission or another under-privileged role |
| Req. 1 | Per-field check inside the write loop, with no all-fields pre-check | **NO** — no test sends a permitted and a denied field in one request, so a partial write before the refusal is invisible |
| Req. 2 | Fix only the API boundary's exact type names | yes — `security/test_record_parsing.py::test_record_subfield_text_is_not_executed` (`checks/sf-jsonapi-parse-only.patch`) |
| Req. 2 | Fix only the field layer | yes — `test_records_field_text_is_not_executed` and `test_record_field_text_is_not_executed` (`checks/sf-no-jsonapi-parse.patch`) |
| Req. 2 | `json.loads` only | yes — `functional/test_records_legit.py::test_records_field_text_saves` (single-quoted literal) |
| Req. 2 | Leave `eval` in `records.py` | **NO** — an exact `RecordsField` string is always parsed at the API boundary before `records.py`'s `set` sees it; no `RecordsField` subclass is exercised |
| Req. 2 | Blocklist the literal payload (`__import__`, `os.system`) instead of parsing safely | **NO** — all three security payloads are the same shape |
| T1_update_authz | Blanket gate / parent check / post-write check | yes, as above |
| T2_update_many | Fix the single update route only | yes — the two `security/test_update_many_authz.py` tests (`checks/sf-update-only.patch`) |
| T2_update_many | Parent check in the batch route | **NO** — the batch tests use `/ar-1` only, where the object and parent maps agree |
| T5_coupled_remarks | Blanket gate / refuse all writes | yes — `functional/test_updates_legit.py::test_analyst_can_save_remarks` and `..._in_batch` (`checks/ff-blanket-access.patch`, `checks/ff-refuse-all.patch`) |
| T5_coupled_remarks | Special-case `Remarks` by name | **NO** — no second custom-permission field is tested |
| T7_jsonapi_eval | Fix the field layer only | yes — `test_record_field_text_is_not_executed` (`checks/sf-no-jsonapi-parse.patch`) |
| T8_field_layer_eval | Fix the API boundary only | yes — `test_record_subfield_text_is_not_executed` (`checks/sf-jsonapi-parse-only.patch`) |
| T8_field_layer_eval | Fix `record.py`, leave `records.py` | **NO** — see Req. 2 above |
| T9_named_method_invocation | Ignore every caller-named method | yes — `functional/test_reads_legit.py::test_computed_values_are_returned` (`checks/ff-drop-include-methods.patch`) |
| T9_named_method_invocation | Gate `read()` on the JSON API permission | yes — `test_anonymous_can_still_read`, `test_analyst_can_read_fields` (`checks/sf-read-gate-only.patch`) |
| T9_named_method_invocation | Leave `read` untouched and fix only writes | yes — both `security/test_read_methods.py` tests |
| T9_named_method_invocation | Denylist known mutator names, or a `get*/is*/has*` prefix heuristic | **NO** — only one state-changing method (`refreshTotals`) and two getters are tested; a name-based heuristic passes without proving the property |

**Wrong fixes no test catches:** hardcoded example fields/roles; `records.py` left unsafe; a payload blocklist; a parent check in the batch route; partial writes on a mixed-field request; special-casing `Remarks`; a name-based read-method heuristic (`Quality to tighten` below).

## 3. Hints (quality; non-blocking)

| Quote | What it names | Neutral wording |
|---|---|---|
| "Two problems are reported." | The flaw count (2), inviting a two-item checklist | "Problems are reported." |
| "A signed-in analyst who may not edit a request's title still changes it through the integration API update; the value is stored." | The actor, the example field and one entry point (`update`) | "A signed-in caller who may not edit a record still changes it through the integration API; the value is stored." |
| "the API runs the expression while handling the request" | The API-boundary stage and mechanism | "the expression is executed instead of the text being stored as data." |

## 3a. Required: generalize

**none.** The two route/stage phrases above name the reported anchor sites (the advisory's update route and API-boundary sink), not a sibling, far site or uncovered route; the earlier address-record and side-effect sentences are already gone (`listing.json`: T8 GENERAL, T9 ABSENT, PASS).

## 4. Realism (quality; non-blocking)

- All trap code is unmodified upstream and reachable through the real handlers; nothing looks planted.
- Only contrived element: the fixture's `refreshTotals` sets `Priority`; make its mutation match its name.
- `transaction.savepoint().rollback()` is a harness no-op, so check-after-write-plus-rollback is scored as a leak; a correct fix checks first, so this is not gate a.
- Check artefacts: `checks/pass-alt.patch` calls `parse_record_literal` in `records.py` without importing it (`NameError` swallowed by the bare `except`); `checks/sf-fail-open.patch` uses the harness-only `allowed_roles`.

## 5. Verdict

**Gate a: READY.** Each test is covered by a stated general property read literally. Requirement 1 ("A caller must not be able to change data the caller is not permitted to change") reaches the single write route, the batch route and the data-returning route: a read that runs `refreshTotals` changes `Priority`, which neither analyst nor anonymous may change. Requirement 2 reaches exact record fields and derived ones. A correct fix — each field's write permission checked on the object before that field is written, literal-only parsing at both sinks, and caller-named methods limited to read-only accessors — passes all 21; the oracle and `pass-hardening` prove it, and `pass-alt` uses another valid layer. Residual: the parsing tests also require the expression text not to be stored, while requirement 2 only forbids execution; storing it would fail, but that reverses the product's invalid-record path and the published a24d65e fix passes. The update refusal helper is narrower than "an error response or an exception", but matches the route's own shape. Difficulty, not unfairness, explains the 9/11 trial runs.

### Quality to tighten

| # | Change | Why |
|---|---|---|
| 1 | Add a `RecordsField`-subclass security case (or a direct field-layer call) for `records.py` | Its `eval` is never reached today, so leaving it scores 11/11 |
| 2 | Add a field with a different write permission and a `Client` role; add an object-level denial case to `update_many` | Defeats hardcoded example fields/roles and a parent check in the batch route |
| 3 | Send a permitted and a denied field in one request and assert neither is stored | The per-field-in-loop check writes the permitted value first |
| 4 | Add a second payload that does not contain `__import__` or `os.system` | Defeats a string blocklist |
| 5 | Add a second state-changing method and one whose name looks like a getter | Defeats a denylist and a naming-prefix heuristic |
| 6 | Align `test_update_authz._refused` with the more tolerant `test_update_many_authz._refused` | Accepts any instruction-allowed error response |
| 7 | Apply the three hint rewrites in section 3 | Removes the flaw-count, entry-point and stage pointers |
| 8 | Make the fixture's `refreshTotals` mutate something its name explains | Removes the one contrived element |

### Stacking checks

| Check | Concept | Finding |
|---|---|---|
| S1 coupled traps | C1 (T1/T2/T5) | `Remarks` (analyst) and `Title`/`Priority` (manager) must keep saving; Req. 1 forbids only data the caller is *not permitted* to change, and the analyst holds the Remarks field permission, the manager the content permission. No contradiction. |
| S1 | C2 (T7/T8) | The three literal dict/list values must keep saving; Req. 2 forbids execution, not literal parsing. No contradiction. |
| S1 | C3 (T9) | `getPrintAddress`/`getVATAmount` and anonymous reads must keep working; Req. 1 forbids changing data, not reading it. No contradiction. |
| S2 shape traps | C1 | Refused shapes (analyst `Title`/`Priority`, anonymous, a workflow-restricted object) all lie outside the permitted set (field write permissions / the object's own map). OK. |
| S2 | C2 | The refused payload is a function-call string; the legitimate format is a Python-literal dict/list (fixtures; the repo's own doctest). Outside. OK. A JSON-only parser also refuses the legitimate single-quoted literals and is caught — a fair shape trap. |
| S2 | C3 | `refreshTotals` is not a read-only accessor and mutates; the legitimate set is get/is/has-style accessors. Outside. OK. |
| S3 fixtures/harness | C1 | States are product-legitimate (roles and a workflow-restricted record); the harness calls the real `Update.update`/`update_many`; a pre-write guard at the route, the shared writer or a field API all pass. |
| S3 | C2 | Real `AddressField`/`RecordField`/`RecordsField` instances via the real update handler; a guard at the API boundary or in either field class passes. |
| S3 | C3 | The real `read()` handler and `load_method_values`; a guard in `read()` or in `load_method_values` passes. |
| S4 independence | C1 | Passes its own tests whatever C2/C3 do; no masking. |
| S4 | C2 | Passes its own tests whatever C1/C3 do; the parsing tests act as a permitted manager, so a correct C1 check does not block them. |
| S4 | C3 | Passes its own tests whatever C1/C2 do (`sf-no-include-methods` = 9/11). Masking: on pinned, `test_read_methods` fails through its own route (nop 0/11). |
| S5 history | C1 | `upstream_fix_raw` (published fixes as shipped) violates Req. 1 literally: a manager changes a workflow-restricted record (`test_object_level_denial_is_respected` fails). Property not too narrow. |
| S5 | C2 | The published a24d65e fix satisfies Req. 2; the parsing tests pass on `upstream_fix_raw`. No history issue. |
| S5 | C3 | `upstream_fix` (corrected recall) violates Req. 1 literally: the read route still runs `refreshTotals`, failing both read tests (9/11). Beyond the published fix but inside the stated property. No dependency bump. `checks/upstream_first_fix.patch` is absent; the recall pair is used instead. |
| S6 contracts | C1 | No name the solver must guess; the protected object is named in product terms ("data", "a request's title") and the authority is the field's write permission on the object. |
| S6 | C2 | No name to guess; the protected class is named in product terms ("record value", "record text"). |
| S6 | C3 | No name to guess; the authority is the existing caller-supplied method list. |
| S7 decisive tests | C1 | `trial_detail_deepseek.json`: 3/3 runs at reward 0.8182 = 9/11 security, 10/10 functional. No per-test breakdown in `build/` (trial directories are outside this sandbox), so the deciding tests are not identified. |
| S7 | C2 | As above; expected (not confirmed) that neither failing test is a parsing test. |
| S7 | C3 | As above; expected deciding pair: `security/test_read_methods.py::test_analyst_read_does_not_run_state_changing_method` and `::test_anonymous_read_does_not_run_state_changing_method`. |

**Human review:** confirm from the three deepseek trial directories which two security tests failed (expected the `test_read_methods.py` pair), and confirm that a fix storing non-literal record text as field data is not a correct fix (the parsing tests' "value untouched" assertion depends on that judgment).

GATE_A: READY
NEEDS_HUMAN_REVIEW: YES
