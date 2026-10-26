# Fairness review — stk-nuclei-ghsajpvm (fairfix 2026-10-24, instruction rewording)

Source of the required changes: `build/stk-nuclei-ghsajpvm/AUDIT-FIX-20261024.md`. The audit found one
contradiction between the instruction and `TestFuzzTargetMarkerValueStaysLiteral`: the refusal
permission let the engine decline a request because it still contained target-supplied marker-looking
bytes, while that functional test requires the target's own value to be sent byte for byte. The tests
and the reference are correct; the repair is instruction-only.

Applied: the refusal bullet now reads "the engine may decline to send a request whose
**template-authored** syntax is still unresolved". Target-supplied bytes are no longer a reason to
decline, so a correct fix can satisfy both the security property and the byte-fidelity test. No
identifier, file, function, route, marker form or count was added, and no trap is named. The
listing check's four GENERAL (hidden) classifications are unaffected by this wording.

## Tests and their covering instruction

| test | asserts | covering sentence | correct fix could fail? | risk |
|---|---|---|---|---|
| `security/security_test.go::TestResponseDerivedExpressionIsNotRendered` | an extracted response value carrying brace marker text is never delivered to the target; if the chained request is sent its query value is exactly the extracted bytes | "Anything that entered from the scan target … must never be rendered, substituted or evaluated as template source"; "any request that is sent must carry its bytes unchanged" (refusal or literal delivery both pass: `requireNotDelivered`/`requireLiteralWhenSent`) | no | low |
| `…::TestResponseDerivedLegacyMarkerIsNotRendered` | the same for the legacy marker form | same property ("rendered, substituted or evaluated") | no | low |
| `…::TestFuzzPayloadDoesNotRenderResponseData` | a fuzz payload fed by an internal extractor carrying brace marker text is not rendered; delivered literally if sent | same property; a fuzz payload is a way the template inserts target data | no | low |
| `…::TestFuzzPayloadDoesNotRenderLegacyMarkerData` | the same for the legacy marker form | same property ("substituted") | no | low |
| `…::TestShadowedVariableValueIsNotRendered` | a target-derived value that shadows a declared template variable is not rendered as template source | "anything taken or derived from them … must never be rendered, substituted or evaluated as template source" | no | low |
| `functional/functional_test.go::TestAuthoredEnvironmentPlaceholdersResolve/{braces,legacy}` | authored environment references in both marker forms resolve (`-ev`) | "Template-authored text may be rendered."; "Everything that works today keeps working." | no | low |
| `…::TestFuzzTargetValueIsSentVerbatim/{prefix,postfix,infix}` | the target's own value, combined by an authored fuzz rule, is delivered byte for byte | "When the template inserts such a value into a request in literal form, any request that is sent must carry its bytes unchanged." | no | low |
| `…::TestFuzzTargetMarkerValueStaysLiteral` | the target's own marker-looking value stays literal (`-X-§…§`) | same byte-fidelity sentence; the refusal clause is now scoped to **template-authored** syntax, so it does not permit declining this request | no — this is the repaired contradiction | low |
| `…::TestExtractedValueDeliveredLiterally` | an extracted plain value is chained into a later request verbatim | same byte-fidelity sentence | no | low |
| `…::TestTemplateDeclaredVariablesResolve` | an authored declared variable resolves | "Template-authored text may be rendered." | no | low |
| `…::TestTemplateAuthoredHelperExpressionRenders` | an authored helper expression renders | "Template-authored text may be rendered." | no | low |
| `…::TestFuzzNestedAuthoredExpressionRenders` | an authored nested expression in a fuzz payload renders | "Template-authored text may be rendered." | no | low |
| `…::TestScanMatchesAndExitsCleanly` | an ordinary scan still reports its match and exits 0 | "Everything that works today keeps working exactly as it does today." | no | low |

## Leniency (QUALITY)

