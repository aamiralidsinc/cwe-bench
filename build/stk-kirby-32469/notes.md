# stk-kirby-32469 — build notes

- Start (UTC): 2026-10-26T02:22:07Z
- End (UTC): 2026-10-26T04:40Z (main task gate complete; control gate ran afterwards)

## Task

Kirby (getkirby/kirby), pinned at `58f819988436b31969078bc4655452dd48546451`, the direct parent of the
published fix `37e206f3ed40ad3fab2e47e055ccb19e9c207dab` ("API upload pre-flight + ensure same template").
Pattern A+B / stacked H4. Entry point: the real API routes through `Kirby\Cms\Api::render`; the tests
acknowledge PHP's `move_uploaded_file` limitation with a namespaced stand-in (the project's own suites
already stub `ini_get`/`ini_set` the same way).

## Levers (one line each)

- T1 (deepseek, advisory route): authorization is absent where the create route stages the first part of an upload; the commit-time rule already refuses the finished file, so the early write reads as an ordering detail. `src/Api/Upload.php:156,181,221,246,334`, `config/api/routes/files.php:44-61`.
- T2 (mimo, published-fix far site): for field uploads the declared file type exists only as the `Api::upload(template:)` argument, so a check written against the request body silently judges the default type. `src/Api/Upload.php:243`, `config/fields/mixins/upload.php:82`.
- T5 (mimo, folded into the T1/T2 fix site): the decision must use a File built from the parent and the declared type because the type's options block takes priority over the role. `src/Cms/ModelPermissions.php:93-119`.
- T3 (deepseek, advisory route): the replace route is the same uploader with a different action and target; the commit-time replace rule makes the early write look covered. `config/api/routes/files.php:110-118`.
- T4 (both, advisory route): the avatar route targets an account; the decision is account update, and self vs other are different permission categories. `config/api/routes/users.php:88-102`.
- T6 (mimo, published-fix far site): nothing pins the declared file type and total length of a multi-request upload, so a later request substitutes them and the completing request's values reach the create. `src/Api/Upload.php:230-259,347-409`.
- T7 (deepseek, uncovered upstream route): chunk-time name validation judges the id-prefixed temporary name, so a banned final name passes into staging. `src/Api/Upload.php:234,354-358`. Current upstream (`main` 8a6f4ac1c) still has `filename: basename($tmp)` in `validateChunk`, and the published fix does not touch it.

Concepts: C1={T1,T2,T5} create/field authorization subject; C2={T3} replace; C3={T4} avatar; C4={T6} declaration pinning; C5={T7} final-name validation.

## Verified on this machine (behavioural, in-container)

- Pinned: 8/8 security tests fail; 8/8 functional pass; project suite 138/138 (ApiTest, FileRules, FileReplace, FilePermissions, UserAvatar).
- Reference (`published fix + T7`): 8/8 security, 8/8 functional, 138/138 project.
- Each per-concept miss patch fails only its own concept's security tests and keeps functional green:
  miss-create 5/8 (T1,T2,T5), miss-replace 7/8 (T3), miss-avatar 6/8 (T4), miss-pin 7/8 (T6),
  miss-filename 7/8 (T7).
- `upstream_fix.patch` (source diff of 37e206f alone) fails the T7 security test → the stack adds more
  than upstream shipped.
- Wrong-fix patches behave: refuse-all → functional 0/8; crash-as-refusal → security 2/8 with functional
  8/8; wrong-resource (avatar judged as a file) → security 6/8; one-direction (create only) → 5/8;
  unlisted-route (create route only) → 4/8; check-after-buffer → security 2/8 (side-effect assertion
  catches it); adjacent-api (mandatory hook on the shared helper) → functional 7/8.
- `pass-hardening.patch` and `pass-alt.patch` (route/field-level authorization, no hook in the shared
  uploader) both score full.
- Control task `stk-kirby-32469-control`: pinned 0/4 security, fix 4/4, functionals 8/8 everywhere,
  miss-create 1/4, refuse-all functional 0/8, pass-alt and pass-hardening full.

## Project suite selection

The project's own `tests/Api/UploadTest.php` asserts the pre-fix chunker behaviour and the pinned
`tests/Form/Field/FilesFieldTest.php` overrides `Api::upload` with the 4-argument signature; the published
fix rewrites both (the fix commit changes exactly those expectations/signature). They cannot be graded
against an arbitrary correct fix, so the verifier's project group runs the rule and permission suites
around the uploader (ApiTest, FileRules, FileReplace, FilePermissions, UserAvatar) — 138 tests, green on
pinned and on every correct fix.

## Could not verify / guesses

- The advisory text and GHSA id were not available offline; the reader record's snippets were consistent
  with the pinned code and the published commit, which was available.
- `p_fail3_*` figures are copied from `pipelines/stacking/out/stack_scores_ds.tsv`; no model trials were run.
- Current upstream was inspected at the clone's `main` (`8a6f4ac1c`); whether T7 was ever reported
  publicly is unknown.
- Whether hidden reviewers count the second property as DESCRIBED is unknown; the wording is kept
  general and does not name a route, file or function.

## Gate

- static: PASS
- nop: PASS (security 0/8, functional 146/146)
- oracle: PASS (3/3 runs reward 1.0, identical results)
- patches: PASS (all 15 listed checks behaved as declared)
- control task: static PASS, nop PASS (security 0/4, functional 146/146); oracle/patches were still running at the session boundary

## Scope

- Only this advisory's protection (upload authorization and the declaration that governs it) and its
  in-repo routes were used. Nothing outside the repository was built on.
