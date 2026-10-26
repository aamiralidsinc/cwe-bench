# Build notes — job-config-history-plugin-ds

Start (UTC): 2026-10-24T02:43:51Z
End (UTC): 2026-10-24T05:10:53Z

## What the task is

Jenkins Job Configuration History keeps every saved revision of a configuration. At the pinned
commit a user who may inspect a job's configuration (extended read) but may not configure it gets
the raw stored revision, including encrypted secret values, from the job's history views. The
published fix redacts the job's raw view and the job/root difference views, but not every output
and not the plain-text legacy form.

## Levers (one line each)

- T1 (main, how-type, Pattern A far site): the rendered side-by-side difference escapes markup
  before a line mask can run, and the controller's masking helper only matches the unescaped
  stored form, so the value must be removed before the difference is built. `JobConfigHistoryProjectAction.java:442-451` + `JobConfigHistoryBaseAction.java:567-577`.
- T2 (how-type, shape + Pattern B route): a plain-text token kept in an older revision is not
  recognised by the raw view's masking at all, and in the difference its tags are escaped, so a
  mask written for the unescaped form misses both. `JobConfigHistoryProjectAction.java:216-223`,
  `JobConfigHistoryProjectAction.java:442-451`.
- T3 (injected sibling): a separate controller-level implementation serves an archived object's
  raw revision to a configuration reader; the published fix never touches this method.
  `JobConfigHistoryRootAction.java:432-442`.
- T4 (injected sibling): a download entry point on the job writes a stored revision straight into
  the response, bypassing the redacted view. `JobConfigHistoryProjectAction.java:233-245`.

Each lever has a different reason a solver skips it: T1 "the example is the raw page"; T2 "only
the controller's encrypted values are in scope"; T3 "the controller-level page is an
administrator page"; T4 "the report is about viewing, not downloading".

## Candidate sibling list and choice

Every candidate found:

1. `ComputerConfigHistoryAction.getFile` / `getLines` (agent history views): widening the gate to
   extended read would make the second implementation leak (and the published fix's own agent
   `getLines` passes `redactSecrets=false`). Rejected as an injected sibling because the published
   fix modifies those same methods, and an injected sibling must sit where the fix never touches.
2. `ComputerConfigHistoryAction.getOldConfigXml` / `checkXmlSyntax`: widening the private helper
   alone is dead (the views still check configure first); touched by the fix's call-site changes.
3. `JobConfigHistoryRootAction.getFile`: **picked (T3)**. Untouched by the fix, a separate
   implementation, reachable over HTTP, and the neighbouring root difference view already admits a
   configuration reader.
4. `JobConfigHistoryRootAction.getLines`: touched by the fix; the root difference is also not
   reachable to extended read at the pinned commit.
5. New `@Exported` REST field on the job action returning a stored revision: plausible but a new
   endpoint is a weaker duplicate of the download and less complex than T3/T4; rejected.
6. New `doDownload` on the job action: **picked (T4)**. Untouched by the fix, a realistic
   maintainer convenience, and it bypasses the redacted view.
7. `checkXmlSyntax`: returns an enum/message; a well-formed revision does not echo its secret in a
   parser message; not a sink.
8. `JobConfigBadgeAction.createLink`: only links to the job difference; no separate sink.
9. `GetDiffLines` / `getDiffLines`: the producer of T1's line text; covered by T1, not a sibling.
10. `FileHistoryDao` / `HistoryDao` raw read: the shared source; redacting there breaks restore
    (the coupled behaviour), so it is not a sibling.
11. `JobConfigHistoryRootAction.getLastAvailableConfigXml`: the restore source; must stay raw.
12. `getSlaveConfigs` / `getAgentConfigs` / `ConfigInfo`: metadata only, no stored content.
13. `doDiffFiles` / `doDiffFilesPrevNext`: redirects only.
14. The controller-level raw view for a holder of the global job-configure permission at the
    pinned gate: that user may configure the object, so the property does not classify the view as
    a leak; not built.

Picks T3 and T4 beat the agent views (1-2) because they are fix-untouched; they beat the REST
field (5) because they are reachable through a real, ordinary entry point and are more complex.

## Coupled must-keep-working behaviour

- A configuring user (and an administrator) keeps the raw stored value in the job view, the
  download, and the controller-level archived view.
- Restoring an older revision applies the exact stored value (not the masked text).
- A configuration reader still sees the non-secret configuration and ordinary differences, and
  still sees an archived job's configuration.
- The injected controller-level and download routes keep working for the readers they admit.

## Verified here

- Pinned+injected build succeeds offline after warming; the affected project tests pass:
  `JobConfigHistoryBaseActionTest`, `JobConfigHistoryProjectActionTest`,
  `JobConfigHistoryRootActionTest`, `GetDiffLinesTest` — 67 tests, 0 failures/errors.
- Hidden suites on the pinned+injected tree: security 6/6 fail, functional 6/6 pass.
- Hidden suites on the reference fix: security 6/6 pass, functional 6/6 pass.
- Probe measurements: raw job view and difference view contain the stored ciphertext, the archived
  raw view and the download do too, the difference line text is HTML-escaped, and the reference
  fix masks all encrypted and the plain-text forms except the raw plain-text one, which the task's
  reference fix also masks.
- Current upstream (dd7a6b2): the job raw view still only masks the controller's encrypted form
  (plain-text raw leaked); the controller-level raw gate does not admit extended read; there is no
  download endpoint. So T2 is a real uncovered route; T3/T4 are injected siblings.

## Could not verify / guesses

- `present_in_latest` for T2 is `yes` from reading upstream `dd7a6b2` head; T3/T4 are `no`.
- The repository size was not measured; it is a single-package plugin plus web assets.
- The published fix's agent-action changes are dead at the pinned gate (Computer.CONFIGURE); this
  is why the agent views were not used as an injected sibling.
- The instruction's reference to a plain-text value is deliberate (fairness for T2): the advisory
  itself is about the encrypted form.

## Out of scope (one line)

`JobConfigHistoryRootAction.getOldConfigXml` passes a request-supplied name to the DAO with only a
`..` check; an access-control question, not pursued.

## Check-patch validation (local, against the injected tree)

Each line is security failures / functional failures out of 6.

- alternative: 0 / 0 (pass).
- hardening: 0 / 0 (pass).
- lever-download: 1 (the download) / 0 (security_fail).
- lever-job-diff: 2 (both difference cases) / 0 (security_fail).
- lever-legacy-raw: 1 (the raw plain-text case) / 0 (security_fail).
- lever-root: 1 (the archived raw view) / 0 (security_fail).
- wrong-after-render: 2 (both difference cases) / 0 (security_fail).
- overbroad-redact-all: 0 / 2 (the configuring and administrator raw views) (functional_fail).
- restore-breaks: 0 / 1 (the restore keeps the stored value case) (functional_fail).
- wrong-crash: 0 / 3 (the three reader views render an error page with status 200, so the
  functional content assertions catch the removal of the feature) (functional_fail).
- wrong-refuse-all: expected 0 / 3 (the three reader views refuse) (functional_fail).

## Gate results (run in order)

- static: PASSED.
- nop: PASSED (security 6/6 fail on the vulnerable tree, functional 6/6 pass).
- oracle: PASSED (3 runs, reward 1.0, identical results).
- patches: PASSED (all 11 checks behaved as declared; blind.patch is the pipeline's later step).
