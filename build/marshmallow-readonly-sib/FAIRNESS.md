# marshmallow-readonly-sib: pre-trial fairness and leniency review

Reviewer: independent sub-agent (did not write the tests), 2026-10-16. Inputs: instruction.md, tests/
(security, functional, score.py, test.sh), solution/fix.patch, manifest.json, notes.md, checks/*.patch,
and the pristine/ref/variant trees in ~/.tb-graders/cwe/work/marshmallow-readonly-sib (read and run
locally with Python 3.13, no Docker). Hidden tests + project suite on ref: 1209 passed.

## 1. Per-test fairness

| test | asserts | instruction basis | correct fix can fail? | risk |
|---|---|---|---|---|
| security::test_enclosing_declaration_keeps_nested_schema_options | enclosing dotted `member.joined` must not cancel nested class's Meta `approved` | the example itself; "Declarations add up" | no | low |
| security::test_constructor_declaration_keeps_schema_options_read_only | `MemberSchema(dump_only=("joined",))` still refuses Meta-read-only `approved` | "as arguments when a schema is created"; "Declarations add up ... in any place, never lifts a declaration made elsewhere" | no. A fix that keeps `or` but merges at binding (alt_correct_fix) passes. Only a fix whose observable behaviour lets a constructor list lift Meta fails, and the instruction forbids that | low |
| security::test_constructor_declaration_keeps_schema_options_write_only | same, write-only on dump | same + "write-only never appears in dumped output" | no | low |
| security::test_enclosing_read_only_with_nested_schema_object | dotted dump_only honoured for `Nested(obj)` | "by any of the means above and at any depth ... whichever way the input reaches it"; "for every way it can be reached"; the class branch 15 lines below already does it; upstream treats dotted only/exclude into instances as a bug (CHANGELOG #1384) | no | low |
| security::test_enclosing_read_only_with_nested_schema_factory | same for `Nested(lambda: obj)` | same (same code path) | no | low |
| security::test_enclosing_read_only_in_list_of_nested | constructor dotted dump_only into `List(Nested(lambda))` | same | no (only a parent-instead-of-root lookup fails) | low |
| security::test_enclosing_read_only_in_mapping_of_nested | same in `Dict(values=Nested(obj))` | same | no | low |
| security::test_enclosing_write_only_with_nested_schema_object | dotted load_only honoured on dump for `Nested(obj)` | "write-only never appears in dumped output, whichever way the output is produced" | no | low |
| security::test_enclosing_read_only_field_with_data_key | attacker uses data_key spelling; value must not load | "handled exactly as the library already handles input for an ordinary read-only field": a dump_only field with data_key already rejects its data_key as unknown (checked on pristine). Standard expert knowledge: dump_only names are field names. "whichever way the input reaches it" is not needed for fairness | no. Any fix that marks the field read-only passes; only key-stripping (filter_by_name) fails | low |
| security::test_enclosing_declaration_keeps_nested_object_own_declarations | object's own constructor dump_only survives the enclosing one | "Declarations add up" | no | low |
| functional::test_unrestricted_nesting_binds_everything | all four nesting forms load unchanged | "Everything else loads and dumps exactly as it does today" | no | low |
| functional::test_enclosing_read_only_still_restricts_and_siblings_bind | class route unchanged; refusal is ValidationError | same + "by default a validation error" (pristine behaviour) | no | low |
| functional::test_restricted_nested_object_other_fields_bind_and_dump[factory,object] | other fields load; write-only loads; read-only dumps | "read-only fields are still dumped and write-only fields are still loaded" | no | low |
| functional::test_shared_schema_object_keeps_its_own_behaviour_elsewhere | T3: shared object unaffected elsewhere and standalone | "keeps behaving exactly as its own declarations say wherever else it is used, on its own or inside other schemas"; also "Everything else ... as it does today"; standard expert knowledge: a fix must not mutate shared state | no | low |
| functional::test_shared_schema_object_under_two_different_restrictions | T3 under two restriction sets, both directions | same | no | low |
| functional::test_schema_options_and_constructor_declarations_still_restrict | Meta and constructor restrictions still work alone | "Keep legitimate use working" | no | low |
| functional::test_exclude_unknown_drops_restricted_input_silently | EXCLUDE drops restricted input (class route) | "dropped when unknown fields are excluded" | no | low |
| functional::test_list_of_restricted_nested_objects_binds_visible_fields | List route: visible fields load, read-only dumps | "Everything else ..." | no | low |

No test can fail a correct fix. Extra questions:

- **Q3 (data_key):** fair, low risk (see the row above).
- **Q4 (`or` to union):** fair. Today `S(dump_only=("b",))` on a schema with Meta `dump_only=("a",)` loads `a` (checked). The instruction's "Declarations add up ... in any place, never lifts a declaration made elsewhere" removes that behaviour explicitly. A fix that keeps `self.dump_only` as a replacement but honours Meta at binding (alt_correct_fix) passes. No project test relies on replacement.

## 2. Leniency

| property / trap | most plausible wrong fix | caught by |
|---|---|---|
| T0 example | none (the fix is one line) | test_enclosing_declaration_keeps_nested_schema_options |
| T0b direct constructor | merge only where Nested builds the class | constructor_* tests; merge_in_nested_only.patch |
| T1 schema object / factory | fix only the reported example | 7 T1 tests; example_merge_only.patch |
| T1 containers | read options from `self.parent` | list/mapping tests; options_from_parent.patch |
| direction | read-only only | write_only tests; read_only_direction_only.patch |
| identity | strip input keys by name | data_key test; filter_by_name.patch |
| own declarations | replace instead of union | keeps_nested_object_own_declarations; nested_overwrites_own.patch |
| T3 | mark fields on the shallow copy | both shared_* tests; nested_no_private_copy.patch |
| refusal shape | lock all fields / raise ValueError | functional; lock_whole_nested / crash_on_nested_object |

Wrong fixes that no test catches:

1. **Depth 2 or more through a schema object (MEDIUM, required change).** The instruction says "at any depth". `Outer.Meta.dump_only = ("member.lead.tier",)` with `member = Nested(T())` and `T.lead = Nested(P)` still loads `tier` on pristine, **on the reference and on alt_correct_fix** (checked; the class route refuses it). The cause is that `Field._bind_to_schema` keeps the first binding (`self.parent = self.parent or parent`, the same for root), so the copied fields keep the original object as root. So the reference does not meet its own instruction. Every fix that misses this passes.
2. Re-instantiating `type(obj)(...)` instead of copying drops the object's own `unknown`, `many`, `only`, `partial` when a restriction applies. This is a functional regression that no test catches (LOW-MEDIUM).
3. Silently dropping instead of raising ValidationError on the object route passes (tests accept both), although the instruction says "by default a validation error" (LOW).

## 3. Hints

- "Our schemas are nested inside one another and reused across endpoints." Mild T3 context. Acceptable.
- "The schema it encloses keeps behaving exactly as its own declarations say wherever else it is used, on its own or inside other schemas." This paraphrases T3 (Q2). It is a behavioural requirement and does not name the mechanism (shallow copy, shared field objects), so it is fair and not a cheat. T3 would stay fair without it ("Everything else ... as it does today" plus the expert rule against mutating shared state). Optional, harder wording: "A declaration made by an enclosing schema applies only within that enclosing schema."
- "Declarations add up ... never lifts a declaration made elsewhere." This states the T0 fix outcome. Keep it: the constructor tests need it (Q4).
- "whichever way the input reaches it" / "whichever way the output is produced" / "This is one example, not the whole problem". These are generic route hints and name no route. Acceptable.
- No file, function, flaw count or nesting-form list is named. The leak_terms (instance, lambda, data_key, fields.List/Dict, ...) are absent from the instruction (checked by reading).

## 4. Realism

- T1, T3 and T0b are unmodified upstream code (Dockerfile checks out the pinned commit) and are reached through `Schema.load` and `Schema.dump`.
- The Nested docstring's own examples use `Nested(lambda: ParentSchema(only=...))` and `Nested(ChildSchema(...))`, so the object routes are mainstream. Nothing is planted.
- **Q1 (legitimacy):** yes, a reasonable maintainer would accept this as a security bug and not a feature request:
  - dump_only and load_only are documented as read-only and write-only for web APIs (quickstart.rst "Read-only and write-only fields").
  - Dotted names for them are a documented feature (CHANGELOG #572) with upstream tests (TestDeeplyNestedLoadOnly).
  - Silently ignoring them for instances is the same defect upstream already fixed for dotted only/exclude (#1384).
  - The failure is fail-open, with no error and no warning.
  - The Nested docstring's "pass a class (not an instance)" concerns Nested's own `only`/`exclude` arguments, not the enclosing schema's declarations.
  - T0 (a parent's declaration silently cancels the child's Meta list, while `exclude` on the line above uses `|`) is an evident bug.
  - Expect "security-relevant bug" rather than CVE-grade severity. CWE-915 fits.
- **Q2:** the hint is acceptable (see section 3). It is what makes T3 fair, and it names no mechanism.

## 5. Verdict: NOT READY (one required change)

Required, choose one:

- **A (preferred).** Make the reference meet "at any depth" through schema objects, and add a security test, for example `Outer(Meta dump_only=("member.lead.tier",))` with `member = Nested(TObj)` and `TObj.lead = Nested(P)`, run both cold and after `TObj` has been used once. A sketch I checked: after the reference's `deepcopy(declared_fields)`, reset `parent`/`root` on each copied field and `_schema = None` on Nested fields. That passes the depth-2 case cold and warm, plus all 1209 hidden and project tests. Containers (List/Tuple inner fields) inside the object also keep their old binding and need the same treatment. Re-run the patch checks afterwards.
- **B.** Narrow the instruction so it does not promise depth through objects. This is weaker, because "at any depth" is already true on the class route and removing it signals something.

Recommended: a functional test showing that an object's own `unknown=EXCLUDE` (and `many`) survive an enclosing restriction (leniency item 2).

## 2026-10-16T13:09Z lead: required change applied before any trial
Fix A done by the builder (reference unbinds copied fields at any depth; 2 depth-2 security tests;
2 functional tests incl. object keeps its own unknown/many/only; checks miss_depth (security_fail) and
rebuild_from_class (functional_fail)). Blind patch still 1.0. Instruction unchanged. Verdict now READY.
