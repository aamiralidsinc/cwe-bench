# oapi-codegen-ds — build notes

- Start: 2026-10-24T04:57:00Z
- End: 2026-10-24T08:28:00Z (final patch check completed; deliverables finalized)
- Advisory: GHSA-RJWR-M7QX-3FJR / GO-2026-6016 (oapi-codegen/oapi-codegen)
- Pinned: b363ca5db8465d8772855797a8fb56918e8264b3; published fix: 19c6282e9a6fb84b51aa92b12fad1f0b7e5f5ef6
- Track: injected; pattern: A+B.

## Security property (one)

Text taken from the OpenAPI document is data, never code: for any document, generation either
fails with an error or produces a single syntactically valid Go file in which no identifier,
declaration, import, statement or expression comes from document text; every emitted piece of
document text appears only inside a correctly quoted Go string literal (reading back as the exact
original) or inside a comment.

## Levers (one line each)

- T1 (report target; how-type shape/coupled): the four server-URL emission points
  (`pkg/codegen/templates/server-urls.tmpl:6-7,39,58,67`) — description in the no-variable and
  constructor forms, URL literal in both, non-enum default. Reason to dismiss: "escaping quotes is
  enough, and the reported example is the form with no variables".
- T2 (pattern B, how-type, main): the shared constant pipeline
  (`pkg/codegen/templates/constants.tmpl:12` fed by `GenerateEnums` in `pkg/codegen/codegen.go:1009-1016`)
  wraps string enum values in raw quotes; the published fix never touches it and schema enums look
  like a different feature. Producer off the check's path: `GenerateEnums` builds the definition,
  the shared template emits it.
- T3 (pattern A far site; how-type): the exported string-literal helper
  (`pkg/codegen/utils.go:909-912`) used by the generated client's response dispatch
  (`pkg/codegen/template_helpers.go:273,281`) — a backslash before a quote defeats its quote-only
  escaping. Reason to dismiss: "the helper is an exported utility that already escapes quotes and is
  used for content types, so it is unrelated to the server-URL report".
- S1 (injected, how-type, different field/template): document title and description emitted as a
  comment after the imports (`pkg/codegen/templates/imports.tmpl`, context built in
  `GenerateImports`); a line break escapes the comment. Reason to dismiss: "document metadata in the
  preamble is not the server description the report shows".
- S2 (injected, how-type, second implementation): a generated `<Server>Description` constant built
  in Go (`pkg/codegen/server_urls.go`, emitted by `server-urls.tmpl`) with its own quote-only
  escaping; a backslash before a quote breaks out. Reason to dismiss: "a constant built in Go and
  emitted next to the URL looks internal and already handled".

## Injected sibling candidates searched (full list) and why the picks won

1. `server-urls.tmpl:53` enum default-pointer comment with `ServerURLDefaultPointer.Description` —
   rejected as a pick: same description/comment concept as T1, one line from the reported site, and
   a solver sweeping descriptions catches it. (Cheap, but weak.)
2. `imports.tmpl` document title/description comment — CHOSEN (S1): different field and template,
   reached on every generation, a maintainer adding document metadata to the preamble would write
   the raw interpolation exactly as the neighbouring raw text does.
3. `server_urls.go` generated description constant — CHOSEN (S2): a second implementation of the
   escaping in Go, a file the published fix never touches, so fixing the helper and the template does
   not fix it; stripping newlines but only escaping quotes mirrors the old helper's bug.
4. `strict/strict-interface.tmpl:132` raw `{{.ContentType}}` in `mime.FormatMediaType` — rejected:
   reached only when a response declares a multipart type, and the surrounding branch is inside a
   function body, so a valid-Go injected declaration needs a fragile brace-closing payload.
5. `gin/chi/gorilla/stdhttp` router templates interpolating path-parameter names raw into string
   literals — rejected: the name also becomes a Go parameter/identifier, so most payloads make the
   file invalid (an error, not injected code), and the route needs a router generator the report
   never mentions; payload design was fragile.
