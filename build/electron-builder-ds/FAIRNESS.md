# FAIRNESS review — electron-builder-ds (pre-trial, 2026-10-20 upgrade)

Read: `instruction.md`, all files under `tests/`, `solution/fix.patch`, `manifest.json`, `notes.md`,
all 18 `checks/*.patch`. Nothing was run. Suite: 18 security + 165 functional (25 hidden functional,
43 `httpExecutorTest`, 20 `nodeHttpExecutorTest`, 77 `utilTest`).

| label | covering instruction sentence (short) |
|---|---|
| **G1** | "A credential is bound to the origin — the scheme, host and port — it was supplied for. No request the product makes may carry it to any other origin, at any hop and by any path, however that credential is expressed: as a request header (standard or application-specific, in any spelling or case), as connection-level authentication, or otherwise." |
| **G2** | "After a redirect to another origin the request may continue only without the credential. ... the operation it belongs to must still complete by its normal path or by an equivalent fallback; a clean internal failure is acceptable only where the overall operation still completes. A refusal or failure must not leave the credential with the other origin, must not crash, and must not break a later legitimate operation." |
| **G3** | "A request redirected within the same origin keeps its credentials and completes, and so does an upgrade from unencrypted to encrypted transport on the same host with standard ports." |
| **G4** | "After a redirect to another origin the request still completes there, and ordinary non-credential headers still travel with it. Private servers keep working." |
| **G5** | "A secret the product is given must not appear in clear text in any diagnostic output the product emits, whether an error message or debug output, and whatever name the field, option, argument or variable holding it has." |
| **G6** | "Every legitimate operation keeps working exactly as it does today, and no capability or result the product already provides is removed. Diagnostic output still contains everything that is not a secret, and a sanitized error still identifies which setting or variable is wrong." |

**no** = a fix meeting G1–G6 at any valid layer (dispatcher, handler, shared helper, Electron
executor; strip-and-continue or abort-with-fallback where G2 allows) passes; **maybe** = a defensible
reading permits a failing fix; **yes** = blocker.

---

## 1. Per-test fairness table

### 1.1 Security (18)

