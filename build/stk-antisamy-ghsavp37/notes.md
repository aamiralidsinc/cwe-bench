# stk-antisamy-ghsavp37 — build notes

Start (UTC): 2026-10-26T02:20:50Z (job start; builder session began at the same slot)
End (UTC): pending gate completion

Candidate: h3-ghsa-vp37-2f9p-3vr3 (reader record under
`pipelines/stacking/out/reader-ds/h3-ghsa-vp37-2f9p-3vr3.json`; the build prompt's
`out/reader/` path does not exist on this checkout). Repo `nahsra/antisamy`, pinned
`578d1f99b5a8d96cbeedef5970eee97fbeb23d27` (first parent of fix A `0199e7e194db`, verified with
`git rev-parse 0199e7e^`). Advisories A = GHSA-3pqg-4rqg-pg9g / CVE-2022-28367 (fix
`0199e7e194db`), B = GHSA-vp37-2f9p-3vr3 / CVE-2022-29577 (fix `32e273507da0`).

## Levers

- T2 (advisory route, both types) — `AntiSamyDOMScanner.processStyleTag`: only the first child of a
  style element is handed to the CSS scanner; later text children are serialised raw and a browser
  reparses the smuggled markup. Reason to dismiss: NekoHTML is assumed to return one text child, and
  any element children are still walked. Fix: A+B (concatenate every child, validate once, remove
  the rest by iterating from the end).
- T4 (uncovered upstream, both types) — `antisamy.xml` `onsiteURL`: the character class accepts a
  backslash, so `/\host` and `\\host` pass the policy but a browser normalises the leading separator
  pair to a protocol-relative reference (another origin). Reason to dismiss: the existing `(?!//)`
  lookahead looks like it already refuses protocol-relative references. Coupled legitimate value: a
  relative path with an internal backslash (`docs\readme.html`) must keep working.
- T5 (uncovered upstream, MiMo type) — `ASXHTMLSerializer.endElementIO`: non-void elements in the
  policy's allowed-empty list (`div`, `textarea`, `object`, ...) are serialised self-closed in XHTML
  output; a browser holds such an element open and absorbs everything rendered after the submitted
  fragment. Reason to dismiss: the shipped policies remove script/iframe and HTML output already
  closes non-void elements, so the short default require-closing list looks sufficient. Coupled
  legitimate values: void elements keep ` />`, and an approved empty container is still returned.

## Rejected from the reader's record

- T1 (SAX parser missing `enforce-strict-attribute-names`): the neko-htmlunit 2.24 sources contain no
  such feature; the DOM parser's `setFeature` is swallowed as unrecognised, so the DOM-side
  protection is inert too. Not a real asymmetry — dropped.
- T3 (`ASXHTMLSerializer` missing `escapeURI`): xerces `XHTMLSerializer` sets `_xhtml = true`, and
  `HTMLSerializer.serializeAttribute` then uses `printEscaped(value)` for every attribute; the
  `escapeURI` override is only reached in HTML mode. No gap — dropped.
- T5 was substituted for T1/T3 (it is the record's fifth independent group, real unmodified code).

## Verified

- Pinned 578d1f9, `mvn test` (Java 11, Maven 3.9): 107 tests, 0 failures.
- Reference fix, `mvn test`: 107 tests, 0 failures.
- Hidden suites against pinned: 8/8 security tests fail, 8/8 functional tests pass.
- Hidden suites against the reference fix: 16/16 pass.
- Every `checks/*.patch` applies to a clean pinned tree with `patch -p1 --dry-run`.
- Variant behaviour measured locally through the same JUnit harness (security failures /
  functional failures): miss_t2 3/0, miss_t4 2/0, miss_t5 3/0, upstream_first_fix 6/0,
  upstream_fix 5/0, one_direction 2/0, hardening 0/0, alt_fix 0/0, functional_fail 6/2,
  adjacent_api 6/1. crash_as_refusal is declared security_fail; its gate run is authoritative.
- `check_stack.py stk-antisamy-ghsavp37`: conforming (3 concepts, pattern H3b).
- Gate static (stacked and control): PASSED.
- Gate nop: PASSED (8/8 security fail, 8/8 functional pass on the pinned tree).
- Gate oracle: PASSED (3 runs, each reward 1.0, 8/8 security and 8/8 functional).
- Gate patches: pending at the time of writing; see `patches-gate.log` and `gate_report.partial.json`.

## Could not verify / notes

- The reader's T1 and T3 reasoning is not supported by the pinned tree (see above); the design
  substitutes T5, so the stacked concept count is 3 (T2, T4, T5), not the reader's 4.
- T4's observable effect through this library is a lexical-versus-resolved URL mismatch (open
  redirect / dangling markup); its classification as script execution is not established from the
  pinned tree. It is built as a URL-origin invariant, separate from the markup property.
- T5's effect depends on the browser reparsing XHTML-as-HTML; the tests assert the serialisation
  property that causes it, not a live browser.
- Latest upstream (checked 2026-10-26, read-only): `onsiteURL` still contains the backslash in both
  character classes; the XHTML serializer no longer exists in the current tree. The register rows
  record `yes` for T4 and `no` for T5 accordingly.
- The pin predates both published fixes and contains neither advisory's regression tests (the
  upstream tests were added by `0199e7e` and `32e27350` only).