6. Response content types in the "unsupported" comment (`template_helpers.go` default branch) —
   rejected: only multipart/form/text names reach it and the comment sits inside a function body; the
   reachable strict-dispatch route (T3) already covers the shared helper with a clean valid-Go payload.
7. Server variable/placeholder names emitted as identifiers, parameters and literals
   (`server_urls.go:267-282`) — rejected: names are also used as Go identifiers, so a quote/newline
   produces an error rather than executable injected code; the property is already satisfied by a
   refusal. Recorded in the register as not built.
8. Security-scheme provider names in `constants.tmpl` — rejected: provider names are sanitised via
   `sanitizeGoIdentity` before use in identifiers, and their only literal use is inside a
   `"{{.ProviderName}}.Scopes"` string that is also sanitised.

S1 and S2 are the only candidates that are reachable through the ordinary generation call, produce a
valid-Go injected top-level declaration on the pinned tree, and sit in code the published fix never
touches. They have different reasons to skip.

## Verified

- Pinned + injection: 10/10 security tests fail (sentinel becomes a declared Go identifier); 8/8
  functional tests pass; the whole `pkg/codegen` test package passes.
- Oracle (published fix reduced to source + every route/sibling fix): 10/10 security and 8/8
  functional pass; `pkg/codegen` passes.
- Every check patch was run locally against both suites:
  - sf-miss-template: 5 T1 security fail, all functional pass.
  - sf-miss-enums: T2 security fail, functional pass.
  - sf-miss-helper: T3 security fail, functional pass.
  - sf-miss-header: S1 security fail, functional pass.
  - sf-miss-desc-const: S2 security fail, functional pass.
  - sf-crash (panic instead of refusal): security group fails, functional pass.
  - ff-refuse-all / ff-overbroad / ff-shared-helper: functional fail.
  - pass-hardening / pass-alt: all pass.
- injection.patch and fix.patch apply cleanly with `patch -p1` to the pinned tree; every checks/
  patch applies cleanly to the pinned+injected tree.
- Latest upstream (read-only, 2026-10-24): `main` now uses `toGoString` for string enum values and
  `strconv.Quote` in the helper, so the enum route (T2) and the helper shape (T3) are no longer
  present upstream. T2 was therefore real, unmodified code at the fix commit that upstream fixed
  later, independently of 19c6282.

## Could not verify

- Whether kin-openapi's loader/validator rejects quotes or line breaks in every field was not
  exhaustively checked; the tests build documents through the same public parse+Generate path with
  values the loader accepts, so each tested shape is reachable in practice.
- Current-upstream status was checked only for the two files above (raw GitHub reads); the other
  register columns stay `unknown`.
- `repo_mb` was not measured.

## Out of scope (one line)

Parameter names, content types and security-scheme provider names interpolated raw across many
router templates are the same mechanism class but outside the server-URL advisory's own protection;
they were not built on.

## Gate results (all four stages, run one at a time)

- static: PASSED.
- nop: PASSED — 10 security tests fail on the pinned+injected tree, 41 functional testcases pass.
  (First nop attempt failed on the project's own `TestRemoteExternalReference`, which fetches a
  GitHub URL; the project-test group is now scoped to the offline tests of the affected area.)
- oracle: PASSED — 3/3 runs reward 1.0 with identical security/functional results.
- patches: PASSED — 11/11 checks as declared:
  sf-miss-template (5 security fail), sf-miss-enums (1), sf-miss-helper (1), sf-miss-header (2),
  sf-miss-desc-const (1), sf-crash (security group fails), three functional_fail patches,
  pass-hardening 1.0 and pass-alt 1.0. The blind patch is supplied later by the blind-fix pass.

## Fairness notes seen by the builder

- The security payloads are harmless marker identifiers; no exploitation steps are written in prose
  anywhere in the task.
- The content-type route needs two vendored JSON media types to reach the strict dispatch; the fix a
  solver needs is the shared string-literal helper, not knowledge of that shape.
- The preservation clause enumerates data classes (URL, default, permitted value, description,
  document metadata) in product terms only; no file, function, template or sibling is named.
