# traefik-ds: build notes (build-v1, pattern B, injected track)

Start: 2026-10-19T18:16:40Z. End: 2026-10-19T20:22:42Z.

Prior art: `tasks/traefik-header-name` was built for the same advisory and **rejected**:
DeepSeek solved it in run 1 (24 min) and MiMo in run 1 (106 min). Both models swept every
`Header.Del`/`Header.Set` site and applied a case+underscore normaliser, because the report
stated the general rule and the full entry-point option contract. This build keeps the
reproducible core and adds difficulty where a sweep does not help: a filter-loop idiom, a
partial defence that looks finished, and a configured-pattern shape that one-way normalisers
miss.

## Design

Trust decision that recurs in this repo: *the proxy asserts a request-header value to the
backend, so a client must not be able to sneak the same name in under a spelling the backend
folds*. The existing `forwardedheaders` package already folds `_` to `-` for its managed
`X-Forwarded-*` headers (`isManagedXHeader`), which is the in-repo precedent a reader can find.

### Levers (one line each)

- **P** (published site, stated contract): entry-point static option
  `http.underscoreHeadersStrategy` = `keep` (default) / `delete` / `reject`, invalid value
  fails start-up. Producer: CLI flag / static configuration -> entry-point HTTP server.
  Coupling: default `keep` must preserve today's forwarding, while every middleware route
  below must still be closed under the default.
- **U1** (B, landing/trigger): basic-authentication user header, `pkg/middlewares/auth/basic_auth.go:108`.
  Reason to dismiss: none — it is the reported example; kept as the trigger and positive control.
- **U2** (B): digest-authentication user header, `pkg/middlewares/auth/digest_auth.go:102`.
  Reason to dismiss: "the report shows basic authentication; digest is a separate, rarely used scheme."
- **U3** (B, injected partial defence on a real route): forward-authentication response headers
  copied by name, `pkg/middlewares/auth/forward.go:197-202`. The tree carries a plausible
  `removeHeaderVariants` helper that only folds letter case (`strings.EqualFold`), so the route
  *looks* already defended; all-underscore and mixed spellings survive.
  Reason to dismiss: "an alias-aware loop is already here; nothing to do."
- **U4** (B): forward-authentication response headers selected by a configured pattern,
  `pkg/middlewares/auth/forward.go:205-216`. The pattern is matched against the received
  canonicalised key only, so a pattern written with `_` never selects the dash spelling (and
  vice versa). Reason to dismiss: "the operator chose the pattern; users choose their own regex."
- **U5** (B): operator-configured custom request headers, set and remove,
  `pkg/middlewares/headers/header.go:120-139` (including the `X-Forwarded-For` nil-slice branch).
  Reason to dismiss: "a generic header rewrite in a different package, not an authentication feature."
- **U6** (B): client-certificate headers set from mutual TLS,
  `pkg/middlewares/passtlsclientcert/pass_tls_client_cert.go:150-165`.
  Reason to dismiss: "the value comes from the TLS layer, in another package; there is no
  client header to overwrite."
- **S1** (INJECTED, new package `pkg/middlewares/trustedheaders`): a trusted-upstream
  identity passthrough. Configured identity headers are removed from requests of untrusted
  clients and forwarded from trusted peers. The removal is a filter loop that compares
  `http.CanonicalHeaderKey(received)` against a canonical set — a different idiom from
  `Header.Del`, and it folds nothing but case. Reachable through the dynamic middleware
  factory and the real request path. Reason to dismiss: "it is a trusted-proxy feature, not an
  authentication middleware, and it already filters exactly the configured names."
- **S2** (INJECTED, `pkg/middlewares/auth/forward.go`): the partial helper above. Its own trap id,
  its own test (mixed spelling `X-Auth_User` / `X_Auth-User` against the copied header).
  Reason to dismiss: "existing alias-aware helper; already handled."
- **S3** (input shapes, no separate site): mixed spellings `X_Auth-User`, `X-Auth_User`;
  configured names in lower case and with underscores; a configured pattern written with
  underscores; multi-value headers. Reason to dismiss: "the example is the all-underscore
  spelling, and case-only folding looks enough."

### Tested sites / routes / shapes

- Entry point: CLI flags (`--entryPoints.web.http.underscoreHeadersStrategy=...`) decoded as the
  `traefik` command decodes them, through `NewTCPEntryPoints`, then a raw HTTP/1.1 request to
  the listening socket. `keep`/unset, `delete`, `reject`, invalid, multi-value headers.
