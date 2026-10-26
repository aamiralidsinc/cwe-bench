# FAIRNESS: electron-builder-credential-leakage

Independent pre-trial fairness and leniency review (BUILDER.md 3h). Static review only: no Docker,
trial or gate was run for this file. The repository source is not present in this tree, so claims
about unmodified repo code come from `manifest.json`, `notes.md` and the patches. The solver sees
only `instruction.md` and the repository. One row per security and task-written functional test;
the copied repo tests are one row per test for `httpExecutorTest` and `nodeHttpExecutorTest`, and
one row per `describe` group for `utilTest` (every test name in the group is given; all of those
tests pin the same existing helper behaviour).

## 0. Instruction sentences cited below

- **S1** — "No credential attached to a request may reach an origin (scheme, host and port) other than the one it was attached for."
- **S2** — "Credentials include any request header that authenticates the client or user, standard or application-specific."
- **S3** — "This holds for every request the updater and the build and publish tooling make, at every redirect."
- **S4** — "Redirects keep working. After a redirect to another origin, the request still completes there without the credentials."
- **S5** — "Ordinary headers such as `Accept` or `User-Agent` still go along."
- **S6** — "Redirects within the same origin keep the credentials. So does an `http` to `https` upgrade on the same host with default ports. Private servers must keep working."
- **S7** — "Everything else works exactly as it does today: update checks, update downloads and publishing, including configuration validation and its error messages. Debug output still shows data that is not secret."
- **S8** — "No secret the tooling is given may appear in clear text in an error message or in debug output (`DEBUG=electron-builder`). Secrets include any credential value, whatever the field, option or variable holding it is called."
- **S9** — "Fix the problem and its close variants, not only the example above."

## 1. Per-test fairness

### 1.1 Security tests (10)

| file::name | what it asserts | instruction basis | could a CORRECT fix fail it? | risk |
|---|---|---|---|---|
| `security/redirect.test.ts::app updater (Electron net) > full download: a capitalised Authorization request header is not sent to the redirect target on another host` | No request reaching any origin other than FEED carries a header value containing the marker. The download may fail; only what another origin received is asserted. | S1 + S2 + S3; standard expert knowledge: HTTP header names are case-insensitive, so `Authorization` is the same header as `authorization`. | no. A fix strips it case-insensitively on the Electron download path, or aborts/refuses (the test tolerates a failed download). | low |
| `security/redirect.test.ts::app updater (Electron net) > GitLab provider: the project access token is not sent to object storage the asset link redirects to` | No header at the storage origin contains the token; `checkForUpdates` may fail. | The "What we observed" example + S1 + S2 + S3. | no. The token legitimately reaches the GitLab origin; only the cross-origin storage hop must be clean. Aborting the check is tolerated. | low |
| `security/redirect.test.ts::publishing HTTP client (Node) > API request: API-key, cookie and proxy credentials are not forwarded to another origin` | Server B (same host, different port) sees none of `X-Api-Key`, `Cookie`, `Proxy-Authorization`; the request may fail. | S1 (port is in the origin) + S2 (standard or application-specific headers) + S3 (publishing tooling). | no. A broad credential-name match or a cross-origin allow-list drops all three. A fix that only recognises auth-sounding names could miss `Cookie`; S2's "standard" covers it, and a credential-leak fix should drop it. | low |
| `security/redirect.test.ts::publishing HTTP client (Node) > API request: a PRIVATE-TOKEN header is not forwarded to another origin` | Server B never sees the PRIVATE-TOKEN value. | S1 + S2 (application-specific) + the example's GitLab token. | no. | low |
| `security/redirect.test.ts::publishing HTTP client (Node) > download: a capitalised Authorization header is not forwarded to another origin` | Server B never sees the Authorization value on `downloadToBuffer`. | S1 + S2 + S3; standard expert knowledge: header-name case-insensitivity. | no. | low |
| `security/differential.test.ts::differential download: the auth token is not sent to the host the update file redirects to` | Single-range block download (`useMultipleRangeRequest: false`, `addAuthHeader`): no non-FEED origin sees the marker. Completion is not asserted. | S3 ("every request … at every redirect") + S9 ("close variants"). | no. Re-issuing through the shared helper, aborting and falling back to a full download, or dropping differential for the redirect all pass. Only fixing the shared helper and leaving this route fails — an incomplete fix. | low |
| `security/differential.test.ts::differential download with the default multi-range requests: an application credential header is not sent to the host the update file redirects to` | Default multi-range path, `X-Api-Key` in `requestHeaders`: no non-FEED origin sees it. Completion is not asserted. | S3 + S9. The default configuration is part of "every request the updater … make[s]". | no. The fix must cover `multipleRangeDownloader` as well as the single-range loop; both the reference and the alternative fix do. | low |
| `security/redaction.test.ts::publish token configuration errors > GitHub: a GH_TOKEN with an invalid character is not echoed in the error` | The marker in the middle of the token is absent from message, stack and `String(error)`. | S8. | no. Hashing, masking, omitting or showing a short prefix all pass; the marker is not part of the env-var name. | low |
| `security/redaction.test.ts::publish token configuration errors > GitLab: a GITLAB_TOKEN with an invalid character is not echoed in the error` | Same, for GitLab. | S8. | no. | low |
| `security/redaction.test.ts::debug output (DEBUG=electron-builder) > a JSON request body's password, API key and client secret are not logged in clear` | With the namespace enabled, stdout+stderr contain none of the three values. | S8. | no. Redacting the values, redacting the fields, or a placeholder all pass. Suppressing the whole body fails the coupled functional test, but that over-fix is not a correct fix (S7). | low |

