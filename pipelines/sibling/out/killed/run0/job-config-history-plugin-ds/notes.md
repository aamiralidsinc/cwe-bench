# job-config-history-plugin-ds — build notes

Start (UTC): 2026-10-24T02:35:24Z
End (UTC): (filled in when done)

Advisory: GHSA-8QR4-27MH-HQFR / CVE-2026-57287 (jenkinsci/job-config-history-plugin,
CWE-312). Pinned `ba0105cedfa57aae6eab16a23c112b5b1cda2889`; published fix
`c8fab15101dce336a8f17f10edd10c7221b860c0` (`SECURITY-3742`), one commit.
Track: injected. Pattern: A (+ injected far sites). Source label: mined+injected.

## What the product does
The plugin records every saved revision of a job's `config.xml` (and agent/node
configs) under `$JENKINS_HOME/config-history/`, and offers job-level and global
views of those revisions. A user holding `Item/EXTENDED_READ` but not
`Item/CONFIGURE` is allowed to read a job's history; the advisory is that the old
revision XML (which contains stored credentials) was returned to that user with
no output redaction. The published fix redacts with
`jenkins.security.ExtendedReadRedaction.applyAll` in the job file/diff views,
adds a cleartext-`<authToken>` mask for the job diff, and passes a redaction flag
through the root and agent view paths.

## The security property (stated once, in instruction.md)
No user who may not configure the object that owns a stored configuration may
receive a stored credential value from any response that serves historical
configuration content; every stored credential (encrypted when saved, or kept as
a legacy plain-text token) is masked before the content leaves the server.
Whoever may configure the object still gets the complete unmodified revision,
and existing operations on the stored content keep working. Read literally it
covers the raw revision views, the comparison view, the global deleted-job view
and the download endpoint, with both credential shapes.

## Levers

L1 (main, HOW) — the comparison view (`JobConfigHistoryProjectAction.getLines`,
base diff builder in `JobConfigHistoryBaseAction`). The report's trigger is a
single revision; the diff is a separate producer (XSLT sort -> unified diff ->
`GetDiffLines` row builder) whose line text is what reaches the response. A fix
that wraps only the revision view, or that applies the core redaction only to
`{AQAAAB...}` blobs without handling the legacy plain token, leaves the old and
new credential values visible in both columns. The correct fix must mask before
or after the diff but for both credential shapes. Reason to dismiss: "the
comparison only shows lines that changed / it is a rendered page, the revision
fix covers it".
L2 (coupled must-keep-working, HOW) — the shared revision accessor feeds
`doRestore`, which writes the revision back into the live job. The tempting DRY
fix (redact inside `getOldConfigXml`/`HistoryDao.getOldRevision`) corrupts every
restore while every read test passes. Functional restore tests catch it. Reason
to dismiss: it is the single obvious choke point.
L3 (injected sibling, far site) — `JobConfigHistoryRootAction.getFile` for a
deleted job: a second implementation in another file, with a different
permission object (global vs item), untouched by the published fix. Injection
widens its gate to `hasReadExtensionPermission()`, mirroring the neighbouring
`getOldConfigXml`/`getJobConfigs` gates. Reason to dismiss: "the global history
page is admin-only; a deleted job is no longer a job page".
L4 (injected sibling, new transport) — `JobConfigHistoryProjectAction.doDownload`:
a revision download endpoint gated like the views but returning the raw XML.
Reason to dismiss: "it is an export/API feature, not the history view".

L1 and L2 are how-type; L3/L4 are where-type extras. L1 and L3/L4 have different
reasons to dismiss; L2's is the coupled-write reason.

## Candidate list (every possible sibling site/route scanned)
Chosen:
- A1 `ProjectAction.getFile` (raw revision; landing, published fix) -> tested.
- A2 `ProjectAction.getLines` (comparison; published fix far site) -> tested (L1).
- A3 `RootAction.getFile` deleted-job raw (upstream-untouched; gate widened by
  injection) -> tested (L3).
- A4 `ProjectAction.doDownload` (injected transport) -> tested (L4).
- A5 `ProjectAction.doRestore` coupling -> functional tests only (L2).

