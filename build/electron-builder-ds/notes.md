# electron-builder-ds — build notes

- Start (UTC): 2026-10-18T19:12:00Z
- End (UTC): (in progress)
- Builder prompt: build-v1, pattern A+B, track injected.
- Candidate: GHSA-P2F4-R6V6-J797 / CVE-2026-54673, electron-userland/electron-builder.
- Pinned: 8a035f836bb79d5346c69246530190dd72ec4519, direct parent of the published fix
  22a7532bd01b9fb42cff7c58d599c7ad683569fe (verified with git log).
- Injection: `environment/injection.patch` adds a realistic Gitea publisher (publish path) whose
  request/error/debug code sits at the same two recurring trust decisions as the advisory
  (which origin may receive an attached credential; which text may carry a secret).

## Design (before building)

Published-fix contract: on a cross-origin redirect, every credential header is dropped for every
request made by the updater, publisher and build tooling, and no configured secret appears in an
error message or `DEBUG=electron-builder` output.

### Levers (each with its own reason a solver would dismiss or skip it)

- **T1 — A, landing (input shapes).** `builder-util-runtime/src/httpExecutor.ts:323`: the redirect
  helper strips only the exact lower-case `authorization` key. Tested with `Authorization`,
  `PRIVATE-TOKEN`, `X-Api-Key`, `Cookie`, `Proxy-Authorization`, underscore spellings, and a
  cross-origin redirect reached by changing the port, through the Node executor used by publishing.
  *Dismiss:* the report's example is a GitLab token; adding that one header looks sufficient.
  Coupled functional: same-origin redirects keep credentials; an `http`→`https` same-host upgrade
  keeps them; ordinary headers survive cross-origin; the redirected request still completes.
- **T2 — B, uncovered route (two real upstream paths).**
  `electron-updater/src/differentialDownloader/DifferentialDownloader.ts:260-264` re-issues the
  redirect itself with `followRedirect()` and keeps `requestOptions` for later ranges;
  `multipleRangeDownloader.ts:73/96` registers no redirect handling at all. Both are reached by
  `AppUpdater.downloadUpdate()` with a blockmap and a 302 to another origin.
  *Dismiss:* a separate optimisation subsystem in another package; comments claim Electron handles
  redirects. Coupled functional: redirect-free differential download still fetches only changed
  blocks; a same-origin redirect keeps the credential and still yields the right file.
- **T3 — A far site (runtime redaction).** `httpExecutor.ts:90` logs a JSON request body raw under
  `DEBUG=electron-builder`; `httpExecutor.ts:209` puts a raw JSON error body into the HttpError
  text; `safeStringifyJson` only knows a few name shapes (`apiKey`, `clientSecret`, `passphrase`,
  `credential`, `PRIVATE-TOKEN` are missed). *Dismiss:* a logging concern in the same file, and the
  existing redactor "already covers token/password". Coupled functional: non-secret fields and
  non-secret options are still printed.
- **T4 — A far site (build/config redaction).** `builder-util/src/util.ts:51` misses the
  `privateToken`/`apiKey` argument stems; `:186/:192` append raw child stdout/stderr to the error;
  `electron-publish/src/gitHubPublisher.ts:61` and `gitlabPublisher.ts:49` echo the token in the
  invalid-token error. *Dismiss:* build-time command output and configuration validation look local
  and unrelated to an HTTP redirect. Coupled functional: non-secret arguments and stderr remain in
  the error; the error code is unchanged; valid tokens still construct.
- **T5 — injected sibling (redirect decision).** New `electron-publish/src/giteaPublisher.ts`
  handles a 307 on an artifact upload by re-issuing the request to the Location with the same
  options/headers. Reached by `GiteaPublisher.upload()`. *Dismiss:* uploads to storage look like a
  publisher concern, not an updater redirect; the published fix never enters this file.
  Coupled functional: an unredirected upload works; a same-origin redirect keeps the credential and
  completes; ordinary headers still arrive.
- **T6 — injected sibling (output decision).** Same publisher's constructor echoes an invalid token
  in its `InvalidConfigurationError`. *Dismiss:* configuration validation is unrelated to the
  reported leak; the published fix only edited the GitHub/GitLab publishers. Coupled functional:
  invalid token is still refused (message names the env var), valid token constructs.
- **T7 — injected sibling (output decision).** Same publisher logs its resolved configuration,
  token included, with `log.debug` when `DEBUG=electron-builder` is on. *Dismiss:* debug-only output
  of a constructor looks harmless. Coupled functional: the instance URL is still shown in debug,
  and nothing is logged when debug is off.

### Producer off the check's path

