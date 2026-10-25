# FAIRNESS — pv-apostrophe (pre-trial review)

Reviewed on disk: `tasks/pv-apostrophe/instruction.md`, all 5 test files (20 security + 17 new
functional + the 241-case frozen project suite), `tests/test.sh`, `tests/score.py`,
`solution/fix.patch`, `environment/injection.patch`, `build/pv-apostrophe/manifest.json`,
`notes.md`, all 10 `checks/*.patch`. Nothing was run; no upstream fix consulted online.

Legend — the instruction's properties:
- **G1** "Whatever the input, the output must not contain a URL whose scheme the configuration
  does not permit for the element it is emitted on — whether that URL is an **attribute value**,
  **one of several destinations inside a list value**, or **a destination that the browser
  derives, copies or loads after sanitization**."
- **G2** "Every destination is judged on its own."
- **G3** "Where the configuration names a per-element scheme list, that list is the complete
  policy for that element; the global list does not widen it."
- **C** "Everything the configuration permits must keep working exactly as today: permitted-scheme
  and relative URLs, values that are not destinations, and several separate URLs in one document."
- **R** "A rejected value or element is left out of the output (or escaped in escape mode) … and
  the rest of the document is sanitized as usual."
- **WH-refresh** standard expert knowledge, HTML's shared declarative-refresh steps: time, optional
  `;`/`,`/whitespace separator, optional case-insensitive `url=`, optional quotes, otherwise the
  remainder is the destination the browser navigates to.
- **WH-smil** standard expert knowledge: SMIL `animate`/`set`/`animateColor`/`animateMotion`/
  `animateTransform` copy `attributeName`'s attribute from `values`/`from`/`to`/`by` after
  sanitization; `values` is `;`-separated.
- **WH-case** standard expert knowledge: HTML/SVG names and URI schemes are compared ASCII
  case-insensitively; htmlparser2 canonicalises tag/attribute names unless configured otherwise.

Harness: `tests/test.sh` runs both groups with mocha against the public module
`packages/sanitize-html/index.js`; `score.py` gives 1.0 only if every security **and** functional
case passes. No test imports notes, tests-from-workspace or an internal helper, so any valid guard
layer is acceptable.

## 1. Per-test fairness

### security/smil_animation.test.js

| test | asserts | covering sentence | could a correct fix fail? | risk |
|---|---|---|---|---|
| values list with a safe fragment prefix | no `javascript:`; `Click me` survives | G1 list value + G2 | no — split the list and judge each entry, or reject the animation; both pass | low |
| values with a forbidden scheme when `values` is not scheme-checked | no `javascript:`; text survives | G1 list value + G1 "copies … after sanitization" | no — a fix gating on `allowedSchemesAppliedToAttributes` is incomplete; the copied list is still an emitted destination | low/medium |
| retargets a link through `from` | no `javascript:`; text survives | G1 "copies"; WH-smil | no — a `values`-only split (smil_values_only) is incomplete | low |
| `<set>` retargets through `to` | no `javascript:`; text survives | G1 "copies"; WH-smil (`set` is an animation element) | no | low |
| retargets through `by` | no `javascript:`; text survives | G1 "copies"; WH-smil | no | low |
| prefixed target `xlink:href` | no `javascript:`; text survives | G1 list value/copied; WH-case | no — compare the local name or case-insensitively | low |
| target written in another case / with whitespace | no `javascript:`; text survives | G1 list value (the emitted `values` is a destination list) + G2; WH-case | no (judgment) — a target match must be trimmed/case-folded, as any attacker-name match should be; a case-sensitive matcher leaves `javascript:` inside an emitted list value, which G1/G2 forbid. If one holds a space-padded target unresolvable by the browser, the assertion is conservative | medium |
| another scheme-checked attribute (`src` on `image`) | no `javascript:` | G1 "the element it is emitted on" (image/src) | no — target must be checked against the full policy, not just `href` | low |
| every SMIL animation element (animateColor/Motion/Transform) | no `javascript:`; text survives | G1 "copies"; WH-smil; WH-case | no — treat animation tag names case-insensitively; a camelCase-only list can miss the parser's lowercase form | medium |

