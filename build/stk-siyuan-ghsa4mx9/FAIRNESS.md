# Fairness review — stk-siyuan-ghsa4mx9

Concepts per `manifest.stacking`: C1 = [T2 icon, T3 asset, T7 prefixed-script]; C2 = [T4 history/repo-diff]; C3 = [T5 emoji]. 10 security + 9 functional tests.

**Active-content checker (2026-10-24 second repair).** Both support copies flag a `foreignObject`
only when its subtree carries something active — a `script`, an event handler, a script-scheme or
non-raster `data:` reference, or an embedding element (`iframe`/`object`/`embed`). An inert
`foreignObject` is accepted, so a sanitiser that removes the active parts but keeps the wrapper
passes while one that leaves active content fails. Verified in-process with an inert document
(div/span, https link, `data:image/png`) and five active variants.

**Harness (2026-10-24 fairness revision).** The four serve-route cases are driven through
`newGinServer`, the constructor production `Serve()` itself calls, so every middleware `Serve`
installs (concurrency, timing, recovery, CORS, JWT, gzip, sessions) runs in front of the routes
exactly once, as in the real server. The fixture then appends the role setter (the JWT middleware
would otherwise leave the visitor role it derives from the request) and registers the three route
functions. A guard at the handler boundary and a guard installed anywhere in that middleware chain
both reach the same request; `checks/pass-engine.patch` proves the engine-level design scores 1.0.

## 1. Per-test fairness