| file::name | what it asserts | instruction sentence that makes it fair | could a correct fix fail it? | risk |
|---|---|---|---|---|
| `security/redirect.test.ts::publishing HTTP client (Node) > standard and application credential headers are not forwarded to another origin` | 307 A→B; `Authorization`, `PRIVATE-TOKEN`, `X-Api-Key`, `Cookie`, `Proxy-Authorization`, `X-Amz-Security-Token` values absent from B | G1 ("standard or application-specific", "however ... expressed") | no — a general name predicate, an ordinary-header allowlist, or a central guard passes; a fixed two-name list is the intended wrong fix | low |
| `… > case and separator variants of credential header names are not forwarded to another origin` | 302 A→B; `AUTHORIZATION`, `PRIVATE_TOKEN`, `X_API_KEY`, `X-Auth-Token`, `X-Gitlab-Token`, `x-access-token` absent | G1 ("in any spelling or case") | no — case/separator folding is standard for HTTP header names | low |
| `… > a redirect to another port on the same host does not receive credentials` | 308 to the same host on a different port; `X-Api-Key` absent | G1 ("scheme, host and port") | no | low |
| `… > basic authentication credentials are not forwarded to another origin` | 302 A→B; the Node-encoded `Authorization: Basic` value from `options.auth` is absent | G1 ("as connection-level authentication"); standard expert knowledge: Node turns `RequestOptions.auth` into Authorization on the wire | no — a fix that strips the headers object but leaves `options.auth` is incomplete, and G1 names connection-level auth explicitly | low |
| `… > a download redirected to another origin does not receive the credential` | `downloadToBuffer` A→302→B; `Authorization` mark absent | G1 ("No request ... by any path") | no | low |
| `…::app updater (Electron net) > a full update download redirected to another origin does not receive the credential` | `NsisUpdater` with `requestHeaders` Authorization, differential disabled; no non-feed request carries the mark | G1 ("No request the product makes", "at any hop") | no — the shared helper and the independent `pass-alt` design both pass; `fakeElectron.ts` models Electron 39's ClientRequest redirect semantics (follow mode re-sends headers; `redirect`/`followRedirect`/`abort` supported) | medium |
| `security/differential.test.ts::differential download: the auth token is not sent to the host the update file redirects to` | single-range block download; `addAuthHeader` token absent outside the feed | G1 + G2 | no — strip-and-follow and abort+full-download fallback both pass; the test inspects only what the other origin received | low |
| `…::differential download with the default multi-range requests: an application credential header is not sent to the host the update file redirects to` | default multi-range path; `requestHeaders: X-Api-Key` absent outside the feed | G1 + G2 | no | low |
| `…::a package whose block map is fetched from the end of the file: the credential is not sent to the host that trailing range request redirects to` | web-package metadata; trailing-range block-map read redirects; `Authorization` absent outside the feed | G1 ("by any path", "No request the product makes") | no — a central redirect guard or the oracle's per-request listener passes; only a fix that misses this real request path fails, and missing a real request path is incomplete, not a different valid layer | medium |
| `security/redaction-runtime.test.ts::debug output (DEBUG=electron-builder) > a JSON request body's application-specific credential fields are not logged in clear` | request-body debug does not contain `private_token`, `apiKey`, `clientSecret`, `passphrase`, `credential` values | G5 ("any diagnostic output ... debug output") | no — hash, drop the field, or drop the line all pass; the coupled functional test fixes the ordinary-field floor | low |
| `…::error messages > a JSON error response's credential fields are not put in the error text` | 400 JSON error text does not contain the credential values | G5 ("whether an error message ...") | no — sanitizing the message while keeping the non-secret text passes | low |
| `security/redaction-build.test.ts::command error output > a credential in a failed command's standard error is not shown in clear` | `exec` error text does not contain the value printed to stderr via `options.env` | G5 ("any diagnostic output the product emits") | no — G5 is value-based, not name-based; output redaction, a logger filter, or a sanitizing wrapper passes | low |
| `… > a credential in a failed command's standard output is not shown in clear` | same for stdout (`--privateToken`) | G5 | no | low |
| `…::publish token configuration errors > GitHub: a GH_TOKEN with an invalid character is not echoed in the error` | invalid `GH_TOKEN` value absent from the constructor error | G5 | no — reporting the variable and the offending character is allowed | low |
| `… > GitLab: a GITLAB_TOKEN with an invalid character is not echoed in the error` | same for GitLab | G5 | no | low |
| `security/gitea-publisher.test.ts::artifact upload redirect > the access token is not sent to the storage origin an upload is redirected to` | 307 upload A→B; `token <mark>` absent at B | G1 ("No request the product makes"); the class is exported and wired into the publish-provider dispatch | no — strip-and-continue and abort+fallback pass; refusal without a completing operation is excluded by G2/G4 and the coupled functional test | low |
| `…::publisher token configuration > a malformed GITEA_TOKEN is not echoed in the configuration error` | invalid `GITEA_TOKEN` value absent | G5 | no | low |
| `…::debug output (DEBUG=electron-builder) > the publisher configuration's access token is not logged in clear` | constructor debug output does not contain the token | G5 | no — removing the token field or filtering the line passes; the functional test keeps the instance URL visible | low |

### 1.2 Hidden functional (25)

