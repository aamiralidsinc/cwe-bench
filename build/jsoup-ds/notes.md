# jsoup-ds build notes

- Start (UTC): 2026-10-24T04:57:43Z
- End (UTC): 2026-10-24T06:28:00Z

Repo: jhy/jsoup @ a682fd5bc8acdf841e5f858e8a19e3d2c92c4df8 (parent of the published fix
92f1aca552548b484bc7d4b94c51e48b8e6eca70). Pattern A, track injected. Advisory GHSA-PMHH-3W7G-XQP8 /
CVE-2026-71497 (CWE-79 sanitizer bypass via a parser differential on element identity).

## The security property (stated once, general)

Sanitization must be sound: the result may contain only elements, attributes, and element text that
the configured safelist permits. No markup a submitter supplies may survive sanitization as an
element, an attribute, or unescaped element content unless the safelist allows that element and
attribute — whatever the tag is called, however it is written, and wherever it appears in the
document. Content that is not allowed is dropped and never passed through in a form a browser would
re-interpret as markup.

The report states this once. No sentence in instruction.md names a route, a sibling, a file, a
function, a tag other than the example's `iframe`, or the mechanism.

## Levers (one line each)

- **T1 (main, HOW-type, published-fix site).** The token producers record a normal name with
  `trim` while the tag registry also trims a supplied tag name, so a start tag whose written name
  has a trailing control character resolves to an allowed opaque tag while raw-text end detection
  keeps the untrimmed name; the swallowed markup is copied verbatim. Fix needs both the producer
  (`Token`) and the registry (`TagSet`), and must keep public-API trimming. Reason to dismiss: the
  registry trim is documented public-API normalisation and the pinned project test asserts it; the
  tempting single-side fix or a sanitizer-side escape either leaves the bypass or breaks allowed
  content.
- **T2 (injected sibling S1, HOW-type).** `HtmlTreeBuilderState`'s body start-tag default branch
  rewrites the start token's name with the parse settings' normaliser before the opaque-text
  decision and the tag lookup; it re-opens every ordinary body route after a producer+registry fix.
  Reason to dismiss: one ordinary-looking line in the huge state machine; after fixing the token
  producer a solver treats recorded names as authoritative.
- **T3 (injected sibling S2, HOW-type).** The noscript-island path rewrites the start token's name
  the same way before the text-state decision and insertion; the sanitizer drops the unsupported
  noscript element but still copies its allowed children out. Reason to dismiss: niche recent code
  and Safelist refuses noscript outright, so the route looks irrelevant.

## Coupled must-keep-working behaviour

- Allowed opaque content round-trips verbatim (`<iframe>content is <data></iframe>` and a permitted
  `<style>` body stay byte-identical).
- Ordinary cleaning, URL-protocol filtering, `isValid`, preserve-case cleaning, custom Data/RcData
  tags and mixed-case RCDATA end tags are unchanged.
- Public tag / tag-set lookup APIs still trim and case-normalise user-supplied names.
- A dropped noscript element's allowed fallback children are still kept.

## Full sibling-site candidate list (searched, then picked)

1. `HtmlTreeBuilder.createElementFor` (recompute the normal name at the element factory) — rejected:
   after the producer fix the opaque-text state transition is decided earlier from the token's
   normal name, so a factory-only re-trim creates a Data-tagged element whose content was never
   treated as raw text. Built and probed: no bypass survives (main path stays safe).
2. `TreeBuilder.tagFor(Token.Tag)` (recompute centrally) — rejected: most call sites only ask for a
   text state; element creation has its own path, so a single site gives no bypass. Probed with a
   token-only fix: no independent bypass.