### 1.2 Task-written functional tests (16)

| file::name | what it asserts | instruction basis | could a CORRECT fix fail it? | risk |
|---|---|---|---|---|
| `functional/redirect.test.ts::app updater (Electron net) > full download through a redirect to another host completes with the right file` | Cross-origin full download completes; sha512 matches. | S4. | no. Only refusing without a fallback fails, which S4 forbids. | low |
| `functional/redirect.test.ts::app updater (Electron net) > full download through a redirect on the same server keeps the Authorization header` | Same-origin redirect still carries `Authorization`; download completes. | S6. | no. | low |
| `functional/redirect.test.ts::app updater (Electron net) > an http to https upgrade on the same host keeps the auth header` | http→https on the same host with default ports keeps auth; download completes. | S6 explicitly. | no. A strict `URL.origin` comparison would fail, but S6 states the exception and the repo's own `isCrossOriginRedirect` tests pin it. | low |
| `functional/redirect.test.ts::app updater (Electron net) > GitLab provider > a token-protected asset redirected within the GitLab server is still found` | Every GitLab request must carry `PRIVATE-TOKEN` (the server 401s otherwise); a same-origin redirect still resolves the release. | S6 + "Private servers must keep working." | no. | low |
| `functional/redirect.test.ts::app updater (Electron net) > GitLab provider > an asset redirected to object storage on another host is still found` | The cross-host asset still resolves to the new version (storage needs no credential). | S4 ("redirects keep working"). | no. Strip-and-continue passes; a full abort of the update fails S4. | low |
| `functional/redirect.test.ts::publishing HTTP client (Node) > a redirect on the same server keeps Authorization and PRIVATE-TOKEN` | Same-origin redirect keeps both; server returns `{ok:true}` only if both arrive. | S6. | no. | low |
| `functional/redirect.test.ts::publishing HTTP client (Node) > a redirect to another origin completes and still sends the ordinary headers` | Cross-origin 307 completes; B receives `accept` and a non-empty `user-agent`. | S4 + S5. | no. An allow-list fix must keep both; S5 names them. | low |
| `functional/redirect.test.ts::publishing HTTP client (Node) > a download redirected to another origin completes` | `downloadToBuffer` through a cross-origin 302 returns the payload. | S4. | no. | low |
| `functional/differential.test.ts::differential download without redirects fetches only the changed blocks` | With no redirect, every installer request carries a `Range` header (differential remains differential). | S7 ("update downloads … exactly as today"). | no. Only disabling differential fails; that would change existing behaviour. | low |
| `functional/differential.test.ts::differential download through a redirect to another host completes with the right file` | The downloaded file hashes correctly; a full-download fallback is allowed. | S4 + S7. | no. The reference re-issues, the alternative aborts and falls back; both complete. | low |
| `functional/differential.test.ts::differential download through a redirect on the same server keeps the auth header` | Every `/storage/...` request carries the auth header; the file hashes correctly. A full-download fallback is allowed (the test was loosened for this). | S6 + S7. | no. Both a same-origin differential follow and a fallback full download satisfy it. | low |
| `functional/redaction.test.ts::publish token configuration > GitHub: an invalid GH_TOKEN is still refused, naming the variable` | Throws and the message matches `/GH_TOKEN/`. | S7 ("configuration validation and its error messages"). | no. Redaction keeps the variable name. | low |
| `functional/redaction.test.ts::publish token configuration > GitHub: a valid GH_TOKEN is accepted` | Does not throw. | S7. | no. | low |
| `functional/redaction.test.ts::publish token configuration > GitLab: an invalid GITLAB_TOKEN is still refused, naming the variable` | Throws and the message matches `/GITLAB_TOKEN/`. | S7. | no. | low |
| `functional/redaction.test.ts::publish token configuration > GitLab: a valid GITLAB_TOKEN is accepted` | Does not throw. | S7. | no. | low |
| `functional/redaction.test.ts::debug output still shows a JSON request body's ordinary fields` | The debug output contains the ordinary `tag_name` value. | S7 ("Debug output still shows data that is not secret"). | no. Only deleting the debug line fails; that over-fix contradicts S7. | low |

