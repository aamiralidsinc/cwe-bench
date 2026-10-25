# FAIRNESS — pv-svgo (pre-trial gate review)

Read: instruction.md, all tests/, solution/fix.patch, manifest.json, notes.md, checks/*.patch; nothing
run. P1/P2/P3 = executable code / embedded active document / executable URL in an attribute. K =
"Everything that cannot execute must behave exactly as it does today". K2 = "dangerous content must be
removed, not rejected" (a throw fails the harness).

## 1. Test fairness

| test (file::name) | what it asserts | covering sentence | could a correct fix fail it? | risk |
|---|---|---|---|---|
| security/foreign_object.test.js::nested_event_handler_in_embedded_html_is_removed | `onbeforetoggle` on a `<p>` nested in foreignObject gone; `<p>` kept | P1 + "nested"; K keeps inert `<p>` | no — walker, plugin or recursive plugin visitor all reach it | low |
| security/foreign_object.test.js::deeply_nested_event_handler_in_embedded_html_is_removed | `onclick` on a two-deep `<span>` gone; span kept | P1 + "nested" | no | low |
| security/foreign_object.test.js::srcdoc_on_direct_child_is_removed | `srcdoc` gone; `<iframe>` kept | P2; K "embedded HTML that is visual or inert keeps its elements" | no — strip the attribute; deleting the iframe breaks K and is over-broad, not correct | low |
| security/foreign_object.test.js::srcdoc_on_nested_child_is_removed | `srcdoc` gone, ordinary `src="https://example.com/x"` kept | P2; K ordinary links/elements | no | low |
| security/foreign_object.test.js::executable_url_attributes_in_embedded_html_are_removed | javascript:/vbscript:/data:text/html/data:image/svg+xml gone from form/button/object/iframe; those elements kept | P3; K keeps visual embedded elements | no | low |
| security/foreign_object.test.js::prefixed_foreign_object_content_is_sanitised | prefixed svg:/xhtml:/alias: content sanitised; `<xhtml:div>` kept | P "however it is named"; expert: a prefix is bound by its in-scope xmlns declaration | no — ns-aware local-name match; a bare local-name match fails functional 28 (wrong fix) | medium |
| security/foreign_object.test.js::event_handler_on_foreign_object_element_is_removed | handler on the foreignObject element gone; div kept | P1 | no | low |
| security/foreign_object.test.js::script_elements_in_embedded_html_are_removed | raw and `xhtml:` script elements gone; `<p>` kept | P1 "carried in an element", "named" | no | low |
| security/foreign_object.test.js::mixed_case_script_element_is_removed | `<SCRIPT>` gone; `<p>` kept | P "spelled"; expert: HTML parsing case-folds element names | no | low |
| security/foreign_object.test.js::executable_data_document_in_embedded_html_is_removed | both `data:` documents gone; `<iframe>` kept | P2, P3 | no | low |
| security/animation.test.js::animation_applying_executable_url_to_link_is_removed | no javascript:/alert; `href="#t"` link and text kept | P3; expert: SMIL `set` assigns the target attribute at render time; K keeps the safe link | no | low |
| security/animation.test.js::animation_applying_executable_url_list_is_removed | no javascript:/alert; **`<animate>` must be absent** | P3 (the `values` attribute holds the URL); no sentence requires the element's removal | **maybe** — a correct fix that deletes the executable `values` item/attribute leaves an inert `<animate>` and fails only this assertion | medium |
| security/animation.test.js::animation_applying_executable_data_url_is_removed | data:text/html gone; text kept | P3 | no | low |
| security/animation.test.js::animation_applying_executable_url_from_value_is_removed | no javascript:/alert | P3 (`from` holds it) | no | low |
| security/anchors.test.js::executable_html_data_link_is_neutralised | data:text/html gone; **no `<a>` element**; text kept | P3; K guarantees the element only for "a link whose URL cannot run code" | **maybe** — a correct fix that deletes the `href` leaves an inert `<a>` and fails the element-absence assertion | medium |
| security/anchors.test.js::executable_xhtml_and_svg_data_links_are_neutralised | three data links gone; **no `<a>`** | P3 | **maybe** — same attribute-strip fix | medium |
| security/anchors.test.js::legacy_vbscript_link_is_neutralised | vbscript: gone; **no `<a>`** | P3; expert: `vbscript:` is a scripting scheme | **maybe** — same | medium |
| security/anchors.test.js::executable_scheme_with_ascii_whitespace_is_neutralised | tab/LF/CR-split schemes gone; **no `<a>`** | expert: browsers strip ASCII tab/LF/CR before URL parsing; P3 | **maybe** — same | medium |
| security/anchors.test.js::namespace_prefixed_anchor_is_neutralised | alert values gone; `<text>` kept (no element-absence assertion) | P "named"; expert: XML namespace binding; K keeps text | no | low |
| security/anchors.test.js::prefixed_href_with_executable_data_link_is_neutralised | data link on `uwu:href` gone; **no `<a>`**; text kept | P3; expert: prefixed attribute local name | **maybe** — same attribute-strip fix | medium |
| security/svg_events.test.js::pointer_event_handler_on_svg_root_is_removed | `onpointerdown` on the root gone; rect kept | P1; expert: `onpointerdown` is a handler, the SVG-1.1 groups are not exhaustive | no — an `on*` guard; a curated list can pass but is a wrong fix | low |
| security/svg_events.test.js::wheel_and_auxclick_handlers_are_removed | `onwheel`, `onauxclick` gone; rect kept | P1 | no | low |
| security/svg_events.test.js::html_only_event_handler_is_removed | `onanimationstart`, `onbeforetoggle` gone | P1 | no | low |
| security/svg_events.test.js::mixed_case_event_handler_is_removed | `onClick`/`onLoad` gone | P "spelled"; expert: HTML case-folds attribute names | no | low |
| security/svg_events.test.js::mixed_case_event_handler_on_nested_element_is_removed | `ONMOUSEOVER` gone; `<g>` kept | P "spelled", "nested" | no | low |
| functional/preservation.test.js::inert_data_links_keep_working | PNG/JPEG/GIF data links intact | K "a link whose URL cannot run code keeps working" | no (stripping every data: is over-broad) | low |
| functional/preservation.test.js::embedded_visual_html_keeps_working | class/style/title, https src/action/embed, input, text kept | K embedded-HTML bullet | no | low |
| functional/preservation.test.js::elements_from_other_vocabularies_keep_their_content | `custom:a href="javascript:…"` and `custom:foreignObject srcdoc` kept | K "elements and attributes that belong to other vocabularies are not acted on …" | no — local-name matching without a namespace check is a wrong fix | low |
| functional/preservation.test.js::ordinary_links_keep_working | https/#/mailto/relative links kept | K link bullet | no | low |
| functional/preservation.test.js::document_attribute_spelling_and_values_are_kept | viewBox/preserveAspectRatio/gradientUnits/aria-label kept | K "values that describe appearance, geometry or layout …" | no | low |
| functional/preservation.test.js::non_executable_animations_keep_working | harmless set/animate/href animation kept verbatim | K "Everything that cannot execute must behave exactly as it does today" | no (removing all href animations is over-broad) | low |
| functional/preservation.test.js::foreign_object_inert_attributes_are_kept | width/data-kind/class kept | K embedded-HTML bullet | no | low |
| functional/project_tests.test.js::project_plugin_fixtures_still_pass | repo's `test/plugins/_index.test.js` green (325) | K; expert: the visible project suite must stay green | no — reference/hardening pass; over-broad `hasScripts` fails | low–med |
| functional/project_tests.test.js::project_library_tests_still_pass | `lib/svgo.test.js`, `lib/svgo-node.test.js` green | same | no | low |

## 2. Leniency (quality, non-blocking)

| property / trap | most plausible WRONG fix | caught? |
|---|---|---|
| T1 traversal | leave the walker skip and clean only foreignObject's direct children / only the reported `srcdoc` | yes — nested and deeply-nested handler tests; `miss_traversal.patch` |
| T1 traversal | keep the xast skip but recurse inside the plugin | not a wrong fix (valid layer) |
| T2 animation | ignore animation entirely | yes — 4 animation tests; `miss_animation.patch` |
| T2 animation | handle only `to`, not `from`/`values` | yes — list/from tests |
| T2 animation | handle only `<a>` targets, or only `href` (not `src`) | **not caught** — every case sits under `<a>`; no animation of `src` |
| T3 event list | extend the fixed SVG-1.1 list with just the names tested (`onpointerdown`, `onwheel`, `onauxclick`, `onanimationstart`, `onbeforetoggle`) | **not caught** — no arbitrary/future handler (`onbeforematch`, `oncontextlost`, `onpointerrawupdate`) |
| T3 event list | strip `on*` only on SVG-namespace elements, not XHTML ones | yes — prefixed `<xhtml:div onpointerdown>` test |
| T4 case folding | case-sensitive attribute comparison (`/^on[a-z]+$/`) | yes — mixed-case handler tests; `miss_case_folding.patch` |
| T4 case folding | lowercase only inside embedded HTML | yes — `onClick`/`onLoad` on SVG root and `<g>` |
| T4 case folding | exact-case `srcdoc` / `attributeName` matching | **not caught** — no `SRCDOC`/`ATTRIBUTENAME` case test |
| T4 case folding | fold only unprefixed names | **not caught** — no mixed-case prefixed `<svg:SCRIPT>` |
| T5 data/vbscript | extend only `data:text/html` | yes — xhtml/svg data-link test; `miss_data_urls.patch` |
| T5 data/vbscript | strip every `data:` URL | yes — inert data links; `strip_everything.patch` (functional fail) |
| T5 data/vbscript | check `href` only, not action/data/formaction/src | yes — embedded-URL test |
| T5 data/vbscript | fix SVG anchors only, or embedded HTML only | yes — the other group's data tests |
| T6 prefixes | strip the prefix and match local names without the namespace check | yes — `elements_from_other_vocabularies_keep_their_content` |
| T6 prefixes | resolve prefixes for `script` only (pinned behaviour) | yes — prefixed anchor/foreignObject tests; `miss_prefixed.patch` |
| T6 prefixes | handle prefixed attributes but not prefixed element names (or vice versa) | yes — `prefixed_href…` vs `namespace_prefixed_anchor…` |
| P3 URL carriers | handle the five HTML URL attributes but not `href` on an anchor inside foreignObject | **not caught** — no `<a href="javascript:…">` inside a foreignObject |
| P3 URL carriers | ignore `<use>`/`<image>` href, CSS `url()`, `<meta refresh>`, `<base href>` | **not caught** |
| refusal | throw/abort on hostile input (`crash_as_refusal`) | yes — support/product.js; `crash_on_attack.patch` |
| refuse all | strip every attribute/element | yes — functional 26/27/30/31/32; `strip_everything.patch` |
| adjacent API | broaden `tools.js:hasScripts` | yes — project plugin fixtures; `broaden_has_scripts.patch` |
| adjacent API | leave `hasScripts` javascript-only | **not caught** (manifest out_of_scope: removes nothing) |

Wrong fixes no test catches: curated-list extension (unlisted handler); exact-case `srcdoc`/`attributeName`;
mixed-case prefixed names; animation of `src` or on a non-anchor element; embedded-HTML anchor `href`;
non-`href` URL carriers; the duplicate `hasScripts` left stale.

## 3. Hints (quality, non-blocking)

- "the embedded `srcdoc` payload" → "the attacker's embedded document".
- "however it is named, spelled, or nested" → "without exception".
- "one form …, not the complete set", "the other forms the same property covers", "Do not special-case
  the example" → delete; the property already covers every input.
- "script-removal option" (and the title) → "sanitiser mode".

## Required: generalize (step 3a)

- "embedded HTML that is visual or inert keeps its elements, text, styles, classes, titles and ordinary
  links" → "Content that cannot execute keeps its elements, text and values exactly as today." (names the
  embedded-HTML format and enumerates the traversal trap's keep case)
- "a link whose URL cannot run code keeps working and keeps its element"; "values that describe
  appearance, geometry or layout keep their spelling and their values" → fold into that sentence.
- "elements and attributes that belong to other vocabularies are not acted on as part of the document and
  keep their content" → "Only content the browser acts on as part of the document is changed; everything
  else keeps its content." (names the other-vocabulary route, hints at namespaces)

## 4. Realism

The traversal gap is the one injected change: a plausible perf hoist of a `foreignObject` skip into the
shared walker, matching the comment's per-plugin skips and a green project suite — synthetic, not
contrived. Animation, the event list, case folding, the duplicated `javascript:` check and prefixes are
real pinned-tree code, open upstream; realistic by definition. All reach `optimize(svg,
{plugins:['removeScriptElement']})`; no fixture bypasses a guard layer.

## Verdict

**NOT READY (gate a).** Six security assertions demand a removal *form* the instruction never states.
P3 forbids "no executable URL in an attribute": a safe fix deleting the offending `href`/`uwu:href`
leaves an inert `<a>`, and deleting the offending `values`/`to`/`from` item leaves an inert `<animate>`;
P, K and K2 hold. But the five anchor tests assert `<a>` is absent and
`animation_applying_executable_url_list_is_removed` asserts `<animate>` is absent, so that correct fix
scores 0.76, never 1.0; the reference (broaden the predicate, keep the existing anchor-unwrap, detach the
animation) passes. Nothing requires element removal — the link clause guarantees the element only for
safe URLs, and K's embedded-HTML bullet is why the same attribute-only fix rightly keeps
`<iframe>`/`<form>`/`<object>`. Test fix only: drop those six assertions (the URL assertions still fail
every `miss_*` patch); accept absent-or-inert. No other correct-fix-fails mechanism.

**Quality to tighten**: add an arbitrary handler (`onbeforematch`, `oncontextlost`); add `SRCDOC`,
`ATTRIBUTENAME` and `<svg:SCRIPT>`; add an embedded-HTML `<a href="javascript:…">`, `<use>`/`<image>`
href and animation of `src`/on a non-anchor; supply the missing `checks/blind.patch` and an
attribute-stripping alternative (`alt_design.patch` repeats the reference's removal form).

Human review: confirm the removal-form call — that deleting only the executable URL attribute (leaving an
inert `<a>`/`<animate>`) is a correct fix; if so, relax those six assertions.

GATE_A: NOT_READY
NEEDS_HUMAN_REVIEW: YES
