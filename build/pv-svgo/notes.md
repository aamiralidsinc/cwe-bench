# pv-svgo build notes

- Start (UTC): 2026-10-23T03:16:43Z (from `start_utc.txt`)
- End (UTC): 2026-10-23T04:04:17Z (build stopped here; blind patch and FAIRNESS.md are post-build)

## Candidate and pinned tree

- Advisory GHSA-4VPR-X523-8J87 / CVE-2026-84369 (svgo, CWE-79, denylist-based SVG/HTML sanitisation).
- The screener said "parent of 0557385" (the v2 backport) but described the **v3** tree (svgo 3.3.4,
  the plugin at `plugins/removeScriptElement.js` with the event loop at 90-94 and the anchor branch at
  106-133). The v3 parent is `72a23886b4698b27624b936f3a15a80afd36d75f`; it matches every line
  reference in the screener and is the parent of the v3 fix `994a9f00d79ddec68ce19a1ce9eb8ca08d747e4f`.
  The task uses that tree and that fix commit. The v2 backport (0557385) adds far more than v3
  (v2 had no event or link handling at all), and v4 (fd51e47) is ESM with a renamed plugin.
- `solution/fix.patch` = the v3 fix reduced to source (`lib/svgo/tools.js`, `plugins/removeScriptElement.js`)
  plus the task's extra fixes (`lib/xast.js` traversal; general `on*` handling; mixed-case element
  matching; animation elements that apply an executable URL).

## Levers (one line each)

1. **traversal** (injected sibling, how-type, input withheld): the shared walker stopped descending into
   `foreignObject`, so the sanitiser never sees embedded HTML; `lib/xast.js:64-76`. Dismissal: the
   plugin code looks complete and the walker is core code assumed correct. Fix must restore traversal.
2. **animation** (pattern B, how-type, protection never existed): `set`/`animate` can assign an executable
   URL to `href`; `plugins/removeScriptElement.js:96-133`. Dismissal: link handling is written for static
   attributes, animation reads as another feature, browser support feels unclear. Still open upstream.
3. **event_denylist** (pattern B): handlers outside the fixed SVG 1.1 groups survive on SVG elements;
   `plugins/removeScriptElement.js:90-94` + `plugins/_collections.js:125-163`. Dismissal: the docs scope
   the feature to "SVG event attributes" and the list looks complete.
4. **case_folding** (pattern B, parser differential): mixed-case handler and element names skip exact-case
   checks; `plugins/removeScriptElement.js:90-94,31-47`. Dismissal: XML is case-sensitive, so exact-case
   reads as correct — but the markup is case-folded when the SVG is embedded in HTML.
5. **data_media_types** (pattern A far value + coupled value): executable `data:` media types and legacy
   `vbscript:` are navigable; `plugins/removeScriptElement.js:106-133`, `lib/svgo/tools.js:160-171`.
   Dismissal: "only `javascript:` is dangerous"; stripping all `data:` would break inert images, which the
   functional suite protects.
6. **namespace_prefixes** (pattern A, second element match): prefixed anchors and embedded-document
   elements are the same executable elements; `plugins/removeScriptElement.js:106-108,31-47`. Dismissal:
   unusual spelling; the tree already resolves prefixes for `script`, which makes the gap look solved.

## Candidate sibling sites considered (full list) and why the picks beat them

Searched the whole pinned tree for a second implementation of the guarded operation
(`javascript`/`srcdoc`/`foreignObject`/event lists), and for any module reachable from
`optimize(svg, {plugins:['removeScriptElement']})`:

| candidate | mechanism | reachable | security-observable | verdict |
|---|---|---|---|---|
| `lib/xast.js visit()` skip foreignObject subtree | withholds the nodes the check consumes | yes | yes | **picked (traversal)** — how-type, untouched by the fix, passes the whole project suite, realistic next to the existing per-plugin skips |
| `plugins/removeScriptElement.js` animation route | feature that never had a check | yes | yes | **picked (animation)** — real unmodified upstream code, still open in upstream main |
| `plugin event list` (`_collections` groups) | incomplete denylist data | yes | yes | **picked (event_denylist)** — real upstream, different dismissal reason |
| exact-case element/attribute matching | parser differential | yes | yes | **picked (case_folding)** |
| `lib/svgo/tools.js hasScripts` second `javascript:` copy | duplicate check in another file | yes | **no** | rejected as a lever: it only gates deoptimisation in other plugins, never removes output. Updated by the reference fix for consistency; listed under out_of_scope. |
| `detachNodeFromParent` (xast) | could be made to fail | yes | contrived | rejected: no plausible maintainer change that fails only for embedded content |
| parser/stringifier attribute rewriting | re-introduce after the check | yes | no plausible | rejected: neither module synthesises attributes; any change was artificial |
| `plugins/_collections.js` unused HTML event group | dead data | yes | same concept as event_denylist | rejected: "more routes of one concept", and a prefix test would make the group irrelevant |
| a second sanitiser plugin (v4 alias `removeScripts`) | planted copy | only if the tests name the alias | where-type | rejected: tests would have to name the extra plugin, which points at the sibling |
| `preset-default`-plugin gap (e.g. `removeUnknownsAndDefaults`) | neighbour plugin | only if the entry point runs preset-default | no | rejected: would change default behaviour and the project fixtures, and the sibling would be invisible with the named entry point |