The header-name/value pair is produced by mappers (`GitLabProvider.setAuthHeaderForToken`, the
injected publisher's auth header) that the redirect decision never calls; the redaction decision
depends on field/argument names produced by callers/serializers elsewhere.

### Sites/routes/shapes covered by security tests

- Sites: shared redirect helper, the two differential download request builders, request-body debug,
  JSON error text, `safeStringifyJson` shapes, `removePassword`/`exec` error text, the two publisher
  constructors, and the injected publisher's upload redirect, error and debug lines.
- Shapes: capitalised/upper-case/lower-case header names, hyphen and underscore separators,
  proprietary token headers, cookies and proxy credentials, several at once, origin change by host
  and by port; field/argument names `apiKey`, `api_key`, `clientSecret`, `passphrase`, `credential`,
  `PRIVATE-TOKEN`, `privateToken`, `X_API_KEY`.
- Functional: same-origin redirects and the `http`→`https` same-host upgrade keep credentials,
  non-credential headers and cookies survive cross-origin, legitimate redirects complete, no
  differential/update/publish path is removed, redaction keeps non-secret output.

## Fairness revision (2026-10-19)

Applied the pre-trial FAIRNESS review (`FAIRNESS.md`, Required items 1–6).

- **R1 — instruction contradiction.** The Contracts bullet now says the request must continue at
  the new origin without the credential; a sub-request may fail cleanly only where the operation
  completes by an equivalent fallback. The old "may continue without it or fail cleanly" wording is
  gone, so the cross-origin completion functional tests are no longer contradicted.
- **R2 — T5–T7 reachability.** `environment/injection.patch` now wires `gitea` into the real publish
  paths: a `case "gitea"` in `PublishManager.createPublisher` and in `requireProviderClass`, plus
  the `GiteaOptions`/`PublishProvider` additions. `GiteaPublisher` is therefore reachable through the
  normal publish-provider dispatch, not only by direct import. T5–T7 are retained. (Dry-run: the
  patched injection applies cleanly to the pinned tree.)
- **R3 — multi-range same-origin leniency.** `functional/differential.test.ts::… still yields the
  right file (multi-range)` now asserts every `/storage/…` request carries
  `x-api-key: same-origin-key`, matching the single-range test.
- **R4 — credential-coverage gap.** `security/redirect.test.ts` adds `X-Amz-Security-Token` (outside
  the previously tested name families) to the standard header test and a new Basic-authentication
  (`options.auth`) redirect test through `httpExecutor.request`.
- **R5 — output/body gaps.** `functional/gitea.test.ts::… an upload redirected to another origin
  completes` now asserts the upload body reaches the storage origin, and
  `functional/redaction.test.ts` gains "an HTTP error keeps the non-secret message from a JSON error
  response".
- **R6 — hints.** Deleted "The example above is one instance…" and the "including configuration
  validation and its error messages" tail; merged "Fix the problem and its close variants…" and
  "Do not special-case the example." into "Fix the underlying behaviour; do not special-case the
  scenario above."

Counts after the revision: 16 security tests (was 15) and 165 functional tests (was 164; one added
redaction test). The oracle needed no change: its redirect helper already deletes `options.auth` on
cross-origin and its credential-name pattern already matches `X-Amz-Security-Token`.

## Verified

- The fix commit 22a7532b's direct parent is 8a035f83 (git log); the pinned tree has none of the
  advisory's regression tests (the fix adds them to test/src/httpExecutorTest.ts).
- The published `GitLabProvider` `redirect:"manual"` change is NOT behavioural at Electron 39:
  `ElectronHttpExecutor.addRedirectHandlers` runs in follow mode too, so metadata requests already
  go through the shared helper. It is covered by a functional test, not used as a lever.
- The two block-based download routes are real at the pinned commit and still present on current
  upstream main; both security tests fail on the pinned+injection copy on the leak assertion.
- The three injected gaps are reachable through the exported publisher class; their security tests
  fail on the pinned+injection copy.
- Local runs in the task image:
  - nop (pre-fairness revision): security 0/15, functional 164/164 (also through tests/test.sh
    itself: reward 0.0).
  - oracle (pre-fairness revision): security 15/15, functional 164/164 (through tests/test.sh
    itself: reward 1.0); `tsc -p` reports 0 errors for the four packages.
  - After the fairness revision the same gates were re-run: nop security 16/16 failing,
    functional 165/165 passing; oracle and the check patches are re-run below.
  - every checks/*.patch behaves as declared, with all four packages rebuilt from source each time
    (post-revision counts from the 2026-10-19 gate run):
    - security_fail (security fails, functional 0): sf-core-redirect 7 (the added Basic-auth test
      is one more), sf-differential 2, sf-runtime-redaction 2, sf-build-redaction 4,
      sf-gitea-upload-redirect 1, sf-gitea-token-error 1, sf-gitea-debug 1,
      sf-named-headers-only 4, sf-lowercase-names 6, sf-single-range-only 1,
      sf-follow-then-strip 2, sf-unlisted-route 5.
    - functional_fail: ff-strip-every-redirect 24, ff-refuse-cross-origin 20 (plus 3 security
      tests that also fail because the refusal happens before their assertion path),
      ff-drop-all-headers 29.
    - pass: pass-hardening 181/181, pass-alt 181/181.
  - Post-revision gate: nop PASSED (16 security / 165 functional), oracle PASSED (3 runs,
    16/16 + 165/165), patches PASSED (17/17). Static passes except the separately-wired
    blind patch.
- Gate: nop PASSED (15 security / 164 functional); oracle PASSED on 3 runs. The patches stage is
  the last stage run by the builder.
- The project's own tests (httpExecutorTest 47, nodeHttpExecutorTest 20, utilTest 76) pass at the
  pinned commit and with the oracle.

## Test infrastructure

- test.sh rebuilds the four packages under test from `/app` source with `tsc -p … --noEmitOnError
  false`, after deleting both `out/` and the package's `tsconfig.tsbuildinfo`. The second deletion
  matters: with a stale incremental state TypeScript considers a project whose `out/` was deleted
  up to date and emits nothing, so the hidden tests could not import the package.
- The tests load the compiled output natively (Vite resolves the workspace package names), as the
  repo's own tests do.
- `tests/vitest.config.mjs` sets `DEBUG=electron-builder` before modules load: the product logger
  snapshots the flag at import time.
- Project tests copied: `httpExecutorTest` (47), `nodeHttpExecutorTest` (20), `utilTest` with its
  snapshot (76; the Windows-only case is skipped by the file itself on Linux).

## Could not verify

- Real Electron runtime behaviour; the in-process stand-in models Electron 39's ClientRequest
  redirect semantics from source, as in the earlier build of this advisory.
- `DifferentialDownloader.readRemoteBytes` redirects: real and present upstream, but not built
  (needs an embedded-blockmap updater); the register records it with built=no.

## Out of scope (not built on)

- The redirect helper shallow-copies options, so deleting from `headers` can mutate a caller's
  object; a correctness issue, not this advisory.

## Upgrade 2026-10-20 (sibling-injection rules §2–§8)

- `instruction.md` rewritten to one general property over the protected outcome: a credential is
  bound to the origin it was supplied for and must reach no other origin at any hop, and a
  configured secret must not appear in clear in any diagnostic output. The old report named the
  self-hosted GitLab scenario, the update-info request, the object-storage redirect, the
  `DEBUG=electron-builder` switch, and the updater/build/publish tooling; those sentences are gone.
  The coupled contracts (same-origin redirects keep credentials, same-host http→https upgrade
  keeps them, cross-origin requests complete without them, ordinary headers travel, operations and
  diagnostics otherwise unchanged) are kept in general terms.
- Levers: the six existing families stay (T1 input-shape differential, T2 uncovered block-based
  ranges, T3/T4 far redaction sites, T5–T7 injected siblings). T1 is an M8 parser/shape
  differential (header names folded over case and `-`/`_`) and T2/T5 are M4 routes where the
  protection never existed, so the task already has HOW-type levers.
- Coverage gap closed: `DifferentialDownloader.readRemoteBytes`/`request()` — the trailing
  byte-range fetch that reads an embedded block map — is real upstream code the published fix
  never touches and had no security test. It is now covered by
  `security/differential.test.ts` ("a package whose block map is fetched from the end of the
  file…"), reached through `NsisUpdater.downloadUpdate()` with ordinary web-package update
  metadata; expected values come from the harness (`sha512`, block-map size), and no sockets or
  network are used. New trap T8.
- Also covered: the updater's full-download path through the Electron executor
  (`ElectronHttpExecutor.addRedirectHandlers` → the shared redirect decision). The shared helper
  looks only for the exact lower-case `authorization` key, so a capitalised or otherwise spelled
  header reached the redirect target at nop. The new test in `security/redirect.test.ts` drives
  `NsisUpdater` with differential download disabled and asserts on what the other origin received.
  This is the same T1 lever through a different caller, so its check is the existing
  `sf-core-redirect.patch` / `sf-lowercase-names.patch` (both now fail it as well); no separate
  check is needed.
- New check `checks/sf-embedded-blockmap.patch`: the oracle minus the `redirect: "manual"` default
  in `createRequestOptions` and the redirect listener in the trailing-range `request()` helper. It
  keeps both visible range paths fixed, so it fails exactly the new test; 17/18 security and
  165/165 functional in-container.
- `mkpatches.py` gained `f2_no_embedded` and the `sf-embedded-blockmap.patch` variant, and all
  patches were regenerated against the actual injected base (`work/repo`, giteaPublisher blob
  409ca40). Content is unchanged for every existing patch; only git index lines and hunk offsets
  were corrected (the old files had been generated from an older copy of the injected publisher).
- No repo code (`environment/injection.patch`) changed, so the prebuilt image is reused unchanged.
- Verified by targeted in-container runs on a real task image (four-package `tsc -p` rebuild each
  time): the pinned tree fails all 3 security/differential tests and all 6 security/redirect tests,
  including both new ones; the oracle passes both files 3/3 and 6/6 full (fix content otherwise
  unchanged); pass-alt and pass-hardening pass 18/18 security, and their 165/165 functional was
  unaffected because only security tests were added; sf-embedded-blockmap fails exactly the
  embedded test (17/18 security) and sf-lowercase-names fails it as expected.