### security/list_scheme_policy.test.js

| test | asserts | covering sentence | could a correct fix fail? | risk |
|---|---|---|---|---|
| element permits no scheme at all (`img: []`) | no `cdn.invalid`; `keep` survives | G3 + G1 list value | no — empty override must be honoured (not treated as absent) | low |
| only the list destinations the policy forbids (`img:['https']`) | no `policy-violation.invalid`; `keep` survives | G3 + G1 list value + G2 | no — per-entry check with the element's list | low |
| alternate list attribute (`imagesrcset` on `link`) | no `policy-violation.invalid`; `keep` survives | G3 + G1 list value | no — all list-valued URL attributes must use the element's policy; handling only `srcset` is incomplete | low |

### security/per_element_policy.test.js

| test | asserts | covering sentence | could a correct fix fail? | risk |
|---|---|---|---|---|
| global list must not re-admit for a frame source | no `data:text/html`; `keep` survives | G3 (explicit) + G1 attribute value | no — replacement semantics pass; union is the bug | low |
| global list must not re-admit for an ordinary URL attribute | no `policy-violation.invalid`; `keep` survives | G3 | no | low |
| global list must not re-admit inside a list value | no `policy-violation.invalid`; `keep` survives | G3 + G1 list value | no — requires the list path to pass the element name, not the attribute name | low/medium |

### security/meta_refresh_destination.test.js

| test | asserts | covering sentence | could a correct fix fail? | risk |
|---|---|---|---|---|
| refresh destination with `javascript:` | no `javascript:`; `keep` survives | G1 "a destination that the browser derives … after sanitization"; WH-refresh | no — deleting `content` or the element both pass R | low |
| refresh destination with `data:` | no `data:text/html`; `keep` survives | G1 derived destination; WH-refresh | no | low |
| separators, quoting, spelling, case (10 variants) | no `javascript:` for each; `keep` survives | G1 derived destination ("whatever the input"); WH-refresh | no (judgment) — a `;url=`-only parser is incomplete under the standard steps; the variants are the algorithm's own forms, including bare/after-`,`/quoted | medium |
| marker case and attribute order | no `javascript:`; `keep` survives | G1 derived destination; WH-case | no — inspect all attributes, compare `http-equiv` case-insensitively | low |
| honours the per-element policy for the embedded destination | no `policy-violation.invalid`; `keep` survives | G1 "the element it is emitted on" + G3 | no — the refresh check must call the policy with `meta` | low/medium |

### functional/url_policy_preservation.test.js

| test | asserts | covering sentence | could a correct fix fail? | risk |
|---|---|---|---|---|
| keeps permitted and relative links | https/mailto/ftp/relative `href` kept exactly | C | no | low |
| keeps the per-element override for a direct attribute | https `src` kept under `img:['https']` | C + G3 | no — replacement semantics keeps it | low |
| keeps a permitted data URL under the override | data `src` kept under `img:['data']` | C + G3 | no — only a fix that requires the global list to widen would fail, and that contradicts G3 | low |
| several permitted destinations in one document | all three URLs kept | C | no — rejects per-call memoisation that loses later URLs | low |
| protocol-relative URLs when permitted | `//example.com/x` kept (default) | C | no | low |
| protocol-relative URLs when forbidden | no `example.com` | C + option contract (`allowProtocolRelative`) | no | low |
| permitted list destinations | https and `//` entries kept under `img:['https']` | C + G3 | no | low |

### functional/meta_preservation.test.js

