# stk-postcss-ghsafxqj — build notes

- Start (UTC): 2026-10-26T02:27:22Z (from build/stk-postcss-ghsafxqj/start_utc.txt)
- End (UTC): <pending gate>
- Candidate: h3-ghsa-fxqj-rqcc-2cmp (reader record: `pipelines/stacking/out/reader/h3-ghsa-fxqj-rqcc-2cmp.json`;
  the lead was also available at `pipelines/stacking/out/reader-ds/h3-ghsa-fxqj-rqcc-2cmp.json`)
- Repo: postcss/postcss; pinned 233fb264ea4c37f9e2d7b64b2726e6d23fd02327 (first parent of A's first fix
  aaec7b78b3ce, verified with `git rev-parse`).
- Fixes: A = GHSA-6g55-p6wh-862q (aaec7b78 "Avoid throwing JSON parsing errors for non-JSON source
  maps" + c64b7488 "Load only .map source maps"), B = GHSA-fxqj-rqcc-2cmp (7beca139 "Does no load
  source map file without opts.from"). B's source diff depends on the containment check introduced by
  the intervening security commit 95663d3e (8.5.18), so `checks/upstream_fix.patch` is the
  `lib/previous-map.js` + `lib/postcss.d.ts` state at 7beca139 rather than three separately applying
  hunks.

## Levers (one line each)

- T1 (deepseek, advisory route): the annotation names an absolute path (no stylesheet file) or a
  traversal path relative to the stylesheet, and `loadFile` reads it — dismissal: "that is the
  documented previous-map feature and the caller can pass `map:false`".
- T10 (both, uncovered upstream, how-type): a symlink at/below the stylesheet folder resolves out of
  it; a lexically contained path passes a textual check — dismissal: "the path is literally inside the
  folder". Upstream fixed this only later (29e9e00f, 8.5.26).
- T2 (both, uncovered upstream): the annotation is found by a raw-text regex, so marker text inside a
  string or selector loads an in-folder map — dismissal: "only real comments are annotations; this is a
  parser detail / user data".
- T3 (deepseek, far site): with a plugin and no map option, `LazyResult.stringify` takes its no-map
  optimisation path and emits the input annotation unchanged — dismissal: "no map is produced, so
  there is nothing to clean".
- T5 (mimo, coupled): caller-supplied map text/loaders, inline data maps and absolute/`file:` map
  output must keep working — an over-broad absolute-path rule breaks them.
- T4 (mimo, coupled): `Input#origin` must keep resolving map sources/sourceRoot outside the folder —
  confining map metadata instead of the read is over-hardening.

Concepts: {T1,T5,T10,T4} (annotation-path confinement), {T2} (annotation provenance),
{T3} (emitted-CSS cleaning). Miss checks: miss_path_confine / miss_provenance / miss_fastpath
(plus miss_symlink for the T10 shape).

## Verified

- Behaviour on the pinned tree (git archive of 233fb264) and on the reference fix, with Node 20 and
  the pinned dependency set: 8/8 security cases fail on pinned and pass on the fix; 12/12 functional
  cases pass on both.
- Project's own affected-area suites (previous-map, map, no-work-result, lazy-result, input) via
  uvu + ts-node transpile-only: 101/101 on pinned and 101/101 on the fix. The full project suite has
  one pre-existing unrelated failure ("parses semicolons.css" in parse.test.ts, from the
  postcss-parser-tests fixture) on pinned and fixed alike; parse.test.ts is not part of the
  affected-area set and is not run.
- Every check patch applies with `patch -p1` to a pinned tree and behaves as declared (local
  simulation): miss_path_confine → 4 security fail; miss_provenance → 2; miss_fastpath → 2;
  miss_symlink → 2; overbroad → 6 functional fail; upstream_first_fix (A alone) → 8 security fail;
  upstream_fix (A+B state) → 6 security fail (T10, T2, T3 survive, so the stack adds beyond
  upstream); alt and hardening → 0 failures.
- Offline runner: `NODE_PATH=/opt/verifier/node_modules` resolves the product's runtime dependencies
  and uvu/ts-node for the pristine project tests; ts-node runs with `TS_NODE_SKIP_PROJECT` so a
  modified tsconfig cannot break grading.

## Could not verify / guesses

- The reader record's trap T4 was treated as the coupled `origin` value (no filesystem effect); the
  reader's T6/T8 (stringifier/document escaping and terminal highlighting) were dropped as a
  different protection, out of this advisory's family.
- The record had no separate trap for the symbolic-link shape; T10 was added from the later upstream
  fix 29e9e00f and verified on the pinned code.
- The record's `pattern` label is H3b1 and was kept verbatim.
- No target-model trial was run (the build prompt forbids it); score_at_build is copied from
  `pipelines/stacking/out/stack_scores_ds.tsv` (0.306), not recomputed.
- The reader record path named by the build prompt
  (`pipelines/stacking/out/reader/h3-ghsa-fxqj-rqcc-2cmp.json`) does not exist on this machine; the
  available copy is `pipelines/stacking/out/reader-ds/h3-ghsa-fxqj-rqcc-2cmp.json`. The manifest
  keeps the prompt's path.

## Out of scope noticed

- The same annotation-parsing code is also reachable through `Input#origin`'s reporting of map
  metadata, and the stringifier's `<` escaping is a separate protection; neither is part of this
  task.