| file::name | what it asserts | instruction sentence that makes it fair | could a correct fix fail it? | risk |
|---|---|---|---|---|
| `functional/redirect.test.ts::app updater (Electron net) > full download through a redirect to another host completes with the right file` | cross-origin 302; download completes, sha512 matches | G2 + G4 | no | low |
| `… > full download through a redirect on the same server keeps the Authorization header` | same-origin 302; 200 only when the header arrives | G3 | no | low |
| `… > an http to https upgrade on the same host keeps the auth header` | http→https, standard ports; header required | G3 (explicitly stated) | no | low |
| `… > a GitLab token-protected asset redirected within the server is still found` | `PRIVATE-TOKEN` metadata; same-host 302 asset; update check succeeds | G3 + G6 | no | low |
| `functional/redirect.test.ts::publishing HTTP client (Node) > a redirect on the same origin keeps Authorization and PRIVATE-TOKEN` | same-origin 302; 200 only when both arrive | G3 | no | low |
| `… > a redirect to another origin completes and still sends the ordinary headers` | cross-origin 307 completes; `Accept` and non-empty `User-Agent` arrive | G2 + G4 | no — refusal without completion is excluded; over-broad header dropping fails G4 | low |
| `… > a download redirected to another origin completes` | cross-origin 302 download completes, payload correct | G2 + G4 | no | low |
| `… > a download redirected on the same origin keeps the credential and completes` | same-origin 302; 200 only with `Bearer keep-me` | G3 | no | low |
| `functional/differential.test.ts::differential download without redirects fetches only the changed blocks` | no redirect; every installer request carries `Range`; file hash correct | G6 ("exactly as it does today", "no capability ... removed") | no — disabling differential downloading whenever a credential is attached removes the capability G6 preserves; the test is the guard | low |
| `…::differential download through a redirect to another host completes with the right file` | cross-origin differential redirect; overall download completes with the correct file | G2 (abort + fallback accepted) | no | low |
| `…::differential download through a redirect on the same server keeps the auth header` | single-range; every `/storage/...` request carries `Bearer same-token` | G3 | no | low |
| `…::differential download through a redirect on the same server still yields the right file (multi-range)` | multi-range; every `/storage/...` request carries `x-api-key`; hash correct | G3 | no | low |
| `functional/redaction.test.ts::publish token configuration > GitHub: an invalid GH_TOKEN is still refused, naming the variable` | throws a message matching `GH_TOKEN` | G6 ("a sanitized error still identifies ... the variable") | no | low |
| `… > GitHub: a valid GH_TOKEN is accepted` | valid token constructs | G6 | no | low |
| `… > GitLab: an invalid GITLAB_TOKEN is still refused, naming the variable` | throws `GITLAB_TOKEN` | G6 | no | low |
| `… > GitLab: a valid GITLAB_TOKEN is accepted` | valid token constructs | G6 | no | low |
| `functional/redaction.test.ts::a failed command keeps its non-secret output and exit code in the error` | error contains `ordinary diagnostic text` and `Exit code: 2` | G6 ("Diagnostic output still contains everything that is not a secret") | no — catches delete-all-output over-redaction | low |
| `…::an HTTP error keeps the non-secret message from a JSON error response` | error contains `ordinary error detail` while the credential field is hidden | G6 | no — catches deleting the whole body | low |
| `…::debug output still shows a JSON request body's ordinary fields` | debug contains `v1.0.1-visibletag` | G6 | no — catches deleting the debug line | low |
| `functional/gitea.test.ts::artifact upload > an upload without a redirect sends the credential and completes` | one request; `Authorization: token <token>`; `name=` query | G6 | no | low |
| `… > an upload redirected on the same origin keeps the credential and completes` | same-origin 307; `/storage/...` carries the token | G3 | no | low |
| `… > an upload redirected to another origin completes` | cross-origin 307; one request at B; content-type octet-stream and the body | G2 + G4 | no — refusal fails G2/G4; dropping the body fails G4 | low |
| `functional/gitea.test.ts::configuration > a missing token is refused, naming the variable` | empty token/env throws `GITEA_TOKEN` | G6 | no | low |
| `… > a valid token is accepted` | valid token constructs | G6 | no | low |
| `… > debug output still shows the instance it publishes to` | debug contains `gitea.example.test` | G6 | no — catches deleting the whole debug line | low |

### 1.3 Project tests — `functional/project/httpExecutorTest.ts` (43)

Basis: G6 ("exactly as it does today", no capability removed) plus standard expert knowledge for
URL/origin semantics. All pass at nop (`notes.md`); the tests are visible in the repo, so every one
pins existing behaviour a correct fix need not change.