Only ONE injected sibling met the bar. The rest of the difficulty is real upstream route coverage, so the
task ships one injected gap (the traversal) plus five real levers. `pattern: A+B` still holds: A is the
published fix's far value set / second element match, B is the uncovered routes.

## Security property (written before choosing routes)

"When script removal is enabled, the optimised document must not cause a browser to execute code when it
renders it. For every element and attribute the browser acts on — however it is named, spelled, or nested —
the output must contain: no executable code, whether bound to an element or carried in an element; no
embedded active document; and no executable URL in an attribute. Hostile input must still produce output."
Each route and the injected sibling falls under those three clauses without being named.

## What was verified

- The pinned tree reproduces every route through `optimize(svg, {plugins:['removeScriptElement']})`:
  embedded-HTML handlers/srcdoc/URLs, data:/vbscript:/tab-folded links, prefixed anchors, unlisted and
  mixed-case handlers, animation values, mixed-case script.
- Hidden suites against the vulnerable tree: **0/25 security pass, 9/9 functional pass**.
- Against the reference fix: **25/25 security, 9/9 functional**.
- Project suites: 13 suites / 425 tests (422 passed, 3 skipped) at the pinned tree, in the built image,
  and after the reference fix.
- Every `checks/*.patch` was applied to a fresh copy of the vulnerable tree and re-run through the same
  suites: each `security_fail` leaves only its own lever's tests failing with all functional passing;
  `strip_everything` breaks 5 functional tests; `broaden_has_scripts` breaks the project plugin fixtures;
  `hardening` and `alt_design` score 25/25 + 9/9.
- `alt_design` is an independent implementation (single recursive root walk, its own URL/data-type and
  namespace resolution) and passes, so the tests do not encode the reference's shape.

## Pattern B register rows

Added to `build/audit/uncovered-routes.tsv` for: `animation`, `event_denylist`, `case_folding`,
`mixed_case_script`, and the injected `traversal` (real_upstream=no). Current upstream main (v4.1.0,
`plugins/removeScripts.js`) was read read-only and still has all four real routes: event list is exact,
element match is exact-case, and no animation handling.

## What could not be verified

- Whether a current browser still executes a `javascript:` URL assigned by SVG `set`/`animate` was not
  checked (no browser here). The task asserts the optimiser's output, not browser behaviour.
- The mixed-case routes rely on the documented HTML case-folding when the SVG is embedded in HTML; that
  was not exercised in a browser either.
- `repo_mb` was not measured by the screener; the source tree is ~5.8 MB.
- The blind pass patch and `FAIRNESS.md` are written after this build (per the brief); static therefore
  reports only `checks/blind.patch` missing.

## Gate (run one stage at a time, in order)

- `--only static`: **FAIL (task) with exactly one problem: `patch check file missing: checks/blind.patch`.**
  Every other static check passes: required files, metadata, canary GUIDs, conformance, no instruction
  leaks, no hidden-test content in the image, no exact-status assertions, wrong-fix catalogue complete.
  The blind patch is written after this build, as the brief directs.
- `--only nop`: **PASSED**. On the untouched vulnerable tree all 25 security tests fail with real
  "attack survived" assertions (not load errors) and all 9 functional tests pass, including the project's
  325 plugin fixtures and the library tests.
- `--only oracle`: **PASSED**. Three runs, reward 1.0 each, identical results.
- `--only patches`: **PASSED** for all 11 existing checks. The manifest lists `blind.patch` as the twelfth
  (kind `blind`); to run the patches stage before that file exists, the blind entry was removed from
  `patch_checks` for this run and restored immediately afterwards. The final manifest lists all twelve.

The full gate will print PASSED once `checks/blind.patch` is supplied. Nothing else is outstanding.

