# mail-mime-parser-ds — build notes

- Start (UTC): 2026-10-24T02:19Z
- End (UTC): (filled at the end)
- Task: `mail-mime-parser-ds`, repo zbateson/mail-mime-parser, pinned `ff054c8e05310c445c2028c6128a4319cc9f6aa8`,
  published fix `d2970b5df266f62e5ee8e675bfb05502b70fc6e1` (same change as `81859c06abb5d79f04b7a3254d293d0a91065948`
  on another branch; both are descendants of the pinned commit).
- Advisory: GHSA-36H5-QG4P-Q2QF / CVE-2026-61815, CWE-93.
- Pattern A+B. Track injected. Delivery format: Frontier separate-verifier layout (`/workspace`,
  `tests/Dockerfile`) as enforced by `builder/conformance_check.py` and `builder/gate.py`
  (the newest gate-green tasks use this layout).

## Security property (written once, before routes)

> No value that the library returns for a header or for an attachment name, and no value it
> writes into a message it produces, may contain a carriage return or a line feed — however that
> value was supplied, read, decoded, assembled, split or folded.

The report states this once, plus the impact through one example (an attachment name supplied by
an uploader), the preservation clauses, and "examples are examples". It does not name any route,
site, file, or mechanism.

## Levers (one line each)

- **T1** — Pattern A (report-led, write path): a caller-supplied attachment name with CR/LF is
  interpolated into the composed attachment headers (`src/Message/Helper/MultipartHelper.php:314`).
  Dismissal: none; this is the reported route.
- **T2** — Pattern A far site, how-type (ordering / ineffective defence): the RFC-2047 decoded-word
  constructor strips CR/LF *before* decoding, so a B- or Q-encoded word decodes to CR/LF afterwards
  (`src/Header/Part/MimeToken.php:46`). Dismissal: the constructor already removes CR/LF, so a
  reader concludes it is handled.
- **T3** — Pattern A far site, how-type (decoder semantics + shape): the RFC-2231 parameter decoder
  percent-decodes and converts the charset with no control-character removal
  (`src/Header/Part/ParameterPart.php:65-71`); split continuations inherit it. Dismissal: a getter is
  meant to return the true decoded text, so stripping looks like a parser-semantics regression.
- **T4** — Pattern B / route where protection never existed, how-type (sink in another module):
  the uuencode filename is emitted verbatim into the `begin` line; the public setter stores it raw
  and the non-MIME parser keeps a bare CR (`src/Message/UUEncodedPart.php:56-61`,
  `src/Parser/NonMimeParserService.php:76-80`). Dismissal: legacy non-MIME path, the begin line is
  not a header, and the line is written by an external stream decorator.
- **T5** — Pattern B (uncovered route, same function): the caller-supplied MIME type and transfer
  encoding are interpolated raw into `Content-Type` / `Content-Transfer-Encoding`
  (`src/Message/Helper/MultipartHelper.php:317-321`). Dismissal: the MIME type/encoding are
  developer constants, not user data; the advisory names the filename.
- **T6** — Injected sibling (write sink): a public "rename this attachment" setter rebuilds the
  disposition header with the same composed-header idiom (`src/Message/MimePart.php:70`).
  Dismissal: a plain setter, not the reported add path; raw header setting is raw by design.
- **T7** — Injected sibling (parse decoder, ordering): a compatibility step percent-decodes plain
  quoted parameter values after the token-level sanitation (`src/Header/Part/ParameterPart.php:78`).
  Dismissal: ordinary quoted values are literals; percent-decoding is an interop tweak, not
  decoding, and the existing decoder already strips CR/LF.

## Sites, routes, input shapes covered by the security tests

- write path: `Message::addAttachmentPart`, `Message::addAttachmentPartFromFile`; MIME branch;
  non-MIME/uuencode branch.
- write values: filename (raw CR/LF, non-ASCII + CR/LF, control chars beyond CR/LF are **not**
  required), MIME type, transfer encoding.
- parse path: `MailMimeParser::parse` / `Message::from` -> `getFilename`, `getHeaderParameter`,
  `getHeaderValue`, `getSubject`.
- parse shapes: RFC-2047 B and Q words in a parameter and in a plain header; RFC-2231 with a
  charset, without a charset, and split continuations; plain percent-encoded quoted value (T7).
- re-emission: parsed `protocol*=` parameter copied into a raw header by `setSignature`.
- uuencode: public `UUEncodedPart::setFilename`, non-MIME `addAttachmentPart`, parsed `begin`
  line with a bare CR.
- injected rename setter.

## Coupled must-keep-working behaviour (functional tests)

- Composed attachment headers keep their `"$type;\r\n\tname=\"...\""` folding (a fix that strips
  CR/LF in the raw-header store breaks it).
- Exact ASCII names, and non-ASCII names keep transliterating as today (`résumé` -> `resume`).
- Non-MIME uuencode `begin` lines and attachment content round-trip.
- Parsed non-ASCII RFC-2231/encoded-word names stay intact; folded quoted values still unfold to
  `a b.pdf`; split continuations still assemble.
