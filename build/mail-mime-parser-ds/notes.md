# Build notes: mail-mime-parser-ds

- Start (UTC): 2026-10-24 02:17
- End (UTC): 2026-10-24 03:28

## Gate results
- static: PASSED (re-run on the final instruction and tests).
- nop: PASSED — all 15 security tests fail on the pinned+injected tree; all 71 functional tests pass.
- oracle: PASSED — 3 runs, reward 1.0, identical results.
- patches: PASSED — all 12 checks behave as declared: 8 security_fail (each isolating its lever, functional green),
  ff-overbroad and ff-refuse-all functional_fail, pass-hardening and pass-alt reward 1.0.
  Reports kept in build/mail-mime-parser-ds/gate_report-{static,patches}.json.

## Advisory / commits
GHSA-36H5-QG4P-Q2QF / CVE-2026-61815 — zbateson/mail-mime-parser, CWE-93 CRLF /
header injection from decoded or caller-supplied values. Pinned (vulnerable)
`ff054c8e05310c445c2028c6128a4319cc9f6aa8`; published fix `d2970b5df266f62e5ee8e675bfb05502b70fc6e1`
(the same change as `81859c06` on another branch). Track INJECTED, pattern A + B + injected siblings.

## Mechanism (one line)
A value the application supplies (or the library decodes out of a message) is placed into a
header line — or into the uuencoded begin line — unchanged, so a CR/LF inside it starts a new
line; the library's output must keep every such value on one line.

## Levers (8; all verified locally: security fails on pinned+injected, passes on oracle;
## all functional pass on both)
- T1 base (A, landing point): attachment name -> Content-Type name= / Content-Disposition
  filename= (`MultipartHelper.php:314-322`). No reason to dismiss; the report leads here.
- T2 far sites (A, HOW-type): decoded values. The token layer removes CR/LF *before*
  RFC 2047 decoding (`MimeToken.php:46`), the RFC 2231 decoder removes nothing
  (`ParameterPart.php:65-71`), split continuations inherit it, and the signing path copies a
  decoded parameter into a new raw header (`PrivacyHelper.php:84-87`). Dismiss: "the parser
  only reads"; the existing removal looks like the defence.
- T3 uncovered real route (B, HOW-type): quoted-pair continuations arrive as literal tokens and
  skip the token-level removal (`Token.php:40-45`), in quoted and unquoted parameter values; the
  quoted-literal class documentation claims CR/LF are stripped (`QuotedLiteralPart.php`). Still
  present in current upstream. Dismiss: "it is just folding, and the docs say stripped".
- T4 uncovered real route (B): caller-supplied signing parameters raw into Content-Type
  (`PrivacyHelper.php:61-64`). Dismiss: signing is a separate feature with developer constants.
- T5 uncovered real route (B, second implementation): body charset raw on both the
  create-new-part and existing-part paths (`MultipartHelper.php:277`, `:390`). Dismiss: charset
  is developer configuration; the two neighbouring paths look handled.
- T6 uncovered real route (B, protection never existed there): non-MIME attachment name stored
  raw and written into the begin line (`UUEncodedPart.php:56-61`). Dismiss: legacy uuencode, not
  a header, writer in another package.
- S1 injected sibling: inline-image API (`MultipartHelper::createAndAddPartForInlineImage` +
  `Message::addInlineImage`) with its own iconv-only name handling and a raw Content-ID.
  Dismiss: neighbouring feature.
- S2 injected sibling: rename API (`MultipartHelper::setAttachmentFilename` +
  `Message::renameAttachment`) with its own iconv-only name handling. Dismiss: the caller is
  setting a name directly on an existing part.

Distinct reasons to dismiss: none (reported) / parser-only + ineffective existing strip /
folding-and-docs / separate feature / developer configuration / legacy non-header path /
neighbouring feature / caller-trusted rename.

## Why the binary is written this way
The property is stated over the outcome ("no outside value may carry a line break into the text
the library produces, or be returned with one"), so every lever above is covered by the same
sentence. The instruction names the product's composition and reading capabilities (attaching,
embedding, renaming, setting the body, signing; parsing and asking for names/subject/parameters)
so the tests drive surfaces the report names, but it never names a file, a parameter name, a
route or a decoding spelling.

## Candidate list for sibling sites and routes (found before choosing)
Real upstream routes/places considered:
1. `MultipartHelper::createAndAddPartForAttachment` mimeType/encoding raw (O8) — same function as
   the landing point, developer constants; not used (too close to the report, no separate lever).