| file::name | what it asserts | fair basis | could a correct fix fail it? | risk |
|---|---|---|---|---|
| `…::HttpExecutor.prepareRedirectUrlOptions > basic functionality > should configure new options from redirect URL` | protocol/hostname/path from Location; header kept | G6; existing helper contract | no (only a rewrite that breaks URL handling) | low |
| `… > should handle relative redirect URLs` | relative Location keeps host, changes path | G6 | no | low |
| `… > should handle absolute redirect URLs with different domains` | absolute Location rewrites host/path | G6 | no | low |
| `… > authorization header handling > should preserve authorization header for same-origin redirects` | same-origin keeps `authorization` | G6 + G3 | no | low |
| `… > should strip authorization header for cross-origin redirects` | cross-origin removes `authorization`, no throw | G6 + G1 | no | low |
| `… > should preserve other headers when stripping authorization` | `User-Agent`/`Accept` survive | G6 + G4 | no | low |
| `… > should handle missing authorization header gracefully` | cross-origin, no credential: no throw, ordinary header kept | G6 + G4 | no | low |
| `… > should handle missing headers gracefully` | no headers: no throw, host rewritten | G6 | no | low |
| `… > cross-origin detection > hostname comparison > should treat same hostname as same-origin` | auth kept | G6 + standard expert knowledge | no | low |
| `… > should treat different hostname as cross-origin` | auth stripped | G1 | no | low |
| `… > should perform case-insensitive hostname comparison` | `API.GitHub.COM`→`api.github.com` keeps auth | standard expert knowledge | no | low |
| `… > should treat case-different hostnames as same-origin` | auth kept | same | no | low |
| `… > protocol comparison > should treat same protocol as same-origin (with same hostname)` | auth kept | standard expert knowledge | no | low |
| `… > should treat different protocol as cross-origin` | https→http strips | G1 ("scheme") | no | low |
| `… > should allow HTTP->HTTPS upgrade on standard ports` | 80→443 keeps auth | G3 (explicitly stated) | no | low |
| `… > should allow HTTP->HTTPS upgrade with implicit standard ports` | implicit ports keep auth | G3 | no | low |
| `… > should not allow HTTPS->HTTP downgrade` | strips auth | G1 | no | low |
| `… > port comparison > should treat same explicit ports as same-origin` | keeps auth | standard expert knowledge | no | low |
| `… > should treat different ports as cross-origin` | strips auth | G1 ("port") | no | low |
| `… > should treat implicit default ports as equivalent to explicit` | 443 == implicit, keeps | G3 ("standard ports") | no | low |
| `… > should treat implicit default port as equivalent to explicit (HTTP)` | 80 == implicit, keeps | G3 | no | low |
| `… > should treat explicit port as equivalent to implicit default` | keeps | standard expert knowledge | no | low |
| `… > should handle non-standard ports correctly` | 8080→443 strips | G1 ("port") | no | low |
| `… > real-world scenarios > should handle GitHub API to GitHub assets redirect` | strips to `objects.githubusercontent.com` | G1 + G6 | no | low |
| `… > should handle GitHub API to release-assets.githubusercontent.com redirect` | strips | G1 + G6 | no | low |
| `… > should handle Azure Blob Storage redirect` | strips | G1 + G6 | no | low |
| `… > should handle AWS S3 redirect` | strips | G1 + G6 | no | low |
| `… > should preserve authorization for same-service redirects` | keeps | G3 | no | low |
| `… > edge cases > should handle URLs with query parameters` | cross-origin strips, query kept in path | G1 + G6 | no | low |
| `… > should handle URLs with fragments` | same-origin, fragment dropped, auth kept | standard expert knowledge; G6 | no — a rewrite that mishandles fragments fails; the pinned helper already does it | low |
| `… > should handle URLs with userinfo (should be ignored in comparison)` | `user:pass@` ignored; auth kept | G1 defines origin as scheme/host/port; standard expert knowledge | no — treating userinfo as part of the origin contradicts G1 | low |
| `… > should handle IPv6 addresses` | `[::1]:8443` same-origin, auth kept | standard expert knowledge | no — only a rewritten comparison that mishandles IPv6 fails | low |
| `… > should handle empty path` | path defaults to `/`, auth kept | standard expert knowledge; G6 | no | low |
| `… > HttpExecutor.isCrossOriginRedirect > should be false for same hostname, protocol, and port` | false | standard expert knowledge | no | low |
| `… > should be true for different hostname` | true | G1 | no | low |
| `… > should be true for different protocol` | true | G1 | no | low |
| `… > should be true for different port` | true | G1 | no | low |
| `… > should be false for implicit vs explicit default port` | false | G3 | no | low |
| `… > should be false for case-insensitive hostname` | false | standard expert knowledge | no | low |
| `… > SPECIAL CASE: should be false for http -> https upgrade with default ports` | false | G3 | no | low |
| `… > SPECIAL CASE: should be false for http -> https upgrade with explicit default ports` | false | G3 | no | low |
| `… > SPECIAL CASE: should be true for http -> https upgrade with non-default ports` | true | G1 ("port") | no | low |
| `… > HttpExecutor error handling > should throw an error if hostname is missing and authorization header is present` | throws `Missing hostname in request options` | G6; existing helper contract | no — a correct fix need not touch this path; the test is visible | low |

### 1.4 Project tests — `functional/project/nodeHttpExecutorTest.ts` (20)

Basis: G6; the file is a copy of the repo's proxy tests and is unrelated to the advisory. All pass at nop.

