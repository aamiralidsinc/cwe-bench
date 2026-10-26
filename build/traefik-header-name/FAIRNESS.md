# FAIRNESS review: traefik-header-name

Reviewer: pre-trial fairness and leniency review (BUILDER.md 3h). Nothing was run. I read
instruction.md, every file under tests/, solution/fix.patch, manifest.json, notes.md, the checks/
patches (the ones relevant to each lever) and, for context, BUILD-PROMPT.md.

## 1. Tests

Equivalence used below: two names are the same if they differ only in letter case or in `_` versus
`-`. ("Rule 1" is the first Required-behaviour bullet.) Go's server canonicalises names
before Traefik sees them (`X_Auth_User` arrives as `X_auth_user`), so every spelling under test is
reachable over real HTTP/1.1.

| Test (file::name) | Asserts | Why it is fair | Could a correct fix fail? | Risk |
|---|---|---|---|---|
| security/auth/zz_alias_sec_test.go::TestSecZZBasicAuthUserHeaderAlias | Basic auth with the user header configured as `X-Auth-User` or `x-auth-user`, client sends `X_Auth_User`, `X_Auth-User`, `X-Auth_User` or `x_auth_user` carrying a marker. Either the request is refused with a 4xx before reaching the backend, or no equivalent spelling reaches the backend with the marker. | The Observed-impact report, plus Rule 1, plus "Refusing such a request with a client error (4xx)… is also acceptable", plus "The names and values above are examples". | No. Mixed spellings and a lower-case configured name follow directly from the stated equivalence. | low |
| security/auth/zz_alias_sec_test.go::TestSecZZDigestAuthUserHeaderAlias | Same property for the digest user header (3 spellings). | Rule 1: "whichever feature or configuration manages the header". | No. | low |
| security/auth/zz_alias_sec_test.go::TestSecZZForwardAuthResponseHeaderAlias | Forward auth lists `X-Auth-User` and `X-Auth-Group` as copied response headers. The auth service returns the user, nothing, or only the group. No client spelling of `X-Auth-User` with the marker may reach the backend. | Rule 1. Traefik removes every listed header from the request unconditionally (`req.Header.Del` before the copy), so it "removes" `X-Auth-User` even when the service returns nothing. | Maybe, slightly. A fix that strips spellings only for headers it actually copies fails the "returns none" case. The code makes it visible that the listed header is always removed, and Rule 1 says "removes", so this fix is wrong, not merely different. | low |
| security/auth/zz_alias_sec_test.go::TestSecZZForwardAuthResponseHeaderRegexAlias | Same property with copied headers selected by pattern `^X-Auth-`, while the service returns `X-Auth-User`. | Rule 1 (Traefik sets `X-Auth-User` from the response). | No. A fix that removes spellings of every header it sets passes, and so does one that matches the pattern against the `-`-folded canonical name. A fix that matches the case-sensitive pattern against a lower-cased name would fail, but that would also break the existing copy semantics. | low |
| security/headers/zz_alias_sec_test.go::TestSecZZCustomRequestHeaderRemovedAlias | Configured request header `X-Auth-User: ""` (remove). Client spellings must not reach the backend with the marker. | Rule 1: "removes", "whichever feature or configuration". | No. | low |
| security/headers/zz_alias_sec_test.go::TestSecZZCustomRequestHeaderSetAlias | Configured request header `X-Auth-User: gateway` (set). Same property. | Rule 1: "sets, replaces". | No. | low |
| security/server/zz_alias_sec_test.go::TestSecZZEntryPointUnderscoreHeadersDelete | Loaded from the CLI flag `--entryPoints.web.http.underscoreHeadersStrategy=delete`. No header with `_` (including `_` alone and an unrelated `Custom_Trace`) reaches the routed handler. Two `X-Auth-User` values arrive unchanged. | `delete` bullet, almost word for word ("removed before routing", "including several values of one header"), and the flag spelling given in the instruction. | Maybe, slightly. Filtering inside a router middleware (for example via the entry point's default `http.middlewares`) instead of before routing would fail, because the test installs the backend directly as the router's HTTP handler. The instruction says "before routing", so this is low. | low |
| security/server/zz_alias_sec_test.go::TestSecZZEntryPointUnderscoreHeadersReject | With `reject`, any `_` header gives a 4xx and is never routed. A request without underscores is routed and keeps `X-Auth-User`. | `reject` bullet. | No. | low |
| security/server/zz_alias_sec_test.go::TestSecZZEntryPointUnderscoreHeadersValues | `keep` forwards `Custom_Trace` unchanged. `drop` and `Delete-All` must fail with an error from `flag.Decode` or from `NewTCPEntryPoints`. | "Any other value is a configuration error: the entry point must fail to start." | **Maybe.** A competent engineer may put the check in Traefik's static-configuration validation, the step the `traefik` command runs before it creates entry points (`Configuration.ValidateConfiguration` in v2.x). The `traefik` binary then refuses to start, which meets the sentence, but the test calls only `flag.Decode` and `NewTCPEntryPoints`, so the fix fails. A check placed in `Start()` (log and refuse to listen) fails the same way. | **medium** |
| functional/auth/zz_alias_func_test.go::TestFuncZZBasicAuthUserHeaderAndOtherHeaders | Unrelated `X_Request_Tag`, `X_Auth_Role` and `X-Auth-User-Id` arrive unchanged. The user header is exactly `[test]`. | Must-keep bullets 1 and 2. | No. `X-Auth-User-Id` is not equivalent to `X-Auth-User`; a prefix match would be wrong. | low |
| functional/auth/…::TestFuncZZBasicAuthWithoutUserHeaderForwardsUnderscoreHeaders | No user header is configured, so a client `X_Auth_User` arrives unchanged. | Must-keep bullet 1 ("Headers that Traefik does not set or remove … forwarded exactly as today"). | No. | low |
| functional/auth/…::TestFuncZZDigestAuthUserHeaderAndOtherHeaders | Digest version of the first functional test. | Same. | No. | low |
| functional/auth/…::TestFuncZZForwardAuthResponseHeadersAndOtherHeaders | Copied list headers keep their values (including two values of one header); unrelated headers unchanged. | Must-keep bullets 2 and 3. | No. | low |
| functional/auth/…::TestFuncZZForwardAuthResponseHeadersRegexAndOtherHeaders | Pattern `^X-Auth-User$`: the copied header is kept and `X-Auth-User-Id` and the underscore headers arrive unchanged. | Must-keep bullet 1. | No. | low |
| functional/auth/…::TestFuncZZForwardAuthWithoutResponseHeadersForwardsUnderscoreHeaders | Forward auth with nothing copied, so a client `X_Auth_User` arrives unchanged. | Must-keep bullet 1. | No. | low |
| functional/headers/zz_alias_func_test.go::TestFuncZZCustomRequestHeaderSetKeepsOtherHeaders | Setting `X-Auth-User` and `X_Static_Tag` gives the configured values. An unrelated client `X_Request_Tag` arrives unchanged. | Must-keep bullets 1 to 3. | No. | low |
| functional/headers/…::TestFuncZZCustomRequestHeaderRemoveKeepsOtherHeaders | Removing works and an unrelated `X_Request_Tag` is unchanged. | Same. | No. | low |
| functional/server/zz_alias_func_test.go::TestFuncZZEntryPointDefaultForwardsUnderscoreHeaders | Default flags: underscore headers and two values of one header are forwarded as they are. | "`keep`, the default". | No. | low |
| functional/server/…::TestFuncZZEntryPointZeroConfigForwardsUnderscoreHeaders | An entry point whose HTTP config never had defaults applied (empty strategy) behaves as keep. | "(also when the option is unset)". | No. The instruction says so explicitly. | low |
| functional/project/auth/basic_auth_test.go::TestBasicAuthUserHeaderCanonical (and the digest twin) | With the user header configured as `x-user`, the backend gets `req.Header["x-user"] == [test]` and no canonical `X-User`. | Must-keep bullet 2: "keep their names and values as today". It is the project's own pre-existing test. | No. A fix that "resolves" the TODO by canonicalising the configured name fails it, as intended (canonical_user_header.patch). | low |
| functional/project/** (the other pristine project tests in 4 packages) | Existing behaviour. | Must-keep bullet 3. | No. | low |

## 2. Leniency

| Property / trap | Most plausible wrong fix | Caught? |
|---|---|---|
| Landing point (basic) / S1 | Delete only the all-underscore spelling `X_Auth_User` | Yes: the mixed spellings in TestSecZZBasicAuthUserHeaderAlias (exact_underscore_spelling.patch). |
| S1 lower-case configured name | Compare spellings against the configured string literally | Yes: the `x-auth-user` field rows. |
| Refusal | Answer 500 or a 2xx without forwarding | Yes: zzAssertNotSpoofed requires a 4xx (crash_as_refusal.patch). |
| T1 digest | Fix basic only | Yes: TestSecZZDigestAuthUserHeaderAlias (no_digest.patch). |
| T2 list | Strip spellings only when the service returned the header | Yes: the "auth sets no user" and "auth sets other hdr" rows (forward_only_when_auth_returns.patch). |
| T2 list | Strip from the auth response instead of the client request | Yes (wrong_header_map.patch). |
| T2 pattern | Fix the list route only, or match the pattern on the received spelling only | Yes: TestSecZZForwardAuthResponseHeaderRegexAlias (forward_list_only.patch). |
| T3 | Fix the remove verb only | Yes: TestSecZZCustomRequestHeaderSetAlias (custom_headers_remove_only.patch). There is no set-only patch, but TestSecZZCustomRequestHeaderRemovedAlias covers that direction. |
| T3 | Skip the headers middleware | Yes (no_custom_headers.patch). |
| T4 | Ship only the option (the published fix) | Yes: 35 middleware testcases (published_fix_only.patch). |
| T4 | Middlewares only, no option | Yes (no_entrypoint_option.patch). |
| T4 | `reject` refuses everything | Yes: the positive control (reject_refuses_all.patch). |
| T4 | `delete` as the default | Yes: functional (default_delete.patch). |
| T4 | `delete` removes only names equivalent to known managed headers | Yes: the `_` and `Custom_Trace` rows. |
| T4 | Unknown values accepted silently | Yes: TestSecZZEntryPointUnderscoreHeadersValues. |
| Over-broad | Strip every `_` header in the middlewares | Yes: functional (strip_all_underscore_headers.patch). |
| Over-broad | Canonicalise the configured user-header name | Yes: project test (canonical_user_header.patch). |

**Wrong fixes no test catches:**
- **PassTLSClientCert** (`pkg/middlewares/passtlsclientcert`, `Header.Set` of `X-Forwarded-Tls-Client-Cert`/`-Info`). With the client's IP in `forwardedHeaders.trustedIPs`, or with `insecure`, a client `X_Forwarded_Tls_Client_Cert` reaches the backend next to the certificate Traefik sets. This is inside Rule 1 ("whichever feature … manages the header"), yet the **oracle does not fix it** and no test covers it. BUILD-PROMPT lists it as O8b injection room. It is an identity header, so this is the most serious gap.
- Custom request header `X-Forwarded-For: ""`: the oracle patches this branch, but no test drives it. With untrusted clients, forwardedheaders already strips underscore variants; with trusted ones it is open.
- `delete`/`reject` on request trailers: only the hardening patch covers them.
- HTTP/2 and HTTP/3 paths: not driven, but they share createHTTPServer and the middlewares, so the risk is low.
- The reverse proxy's own hop-by-hop removals (for example `Proxy-Authorization`): Rule 1 literally covers them; the oracle and the tests do not.

## 3. Hints

- "Several Traefik features set, replace or remove request headers before a request is forwarded to the backend." This tells the solver there is more than one site; it is a mild route-count hint. Neutral alternative: "Traefik can set, replace or remove request headers before a request is forwarded to the backend." (Optional, low.)
- "This applies whichever feature or configuration manages the header, and with every entry-point setting, including the default." This is a scope statement. It is needed to make T1–T3 and the T4 coupling fair, so keep it.
- The option name, its values and the flag syntax are needed: the tests drive them, and they are the published API. Keep them.
- "including several values of one header" mirrors a test assertion, but it is a behavioural spec, not a mechanism. Acceptable.
- None of the leak_terms appear in instruction.md (checked: canonical, alias, digest, forward auth, regex, headerField, createHTTPServer and the others).

## 4. Realism

T1, T2, T3 and S1 are unmodified upstream code at the pinned commit. T4 is the published fix. Nothing is planted, and every route is reached through the real constructors over real HTTP, or through CLI flags, `NewTCPEntryPoints` and a raw TCP request. One known divergence: upstream deliberately leaves the middlewares canonical-only and makes the option opt-in. The task's stricter invariant is stated explicitly in the instruction, so the divergence is fair.

## 5. Verdict: NOT READY

Two changes are required:

1. **The instruction claims more than the oracle and tests deliver.** Rule 1 covers every feature, but the oracle leaves PassTLSClientCert (and the proxy's hop-by-hop stripping) open. Pick one:
   - (preferred) Extend the oracle to strip equivalent spellings before PassTLSClientCert sets its headers, and add a security test with the client inside `trustedIPs`, plus a coupled functional test.
   - Or narrow Rule 1 to the headers a middleware sets or removes as configured by the operator, and record PassTLSClientCert as out of scope in notes.md. Do not list the features by name.
2. **TestSecZZEntryPointUnderscoreHeadersValues is too narrow about where an invalid value may be rejected.** Also call the static-configuration validation step the `traefik` command runs (at the pinned commit), and accept an error from it. Alternatively, change the instruction sentence to "creating the entry point must fail with an error". Loosening the test is the better choice.

Optional: neutralise the "Several Traefik features…" sentence (section 3).
