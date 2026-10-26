# traefik-header-name: build notes (build-v1)

Start: 2026-10-17T04:28:02Z. End: see the bottom of this file.

## Levers (one line each)
- T1 (B, sibling scheme): the digest user header, `pkg/middlewares/auth/digest_auth.go:100-104`, deletes only the canonical name. Reason to dismiss: "the report shows basic authentication".
- T2 (B, 2 routes): the headers that forward authentication copies (by list, and by pattern), `pkg/middlewares/auth/forward.go:197-216`, delete only the canonical or received spelling. This includes the case where the auth service returns no header. Reason to dismiss: upstream's own comment leaves spellings to the entry-point option.
- T3 (B, other package): an operator-configured custom request header set or removed, `pkg/middlewares/headers/header.go:120-139`. Reason to dismiss: "not an authentication feature".
- T4 (published sites, stated contract): the entry-point option `underscoreHeadersStrategy` (keep/delete/reject, invalid value = start-up error). It is loaded from CLI flags through the static-config loader into the entry point, `pkg/config/static/entrypoints.go:63-78` and `pkg/server/server_entrypoint_tcp.go:602`. The trap is the coupling: the default must stay keep while T1-T3 still hold.
- S1 (input shape): mixed spellings (X_Auth-User, X-Auth_User) and a lower-case configured header name. These defeat the tempting fix that deletes only the all-underscore spelling.
- Coupled must-keep-working: unrelated headers with underscores (X_Request_Tag, X_Auth_Role, X-Auth-User-Id) keep arriving. X_Auth_User arrives unchanged where no feature manages X-Auth-User. The configured user-header spelling is kept (project tests). The entry-point default forwards underscore headers and multi-value headers as they are.

## Verified
- The pinned commit 0056f09a is the parent of fix 108a5264, and the fix's regression tests are absent at the pinned commit.
- The project's tests for the four packages pass offline in the image at the pinned commit (247 functional testcases including 12 hidden TestFuncZZ*).
- Every route was confirmed by behavioural test on the pinned copy: the spoof marker reaches the backend handler. Every route also stays open with the published fix applied (published_fix_only.patch: 35 of 48 security testcases fail, all of them middleware tests).
- Go's server canonicalises a client X_Auth_User to X_auth_user (no '_' folding), so the routes are reachable over real HTTP/1.1.
- Oracle = the published source changes, plus a spelling-insensitive delete in basic, digest and forward (list + pattern), plus the same in custom request headers.
- Locally, all 17 check patches behaved as declared before the gate.
- Current upstream (read-only, origin/master 62b1f935 and origin/v2.11 0a2ab088, 2026-10-15) still has T1-T3 open. Code comments there say spellings are left to an aliasHeadersStrategy entry-point option.

## Not verified / judgement calls
- Our invariant departs from upstream's choice. Upstream keeps the middlewares canonical-only and offers an opt-in entry-point filter. The task requires the middlewares to protect the headers they manage under the default too. The instruction states this explicitly ("with every entry-point setting, including the default").
- Only HTTP/1.1 is driven. h2c/HTTP2/HTTP3 share the same handler chain and middlewares.
- Refusal is accepted as an alternative to stripping (any 4xx, backend not reached). alt_refuse_in_auth.patch is the passing proof.
- The invalid-value check accepts an error from the flag loader or from entry-point creation.
- Dot spellings (X.Auth.User, handled by upstream's later alias option) are not tested, and the instruction defines the equivalence only as case and '_' versus '-'.

## Out of scope (one line)
- The published wrappers' comment says "header and trailer" but only headers are filtered. Upstream later added an aliasHeadersStrategy covering '.' spellings. Neither was built on.

## Gate
- static: fails only on the missing blind patch and FAIRNESS.md (written by others).
- nop: PASSED (38 security testcases all fail, 247 functional all pass).
- oracle: PASSED (3 runs, reward 1.0, identical).
- patches: PASSED (17 of 17 as declared: 12 security_fail, 3 functional_fail, hardening and alternative pass at 1.0).

End: 2026-10-17T05:44:39Z

## Revision after FAIRNESS review (2026-10-17)
- R1 (instruction claimed more than the oracle delivered): took the preferred option. The oracle now also removes equivalent spellings before the client-certificate middleware sets its two headers (new lever T5). New tests: TestSecZZPassTLSClientCertHeaderAlias (real HTTPS server with mutual TLS, generated client certificate, 5 spellings) and coupled TestFuncZZPassTLSClientCert{PEM,Info}KeepsOtherHeaders; the package's own tests are restored pristine and run in the functional group. no_passtlsclientcert.patch (the previous oracle) is the security_fail check; hardening and alt_refuse_in_auth carry the same hunk. Hop-by-hop headers are now explicitly out of scope in Rule 1 (no feature named).
- R2 (invalid-value check too narrow): TestSecZZEntryPointUnderscoreHeadersValues now accepts a failure at flag loading, at the static-configuration validation the traefik command runs (SetEffectiveConfiguration + ValidateConfiguration on a configuration seeded like the command's), at entry-point creation, or an entry point that never routes a request after Start. A positive keep control guards the probe. Locally verified: check in ValidateConfiguration passes, silently accepting the value fails.
- Recommended: neutralised "Several Traefik features ..."; added an X-Forwarded-For removal row to TestSecZZCustomRequestHeaderRemovedAlias (oracle already handled it).
