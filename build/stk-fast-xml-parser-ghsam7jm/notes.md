# stk-fast-xml-parser-ghsam7jm — build notes

start_utc: 2026-10-26T12:31:51Z (build job start)
end_utc: 2026-10-26T__:__Z (write after the container gate)

## Stack

Pinned commit a874ce78df0be1b5dceadc4e5e7e549c65a7a6ce (fast-xml-parser 4.1.2) is the first
parent of a4bdced80369, the first commit of advisory A's fix (GHSA-6w63-h3fj-q4vw: entity
encoding bypass via regex injection in DOCTYPE entity names). A's fix landed as a4bdced80369
(rewrite of the DOCTYPE entity reader) and 39b0e050bb90 (a special-character reject list).
Advisory B (GHSA-m7jm-9gc2-mpf2) was fixed later on the same line by ddcd0acf26dd and
943ef0eb1b2d, which escape regex characters that A's reject list missed and apply the same
escaping to the application-registered entity path. The task is H3b.

## Levers (one line each)

- T1 (A, advisory route; both): a DOCTYPE entity name accepted by the declaration grammar is
  interpolated into the matcher for its references, so a declaration under one name answers a
  differently named reference. src/xmlparser/DocTypeReader.js:108-116. No reason to dismiss:
  the report's example points here.
- T2 (A's far site / B; deepseek): the same name-to-matcher construction is implemented a second
  time behind the application-facing entity API, whose guard rejects only '&' and ';'.
  src/xmlparser/OrderedObjParser.js:57-64 (producer src/xmlparser/XMLParser.js:45-55). Reason to
  dismiss: the names are supplied by the application, not by the parsed document, and the
  documented example names are constants such as '#xD'.
- T3 (B, uncovered upstream; mimo): declared replacement text is handed to String.replace as the
  replacement pattern, so characters in the declared text duplicate or drop surrounding text.
  src/xmlparser/OrderedObjParser.js:370-389. Reason to dismiss: DOCTYPE values cannot contain
  '&', so the usual entity-expansion tricks look blocked and the visible effect is only
  duplication of the text around the reference.

Concepts (reference-fix edit sites): T1 (DocTypeReader.js), T2 (OrderedObjParser.js:62),
T3 (OrderedObjParser.js replaceEntitiesValue). Three independent edits; DeepSeek-type: T2;
MiMo-type: T3. T4 from the reader record (re-scanning through the literal '&') was excluded:
its natural fix removes the dynamic-entity expansion that the project's own specification
asserts (spec/entities_spec.js) and that the report's preservation clause protects.

## Verified

- Behaviour reproduced on the pinned tree through the public API before writing the tests:
  DOCTYPE name `a\` makes `&a;` expand (text, attribute, nested element); registered `a.b`
  over-matches `&aZb;` and `a+b` over-matches `&aab;`; declared `$'` turns `PRE&x;POST` into
  `PREPOSTPOST` and `$$` into `PRE$POST`; registered `$'` behaves the same.
- Hidden security: 9 tests, all fail on the pinned tree and all pass on the reference
  (text/attribute/nested/alongside declarations; dot and plus registered names; three
  replacement-text cases).
- Hidden functional: 14 library cases plus the pristine project entity specification
  (21 specs) = 35 tests, all pass on the pinned tree, the reference, and every check patch.
- Each check patch was applied to a fresh pinned copy and run against both suites:
  reference 9/9 + 35/35; miss_T1 4 T1 failures; miss_T2 2 T2 failures; miss_T3 3 T3 failures
  (functional always 35/35); upstream_first_fix (A alone) 5 security failures;
  upstream_fix (A plus B ported) 3 security failures; hardening 9/9 + 35/35;
  alternative 9/9 + 35/35; ff-refuse-all functional 15/35; ff-strict-names functional 31/35.
- The project's own entity specification (21 specs) passes on the pinned tree and on the
  reference fix.
- Control task: pinned 0/4 security + 35/35 functional; control reference 4/4 + 35/35;
  sf-no-fix 0/4 + 35/35; ff-refuse-all 4/4 + 15/35.

## Could not verify

- The prompt names `pipelines/stacking/out/reader/h3-ghsa-m7jm-9gc2-mpf2.json` as the reader
  record; that path does not exist. The record used is
  `pipelines/stacking/out/reader-ds/h3-ghsa-m7jm-9gc2-mpf2.json` (same candidate id and
  content, from the DeepSeek reader run). The manifest records the path that exists.
- B's 2026 fix also touches `src/v6/EntitiesParser.js`, a file that does not exist at the 2023
  pin. `checks/upstream_fix.patch` ports B's document-reader and application-registered changes
  to the pin and omits the v6 file, which is outside the pinned tree.
- `checks/upstream_first_fix.patch` is the net `a874ce78..39b0e050bb90` change to
  `src/xmlparser/DocTypeReader.js`; A's added specification case is not included.
- T2's practical exposure depends on an application passing a name it did not choose to
  `addEntity`; the advisory's own fix treats that path as in scope, but no real caller was
  audited.
- T1 is the anchor and is easy for both models (the report points at DOCTYPE declarations);
  T2 and T3 carry the model-specific difficulty.
- Whether current upstream will later change the replacement handling could not be checked
  beyond the repository HEAD available here (fe9a852), where the value is still passed as the
  replacement string.

## Gate

- static (stacked): PASSED. static (control): PASSED.
- nop / oracle / patches: see below (filled after each stage).
