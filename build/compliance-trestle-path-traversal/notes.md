# compliance-trestle-path-traversal: build notes

Start (UTC): 2026-10-17T04:31:49Z  (build session began 2026-10-17T04:31:54Z)
End (UTC): 2026-10-17T06:19:47Z

## Levers
- T1 (A) shared name check, file_utils.py:95-122: component-generate -o and docs/folders setup task names; dismiss: report lands on catalog-generate, the check looks like a naming rule.
- T2 (A) create.py:95 / replicate.py:90: model commands writing into another trestle workspace; dismiss: model management, and a plain outside path is already refused.
- T3 (B) import_.py:81-84: import -o; dismiss: import reads external content, untouched by the published fix.
- T4 (B, producer off the check's path) model_utils.py:635-648 save-by-name mapper used by catalog/component-assemble, profile-resolve, ssp-assemble; dismiss: a model name is not a path.
- T5 (B) component.py:63-77: --force-overwrite clears before the name check; dismiss: opt-in flag, and the command already checks the name.
- Coupled: nested names stay valid; workspace-wide headers validation must still examine root folders (helper sees relative paths); reserved names still refused.

## Verified
- Pinned 0f82d19 is the sole parent of fix 37ed44f5; the regression-test additions in fs_test.py are absent at the pinned commit.
- Every security testcase fails on the pinned image by its side-effect assertion (26/26). Assemble routes delete the outside directory.
- create/replicate/import refuse targets in no trestle project (CreatePathAction) but write into any other trestle project; tests use a sibling workspace.
- Absolute -o on the mapper route stays inside the workspace (string prefix join), so it is not tested there.
- The project area tests pass offline at the pinned commit except 7 network tests (deselected). Full suite: same 29 network failures on pinned and oracle.
- T3/T4/T5 are still open in upstream HEAD a92c5955 (2026-10-15): no workspace check in import_.py, model_utils.py or component-assemble/generate.

## Not verified
- Whether a public upstream report exists for T3-T5 (no search done).
- profile-assemble, ssp-filter and profile-inherit -o go through the same mapper. The oracle closes them, but no test covers them.
- Symlink-based escapes are not tested (outside this advisory's spelled-name scope).

## Out of scope (one line each)
- -n input names of replicate/catalog/profile are read-side traversal.
- clear_folder on generate -fo resolves relative to the cwd, not trestle_root.

## Gate
static: only blind patch + FAIRNESS.md missing (expected). nop PASSED. oracle PASSED (3 runs). patches PASSED (second run; first died on a Docker network pruned by a concurrent gate).

## Fairness revision (2026-10-17)
- Outside fixtures renamed to <tmp>/ws-outside and <tmp>/ws-neighbour (workspace name as prefix); resolved_prefix.patch (resolve + startswith, no separator) added, expect security_fail.
- New security tests on the remaining mapper routes: profile-assemble, ssp-filter, profile-inherit -o; call_sites_only.patch (checks at the four previously tested call sites only) added, expect security_fail.
- New security tests: profile-generate and ssp-generate -o <outside> -fo.
- instruction.md: boundary sentence no longer mentions another workspace; reserved-names bullet reworded neutrally.
