# FAIRNESS review — flowise-cross-tenant-inj

Read: `tasks/flowise-cross-tenant-inj/instruction.md`, every file under `tests/` (5 specs,
`harness.js`, all 8 stubs, both jest/babel configs, `score.py`, `test.sh`),
`solution/fix.patch`, `environment/inject.patch`, `task.toml`, `manifest.json`, `notes.md`,
all of `checks/*.patch`. Nothing was run.

Harness facts that drive several findings:

- The specs call the **controller default exports directly**; `stubs/express.js` makes
  `Router()` a no-op and no route/middleware chain is ever executed.
- `moduleNameMapper` rewrites only the literal specifiers `../../utils`,
  `../../utils/getRunningExpressApp`, `../../utils/fileValidation`. Any other spelling that
  reaches those modules (e.g. `./getRunningExpressApp` from a new `src/utils/` helper) loads
  the real server module.
- The in-memory repo implements `findOneBy`/`findOne`/`find` with plain object equality only.
  It has **no** `count`, `exists`, `findOneOrFail`, array/OR `where`, `In()`, or
  `createQueryBuilder`.
- `stubs/utils.js` exports `decryptCredentialData`, `encryptCredentialData`, `getAppVersion`
  only; it does not export `getRunningExpressApp`.

## 1. Per-test table

| Test (file::name) | What it asserts | Instruction sentence that makes it fair | Could a CORRECT fix fail it? | Risk |
|---|---|---|---|---|
| `security/base_vector_store.spec.ts::cross-tenant read of a vector store does not use the foreign credential` | Victim `encryptedData` never reaches `decryptCredentialData`; victim key never reaches the OpenAI client; `res.json` not called; `next` called with a truthy argument. | "must never cause the server to decrypt or use a stored secret that does not belong to the caller's active workspace"; "respond with a client error and perform no side effect". | **yes** — a correct refusal written as `return res.status(403).json({ error: 'Forbidden' })` (the exact pattern `routes/oauth2/index.ts` already uses pre-fix for a missing credential, and allowed by "No specific status code or message is required") makes `res.jsonCalled` true and never calls `next`. Also maybe: a router-middleware guard never runs here; a helper under `src/utils/` importing `./getRunningExpressApp` loads the real module. | high |
| `security/base_vector_store.spec.ts::cross-tenant list of vector stores does not use the foreign credential` | Same four observables. | same | **yes** — same `res.status(403).json` refusal; same router/import-path maybes. | high |
| `security/base_vector_store.spec.ts::cross-tenant delete of a vector store does not use the foreign credential` | Same four observables for the write route. | same; "no matter which operation it is" and "no matter what the operation returns". | **yes** — same refusal-shape failure. | high |
| `security/uncovered_assistants.spec.ts::cross-tenant listing of assistants does not use the foreign credential` | Same four observables. | "This holds for **every** operation that accepts a credential reference — no matter which operation it is"; "Fix the flaw and its close variants, not just the exact request shown". | **yes** — same refusal-shape failure. | high |
| `security/uncovered_assistants.spec.ts::cross-tenant read of a single assistant does not use the foreign credential` | Same four observables. | same | **yes** — same refusal-shape failure. | high |
| `security/injected_models.spec.ts::cross-tenant model listing does not use the foreign credential` | Same four observables, query-shaped helper. | "no matter what the operation returns (data, a status, or nothing)"; "every operation". | **yes** — same refusal-shape failure. | high |
| `security/injected_verify.spec.ts::cross-tenant credential verification does not use the foreign credential` | Same four observables, credential in the body. | "no matter whether the reference arrives as part of the query, the path, or the request body"; "every operation". | **yes** — same refusal-shape failure (a body guard returning 403 json). | high |
| `functional/legitimate_use.spec.ts::a workspace can read its own vector store` | `next` not called, `res.json` called, own secret reaches the OpenAI client. | "Legitimate use must keep working. A caller operating on a credential that its own workspace owns ... must succeed exactly as before." | **maybe** — a correct lookup written with `findOneOrFail`, `.count()`, `.exists()`, OR/array `where` or `In()` returns null / throws in the fake repo. Also a helper in `src/utils/` importing the real barrel. | medium |
| `functional/legitimate_use.spec.ts::a workspace can list assistants with its own credential` | same | same | **maybe** — same repository/import-path limits. | medium |
| `functional/legitimate_use.spec.ts::a workspace can list models with its own credential` | same | same | **maybe** — same. | medium |
| `functional/legitimate_use.spec.ts::a workspace can verify its own credential` | same | same | **maybe** — same. | medium |
| `functional/legitimate_use.spec.ts::a credential shared into the caller workspace still resolves (vector store)` | Owner ≠ caller; a `WorkspaceShared` row targets the caller's workspace; call succeeds and the shared secret reaches OpenAI. | "The only exception is a secret that the owning workspace has explicitly shared into the caller's workspace"; "resolving a credential explicitly shared into the caller's workspace, must behave exactly as today". | **maybe** — share lookup via `.count()`/`.exists()`/`In()`/query builder, or a helper in a new location whose `utils` import is not mapped, fails. | medium |
| `functional/legitimate_use.spec.ts::a credential shared into the caller workspace still resolves (assistants)` | same | same | **maybe** — same. | medium |
| — (low severity note) | Security tests accept *any* truthy `next(err)`, including a `TypeError`/500; the instruction asks for a client error. | "respond with a client error". | no (lenient, not strict) | low |

