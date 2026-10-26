# stk-silverpeas-core-27788 — build notes

Start (UTC): 2026-10-26T02:04:26Z
End (UTC): 2026-10-26T04:55Z

## Advisory and pin

- Advisory: GHSA-QV8H-RQR3-MPH9 / CVE-2026-53698 (path traversal / arbitrary file read, CWE-36).
- Pinned: `b1d65df25a0b8f0e3fde7fa5b57452eadffc644c` (parent of the published fix).
- Published fix: `caa6e6d1ac967ebd29b39e11c2ef5e7fd0047eec` (touches only `FileServer.java` and
  `FileServerUtils.java`).

## Levers (one line each)

- T1 (A, advisory route, deepseek): a download request with no space identifier is treated as the
  supported "personal space" and served from the uploads root's `null` directory
  (`FileServer.java:80,148-164`); dismissed because the branch is commented as a feature and the
  framework's own controller also authorises a null component id.
- T2 (A, advisory route, deepseek): an absolute location in the request plus the absolute-location
  marker makes the descriptor skip the component repository and open the location directly
  (`FileServer.java:112-131`, `SilverpeasFileProvider.java:202-216`); dismissed because a caller
  with an entitled space is already authorised and the marker looks like an internal URL-builder
  flag.
- T3 (B, uncovered upstream, deepseek): the sibling file-serving entry point resolves and sends a
  file for any caller with no session, no entitlement check and no space identifier
  (`OnlineFileServer.java:58-99`); dismissed as the legacy inline-media servlet, which the
  advisory and its fix never mention.
- T5 (coupled value, mimo): a storage space that shares its files with signed-in non-members
  (`FileServer.java:154-157`); the natural over-broad "members only" repair silently removes it.

## Concepts

- C1 = [T1, T5] — one access-control edit site (the component gate and the entitlement rule).
- C2 = [T2] — the absolute-location switch and its constant.
- C3 = [T3] — the sibling servlet's session, entitlement and identifier checks.

## What was verified

- The pinned tree is the only parent of the published fix commit (`git rev-list --count` = 1).
- The published fix leaves `OnlineFileServer` untouched; current upstream `master` still has the
  unprotected sibling, so the `present_in_latest` register value is `yes`.
- The relative-path `..` shapes are already stopped in production by the shared
  `RelativePathCheckingProcessor` (`FileUtil.assertPathNotRelative` rejects `../` and `/..` on the
  final path); only the absolute-location shape is exploitable. This is why T2 is the absolute
  switch alone and not a fold of the relative shapes.
- The harness registers that same processor (and the existence checker) so the pinned behaviour
  matches production; without it a mock test would report a relative traversal that production
  does not have.

## Levers considered and dropped

- T4 (`TempFileServer` traversal): the reader's record calls the two-substring `isValid` weak, but
  the path is finally checked by `RelativePathCheckingProcessor`; with the production processors
  registered the `..` shape returns `NO_FILE`, so the route is not exploitable at the pinned
  commit. Dropped rather than shipped as an unfair lever.
- T6 (`ImageUrlToDataSourceScanner`): it calls the same `getSilverpeasFile` helper as T2, so one
  containment fix closes both — it is not an independent concept; dropped to keep concepts
  independent and the report free of a mail-generation surface.

## What could not be verified

- The reader record path given to the build (`pipelines/stacking/out/reader/h4-27788.json`) does not
  exist in this checkout; the record actually used is
  `pipelines/stacking/out/reader-ds/h4-27788.json`. The manifest keeps the path the build prompt
  asked for.
- The document/attachment branches of `OnlineFileServer` were not driven: they need the attachment
  service and database rows. The reference adds the entitlement check on the document's instance id
  for them too, but the hidden tests exercise the fallback branch only.
- The project's full unit suite has three pre-existing `ComponentLocalizationTest` errors
  (`MissingResource`) in this container; only the affected-area `FileServerUtilsTest` is used as the
  project-test proof.
