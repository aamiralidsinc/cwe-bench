# pv-apostrophe — build notes

Start: 2026-10-23T03:19:11Z (build/start_utc.txt)
End: 2026-10-23T04:15:00Z (approx; see gate_report.partial.json timestamps)

Candidate: apostrophecms/apostrophe, package `sanitize-html`; advisory
GHSA-g8qq-57p8-ggw5 / CVE-2026-84371 (CWE-79 stored XSS, URL scheme-policy
bypass by an HTML sanitizer; SVG SMIL animation retargeting).
Pinned commit: parent of 1135516a1a4a8f9638641c460488a43d8af20081 =
78e3e108ba9a5923c3099ad64a8c4c740a924da0 (verified with `git rev-list --parents`).
Published fix: 1135516a (4 files; source change only in
packages/sanitize-html/index.js). The second candidate commit (38ff1106) is a
release reconciliation and is not used.

## The protected outcome (property, written once)

> After sanitization, no URL in the output — as an attribute value, as one of
> several destinations in a list, or embedded in a value that the browser later
> turns into a destination — may have a scheme that the configuration does not
> permit for the element it is emitted on (including every per-element scheme
> override). Each destination is judged on its own.

Every tested lever falls under this sentence as written; the instruction does
not describe where any of them lives.

## Every candidate sibling site/route found (before choosing)

From the code at the pinned commit (packages/sanitize-html/index.js), the
screener's O8/O8b leads, and later upstream commits:

1. **SMIL animation retargeting** (reported; published fix). `attributeName` +
   `values`/`from`/`to`/`by` are copied into a URL attribute by the browser
   after sanitization. Site: onopentag skip decision + helper. HOW.
2. **`<meta http-equiv="refresh" content="...">` destination** (real, untouched
   at the pin; fixed later as GHSA-cv27-6wvh-8x7j). `content` is not in
   `allowedSchemesAppliedToAttributes`, and the URL is embedded after a
   time/separator (`0;url=…`, `0,…`, `0; …`), so no scheme check ever runs.
   HOW (route where protection never existed + separator grammar).
3. **Per-element scheme list merged with the global list** (injected, lever C).
   A memo/merge refactor makes `allowedSchemesByTag` additive instead of an
   override, so a scheme the element forbids is re-admitted (including a data:
   destination on a frame). HOW (merged/defaults route).
