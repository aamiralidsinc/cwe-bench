# flowise-ds pre-trial fairness review

Reviewed: `tasks/flowise-ds/instruction.md`, all six security specs, the functional spec, the harness and its stubs, `solution/fix.patch`, `build/flowise-ds/manifest.json`, `notes.md`, and all fifteen `checks/*.patch`. Nothing was run. The solver sees only the instruction and the repository.

**Legend.**
- **P** = "A stored credential may be loaded, decrypted, or used to act with an external provider only if it belongs to the caller's active workspace, or the owning workspace has explicitly shared it into that workspace for this purpose. This applies to every request that can reach a stored credential."
- **NW** = "If a request's caller is authenticated but has no active workspace, no stored credential may be loaded or used."
- **R** = "respond with a client error and perform no side effect. The foreign secret is never decrypted and never used to contact the external provider. No specific status code or message is required."
- **PR** = "must succeed exactly as before", including the shared-credential clause.
- **S** = "The property applies both to interactive sessions and to callers authenticated by an API key."

The tests drive the real leaf router: `router.use` middleware, the controller and the service are all exercised. A correct guard in any of those layers runs, and any 4xx refusal form (thrown `statusCode`, `status`, or `res.status()`+json) is accepted. A guard placed after decryption is not correct under R (the secret must never be decrypted). A parent-router/app-level-only guard is outside the imported chain; that is an implementation-shape risk, not the instruction's primary mechanism (see Human review). All "No" entries assume the natural fix resolves the credential with the repository methods this codebase already uses (`findOneBy`/`find`/`findBy`; `alt_fix.patch` proves `find`+`In`). A `createQueryBuilder`-only fix is not modelled by the stub (see Human review).

## 1. Test-by-test fairness