| test (`file::name`) | asserts | fair because | correct fix fail? | risk |
|---|---|---|---|---|
| `security/zz_stk_sec_icon_test.go::TestSec_DynamicIconDropsEventHandlerAttribute` | icon built from caller text `</text><image onerror=...>` carries no `on*` attribute | "no event-handler attribute"; "Text that a caller supplies ... is content, never markup" | no — escaping the text or sanitising the document both pass | low |
| `...::TestSec_DynamicIconDropsScriptHref` | caller text with `<a href="javascript:...">` loses the reference | "no reference that runs code" | no — local-name href filter or escaping | low |
| `...::TestSec_DynamicIconDropsMarkupDataHref` | `data:text/xml`, `data:application/xml` references removed | "may not ... inline-load another document's active content into the page" (a `data:text/xml` document with an `onload` is another document's active content; neither type is a raster image) | no — raster allowlist or escaping | low |
| `...::TestSec_DynamicIconDropsActiveElements` | iframe/object/embed/foreignObject gone | "may not run script, and it may not embed or inline-load another document's active content into the page" | no — element denylist/allowlist | low |
| `...::TestSec_DynamicIconDropsPrefixedScriptElement` | `svg:script` removed | "no element that runs script"; standard expert knowledge: an SVG-namespaced element written with a prefix is still a script element when parsed as XML | no — local-name match; escaping also passes | medium |
| `...::TestSec_DynamicIconNeutralisesCallerTextWhenSettingEnabled` | with the setting on, caller text `</text><script>…` still yields no executable content (or a 4xx) | "Text that a caller supplies to the icon API is content, never markup: no value of it may become executable content in the returned document" — read without a setting condition; the setting-on exemption covers documents "as stored" only | no — escaping at the icon sink, sanitising the generated document, or a refusal all pass | low |
| `security/zz_stk_sec_serve_test.go::TestSec_EmojiSvgActiveContentNeutralised` | `/emojis/stkpack/evil.svg` carries no active content (reader) | "no SVG document the kernel returns to a client may carry executable content"; served through production `newGinServer` | no — handler guard or engine-chain middleware (`pass-engine`), or a 4xx refusal | low |
| `...::TestSec_HistorySvgActiveContentNeutralised` | `/history/.../snapshot.svg` cleaned (admin) | same general property; production engine chain | no — handler or engine-chain guard | low |
| `...::TestSec_RepoDiffSvgActiveContentNeutralised` | `/repo/diff/.../diff.svg` cleaned (admin) | same general property; production engine chain | no — handler or engine-chain guard | low |
| `...::TestSec_AssetSvgActiveContentNeutralised` | `/assets/evil.svg` cleaned (reader) | same general property; production engine chain | no — handler or engine-chain guard | low |
| `functional/zz_stk_func_icon_test.go::TestFunc_DynamicIconRendersPlainText` | text icon shows `A`, `你`, `A&B`; none becomes markup | "Everything that works today keeps working ... text icons keep displaying their text"; "no value of it may become executable content" (escaping keeps the text) | no — escaping displays the same text | low |
| `...::TestFunc_DynamicIconRendersTemplateOutput` | `.action{.title}` expands and shows the stored title | "Everything that works today keeps working"; "text icons keep displaying their text" (the expanded title is the text displayed) | no | low |
| `...::TestFunc_DynamicIconKeepsTextVisibleWhenSettingEnabled` | setting on: plain text (`A`, `你`, `A&B`) still renders as text | "Everything that works today keeps working ... text icons keep displaying their text"; the setting-on clause governs documents "as stored" and does not make the endpoint refuse or blank a text icon | no — escaping keeps the same text; no security rule forbids it | low |
| `functional/zz_stk_func_serve_test.go::TestFunc_EmojiSvgKeepsNonExecutableContent` | https + xlink-https hrefs, prefixed rect, `data:image/png`, inline style, text survive | "Everything that works today keeps working: a legitimate SVG that carries no executable content keeps its content intact"; "Ordinary navigation links and raster images stay as they are" | no — denylist or local-name allowlist keeps them (see Realism on the prefix) | medium |
| `...::TestFunc_HistorySvgKeepsNonExecutableContent` | same markers via `/history` | same clause | no | medium |
| `...::TestFunc_RepoDiffSvgKeepsNonExecutableContent` | same markers via `/repo/diff` | same clause | no | medium |
| `...::TestFunc_AssetSvgKeepsNonExecutableContent` | same markers via `/assets` | same clause | no | medium |
| `...::TestFunc_NonSvgFilesServedUnchanged` | png/txt/json bodies byte-identical | "Everything that works today keeps working" (files that are not SVG carry no executable content and keep their bytes) | no | low |
| `...::TestFunc_SvgScriptsServedWhenSettingEnabled` | stored SVG with `onload`/script returned verbatim when setting on | "When the SVG-script setting is on, documents are returned exactly as stored" | no | low |

## 2. Leniency (quality, non-blocking)

| property / trap | most plausible WRONG fix | caught? |
|---|---|---|
| P1 all returned SVG clean (T2) | keep `RemoveScriptsInSVG` (script-name only) | yes — 6 icon tests (`miss_sanitizer.patch`) |
| P1 (T3 asset) | fix the icon sink only, leave `serveSVG` on the weak helper | yes — `TestSec_AssetSvgActiveContentNeutralised` (`miss_sanitizer`) |
| P1 (T4) | fix `/assets` + `/emojis`, leave `http.ServeFile` in `/history`, `/repo/diff` | yes — `TestSec_History...`, `TestSec_RepoDiff...` (`miss_serve_history`) |
| P1 (T5) | leave `emojis.Static` | yes — `TestSec_Emoji...` (`miss_emoji`) |
| P1 (T7) | keep `EqualFold(c.Data,"script")` while adding attribute/URL filtering | yes — prefixed-script test + asset test (`upstream_fix` leaves both red) |
| P1 | strip static attributes only; allow SVG animation (`<set attributeName="href" to="javascript:...">`), CSS `url(data:…)`, `<meta>/<link>/<base>` | **no test** |
| P1 | detect SVG only by a case-sensitive `.svg` suffix | **no test** (`.SVG`, extensionless untested) |
| P2 caller text is content | drop text containing `<`/`>` instead of escaping it | **no test** (functional cases are `A`, `你`, `A&B`; the security case accepts removal) |
| P2 caller text is content | serve caller text raw when the setting is on (keep the escape behind the setting gate) | yes — `TestSec_DynamicIconNeutralisesCallerTextWhenSettingEnabled` |
| P2 | sanitise only `type=8` | **no test** (every icon case is type 8) |
| P3 legit preserved | strip every href / data URL | yes — `TestFunc_*KeepsNonExecutableContent` (`ff-strip-links`) |
| P3 | refuse everything | yes — functional 200 + content demands (`ff-refuse-all`) |
| P4 setting on verbatim | sanitise stored documents unconditionally | yes — both stored-document setting-on functional tests |
| P4 inert markup wrapper | flag any `foreignObject` even when its content is inert | corrected 2026-10-24 — the checker now flags a `foreignObject` only when its subtree is active, so an inert wrapper passes |
| fail-closed | crash (500) instead of clean refusal | yes — `stkAssertNeutralised` rejects ≥500 (`crash-as-refusal`) |

Wrong fixes no test catches: text-with-`<` dropped; case-sensitive suffix / extensionless SVG; animation / CSS-url / meta-link active content; `type=8` special-casing; sanitising `/public`, `/widgets`, `/plugins` (deliberately active, see Realism). Catalogue n/a rows stand: no wrong resource, role/direction, write path, normalisation step or authority; `unlisted_route`→`miss_serve_history`, `malformed_identity`→`miss_sanitizer`, `adjacent_api`→`ff-strip-links`.

## 3. Hints (quality, non-blocking)

The current `instruction.md` names no file, function, helper, setting-implementation detail, trap or
variant count. It states the property once over every returned document and gives one published
trigger as an illustration, explicitly framed as "one illustration" of an invariant rather than a
list of cases:

- "For example, a request to `/api/icon/getDynamicIcon?type=8` whose text value contains a script
  URL ..." — the advisory's public entry point; retained as the trigger, not a fix location.
  Accepted: it names the route the report is about, not a file or helper.
- "When the SVG-script setting is on, documents are returned exactly as stored." — states the
  stored-document exemption as a product behaviour, not a code path.

No other sentence points at a route, stage, source, form or alias. Nothing was added by this
repair (the audit forbade editing `instruction.md`).

## 4. Realism

T2/T3 are the published advisory and its far site in real upstream code. T4/T5 are real unmodified handlers both published fixes leave open — realistic by definition, not "beyond the advisory". T7's equality test is the real helper; a prefixed element is ordinary XML/SVG.

Fixture repair (2026-10-24): `stkLegitSVGDocument` now declares `xmlns:svg` for its harmless
`<svg:rect>` marker, so the "legitimate" document is well-formed `image/svg+xml` and a correct fix
that parses the SVG namespace strictly is not failed by the fixture (previously flagged in this
section as a fixture defect). Both published fixes leave `/public/`, `/widgets/` and `/plugins/`
serving deliberately active content; those routes are untested and outside the property. Nothing
looks planted.

The engine constructor (`newGinServer`) added to the pinned tree is a behaviour-preserving extraction of the code `Serve()` already ran: same engine settings, same middleware in the same order, same session store, and `Serve()` calls it unchanged otherwise. It adds no route and no guard, so it neither creates nor removes a vulnerability; it exists so the hidden suite and the real server share one middleware chain.

## Stacking checks

| check | concept | finding | gate-a |
|---|---|---|---|
| S1 coupled | C1 | must-keeps: "Everything that works today keeps working"; the reworded security rule says "Ordinary navigation links and raster images stay as they are", so the kept https/xlink links, `data:image/png` and inline styles are not forbidden. Setting-on verbatim ("documents are returned exactly as stored") sits under the scoped "While the SVG-script setting is off" rule. The setting-on functional case keeps only plain text (`A`, `你`, `A&B`), which no security rule forbids; the caller-text rule is unconditional, and `TestSec_DynamicIconNeutralisesCallerTextWhenSettingEnabled` tests it in that mode. | no |
| S1 coupled | C2 | same fixture/keep clauses; no security rule forbids them | no |
| S1 coupled | C3 | same; the setting-on case holds raw script only while the rule is off | no |
| S2 shape | C1 | refused shapes (`on*`, `javascript:`, `data:text/xml`, `data:application/xml`, iframe/object/embed, active `foreignObject`, `svg:script`) all lie outside the stated legitimate set ("Ordinary navigation links and raster images stay as they are": https href/xlink, `data:image/png`, plain text and non-executable content). An inert `foreignObject` is no longer refused by the checker, so it lies inside the legitimate set; the setting-on security case refuses caller-supplied markup, which the text rule declares to be content, never markup. | no |
| S2 shape | C2 | same active/legit fixture pair | no |
| S2 shape | C3 | same | no |
| S3 fixtures/harness | C1 | setting defaults off, real workspace doc, real handler; asset via real `serveAssets`. The serve routes are built through production's `newGinServer`, so a guard in that middleware chain and a per-sink handler guard both pass (`pass-engine` vs oracle). The icon case drives `getDynamicIcon` directly, so a guard installed *only* as engine middleware is not exercised there; the primary per-sink mechanism passes. | no |
| S3 fixtures/harness | C2 | real `serveAssets` registers `/history`; `HistoryDir`/`TempDir` legit; admin role as the route expects; production engine chain installed | no |
| S3 fixtures/harness | C3 | real `serveEmojis`; pack dir legit; production engine chain installed | no |
| S4 independence | C1 | icon/asset tests pass with only C1 fixed; no C2/C3 dependency. `miss_serve_history` and `miss_emoji` carry the C1 fix (including the caller-text escape), so each leaves only its own concept's tests red; `miss_sanitizer` leaves all C1 tests red. | no |
| S4 independence | C2 | history/repo-diff tests pass with only C2 fixed | no |
| S4 independence | C3 | emoji tests pass with only C3 fixed; H3c masking N/A (pattern H3a) | no |
| S5 history | C1 | `upstream_first_fix` keeps `svg:script` and `data:text/xml`, violating "it may not run script" / "it may not embed or inline-load another document's active content into the page"; it also leaves caller text raw in setting-on mode, violating "Text ... is content, never markup" read literally | no |
| S5 history | C2 | A leaves both handlers on `http.ServeFile`, violating "No stored ... document is exempt" | no |
| S5 history | C3 | A leaves `emojis.Static`, violating the same property | no |
| S6 contracts | C1 | tests use existing `getDynamicIcon`, `serveAssets` and the repo's own `newGinServer`; `model.RoleContextKey` is the existing authentication key. No guessed names. | no |
| S6 contracts | C2 | `serveAssets` must keep registering `/history`; existing structure, but relocating it would evade the harness | no |
| S6 contracts | C3 | `serveEmojis` must keep its name/signature (existing) | no |
| S7 decisive | all | no `trial_summary.md` and the audit's postmortem path is no longer on disk. The audit of the 2026-10-24 v4 DeepSeek run 1 attributes the failure to a **test fault**: `TestFunc_DynamicIconServesScriptsWhenSettingEnabled` demanded raw caller markup with the setting on, contradicting "Text ... is content, never markup". That test is now a keep-working case (plain text only) and the caller-text rule is tested in the security group. No single remaining test decides a run: the earlier deepseek run (0.6667) failed six C1 security tests, and `pass-engine`/oracle now cover both the sink and engine layers for the serve routes. | n/a |

## Verdict

Gate a: every test is covered by the one general property ("no SVG document the kernel returns to a client may carry executable content: it may not run script, and it may not embed or inline-load another document's active content into the page"), the unconditional caller-text rule ("Text that a caller supplies to the icon API is content, never markup"), or a stated must-keep clause ("Everything that works today keeps working"; "When the SVG-script setting is on, documents are returned exactly as stored"). The primary mechanism — extend the shared sanitizer to local-name element/attribute/URL filtering, escape caller text at the icon generator in every mode, and wire each SVG-producing site behind the existing `AllowSVGScript` gate — passes all 19 (oracle, `pass-alt`, `pass-hardening` at 1.0). A correct guard placed instead in the engine middleware chain passes every serve-route case (`pass-engine` at 1.0), because the fixture now runs production's chain. No correct-fix-fails mechanism found; the 2026-10-24 test fault (setting-on caller markup) is removed.

Required: generalize (step 3a): none in this audit. The five items listed by the previous review (R1–R5) were applied in the earlier instruction revision; the current `instruction.md` contains no sentence that names a file, function, mechanism, trap, variant list or count, and this repair did not edit it.

Quality to tighten: extend `stkActiveSVGContent` to animation attributes, CSS `url(...)`, `<meta>/<link>/<base>`; add `.SVG`/extensionless and leading-whitespace-scheme cases; add a plain-text-containing-`<` functional case; add a non-type-8 generated badge case; settle the `/public`, `/widgets`, `/plugins` scope. Fixed in this repair: the `xmlns:svg` declaration on the legitimate fixture, and the inert-`foreignObject` checker.

Human review: confirm the residual that an engine-middleware-only guard is not exercised by the icon cases (it is exercised by the four serve cases; the reference, `pass-engine` and the other alternatives all pass all ten security tests). The setting-on caller-text contradiction and the undeclared-prefix must-keep flagged previously are resolved.

Fairfix note (2026-10-24, audit `AUDIT-FIX-20261024.md`): the serve fixture now builds its engine through the product's own `newGinServer` constructor, so a guard at the engine's middleware chokepoint runs exactly as in `Serve()`. `instruction.md` and the reference fix are unchanged, as the audit required; `checks/pass-engine.patch` (expect `pass`) proves the engine-level design scores 1.0.

Fairfix note 2 (2026-10-24, audit `AUDIT-FIX-20261024.md`, instruction rewording): the Required property's second clause previously read "embed another document, or cause a document that is not an image to be loaded", which read literally also forbade the ordinary navigation links the functional suite keeps. It now reads "it may not run script, and it may not embed or inline-load another document's active content into the page. Ordinary navigation links and raster images stay as they are." No attribute, scheme, element or route is named. This removes the S1 contradiction; only `instruction.md` changed, and the launcher copies it to `stk-siyuan-ghsa4mx9-control` (rule 13). Every security test still fails on the pinned tree and the oracle still scores 1.0.

Fairfix note 3 (2026-10-24 second repair, audit `AUDIT-FIX-20261024.md`): (a) the setting-on functional icon test no longer demands raw caller markup — it now checks plain text still renders with the setting on, and a new security case enforces the unconditional caller-text rule in that mode; the reference and the three pass patches escape caller text in `generateTypeEightSVG` in every mode. The escape assertion sits in the security group because a functional test must pass on the pinned tree (gate nop). (b) The active-content checker flags a `foreignObject` only when its subtree is active, so an inert wrapper passes; both support copies were changed and verified against inert and active documents. (c) `stkLegitSVGDocument` declares `xmlns:svg`. `instruction.md` was not changed. Re-verified in-process: nop = 10 security fail / 9 functional pass; oracle and `pass-alt`, `pass-hardening`, `pass-engine` = 19/19; `miss_serve_history` leaves only history/repo-diff red, `miss_emoji` only emoji, `miss_sanitizer` all six icon/asset C1 tests red, `ff-*` still fail functional, `upstream_*` still fail security.

GATE_A: READY
NEEDS_HUMAN_REVIEW: YES