| test | asserts | covering sentence | could a correct fix fail? | risk |
|---|---|---|---|---|
| permitted refresh | `0;url=https://example.com/` kept exactly | C (permitted URLs keep working exactly) | no — a fix must not rewrite a permitted value | low |
| quoted refresh | `0; URL='https://example.com/'` kept exactly | C | no (judgment) — a fix that normalises/rebuilds `content` changes today's output; C forbids that, so it is not a correct fix | low/medium |
| relative refresh destination | `0;url=/relative/path` kept | C (relative URLs) | no | low |
| refresh with no destination | `content="5"` kept | C (values that are not destinations) | no — a fix that drops every unparseable refresh is over-broad | low |
| non-navigation meta content | `A price: 5 dollars` kept | C (values that are not destinations) | no — a colon-scan over all meta content is over-broad | low |
| permitted destination under a narrower per-element policy | refresh kept under `meta:['https']` | C + G3 | no | low |

### functional/animation_preservation.test.js

| test | asserts | covering sentence | could a correct fix fail? | risk |
|---|---|---|---|---|
| animation of a presentation value | `animate`, `red;blue`, `attributename="fill"` kept | C (values that are not destinations) | no — only a refuse-all-animations fix fails | low |
| `<set>` targeting a harmless attribute | `<set`, `to="0"`, `attributename="opacity"` kept | C | no — "0" is not a forbidden destination | low |
| non-animation element carries `attributeName` | `href="#safe"` and `attributename="href"` kept | C | no — keying on any `attributeName` rather than animation elements is over-broad | low |
| permitted link and content around an animation | https `href`, `Click me` kept | C | no | low |

### functional/project_suite.test.js

| test | asserts | covering sentence | could a correct fix fail? | risk |
|---|---|---|---|---|
| all 241 frozen upstream cases (incl. per-tag scheme override with `img:[]`, `srcset`/`imagesrcset` good+bogus entries, `xlink:href`, `formaction`, `object data`, escaping, parser options) | today's exact output | C | no — reference/alt/hardening trees pass; only an over-broad or union fix fails | low |

## 2. Leniency (QUALITY, non-blocking)

### 2a. Per security property

| property | most plausible WRONG fix | caught? |
|---|---|---|
| G1 attribute value | fix only `href` on `<a>` (the reported shape) | yes — per_element 1–2 (iframe/img `src`), smil 8 (`src` target) |
| G1 list value | treat `srcset`/`imagesrcset`/`values` as one flat URL | yes — list_scheme 1–3, per_element 3, smil 1–2/6 |
| G1 copied destination | fix only `values`; ignore `from`/`to`/`by` and `<set>` | yes — smil 3–5; `checks/smil_values_only.patch` |
| G1 copied destination | inspect the animation element's own `href`/`src` instead of `attributeName` | yes — smil 1–2 (`javascript:` survives); `checks/wrong_object_animation.patch` |
| G1 derived destination | classic `^\d+;\s*url=` regex (meta_classic_only) | yes — meta 3 (`0,url=`, `0 url=`, bare, quoted); `checks/meta_classic_only.patch` |
| G1 derived destination | drop all `meta`/`content` on refresh | yes — meta_preservation 1–6 |
| G3 completeness | union the global and per-element lists | yes — per_element 1–3, list_scheme 1–3; `checks/union_kept.patch` |
| G3 completeness | use the element name for `srcset` only | yes — list_scheme 3 (`imagesrcset`), per_element 3 |
| C | refuse all animation elements | yes — animation_preservation 1–2; `checks/overbroad_animation.patch` (functional_fail) |
| C | drop `allowedSchemesByTag` altogether | yes — url_policy 2–3, project suite per-tag case; `checks/shared_helper_overreach.patch` (functional_fail) |
| R | throw/crash on a URL-animating element | yes — mocha records an error, not a pass; `checks/crash_on_url_animation.patch` (security_fail) |

### 2b. Per trap (manifest.traps)