- Middleware routes U1-U6 and S1/S2, each with the client spelling variants above; forward auth
  is exercised with the auth service returning the header, returning nothing, and returning
  another listed header; custom headers with set and with empty-value removal.
- S1 through its `New` constructor (the middleware factory's construction path), untrusted and
  trusted client addresses.

### Coupled must-keep-working (functional)

- Default `keep`: unrelated underscore headers and multi-value headers forwarded unchanged.
- `delete`: only underscore names removed; dash names (multi-value) intact; no rejection.
- `reject`: only requests carrying an underscore name refused; others served.
- Basic/digest: the authenticated user still arrives in the configured header under its exact
  configured spelling; unrelated headers unchanged.
- Forward auth: the service's listed/pattern-matched headers are still set; unrelated headers
  unchanged; request-header filtering still works.
- Custom headers: other configured set/remove behaviour unchanged; `Host` still handled.
- PassTLSClientCert: both certificate headers still set from mutual TLS.
- S1: a trusted peer's configured headers (canonical and variant) still arrive unchanged;
  other headers of untrusted clients are untouched.
- The project's own tests for every affected package, restored from pristine copies.

### Injected siblings

Two, both at the same trust decision, both reachable through the real path, both placed where
the published fix (`pkg/config/static/entrypoints.go`, `pkg/server/server_entrypoint_tcp.go`)
never touches. Both are ordinary feature code with no misleading names.

1. `trustedheaders` middleware (new package + dynamic config field + factory branch).
2. `removeHeaderVariants` (case-only alias filter) used by the forward-auth response-header loop.

## Verified

- The pinned commit 0056f09a is the direct parent of fix 108a5264; the fix's regression tests are
  absent at the pinned commit.
- Both patches apply cleanly: `inject.patch` to the pristine pinned tree, `fix.patch` to the
  injected tree.
- Local (host Go, injected tree): 82 security testcases, **0 pass / 82 fail** on the vulnerable
  code; all pass with the oracle. Functional group (hidden functional tests + 18 pristine project
  test files, 6 packages) passes on both the vulnerable tree and the oracle.
- All 21 check patches behaved as declared locally: 17 security_fail (2..79 security testcases
  failing, 0 functional failures), 3 functional_fail, and the hardening and alternative passes
  at zero failures.
- Injected code compiles (`go build ./pkg/middlewares/... ./pkg/server/... ./pkg/config/...`).

## Not verified / judgement calls

- Only HTTP/1.1 is driven. h2c/HTTP2/HTTP3 share the same entry-point handler chain.
- Refusal is accepted as an alternative to stripping (any 4xx, backend not reached).
- The invalid-value check accepts a failure at flag loading, at static-configuration validation,
  at entry-point creation, or an entry point that never routes a request.
- Dot spellings (`X.Auth.User`) are not tested; the instruction defines the equivalence only as
  case and `_` versus `-`.
- The injected middleware is a new dynamic-config feature; a solver must read the middleware
  tree rather than rely on the upstream advisory. It is ordinary feature code with no
  misleading names or comments.

## Out of scope (one line)

- Upstream's filter comment mentions trailers but only headers are examined, and current upstream
  also has a later `aliasHeadersStrategy` option for `'.'` spellings. Neither is built on.

## Gate

- static: **fails only** on the missing `blind` patch and `build/traefik-ds/FAIRNESS.md` (both are
  written by others after this build).
- nop: **PASSED** — 82 security testcases, 0 pass / 82 fail on the injected pinned tree; 280
  functional testcases, 280 pass. (First attempt hit the shared-Docker network-prune race and was
  retried; the retry passed.)
- oracle: **PASSED** — 3 runs, reward 1.0 each, 92/92 security and 280/280 functional, identical.
- patches: **PASSED** — 21/21 checks as declared: 17 security_fail (3..79 security testcases
  failing, 0 functional failures), 3 functional_fail, `hardening` and `alt_refuse_in_auth` at
  reward 1.0. (First attempt hit the same network-prune race; the retry loop passed on attempt 1
  of the retry.)
- Stage-by-stage runs write `build/traefik-ds/gate_report.partial.json` by design; each stage's
  log is `gate_nop.log`, `gate_oracle.log`, `gate_patches.log` beside it.