### 1.3 Copied repo tests — `functional/project/httpExecutorTest.ts` (43 tests)

Basis for the whole table: S7 ("Everything else works exactly as it does today") plus standard
expert knowledge for URL/origin semantics. All pass at nop, so they pin existing helper behaviour
rather than the reference design; a fix that leaves the public helper semantics alone passes.

| file::name | what it asserts | instruction basis | could a CORRECT fix fail it? | risk |
|---|---|---|---|---|
| `… > HttpExecutor.prepareRedirectUrlOptions > basic functionality > should configure new options from redirect URL` | protocol/hostname/path from Location; existing header kept | S7; existing helper contract | no (only a rewrite that breaks URL handling) | low |
| `… > should handle relative redirect URLs` | relative Location keeps host, changes path | S7 | no | low |
| `… > should handle absolute redirect URLs with different domains` | absolute Location rewrites host/path | S7 | no | low |
| `… > authorization header handling > should preserve authorization header for same-origin redirects` | same-origin keeps `authorization` | S6 + S7 | no | low |
| `… > should strip authorization header for cross-origin redirects` | cross-origin removes `authorization` without throwing | S1 + S7 | no | low |
| `… > should preserve other headers when stripping authorization` | `User-Agent`/`Accept` survive | S5 + S7 | no; a rewrite that rebuilds headers with lowercased keys would fail the casing assertion, but that is a gratuitous change and the repo test is visible. | low |
| `… > should handle missing authorization header gracefully` | cross-origin without credentials: no throw, ordinary header kept | S7 | no | low |
| `… > should handle missing headers gracefully` | no headers: no throw, host rewritten | S7 | no | low |
| `… > cross-origin detection > hostname comparison > should treat same hostname as same-origin` | auth kept | S6 + standard expert knowledge | no | low |
| `… > should treat different hostname as cross-origin` | auth stripped | S1 | no | low |
| `… > should perform case-insensitive hostname comparison` | `API.GitHub.COM` → `api.github.com` keeps auth | standard expert knowledge: host names are case-insensitive | no | low |
| `… > should treat case-different hostnames as same-origin` | auth kept | same | no | low |
| `… > protocol comparison > should treat same protocol as same-origin (with same hostname)` | auth kept | standard expert knowledge | no | low |
| `… > should treat different protocol as cross-origin` | https→http strips | S1 ("scheme") | no | low |
| `… > should allow HTTP->HTTPS upgrade on standard ports` | 80→443 keeps auth | S6 explicitly | no | low |
| `… > should allow HTTP->HTTPS upgrade with implicit standard ports` | implicit ports keep auth | S6 | no | low |
| `… > should not allow HTTPS->HTTP downgrade` | strips auth | S1 | no | low |
| `… > port comparison > should treat same explicit ports as same-origin` | keeps auth | standard expert knowledge | no | low |
| `… > should treat different ports as cross-origin` | strips auth | S1 ("port") | no | low |
| `… > should treat implicit default ports as equivalent to explicit` | 443 == implicit; keeps | S6 ("default ports") | no | low |
| `… > should treat implicit default port as equivalent to explicit (HTTP)` | 80 == implicit; keeps | S6 | no | low |
| `… > should treat explicit port as equivalent to implicit default` | keeps | standard expert knowledge | no | low |
| `… > should handle non-standard ports correctly` | 8080→443 strips | S1 ("port") | no | low |
| `… > real-world scenarios > should handle GitHub API to GitHub assets redirect` | strips to `objects.githubusercontent.com` | S1 + S7; existing helper behaviour | no | low |
| `… > should handle GitHub API to release-assets.githubusercontent.com redirect` | strips | S1 + S7 | no | low |
| `… > should handle Azure Blob Storage redirect` | strips | S1 + S7 | no | low |
| `… > should handle AWS S3 redirect` | strips | S1 + S7 | no | low |
| `… > should preserve authorization for same-service redirects` | keeps | S6 | no | low |
| `… > edge cases > should handle URLs with query parameters` | cross-origin strips; query kept in path | S1 + S7 | no | low |
| `… > should handle URLs with fragments` | same-origin; fragment dropped; auth kept | standard expert knowledge + S7 | no; only a rewrite that mishandles fragments | low |
| `… > should handle URLs with userinfo (should be ignored in comparison)` | `user:pass@` ignored in comparison; auth kept | standard expert knowledge: userinfo is not part of the origin | no; treating userinfo as a request credential would be over-broad. | low |
| `… > should handle IPv6 addresses` | `[::1]:8443` same-origin; auth kept | standard expert knowledge | no; only a hand-rolled parser that mishandles IPv6 | low |
| `… > should handle empty path` | path defaults to `/`; auth kept | standard expert knowledge + S7 | no | low |
| `… > HttpExecutor.isCrossOriginRedirect > should be false for same hostname, protocol, and port` | false | standard expert knowledge | no | low |
| `… > should be true for different hostname` | true | S1 | no | low |
| `… > should be true for different protocol` | true | S1 | no | low |
| `… > should be true for different port` | true | S1 | no | low |
| `… > should be false for implicit vs explicit default port` | false | S6 | no | low |
| `… > should be false for case-insensitive hostname` | false | standard expert knowledge | no | low |
| `… > SPECIAL CASE: should be false for http -> https upgrade with default ports` | false | S6 explicitly | no | low |
| `… > SPECIAL CASE: should be false for http -> https upgrade with explicit default ports` | false | S6 | no | low |
| `… > SPECIAL CASE: should be true for http -> https upgrade with non-default ports` | true | S1 ("port") | no | low |
| `… > HttpExecutor error handling > should throw an error if hostname is missing and authorization header is present` | throws `Missing hostname in request options` | S7 ("everything else … exactly as today"); existing helper contract; the manifest records it as a repo test present at the pinned commit | no. A correct fix need not touch this path. A fail-closed rewrite that catches the existing error and proceeds would fail it, but that deliberately changes today's behaviour, which S7 forbids; `blind.patch` did this and failed (a patch-quality defect, see §4). | low–medium |

