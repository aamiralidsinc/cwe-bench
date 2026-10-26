# FAIRNESS review: compliance-trestle-path-traversal

Reviewer scope: instruction.md, tests/ (security, functional, project copies, test.sh, score.py),
solution/fix.patch, manifest.json, notes.md, checks/*.patch. Nothing was run. The trestle source
(e.g. `PathSecurityValidator.validate_local_path` body) is not in the project tree and was not inspected
beyond what the patches show.

Common harness facts used below: every test runs the real CLI (`python -m trestle`) with cwd = a fresh
`trestle init` workspace `<tmp>/ws`; `assert_refused` requires (a) no path under `<tmp>` outside `ws`
created/changed/deleted and (b) non-zero exit. Any non-zero exit is accepted, so the refusal mechanism
(exception, return code, log) is free.

## 1. Per-test fairness

### Security (26 cases)

| test | asserts | instruction basis | correct fix could fail? | risk |
|---|---|---|---|---|
| test_sec_author_generate.py::test_catalog_generate_output_outside[absolute,nested_parent] | catalog-generate `-o /abs/outside/cat_md` or `-o sub/../../outside/cat_md` refused, nothing outside written | "Observed impact" example; Required behaviour bullet 1 ("whatever its form") | no | low |
| test_sec_author_generate.py::test_catalog_generate_force_overwrite_outside | `-o <outside> -fo` refused, outside dir not cleared | "With `--force-overwrite`, an existing directory ... is deleted first"; bullet 3 "including before the command fails" | no | low |
| test_sec_author_generate.py::test_profile_generate_output_outside[absolute,nested_parent] | same for profile-generate | bullet 1; "one example, not the full set"; "close variants" | no | low |
| test_sec_author_generate.py::test_ssp_generate_output_outside[absolute,nested_parent] | same for ssp-generate | as above | no | low |
| test_sec_task_names.py::test_component_generate_output_outside[absolute,nested_parent] | component-generate `-o` outside refused | bullet 1 ("any trestle command") | no | low |
| test_sec_task_names.py::test_docs_setup_task_outside[absolute,nested_parent] | `author docs setup -tn <outside>` refused, no folder created outside | bullet 1; "a task name such as `policies/access`" makes task names in scope | no | low |
| test_sec_task_names.py::test_folders_setup_task_outside | `author folders setup -tn /abs` refused | as above | no | low |
| test_sec_force_overwrite.py::test_component_generate_force_overwrite_outside[absolute,nested_parent] | component-generate `-o <outside> -fo` refused and the pre-existing outside dir (marker.txt, keep/) survives | bullet 3 "Nothing outside ... removed, including before the command fails" | no | low |
| test_sec_import.py::test_import_output_outside[parent,absolute] | `import -o ../../neighbour/catalogs/imported` (or absolute) refused; neighbour workspace untouched | bullet 2 "including another trestle workspace elsewhere on disk" | no (sentence is what makes it fair) | low |
| test_sec_model_commands.py::test_create_output_outside[parent,nested_parent,absolute] | `create -o` into neighbour workspace refused | bullet 2 | no | low |
| test_sec_model_commands.py::test_replicate_output_outside[parent,absolute] | `replicate -o` into neighbour workspace refused | bullet 2 | no | low |
| test_sec_assemble.py::test_catalog_assemble_output_outside[parent,nested_parent] | catalog-assemble `-o ../../outside` refused; outside dir not rmtree'd | bullet 1 ("something it produces or replaces"); bullet 3 | no | low |
| test_sec_assemble.py::test_component_assemble_output_outside | same, component-assemble | as above | no | low |
| test_sec_assemble.py::test_profile_resolve_output_outside | profile-resolve `-o ../../outside/resolved` refused | as above | no | low |
| test_sec_assemble.py::test_ssp_assemble_output_outside | ssp-assemble `-o` outside refused | as above | no | low |

Note: assemble tests use only `..` spellings, consistent with notes ("absolute -o on the mapper lands
inside the workspace"); a fix that also refuses absolute names there is not penalised.

### Functional (hidden, 14 cases)

| test | asserts | instruction basis | correct fix could fail? | risk |
|---|---|---|---|---|
| test_func_tasks.py::test_docs_setup_nested_task | `-tn policies/access` works | "a task name such as `policies/access`" | no | low |
| test_func_tasks.py::test_folders_setup_nested_task | `-tn architecture/diagrams` works | "nested ones" | no | low |
| test_func_tasks.py::test_reserved_task_name_still_refused | `-tn catalogs` still fails | "existing rules that refuse reserved names" | no | low |
| test_func_tasks.py::test_headers_validate_whole_workspace | `headers validate --global -r` still reports a bad header in a root folder | "Validating governed documents across the whole workspace without naming a task"; visible headers_test::test_exclude_global | maybe: a fix hardening the shared name check against absolute paths silently breaks this caller; the bullet and the visible project test both warn, so fair | low |
| test_func_models.py::test_create_replicate_import / test_import_named | plain names still work, nothing outside written | "Keep legitimate use working" | no | low |
| test_func_models.py::test_catalog_assemble_overwrites_own_output | re-assemble to same name replaces own output | bullet "re-running a command so that it replaces its own earlier result" | no | low |
| test_func_models.py::test_profile_resolve | plain resolve works | legitimate use | no | low |
| test_func_generate.py::test_catalog_generate_nested_output | `-o markdown/catalogs/nist` works | quoted verbatim in instruction | no | low |
| test_func_generate.py::test_catalog_generate_force_overwrite_inside | `-fo` inside clears stale file | "`--force-overwrite` on a folder inside the workspace" | no | low |
| test_func_generate.py::test_profile_generate_and_assemble / test_ssp_generate_and_assemble / test_component_generate_and_assemble | nested md dirs + assemble work | legitimate use | no | low |
| test_func_generate.py::test_component_generate_nested_and_force_overwrite | nested `-o md/components` with `-fo` works and regenerates the same files | `--force-overwrite` inside bullet | no (a fix that refuses separators fails, correctly: no_separators.patch) | low |

### Project tests (pristine copies, 11 files, 7 network tests deselected)
Visible to the solver in the repo; "The project's existing test suite" bullet. fs_test::test_allowed_task_name
pins current behaviour (`task/name` allowed, `hello.world` refused) and does not forbid adding absolute/`..`
refusals. Risk low.

No test requires refusing an inner `..` that stays inside the workspace, nor accepting an absolute path that
stays inside; both designs pass. No unfairness found.

## 2. Leniency

| property / trap | most plausible wrong fix | caught? |
|---|---|---|
| landing (generate -o) | lexical-only check on `parts[0] == '..'` / unresolved prefix | yes: nested_parent cases; prefix_check.patch |
| T1 shared name check | fix only the three generate commands | yes: test_component_generate_output_outside, test_docs_setup_task_outside; generate_only.patch, no_helper.patch |
| T1 coupled | harden helper, leave headers caller passing absolute paths | yes (functional): test_headers_validate_whole_workspace; headers_not_adapted.patch |
| T2 create/replicate | trust existing "in a trestle project" check | yes: test_create/replicate_output_outside; no_create_replicate.patch |
| T3 import | fix create/replicate only | yes: test_import_output_outside; no_import.patch, published_fix_only.patch |
| T4 save-by-name mapper | validate only on lookup, or validate the model-type dir | yes: test_sec_assemble.py; reads_only.patch, wrong_resource.patch, no_mapper.patch |
| T5 clear before check | keep `-fo` clear ahead of the check | yes: test_component_generate_force_overwrite_outside; check_after_clear.patch |
| over-hardening | refuse separators / everything | yes (functional): no_separators.patch, refuse_all.patch |

**Wrong fixes no test catches**
1. **String-prefix check without a separator (medium).** `str(p.resolve()).startswith(str(root.resolve()))`
   is the textbook wrong fix and passes all 26 tests, because no outside target shares the workspace's name
   prefix (`ws` vs `outside`, `neighbour`). Under that check `<tmp>/ws-evil` counts as inside.
   prefix_check.patch is caught only because it also skips `resolve()`.
2. **Per-call-site checks in the four tested assemble/resolve commands instead of the mapper (medium).**
   `profile-assemble -o`, `ssp-filter -o` and `profile-inherit -o` use the same mapper (notes, "Not verified")
   but have no security test. A fix that adds checks in catalog/component-assemble, profile-resolve and
   ssp-assemble only passes and leaves three write-and-rmtree routes open.
3. profile-generate / ssp-generate `-fo` outside: not tested (only catalog -fo). A fix that validates after
   `clear_folder` in those two passes. Low-medium.
4. Symlink escapes (a workspace symlink to outside): not tested; notes scope them out. The phrase "whatever its
   form" could cover them, but leaving them untested is lenient, not unfair. Low.
5. `headers setup -tn`, `folders setup` with `..`: not tested separately; same helper as docs. Low.

## 3. Hints

| quote | concern | proposed wording |
|---|---|---|
| "Any other location counts as outside, including another trestle workspace elsewhere on disk, for example one next to it." | Paraphrases the T2/T3 dismissal reason (existing "in a trestle project" check) and the test layout (sibling workspace; leak terms "sibling", "neighbouring workspace"). | "Any location not inside that workspace counts as outside, whatever it contains." (Medium. This still makes T2/T3 fair: a trestle project elsewhere is still not inside the workspace.) |
| "With `--force-overwrite`, an existing directory at that location is deleted first." + "including before the command fails" | Points at check-after-clear (T5). | Acceptable: it describes observed impact and the requirement, and T5 needs it for fairness. Keep. Low. |
| "The existing rules that refuse reserved names, such as a task named after a model folder." | Points the solver at the task-name rule (the shared helper, T1). | "Names that trestle refuses today must still be refused." The visible fs_test::test_allowed_task_name already guarantees fairness. Medium-low. |
| "Validating governed documents across the whole workspace without naming a task." | Paraphrases the coupled headers caller (adjacent_api). | Keep: without it, test_headers_validate_whole_workspace would rest only on the visible project test. Low. |
| "a task name such as `policies/access`" | Says task names are in scope (T1 docs/folders route). | Keep: this is a legitimate-use example. Low. |

No file, function, flaw count or variant list is named. Leak terms (import, assemble, `-tn`, headers, ...)
do not appear.

## 4. Realism
All five traps are real upstream code at the pinned commit. T1/T2 were changed by the published fix. T3/T4/T5
are unmodified and still open upstream at HEAD per notes. Each is reached through the real CLI with an ordinary
`-o`/`-tn` argument. The neighbour-workspace and pre-populated outside-directory fixtures are realistic (CI
checkouts side by side). The tests plant no code. Nothing looks contrived.

## 5. Verdict: NOT READY

Required changes (all cheap, none weakens fairness):
1. **Tighten (prefix):** name an outside target with the workspace's name as a prefix, e.g. move the
   `neighbour` fixture to `<tmp>/ws-neighbour` (or `ws2`) and/or add a generate case targeting `<tmp>/ws-out`.
   Re-run the oracle, hardening and alt patches to confirm they still pass (oracle relies on
   `validate_local_path`, whose body I did not inspect). Then add a check patch `resolved_prefix.patch`
   (resolve + startswith, no separator), expected security_fail.
2. **Tighten (mapper routes):** add security tests for `author profile-assemble -o ../../outside` (and
   preferably `ssp-filter -o` and `profile-inherit -o`), plus a check patch that adds checks only at the four
   currently tested call sites, expected security_fail.
3. **Instruction:** replace "Any other location counts as outside, including another trestle workspace
   elsewhere on disk, for example one next to it." with "Any location not inside that workspace counts as
   outside, whatever it contains." Optionally reword the reserved-names bullet as in section 3.
4. Optional: add `-fo` outside cases for profile-generate and ssp-generate.