| trap | most plausible WRONG fix | caught by |
|---|---|---|
| trap_smil_retargeting | split only `values` and scheme-check entries | yes — smil 3–5 (from/to/by, set), smil 9; `smil_values_only.patch` |
| trap_smil_retargeting | refuse the whole animation feature | yes — animation_preservation 1–2; `overbroad_animation.patch` |
| trap_smil_retargeting | check the animation element's own URL attributes | yes — smil 1–2; `wrong_object_animation.patch` |
| trap_refresh_destination | `;url=`-only parser | yes — meta 3; `meta_classic_only.patch` |
| trap_refresh_destination | global list instead of `meta`'s policy | yes — meta 5 |
| trap_per_element_policy | union global + per-tag | yes — per_element 1–3, list_scheme 1–3; `union_kept.patch` |
| trap_srcset_policy_context | keep passing the attribute name to the policy | yes — per_element 3, list_scheme 2–3; `srcset_key_kept.patch` |

Catalogue: `refuse_all`=overbroad_animation, `crash_as_refusal`=crash_on_url_animation,
`wrong_resource`=wrong_object_animation, `unlisted_route`=union_kept,
`malformed_identity`=meta_classic_only, `adjacent_api`=shared_helper_overreach — all caught.
`one_role_or_direction`, `reads_only`, `check_after_adjustment`, `missing_authority` are genuinely
n/a for a pure string transformer with one policy path; `hardening`/`alt_fix` pass, showing a second
valid layer (per-attribute filtering) and a second refresh parser also score 1.0.

### 2c. Wrong fixes no test catches

1. **javascript-only blacklist in animations.** Every SMIL security payload uses `javascript:`; no
   test animates a `data:`/other forbidden scheme, or a permitted non-http destination.
2. **Hard-coded href/src targets.** No test animates a URL attribute that is URL-bearing only
   because the caller added it to `allowedSchemesAppliedToAttributes` (e.g. `poster`), so ignoring
   that option passes.
3. **Exact attribute keys.** With `parser.lowerCaseAttributeNames:false`, `attributeName`/`values`
   keys are camelCase; a fix keyed on the exact lowercase keys passes every test but misses that
   real residual route.
4. **Other list-valued URL attributes.** `ping`/`archive` are still checked as one flat URL at the
   pin; a fix that only handles `srcset`/`imagesrcset`/`values` passes, although G1's "one of
   several destinations inside a list value" covers them. Real unmodified upstream route — realistic,
   not "beyond the advisory".
5. **Over-broad animation rejection.** No functional test animates a *permitted* URL destination
   (e.g. `<animate attributeName="href" values="#safe;https://example.com/">`), so dropping every
   URL-targeting animation passes although C says permitted destinations keep working. The
   reference fix itself rejects on the target, not the value.
6. **Refresh quoting gap.** Variants cover `url = javascript:` unquoted and `url="javascript:"`, but
   not `url = "javascript:"` combined; a parser handling one but not both passes.
7. **Whole-`srcset` drop on one bad entry** is caught by the frozen project-suite case
   ("should drop bogus srcset") — noted so the gap list stays honest.

## 3. Hints (QUALITY, non-blocking)

| quote | why it is a hint | neutral rewording |
|---|---|---|
| "so the rendered link can be made to navigate to it when the animation runs" | explains the deferred-copy mechanism beyond the observed output | end the sentence at "still present" |
| "Fix the reported problem and its close variants rather than the one example" | announces a hidden variant family | "Fix the underlying problem generally, not only the reported input." |
| "The example is an example, not the full set." | discloses that further flaws exist (flaw count) | delete |
| "do not … remove features to make the example disappear; … do not special-case the example" | names the fix approach | "Do not weaken the allowlists or remove features." (the allowlist/feature clause is a contract; keep it) |
| "Where the configuration names a per-element scheme list, that list is the complete policy for that element; the global list does not widen it." | states the precedence semantics that trap C violates | keep — it is a product contract required for G3's tests to be derivable (the repo's own per-tag test also pins it) |
| "whether that URL is an attribute value, one of several destinations inside a list value, or a destination that the browser derives, copies or loads after sanitization" | enumerates destination forms | keep — this is the single general property over the protected outcome, not a route list |
| "The policy options are `allowedSchemes` … `allowedSchemesAppliedToAttributes` …" | public API option names | keep — contract vocabulary the tests configure |