### 1.4 Copied repo tests — `functional/project/nodeHttpExecutorTest.ts` (20 tests)

Basis for the whole table: S7 and standard expert knowledge. The file exercises the proxy-agent
helper, unrelated to the advisory; all tests pass at nop. A correct fix that leaves
`buildGotProxyAgent`/`createRequest`'s agent selection alone passes; nothing in the advisory
requires touching them.

| file::name | what it asserts | instruction basis | could a CORRECT fix fail it? | risk |
|---|---|---|---|---|
| `…::buildGotProxyAgent > returns undefined when no proxy is configured > no proxy env vars set` | `undefined` | S7 (unrelated subsystem) | no | low |
| `… > all proxy env vars are empty strings` | `undefined` | S7 | no | low |
| `… > all proxy env vars are whitespace-only` | `undefined` | S7 | no | low |
| `… > returns correct agent shape > only https key when HTTPS_PROXY is set` | https agent only | S7 | no | low |
| `… > only https key when https_proxy (lowercase) is set` | https agent only | S7 | no | low |
| `… > only http key when HTTP_PROXY is set` | http agent only | S7 | no | low |
| `… > only http key when http_proxy (lowercase) is set` | http agent only | S7 | no | low |
| `… > both keys when HTTPS_PROXY and HTTP_PROXY are set` | both agents | S7 | no | low |
| `… > only https key when HTTPS_PROXY is valid but HTTP_PROXY is whitespace-only` | only https | S7 | no | low |
| `… > falls back to https_proxy when HTTPS_PROXY is whitespace-only` | https from fallback var | S7 | no | low |
| `… > falls back to http_proxy when HTTP_PROXY is whitespace-only` | http from fallback var | S7 | no | low |
| `… > env var precedence > HTTPS_PROXY takes precedence over https_proxy when both are set` | uppercase host wins | S7 | no | low |
| `… > HTTP_PROXY takes precedence over http_proxy when both are set` | uppercase host wins | S7 | no | low |
| `… > agent instances > http agent is an HttpProxyAgent` | constructor name | S7 | no | low |
| `… > https agent is an HttpsProxyAgent` | constructor name | S7 | no | low |
| `… > NodeHttpExecutor.createRequest > proxy agent assignment > sets HttpsProxyAgent when https_proxy is set and protocol is https:` | agent assigned | S7 | no | low |
| `… > sets HttpProxyAgent when http_proxy is set and protocol is http:` | agent assigned | S7 | no | low |
| `… > does not set agent when no proxy env vars are set` | `undefined` | S7 | no | low |
| `… > does not set agent when https_proxy is set but protocol is http: (mismatch)` | `undefined` | S7 | no | low |
| `… > does not set agent when http_proxy is set but protocol is https: (mismatch)` | `undefined` | S7 | no | low |

### 1.5 Copied repo tests — `functional/project/utilTest.ts` (grouped; 77 tests at runtime)

Basis for the whole table: S7 and standard expert knowledge. These are the repo's own redaction /
env / process-helper tests and snapshots. They pass at nop. A correct fix need not change
`removePassword`, `filterSensitiveEnv`, `resolveEnvShellValue` or `spawnAndWriteWithOutput`; the
reference leaves their output byte-identical. The only plausible breakage is a fix that changes
`removePassword`'s `(sha256 hash)` replacement format or over-redacts env keys; that would be a
gratuitous change pinned by the visible snapshots/tests.

