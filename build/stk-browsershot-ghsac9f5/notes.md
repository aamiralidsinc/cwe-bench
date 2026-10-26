# stk-browsershot-ghsac9f5 — build notes

- Start: 2026-10-26T02:06:11Z
- End: pending (filled after the gate)
- Reader record: `pipelines/stacking/out/reader-ds/h3-ghsa-c9f5-29f6-c35w.json` (the build prompt named
  `pipelines/stacking/out/reader/...`, which does not exist on this checkout; the reader-ds copy is the
  record the runner actually produced).
- Pinned commit `bc075ca36411a5df6130e6b2f22b67fd35bd4e7f`; its rule was verified with
  `git rev-list --parents -1 fae8396` (first parent = bc075ca).

## Levers (one line each)

- **A1 — advisory route** (`src/Browsershot.php:258-264`): the page-address guard compares the raw
  string, so leading whitespace, a source-view prefix or backslashes reach the renderer. DeepSeek type.
  Dismissal: a guard is already there and the plain forms are refused.
- **T1 — construction-time address** (`src/Browsershot.php:86-88`): the constructor stores the address
  without validation; documented as the alternative to the convenience constructor. DeepSeek type.
  Dismissal: trusted configuration; the guard belongs to the setter.
- **T5 — library-internal document address** (`src/Browsershot.php:1022-1024,1200-1205`): the library
  builds its own `file://` document address in the same field a caller writes, so a check at the request
  sink also refuses documented rendering. MiMo type (coupled must-keep-working value).
- **T2 — caller-supplied base address** (`src/Browsershot.php:981-984`, `576-581`, `1011-1012`;
  `bin/browser.cjs:116,122,208,293`): a base address stored by the dedicated accessor, or by the public
  generic settings accessor and merged into the request later, becomes the address the document's
  references resolve against. DeepSeek type. Dismissal: it is only a base for relative resources, and
  the page-address guard is believed to cover navigation.

Concepts: `[A1]`, `[T1,T5]`, `[T2]` (3 independent reference edit sites: the setter, the constructor,
the request-construction base-address check).

## Substitution

The reader's T4 (a document's own relative/absolute references resolving against the library's temporary
`file://` document, `bin/browser.cjs:161-238`) is real but only observable with a browser engine
resolving the subresources. The build runs with no browser and no network, so T4 was not built; its
same-sink, differently-reached sibling — the caller-supplied base address through the dedicated and the
generic settings accessor — is T2's second security test (the merged route). The reader's T3 and T6 were
excluded for the reasons the record gives (documented `htmlFromFilePath` behaviour; documented Chromium
flags).

## Verified (locally, then in the built agent image)

- Pinned tree: 8 security tests fail (every attack form leaks a marker into the rendered output), 11
  functional tests pass.
- Reference fix: 8 security + 11 functional pass, as uid-1000 `agent` in the built `environment/` image.
- First published fix (trim only): 6 security tests fail (source-view, backslash, constructor, both
  base-address routes).
- Complete published fix state (`bc075ca..f791ce0`, source): 4 security tests fail (constructor and both
  base-address routes) — the stack adds real coverage.
- Concept-miss patches: `miss_advisory` → the 4 advisory tests fail; `miss_constructor` → the 2
  constructor tests fail; `miss_content_url` → the merged-route base-address test fails (the dedicated
  accessor alone is not enough). Functional passes for all three.
- `functional_overbroad` (rejecting the library's own generated document address at the sink): 4
  functional tests fail. `refuse_all`: 7 functional tests fail.
- `alternative` (scheme parsing, validation in the generic settings accessor) and `hardening`
  (reference plus document-source and setter hardening): both score 1.0.
- Project tests: the project's own URL-guard assertions (`tests/BrowsershotTest.php:55-69`) are
  reproduced unchanged in the functional group and pass on the pin and on the reference.

## Could not verify

- The reader's T4 (browser-resolved subresources) — no browser engine is available offline; see above.
- The remaining upstream project suite needs a real browser and the network; only the URL-guard
  assertions for the affected area run here.
- The `present_in_latest` register values were read from the clone's `origin/main` (`3a2ad83`); the
  constructor and `setContentUrl` gaps are still present there.

## Scope note

`setNodeBinary`/`setIncludePath`/`setNodeModulePath` are interpolated into a shell string without
escaping; that is a separate input-validation surface outside these advisories and was not built on.

## Build-time corrections

- The first nop trial showed the suites themselves behaving exactly as intended in Harbor (8 security
  failures, 11 functional passes) but `score.py` could not run: the verifier image is PHP-based and did
  not carry `python3`. `python3` (and `curl`, used by the Node boilerplate) were added to the apt list
  of both images, and the control's copies. The nop stage was re-run after the fix.

## Gate log (shared VM, heavy concurrent load)

- static: fails only on the expected missing `blind` patch (written after this build).
- nop: PASSED — 8/8 security tests fail on the pinned tree, 11/11 functional pass (trial
  `stk-browsershot-ghsac9f5-nop-1792982003`).
- oracle: the first parallel attempt was cut by the known Harbor temp-file race (`docker compose`
  could not open its own `/tmp/tmp*/...resources.json`); classified `infra`, retried sequentially with
  an isolated `TMPDIR` on the root disk. All three runs reward 1.0 (8/8 security, 11/11 functional)
  with identical results — PASSED.
- patches: running.