Rejected, with reason:
- B1 `BaseAction.getStringFromXmlFile` / `getLines(XmlFile,XmlFile,boolean)`
  published-fix lower-level API: not an HTTP entry point; a test would have to
  call it directly against the spec's "real entry point" rule.
- B2 `RootAction.getLines` deleted-job diff (published fix): verified dead for
  under-privileged users — the gate requires global `Item/CONFIGURE` or
  `Overall/CONFIGURE`, so nobody who lacks configure authority reaches it.
- B3 `ComputerConfigHistoryAction.getFile/getLines` (published fix): dead —
  `checkConfigurePermission()` (Computer.CONFIGURE) runs before the new
  redaction branch; also the published fix edits exactly those method bodies, so
  an injected gate change would sit in the fix's own hunk.
- B4 `RootAction.getFile` system-config raw (O8b lead 2): no core global
  configuration with a decryptable `Secret` exists in a stock Jenkins to make a
  realistic test; would have been the same method as A3.
- B5 `XmlSyntaxChecker.check` SAX messages returned to extended-read users via
  `checkXmlSyntax`: returns parser diagnostics, not stored values; not a leak of
  the protected data.
- B6 `RootAction.getOldConfigXml(String,String)`: public but takes parameters;
  Stapler does not bind it as an HTTP getter.
- B7 `JobConfigBadgeAction.createLink`: link only, no content.
- B8 `RootAction.getJobConfigs`/`getSingleConfigs`, `ProjectAction.getJobConfigs`:
  metadata only.

Why the picks beat the rejects: A3 is the only far site that is both real
product code and reachable by an under-privileged user after a one-line,
maintainer-plausible gate change (B2/B3 are dead; B4 has no realistic secret).
A4 is a second transport that a view-by-view fix misses (B1 is not a route).
A2+A5 give the task its how-type difficulty (producer/ordering and the coupled
write path), which no where-type site provides.

## Injection
`environment/injection.patch` (two hunks, our copy only):
1. `JobConfigHistoryRootAction.getFile`: deleted-job branch admits
   `hasReadExtensionPermission()` in addition to `hasJobConfigurePermission()`.
2. `JobConfigHistoryProjectAction.doDownload`: new GET endpoint serving a
   revision's XML, gated like the other views.

## Verified
- The flaw reproduces at the pinned commit through the real HTTP entry points
  (JenkinsRule + WebClient): an EXTENDED_READ-only user receives the raw
  revision (plain and xml) and the comparison page containing the encrypted
  password-parameter default; the same user is refused by the global deleted-job
  view before the injection.
- The injected tree makes the deleted-job raw view and the download endpoint
  leak to the same user.
- The published fix is dead in `RootAction.getLines` and
  `ComputerConfigHistoryAction` for under-privileged users (gates above).
- `Secret.ENCRYPTED_VALUE_PATTERN` masking is `>{AQAAAB...}<` only (core
  `ExtendedReadSecretRedaction`); a plaintext `<authToken>` is untouched by it,
  which is why the legacy-token shape is a real lever.
- Project tests for the affected area pass at the pinned commit
  (`JobConfigHistoryRootActionTest` 27/27; see build log).
- Offline Maven build and an out-of-surefire JUnit4 JenkinsRule run against the
  warmed repository work (JVM `--add-opens` list + early BouncyCastle provider
  registration for `instance-identity`).

## Could not verify / guesses
- Upstream `redactAuthTokensInLines` uses an HTML-escaped regex
  (`&lt;authToken&gt;`) while `DiffRowGenerator` does not escape line text; the
  upstream test that exercises it is a `*IT` excluded by the build. Our oracle
  masks the literal element instead; tests assert only that the value is absent.
- Whether the cleartext token should also be masked in the raw view upstream is
  unknown (the published fix masks it only in the diff); our property requires
  it everywhere, which is the advisory's CWE-312 wording.
- `present_in_latest` for the injected routes is n/a (they exist only in this
  copy).

## Scope notes
- Out of scope, noticed only: `RootAction.getOldConfigXml` passes a request
  `name` to the DAO with only a `..` check (path question); `XmlSyntaxChecker`
  echoes parser messages. Neither is built on.
