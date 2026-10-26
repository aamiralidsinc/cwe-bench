# electron-builder-credential-leakage: build notes

- Start (UTC): 2026-10-17T04:27:40Z
- End (UTC): 2026-10-17T05:31:05Z
- Builder prompt: build-v1, pattern A+B, track mined.

## Levers

- **T1, input shapes at the landing site.** The shared redirect helper drops only the lower-case `authorization` key. It is tested with a capitalised Authorization, PRIVATE-TOKEN, and API-key + cookie + proxy credentials, through the Electron updater and the Node publishing client. Lever: `packages/builder-util-runtime/src/httpExecutor.ts:323`.
- **T2, pattern B uncovered route.** The block-based update download follows a redirect with all its headers, then sends later ranges straight to the new host. This route never calls the helper. Lever: `packages/electron-updater/src/differentialDownloader/DifferentialDownloader.ts:260-264`. Reason to dismiss: another subsystem, and comments say "Electron net handles redirects".
- **T3, pattern A far sites (redaction).** Publisher invalid-token errors echo the token, and the debug log prints JSON request bodies raw. Lever: `packages/electron-publish/src/gitHubPublisher.ts:61`, `packages/electron-publish/src/gitlabPublisher.ts:49`, `packages/builder-util-runtime/src/httpExecutor.ts:90`. Reason to dismiss: a logging concern in other packages.

## Verified

- Fix 22a7532b's parent is the pinned commit 8a035f83. Its regression tests are not present at the pinned commit.
- Electron v39.8.5 source (read-only):
  - `net-client-request.ts` emits `redirect` in both follow and manual mode.
  - `electron_api_url_loader.cc`: `abort()` inside the event cancels the follow.
  - Chromium `redirect_util.cc` keeps custom headers and Authorization on a followed redirect.
  - The fake `net` in `tests/support/fakeElectron.ts` implements exactly these semantics.
- Consequence: the published GitLabProvider `redirect:"manual"` change, and the screener's Provider-metadata route, change nothing behaviourally. The executor's listener already routes those requests through the helper. They are not used as levers, and the register row says so.
- Local nop: 9/9 security tests fail, each on its leak assertion; 156/156 functional tests pass.
- Local reference: 1.0. tsc reports no errors after the rebuild.
- All 13 check patches behave as declared locally. hostname_only_compare is caught by the repo's own port tests, so it is declared `functional_fail`.
- Gate stages:
  - static: only blind and FAIRNESS remain.
  - nop: pass.
  - oracle: pass x3, after one infrastructure retry ("network not found" from a concurrent prune).
  - patches: 13/13 as declared, after one infrastructure retry (same error).

## Could not verify

- Real Electron runtime behaviour. No Electron binary or GUI is available, so behaviour is modelled from source, not executed.
- Whether Electron's network service drops `Authorization` on a cross-origin follow. The T2 test leaks via the later ranges regardless.
- The multi-range route (multipleRangeDownloader). It is real by reading, closed in the reference fix, and untested (same concept as T2).
- Upstream `present_in_latest` was checked by reading current master files only.

## Test infrastructure

- test.sh rebuilds the four packages under test from `/app` source with `tsc -p … --noEmitOnError false`. Type errors (for example noUnusedLocals) therefore never block grading.
- The tests load the compiled output natively. Vite's ESM transform breaks the source's `import * as` CommonJS calls.
- Project tests copied:
  - httpExecutorTest.
  - nodeHttpExecutorTest.
  - utilTest, with its snapshot. Its Windows-only skipped case was dropped, because score.py counts skips as failures.

## Out of scope (not built on)

- The redirect helper shallow-copies its options and deletes from the caller's headers object.
- Upstream's later `feedBaseUrl` origin gating suggests related follow-up advisories.

## Fairness revision (2026-10-17)

- instruction.md: removed the invalid-publish-token sentence (folded into "including configuration validation and its error messages"); replaced the credential and secret variant lists with neutral wording.
- Added security test for the default multi-range block-based download (X-Api-Key via requestHeaders, CDN answers multipart/byteranges, fallback allowed). Fails at nop and with upstream_fix.patch; passes with the reference and alt patches.
- New check `single_range_only.patch` (security_fail): reference minus the multi-range listeners.
- functional/differential.test.ts same-server test loosened: requires Authorization on the redirect target and a correct file, no longer that it stays block-based (a full-download fallback on any redirect is allowed).
