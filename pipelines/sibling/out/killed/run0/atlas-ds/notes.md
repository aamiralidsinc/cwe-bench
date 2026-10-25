# atlas-ds build notes

- Start UTC: 2026-10-24T02:30Z
- Slug: atlas-ds. Pattern A+B. Track: injected.
- Advisory: GHSA-V73P-F52R-FMMR / CVE-2025-62198, apache/atlas, CWE-80/79 (UI XSS).
- Pinned vulnerable commit: e67cc199e61afc92f242cccd05e97a61e0791bd2
- Published fix commit: 800f979307d6ea0f0b6563ec890f6b728022e497

## Product / mechanism (one line)
Atlas has two browser UIs (React `dashboard/` and legacy Backbone `dashboardv2/`); values that a user
stores or supplies (business-metadata strings, attribute values, display names, references, session
user name) are concatenated into HTML/inserted with `dangerouslySetInnerHTML` or jQuery `.html()` at a
number of independent sinks, so a value carrying markup runs in the viewer's session.

## Security property (once, general)
No value a user can supply, and no value stored in the repository, may execute code or run an event
handler when the Atlas web interface displays it — whatever the value is called, wherever the
interface displays it, and whatever shape it has. A fixed harmless formatting set (b/em/strong/u/ul/
ol/li/p/strike/h1-h4 and http/https/mailto links) keeps rendering; everything else appears as text.
Rendering must not fail or change legitimate display.