| file::name | what it asserts | fair basis | could a correct fix fail it? | risk |
|---|---|---|---|---|
| `…::buildGotProxyAgent > returns undefined when no proxy is configured > no proxy env vars set` | undefined | G6 (unrelated subsystem) | no | low |
| `… > all proxy env vars are empty strings` | undefined | G6 | no | low |
| `… > all proxy env vars are whitespace-only` | undefined | G6 | no | low |
| `… > returns correct agent shape > only https key when HTTPS_PROXY is set` | https agent only | G6 | no | low |
| `… > only https key when https_proxy (lowercase) is set` | https agent only | G6 | no | low |
| `… > only http key when HTTP_PROXY is set` | http agent only | G6 | no | low |
| `… > only http key when http_proxy (lowercase) is set` | http agent only | G6 | no | low |
| `… > both keys when HTTPS_PROXY and HTTP_PROXY are set` | both agents | G6 | no | low |
| `… > only https key when HTTPS_PROXY is valid but HTTP_PROXY is whitespace-only` | only https | G6 | no | low |
| `… > falls back to https_proxy when HTTPS_PROXY is whitespace-only` | https agent | G6 | no | low |
| `… > falls back to http_proxy when HTTP_PROXY is whitespace-only` | http agent | G6 | no | low |
| `… > env var precedence > HTTPS_PROXY takes precedence over https_proxy when both are set` | uppercase host wins | G6 | no | low |
| `… > HTTP_PROXY takes precedence over http_proxy when both are set` | uppercase host wins | G6 | no | low |
| `… > agent instances > http agent is an HttpProxyAgent` | constructor name | G6 | no | low |
| `… > https agent is an HttpsProxyAgent` | constructor name | G6 | no | low |
| `…::NodeHttpExecutor.createRequest > proxy agent assignment > sets HttpsProxyAgent when https_proxy is set and protocol is https:` | `options.agent` | G6 | no | low |
| `… > sets HttpProxyAgent when http_proxy is set and protocol is http:` | `options.agent` | G6 | no | low |
| `… > does not set agent when no proxy env vars are set` | undefined | G6 | no | low |
| `… > does not set agent when https_proxy is set but protocol is http: (mismatch)` | undefined | G6 | no | low |
| `… > does not set agent when http_proxy is set but protocol is https: (mismatch)` | undefined | G6 | no | low |

### 1.5 Project tests — `functional/project/utilTest.ts` (77)

Basis: G6 and the repo's pinned `removePassword`/env-helper behaviour. The oracle only adds
`privateToken` and `apiKey` to `removePassword`; no snapshot input contains those stems, so the
snapshots are unchanged. All pass at nop.