| wrong fix | caught by |
|---|---|
| refuse every request carrying marker-looking bytes | `checks/ff-refuse-all.patch` → `functional_fail` (`TestFuzzTargetMarkerValueStaysLiteral`); the instruction no longer permits it |
| fix only the shared evaluator / published first commit | `checks/sf-no-echo.patch`, `checks/upstream_first_fix.patch` → `security_fail` |
| fix only the fuzz path | `checks/sf-no-fuzz.patch` → `security_fail` |
| fix only the brace form, not the legacy form | `checks/sf-no-marker.patch`, `checks/upstream_fix.patch` → `security_fail` |
| fix only the fuzz path plus the evaluator, missing the legacy renderer | `checks/upstream_fix.patch` → `security_fail` |
| fix only the declared-variable merge | `checks/sf-no-shadow.patch` → `security_fail` |
| a different correct design | `checks/pass-alt.patch`, `checks/pass-hardening.patch` → `pass` (reward 1.0) |

No wrong-fix class in `manifest.wrong_fix_catalogue` is left uncatched.

## Hints (QUALITY)

No sentence names a file, function, mechanism, trap, variant list or flaw count. The trigger is
described as one instance and explicitly called not the full set. The refusal clause now states only
the source boundary (template-authored vs target-entered), which is already the subject of the
security property.

**Required: generalize** — the audit contains no such item, and no sentence describes where a
sibling, far site or uncovered route lives. None.

## Realism (QUALITY)

T1 is the advisory's own route; T3, T7, T5 and S1 are real, unmodified upstream routes that the
published fixes left open, so leaving one open is the solver's judgement, not an out-of-scope
finding. Every test drives the built CLI against a local target; nothing is planted.

## Stacking checks

Concepts (`manifest.stacking`): **C1 = {T1, T3}** (DAST/fuzz payload evaluation), **C2 = {T7}**
(shared evaluator ordering), **C3 = {T5}** (legacy marker substitution in the shared renderer),
**C4 = {S1}** (declared-variable merge). Pattern H3b; no masking (H3c).

### S1 — Coupled traps

| functional value | concept | covering clause | security rule that forbids it |
|---|---|---|---|
| `TestAuthoredEnvironmentPlaceholdersResolve` (both forms) | C3 | "Template-authored text may be rendered."; keep-working | none: the value is authored, not target-entered |
| `TestFuzzTargetValueIsSentVerbatim` (three modes) | C1 | "…any request that is sent must carry its bytes unchanged."; keep-working | none |
| `TestFuzzTargetMarkerValueStaysLiteral` | C1/C3 | same byte-fidelity sentence | none after the fix: the refusal permission is limited to template-authored syntax, so target-supplied bytes never justify declining |
| `TestFuzzNestedAuthoredExpressionRenders` | C1/C2 | "Template-authored text may be rendered." | none: the payload text is authored |
| `TestExtractedValueDeliveredLiterally` | C2/C4 | byte-fidelity sentence; keep-working | none |
| `TestTemplateDeclaredVariablesResolve` | C2/C4 | "Template-authored text may be rendered."; keep-working | none |
| `TestTemplateAuthoredHelperExpressionRenders` | C2 | "Template-authored text may be rendered." | none |
| `TestScanMatchesAndExitsCleanly` | — | keep-working | none |

Result: no contradiction in any concept. The one contradiction in the pre-fix wording (S1 on
`TestFuzzTargetMarkerValueStaysLiteral`) is removed by narrowing the rule over its protected outcome,
not by adding a clause that names the value.

### S2 — Shape traps

| concept | refused shape | outside the legitimate set because |
|---|---|---|
| C1 | a fuzz payload value carrying target marker text (both forms) | it entered from the target; the legitimate set is authored payload text, including authored nested helpers (`TestFuzzNestedAuthoredExpressionRenders`) |
| C2 | a chained extracted value carrying marker text (both forms) | it is taken from a response; the legitimate set is authored placeholders/expressions and literal delivery of any extracted value |
| C3 | the legacy form inside target data | it is target-entered; authored use of the same form remains legitimate (`TestAuthoredEnvironmentPlaceholdersResolve/legacy`) |
| C4 | a caller-supplied value that shadows a declared variable, used as template source | it did not come from the template; the legitimate set is declared template text |