| test (file::name) | asserts | fair because | could a correct fix fail? | risk |
|---|---|---|---|---|
| base_vector_store.spec.ts::cross-tenant read of a vector store does not use the foreign credential | GET `/vs_1` with victim credential; no victim decrypt, no victim provider key, 4xx | P (load/decrypt/use) + R | No — sink-level scope check refuses before decrypt; any 4xx accepted | low |
| base_vector_store.spec.ts::cross-tenant listing of vector stores does not use the foreign credential | GET `/` with victim credential; same | P + R | No — same | low |
| base_vector_store.spec.ts::cross-tenant creation of a vector store does not use the foreign credential | POST `/` with victim credential; same | P + R | No — same | low |
| base_vector_store.spec.ts::cross-tenant update of a vector store does not use the foreign credential | PUT `/vs_1`; same | P + R | No — same | low |
| base_vector_store.spec.ts::cross-tenant deletion of a vector store does not use the foreign credential | DELETE `/vs_1`; same | P + R | No — same | low |
| base_vector_store.spec.ts::cross-tenant file upload to a vector store does not use the foreign credential | POST `/vs_1` with empty files; same | P + R | No — same | low |
| base_vector_store.spec.ts::cross-tenant file deletion from a vector store does not use the foreign credential | PATCH `/vs_1`; same | P + R | No — same | low |
| base_vector_store.spec.ts::a share recorded for another kind of resource does not authorise a credential | chatflow-typed share does not authorise; no decrypt, 4xx | P ("for this purpose") + PR's typed-share sentence | No — a type-aware share lookup refuses | low |
| base_vector_store.spec.ts::a caller with no active workspace cannot use a named credential | user with no `activeWorkspaceId`; no decrypt, 4xx | NW + R | No — explicit rule | low |
| oauth2_authorize.spec.ts::cross-tenant OAuth authorisation does not use the foreign credential | POST `/authorize/cred_victim`; no decrypt, 4xx | P (decrypt is itself gated; reference shape is irrelevant) + R | No — sink resolves and refuses; path-shaped input does not change the outcome | low |
| oauth2_authorize.spec.ts::a caller with no active workspace cannot start OAuth with a named credential | no workspace; no decrypt, 4xx | NW + R | No — explicit rule | low |
| uncovered_assistants.spec.ts::cross-tenant listing of assistants does not use the foreign credential | GET `/` with victim credential; no decrypt/provider key, 4xx | P ("every request that can reach") + R | No — same sink check | low |
| uncovered_assistants.spec.ts::cross-tenant read of a single assistant does not use the foreign credential | GET `/asst_1`; same | P + R | No — same | low |
| uncovered_assistants.spec.ts::cross-tenant assistant file upload does not use the foreign credential | POST `/upload/`; same | P + R | No — same | low |
| sibling_credential_test.spec.ts::cross-tenant credential connection test does not use the foreign credential | POST `/cred_victim/test`; no decrypt/provider use, 4xx | P (decrypt/use) + R | No — same sink check; returning only a status does not exempt it | low |
| sibling_credential_test.spec.ts::a caller with no active workspace cannot test a named credential | no workspace; no decrypt, 4xx | NW + R | No — explicit rule | low |
| sibling_thread.spec.ts::cross-tenant thread creation does not use the foreign credential | POST `/thread`, body credential; no decrypt/provider key, 4xx | P (body-carried reference is still a load/use) + R | No — same | low |
| sibling_thread.spec.ts::a caller with no active workspace cannot create a thread with a named credential | no workspace; no decrypt, 4xx | NW + R | No — explicit rule | low |
| stored_credential_assistant.spec.ts::a credential recorded on an assistant row is not used across tenants | DELETE `/asst_1`; no victim decrypt/provider key, 4xx, assistant row still present | P ("every request that can reach a stored credential"; provenance not restricted) + R's "no side effect" | No — a resolution-sink guard sees the stored reference; a request-field-only guard is a wrong fix, not a correct one | medium |
| legitimate_use.spec.ts::a workspace can read its own vector store | 200, own secret decrypted and used | PR | No — own workspace resolves | low |
| legitimate_use.spec.ts::a workspace can list its own vector stores | 200, own secret decrypted | PR | No — same | low |
| legitimate_use.spec.ts::a workspace can create, update and delete a vector store with its own credential | 200 on all three; own secret decrypted | PR | No — same | low |
| legitimate_use.spec.ts::a workspace can upload files to and delete files from a vector store with its own credential | 200 on both; own secret decrypted | PR | No — same | low |
| legitimate_use.spec.ts::a credential shared into the caller workspace still resolves for vector stores | credential-typed share to caller; 200, shared secret decrypted | PR shared clause | No — correct share lookup retains it | low |
| legitimate_use.spec.ts::a workspace can list and read assistants with its own credential | 200 on both; own secret decrypted | PR | No — own workspace resolves | low |
| legitimate_use.spec.ts::a workspace can upload assistant files with its own credential | 200; own secret decrypted | PR | No — same | low |
| legitimate_use.spec.ts::a credential shared into the caller workspace still resolves for assistants | credential-typed share to caller; 200, shared secret decrypted | PR shared clause | No — same | low |
| legitimate_use.spec.ts::a workspace can start OAuth with its own credential | 200/json; own secret decrypted | PR | No — own workspace resolves | low |
| legitimate_use.spec.ts::a workspace can test its own credential | 200; own secret decrypted and provider used | PR | No — own workspace resolves | low |
| legitimate_use.spec.ts::a workspace can create a thread with its own credential | 200; own secret decrypted and provider used | PR | No — own workspace resolves | low |
| legitimate_use.spec.ts::a workspace can delete an assistant whose stored credential it owns | DELETE; 200; own secret decrypted and provider used | PR | No — stored reference resolves to the caller's own credential | low |
| legitimate_use.spec.ts::an API-key caller can use its own workspace credential | API-key user with active workspace; 200, own secret decrypted | S | No — the requirement is explicitly stated; a session-id-only check would be a wrong fix | low |
| legitimate_use.spec.ts::the credential management API still returns an owned credential | GET `/cred_own`; 200/json, own secret decrypted | PR | No — unchanged legitimate path | low |
| legitimate_use.spec.ts::the credential management API still refuses another workspace credential | GET `/cred_foreign`; no foreign decrypt, error or 4xx | P + R + PR ("exactly as before") | No — existing refusal preserved | low |

## 2. Leniency (quality; non-blocking)

### Trap-by-trap: most plausible wrong fix and whether a test catches it