| file::name | what it asserts | fair basis | could a correct fix fail it? | risk |
|---|---|---|---|---|
| `…::removePassword: --accessKey > handles unquoted value (snapshot)` | value replaced by sha256 hash, flag kept | G6; repo snapshot | no | low |
| `… > handles double-quoted value (snapshot)` | same with quotes | G6 | no | low |
| `… > handles single-quoted value (snapshot)` | same with single quotes | G6 | no | low |
| `…::removePassword: --secretKey > handles unquoted value (snapshot)` | hashed | G6 | no | low |
| `… > handles double-quoted value (snapshot)` | hashed | G6 | no | low |
| `… > handles single-quoted value (snapshot)` | hashed | G6 | no | low |
| `…::removePassword: -p > handles unquoted value (snapshot)` | hashed | G6 | no | low |
| `… > handles double-quoted value (snapshot)` | hashed | G6 | no | low |
| `… > handles single-quoted value (snapshot)` | hashed | G6 | no | low |
| `…::removePassword: -pass > handles unquoted value (snapshot)` | hashed | G6 | no | low |
| `… > handles double-quoted value (snapshot)` | hashed | G6 | no | low |
| `… > handles single-quoted value (snapshot)` | hashed | G6 | no | low |
| `…::removePassword: -String > handles unquoted value (snapshot)` | hashed | G6 | no | low |
| `… > handles double-quoted value (snapshot)` | hashed | G6 | no | low |
| `… > handles single-quoted value (snapshot)` | hashed | G6 | no | low |
| `…::removePassword: /p > handles unquoted value (snapshot)` | hashed | G6 | no | low |
| `… > handles double-quoted value (snapshot)` | hashed | G6 | no | low |
| `… > handles single-quoted value (snapshot)` | hashed | G6 | no | low |
| `… > handles Mac host path without hashing (snapshot)` | `\\Mac\Host\...` unchanged | G6; existing word-boundary rule | no | low |
| `…::removePassword: pass: > handles unquoted value (snapshot)` | hashed after `pass:` | G6 | no | low |
| `… > handles double-quoted value (snapshot)` | hashed | G6 | no | low |
| `… > handles single-quoted value (snapshot)` | hashed | G6 | no | low |
| `…::removePassword: /b … /c block > handles /b … /c block (snapshot)` | block secret hashed, markers kept | G6 | no | low |
| `…::removePassword: word boundary protection > does not redact -path argument` | unchanged | G6 | no | low |
| `… > does not redact -pid argument` | unchanged | G6 | no | low |
| `… > does not redact -StringLength argument` | unchanged | G6 | no | low |
| `… > does not redact a bare file path containing /p` | unchanged | G6 | no | low |
| `… > redacts -passphrase argument` | no secret | G6 | no | low |
| `… > still redacts -p when it is a standalone flag` | no secret | G6 | no | low |
| `… > still redacts /p when preceded by whitespace` | no secret | G6 | no | low |
| `…::removePassword: case-insensitive flag matching > redacts -P (uppercase variant of -p)` | no secret | G6 | no | low |
| `… > redacts -PASS (uppercase variant of -pass)` | no secret | G6 | no | low |
| `… > redacts -STRING (uppercase variant of -String)` | no secret | G6 | no | low |
| `… > redacts --ACCESSKEY (uppercase variant of --accessKey)` | no secret | G6 | no | low |
| `…::removePassword: pass: colon-separator style > redacts pass:value with no space (OpenSSL style)` | value hashed, `pass:` and `(sha256 hash)` kept | G6 | no | low |
| `… > redacts pass: value with space` | hashed | G6 | no | low |
| `…::removePassword: multiple keys in one string > handles two keys unquoted (snapshot)` | both hashed | G6 | no | low |
| `… > handles mixed quoted and unquoted keys (snapshot)` | both hashed | G6 | no | low |
| `… > handles several keys and /b … /c block (snapshot)` | all hashed | G6 | no | low |
| `…::validateEnvVarUrl > returns null when env var is not set` | null | G6 (unrelated helper) | no | low |
| `… > throws when value is not a valid URL` | throws naming var | G6 | no | low |
| `… > throws when protocol is http (non-https)` | throws | G6 | no | low |
| `… > throws when protocol is file` | throws | G6 | no | low |
| `… > returns the URL string for a valid https URL` | returned | G6 | no | low |
| `… > returns the URL string unchanged when it has a path and query` | returned | G6 | no | low |
| `…::filterSensitiveEnv > redacts values for keys containing KEY` | sha256 hash | G6 | no | low |
| `… > redacts values for keys containing TOKEN` | hash | G6 | no | low |
| `… > redacts values for keys containing SECRET` | hash | G6 | no | low |
| `… > redacts values for keys containing PASSWORD` | hash | G6 | no | low |
| `… > is case-insensitive on the key name` | hash | G6 | no | low |
| `… > does not redact values for non-sensitive keys` | unchanged | G6 | no | low |
| `… > replaces the entire value, not just the sensitive substring within it` | whole value hashed | G6 | no | low |
| `… > handles a mixed env object, redacting only sensitive keys` | mixed | G6 | no | low |
| `… > redacts values for keys containing CSC (code-signing certificate vars)` | hash | G6 | no | low |
| `… > redacts values for WIN_CSC_LINK` | hash | G6 | no | low |
| `… > redacts values for keys containing CREDENTIAL` | hash | G6 | no | low |
| `… > does not redact unrelated LINK or CSC-free vars` | unchanged | G6 | no | low |
| `…::resolveEnvShellValue > returns null when env var is not set` | null | G6 | no | low |
| `… > returns null when env var is empty string` | null | G6 | no | low |
| `… > returns null when env var is whitespace only` | null | G6 | no | low |
| `… > returns the value trimmed of surrounding whitespace` | trimmed | G6 | no | low |
| `… > throws on shell-unsafe character: ;` | throws | G6 | no | low |
| `… > throws on shell-unsafe character: &` | throws | G6 | no | low |
| `… > throws on shell-unsafe character: \|` | throws | G6 | no | low |
| `… > throws on shell-unsafe character: \`` | throws | G6 | no | low |
| `… > throws on shell-unsafe character: $` | throws | G6 | no | low |
| `… > throws on shell-unsafe character: <` | throws | G6 | no | low |
| `… > throws on shell-unsafe character: >` | throws | G6 | no | low |
| `… > throws on shell-unsafe character: "` | throws | G6 | no | low |
| `… > throws on shell-unsafe character: '` | throws | G6 | no | low |
| `… > throws on backslash on non-Windows platforms` | throws on Linux | G6 | no | low |
| `…::spawnAndWriteWithOutput > resolves with captured stdout and stderr` | captured values | G6 | no | low |
| `… > resolves with empty stdout and stderr when process emits nothing` | empty | G6 | no | low |
| `… > rejects with ExecError on non-zero exit code` | ExecError | G6 | no | low |
| `… > ExecError includes stdout and stderr from failed process` | message contains `stdoutval`/`stderrval`, exitCode 2 | G6 | no — hashing all child output would fail, but that violates G6 | low |
| `… > writes data to stdin and reads it back` | round-trip | G6 | no | low |
| `… > rejects with a timeout error when process does not finish within 4 minutes` | timeout message | G6 | no | low |

