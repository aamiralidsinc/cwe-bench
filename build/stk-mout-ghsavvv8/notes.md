# stk-mout-ghsavvv8 — build notes

Start (UTC): 2026-10-26T12:23:48Z (build launcher) / 2026-10-26T12:24Z (this session)
End (UTC): see the last line of this file.

## Levers (one line each)

- T1 — A (published-fix far site): the fill-only deep copy recurses into the destination's inherited
  `Object.prototype` when a source owns a `__proto__` key; src/object/deepFillIn.js:15-23; reason to
  dismiss: the null-check makes the inherited slot look unfillable.
- T2 — A (advisory route): the recursive mix reads the destination's inherited `Object.prototype` as
  an existing child; src/object/deepMixIn.js:15,23-27; shown in the impact example.
- T3 — A+B (published-fix far site): the dotted-path setter coerces a non-string path after the
  raw-value scan, and its public namespace creator follows an inherited segment;
  src/object/set.js:7-12, src/object/namespace.js:8-14; reason to dismiss: caller-supplied paths
  look like a different feature and a `__proto__`-only guard leaves the inherited-name form open.
- T4 — B (uncovered upstream): the deleter walks through inherited `constructor`/`__proto__`
  segments onto `Object.prototype`; src/object/unset.js:7-14; readers get.js/has.js must keep their
  inherited semantics (coupled); reason to dismiss: read-only/delete-only looks outside a pollution
  advisory.

Concepts: C1 = [T1, T2] (own-key copy into a destination), C2 = [T3] (dotted-path writers),
C3 = [T4] (dotted-path deletion). Three independent protections; no single guard closes two.

## Verified (local, before the container gate)

- Every attack reproduces through the public AMD modules at the pinned commit: deepMixIn, deepFillIn,
  set (plain, `__proto__` and non-string paths), namespace, unset; 12/12 security cases fail on the
  pinned tree and pass on the reference fix.
- Functional suite: 9/9 pass on the pinned tree, on the reference fix and on every `pass` check.
- Project's own suite at the pinned commit: 1060 tests, 0 failures (also run in the image build).
- Every check patch reproduces its declared outcome locally:
  miss_concept_deepcopy 7/12 security; miss_concept_writers 7/12; miss_concept_unset 10/12 (all
  functional green in each); upstream_first_fix 2/12; upstream_fix 3/12 (functional green);
  functional_overbroad 7/9 functional; adjacent_api 8/9 functional; alt_correct_fix and hardening
  12/12 + 9/9.
- Control task runs the advisory route only: pinned 0/5 + 6/6, control fix 5/5 + 6/6,
  control_miss 0/5 + 6/6, control_overbroad 5/5 + 4/6, control_alt 5/5 + 6/6.

## Things that were not verifiable / guesses

- The advisories name deepFillIn/deepMixIn, but both published fix commits touch only
  `src/object/set.js` (A adds a raw-value substring guard; B stringifies the path first). The record
  inferred A=deepFillIn / B=deepMixIn; that inference is wrong. The task keeps the record's trap
  identities (T1 fill sibling, T2 reported mix, T3 set/namespace, T4 delete) and labels the origin
  of T3 as the published fix's far site, which is what the commits actually support.
- `stacking.reader_record` is written with the path the build prompt names
  (`pipelines/stacking/out/reader/...`); the record actually on disk is
  `pipelines/stacking/out/reader-ds/h3-ghsa-vvv8-xw5f-3f88.json`.
- Whether upstream ever intended to fix the deep-copy family: latest upstream (eac5db7) still has
  the unguarded deepMixIn, deepFillIn, namespace and unset code, so those are real uncovered routes.
- T2's `type` is recorded as "both" only because the static schema allows deepseek/mimo/both; the
  reader's tiers are easy/easy. T4 is the MiMo-type lever (hard/hard); T1/T3 are the DeepSeek-type
  levers.

## Scope

- Only the mout tree at the pinned commit, the two advisories' own protection (shared prototypes),
  this repository, and the build directories. Nothing outside that scope was used.
2026-10-26T12:37:45Z
