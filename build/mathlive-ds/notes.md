# mathlive-ds build notes

- Start: 2026-10-24T04:12Z (clone of arnog/mathlive)
- End: 2026-10-24T05:19Z (all four gate stages passed)

## Task shape

Pinned commit `25db1a83`, published fix `5fe1c461` ("address XSS vulnerability in text-mode
content rendering"). The vulnerable image is the pinned tree plus `environment/injection.patch`
(two sibling paths). `solution/fix.patch` is the published source change extended to every
producer used by the tests and to the injected siblings.

Property in `instruction.md` (stated once): no character taken from the LaTeX input may be
interpreted as markup by anything that consumes the library's output, in any output the library
produces, for text the author writes and for characters used as delimiters.

## Levers

- **T1 (A, where): HTML element content.** `src/core/box.ts:356` interpolates `Box.value` raw
  into `<span>` content; the reported trigger lands here. Reason to dismiss: none — this is the
  report; included for completeness and as the positive control.
- **T2 (A, where): MathML serializer.** `src/formats/atom-to-math-ml.ts:24,257,620,760,795,861,
  870,880,1134,1140` is a second output implementation with its own escaper, run coalescing and
  delimiter sites. Reason to dismiss: it is a visually hidden assistive side output and the
  report's example only exercises the HTML renderer.
- **T3 (B, how — main lever): speakable-text route.** `src/formats/atom-to-speakable-text.ts`
  concatenates text-mode values raw at three sites (231 run, 280 single atom, 539 text-mode
  branch) and `src/addons/static-render.ts:289` assigns the markup form to `innerHTML`. The plain
  form strips only complete tags. Reason to dismiss: the option is off by default, the output is
  described as plain text for a speech engine, and the strip step looks like it already
  sanitizes. Fix needs the mechanism understood: producer vs sink, plain vs markup mode, complete
  vs split text runs. This route is real, unmodified upstream code and was hardened in a later
  upstream commit (9ac6ebae), i.e. it is not covered by the published fix.
- **T4 (injected, where): starred operator argument.** `src/formats/atom-to-math-ml.ts:586` (added
  `toMo` branch) joins the characters of `\operatorname*{...}` into `<mo>` raw. Reason to
  dismiss: obscure starred variant; the neighbouring plain-operator path looks handled.
- **T5 (injected, where): static element error display.** `src/public/math-static-elements.ts:354`
  assigns the original content with `innerHTML` when conversion fails. Reason to dismiss: only an
  error-display path, not a rendering path.

Coupled must-keep-working behaviour: normal text values and their ampersands (T1/T2), named and
directly written symbols (T2/T4), delimiters (T2), plain spoken output staying plain and the
markup document staying intact (T3), and the unrenderable content still being displayed (T5).

## Candidate sibling list (full)

HTML producers found: `Box.toMarkup` value (chosen T1); `svgBody`/`svgOverlay`/`svgStyle`
(internal fixed strings, no attacker text); `htmlData`/`href`/attributes/classes/cssId/htmlStyle
(attribute or CSS context — a different protected outcome, out of the advisory's element-content
scope); `math-static-elements._renderContainer` and `_mathMLContainer` (delegate to the two
converters, covered); mathfield render `innerHTML` (delegates to the HTML converter); editor UI
and virtual-keyboard `innerHTML` sinks (localised product labels, no LaTeX data).

MathML producers found: text atom/text run/raw-latex atom (published fix); array, genfrac,
left/right and sized-delimiter sites (published fix); `mord` unicode and `\char` entity emission
(published fix but verified unreachable through the public converters at this commit — probes for
`\char"3B1`, `\dblcolon`, `\mathop{\char"2237}` and literal non-Latin identifiers produced no
entity output; the screener's O5 coupled-lever claim therefore does not reproduce and is not used);
`mpunct` command (fixed symbol token, not attacker text); `case 'mop'` body (atom array, drops or
stringifies, no text); `toMo` (uses the escaping `toString` helper); `case 'macro'` (escaped plus a
restricted macro name); `box` background and `enclose` notation and `\bbox` border (attribute/CSS
context, different outcome, later advisory); `mathVariantToUnicode` mapped output (fixed table);
`\mbox` in MathML (produces no output, not a sink).

Speakable/other found: the three raw text sites plus the static-render sink (chosen T3); the
public `convertLatexToSpeakableText` (same producer); `aria-label` on the static elements
(attribute, safe); ascii-math and LaTeX serializers (not markup); editor a11y/speech modules
(no HTML sink for formula text).

Why the picks beat the others: T3 is the only remaining real producer/sink pair at the pinned
commit and is mode- and shape-sensitive (how-type). T4/T5 are the two most complex natural
injected gaps that are actually reachable with attacker text: both sit in helpers/paths the
published fix never touches, both are ordinary maintainer code, and each has a different reason to
be skipped. The other MathML candidates were rejected because probing showed they cannot carry
attacker text without contriving the injection; attributes were rejected as a different protected
outcome (wrong scope).

## Gate results (Harbor, 2026-10-24)

- static: PASSED.
- nop: PASSED (security 27/27 fail on the untouched image; functional 150/150 pass).
- oracle: PASSED, 3/3 runs reward 1.0 with identical results.
- patches: PASSED. miss_html 10 security failures / 0 functional; miss_mathml 14/0;
  miss_speakable 3/0; miss_injected_mop 2/0; miss_injected_fallback 1/0;
  escape_plain_speakable 0 security / 1 functional; hardening 1.0; alternative 1.0.

## Verified locally (outside Docker, exact suites and configs)

- Vulnerable tree (pinned + injection): 27/27 security cases fail, 14/14 functional cases pass,
  136/136 project tests pass.
- Reference fix applied to the vulnerable tree via `solution/fix.patch`: 177/177 cases pass.
- Each `checks/*.patch`: `miss_html` 10 security failures / 0 functional; `miss_mathml` 14/0;
  `miss_speakable` 3/0; `miss_injected_mop` 2/0; `miss_injected_fallback` 1/0;
  `escape_plain_speakable` 0 security / 1 functional; `hardening` and `alternative` pass all 177.
- `npm ci --ignore-scripts` produces a tree that runs the project jest suite (333 tests).
- jsdom 26.1.0 drives the real `renderMathInElement` and `<math-span>` paths; the strict XML check
  uses jsdom's `DOMParser`.

## Could not verify

- Upstream state after the clone's main tip (read-only look showed the speakable route hardened in
  9ac6ebae; no published advisory text for that follow-up was consulted).
- Whether some macro expansion can ever place attacker text into `mpunct.command` (probes say no).
- Real-browser behaviour for malformed fragments was not used: the DOM assertions only rely on
  complete tags, which jsdom and browsers parse the same way.
- `repo_mb` was not measured.

## Fairness concerns I see

- T2 requires auditing a second public conversion function that the report never names; the
  property says "every output", so it is in scope, but a solver who reads only the example will
  miss it. That is the intended scope lever.
- T3 requires auditing the `innerHTML` sinks of the static renderer; the route is opt-in and
  described as plain text. The property covers it literally and the code is visible.
- The `&` escaping kept from the published fix is not required by any test (entities do not
  re-tokenise as markup); it was kept to match the published change and does not narrow correct
  fixes.

## Outside the scope I noticed (not built on)

- Attribute/CSS injection through `\htmlData`/`\bbox`/`\enclose` values was hardened in a later
  upstream commit; it is a different protected outcome and was left alone.
- The speakable text-run site at `atom-to-speakable-text.ts:231` is still unescaped in current
  upstream; only the tested route (markup mode) is in scope here.
