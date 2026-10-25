# FAIRNESS-VALIDATION: pv-svgo

What I read: instruction.md, every file in tests/, solution/fix.patch, manifest.json, notes.md,
checks/, FAIRNESS.md (DeepSeek, GATE_A NOT_READY), and the 7 run audits (`verdict.json`) with each
run's `verifier/results.json` under `~/.tb-graders/cwe/jobs/ext-actions-pv-svgo-*`. I also read the
repo's own fixtures `test/plugins/removeScriptElement.0{1..8}.svg.txt` from a gate workspace copy.
Nothing was run. None of the run imports includes code, a transcript or the failure messages
(`transcript.md` = "(no transcript)"). Per-run behaviour can only be inferred from which tests
passed and failed.

Instruction sentences used below:
- **P**: "For every element and attribute the browser acts on - however it is named, spelled, or nested -
  the output must contain: no executable code ...; no embedded active document; and no executable URL
  in an attribute." Also: "the optimised document must not cause a browser to execute code when it
  renders it."
- **K-html**: "embedded HTML that is visual or inert keeps its elements, text, styles, classes, titles and
  ordinary links"
- **K-link**: "a link whose URL cannot run code keeps working and keeps its element"
- **K-vocab**: "elements and attributes that belong to other vocabularies are not acted on as part of the
  document and keep their content"
- **K-all**: "Everything that cannot execute must behave exactly as it does today" and "Keep all existing
  legitimate behaviour working."

## 1. The reviewer's six assertions

### Five anchor tests that assert `<a>` is absent (`executable_html_data_link`, `executable_xhtml_and_svg_data_links`, `legacy_vbscript_link`, `executable_scheme_with_ascii_whitespace`, `prefixed_href_with_executable_data_link`)

**FAIR (strict, but the repo sets the form).** The reviewer is right that P alone would allow
deleting only the `href`. But the product already has a removal form for exactly this class. The
pinned plugin replaces an anchor whose `href` / `*:href` is `javascript:` with its children. The
repo's own fixtures pin that behaviour:
- `removeScriptElement.02` "Collapses links to JavaScript functions";
- `.04`, `.05` "Removes hrefs to JavaScript URIs, including unconventional namespaces" (with
  `uwu:href`, the same shape as the hidden prefixed test);
- `.08` (uppercase).

The functional test `project_plugin_fixtures_still_pass` runs these fixtures.

So a fix that switches to deleting the attribute fails a fair functional test on `javascript:`
anchors. A fix that collapses `javascript:` but only strips `data:`/`vbscript:` gives one class of
link two different treatments, and nothing in the instruction suggests doing that. K-link points the
same way: only a link "whose URL cannot run code ... keeps its element". The obvious engineering move
is to widen the existing predicate, which the reference and `alt_design` both do. That yields the
collapse form. The reviewer missed the existing behaviour, so its correct-fix-fails claim does not
hold for these five. Optional robustness repair: accept "absent or inert `<a>`".

### `animation_applying_executable_url_list_is_removed`, assertion `notMatch(/<animate[\s>]/)`

**UNFAIR, but only that assertion.**
- The pinned tree has no animation handling, so no existing form applies.
- No sentence requires removing the animating element.
- The sibling tests contradict a removal requirement: `..._to_link`, `..._data_url` and `..._from_value`
  check only that the URL is gone.

A correct fix that drops the `javascript:` item from `values` (leaving `values="#one;#two"`), or
deletes the `values` attribute, leaves an inert `<animate>` and fails here. Its two URL assertions
are fair.

## 2. The audit's frame / embedded-HTML assertions