---

## 2. Leniency (QUALITY, non-blocking)

| property | most plausible wrong fix | caught? |
|---|---|---|
| P1 credential/origin | pinned exact-lowercase `authorization` + the one reported GitLab token, matched without folding | yes — `security/redirect.test.ts` standard/case/port/Basic/download, multi-range differential, Gitea upload; `sf-core-redirect` (7), `sf-named-headers-only` (4), `sf-lowercase-names` (6) |
| P1 variants | single-range only; follow-then-strip; published sites only; miss `options.auth`; miss the trailing range; miss the Electron full download; refuse all cross-origin; strip same-origin too; drop all headers | yes — multi-range (`sf-single-range-only`); both differential (`sf-follow-then-strip`); differential + Gitea (`sf-unlisted-route`); Basic test; embedded test (`sf-embedded-blockmap`); full-download test; functional completion (`ff-refuse-cross-origin`); functional same-origin (`ff-strip-every-redirect`); ordinary-header/Gitea body (`ff-drop-all-headers`) |
| P2 secrets | extend `safeStringifyJson` only | yes — both runtime tests (`sf-runtime-redaction`, 2) and command/token tests (`sf-build-redaction`, 4) |
| P2 variants | remove the debug line; delete child output; delete the whole error body; drop the variable name; fix one Gitea output only | yes — coupled functional redaction tests; `sf-gitea-upload-redirect`, `sf-gitea-token-error`, `sf-gitea-debug` (one each) |

| trap | most plausible wrong fix | caught? |
|---|---|---|
| T1 core redirect shapes | fixed list of `authorization` + the reported token | yes — redirect standard/case/port/Basic/download and multi-range; `sf-named-headers-only`, `sf-lowercase-names`, `sf-core-redirect` |
| T2 block-based download redirects | fix only single-range, or follow first then strip | yes — differential multi-range (`sf-single-range-only`), both differential tests (`sf-follow-then-strip`, `sf-differential`) |
| T8 embedded trailing range | fix the two visible range paths, leave the trailing-range read | yes — embedded test (`sf-embedded-blockmap`) |
| T3 runtime redaction | extend `safeStringifyJson` only | yes — both runtime tests (`sf-runtime-redaction`) |
| T4 build/config redaction | fix publisher token messages only, leave `exec` raw (or reverse) | yes — both command tests and both token tests (`sf-build-redaction`) |
| T5 Gitea upload redirect | reissue `send` with the same options/headers | yes — gitea upload test (`sf-gitea-upload-redirect`); refusal caught by functional cross-origin upload |
| T6 Gitea token error | echo `JSON.stringify(token)` | yes — malformed-token test (`sf-gitea-token-error`) |
| T7 Gitea debug config | log the resolved config including the token | yes — debug test (`sf-gitea-debug`) |

| wrong fix no test catches |
|---|
| fixed header list covering only tested names (`X-Auth-Signature`, `X-Session-Id`, `X-CSRF-Token` are untested) |
| fixed JSON-body/error field list covering only tested names (`secret`, `accessKey`, `passwd` are untested) |
| in-place mutation of the caller's shared `headers` object instead of copying |
| cross-origin redirect of the updater's metadata request (latest-*.yml) with `requestHeaders`/GitLab token — no security test drives it |
| non-JSON error bodies and a raw body left in `error.data`/`cause` while the message is sanitized |
| credential moved into the URL query or request body on redirect (assertions inspect headers; the Gitea body check covers only that publisher) |
| reversible encoding (base64) instead of redaction |
| `removePassword` only for the two tested stems / only the space-separated form |

---

## 3. Hints (QUALITY, non-blocking)

