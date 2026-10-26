# atlas-ds — build notes

Start: 2026-10-24T02:44Z.
End: 2026-10-24T04:11Z.

Task: apache/atlas, advisory GHSA-V73P-F52R-FMMR / CVE-2025-62198 (XSS, CWE-80/79).
Pinned tree e67cc199e61afc92f242cccd05e97a61e0791bd2; published fix
800f979307d6ea0f0b6563ec890f6b728022e497. Pattern A+B, track injected.

## Mechanism (one line)
User-authored metadata reaches several DOM-injection sinks in two independent front ends; the
published fix sanitises the sites it names, while the same values are rendered unsanitised by a
type-flagged branch in the legacy UI and by two richer render branches added to the React UI here.

## Levers (one line each)
- T1 (main, B, how-type): the legacy table helper escapes values only when an attribute-type flag is
  absent; the search-result caller sets the flag for business-metadata string attributes, so scalar
  and list values flagged as editor content reach the cell as HTML. Fix must sanitise rich text, not
  escape it, or the formatting the product renders breaks. Dismiss: legacy second UI; the flag reads
  as an intentional rich-text opt-in. `CommonViewFunction.js:128-131,196-198,318-330`,
  caller `SearchResultLayoutView.js:720-731,1030`.
- T2 (A, where-type): the account name the server reports is written into the page chrome with
  `.html(...)`. Dismiss: an account name is trusted identity data, not user content; legacy UI.
  `Header.js:137` (published fix site).
- T3 (injected, shape): list-valued business metadata takes a different branch from the reported
  scalar attribute and joins its items into HTML. Dismiss: a list looks like plain data.
  `BMAttributes.tsx:303-317` (injected).
- T4 (injected, ordering/refactor): the formatted-description caller passes the raw description to
  the shared truncated-text renderer, leaving sanitising to the shared component alone. Dismiss: the
  description "was sanitised by its caller"; the shared renderer looks like a pure presenter.
  `DetailPageAttributes.tsx:259-265` (injected) + `ShowMoreText.tsx:44-51`.
- Reported landing site (not a lever, covered): business-metadata string value rendered raw by
  `HtmlRenderer.tsx:18-25`; `security/react_bm_string.test.tsx`, `sf-miss-hidl.patch`.