- **base**: "fix the read/list path only" — caught by the five write-route security tests (create/update/delete/upload/delete-files) and `checks/reads_only.patch` (5 security fails); "ownership only, forget shares" — caught by the two shared-credential functional tests and `checks/func_overbroad.patch` (2 functional fails); `checks/sec_miss_base.patch` fails all 9.
- **far_site_oauth**: "fix only query-shaped references; a path segment in a separate router is another feature" — caught by both `oauth2_authorize.spec.ts` tests; `checks/sec_miss_oauth2.patch` (2 fails).
- **uncovered_assistants**: "fix only the module the report points at; the file router is a storage helper" — caught by the three `uncovered_assistants.spec.ts` tests; `checks/sec_published_only.patch` (7 security fails across uncovered, credtest and thread).
- **sibling_credential_test**: "a connection test is configuration validation and returns only a status, not tenant data" — caught by both `sibling_credential_test.spec.ts` tests; `checks/sec_miss_credtest.patch` (2 fails).
- **sibling_thread**: "ephemeral object, no tenant data, body-shaped input" — caught by both `sibling_thread.spec.ts` tests; `checks/sec_miss_thread.patch` (2 fails).
- **stored_assistant_credential**: "check the credential fields of the request; the reference is trusted stored state" — caught by `stored_credential_assistant.spec.ts::a credential recorded on an assistant row is not used across tenants`; `checks/sec_miss_legacy_assistant.patch` (1 security fail).

### Property-by-property