| file::name | what it asserts | instruction basis | could a CORRECT fix fail it? | risk |
|---|---|---|---|---|
| `…::removePassword: --accessKey > handles unquoted / double-quoted / single-quoted value (snapshot)` | hashes the value after `--accessKey`, preserving quoting | S7; visible repo snapshot | no, unless the fix changes the hash format | low |
| `…::removePassword: --secretKey > handles unquoted / double-quoted / single-quoted value (snapshot)` | same for `--secretKey` | S7 | no | low |
| `…::removePassword: -p > handles unquoted / double-quoted / single-quoted value (snapshot)` | same for `-p` | S7 | no | low |
| `…::removePassword: -pass > handles unquoted / double-quoted / single-quoted value (snapshot)` | same for `-pass` | S7 | no | low |
| `…::removePassword: -String > handles unquoted / double-quoted / single-quoted value (snapshot)` | same for `-String` | S7 | no | low |
| `…::removePassword: /p > handles unquoted / double-quoted / single-quoted value and Mac host path without hashing (snapshot)` | same for `/p`; a `\\Mac\Host\...` path is left intact | S7 | no | low |
| `…::removePassword: pass: > handles unquoted / double-quoted / single-quoted value (snapshot)` | hashes the OpenSSL `pass:` value | S7 | no | low |
| `…::removePassword: /b … /c block > handles /b … /c block (snapshot)` | hashes the block content | S7 | no | low |
| `…::removePassword: word boundary protection > does not redact -path / -pid / -StringLength / a bare file path; redacts -passphrase / -p / /p` | word-boundary guards | S7; standard expert knowledge | no | low |
| `…::removePassword: case-insensitive flag matching > redacts -P / -PASS / -STRING / --ACCESSKEY` | case-insensitive stems | S7; standard expert knowledge | no | low |
| `…::removePassword: pass: colon-separator style > redacts pass:value and pass: value` | colon separator | S7 | no | low |
| `…::removePassword: multiple keys in one string > handles two keys unquoted; mixed quoted/unquoted; several keys and /b … /c (snapshot)` | multiple replacements | S7 | no | low |
| `…::validateEnvVarUrl > returns null when unset; throws for non-URL / http / file; returns a valid https URL unchanged` | env URL validation | S7 (unrelated) | no | low |
| `…::filterSensitiveEnv > redacts KEY/TOKEN/SECRET/PASSWORD/CSC/WIN_CSC_LINK/CREDENTIAL; case-insensitive; whole value; leaves NODE_ENV/PATH/GITHUB_LINK/ELECTRON_CACHE` | env-name redaction | S7; visible repo tests | no, unless the fix over-redacts an unrelated key such as `GITHUB_LINK` | low |
| `…::resolveEnvShellValue > null for unset/empty/whitespace; trims; rejects 9 shell-unsafe characters and backslash` | env shell validation | S7 (unrelated) | no | low |
| `…::spawnAndWriteWithOutput > captures stdout/stderr; empty output; ExecError/exit code; stdin round-trip; 4-minute timeout` | process helper | S7 (unrelated) | no | low |

## 2. Leniency (quality; not a reason for NOT READY)

### 2.1 Security property P1 — no credential reaches another origin at any redirect

| most plausible WRONG fix | caught? (test + check patch) |
|---|---|
| Keep the old helper: delete only the exact lower-case `authorization` key | Yes: `security/redirect.test.ts` capitalised-Authorization tests (updater full download and Node download) and the PRIVATE-TOKEN / X-Api-Key / Cookie / Proxy-Authorization tests; `checks/lowercase_only_names.patch` (declared security_fail, 5 tests). |
| Case-insensitive `Authorization` + `PRIVATE-TOKEN` only (the tempting narrow fix from the report) | Yes: `security/redirect.test.ts::publishing HTTP client (Node) > API request: API-key, cookie and proxy credentials…` (X-Api-Key, Cookie, Proxy-Authorization) and `security/differential.test.ts` multi-range (X-Api-Key); `checks/auth_and_private_token_only.patch` (declared security_fail). |
| Fix only the Electron updater | Yes: the three Node publishing-client tests; `checks/electron_only.patch` (declared security_fail, 3 tests). |
| Fix only the Node publishing client, leave the Electron updater | Yes: the two updater security tests (full download, GitLab) and the two differential tests. No dedicated check patch, but the tests cover it. |
| Compare hostnames only, ignoring scheme and port | Yes: the three Node tests (server B is on another port, same host) plus the repo's port/downgrade tests; `checks/hostname_only_compare.patch` (declared functional_fail; security also fails). |
| Fix the shared redirect helper only (the published upstream fix), leave the block-based download | Yes: both `security/differential.test.ts` tests; `checks/upstream_fix.patch` (declared security_fail). |
| Fix only the single-range differential loop | Yes: the default multi-range test; `checks/single_range_only.patch` (declared security_fail, 1 test). |
| Strip the request options after calling `followRedirect()` (check after adjustment) | Yes: the single-range differential test (the first followed hop still carries the credential); `checks/strip_after_follow.patch` (declared security_fail, 1 test). |
| Refuse every cross-origin redirect | Yes: functional cross-origin completion tests (`functional/redirect.test.ts` full download, GitLab-to-storage, Node request, Node download; `functional/differential.test.ts` cross-origin); `checks/refuse_cross_origin.patch` (declared functional_fail). |
| Strip credentials on same-origin redirects too | Yes: functional same-origin tests and the repo's same-origin/upgrade tests; `checks/strip_on_every_redirect.patch` (declared functional_fail). |
| Drop every header on a cross-origin redirect | Yes: `functional/redirect.test.ts::publishing HTTP client (Node) > a redirect to another origin completes and still sends the ordinary headers` (Accept/User-Agent); `checks/drop_all_headers_cross_origin.patch` (declared functional_fail). |
| Treat the http→https default-port upgrade as cross-origin (strict `URL.origin`) | Yes: `functional/redirect.test.ts > an http to https upgrade…` and the repo's `SPECIAL CASE` tests. S6 states the exception. |