4. **`srcset`/`imagesrcset` per-element policy** (real, untouched at the pin;
   fixed later in PR #5576). The per-entry check passes the attribute name
   where the element name belongs, so a per-element override is ignored. HOW
   (wrong context identity). Coupled with lever C: only observable once the
   override is an override again.
5. `ping`/`archive` are list-valued URL attributes checked as one flat URL.
   Real code at the pin (still in latest). **Rejected**: a `javascript:` entry
   there is a fetch destination a browser does not execute, and upstream does
   not treat it as a vulnerability; testing it would impose a contract the
   product does not hold.
6. Attribute-name case with `lowerCaseAttributeNames:false` and a glob
   allowlist (screener O8). Real, still in latest. **Rejected**: pure
   spelling/parser-configuration variant (design forbids spelling variants as
   levers).
7. Namespace-prefixed animation element/`attributeName` key (`svg:animate`).
   Real later fix GHSA-374f-7chj-9948. **Rejected as a lever**: pure spelling
   variant; folded into the hardening "pass" patch only.
8. `<iframe srcdoc>` / `<foreignObject>` raw markup. **Rejected**: markup
   injection, not a URL-scheme sink; outside this advisory's protection.
9. CSS `url()` in `style`. **Rejected**: browsers do not execute `javascript:`
   from CSS `url()` in 2026.
10. `allowedIframeHostnames` / `allowedScriptHostnames` routes (IDN, relative
    URL bypass). **Rejected**: host allowlists, not scheme policy; separate
    advisories, outside scope.
11. Escape-mode animation output. **Rejected**: the payload becomes inert
    escaped text, so a `javascript:` substring check would wrongly fail the
    correct fix.
12. Per-call scheme-verdict memo keyed by element+attribute (an alternative
    injected candidate). **Rejected**: it breaks three tests in the project's
    own suite at the pinned commit (documents with more than one URL on the
    same element), so the image could not satisfy "project tests pass at the
    pinned commit".
13. Removing `background`/`poster` (or `action`/`formaction`/`data`/
    `xlink:href`) from the default checked-attribute list (the pre-2.17.5
    state, CVE-2026-53606). **Rejected**: the 2.17.5 attributes are covered by
    the project's own tests at the pin, so removing them breaks the suite; the
    remaining attributes are not executable sinks.

### Picks (hardest / most complex first)

- **Lever A (main, reported): SMIL retargeting.** HOW-type: needs the mechanism
  (a deferred copy into a live URL attribute, and `values` is a
  semicolon-separated list a flat check only partly reads) plus every value
  attribute, every animation element (including the parser's canonical SVG
  camelCase), and every scheme-checked target.
- **Lever B: refresh destination.** Protection never existed (reads as
  design), real untouched upstream code, far from the report (attribute loop),
  dismissal: "content is not a URL attribute and meta is not in the default
  tags".
- **Lever C (injected): per-element list merged with the global list.** Merged/
  defaults route, real XSS (data: frame source), dismissal: "the per-element
  list just adds schemes; the global list still applies". Passes the project's
  own suite at the pin.
- **Lever C2 (real, coupled): srcset per-element policy.** Dismissal: "srcset
  is already validated candidate by candidate". Only observable once C is
  fixed, so it adds depth to C rather than a separate search.

## Input shapes covered by the security tests

- A: `values="#safe;javascript:…"` with `values` added to the scheme-checked
  attributes; `values="javascript:…"` with the default policy; `from`; `to` on
  `<set>`; `by`; `attributeName="xlink:href"`; `attributeName=" HREF "`;
  `attributeName` targeting `src` on `<image>`; animateColor/animateMotion/
  animateTransform.
- B: `0;url=javascript:…`; `data:`; uppercase `URL=`; spaces around `=`;
  comma separator; `0 url=…`; quoted (`"`/`'`) destinations; `0;javascript:…`;
  `0;"javascript:…"`; `http-equiv` case and attribute order; a per-element
  override that denies the destination.
- C: a global list that would re-admit a scheme for a frame source, for an
  ordinary URL attribute and for a list value under a narrower per-element
  list.
- C2: an `img:['https']` override with an `http:` entry in `srcset`, the
  alternate list attribute, and an element that permits no scheme at all.

## Coupled must-keep-working behaviour (functional tests)

- A: animations of non-URL attributes (`fill`, `opacity`) survive; a
  non-animation element carrying `attributeName` keeps its own `href`.
- B: permitted, quoted, relative and destination-free refreshes survive;
  meta content that is not a navigation is untouched.
- C/C2: the documented per-element override keeps a permitted data URL and a
  permitted https source; permitted list destinations and relative list entries
  survive.
- Ordinary permitted/relative/protocol-relative URLs and several permitted
  URLs in one document are unchanged.
- The project's own suite at the pinned commit (241 mocha cases) runs as a
  functional group, so an over-broad fix fails.

## Injection (track: injected)

`environment/injection.patch` replaces the per-element scheme lookup in
`naughtyHref` with an additive merge of the global list and the per-element
list. It is reached through the public `sanitizeHtml(html, options)` entry
point, passes the project's own suite at the pinned commit, and lies in the
scheme helper, which the published fix never touches. The instruction states
the per-element semantic ("that list is the complete policy for that element")
as a product contract, so the bug is findable from the report and the code.

## Oracle and checks

- `solution/fix.patch`: published SMIL fix + refresh-destination parser +
  `naughtyHref(elementName, entry)` for srcset + the per-element override
  restored.
- checks: `smil_values_only` (security_fail, SMIL lever), `meta_classic_only`
  (security_fail, refresh lever), `union_kept` (security_fail, merged/defaults
  lever), `srcset_key_kept` (security_fail, list-policy lever),
  `overbroad_animation` (functional_fail, refuse-all), `crash_on_url_animation`
  (security_fail, crash-as-refusal), `wrong_object_animation` (security_fail,
  wrong object), `shared_helper_overreach` (functional_fail, adjacent API),
  `hardening` (pass), `alt_fix` (pass, filter-based animation handling and a
  different refresh parser).

## Gate results (this machine)

- static: only the deliberately missing `blind` pass patch (written after the
  build by another agent) and `FAIRNESS.md` remain; every other static check
  passes.
- nop: PASSED (all 20 security tests fail, all 258 functional tests pass).
- oracle: PASSED (3 identical runs, reward 1.0).
- patches: PASSED (all 10 declared behaviours).

## Verified at build time

- The flaw reproduces through `sanitizeHtml()` on the pinned (injected) tree
  for every lever; no exploitation steps are written out here.
- The project's own suite passes at the pin, with the injection, and with the
  oracle (241 passing each), and is part of the functional group.
- The pinned commit does not contain the advisory's regression tests (they are
  added by 1135516a: 172 lines in test/test.js).
- Both images build offline at test time (dependencies in /opt/app-deps; the
  verifier restores /workspace without node_modules).

## Could not verify

- Browser execution semantics of `javascript:` in a refresh destination
  (upstream treats it as a policy violation; the tests assert only that the
  forbidden destination is not emitted).
- Whether any downstream Apostrophe rich-text configuration allows SVG
  animation elements (the upstream changeset says Apostrophe was not affected).
- Target-model behaviour (trials are run by the pipeline, not by the builder).