- **Workspace scope**: reads-only and request-field-only are caught as above; scoping by organization instead of workspace breaks the own-use functional tests (the seeded credential has a `workspaceId`, no organization id) — caught.
- **Typed share**: ignoring `itemType` is caught by `base_vector_store.spec.ts::a share recorded for another kind of resource does not authorise a credential`; `checks/sec_wrong_resource.patch`.
- **No active workspace**: failing open when `activeWorkspaceId` is absent is caught by the four no-workspace tests (base, OAuth, credtest, thread); `checks/sec_missing_authority.patch` (4 fails).
- **Refusal form / no side effect**: a crash or a wrapped 500, or a 200 with empty data, fails `expectBlocked`'s 400–499 requirement; refusing everything fails 12 functional tests (`checks/refuse_all.patch`); loosening the existing credential API fails `the credential management API still refuses another workspace credential` (`checks/adjacent_api.patch`). The manifest's n/a items hold: there is no role/direction dimension, credential ids are opaque exact-match strings, and a 500 cannot pass.
- **Sessions / API key**: requiring an interactive user id (rather than the request's active workspace) is caught by `an API-key caller can use its own workspace credential`.

### Wrong fixes no test catches

1. Share lookup checks `itemType` + `sharedItemId` but drops `workspaceId`: a credential shared to *any other* workspace authorises the caller. No test seeds a share whose `workspaceId` is a third workspace.
2. Share lookup checks `workspaceId` + `itemType` but drops `sharedItemId`: any credential share in the caller's workspace authorises every credential id. No test seeds a share for a different credential id.
3. Shares honoured only on reads: the only shared-credential functional tests are a vector-store read and an assistants list. A fix that allows shares for GETs but requires ownership for vector-store create/update/delete/upload/file-delete, thread creation, OAuth authorise, credential test and legacy assistant delete passes every test, although PR says shared credentials "must succeed exactly as before" without a read/write distinction.
4. The share-type negative exists only on the vector-store route. A fix that ignores `itemType` on the assistants, file, OAuth, credtest, thread or legacy routes passes.
5. No no-active-workspace security test on the assistants/file routes or the legacy assistant delete. A route-specific fail-open there is not caught.
6. The OAuth2 `/callback` and `/refresh` handlers are real, unauthenticated routes that load a stored credential with no request workspace. They are untested and unfixed, so a fix that leaves them unscoped passes. This is a coverage gap, not a claim that they are beyond the property: P, read literally, covers them.
7. Only the stored-assistant test asserts "no side effect" on the refused operation. The vector-store write refusals assert no provider key, which excludes the provider side effect, but not a local database side effect before refusal; the real services resolve the credential first, so this is minor.

## 3. Hints (quality; non-blocking)

- "Sharing is an existing mechanism with a type: a share recorded for a different kind of resource is not a credential share." Names the mechanism, the field and the type check, and exists to cover the wrong-resource trap. Neutral: delete it; the property's "explicitly shared it into that workspace for this purpose" (tightened to "for use as a credential") already states it. (Also in 3a.)
- "A fix that only checks direct ownership and forgets shared credentials would break legitimate use." Names a specific wrong fix and pre-warns it. Neutral: delete; PR's first sentence already requires shared credentials to succeed exactly as before.
- "Sessions. The property applies both to interactive sessions and to callers authenticated by an API key." Names two authentication channels/entry points. Neutral: "The property applies to every authenticated caller." (Also in 3a.)
- "When a request would reach a credential the caller is not entitled to — or the caller has no active workspace — ..." Restates the specific no-workspace state that one wrong fix exploits. Neutral: drop the parenthetical; the NW sentence above is the general rule.
- "Fix the flaw and its close variants, not just a single path." Signposts that several sites exist. Neutral: rely on "This applies to every request that can reach a stored credential"; keep only the preservation constraints.
- "the server resolves a stored credential ..., decrypts it, and uses it to contact the external provider" paraphrases the vulnerable stages, but it is the observed-impact description and does not name a file, route or module. Acceptable as written.

## 3a. Surface descriptions — Required: generalize

The instruction is route-neutral: it does not name vector stores, assistants, files, threads, OAuth, the credential module, a request field, a function or a file. Two sentences still describe a channel or a mechanism that exists to cover one lever/trap and should be stated once as the general property:

1. "Sessions. The property applies both to interactive sessions and to callers authenticated by an API key." — names two entry channels. General rewording: **"The property applies to every authenticated caller, however the request was authenticated."**
2. "Sharing is an existing mechanism with a type: a share recorded for a different kind of resource is not a credential share." — names the sharing mechanism and its type field, and exists to cover the share-type trap. General rewording: fold it into P: **"…or the owning workspace has explicitly shared it into the caller's workspace for use as a credential."**

No sentence describing where a sibling, far site or uncovered route lives was found. (The "Observed impact" paragraph is a property-level description, not a route description, and is not listed here.)

## 4. Realism (quality; non-blocking)

- **base**: real upstream service/controller; all seven vector-store routes do the unscoped `findOneBy({id})`. Realistic.
- **far_site_oauth**: real upstream `routes/oauth2/index.ts` with inline DB access and the id in the path; reachable via `POST /api/v1/oauth2/authorize/:credentialId`. Realistic.
- **uncovered_assistants**: real, unmodified upstream code in the assistants service and the third `openai-assistants-file` router; reachable via `GET /openai-assistants`, `GET /openai-assistants/:id` and `POST /openai-assistants-file/upload`. Realistic by definition; not flagged as outside the advisory.
- **sibling_credential_test**: injected, but it is the module's own lookup→decrypt→provider pattern in a "test connection" endpoint; the helper already existed and the inject adds the route/controller. Reachable via `POST /api/v1/credentials/:id/test`. A real maintainer could write this; not contrived.
- **sibling_thread**: injected, but assistant-thread creation is a normal feature and mirrors the module's other lookups; reachable via `POST /api/v1/openai-assistants/thread`. Not contrived.
- **stored_assistant_credential**: real, unmodified upstream `services/assistants/index.ts` delete path; reachable via `DELETE /api/v1/assistants/:id`. The test seeds the assistant row directly rather than producing it through the create/update flow, but the row and the code path are real and the property does not depend on provenance. Not a contrivance.
- The injected code's catch-all-wraps-to-500 is exactly why a correct 4xx refusal must be rethrown; it is realistic maintainer code, not a planted trap.

No trap looks planted or contrived. Real upstream routes the published fix left open are treated as in scope, not as "beyond the advisory".

## 5. Verdict

**Gate A: READY.** P, read literally, covers every route the tests drive: load, decrypt or provider use is gated on the caller's active workspace (own or credential-typed share); NW covers the no-workspace cases. Each security test asserts the instructed outcome — no victim decrypt, no victim provider key, any 4xx — and R declines to pin a status, so no error class is demanded. The functional tests assert PR and S. The primary correct fix, pre-decrypt resolution scoped at the sink, passes all 34; the oracle, alt_fix and hardening checks confirm it. No instruction/test contradiction, and no test needs a route-naming sentence. Wrong fixes are gate-b leniency; none is a correct fix.

**Required: generalize.** (1) "Sessions. The property applies both to interactive sessions and to callers authenticated by an API key." → "The property applies to every authenticated caller, however the request was authenticated." (2) "Sharing is an existing mechanism with a type: a share recorded for a different kind of resource is not a credential share." → fold into P: "…or the owning workspace has explicitly shared it into the caller's workspace for use as a credential."

**Quality to tighten.** Add the two share-scope tests (third-workspace and other-credential-id shares); shared-credential functional tests for OAuth, test, thread, legacy delete and one write; a share-type negative on a non-vector route; no-workspace tests on assistants/file/legacy; tests for the OAuth callback/refresh loads; neutralize the hints above.

**Human review:** confirm the stub's missing query-builder support, the leaf-router start point, and that the unauthenticated OAuth2 callback/refresh credential loads are intentionally untested.

GATE_A: READY
NEEDS_HUMAN_REVIEW: YES
