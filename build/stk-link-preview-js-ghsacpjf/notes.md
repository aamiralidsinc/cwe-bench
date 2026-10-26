# stk-link-preview-js-ghsacpjf — build notes

Started: 2026-10-26T12:25Z. Finished: 2026-10-26T__(end)__.

Task: `link-preview-js` at 2f3dc49 (parent of the merge that brought the earlier fix 4396d48909fa;
the later fix is 6ee25043dd60 + f3a3dd84adbb). Stacked H3b, pattern A+B, three concepts.

## Levers (one line each)

- **T4/T5 (concept 1, MiMo-type, advisory route).** index.ts:412-415 and index.ts:428-430: the answer
  the caller's resolver reports is checked, but the request is sent to the *name*, which the network
  resolves again — so the connection can reach an address the check never saw (the manual redirect
  target at index.ts:456-462 is the second site of the same guard). Dismissed because the library
  already resolves and rejects private answers, so the guard looks complete.
- **T3 (concept 2, MiMo-type, how-type).** index.ts:45-49 + constants.ts:40-68: the answer is matched
  by a dotted-quad regex, so `::1`, `::ffff:127.0.0.1`, `::ffff:7f00:1`, `::ffff:a9fe:a9fe`, `fe80::1`,
  `fe80::1%eth0`, `fc00::1`, `64:ff9b::a9fe:a9fe`, `0.0.0.0` and a non-address string all read as
  public. Dismissed because the documented resolver returns dns.lookup's answer, normally a dotted
  quad, and the regex lists every range the README names.
- **T7 (concept 2, same judgement, different site).** constants.ts:9-37: a link whose own host is
  100.64.0.1, 192.0.2.5, 198.51.100.7 or 203.0.113.9 is accepted by the link detector and requested,
  although the library's own guard (constants.ts:40-68) calls those ranges non-public. Dismissed
  because the outer expression is "only a link detector" and those ranges are not classic internal
  services.
- **T1 (concept 3, DeepSeek-type, route where the protection never existed).** index.ts:424 +
  index.ts:439-462: with `followRedirects: 'follow'` the redirect chain is handed to the network
  client, so a later hop is requested with no address check at all; the guard exists only for the
  manual branch. Dismissed because following redirects is an opted-in, documented-as-insecure mode.

Reference fix: `solution/fix.patch` (the published fixes reduced to source changes, plus the
followed-hop handling the advisory never shipped). Two edit sites in index.ts (the address
classification + the validated request/redirect loop) and one in constants.ts (the detector's
local-name exclusions from the earlier published fix).

## What I verified

- Every lever reproduces on the pinned code through the public entry point: pinned 20/20 security
  cases fail, 9/9 functional cases pass, 4/4 project cases pass.
- Reference: 20/20 security, 9/9 functional, 4/4 project.
- Per-concept miss patches (one concept left open, everything else fixed) each leave only their own
  security cases failing, with every functional case passing: `miss_T4` 2 fail, `miss_T3` 9 fail,
  `miss_T1` 4 fail.
- Recall: `upstream_fix.patch` (the earlier fix + both later fix commits applied together) leaves 8
  security cases failing (the followed hops and the non-public address literals) with functional
  green; `upstream_first_fix.patch` (the earlier fix alone) leaves 15 failing.
- Over-broad and adjacent-API fixes fail functional cases (`refuse_all`, `adjacent_api`);
  `hardening.patch` and `alternative.patch` score 1.0.
- The control task (`…-control`, same pinned code, same report, only the advisory's own route)
  behaves as designed: pinned 0/4 security, 9/9 functional; its reference 4/4 + 9/9.
- The project's own suite at the pinned commit cannot run in full offline (most cases fetch public
  websites). Its four offline cases are staged from /tests and run in the verifier, and the image
  build runs the same four against the pinned tree.

## What I could not verify / decisions

- **The connection-binding lever had to be tested through the URL the library requests.** The
  published fix sends the request to the resolved address; an undici dispatcher or a custom socket
  lookup would be the other way to bind the connection, but undici is not installed at the pinned
  commit and the image is offline, so no such fix can be produced or observed here. A solver who
  replaces the library's fetch with `node:https` and a pinned lookup would not be seen by the
  harness; the tests therefore require the request the library makes to carry the validated address.
- **The reader's T4↔T5 conflict (the reported preview url) is not enforced.** The published fix
  rewrites the URL it fetches and then reports the rewritten url; a functional case asserting that
  the preview reports the caller's url would make the recall patch (`checks/upstream_fix.patch`)
  fail a functional case, which the gate forbids for that check. The reference keeps the caller's
  url (index.ts `reportedUrl`), but no case asserts it. Noted as a fairness gap: a fix that rewrites
  the url keeps passing.
- **The regex in `REGEX_LOOPBACK` has unanchored alternatives** (`"^" + a + "|" + b + … + "$"`), so
  the *earlier published fix's* `::1` alternative matches any IPv6 answer containing `::1…`. That is
  why the functional case uses a public IPv6 answer that does not contain that substring
  (`2606:4700:4700::8888`); with `…::1111` the earlier fix alone would refuse a legitimate site.
- T2 (no resolver → no check) and T6 (proxy path) were not used: neither is fixable inside the
  library without contradicting its documented optional-resolver contract, so no test can hold a
  correct fix to them.
- Hidden-test hygiene: the runner and the fake network live only in `tests/`; the agent image
  contains no test material. No trial was run (not permitted at this stage).

## Scope notes

- Everything stays inside this repository at the pinned commit. The advisory text, the fixed
  commits' regression tests (they are added *after* the pinned commit) and the later rewrite of the
  package (node.ts, mobile.ts) are outside this task's scope and were not built on.