## 3a. Required: generalize

**none.** The only concrete route is the reported SMIL example, which is the report itself, not a
sibling/far/uncovered route. The destination-form sentence is the one general property over the
protected data/outcome (kept deliberately), and no general word is also the name of one stage or
entry point. Nothing was written only to cover a trap.

## 4. Realism (QUALITY, non-blocking)

- **SMIL (A)**: real, unmodified upstream code at the pin; the deferred copy after sanitization is a
  natural maintainer blind spot, reachable via the public `sanitizeHtml` with SVG tags allowed.
- **Refresh (B)**: real, unmodified upstream code where the protection never existed; reachable;
  the dismissal "`content` is not a URL attribute" is a natural maintainer judgement. Realistic by
  definition, not "out of scope".
- **srcset/imagesrcset (C2)**: real, unmodified upstream; passing the attribute name where the
  element name belongs is a classic maintainer slip.
- **Injected per-element union (C)**: a plausible "merge the two documented lists" refactor that
  passes the project's own suite (which only pins non-overlapping/empty cases), reachable through
  every element. The injected comment's additive reading is defensible; not contrived.
- Harness: real public entry point, frozen upstream suite, no synthetic wrapper. The tests assert
  the forbidden destination is not emitted, not that a browser executes it — consistent with the
  instruction's guarantee and the builder's stated browser-semantics caveat.
- Minor: `smil_animation` test 9 spells `allowedTags` camelCase; if allowlist matching is exact and
  the parser lowercases, the elements are dropped as disallowed and the case proves little. Verify
  the animation elements are actually emitted in the oracle output.

## Verdict

**Gate a: READY.** G1–G3 read literally cover every route the security suite drives: direct
attribute values, `srcset`/`imagesrcset`/`values` list entries, destinations the browser copies
(SMIL) or derives (refresh), and per-element completeness. The natural correct fix following the
stated mechanism — judge every emitted destination against the element's own policy — passes all
20 security and 258 functional cases. Refusal form is free (R), and guards at the tag-skip
decision, the attribute loop or a post-parse filter all pass. The functional group pins only
today's permitted output, which a correct fix preserves.

Judgment points, both resolved for READY: the refresh route is never named and rests on standard
HTML refresh parsing (comma/space/bare forms); and the case/whitespace target test assumes a
malformed `attributeName` still carries an emitted destination list, which G1/G2 forbid regardless.
Neither makes a correct fix fail.

**Required: generalize** — none.

**Quality to tighten**
- Add a SMIL case with a non-`javascript:` forbidden scheme and a permitted-destination animation
  (`values="#safe;https://example.com/"` must survive); add a target supplied only via
  `allowedSchemesAppliedToAttributes` (e.g. `poster`); add a `lowerCaseAttributeNames:false`
  animation case. These are currently uncaught.
- Add a `ping`/`archive` list case (G1 covers it) and a `0; url = "javascript:…"` refresh variant.
- Verify test 9's camelCase allowlists actually emit the animation elements; use canonical names.
- Neutralise the four hint rows; keep the contract and property sentences.

Human review: confirm the refresh route (never named) is fair on "standard expert knowledge" of the
HTML refresh steps including bare/no-`url=` forms, and that a case/whitespace-sensitive target
matcher is correctly counted as incomplete rather than as a correct fix failed by
`smil_animation` "another case or with whitespace".

GATE_A: READY
NEEDS_HUMAN_REVIEW: YES