| test | element-survival assertion | verdict |
|---|---|---|
| `srcdoc_on_direct_child_is_removed` | `<iframe` kept | **UNFAIR.** An iframe that carries `srcdoc` is neither "visual" nor "inert" (K-html does not cover it). Under "no embedded active document", deleting the frame is a natural correct fix, and the instruction's own example is exactly this element. No existing behaviour applies (the walker never reached foreignObject content). |
| `srcdoc_on_nested_child_is_removed` | `src="https://example.com/x"` kept on the srcdoc iframe | **UNFAIR**, for the same reason: frame removal fails it. |
| `executable_url_attributes_in_embedded_html_are_removed` | `<form>`, `<button>`, `<object>`, `<iframe>` kept | **UNFAIR as a unit.** Keeping form/button is defensible (K-html: visual, holds text). Keeping `<object data="data:text/html…">` and the `<iframe src="data:image/svg+xml">` frame is not: these are active-document containers, and removing them is correct. The URL assertions are fair. |
| `executable_data_document_in_embedded_html_is_removed` | `<iframe` kept | **UNFAIR**, same as above. The `data:` assertion is fair. |
| `embedded_visual_html_keeps_working` (functional) | `src="https://example.com/embed"` iframe kept | **UNFAIR (contradiction-grade).** A remote iframe renders an embedded active document that runs code. Read literally, P ("must not cause a browser to execute code when it renders it"; "no embedded active document") supports removing it, while the test zeroes the reward if it is removed. The task also forbids `data:text/html` frames, which run in an opaque origin just as a cross-origin https frame does, so the line it draws between the two is arbitrary. The rest of that test (class/style/title/img/form action/input/text) is fair. |

I agree with the audit on the frame class and disagree with it on the animation-list
element-absence assertion. On the anchors I agree with the audit and disagree with the reviewer.

Other tests I checked that the runs fail:
- **`elements_from_other_vocabularies_keep_their_content`: FAIR.** K-vocab states it outright.
  Fixture `.07` (`filmmaker:script` is kept) shows the repo already resolves namespaces. The nop
  tree passes it, so a failure means the fix acted on `custom:a` / `custom:foreignObject`
  (local-name matching, or stripping `srcdoc` everywhere). No frame-removal policy can cause this
  failure, because the test has no frame element.
- **FAIR:** the remaining animation tests (URL plus kept-text or kept-safe-link assertions), the
  event-handler tests, and the nested-handler tests.

## 3. Key question: does every graded run still fail a fair test?

Unfair set excluded: the animation-list `<animate>` assertion (I count the whole test as excluded,
because its cause cannot be told apart without code), the four frame security tests, and
`embedded_visual_html_keeps_working`.

| run | fair tests it still fails | holds? |
|---|---|---|
| deepseek-a1 | functional `elements_from_other_vocabularies_keep_their_content`, so reward stays 0 | YES (rests on one fair functional test) |
| deepseek-a2 | animation `to_link`, `data_url`, `from_value`; functional `other_vocabularies`; anchors ×3 (data links) | YES |
| deepseek-a3 | animation `to_link`, `data_url`, `from_value`; functional `other_vocabularies` | YES |
| mimo-a1 | functional `other_vocabularies` | YES (same single fair functional test) |
| mimo-a2 | `animation_applying_executable_data_url_is_removed` (asserts only that the `data:text/html` URL is gone and the text is kept); anchors ×3 on data links | YES (security share < 1, no solve) |
| mimo-a3 (agent timeout 7200 s, graded) | `svg_events` ×5, nested/deeply-nested handlers, `script_elements`, `namespace_prefixed_anchor`, animation ×3, and more | YES (timeout counts as a fail) |
| mimo-a4 | functional `other_vocabularies` | YES (same single fair functional test) |

Notes on two of those rows:
- **mimo-a2 and deepseek-a2, anchors.** These two runs pass `legacy_vbscript_link` and
  `executable_scheme_with_ascii_whitespace`, which carry the same `<a>`-absent assertion. So they
  already collapse anchors; their data-link failures are almost certainly the `data:` URL
  surviving. Neither run needs the anchor tests to hold.
- **deepseek-a1, mimo-a1, mimo-a4 rest on one test.** Each depends only on the
  `other_vocabularies` failure. Without failure messages that is inferred, but every assertion in
  that test enforces K-vocab, so any way of failing it is fair.

No run fails only unfair assertions. Every run remains a counted model failure.

Repairs needed before the task is READY:
1. Drop or relax the frame-survival assertions (`foreign_object.test.js` lines 44, 56, 77-78, 143) and
   the remote-iframe line in `embedded_visual_html_keeps_working`. Alternatively, state in the
   instruction that frames are kept once their dangerous attribute or URL is removed, and that remote
   frames are allowed.
2. Drop the `<animate>`-absent assertion.
3. Add a frame-removing alternative patch to the checks.

VALIDATION: CONFIRM_NOT_READY
BREAKER_HOLDS: YES
