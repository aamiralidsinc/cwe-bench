# Fairness review — stk-siyuan-ghsa4mx9-control

Control of the stacked H3a task: one concept, the advisory's own icon route (T2). 6 security +
5 functional tests, all through the real registered `getDynamicIcon` handler.

**Repair (2026-10-25, `AUDIT-FIX-20261025.md`).** The setting-on functional case no longer
demands raw caller markup. It now checks that a text icon still displays its text with the setting
on; the unconditional caller-text rule is enforced by a new security case in that same mode. The
reference (and the security-fail check) now escape caller text in the icon generator in every
mode. The active-content checker flags a `foreignObject` only when its subtree is active, so an
inert wrapper passes. `instruction.md` was not changed (the audit required that).

## 1. Per-test fairness

| test (`file::name`) | asserts | fair because | correct fix fail? | risk |
|---|---|---|---|---|
| `security/zz_stk_sec_icon_test.go::TestSec_DynamicIconDropsEventHandlerAttribute` | caller text with `<image onerror=...>` yields no `on*` attribute | "Text a caller supplies ... is content, never markup"; "may not run script" | no — escaping the text or sanitising the document passes | low |
| `...::TestSec_DynamicIconDropsScriptHref` | `javascript:` link from caller text is gone | same two sentences | no — escaping or a URL filter passes | low |
| `...::TestSec_DynamicIconDropsMarkupDataHref` | markup-bearing `data:` links from caller text are gone | caller text is content, never markup; a markup document is not a raster image | no — escaping passes; the primary mechanism is the text sink | low |
| `...::TestSec_DynamicIconDropsActiveElements` | iframe/object/embed and an active `foreignObject` gone | "may not embed or inline-load another document's active content" | no — escaping or a local-name denylist passes | low |
| `...::TestSec_DynamicIconDropsPrefixedScriptElement` | `svg:script` gone | "may not run script"; an XML-prefixed script is still a script | no — escaping or local-name matching passes | low |
| `...::TestSec_DynamicIconNeutralisesCallerTextWhenSettingEnabled` | setting on: caller text `</text><script>…` still yields no executable content (or a 4xx) | caller-text rule is unconditional; the setting-on clause covers documents "as stored", not generated icons | no — escaping at the sink, sanitising, or a refusal all pass | low |
| `functional/zz_stk_func_icon_test.go::TestFunc_DynamicIconRendersPlainText` | text icon shows `A`, `你`, `A&B`; none becomes markup | "text icons keep displaying their text"; no value may become executable content (escaping keeps the text) | no | low |
| `...::TestFunc_DynamicIconRendersTemplateOutput` | `.action{.title}` expands and shows the stored title | "Everything that works today keeps working"; "text icons keep displaying their text" | no | low |
| `...::TestFunc_DynamicIconKeepsTextVisibleWhenSettingEnabled` | setting on: plain text still renders as text | "text icons keep displaying their text"; "Everything that works today keeps working". No security rule forbids plain text; the setting-on clause governs documents "as stored" | no — escaping keeps the same text | low |
| `...::TestFunc_DynamicIconRendersDateIcon` | the type-1 badge still renders a clean SVG | "Everything that works today keeps working"; "a legitimate SVG that carries no executable content keeps its content intact" | no | low |
| `...::TestFunc_DynamicIconKeepsPaletteColour` | named palette colour still paints the badge | "Everything that works today keeps working" | no — a sanitiser keeps a plain `fill:` style | low |

## 2. Leniency (quality, non-blocking)

| property / trap | most plausible WRONG fix | caught? |
|---|---|---|
| caller text is content | serve caller text raw when the setting is on | yes — `TestSec_DynamicIconNeutralisesCallerTextWhenSettingEnabled` (`control_miss_content.patch`) |
| returned SVG clean | keep the script-name-only helper | yes — five security cases (`control_miss_content.patch`) |
| returned SVG clean | refuse every icon request | yes — functional 200 + content demands (`control_overbroad.patch`) |
| inert wrapper | flag any `foreignObject`, even inert | corrected — the checker now flags only an active subtree |
| fail-closed | crash (500) instead of a clean refusal | yes — `stkAssertNeutralised` rejects ≥500 |

Wrong fixes no test catches (quality only): dropping text that contains `<` instead of escaping
it (the functional cases are `A`, `你`, `A&B`; the security case accepts removal); special-casing
`type=8` (every icon case is type 8); animation attributes, CSS `url(...)`, `<meta>/<link>/<base>`.

## 3. Hints (quality, non-blocking)

`instruction.md` names no file, function, helper, trap, variant list or count. The one route it
mentions is the published trigger, explicitly framed as "one illustration" of an invariant.
Nothing was added or removed by this repair (the audit forbade editing `instruction.md`).

## 4. Realism

The trap is the published advisory route at the pinned commit. The setting-on behaviour and the
palette/date forms are real upstream code. Nothing looks planted. The fixture uses the default
editor settings (setting off) and a real workspace document; the setting-on cases enable the
documented setting.

## Stacking checks

| check | concept | finding | gate-a |
|---|---|---|---|
| S1 coupled | C1 (T2) | The must-keep values (plain text `A`/`你`/`A&B`, the expanded title, the date badge, the palette colour) are covered by "Everything that works today keeps working ... text icons keep displaying their text". No security rule forbids plain text: text a caller supplies stays *content*, and escaping preserves it. The setting-on functional case keeps only plain text, which the caller-text rule does not forbid. | no |
| S2 shape | C1 | Refused shapes (`on*`, `javascript:`, markup `data:` links, iframe/object/embed, an active `foreignObject`, `svg:script`) all lie outside the stated legitimate set ("Ordinary navigation links and raster images stay as they are"; text and non-executable content). An inert `foreignObject` is no longer refused, so it lies inside the legitimate set. | no |
| S3 fixtures/harness | C1 | Setting defaults off; the workspace document and palette/date states are legitimate; every request goes through the product's registered handler. A guard in the handler or in the SVG generator both pass. | no |
| S4 independence | C1 | Single concept, so independence is vacuous. The security case that fails on pinned code does so through its own route (setting-on icon request). | no |
| S5 history | C1 | Not an H3a/H3b stacked task and carries no `upstream_first_fix` check; the advisory's published fix is the reference behaviour. N/A. | n/a |
| S6 contracts | C1 | Tests use the existing handler and configuration model; no name the solver would have to guess. No wrong-object or fail-open fallback. | no |
| S7 decisive | C1 | No `trial_summary.md`. The audit's deciding test, `TestFunc_DynamicIconServesScriptsWhenSettingEnabled`, demanded raw caller markup with the setting on; it has been replaced by a plain-text keep-working case, and the caller-text rule is enforced in the security group. No remaining single test decides a run. | n/a |

## Verdict

Every test is covered by the general property ("no SVG document the kernel returns to a client
may carry executable content ..."), the unconditional caller-text rule, or a stated must-keep
clause. The primary mechanism — escape caller text at the icon sink in every mode — passes all
tests; a guard at the handler layer also passes. The 2026-10-25 test fault is removed. No
correct-fix-fails mechanism found.

Required: generalize: none. Quality to tighten: animation/CSS-url/meta content, a
plain-text-with-`<` functional case, `.SVG`/extensionless naming; `type=8` is the only icon kind
exercised.

GATE_A: READY
NEEDS_HUMAN_REVIEW: NO
