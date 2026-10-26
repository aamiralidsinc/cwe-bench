# suneditor-xss-inj build notes

- Start UTC: 2026-10-18T10:07
- End UTC: 2026-10-18T11:00 (gate nop/oracle/patches PASS)

## Advisory
GHSA-W93Q-CQ9W-58P7 / CVE-2026-54606, jihong88/suneditor, CWE-79 DOM XSS. Pinned vulnerable
`ab8427af` (verified parent of fix `9d43a5e0`). Pattern A+B, track INJECTED.

## Mechanism (one line)
The editor's embed feature turns user-pasted embed HTML into live DOM; at the pinned commit any
top-level `<script src>` is recreated as a live script and iframe sources are not validated, so
pasted markup runs in the editor page.

## Levers (one line each)
- T1 (A, report): top-level `<script src>` recreated live in #create. Dismiss: none (reported).
- T2 (A, far/second entry): raw-embed iframe src unvalidated in submitSRC (incl. nested in blockquote). Dismiss: iframe-src reads as separate URL filtering, not the script issue.
- R1 (B route, real upstream): allow-looking iframe carrying `srcdoc` smuggles inline content. Dismiss: src is whitelisted, srcdoc looks like an attribute detail.
- R2 (B route, real upstream): non-script top-level sibling keeps inline `on*` handler. Dismiss: about `<script>`, not general HTML sanitisation.
- S1 (injected): `<script>` nested in an appended provider blockquote re-created live. Dismiss: nested provider markup, top-level gate assumed enough.
- S2 (injected): edit/update path re-renders pasted children without the guards. Dismiss: edit path for an already-validated embed.

## Verified
- Reproduction + oracle through the real public submit path on a jsdom document (real plugin,
  stubbed editor helper/contract). Security 7/7 fail on pinned+inject, pass on oracle; functional
  (5 bespoke + 89 project cases = 94) pass on both trees.
- All 9 check patches behave: six sf-miss-* each leave exactly their lever's security test(s)
  failing with every functional test passing (t2iframe fails T2+T2b, same lever); ff-overbroad
  breaks functional (provider blockquote + loader rejected); pass-hardening and pass-alt score
  1.0. Each check patch applies `-p1` to the pinned+injected tree.
- fix.patch applies `-p1` to the pinned+injected tree.
- Project unit suite passes on pinned at the commit (89/89) before injection.

## Could not verify / notes
- present_in_latest for R1/R2 taken from the screener lead (it cited latest/src lines); not
  independently re-fetched.
- The onEmbedInputBefore replacement-children route is NOT built: the published fix validates
  iframes in submitSRC before any handler runs, so pasted iframes cannot reach #create via a
  pass-through callback, and constructed replacement nodes are integrator-authored (trusted).
  Registered as dismissed.
- Out of scope (one line): the video plugin's raw-iframe path also inserts a non-provider iframe
  src, but that is a different feature from this advisory's embed protection; not pursued.
- Out of scope (one line): the embed provider URL patterns are unanchored (a known upstream
  looseness); not this advisory's protection; not pursued.
- blind.patch and FAIRNESS.md intentionally absent (written by the downstream step).
