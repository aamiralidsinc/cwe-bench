# stk-kiota-typescript-7845 — build notes

Start (UTC): 2026-10-26T12:21:06Z (recorded by the launcher)
End (UTC): (filled when the gate finishes)

## Task

- Project: microsoft/kiota-typescript, pinned at `765d509a98a8e0024da094584b5ad524b004fa25`.
  `git rev-parse 09f8bd9b34d68bf412a9b78f6ca7e7961ef14974^` is exactly the pin; the source
  change is `4dab0e233e1196817b253006e69498db073b6296`, merged by `09f8bd9b34d68bf412a9b78f6ca7e7961ef14974`.
- Advisory: GHSA-396q-4vc8-28x9 / CVE-2026-49336 (CWE-178 + CWE-200): the default redirect scrub
  deletes the canonical property names, but every header key has been lower-cased before the scrub
  runs, so the delete is a no-op and the credentials follow the redirect.
- Stacked pattern H4, three concepts (T1+T4, T5, T3).

## Levers (one line each)

- T1 (both; advisory route): the scrub's exact-property deletes never match the adapter's
  lower-cased keys. `packages/http/fetch/src/middlewares/options/redirectHandlerOptions.ts:79-82`;
  producer at `packages/http/fetch/src/fetchRequestAdapter.ts:529-532`.
- T4 (mimo; how-type, same route): a supported authentication middleware writes the same bearer
  token under the canonical spelling next to the adapter's lower-cased one, so a fix that matches
  only one spelling leaves the other. `packages/http/fetch/src/middlewares/authorizationHandler.ts:53,67,80`
  via `packages/http/fetch/src/kiotaClientFactory.ts:50-54`.
- T5 (deepseek; uncovered route where the protection never existed): the roster names two of the
  three standard credential headers; a caller-attached proxy credential is never removed, and the
  comments argue the omission is intentional.
  `packages/http/fetch/src/middlewares/options/redirectHandlerOptions.ts:60-62,79-82,89-92`.
- T3 (deepseek; uncovered route where the protection never existed): the native-request hand-off
  returns the authenticated request with no redirect policy, while only the middleware path sets
  the manual policy. `packages/http/fetch/src/fetchRequestAdapter.ts:536-537,556-566`;
  contrast `packages/http/fetch/src/middlewares/redirectHandler.ts:175`.

## Dropped from the reader's design

- **T2 (browser default chain) was dropped.** The browser chain intentionally has no redirect
  middleware because the browser follows redirects itself. The only fix that would make a
  behavioural test pass there is to insert the existing redirect middleware, which forces
  `redirect: "manual"`; a browser then returns an opaque redirect response with no readable
  `Location` (`redirectHandler.ts:84-96`), so browser redirect following stops working. There is
  no fix that both blocks a leak through a non-browser transport and keeps the documented browser
  behaviour, so a security test for it would either be unfaithful to a browser or unfixable. The
  record itself lists this conflict. Dropping it rather than shipping an unfair lever.
- **T5 was promoted to its own concept** in place of T2. It is an independent guard: a fix can be
  fully case-insensitive and still forget the proxy credential (the published fix adds it; the
  comments dismiss it). The miss patch shows the concepts are separable.
- **T6** (caller-supplied middleware list without a redirect handler) stays excluded as the reader
  recommended: using the caller's list verbatim is a tested, documented contract, so forcing a
  redirect handler in is not a legitimate requirement.

## Verified on the pinned tree (local harness, vitest, source aliases)

| variant | security failures | functional failures | expected |
|---|---|---|---|
| pinned | 17/17 | 0/73 | nop contract |
| reference (oracle) | 0/17 | 0/73 | oracle |
| miss_case (canonical delete + lower-case proxy) | 10/17 (T1+T4) | 0/73 | security_fail |
| miss_proxy (case-insensitive, no proxy) | 4/17 (T5) | 0/73 | security_fail |
| miss_native_handoff (published scrub only) | 3/17 (T3) | 0/73 | security_fail |
| upstream_fix (published source change) | 3/17 (T3) | 0/73 | recall: security_fail |
| functional_overbroad (strip on every redirect) | 0/17 | 8/73 | functional_fail |
| alt_correct_fix (scrub + `redirect: "error"`) | 0/17 | 0/73 | pass |
| hardening (oracle + defensive set/guard) | 0/17 | 0/73 | pass |

The functional group is 10 hidden functional tests plus the project's own 63 affected-area tests
(`test/node/RedirectHandler.ts`, `RedirectHandlerOptions.ts`, `kiotaClientFactory.ts`,
`MiddlewareFactory.ts`, `httpClient.ts`, `test/common/middleware/authorizationHandler.ts`,
`headersUtil.ts`), copied pristine at grade time.

## What I could not verify

- T3 is tested with a caller-side transport that follows redirects and forwards the headers it was
  given unless the request opts out. Node's own fetch strips the three standard credential headers
  on cross-origin redirects, so the hand-off leak is only observable through a transport that does
  not strip. That is exactly the caller-supplied transport boundary the method documents: the
  product must not rely on the transport's implicit behaviour. A correct fix (disable automatic
  redirect following, or refuse it) passes; stripping the credentials from the prepared request
  fails the coupled functional test.
- Whether a `Headers` instance (rather than the plain record the adapter builds) reaches the scrub
  through any real entry point; it does not on the adapter routes, so it is not a lever.
- Browser behaviour is not exercised (no browser in the image); the browser chain is not a lever.
- Current upstream (checked read-only on 2026-10-26 at `61cb1cc`) still has the native hand-off
  without a redirect policy (T3 present) and has the case-insensitive proxy roster (T5 fixed).

## Outside scope (one line)

- The advisory's token-minting host allowlist (`packages/abstractions/src/authentication/allowedHostsValidator.ts`)
  is a second, different credential protection and is not built on.