## 2. Leniency (QUALITY, non-blocking)

| Property / trap | Most plausible WRONG fix | Caught? |
|---|---|---|
| Property 1 — foreign credential never decrypted/used, every operation | Fix only the routes the hidden suite touches; leave `createAssistantVectorStore`, `updateAssistantVectorStore`, `uploadFilesToAssistantVectorStore`, `deleteFilesFromAssistantVectorStore` and `uploadFilesToAssistant` unscoped. | **No.** `base_vector_store.spec.ts` covers only get/list/delete; `sec_miss_base.patch` only models skipping the whole module. Four of seven vector-store routes and the assistant upload are unexercised. |
| Property 1 — every request shape | Fix only query-shaped references; leave the path-param `oauth2 /authorize/:credentialId` (and its `res.status(404).json` miss path) untouched. | **No.** No spec imports `routes/oauth2`. Instruction promises "the path" is in scope. |
| Property 1 — share is only the *caller's* share | Accept any `WorkspaceShared` row for the credential, omitting `workspaceId` and/or `itemType` from the share predicate. | **No.** Security tenants are never given a share; functional seeds only a valid caller-target share. |
| Property 1 — missing identity must fail closed | `const where = { id }; if (workspaceId) where.workspaceId = workspaceId;` | **No.** Every request in the suite has `activeWorkspaceId`; the manifest's `missing_authority: n/a` is wrong. |
| Property 1 — workspace comes from the session | Take workspace from `req.query.workspaceId`/body/header with a `req.user` fallback. | **No.** No test supplies a client-controlled workspace value. |
| Property 1 — decrypt only after entitlement | Decrypt first, then compare `credential.workspaceId`. | **Yes** — `decryptCalls()`/`openaiKeys()` assertions in every security spec. |
| Property 2 — own + shared kept working | Direct-ownership-only fix (drops `WorkspaceShared`). | **Yes** — the two shared functional tests, exercised by `checks/func_overbroad.patch` (security pass, functional fail). |
| Property 2 — own kept working | Refuse everything. | **Yes** — the four own-credential functional tests. Note `wrong_fix_catalogue.refuse_all` points at `func_overbroad.patch`, which is not refuse-all; the label is stale. |
| Trap `base` | Guard only the read/list routes of the module. | **Partly** — delete is tested; create/update/upload/deleteFiles are not (see first row). |
| Trap `uncovered_assistants` | Fix only the advisory's vector-store module. | **Yes** — `security/uncovered_assistants.spec.ts` + `checks/sec_published_only.patch`. Assistant file upload remains uncaught. |
| Trap `sibling_models` | Dismiss `getAssistantModels` as a harmless read-only helper. | **Yes** — `security/injected_models.spec.ts` + `checks/sec_miss_models.patch` (that patch adds `workspaceId` to the signature but keeps the unscoped `findOneBy`). |
| Trap `sibling_verify` | Dismiss the body-shaped, status-only `/verify` helper. | **Yes** — `security/injected_verify.spec.ts` + `checks/sec_miss_verify.patch` (same signature-only miss). |

Wrong fixes **no test catches**: partial route coverage (4 vector-store routes, assistant upload,
oauth2); a share predicate not scoped to the caller/`itemType`; fail-open when
`activeWorkspaceId` is absent; a workspace id taken from the client; a 500/`TypeError` refusal
scored as a pass even though the instruction requires a client error.

## 3. Hints (QUALITY, non-blocking)

- "no matter whether the reference arrives as part of the query, the path, or the request body,
  and no matter what the operation returns (data, a status, or nothing)" — a variant list that
  maps onto oauth2 (path), S2 (body) and S2's status-only return. Neutral wording: "This holds
  for every operation that accepts a credential reference, regardless of how the reference is
  supplied or what the operation returns."
- "Sharing is an existing mechanism; a fix that only checks direct ownership and forgets shared
  credentials would break legitimate use." — names the existing mechanism **and** the
  `func_overbroad` wrong fix. Keep the preceding preservation sentence and delete this one.
- "The examples above are illustrations, not the full set of operations or request shapes
  through which the property can be violated." — announces extra variants (and refers to
  "examples above" that do not exist). Delete.
- "Both travel the same request-handling path." — points at the shared lookup/sink as the place
  to fix. Delete (it carries no contract).
- "load the matching stored secret, decrypt it, and use it to talk to the external provider" —
  paraphrases the vulnerable mechanism. The "never decrypt or use" property already states the
  observable; the discovery sentence could be shortened to "use a stored credential on the
  caller's behalf" without changing fairness.