### S3 — Fixtures and harness

Every fixture is a normal scan with the environment-variable option enabled, which the instruction
calls an operator opt-in, against a local target. Every concept is driven through the built scanner
CLI (`nuclei -t … -u …`, plus `-dast` for the fuzz route) with an in-process target; a guard at any
valid layer (payload pipeline, evaluator, renderer, variable merge) passes. Pass.

### S4 — Concept independence

| concept | security test(s) attributed | pinned | its miss check (reference minus this concept) | functional green |
|---|---|---|---|---|
| C1 {T1,T3} | `TestFuzzPayloadDoesNotRenderResponseData`, `…LegacyMarkerData` | fail | `sf-no-fuzz.patch` flips both | yes |
| C2 {T7} | `TestResponseDerivedExpressionIsNotRendered` | fail | `sf-no-echo.patch` flips it; because the shared evaluator sits on every rendering route, removing it also exposes the fuzz response-data route (C1) and the shadow route (C4) | yes |
| C3 {T5} | `TestResponseDerivedLegacyMarkerIsNotRendered`, `…FuzzPayloadDoesNotRenderLegacyMarkerData` | fail | `sf-no-marker.patch` flips both | yes |
| C4 {S1} | `TestShadowedVariableValueIsNotRendered` | fail | `sf-no-shadow.patch` flips it | yes |

Every concept's edit site is necessary: the pinned tree fails all five security tests, and removing
any one concept from the reference (its miss check) leaves at least one security test failing while
every functional test passes. No concept is masked — no test attributed to a concept passes while
that concept's own fix is missing. The matrix does show a dependency: the shared evaluator ordering
(C2) is a prerequisite on the chaining, fuzz and shadow routes, so `sf-no-echo` also exposes those
two other concepts' routes. That is a shared prerequisite, not masking, and a correct full fix passes
all five (as do the two independent designs, `pass-alt` and `pass-hardening`). Pattern H3b; no H3c
concept is being shielded by another. `checks/upstream_first_fix.patch` (1/5 security) shows the
concepts do not collapse into a single edit.

### S5 — History

H3b. `checks/upstream_first_fix.patch` is the earlier advisory's first commit (collect expressions
before substitution). It still substitutes the legacy marker form in target data, still renders the
fuzz path and still renders a shadowing caller value, so it violates the property read literally
("must never be rendered, substituted or evaluated as template source") — four security tests fail.
The combined published equivalents (`checks/upstream_fix.patch`) still leave the legacy form open —
two security tests fail. Both are wired `security_fail` and functional-green. Pass.

### S6 — Contracts

Every test drives the product CLI with template files; no internal field, function or header name is
required. The protected object class is stated in product terms: "anything that entered from the
scan target — the target's own request data, its responses, and anything taken or derived from
them". No fail-open authority or fallback is involved. Pass.

### S7 — Decisive tests

No `build/stk-nuclei-ghsajpvm/trial_summary.md` exists (model trials are on hold), so S7 does not
fire. The audit itself names `TestFuzzTargetMarkerValueStaysLiteral` as the single deciding test for
the over-broad refusal fix (`ff-refuse-all`). Re-checked first against S1–S6: it holds the target's
own value next to an enabled environment option, the fixed refusal clause no longer forbids sending
it, it drives the real CLI, and the expected bytes are computed in the test. It now passes a correct
fix and still fails the over-broad one.

## Verdict

The pinned tree fails all five security tests; the reference passes all five security and all
thirteen functional tests. Every functional value is covered by the general authored-text and
keep-working sentences, and after the scoped refusal wording no security rule read literally
forbids any of them. Gate a is clear.

GATE_A: READY
NEEDS_HUMAN_REVIEW: NO
