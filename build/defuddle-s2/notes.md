# defuddle-s2 — build notes

- Start (UTC): 2026-10-26T12:32:00Z
- End (UTC): 2026-10-26T13:05:00Z (gate stages started after this)
- Candidate: screener entry 12193, kepano/defuddle, pinned 19520add09282abdfadbc6d23eb6bf8393af2bf8, published fix baf2eaef61d334ef595b28c89e5c5e89e52daf7f.
- Advisory family: GHSA-JG4P-G6XJ-4QMF / CVE-2026-61824 (CWE-79 / CWE-116).
- Pattern A+B, injected track, strict gate.

## Security property (written once, before routes)

No value the library obtains while processing a page may become executable markup in the content it
returns. For every response, whatever path its content took to reach it, the returned content must
not contain an event-handler attribute, `srcdoc`, a script-capable element, or a script-capable URI
in a link/resource address. The instruction states this invariant, the preservation clauses and the
"examples are examples" clause, and no route.

## Levers

1. **L1 — reported base site.** X article header image alt/src interpolated into generated
   attributes. where src/extractors/x-article.ts:114. dismiss: escape the one reported value.
2. **L2 — published far site.** Substack note image address from og:image/srcset into `src`.
   where src/extractors/substack.ts:181,186. dismiss: it is a resolved image URL from metadata.
3. **L3 — published far site.** YouTube description text placed in a paragraph as markup.
   where src/extractors/youtube.ts:368-369. dismiss: plain metadata text, already wrapped in `<p>`.
4. **L4 — main how-type lever, pattern B (protection never existed).** Structured-data text is
   assigned to response content verbatim when no matching element exists. where
   src/defuddle.ts:181-184. dismiss: the block above sanitizes a clone, and the project test calls
   the value plain text.
5. **L5 — pattern B, real upstream.** Hacker News post-page story link href/text unescaped.
   where src/extractors/hackernews.ts:210. dismiss: the same extractor escapes every other field.
6. **L6 — pattern B, real upstream.** BBCode link/image converter emits page text as markup.
   where src/utils/bbcode.ts:25,29. dismiss: it already rejects dangerous URI schemes.
7. **L7 — injected sibling.** oEmbed article POLL block renders fetched question/option labels
   unescaped. where src/extractors/x-oembed.ts:526-532 (async route, public `fetch` option).
   dismiss: structured third-party JSON, and the nearby branches escape.
8. **L8 — injected sibling.** Comment-header flair field read from a page attribute and rendered
   unescaped. where src/utils/comments.ts:122-124 (+ src/extractors/reddit.ts:180-181). dismiss:
   the builder already escapes author/date/score/link.
9. **L9 — injected sibling.** c2 wiki-link branch reuses the module's quote-only escapeAttr for
   element text. where src/extractors/c2-wiki.ts:159-160 (async route). dismiss: the file has its
   own escaper, used on both address and label.

Different dismissals: one reported value; URL-from-metadata; metadata text in a paragraph; looks
sanitized above / plain text; already-handled neighbour; converter already checks schemes;
structured vendor data; helper already escapes fields; private escaper in the file.

How-type levers: L4 (route where protection never existed), L9 (a check that handles the wrong
context), and the coupled preservation clause (media embeds and relative-address resolution).

## Sibling candidate list (every one found, then the picks)

- `src/utils/comments.ts` comment-header metadata (author/date/score/link already escaped) — picked
  as L8 with a new flair field; reachable from old.reddit.
- `src/utils/transcript.ts` segment/chapter builder — rejected: the YouTube transcript grouping
  path merges segments before the builder, so a per-segment field does not survive to the sink
  without changing the grouping model (would be artificial).
- `src/extractors/c2-wiki.ts` local escapeAttr — picked as L9 in a new link branch, using the
  escaper on element text (wrong context).
- `src/extractors/nytimes.ts` private escapeHtml/escapeAttr — rejected: both are attribute-safe for
  the double-quoted attributes they are used in, so a new branch there would duplicate L9's concept.
- `src/extractors/x-oembed.ts` entity branches — picked as L7 with a new POLL branch (async).
- `src/extractors/hackernews.ts` post link — real upstream, used as L5 rather than as an injected
  sibling.
- `src/utils/bbcode.ts` link/image converter — real upstream, used as L6.
- `src/extractors/_conversation.ts`, `chatgpt.ts`, `grok.ts` footnote links — rejected: the
  conversation extractor re-parses its own HTML, and a probe confirmed the inner pipeline strips
  the injected handler, so the route is not exploitable.
- `src/extractors/bilibili.ts` embed/description — rejected: src and description are constructed or
  escaped already; no reproducible injection.
- `src/defuddle.ts` schema fallback — real upstream, used as L4.

Picks are the three with distinct mechanisms and the most moving parts: an async fetched-data
branch (L7), a builder field reached only through an attribute read (L8), and a private escaper
used in the wrong context behind an async page fetch (L9).

## Verified

- Probes on the pristine pinned tree: all ten security inputs produce executable markup through the
  real APIs (DefuddleClass.parse / async Defuddle with a stubbed fetch); the functional inputs pass.
- Injected tree: full project suite 368/368 passes; the eight affected-area project files used in
  the image build pass.
- Oracle tree (published fix + structured-data fallback fix): 10/10 security and 14/14 functional
  pass through the real verifier runner.
- No-oracle tree: 10/10 security fail, 14/14 functional pass.
- Every check patch was run through the same runner locally:
  `sf_l1..l9` each fail exactly its own lever's security cases with all functional passing;
  `sf_unlisted_sites` fails seven security cases with functional passing; `ff_overbroad` fails the
  YouTube embed functional case; `pass_hardening` and `pass_alt` pass everything.
- Latest upstream read-only: the structured-data fallback now uses the shared sanitizer
  (src/defuddle.ts:204), and the Hacker News / BBCode raw interpolations remain but are covered by
  the shared extractor sanitizer (src/defuddle.ts:1775,1820). The gap is closed in latest.

## Could not verify

- Docker/Harbor gate stages and target-model trials: not run at build time.
- The fixed tree's exact line numbers for the published method (taken from the published diff).
- Whether unseen pages of the same shapes (fixtures) exist; only the checked-in fixture set was run.

## Outside scope

- Nothing outside this advisory's HTML-injection protection was pursued; no other repository or
  advisory was read for a task mechanism.

## Harness notes

- The verifier stages the hidden suites into /workspace/.htests and runs the runner as uid 1000;
  esbuild bundles /workspace/src/node.ts and the product's runtime optional dependencies resolve
  from /opt/verifier/node_modules through NODE_PATH. No network is used at grading time.
- Async extractor requests are stubbed by the suite through the public options.fetch field.
