# nuclei-s3 — build notes

Start (UTC): 2026-10-25T22:56:08Z (job start). End (UTC): see gate report.

## What the task is

Pattern A + injected on projectdiscovery/nuclei, pinned at `1e294aa7` (the parent of the published
rendering-boundary fix `ccbfb12`). Protected outcome: text that entered from the scanned target is
never interpreted as template or DSL source, so it cannot disclose scanner-host environment
variables; it is delivered, compared and reported literally. One general property in the report
covers every route.

## Levers (one line each)

- **L1 — DAST/fuzz pipeline** (`pkg/fuzz/execute.go:151-164,221-260` + `pkg/fuzz/parts.go:194-202`,
  real, advisory route). The value sweep and the payload render evaluate target-derived values a
  second time. Dismissal: interactsh-only bookkeeping; the value map looks like CLI variables.
- **L2 — shared evaluator** (`pkg/protocols/common/expressions/expressions.go:52-89`, real, how-type
  shape trap). A value substituted raw inside a template-authored expression's quoted argument can
  close the quote and inject DSL. Dismissal: the existing tests already show values staying literal
  for plain placeholders, so the evaluator looks protected.
- **L3 — matcher re-compile** (`pkg/operators/matchers/match.go:196-207`, real, second
  implementation). The matcher resolves markers then compiles the result, so a response value can
  change the matcher. Dismissal: the expression is authored and the value sits inside a literal, so
  it reads as matcher semantics.
- **L4 — declared-variable merge** (`pkg/protocols/common/variables/variables.go:83-89,118-126`,
  real, coupled must-keep-working). A supplied value shadowing a declared variable is rendered
  instead of used as data. Dismissal: overrides are a legitimate precedence feature.
- **L5 — shared placeholder renderer** (`pkg/protocols/common/replacer/replacer.go:13-20`, real,
  route where the protection never existed). The second marker-form pass rescans the first pass's
  output, so a target value carrying the legacy form resolves. Dismissal: legacy syntax; the
  published fix never touches this file (current origin/main 731d4383 still has the two passes).
- **S1 — DSL extractor** (`pkg/operators/extractors/extract.go:180-196`, injected, second
  implementation). Extractor expressions resolve markers and re-compile the result. Dismissal:
  extraction is output-side and mirrors the matcher feature.
- **S2 — report-time extraction expansion**
  (`pkg/protocols/common/helpers/eventcreator/eventcreator.go:34-38,63-88`, injected). Extracted
  values are expanded before reporting. Dismissal: they already look like final results.

Concepts: 7 independent edit sites. Injected siblings: S1 (feature parity with the matcher) and S2
(report convenience); both are code a maintainer could have left where the published fix never
touches.

## Verified locally (this session, Go 1.27.2 on the host; verifier toolchain is Go 1.25.7)

Built the pinned+injected tree, the reference, and every check variant, then ran both hidden suites
as standalone Go modules against a loopback target. Counts include subtests.

| variant | security | functional |
|---|---|---|
| pinned+injected | 0/10 | 15/15 |
| reference | 10/10 | 15/15 |
| sf-no-fuzz | 9/10 (L1 fails) | 15/15 |
| sf-no-expr | 7/10 (three L2 tests) | 15/15 |
| sf-no-matcher | 8/10 (both L3 tests) | 15/15 |
| sf-no-vars | 9/10 (L4 fails) | 15/15 |
| sf-no-replacer | 9/10 (L5 fails) | 15/15 |
| sf-no-extract | 9/10 (S1 fails) | 15/15 |
| sf-no-event | 9/10 (S2 fails) | 15/15 |
| upstream_fix | 7/10 (L5, S1, S2 fail) | 15/15 |
| ff-overbroad | 10/10 | 13/15 (authored legacy placeholder) |
| pass-hardening | 10/10 | 15/15 |
| pass-alt | 10/10 | 15/15 |

Project tests for the affected packages pass on the pinned+injected tree and on the reference,
except the pinned `TestEvaluateWithInteractshOverrideOrder` subtest that asserts the old
"input override is interactsh-replaced" behaviour: the published fix changed that same test, so the
reference deliberately drops it. The verifier's BUILD is `go build`, so project tests are a build
time check on the pinned tree, not a grading input.

## Not verified / guesses

- The interactsh marker-allocation details of the reference renderer are not exercised by any
  hidden test (no interactsh server offline); the reference keeps allocation on authored text.
- `present_in_latest` for L5 is `yes` (read-only look at origin/main 731d4383); the other routes were
  not re-checked against current upstream.
- The trap "type" labels are judgement, not measured.

## Gate (final)

- static: PASSED
- nop: PASSED (0/10 security, 15/15 functional on the pinned+injected tree)
- oracle: PASSED, 3/3 runs at reward 1.0
- patches: PASSED, 11/11 declared outcomes (see build/nuclei-s3/gate_report.json)
- full consolidated run: PASSED

End (UTC): 2026-10-26T00:18:38Z