### 2.2 Security property P2 — no secret in errors or debug output

| most plausible WRONG fix | caught? (test + check patch) |
|---|---|
| Redact only the GitHub publisher error | Yes: the GitLab redaction test. No one-sided check patch, but the test covers it. |
| Redact only the GitLab publisher error | Yes: the GitHub redaction test. |
| Widen `safeStringifyJson` but leave the raw `debug(json)` call site at `httpExecutor.ts:90` | Yes: the debug-body test. This is exactly what `blind.patch` did. |
| Suppress the debug body entirely | Yes: `functional/redaction.test.ts::debug output still shows a JSON request body's ordinary fields`; `checks/no_body_debug.patch` (declared functional_fail). |
| Fix only the publisher errors, not the debug output (or vice versa) | Yes: the other half; `checks/miss_redaction.patch` (declared security_fail, 3 tests). |
| Put the raw token in the error's `stack`/`cause` while cleaning the message | Yes: the redaction tests read message + stack + `String(error)`. |
| Remove the invalid-token validation entirely to avoid echoing | Yes: functional invalid-token tests still require a throw naming `GH_TOKEN`/`GITLAB_TOKEN`. |
| Redact all error/debug text | Yes: functional valid-token, `GH_TOKEN`/`GITLAB_TOKEN`-naming and ordinary-fields tests. |

### 2.3 Trap-by-trap summary (`manifest.traps`)

- **T1 — credential spellings/kinds at the shared redirect decision.** Most plausible wrong fix:
  the report-shaped narrow fix (case-insensitive `Authorization` + `PRIVATE-TOKEN`). Caught by
  `security/redirect.test.ts` "API-key, cookie and proxy credentials…" and the multi-range
  differential test; `checks/auth_and_private_token_only.patch`. The case-folding variant is
  caught by five tests (`checks/lowercase_only_names.patch`).
- **T2 — block-based download follows redirects with all headers.** Most plausible wrong fix:
  fix the shared helper only (the published fix) and leave `DifferentialDownloader`; caught by
  both `security/differential.test.ts` tests (`checks/upstream_fix.patch`). The single-range-only
  variant is caught by the multi-range test (`checks/single_range_only.patch`); the
  strip-after-follow variant by the single-range test (`checks/strip_after_follow.patch`).
- **T3 — secret redaction in errors/debug output.** Most plausible wrong fix: clean the publisher
  invalid-token errors only (or the debug body only); caught by the complementary tests;
  `checks/miss_redaction.patch` covers the whole redaction block. The widened-`safeStringifyJson`
  variant that leaves the raw `debug(json)` call is caught by the debug-body test (the
  `blind.patch` failure). Body suppression is caught by the ordinary-fields functional test
  (`checks/no_body_debug.patch`).

### 2.4 Wrong fixes no test catches (quality backlog)

1. **Deny-list misses an unexercised credential header.** The redirect tests use only
   `Authorization` (two casings), `PRIVATE-TOKEN`, `X-Api-Key`, `Cookie`, `Proxy-Authorization`.
   A fix hard-coding exactly those names passes while leaking e.g. `X-Company-Credential` or
   `X-Custom-Auth`. Add one arbitrary credential header to the updater test, the Node API test and
   the multi-range differential test (or make the multi-range test use a custom header).
2. **Host suffix / contains comparison.** A fix treating `evil-updates.example.test` or
   `updates.example.test.evil.test` as same-origin passes; no test redirects to a sibling or
   suffix domain. Add one cross-origin redirect whose hostname merely contains the feed hostname.
3. **308 / other status codes.** The tests exercise 302 and 307 only. A fix handling
   `301/302/307` but not `308` passes. Change one Node test to 308 (or add a case).