## Levers (one line each)
- R0 (reported landing, published-fix site): React `HtmlRenderer` puts the business-metadata string
  straight into `dangerouslySetInnerHTML`. No dismissal (this is the report's example).
- R1 (A far site / SECOND IMPLEMENTATION, published-fix): legacy `Header.onRender` writes the
  signed-in user's name from the session response with jQuery `.html()`. Dismiss: legacy UI, and a
  user name is "identity-provider data", not attacker data.
- R2 (B route, REAL upstream, protection never existed -> HOW): lineage node tooltip builds d3-tip
  HTML by concatenating `toolTipLabel` (entity displayText), `typeName` and `queryText`
  (`dashboard/src/views/Lineage/atlas-lineage/src/index.js:553-565`). Dismiss: vendored lineage
  sub-library, tooltip is behind an optional node-details toggle; the published fix touched that
  file only for a legends refactor.
- R3 (B route, REAL upstream, shape -> HOW): legacy `propertyTable`/`extractObject` concatenates the
  reference id into `href`/`data-id` without escaping
  (`dashboardv2/public/js/utils/CommonViewFunction.js:239,242,244`). Dismiss: "ids are server GUIDs".
  The shape: a struct/map attribute whose `id`/`guid` field is free text, so it is not a GUID.
- J1 (INJECTED, HOW): `JSONPrettyPrint` in `dashboard/src/utils/CommonViewFunction.ts` was refactored
  to escape values inside the per-line replacer while the global escape chain was dropped, so object
  keys/lines the line regex does not match pass through raw. Dismiss: "JSON values are escaped and
  keys are just labels". Untouched file.
- J2 (INJECTED, shape): `GetArrayValue` in `dashboard/src/components/commonComponents.tsx` renders a
  list of primitive values by joining them into an HTML string with `dangerouslySetInnerHTML`
  instead of React text nodes. Dismiss: "React text nodes already escape; HtmlRenderer covers HTML".
  Untouched component (the published fix touches a different branch of the same file).

## Injected siblings: full candidate list and why the picks won
Candidates examined (screener O8/O8b plus own search):
1. `dashboard/src/views/Lineage/atlas-lineage/src/index.js:537-569` d3-tip .html() — REAL upstream;
   picked as R2 (B route, not injected).
2. `dashboardv2/public/js/external_lib/atlas-lineage/src/index.js:513-518` — rejected: the legacy app
   ships the prebuilt dist bundle (`dashboardv2/public/js/main.js:159`), so editing the source cannot
   protect the served app; not a fair route.
3. `dashboardv2/public/js/utils/CommonViewFunction.js:155-166` soft-reference error branch raw id —
   examined; the fetch branch only runs when the escaped display name equals the raw id, so the raw
   id can carry no markup there; NOT used.
4. `dashboardv2/public/js/utils/CommonViewFunction.js:239-244` raw id in href/data-id — REAL upstream;
   picked as R3 (B route).
5. `SearchLayoutView.js:575` service names — out of this advisory's protected data; not pursued.
6. `BusinessMetadataTab.tsx:87-93` "truncate after sanitize" — examined; sanitize-html output cannot
   become executable by truncation, so not exploitable; not injected.
7. `BMAttributes.tsx` array<string> raw join (O8b) — plausible but the component needs the full
   redux/router/form stack to drive through a real entry; replaced by J2 in the same value shape,
   which is a real exported component on the same properties-table path.
8. `JSONPrettyPrint` key parser differential (O8b) — picked as J1: how-type, untouched file, reachable
   through the object-attribute path of the properties table.
9. `ShowMoreText` caller passing raw HTML — rejected: the only callers sanitize at the pin, so it is
   not a real route; its published fix is included in the oracle as defence-in-depth only.
10. `CommonViewFunction.generateQueryOfFilter` conditions — examined; `extractUrl` normalises every
    condition to AND/OR before it reaches the sink, so it is NOT exploitable at the pin; not used.
Picks: R2, R3 (real B routes) and J1, J2 (injected). Two injected siblings, each with a different
dismissal (label-vs-value escaping; list vs string shape), both reachable through the real
properties-table path, both in code the published fix never touches.

## Sites/routes and input shapes the security tests cover
- business-metadata string value on the entity Properties tab (R0);
- signed-in user name rendered by the legacy header (R1);
- entity display name / type / query text in the lineage tooltip (R2);
- struct/map attribute value carrying `id`/`guid`, legacy properties table (R3);
- object attribute keys in the pretty-printed value (J1);
- list-of-primitive attribute values in the properties table (J2).
Shapes: plain string, list element, structured object key, lazily-built reference value, session
string.

## Coupled must-keep-working behaviour
- allowed formatting (b/em/strong/u/ul/ol/li/p/h1-h4, a href http/https/mailto) still renders in
  HtmlRenderer and ShowMoreText, including after truncation;
- plain text and legitimate names containing `&`/quotes/`<` display identically;
- the lineage node label text and the tooltip text show the exact display name;
- legacy reference links keep working (href `#!/detailPage/<guid>`) and JSON pretty-print keeps its
  json-key/json-string span markup;
- list values display as `<value>, <value>`.

## Oracle
Published source fix reduced to source (HtmlRenderer sanitises; ShowMoreText sanitises its truncated
slice; ExtractObject escapes primitives; Utils gains escapeHtml + non-string coercion + scheme map;
legacy fetchInputOutputValue escapes id/value; Header uses .text()) plus fixes for R2, R3, J1, J2.
The `allowedSchemesByTag` and condition-escaping parts of the published diff are kept for
conformance even though they are not independently exploitable at the pin.

## Build/verifier approach
- React suites: vitest 2 + jsdom + @testing-library/react, real components imported from
  /workspace/dashboard/src through aliases; tsx is transpiled by esbuild (no tsc/vite build needed).
- Legacy + lineage suites: an AMD shim loads the real `dashboardv2` modules (real Utils/Enums/Globals,
  stubbed third-party globals), and the real LineageHelper + DataUtils with only the d3-tip renderer
  replaced by a capture stub; SVG jsdom gaps polyfilled; XHR stubbed.
- Verifier image pre-installs the pinned dashboard dependency tree plus the runner deps in
  /opt/atlasdeps; test.sh symlinks /workspace/dashboard/node_modules to it and copies the hidden
  suites into /workspace/dashboard/.htests at grade time.

## Verified before build (prototypes on the pinned tree)
- HtmlRenderer renders an attacker `<img onerror>` as a live element on the pinned tree.
- ShowMoreText renders raw HTML on the pinned tree (no reachable unsanitized caller).
- Legacy `Header.onRender` creates `<img onerror>` from the session user name on the pinned tree.
- Legacy `propertyTable` creates `<img onerror>` from a struct attribute `id` on the pinned tree.
- Lineage tooltip HTML (captured through the real LineageHelper + real DataUtils) contains the raw
  attacker displayText on the pinned tree; node label text is separately available.
- `JSONPrettyPrint` and `GetArrayValue` are safe on the pinned tree; their injected variants become
  the J1/J2 routes.

## Post-build verification
(to fill in: pinned/pinned+injected security fail counts, oracle pass counts, project test status,
check patches, gate stages)
