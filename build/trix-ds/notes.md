# trix-ds build notes

Start (UTC): 2026-10-24T05:03:20Z
End (UTC): 2026-10-24T08:30:27Z

## Gate progress
- static: PASSED (2026-10-24T05:21Z).
- nop: PASSED (2026-10-24T05:44Z) — 13 security tests failing, 226 functional passing.
- oracle: PASSED (2026-10-24T07:54Z) — three runs, reward 1.0, 13/13 security and 226/226
  functional in each. Earlier invocations only failed on shared-host infrastructure (a `/tmp` tmpfs
  exhaustion during an image build, then the Docker daemon deadlock that was fixed at ~07:40Z);
  the task files were not modified for those.
- patches: PASSED (2026-10-24T08:30Z) — sf-miss-t1 10 security fails/0 functional, sf-miss-t2 2/0,
  sf-miss-t1-shape 1/0, sf-miss-s1 3/0, sf-miss-s2 3/0, ff-overbroad 13 functional fails,
  pass-hardening and pass-alt reward 1.0. The missing blind.patch (written downstream) and
  FAIRNESS.md are the only expected outstanding items.

## Task
basecamp/trix at e62fcc3b (vulnerable) — CWE-79 stored/DOM XSS through a link destination
carried in a stored document. Pattern A+B, injected track. The published fix validates `href`
in `StringPiece.fromJSON` (source + the prebuilt gem asset).

## Levers (one line each)
- T1 (A, main, how-type): stored-document deserialisation is the shared funnel for host loads and
  drag-drop; the pasted-markup path already sanitises anchors, so the stored format looks
  internal/trusted. `src/trix/models/string_piece.js:6-8`, rendered at
  `src/trix/views/piece_view.js:113-124`. Reason to dismiss: "the markup parser is where XSS
  from links is handled".
- T2 (A, extra, second packaging): `action_text-trix/app/assets/javascripts/trix.js` is the
  prebuilt asset server-side applications load; fixing the source changes nothing there. Reason
  to dismiss: "generated artifact; source is the truth".
- T3 (A, shape): a destination supplied as a non-string JSON value (array) is coerced by
  `setAttribute`; a string-typed check sees nothing. Same site as T1. Reason to dismiss:
  "document attribute values are strings".
- S1 (injected, how-type): a second configured text attribute (mention) binds its value to the
  anchor destination through `config.groupAttribute` in `piece_view.js`, with grouping support in
  `piece.js`. Reason to dismiss: "a different feature; its values are profile addresses".
- S2 (injected, how-type, wrong object): an attachment piece `link` is rendered around the
  attachment by `attachment_view.js:31`; the existing DOMPurify check at `:128-135` validates the
  attachment's own `href`, a different object. Reason to dismiss: "the attachment view already
  checks destinations".

Coupled must-keep-working values: safe web/mail/relative destinations with their text; other text
and block formatting next to a refused destination; attachment captions, attachment content and the
attachment's own download destination.

## Protocol / input coverage in the hidden suites
Security: 13 cases (stored-document 8, prebuilt asset 2, pasted markup 3). Functional: 13 task
cases + 213 project unit tests (220 QUnit tests, 7 skipped as jsdom cannot do bidi/layout).

## What was verified (locally, under jsdom; then in the gate)
- The flaw reproduces at the pinned commit through `Document.fromJSONString` /
  `deserializeFromContentType` and `DocumentView.render` (renders `<a href="javascript:...">`).
- The published fix closes T1/T3 and, applied to the prebuilt asset, T2.
- The published fix does NOT close S1 or S2 (or the non-string shape for a string-only check).
- Each check patch produces the declared outcome in the local runner:
  - sf-miss-t1: 10 security failures, 0 functional (filters markup only; stored route and asset open).
  - sf-miss-t2: 2 security failures, 0 functional.
  - sf-miss-t1-shape: 1 security failure (non-string), 0 functional.
  - sf-miss-s1: 3 security failures, 0 functional.
  - sf-miss-s2: 3 security failures, 0 functional.
  - ff-overbroad: 13 functional failures.
  - pass-hardening, pass-alt: 0 failures.
- Project unit suite green on the pinned+injected tree and on the oracle tree (213 reported tests).

## What could not be verified / guesses
- The advisory text was not available; the screener's record and the fix diff were the source. The
  published fix is JSON drag-drop deserialisation; the HTML-paste framing in the advisory summary
  is the report's red herring (the markup path is sanitised by HTMLSanitizer).
- `present_in_latest` for the injected siblings is not applicable (our copy only).
- Whether a real browser would still execute some exotic destination spelling was not explored;
  the suites use the three shapes named by the screener plus a non-string shape, and the fix is
  DOMPurify's own attribute decision.
- The prebuilt asset is not regenerated at image build (deliberately: it is the published pre-fix
  asset). A solver who runs the project's JS build regenerates it from the fixed source; a solver
  who does not must edit it. This is the published fix's own second site.
- The project's browser suite was replaced by a jsdom run of its unit files (Playwright is not
  installed); seven tests that need real layout/bidi are excluded, documented above.

## Sibling candidates considered (all found in the code)
1. Mention / second configured `groupTagName` text attribute (chosen, S1): a value bound to an
   element attribute at render; config-driven, plausible feature, different reason to skip.
2. Attachment piece link (chosen, S2): a separate model type and view; the existing check examines
   the attachment's own href, a different object.
3. Block-level `htmlAttributes` (e.g. a block whose container is an anchor): the allowlist is by
   name, not value. Rejected: a block tagName of `a` enters `getBlockTagNames()` and changes HTML
   parsing of every anchor (breaks the project suite); any non-anchor tag has no script sink.
4. Attachment own `href` (upstream): already guarded by DOMPurify in `AttachmentView.getHref` — no
   lever.
5. Previewable attachment `url` -> `img src`: `javascript:` in `img src` does not execute; out of
   scope (noted by the screener).
6. Block htmlAttribute `cite`/`language`: not a script sink.
7. `Editor.activateAttribute` / `Composition.setTextAttribute` direct string piece: developer API,
   caller trusted; no untrusted document data, and the published fix leaves it. Dismissed as a
   lever (a solver could not be expected to call a developer API attacker input).
8. Level 2 `beforeinput` insertLink (`event.data`): browser-originated, self-XSS; dismissed.
9. Paste `URL` data -> `createLinkHTML` -> HTMLParser: sanitised by HTMLSanitizer; not open.
10. `data-trix-serialized-attributes` text/html serializer: different advisory (earlier H1 fix);
    out of scope.
11. Attachment content HTML: goes through HTMLSanitizer; not open.

Picks: 1 and 2 beat the others on mechanism (a different model/view path each), plausibility and a
distinct reason to dismiss; none of the rejected candidates reaches a script sink through untrusted
document data at the pinned commit.

## Pattern B register rows
Added to `build/audit/uncovered-routes.tsv`:
- trix-ds / basecamp/trix / GHSA-53G2-MVCC-Q9X3 / S1 / no / no / no / yes (B) / built / injected sibling, our copy only / pending client decision
- trix-ds / basecamp/trix / GHSA-53G2-MVCC-Q9X3 / S2 / no / no / no / yes (B) / built / injected sibling, our copy only / pending client decision

## Fairness self-check
- The instruction states one property over the rendered outcome and the value, lists no route and
  no sibling; the coupled preservation clauses are property-level.
- T2 is the published fix's own site; updating a checked-in generated asset after a source fix is
  standard practice and the project's build scripts do it.
- S1/S2 are visible in `src/`; a solver who greps for what can become a link destination finds
  both. The instruction deliberately says "wherever in the document the value sits".