- "This holds for **every** operation that accepts a credential reference" is required for
  fairness (it is what makes the uncovered-assistants trap fair), so keep it.

## 4. Realism (QUALITY, non-blocking)

- `base` and `uncovered_assistants` are real, unmodified upstream code and are reachable from
  the real HTTP routes (`openai-assistants-vector-store`, `openai-assistants`).
- S1 (`getAssistantModels`) and S2 (`verifyAssistantCredential`) are literal copies of the
  existing lookup→decrypt→use pattern, registered before `/:id`; a maintainer adding a
  convenience/validation endpoint would plausibly write exactly this. Minor tell: a `POST
  /verify` gated by `assistants:view`, and the two injected bodies are verbatim clones. Neither
  reads as planted; no trap comments or magic values exist in product code.
- The main realism weakness is the **harness entry point**: it starts at the controller, and
  `stubs/express.js` discards the router, so the real route/middleware chain — the actual
  request entry point — is never exercised. A middleware-level fix is both realistic and
  invisible. That is a fairness issue (see 5a), not a contrived-trap issue.
- The server never runs; the DB, decryption and OpenAI SDK are stubs. This is faithful to the
  project's own mock-typeorm unit-test style, but it means only the stubbed repository surface
  and the two literal `utils` import spellings are supported.

## 5. Verdict

### 5a. UNFAIRNESS gate — **NOT READY**

**Primary (deterministic `yes`).** All seven security tests require the refusal to arrive as
`next(err)` and forbid any response body (`res.jsonCalled === false`). The instruction instead
says "respond with a client error and perform no side effect. ... No specific status code or
message is required", and the visible repo already refuses a missing credential with
`return res.status(404).json({ success: false, message: 'Credential not found' })` in
`routes/oauth2/index.ts`. A competent engineer who copies that idiom into the controllers —
`return res.status(403).json({ error: 'Forbidden' })` — has a correct, side-effect-free client
error and fails 7/7 security tests.

Required change (all four security specs): replace `assertBlocked` with a form-neutral check and
drop the unconditional `next`/`jsonCalled` assertions. For example:

```ts
function assertBlocked(res: any, next: jest.Mock) {
    expect(openaiKeys()).not.toContain(SECRET)
    expect(decryptCalls()).not.toContain(SECRET)
    const refusedViaNext = next.mock.calls.length > 0 && Boolean(next.mock.calls[0][0])
    const refusedViaRes = res.statusCode >= 400 && res.statusCode < 600
    expect(refusedViaNext || refusedViaRes).toBe(true)
}
```

Alternatively (less preferred, because it leaks harness form): add to "Refusal form" —
"Refuse by passing an error to `next(error)`; do not write the error response directly."

**Secondary `maybe` (unresolved; would also block if the primary were relaxed).**
1. Route/middleware fixes never run: specs call controller exports; `express.Router()` is a
   no-op. Required: drive the real router (recording `Router` stub or supertest with real
   express) with auth/permission middleware stubbed to set `req.user`, **or** add an explicit
   contract: "Enforce the check inside each operation's own handler (controller or the service
   it calls), so it holds even when the handler is invoked without the HTTP router."
2. Stub mapping is by literal specifier, not resolved path. A correct helper placed in
   `src/utils/` that imports `./getRunningExpressApp` or `./index` loads the real module and
   fails the functional tests. Required: a `setupFiles` file that `jest.mock`s the resolved
   `PRODUCT_ROOT/utils/index.ts` and `PRODUCT_ROOT/utils/getRunningExpressApp.ts`, or mapper
   entries covering any spelling; and export `getRunningExpressApp` from `stubs/utils.js`.
3. The fake repo is narrower than TypeORM. A correct fix using `count`, `exists`,
   `findOneOrFail`, OR/array `where` or `In()` fails. Required: implement those in
   `tests/support/harness.js` (and a minimal `createQueryBuilder` if practical), or restrict
   accepted idioms only if that is stated in the instruction.

### 5b. Quality to tighten (recorded; NOT a reason for NOT READY)

- Add security tests for `create`/`update`/`uploadFiles`/`deleteFiles` vector-store routes and
  `uploadFilesToAssistant`; add an oauth2 `/authorize` test or remove "the path" from the
  instruction.
- Add security tests for: victim credential shared to a *third* workspace; missing
  `activeWorkspaceId` (must fail closed); attacker-supplied `workspaceId` in query/body; a
  `WorkspaceShared` row with the wrong `itemType`.
- Make the refusal assertion require a 4xx (`next.mock.calls[0][0]?.statusCode` or
  `res.statusCode`) instead of any truthy error, so a TypeError/500 is not scored.
- Neutralize the hints in §3; delete "Both travel the same request-handling path."
- Fix `wrong_fix_catalogue`: `refuse_all` is not `func_overbroad.patch`, and `missing_authority`
  should not be `n/a` (fail-open when the workspace id is absent is a real wrong fix).
- Realism: make the harness exercise at least one real route chain so the "real entry point"
  claim in the manifest is true.