2. `UUEncodedPart::setFilename` -> begin line — kept as T6.
3. `NonMimeParserService` begin-line filename keeps a bare CR (O8) — legacy parser path, a bare CR
   is not a line terminator in this writer; not used.
4. `MultipartHelper::setContentPartForMimeType` / `createContentPartForMimeType` charset — kept as T5.
5. `PrivacyHelper::setMessageAsMultipartSigned` micalg/protocol — kept as T4.
6. `PrivacyHelper::setSignature` decoded protocol copied into a raw header — folded into T2 (closed by
   the decoder fix, and the oracle also sanitises the copy).
7. `GenericHelper::copyHeader` copies a raw value — raw values legitimately contain the library's
   own folding; no line break is introduced; not used.
8. Quoted-pair literal continuations (`Token`/`QuotedLiteralPart`/`ParameterPart`) — kept as T3; the
   strongest how-type lever found.
9. Address display names (`AddressPart::getValue` composes a quoted value) — decoded values never
   re-enter a written header from that path; not used.
10. `MimePart::setRawHeader` / `addRawHeader` — raw by design (out of scope note).

Injected-sibling candidates considered:
a. inline image (`addInlineImage` + helper) — picked (S1): a distinct neighbouring feature reachable
   from the public message API, with its own composition and a second caller value (Content-ID).
b. rename (`renameAttachment` + helper) — picked (S2): a plausible maintainer addition next to
   getFilename, own composition; dismissed as caller-trusted.
c. "copy decoded param into a new header" helper next to setSignature — dropped: closed by the
   decoder fixes, so not independent.
d. quoted-string unescape decoder added after the token layer — dropped: overlaps T3 and would not be
   reachable through a real entry point without inventing a new input shape.
e. additional attachment metadata header (e.g. Content-Description from the original name) — dropped:
   it would sit inside the published fix's own function and is trivially visible there.
f. "forward/template" API copying decoded header values — dropped: closed by the decoder fixes, so not
   an independent lever.
S1/S2 won because each is the most complex independent candidate: a full composition path in a
different public API with its own value handling, reachable through the same product surface, and
each carries a different dismissal (neighbouring feature vs caller-trusted rename).

## Verified
- Flaw reproduces at the pinned commit through the public API (MailMimeParser::parse, IMessage
  composition methods, IUUEncodedPart::setFilename); probes in
  `~/.tb-graders/cwe/work/mail-mime-parser-ds/probe/`.
- 15 security tests: all fail on pinned+injected; all pass on the oracle.
- 71 functional tests (14 hidden + 57 pristine project tests): all pass on pinned+injected and on
  the oracle.
- Full project suite (609 tests) passes on the oracle tree at build time.
- All 12 check patches behave as declared locally (8 security_fail with functional green,
  ff-overbroad and ff-refuse-all with functional failures, pass-hardening and pass-alt at 1.0).
- `inject.patch` applies with `patch -p1` to the upstream pinned tree; `fix.patch` applies on top and
  reproduces the oracle tree exactly.
- Pattern B rows appended to `build/audit/uncovered-routes.tsv`.
- Read-only look at current upstream (`2d59283`): quoted-pair continuation route still present; the
  signing, charset and non-MIME-name routes were fixed later upstream with a shared control-character
  stripper (so `present_in_latest = no` for those rows, `yes` for quoted-pair).

## Could not verify
- The screener's claim that `UUStream::setFilename` writes the filename verbatim: not needed — the
  output confirms the begin line carries whatever value the part stores.
- Upstream's *release* versions for `present_in_latest`: checked the default branch only.
- Whether the two target models fail all three attempts: the gate and the trial harness decide.

## Out of scope (one line each)
- The sanitised name is still placed inside a quoted-string without escaping `"` or `;` (parameter
  injection, not CRLF) — not pursued.
- `IMimePart::setRawHeader` / `addRawHeader` take raw values by design — not treated as a route.
- A bare CR in a parsed uuencode begin-line filename (legacy parser path) — not pursued.

## Fairness
Everything the tests require is visible from `instruction.md` plus the repository: the invariant is
stated once over the outcome, the preservation clauses name the ordinary behaviour that must keep
working, and every route is reachable from a public API the instruction describes in product terms.
The project's own tests for the touched classes are in the tree, so the coupled contracts (token
literal values, quoted-literal spacing, folded output) are discoverable. A careful engineer who
greps for values interpolated into headers and for the decoding entry points finds every lever in
about 45 minutes; the two how-type levers need the strip/decode ordering and the literal-token
bypass to be understood.

## Scratch
`~/.tb-graders/cwe/work/mail-mime-parser-ds/` (repo with an injected commit, oracle work tree,
probe scripts, checks source, run_hidden.sh).