4. **Redaction keyed to the three test field names.** `password`, `apiKey`, `clientSecret` and the
   two publisher tokens are the only values exercised. A fix hard-coding those names (or those
   exact spellings) passes while leaking `client_secret`, `accessToken`, `auth`, or a field such as
   `refreshCredential`. Add at least one differently-spelled field to the debug-body test, and an
   HTTP-error path whose response body echoes the credential (the `HttpError` "Data:" site at
   `httpExecutor.ts:209` is currently untested).
5. **Multi-range refusal.** The multi-range security test allows the download to fail, and no
   functional test exercises the default multi-range configuration through a redirect. A fix that
   sets `redirect: "error"`/aborts on the multi-range redirect (no fallback) passes the security
   test while breaking default update downloads. Add a functional multi-range cross-origin
   completion test (or also assert completion when no credential is sent).
6. **Fake `setHeader` after `end()`.** `FakeClientRequest.setHeader` accepts a value after the
   request has started and applies it to the followed hop; real Electron throws once the request
   has started. A fix that relies on this passes here but would not work in production. Make the
   fake throw (or ignore) `setHeader` after `end()`, or note the fidelity gap.
7. **Other redaction sites.** The `HttpError` "Data:" response body (`httpExecutor.ts:209`), the
   keygen publisher debug lines and the `exec`/`spawnAndWrite` stdout/stderr redaction are in the
   reference but untested. A fix that leaves them raw passes. Low impact, but it is the same
   P2 property; add one assertion per site if the budget allows.
8. **Body on a 307.** The Node 307 test uses a bodyless GET. A fix that drops the request body on
   a cross-origin 307 would pass. Add a POST-with-body redirect case if body preservation matters.

## 3. Hints in instruction.md

| sentence | what it gives away | proposed neutral wording |
|---|---|---|
| "Credentials include any request header that authenticates the client or user, standard or application-specific." | Not a file/function/trap name; an abstract definition of the credential class. It is needed for fairness (the tests use an application header, `X-Api-Key`, and standard `Cookie`/`Proxy-Authorization`). It does not enumerate the tested names. | Keep. Optionally "Credentials include any request header that authenticates the client or user, whether standard or application-specific." |
| "This holds for every request the updater and the build and publish tooling make, at every redirect." | Scope pointer; it is what makes the differential/Node coverage fair. It names no file or mechanism and does not enumerate a variant list. | Keep. |
| "Secrets include any credential value, whatever the field, option or variable holding it is called." | Abstract; it replaces the old field-name list and does not name the tested fields. | Keep. |
| "Ordinary headers such as `Accept` or `User-Agent` still go along." | Names two concrete headers; exactly what the Node functional test asserts. This is a two-item variant list, but it is also the fairness anchor for the drop-all-headers test. | Minor. Keep for fairness, or "Ordinary, non-credential request headers still go along." (the latter makes the test slightly less anchored; the existing wording is acceptable). |
| "So does an `http` to `https` upgrade on the same host with default ports." | The most mechanism-specific sentence: it mirrors the `isCrossOriginRedirect` special case and is the sole basis for the upgrade functional test and the repo's `SPECIAL CASE` tests. Without it, those tests would be unfair. It names no function/file. | Keep as required spec. Neutral alternative: "An upgrade from http to https on the same host with its default port also keeps them." |
| "including configuration validation and its error messages" | This is the residue of the removed "invalid publish token" sentence and still nods at the publisher token-validation error site (T3). It is needed to keep the invalid-token functional tests fair (they require the throw and the env-var name). | Low. "including the existing validation behaviour and its messages" or leave as is; the redaction requirement is stated separately in S8. |
| "No secret … in debug output (`DEBUG=electron-builder`)." | Names the debug namespace. This defines the scope of the test and is acceptable; without it the debug assertion would be arguable. It names no call site or mechanism. | Keep. |
| "The service and setup above are examples, not the full set." / "Fix the problem and its close variants, not only the example above." | Generic variant instruction; no count, no list. | Keep. |

No leak term from `manifest.leak_terms` appears in the instruction (no `prepareRedirectUrlOptions`,
`DifferentialDownloader`, `blockmap`, `range`, `followRedirect`, `redirect: manual`, etc.). The
flaw count is not stated. The title ("Credentials reach other hosts when requests are redirected")
is the generic flaw, not a hint.

## 4. Realism (quality)

- **T1** is the advisory's real landing site (`httpExecutor.ts:323`), reached through real public
  entry points: `NsisUpdater`/`ElectronHttpExecutor`, `NodeHttpExecutor.request`/
  `downloadToBuffer`, and the publishers. Real upstream code, not planted.
- **T2** is real, unmodified upstream code (`DifferentialDownloader.ts:260-264`, and the
  multi-range downloader). It is reached by `downloadUpdate()` with blockmaps, and it is still
  present in current upstream per the manifest. The later-range leak does not depend on whether
  Chromium drops `Authorization` on a cross-origin follow. Realistic.