- No target-model trial was run in this build.

## Local in-process proof (warmed image, before the container gate)

- Pinned: 7/7 security tests fail with the marker in the response body (the file is served);
  7/7 functional tests pass.
- Reference: 7/7 security and 7/7 functional pass.
- miss_T1 leaves `requestWithoutSpaceIdentifierIsRefused` failing; miss_T2 leaves
  `absoluteSourceIsNotServed` failing; miss_T3 leaves all three sibling tests failing. Every
  miss patch keeps all functional tests passing.
- alternative and hardening: 7/7 + 7/7.
- crash, one-direction and wrong-resource: security fails, functional passes.
- refuse-all and over-hardening: functional fails (over-hardening fails only the storage-sharing
  value).
- upstream_fix alone: T1/T2 pass, all three T3 tests fail (the recall check).
- Control: pinned 4/4 security fail and 7/7 functional pass; the published fix 4/4 + 7/7.

The harness drives the real servlet entry points in-process with ordinary servlet requests and a
recording response. It registers the product's own `RelativePathCheckingProcessor` and
`FileExistenceCheckingProcessor` (the startup `Initialization` services) so behaviour matches
production, and supplies the product's authorization beans (`OrganizationController`,
`ComponentAccessControl`, `UserProvider`) through the `TestBeanContainer` the kernel uses in unit
tests.

## Container gate attempts

- 2026-10-26T03:03Z: `nop` attempt 1 failed as infrastructure: `OSError [Errno 28] No space left on
  device` in Harbor's temp directory (the shared VM's `/tmp` inode table was full from concurrent
  sessions). Retried.
- The shared VM was heavily oversubscribed by other sessions' builds and trials (load average above
  80-100 on 8 CPUs), so the image build and the gate stages were slow. Stage results are recorded
  below when they finish.
- `static` PASS (stacked and control). `nop` PASS (7/7 security fail on the pinned code, 7/7
  functional pass; verifier build 1:44). `oracle` PASS 3/3 (7/7 + 7/7, reward 1.0 each).
- The `patches` stage's Harbor trials never left their setup phase under the saturated shared
  daemon (more than 140 running containers from other sessions; a trivial `docker run` took over
  120s). Every check was therefore run through the *identical* official verifier image
  (`...__gkfwcnf__verifier__trial-main`, same `/tests`, same three-module BUILD) against the
  matching agent workspace:
  - miss_T1: security fail (undefined-space gate), functional pass.
  - miss_T2: security fail (absolute location), functional pass.
  - miss_T3: three security fails (sibling servlet), functional pass.
  - overhardening: functional fail (storage sharing), security pass.
  - refuse_all: functional fail.
  - crash_as_refusal: five security fails, functional pass.
  - wrong_resource: one security fail, functional pass.
  - one_role_or_direction: one security fail (the POST path), functional pass.
  - alternative: reward 1.0.
  - hardening: reward 1.0 (the first version of this check patch used `File` in
    `OnlineFileServer` without importing it and did not compile; found by the official verifier,
    fixed, re-run to 1.0).
  - upstream_fix: three sibling security tests still fail, functional pass (the recall check).
- The verifier build was narrowed to the three modules a plausible fix can live in
  (`core-library`, `core-web`, `core-war`) without `-am`; the other modules resolve from the warmed
  local repository. Measured at 57 s from scratch in the warmed image instead of several minutes
  for the whole reactor. This keeps every plausible fix layer compiled (the servlets, the shared
  sender, and the file provider/descriptor library) while keeping the offline verifier fast.

## Reference and recall

- `solution/fix.patch` = the published `FileServer`/`FileServerUtils` changes plus the sibling
  servlet's session, entitlement and identifier checks.
- `checks/upstream_fix.patch` is the complete published fix alone. It must fail: it still leaves
  T3's security tests failing.
- The control (`stk-silverpeas-core-27788-control`) uses the same report, the published fix as its
  reference, and only T1/T2 in its security tests.