## Candidate inventory (every site/route found) and why the picks beat the rest
React dashboard:
1. `HtmlRenderer` raw string (reported; built).
2. `ShowMoreText` isHtml raw (published fix; upstream callers sanitised at the pinned commit, so only
   reachable after T4 was added; built as T4's sink).
3. `ExtractObject` primitive branch (published fix's `escapeHtml`; not treated as a lever: through the
   product, `getValues` sends arrays to `GetArrayValue` and objects to `JSONPrettyPrint`, so no
   attacker-controlled primitive reaches this branch — verified by rendering `AttributeProperties`
   with an array attribute and by grepping every caller; the published change is defence in depth).
4. `BusinessMetadataTab` description cells (sanitised; truncate-after-sanitise is not exploitable).
5. `sanitizeHtmlContent` non-string coercion (robustness/DoS, not markup injection).
6. `sanitizeHtmlContent` `allowedSchemesByTag` array (sanitize-html falls back to its default scheme
   set, which already blocks `javascript:`; hardening, not exploitable).
7. `JSONPrettyPrint` (escapes `<`, `>`, `&` before wrapping spans; no parser differential found).
8. React lineage d3-tip tooltip (`views/Lineage/atlas-lineage/src/index.js:537-569`): real and
   stored in the pinned tree, but current upstream now escapes it and the harness would need
   dagre-d3 rendering in jsdom; not built (documented as a candidate, not relied on).
9. `GetArrayValue`, `FilterQuery`, `AttributeTable`, `UserDefinedProperties`: React text, safe.
Legacy:
10. `propertyTable`/`getValue` type-flagged rich text (T1; built).
11. `fetchInputOutputValue` (published fix site): same mechanism and same fix as T1 through the same
    `getValue` closure; not tested separately ("more routes of one concept").
12. `fetchInputOutputValue` soft-reference error branch raw id (GUID, error branch; dismissed).
13. `generateQueryOfFilter` condition concatenations (published fix): the condition is derived to
    AND/OR by `extractUrl`, not attacker text; not exploitable at the pinned commit; not built.
14. Header account name (T2; built).
15. `tagForTable` classification names / `TagDetailTableLayoutView` option tags / BM admin table names
    (`BusinessMetadataTableLayoutView.js:305`) / `BusinessMetadataDetailLayoutView` title: real raw
    sinks, but the values are admin-created type/classification names; not regular user-authored
    content; not built.
16. legacy `external_lib/atlas-lineage` tooltip (same as 8, served from the built bundle; current
    upstream escapes it; not built).
17. Legacy glossary long description/title (sanitised/text; safe).

Injected siblings considered:
- S-A list-valued business metadata rendered as HTML (picked T3): a shape the scalar example misses,
  a different branch in a different component, plausible for rich-text list values.
- S-B formatted description passes the raw value to the shared renderer (picked T4): an
  ordering/refactor lever that makes the published fix's own shared-component change necessary; the
  caller is outside every published hunk.
- S-C `GetArrayValue` properties branch raw join (rejected: same file/near the published
  `ExtractObject` change, caught by the same grep/audit; a pure helper with no coupled formatting).
- S-D `UserDefinedProperties` raw value (rejected: same Properties tab, trivially visible, no
  plausible reason a maintainer would render custom attribute values as HTML).
- S-E `JSONPrettyPrint` key/quote parser differential (rejected: could not construct a plausible
  encoding bypass; the pre-escape chain escapes `<` before the span wrapping).
- S-F legacy filter summary saved-search name (rejected: no saved-search concept exists in the legacy
  UI, so the branch would look artificial; also inside the function the published fix touches).
- S-G legacy BM admin description raw (rejected: repeats T4's description mechanism, needs more
  legacy view scaffolding, and the value is admin-authored).
- S-H legacy detail page `propertyTable` with the editor flag (rejected: same mechanism as T1 and
  over-broad for all attributes; "more routes of one concept").
Picked: S-A and S-B — different mechanisms (list-shape branch, shared-renderer refactor), reachable
through the existing React entry points, plausible, and covered by the one general property.

## Verified
- Baseline (pinned + `environment/injection.patch`), in-process: 6/6 security tests fail, 7/7
  functional tests pass. Oracle: 6/6 security and 7/7 functional pass.
- The six security routes drive the real product paths: `PropertiesTab` (business-metadata string and
  list values), `DetailPageAttribute` (formatted description through `ShowMoreText`), the legacy
  `CommonViewFunction.propertyTable` with the options the search-result column formatter builds
  (scalar and list), and the legacy `Header.onRender` with the session response the app stores.
- The legacy suites load the project's real `Utils.js`, `Enums.js`, `CommonViewFunction.js` and
  `Header.js` AMD modules in jsdom, with real underscore/jquery/moment/DOMPurify.
- Upstream master (read-only) now sanitises the T1 path
  (`CommonViewFunction.js:132-134` on master), which confirms the route and registers
  `present_in_latest=no`; master also escapes the two lineage tooltips, so those candidates are
  fixed upstream and were not built.
- Check patches validated locally against the same suites: each `security_fail` leaves functional
  green, the `functional_fail` patch breaks the rich-text functional tests, and both pass patches
  score 1.0.
- Docker gate (all four stages, run one at a time with `DOCKER_BUILDKIT=1`; compose's classic
  builder deadlocked twice under the shared VM's build concurrency, BuildKit ran cleanly):
  - static: PASS.
  - nop: PASS - 6/6 security tests fail on the pinned+injected image and 7/7 functional tests pass
    (reward 0.0), in the separate offline verifier with the pristine pinned dependency tree.
  - oracle: PASS - 3/3 runs reward 1.0 with identical results.
  - patches: PASS - all 8 declared checks matched: five `security_fail` patches each leave exactly
    their lever's security test(s) failing with functional green (rewards 0.83/0.67); the
    over-broad `functional_fail` patch breaks the three rich-text functional tests (security all
    green); the hardening and alternative `pass` patches score 1.0.

## Could not verify
- Whether a non-admin user can choose the account name in every Atlas deployment (it depends on the
  user store). The instruction names it as a protected value and the published fix treats it as XSS.
- The lineage tooltip routes (8/16): not built; their harness would need dagre-d3 in jsdom.
- `present_in_latest` for the other O8 routes beyond the files checked (only CommonViewFunction,
  Header, HtmlRenderer and the two lineage files were inspected on master).

## Fairness notes
- The main lever lives in the legacy UI. The instruction states the property over "any view, table,
  panel, tooltip or summary" and the repository plainly contains both front ends; a solver that
  assumes only the React dashboard is in scope misses it. That is the intended judgement failure.
- The account-name route depends on a value an administrator may provision; the instruction names it
  explicitly as protected, so the scope is findable from the report.
- Tests drive exported components/functions with the same props/options the product passes. A fix
  placed at a higher caller only (for example sanitising an API response before the component) would
  not be exercised, but the product renders these values in several independent callers, so the
  shared-renderer layer the reference fix chooses is the layer the upstream fix also chose.
- Functional tests keep the supported rich-text vocabulary, links, plain text, list joining and
  numbers working, so escaping everything fails.