| quote | why it is a hint | proposed neutral wording |
|---|---|---|
| "as a request header (standard or application-specific, in any spelling or case), as connection-level authentication, or otherwise" | variant list naming the T1 shapes | "however that credential is expressed" |
| "whether an error message or debug output" | variant list naming the two diagnostic channels | "in any diagnostic output the product emits" |
| "whatever name the field, option, argument or variable holding it has" | variant list of secret containers | "however it is named or carried" |
| "by an equivalent fallback" | names the abort-then-full-download fix approach for the block-based routes | "the operation it belongs to must still complete" |
| "an upgrade from unencrypted to encrypted transport on the same host with standard ports" | names the `isCrossOriginRedirect` special case; needed for fairness, so retain the substance | "a transport upgrade on the same host on standard ports" |
| "Private servers keep working." | product-category pointer to the self-hosted publisher sibling | delete; G6 already covers it |

No sentence names a file, function, package, class, header name, "differential", "blockmap",
"Gitea", a route, or a flaw count.

---

## 4. Realism (QUALITY, non-blocking)

| trap/site | realistic? | note |
|---|---|---|
| T1, T3, T4 | yes | real upstream code at the pinned commit and the published fix's own sites; documented entry points |
| T2, T8 | yes | real, unmodified upstream code in `DifferentialDownloader.ts`, `multipleRangeDownloader.ts` and the `readRemoteBytes` trailing-range helper; still on upstream main; realistic by definition |
| T5 | yes (mild) | injected self-hosted publisher, wired into `PublishManager.createPublisher`/`requireProviderClass` and exported; code is not deceptive. Mild: a 307-to-object-storage on a Gitea asset `PUT` is plausible behind a reverse proxy but not typical Gitea (it stores the asset itself), and Gitea normally uses `POST` for release assets |
| T6 | yes | mirrors the pre-fix GitHub/GitLab `JSON.stringify(token)` error |
| T7 | yes (mild) | logging a new publisher's resolved config is a classic copy-paste debug defect; blatant once the file is opened |
| harness | yes | `fakeElectron.ts` is a documented in-process stand-in for Electron 39 `net`/`session`/`app`; the real `electron-updater` path is driven; no network/GPU/GUI |

---

## 3a. Required: generalize

1. **"Private servers keep working."** — a deployment-category sentence that exists only to reassure
   the added self-hosted publisher path. Delete it; "Every legitimate operation keeps working exactly
   as it does today" states the property once over the product's operations.
2. **"whether an error message or debug output"** — enumerates channels; the property is already
   stated over "any diagnostic output the product emits". Delete the enumeration.

(The http→https sentence is a legitimate contract, not a route pointer; removing it would make
`functional/redirect.test.ts::an http to https upgrade ...` unfair. Keep its substance.)

---

## 5. Verdict

**READY.** G1 read literally covers every security route: it binds the credential to scheme/host/port
and forbids any request the product makes from carrying it to another origin "at any hop and by any
path"; G5 covers any diagnostic output regardless of the holding name. G3/G4/G6 cover the functional
contracts. The oracle passes the recorded upgrade runs (6/6 redirect and 3/3 differential; the other
9 security tests unchanged from the verified build; 165/165 functional), and the independent
`pass-alt`/`pass-hardening` designs pass. The security tests assert only on what the other origin
received, so a dispatcher guard, handler guard, strip-and-continue, or abort-with-fallback all pass;
completion is required only where G2/G4 require it. No row is "yes" or an unresolved "maybe": the
only defensible one — disabling differential download whenever a credential is attached — removes a
capability G6 preserves, so it is not a correct fix.

**Required: generalize** — (1) delete "Private servers keep working."; (2) replace "whether an error
message or debug output" with "in any diagnostic output the product emits".

**Quality to tighten** — add `X-Auth-Signature`/`X-Session-Id` to the standard redirect test and
`secret`/`accessKey` to each runtime redaction body; add a security test for a cross-origin metadata
redirect; add a caller-headers non-mutation test or record the `notes.md` out-of-scope line; add a
non-JSON/`error.data` test if G5 covers it; neutralize the hint wording in §3.

**Human review:** confirm the in-process `fakeElectron` stand-in is accepted as faithful to Electron
39 for the full-download test, and that the two new security tests (full download, embedded trailing
range) receive the full launcher re-gate rather than only the targeted runs in `notes.md`.

GATE_A: READY
NEEDS_HUMAN_REVIEW: YES
