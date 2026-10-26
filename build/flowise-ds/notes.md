# flowise-ds build notes

Start (UTC): 2026-10-18T19:12:23Z
End (UTC): 2026-10-18T19:51:47Z

Candidate: flowiseai/flowise, GHSA-CHM3-VQCF-52RX / CVE-2026-70472, CWE-285/863.
Pinned: 700137738bcaebefd4709021f6d6b0abcd7df0ac (verified parent of fix d81483b70c997ddf981acc9c49fbd9a02fa345cd via the GitHub API).
Pattern A+B, track injected.

## Protected sink

A caller-supplied credential id must resolve to a stored Credential owned by the caller's active
workspace, or explicitly shared into it through a WorkspaceShared row of type `credential`, before
the server decrypts the secret and uses it. At the pinned commit the vector-store, assistants and
OAuth2 handlers look the credential up by id alone.

## Levers (one line each)

1. base (A, published): services/openai-assistants-vector-store/index.ts:13 — all 7 routes resolve
   `?credential=` by id alone. Dismiss: obvious.
2. far_site (A, published): routes/oauth2/index.ts:80 — credential in the path, separate OAuth2
   router with inline DB access. Dismiss: another feature/router; report example is a query shape.
3. uncovered_assistants (B, real upstream): services/openai-assistants/index.ts:18,46,87 and the
   third router openai-assistants-file (POST /upload). Dismiss: neighbouring feature, two other
   router names, file helper whose download sibling is public.
4. sibling_credential_test (injected): services/credentials/index.ts:196 — POST /credentials/:id/test,
   path-shape, returns only a status. Dismiss: diagnostic validation in the credential module.
5. sibling_thread (injected): services/openai-assistants/index.ts:118 — POST /openai-assistants/thread,
   body-shape, returns only an opaque id. Dismiss: ephemeral object, no tenant data, body input.

Coupled keep-working behaviour: own-workspace credentials, explicitly shared credentials, API-key
callers, and the existing credential-management API still refusing foreign ids. Extra security
subtleties: a share row of another item type must not count; an authenticated caller with no active
workspace must be refused.

## Tests (hidden)

18 security tests, 14 functional tests. Every test imports the real route file; an express stub
records route registrations and a dispatcher matches method/path, extracts path params, runs
matching router.use middleware, then the real middleware + controller chain. RBAC answers per
permission string. Infrastructure stubbed: in-memory repositories with equality/Equal/In/OR
matching and the common TypeORM methods, credential decryption, OpenAI SDK, running-app singleton,
workspace service, constants/logger/utils barrels, axios/lodash. Security asserts: the foreign
secret is never decrypted and never reaches the provider SDK, and the caller gets a 4xx client
error (next(err) with a 4xx statusCode, or a 4xx response). Functional asserts legitimate use
succeeds with the own/shared secret.

## Verified locally (pinned+injected vs oracle)

- pinned+injected: security 18/18 fail (all because the victim secret is decrypted); functional
  14/14 pass.
- oracle: 18/18 security and 14/14 functional pass.
- hardening (pass): all pass. alt_fix (alternative design using find/find with In): all pass.
- sec_miss_base: 9 security fail, functional pass. sec_miss_oauth2: 2/0. sec_miss_assistants: 3/0.
  sec_miss_thread: 2/0. sec_miss_credtest: 2/0. sec_published_only: 7/0.
  sec_wrong_resource (share lookup ignores itemType): 1/0. sec_missing_authority (fail-open
  without a workspace): 4/0. reads_only (write routes unfixed): 5/0.
- func_overbroad (ownership only, no shares): 2 functional fail. refuse_all: 12 functional fail.
  adjacent_api (credential-management API scoped by id only): 1 functional fail.

## Gate

- static: clean except the two items the pipeline writes later (missing blind pass patch and
  missing build/flowise-ds/FAIRNESS.md).
- nop: PASSED (18 security tests failed on the vulnerable+injected image, 14 functional passed).
- oracle: PASSED, three identical runs at reward 1.0 (18/18 security, 14/14 functional).
  One earlier oracle attempt lost its third trial to a Docker networking race
  ("network ... not found"); the stage was re-run and passed. Infrastructure, not a test result.
- patches: PASSED, all 14 declared checks:
  sec_miss_base 9 security fail / 0 functional; sec_miss_oauth2 2/0; sec_miss_assistants 3/0;
  sec_miss_thread 2/0; sec_miss_credtest 2/0; sec_wrong_resource 1/0; sec_missing_authority 4/0;
  reads_only 5/0; sec_published_only 7/0; func_overbroad 0/2; refuse_all 0/12; adjacent_api 0/1;
  hardening reward 1.0; alt_fix reward 1.0.

Gate reports: build/flowise-ds/gate_report.partial.json (last stage: patches) and the per-stage
logs gate_nop.log, gate_oracle2.log, gate_patches.log.

## Could not verify

- That both target models fail 3/3 attempts: no trials are run while building.
- Current-upstream status of the three real pattern-B routes was checked read-only over the
  network: today the assistants service filters those lookups by workspaceId, so `present_in_latest`
  is `no`.
- The OAuth2 /callback and /refresh handlers are whitelisted as unauthenticated and have no request
  workspace; they are outside this advisory's protection and are not tested or fixed.
- A correct fix written exclusively with a TypeORM query builder would not run against the
  in-memory repository (it models the repository methods the codebase uses for these lookups, not
  query builders).

## Upgrade 2026-10-20 (sibling-injection rules §2–§8)

- instruction.md rewritten: one general property over the stored credential ("loaded, decrypted,
  or used to act with an external provider only if it belongs to the caller's active workspace or
  has been explicitly shared ..."); removed the operation example and the query/path/body shape
  list. Coupled contracts kept (4xx refusal, shares with a type, API-key callers).
- New how-type lever (real upstream, no repo change): services/assistants/index.ts:185. The legacy
  assistants delete handler reads the credential reference from the stored assistant row and looks
  it up by id alone, then decrypts and builds the provider client. It is M6 (a producer no
  request-field check sees) and M4 (protection never existed; the published fix never touches this
  module). The reference is producible through the module's own CUSTOM-create / type-update flow
  because `type` and `credential` are not protected fields.
- Coverage: security/stored_credential_assistant.spec.ts (1) and the coupled functional
  "a workspace can delete an assistant whose stored credential it owns"; checks/
  sec_miss_legacy_assistant.patch is the previous fix (all older levers closed, new one open),
  expect security_fail.
- solution/fix.patch extended: deleteAssistant resolves through resolveCredentialForWorkspace and
  rethrows InternalFlowiseError from both catch layers so the refusal stays a 4xx.
- Counts now 19 security / 15 functional. environment/ unchanged, so the prebuilt image is reused;
  no rebuild.
- Verified manually in the prebuilt image (mounted src trees, jest config + tests from tests/):
  pinned+injected 19/19 security fail + 15/15 functional pass; patched oracle 19/19 + 15/15;
  pre-extension fix (sec_miss_legacy_assistant) 1 security fail + 15/15 functional pass.