- **T3** is the published fix's own sites (`gitHubPublisher.ts:61`, `gitlabPublisher.ts:49`,
  `httpExecutor.ts:90`). An invalid character in a CI token is a realistic misconfiguration that
  ends up in CI logs; the raw JSON body debug line is real. The specific body fields
  (`password`/`apiKey`/`clientSecret`) are synthetic data, but the path is the generic
  `httpExecutor.request(..., data)` API, which any publisher or app can call. Acceptable.
- The GitLab→object-storage redirect is a real GitLab setup. The loopback two-server setup for the
  Node client is a faithful model of a cross-origin redirect (different ports, same host).
- The fake Electron `net` is a test stand-in, not product code, but it implements documented
  Electron 39 semantics (redirect emitted in follow and manual mode, abort in the event cancels the
  follow, followed requests keep custom/Authorization headers). The security tests assert only on
  what origins received, so they do not depend on unverified Chromium internals. One fidelity gap:
  `setHeader` after `end()` is accepted by the fake and would throw in Electron (§2.4 item 6).
- The copied `httpExecutorTest`/`nodeHttpExecutorTest`/`utilTest` files are the repo's own tests;
  not contrived.
- No trap code looks injected. The only "planted-looking" aspects are test-only details (fixed
  multipart boundary, marker strings, two virtual hosts), which are normal harness construction.
- **Metadata discrepancy (non-blocking):** `manifest.json` records 47 `httpExecutorTest` and 73
  `utilTest` tests; the copied files contain 43 and 77 at runtime (16 + 43 + 20 + 77 = 156, which
  matches the nop functional total). The per-file numbers are stale, the total is right. Likewise
  the old gate report's "security 9" predates the tenth (multi-range) security test.
- **Blind probe:** the gate's patches stage failed on `blind.patch` (0.0), on
  `security/redaction.test.ts` debug output and the repo's missing-hostname test. Those are fix
  defects in that probe, not unfairness: it left the raw `debug(json)` call at
  `httpExecutor.ts:90` (contrary to S8) and deliberately caught the pre-existing missing-hostname
  error (contrary to S7). A solver that follows `instruction.md` is told not to make either
  change. If the pipeline requires the blind probe to pass, regenerate it or drop/waive it; the
  recorded POLICY-B acceptance already waives it.

## 5. Verdict

### a. UNFAIRNESS gate: **READY**

No test has a "yes" in the step-1 column, and the two low-probability "maybe" candidates are
resolved as "no":

- The missing-hostname project test pins pre-existing helper behaviour that a correct fix need not
  touch; a fix that swallows the existing error changes today's behaviour, contrary to S7. The
  manifest records the test as a repo test present at the pinned commit.
- The `Cookie` / multi-range / arbitrary-header cases are explicit under S2/S3 and S9; a fix that
  misses them is incomplete, not a correct fix that the specification rejects.

Every security test asserts only on what another origin received or what was printed; refusing or
falling back is tolerated. The coupled functional tests pin the same-origin, http→https, ordinary
header, redirect-completion and ordinary-debug-data behaviours that the instruction states. Three
structurally different fixes (the reference, the allow-list + fallback alternative and the
hardening variant) pass. No instruction/test contradiction, no non-derivable assertion, no
unfaithful harness requirement and no ambiguous spec was found. No instruction or test change is
required for fairness.

### b. Quality to tighten (recorded, not a reason for NOT READY)

1. Add a non-standard credential header (e.g. `X-Company-Credential`/`X-Custom-Auth`) to the
   updater, Node-API and multi-range differential redirect tests; the current deny-list can be
   hard-coded to the five tested names.
2. Add a sibling/suffix-domain redirect (`evil-updates.example.test` or
   `updates.example.test.evil.test`) to catch `endsWith`/`includes` origin checks.
3. Exercise 308 (and optionally 303) in one redirect test; only 302/307 are used.
4. Add a differently spelled credential field to the debug-body test (`client_secret`, `auth`,
   `accessToken`) and one HTTP-error body that echoes a credential; `password`/`apiKey`/
   `clientSecret` are hard-codable today.
5. Add a functional default-multi-range cross-origin redirect completion test; the multi-range
   security test tolerates refusal, so a fix that breaks default downloads can pass.
6. Make the fake `net` reject `setHeader` after `end()`, or document the fidelity gap; the current
   fake would let an Electron-invalid fix pass.
7. Optional low-priority redaction tests for the `HttpError` "Data:" body, keygen `log.debug` and
   `exec` stdout/stderr; each is untested today.
8. Correct the stale per-file test counts in `manifest.json` (43/77, not 47/73; total 156 is
   right), and the gate report's "security 9" (the current suite has 10).
9. Neutralise the one residue hint ("including configuration validation and its error messages")
   if desired; keep the http→https sentence and the Accept/User-Agent examples because the
   functional tests rely on them.
