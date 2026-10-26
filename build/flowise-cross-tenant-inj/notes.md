# flowise-cross-tenant-inj build notes

- Start (UTC): 2026-10-18T02:46:29Z
- End (UTC): 2026-10-18T03:11:27Z

## Mechanism
A caller-supplied credential id must belong to (or be shared into) the caller's active
workspace before the server loads, decrypts, and uses the stored secret. At the pinned
commit the sinks look the credential up by id alone (`findOneBy({ id })`). The published fix
introduces `resolveCredentialForWorkspace` (direct ownership via `{ id, workspaceId }`, else an
explicit `WorkspaceShared` record of itemType `credential`).

## Levers (pattern A+B, injected track)
- base (A) — vector-store module, `services/openai-assistants-vector-store/index.ts:13` + controller:21.
  The module the advisory names. Reason to dismiss: none (obvious lever).
- uncovered (B) — assistants module, `services/openai-assistants/index.ts:15,43` (list / single via
  `?credential=`). Real, unmodified upstream, NOT touched by this advisory's fix. Reason to dismiss:
  "a neighbouring feature (assistants, not vector-store)".
- injected S1 — `listAssistantModels` (`services/openai-assistants/index.ts:118`), `?credential=`.
  Reason to dismiss: "read-only helper returning only public model ids, looks harmless".
- injected S2 — `verifyAssistantCredential` (`services/openai-assistants/index.ts:146`), credential id in
  the request body. Reason to dismiss: "diagnostic/validation endpoint for trusted admins, returns no
  data". Different input shape (body vs query).

## Harness
Follows the project's own unit-test convention (virtual-mock typeorm + mock the repository). No full
pnpm/turbo build: the hidden jest suites drive the REAL controller default-export handlers with a
fabricated req/res/next; only the infra boundary is stubbed (in-memory repository with TypeORM
finder/query-builder parity via `getRunningExpressApp`; `decryptCredentialData`; the OpenAI SDK as a
deep proxy recording the api key; flowise-components). The utils barrel and `getRunningExpressApp`
are mapped by resolved path, so any import spelling reaches the stubs. Stubs are plain CommonJS `.js`
so they need no
transform; product `.ts` is transformed by babel-jest (preset-typescript + legacy decorators). The
leak observable is whether the victim credential's ciphertext is ever decrypted / used to build an
OpenAI client (globalThis.__decryptCalls / __openaiKeys).

## Verified (local jest, pinned+inject vs oracle)
- Vulnerable (pinned+inject): security 17 FAIL, functional 6 PASS.
- Oracle (pinned+inject+fix): security 17 PASS, functional 6 PASS.
- Every check patch behaves as declared: sec_miss_base (base fails), sec_published_only (uncovered+both
  siblings fail), sec_miss_models (S1 fails), sec_miss_verify (S2 fails), sec_share_unscoped (third-party
  and wrong-itemType shares fail), sec_client_workspace (query/body workspace fail), sec_missing_authority
  (no-workspace fail-open fails), sec_crash (500-as-refusal fails), sec_reads_only (write routes fail) —
  all functional PASS; func_overbroad and func_refuse_all (security PASS, functional FAILS);
  hardening + alt_fix + blind (all PASS).
- inject.patch and fix.patch apply cleanly (`patch -p1`) on a fresh pinned checkout.
- Pinned commit confirmed as the parent of fix d81483b7. No regression tests for these modules exist
  at the pinned commit (fix adds only tenantRequestGuards.test.ts).

## Fairness revision (pre-trial FAIRNESS.md)
- Refusal assertion is form-neutral: a security test now passes when the handler either passes a 4xx
  error to `next()` or writes a 4xx response, and requires a 4xx (a 500/TypeError is not a refusal).
  This removes the previous implicit "must call next" contract.
- The instruction states the check must live in each operation's own handler (controller or the service
  it calls) — the exact seam the suite drives — instead of promising a router-level path that the
  harness never executes.
- The utils barrel / getRunningExpressApp are mapped through a jest resolver for *any* spelling, so a
  helper in a new directory reaches the offline stubs; the stub barrel also exports getRunningExpressApp.
- The in-memory repository now matches TypeORM's finder surface: undefined conditions ignored, OR
  arrays, `In/Not/Like/IsNull`, `count/countBy/exists/existsBy/findOneOrFail/findBy/findAndCount`, and a
  minimal `createQueryBuilder`. The blind patch (which uses `count`) had never passed before this.
- Security coverage extended to every vector-store route (create/update/upload/deleteFiles), the
  assistant file upload, a caller with no active workspace, shares into a third workspace, wrong
  itemType shares, and client-supplied workspace ids in query and body. `blind.patch` was repaired
  (missing import + unscoped injected siblings) and now scores 1.0.


## Coupled must-keep-working
A credential owned by another workspace but shared into the caller's workspace via `WorkspaceShared`
(itemType `credential`) must still resolve — tested for both the base and the uncovered module. A fix
that only adds `workspaceId` to the lookup and drops the share branch breaks this (func_overbroad).

## Could not verify / caveats
- Did not run the full flowise monorepo build or a live HTTP server; the seam is the controller
  handler with stubbed infra (faithful to the project's own unit tests). The OpenAI SDK and DB are
  never real.
- oauth2 `/authorize/:credentialId` is part of the published fix (path-param shape, separate router).
  It is included in the oracle for fidelity but NOT exercised by the hidden suite: its handler is an
  inline `router.post` callback, not a controller export, so driving it would need supertest/express
  and a second harness style. Recorded as out-of-scope, not a lever.
- Target-model trials not run here (per instructions). The gate's blind patch and FAIRNESS.md are
  left for the downstream steps.

## Out of scope (one line)
The fix commit bundles several unrelated tenant-isolation fixes (chatflows, leads, upsert-history,
document-store, evaluations/dataset, enterprise user/role/workspace reads); only the credential-scope
sinks of this advisory are in scope here.