3. Foreign-content custom-data-tag branch (`HtmlTreeBuilderState` ~1783, screener O8b #1) —
   rejected: only `script` is a Data tag in the SVG namespace, and a safelist that permits script is
   not a meaningful sanitizer configuration; the foreign element's tag is resolved separately from
   the lookup, so it stays generic.
4. `XmlTreeBuilder` start-tag lookup via `settings.normalizeTag` (screener O8b #2) — rejected: the
   XML tree builder uses an empty tag set, so no element can be an opaque/Data tag; `Cleaner` over an
   XML document has no raw sink.
5. `HtmlTreeBuilder.insertNoscriptStartTag` — **picked S2.** Mutates the token after emit, so it
   changes both the text-state decision and the element's tag; real bypass verified.
6. `HtmlTreeBuilderState.inBodyStartTag` default branch — **picked S1.** The branch that resolves
   custom/opaque start tags; mutating the token there changes both decisions; behaviour-preserving
   for ordinary names; real bypass verified.
7. `HtmlTreeBuilderState.InTable` start-tag case — rejected: a disguised name does not reach the
   head-processing branch, so it needs its own normalisation at the top of the state; that duplicates
   S1's mechanism in a harder-to-reach context and adds no new reason to dismiss.
8. `Cleaner` DataNode gate / `Safelist.isSafeTag` normalisation — rejected: once the parser is
   correct there is no DataNode under a disguised name, so a sanitizer-side trim cannot create a
   bypass; it only widens matching for already-safe output.
9. Serializer tag-name normalisation (`Element` output / `Tag`) — rejected: the disguised element is
   dropped by the sanitizer before serialization, so output normalisation cannot reintroduce it.
10. `Token.nameAttr` / `TreeBuilder.processStartTag(String,Attributes)` — rejected: no production
    caller with an attacker-controlled name at this pin; unreachable from `Jsoup.clean`.
11. `XmlTreeBuilder.popStackToClose` trimmed end names — real upstream asymmetry, rejected: a
    structural/correctness mismatch, not a sanitizer sink; XML has no Data tags.
12. Table/template-context normalisation variants — rejected: same mechanism as S1 and reached only
    through S1's dispatch; no separate lever.

Picks T2/S1 and T3/S2 beat the others because they are the only sites that are reachable from
`Jsoup.clean` with ordinary safelists, change both the opaque-text decision and the element's tag
identity, are behaviour-preserving for every legitimate name (so they survive the natural fix), and
carry two different reasons to dismiss (body dispatcher vs. forbidden-noscript island).

## What was verified

- Pinned tree reproduces the bypass through `Jsoup.clean` and `Cleaner.clean(Document)`: the
  sanitized output, re-parsed, contains a live `<svg onload=...>` element the safelist disallows.
- Every security test fails on the pinned+injected tree and passes on the oracle; every functional
  test passes on both.
- Local sweep for Pattern B: 8 opaque/RCDATA tag names x 26 control characters x 9 shapes x 11
  contexts plus document/preserve-case entry points found no residual bypass on the published fix
  alone, so there is no real uncovered route; residual routes are the injected siblings.
- The injected siblings are behaviour-preserving: the project's parser/safety tests (705 tests) pass
  at the pinned+injected tree; on the oracle only `HtmlParserTest.trimNormalizeElementNamesInBuilder`
  fails, and that test asserts the pre-fix normalisation (the published fix replaces it), so it is
  excluded from the verifier's project-test set.
- Gate stages, run one at a time on the task (private dockerd; the shared daemon was wedged):
  `static` PASS; `nop` PASS (14/14 security failing, 120/120 functional passing);
  `oracle` PASS (3 runs, reward 1.0, identical results);
  `patches` PASS - every check behaved as declared: sf-miss-base (13 security failing, functional
  all pass), sf-miss-s1 (11 security failing), sf-miss-s2 (the 3 noscript tests failing),
  ff-overbroad (functional failing: allowed opaque content + CleanerTest), ff-public-trim
  (functional failing: public tag lookup), pass-hardening 1.0, pass-alt 1.0.
- Offline build verified in both images (compile + dependency classpath + project tests: 108 tests).
- Nop = 14/14 security fail, 120/120 functional pass, reward 0; oracle = 1.0.

## What could not be verified

- Target-model behaviour: not run, per the build instructions (no trials).
- `present_in_latest`: the published fix is the direct child of the pinned commit and the tree is
  pinned there; a later upstream state was not inspected.
- Real-browser re-parse: the tests use the product's own parser to re-parse the sanitized output, as
  the sanitizer's own contract is defined against that parser.

## Out of scope (one line each)

- `Tag.name(String)` and the public `Tag` constructors still trim via `ParseSettings.normalName`;
  those are public-API inputs, not parser input, and were left alone.
- `XmlTreeBuilder.popStackToClose` trims end-tag names while start names are no longer trimmed after
  the fix: a structural/correctness mismatch, not pursued.