- Plain quoted percent values keep decoding (`a%20b.pdf` -> `a b.pdf`, the injected compatibility
  behaviour).
- Renaming an attachment with a legitimate name still works and keeps the disposition type.
- A parsed signed message with a normal protocol parameter still re-emits the same protocol.
- The project's own 609 tests pass at the pinned+injection baseline and after the fix.

## Candidate list (every sibling site/route found) and why the picks won

Real upstream candidates:
1. `MultipartHelper::createAndAddPartForAttachment` filename, MIME branch — T1 (base).
2. Same function, non-MIME -> `UUEncodedPart::setFilename` — part of T4.
3. `UUEncodedPart::setFilename` public setter — T4.
4. `Parser/NonMimeParserService` begin-line filename (bare CR) — T4 shape.
5. Same function, `$mimeType` / `$encoding` — T5.
6. `PrivacyHelper::setSignature` re-emitting the decoded `protocol` parameter — T3 route
   (closed by the T3 decoder fix; tested end-to-end).
7. `MimeToken` decoded word — T2.
8. `ParameterPart::decodePartValue` (and `SplitParameterPart` inheritance) — T3.
9. `MultipartHelper::createContentPartForMimeType` / `setTextPart` / `setHtmlPart` charset — not
   covered: charset is developer configuration, not attachment data; the property is about values
   the library derives or the caller supplies for a message's headers, and these are the same
   class, but no test asserts them (kept out of scope; see "outside scope" line).
10. `PrivacyHelper::setMessageAsMultipartSigned` micalg/protocol — developer configuration; out.
11. `GenericHelper::copyHeader` raw copy — raw by design; out.
12. `MimePart::setRawHeader` / `addRawHeader`, `PartHeaderContainer::set/add` — raw escape hatch by
    design; out.
13. `Message::addAttachmentPartFromFile` basename — part of T1 shape.
14. `MultipartHelper::createAndAddPartForAttachment` disposition — normalised by
    `Message::addAttachmentPart`; direct-helper callers only; out of the tested set.

Injected sibling candidates considered:
a. `MimePart::setFilename` rename setter (O8b #1) — **picked (T6)**: public, reaches the same sink
   from a new entry point, own fix, plausible because `getFilename()` exists with no setter.
b. Percent-decode of plain quoted parameter values in `ParameterPart::getValueFromParts`
   (O8b #3 shape: a decoder after the token-level strip) — **picked (T7)**: how-type ordering,
   independent fix, plausible interop tweak.
c. A quoted-pair unescape using C-style escapes — rejected: the parser already handles quoted
   pairs per RFC; a `stripcslashes`-style change would be a regression, less plausible.
d. A double-decoding filename accessor — rejected: contrived, and the parser already decodes
   RFC-2231.
e. An inline-image helper with its own header composition — rejected: a second copy of the write
   path, the same concept as T1/T6, and a maintainer would call the existing helper.
f. A bulk attachment spec/import method with its own header composition — rejected: same reason
   (second write-path copy) and the natural fix (sanitise in the shared builder) closes it.
g. A "copy decoded header into a new message" helper (O8b #2) — rejected as a lever: its only
   fixes are the T2/T3 decoder fixes or a sink the rename setter already covers, so it cannot have
   an independent `sf-miss-S` patch.
h. A serializer that decodes headers on save — rejected: it would call the decoders, so it is on
   the check's path, not a producer off it.

## Injection (pinned tree only; the published fix never touches these methods)

- `MimePart::setFilename(?string)` + `IMimePart::setFilename` declaration: rebuilds
  `Content-Disposition` as `"$disposition;\r\n\tfilename=\"$name\""`; `null` removes the header.
- `ParameterPart::getValueFromParts` calls a new `decodePercentEncoding` for non-RFC-2231 values
  (only when a `%XX` sequence is present), keeping RFC-2231 decoding as-is.

## Oracle

Published fix (3 files) + sanitisation of the injected rename setter + sanitisation in
`UUEncodedPart::__construct`/`setFilename` + strip after the injected percent decode + sanitisation
of the attachment MIME type and transfer encoding. Tests assert outcomes, so a fix at another valid
layer (central raw-header sanitation that preserves folding, or part-value sanitation) also passes;
`pass-alt.patch` proves it.

## Checks to build

- `sf-miss-T1..T7` (one per lever), `ff-overbroad` (strips all CR/LF in the raw-header store,
  breaking composed folding), `pass-hardening`, `pass-alt`.

## Verified so far (probe log)

- Baseline injections confirmed through public APIs: write MIME, write non-MIME, mimeType,
  encoding, direct uuencode setter, parsed uuencode bare CR, B/Q encoded words in parameters and
  Subject, RFC-2231 with/without charset, split continuations, percent plain value, and
  `setSignature` re-emitting the decoded protocol as a real `Bcc:` line.
- Published fix closes: write MIME, non-MIME write via the shared safe name, all MIME decoders,
  and the setSignature re-emission. It leaves open: direct `UUEncodedPart::setFilename`, parsed
  uuencode bare CR, mimeType, encoding, and the two injected siblings.
- PHP 8.3 + PHPUnit 9.6 + project suite: 609 tests pass at pinned.
