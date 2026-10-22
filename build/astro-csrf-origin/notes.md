# astro-csrf-origin — build notes (build-v1, pattern A)

Start: 2026-10-17T06:25:10Z (start_utc.txt). End: see the bottom of this file.

## Levers
- T1 (A, far site): page/endpoint dispatch with no middleware step. `packages/astro/src/core/pages/handler.ts:110-120`. Dismissable because mounting `middleware()` looks mandatory.
- T2 (A, lower-level public API): the `astro/fetch` primitives `actions(state)` and `pages(state)` (`packages/astro/src/core/fetch/index.ts:102-110,146-154`), protected in `packages/astro/src/actions/handler.ts:33-45`. Dismissable because the report names only the Hono integration.
- T3 (input shapes): form action vs RPC, a missing content type, non-POST methods, content-type case and parameters, a missing Origin header. All of these come from the existing general rule (`packages/astro/src/core/app/middlewares.ts:28-66`).
- T4 (coupled): cross-site non-form requests (JSON), safe methods and `checkOrigin: false` must all still pass. Over-broad fixes fail functionally.
- Not used: producer-off-path. `manifest.checkOrigin` is a static build-time flag that the check reads, so there is no realistic infrastructure producer to stage.

## Verified
- The pinned commit 79aa99c6 is the parent of fix 0b30b35f. The upstream regression tests are absent at the pin.
- In the dev image, all 10 security tests fail on the pinned code because the handler runs. The form action case returns 403 from `middleware()` only after the action has run.
- The oracle scores 1.0 with 154 functional tests. These include six project unit-test files for hono, fetch, actions and middleware.
- Every `checks/` patch behaves as declared in a pre-run on the dev image (before the gate).
- The hidden fixture provides a pass-through site middleware loader, the way a real server build does. With no loader, `getMiddleware()` returns a no-op, and even `App.render` skips the origin check (see below).

## Could not verify / scope notes
- Prerendered routes as a coupled behaviour: an on-demand App does not match prerendered routes (404), so the composable entry points cannot reach them. Not tested.
- The project test `test/units/app/csrf.test.ts` was excluded. It imports the module that the upstream fix renames.
- Out of scope (screener O8, one line): when the manifest has no middleware loader (edge-middleware mode), the standard `App.render` path skips the origin check. Confirmed behaviourally in the dev image with a bare test manifest. Not built on, and whether edge adapters check elsewhere was not traced.
- Out of scope: the container API hard-codes `checkOrigin: false`.

End: 2026-10-17T06:56:23Z. Gate: static (only blind + FAIRNESS.md missing, as intended), nop, oracle (3 runs), patches (13/13) all passed.
