# stk-fast-xml-parser-ghsa8gc5 — build notes

- Start (UTC): 2026-10-26T12:18:29Z
- End (UTC): pending gate
- Pinned commit: `fe9a85270122036ae22637167ce38a5f71b73a5f` (parent of the first published fix)
- Published fixes: `910dae5be2de` (A, GHSA-jmr7-xgp7-cmfj / CVE-2026-26278) and
  `bd26122c838e` (B, GHSA-8gc5-j5rx-235r, incomplete-fix advisory)
- Track: stacked H3a. Control: `stk-fast-xml-parser-ghsa8gc5-control`.

## Design substitution (read this first)

The build prompt's embedded "screener record" and the reader record at
`pipelines/stacking/out/reader/h3-ghsa-8gc5-j5rx-235r.json` do not agree, and the lead's plan
(`T1, T3, T5, T6`) is expressed in the screener record's ids. I verified the screener's mechanisms
on the pinned tree and against the two published commits before building:

- Screener T1 ("DOCTYPE values containing '&' must be made resolution-aware"): the guard at
  `src/xmlparser/DocTypeReader.js:28` already drops every value containing '&', which is the only
  way a value can contain a reference; no amplification route remains. The published fix does not
  change that line. Not usable as a security lever.
- Screener T6 ("second implementation in src/v6"): `src/v6/XmlSpecialTagsReader.js:85-111` reads
  `source` and `text` that are not defined in scope, and `src/v6/EntitiesParser.js:70-74` reads an
  undefined `ent`; v6 doctype and external entity registration throw before expansion. The
  `src/fxp.js` entry never imports v6. Not reachable; excluded.
- Screener T3/T5 (public `addEntity` route and replacement-pattern values) do correspond to real
  code. They are kept, with the mechanisms as they actually exist (external values bypass the
  growth bound; a declared value is used as a `String.replace` replacement string).

The reader record itself is marked `usable: false` (it sees T3/T5 collapsing into one counter and
asks for three independent protections). I built the three concepts the actual fix history and the
code support, and proved their independence with one `miss_*` check each:

1. concept `expansion` (`T1` advisory anchor, `T5` MiMo shape): bound DOCTYPE replacement by count
   and by total growth, with safe defaults; a count-only budget passes `T5`.
2. concept `all-kinds` (`T2`): the same substitution through the predefined and HTML/numeric tables
   must obey the configured reference limit. This is exactly what B added after A left it open.
3. concept `external` (`T3`): a value registered by the caller is counted but its growth is not
   bounded; the output bound must cover that table (or the value must be size-checked at
   registration). Neither published fix closes this, so `checks/upstream_fix.patch` fails.

## Levers (one line each)

- T1 (advisory_route, both): a DOCTYPE entity with no '&' in its value, referenced 2000× in text or
  an attribute, expands to 10 MB with no bound — `src/xmlparser/OrderedObjParser.js:439-458`.
- T5 (advisory_route, mimo): a declared value `$'` (no '&') is a `String.replace` replacement
  pattern and duplicates surrounding text; 900 references grow ~10 MB while a count-only budget
  allows them; only a growth bound (or a literal replacement) closes it —
  `src/xmlparser/OrderedObjParser.js:444`.
- T2 (published_fix_far_site, deepseek): numeric and predefined references run in the same
  substition path but outside the DOCTYPE budget; with `maxTotalExpansions: 20`, 40 references
  still expand — `src/xmlparser/OrderedObjParser.js:446-456`.
- T3 (uncovered_upstream, deepseek): a 200 KB value registered by the caller, referenced 50×,
  yields 10 MB; the count bound is satisfied and the growth bound is never applied — 
  `src/xmlparser/OrderedObjParser.js:446-449`, `src/xmlparser/XMLParser.js:46-56`.

Reason to dismiss, in one phrase each: the reported document route looks like the whole attack
(T2's other tables look like single-character substitutions); a value with no '&' looks inert
(T5); a value supplied by the embedding application looks trusted (T3).

## Verified

- Pinned tree: security suite 6/6 fail; functional suite 293 pass (289 project specs + 4 more, one
  project spec is `xit` and is not scored); project specs 289/0.
- Reference (`solution/fix.patch`): security 6/6 pass, functional 293/0.
- A alone: security fails 3 (numeric, predefined, caller-registered), functional 293/0.
- A+B (`upstream_fix.patch`): security fails exactly the caller-registered value test; functional
  293/0.
- `miss_expansion`: security fails T1's two tests and T5's one (the count bound is still met at 900 references while growth is unbounded), functional 293/0.
- `miss_allkinds`: security fails T2's two tests, functional 293/0.
- `miss_external`: security fails T3's test, functional 293/0.
- `miss_shape`: security fails only T5's test, functional 293/0.
- `functional_fail` (rejects values containing `$`): security 6/6 pass, functional fails 1.
- `refuse_all` (rejects every DOCTYPE): security 6/6 pass, functional fails 17 — catalogue
  `refuse_all`.
- `alt_correct_fix` (single post-pass budget design): all 6 + 293 pass.
- A second alternative that inserts declared values literally (`String.replace` with a function)
accepted for T5's shape: it prevents the growth rather than bounding it; T5's test accepts a
refusal or a proportionate result for that one shape.
- `hardening` (oracle + entity-count cap + null-prototype map + name guard): all pass.
- Control: pinned security 4/4 fail, functional 293/0; fix A security 4/4 pass, functional 293/0.

## Could not verify / unknowns

- The two published commits were applied as their own source diffs. An intermediate upstream commit
  `3abdca9` (2026-03-03, "support maxEntityCount") is an ancestor of B but is not one of the two
  published fix commits; it is not in `checks/upstream_fix.patch`. It would close an additional
  (not scored) declaration-count route if included.
- Whether current upstream (`@nodable/entities`, from `169fbf9`) still applies a growth bound to
  values registered through the public API: not checked; `present_in_latest` for T3 is `unknown`.
- The prebuilt `lib/fxp.cjs` bundle in the pinned tree contains the old code and is not regenerated
  by the published fixes. The tests use the package's ESM entry (`src/fxp.js`, the `module` and
  `exports.import` target, and the entry the project's own specs use). A submission that edits only
  the generated bundle is not exercised by the tests.
- `T2` has no amplification (numeric references contract or stay one character); its test therefore
  uses the report's configured limit (`maxTotalExpansions: 20`) rather than a size bound. This is
  the one policy-shaped lever; the report states the limit applies to every reference.

## Fairness notes

- The instruction states the configuration contract by its two public field names only
  (`processEntities.maxTotalExpansions`, `processEntities.maxExpandedLength`); it does not name a
  table, reference form, or registration API.
- The documented chained-substitution example (`&writer;&&nbsp;&copyright;`) is a functional test;
  a single-pass or no-re-expansion fix fails it.
- Numeric/hex references, out-of-range references, `processEntities: false`, caller overrides of a
  built-in entity, and a value containing a literal `$` are all functional tests.
- The control's `instruction.md` is byte-identical to the stacked task's, as rule 13 requires.

## Register rows

Added to `build/audit/uncovered-routes.tsv`: T2 (predefined/HTML tables; fixed by B) and T3
(caller-registered values; not fixed by A or B).
