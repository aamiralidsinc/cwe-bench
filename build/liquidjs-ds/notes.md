# liquidjs-ds — build notes

Start: 2026-10-24T02:42Z (pipeline start); design/build begin 2026-10-24T03:00Z.
Repo: harttle/liquidjs. Pinned vulnerable commit: 8bfb6428ae7a1cb414a77acec30d26dfd28af9e2.
Published fix: 552819a84b80c62306fe61072628a756272dc749. Pattern A+B, injected track.

## Candidate (screener)

`build/liquidjs-ds/BUILD-PROMPT.md`, entry id 11212. Claim: with `ownPropertyOnly`
(default true), scope reads may return only own properties, but the negative-index branch of
`Context.readProperty`, the `first`/`last` magic keys, and the `first`/`last` filters bypass the
guard and surface prototype-inherited array indices.

## Verified at the pin (behavioural probe, jest, before any build)

Prototype pollution marker `Array.prototype[0..2]` + a sparse array `a = []; a.length = 3`:

- `{{ a[0] }}` blocked; `{{ a[-1] }}`, `{{ a[-2] }}`, `{{ a[-3] }}` leak (report target).
- `{{ a.first }}`, `{{ a.last }}` leak; on a plain object with `Object.prototype.first/last` they leak.
- `{{ a | first }}`, `{{ a | last }}` leak (separate module, second implementation).
- `{{ a | join }}`, `| compact | join`, `| concat | join`, `| slice | join`, `| sort | join`,
  `| reverse | join`, `| uniq | join`, `{{ a | json }}`, `{{ a | inspect }}`, `{{ a }}` leak
  (standard array operations read through the prototype; the published fix's
  `Array.prototype.X.call` rewrite does not change this — verified with plain node).
- `{% for %}`, `{% for ... reversed/limit/offset %}`, `{% tablerow %}`, `{% render ... for %}` leak.
- `{{ a | array_to_sentence_string }}` leaks.
- `{{ a.size }}` / `{{ o.size }}` leak when `Object.prototype.size` is polluted: `readSize` reads an
  inherited `size` before falling back to the structural size.
- `Context.getSync(['a',-1])`, `['a','first']`, `['a','last']` leak; `['a',0]` is already guarded.

Current upstream (origin/master 920166e3f, 10.30.0) still carries the same open routes:
`readArrayElement` is only applied at the three published sites; `toArray`/`toEnumerable`/
`stringify`, the filter transforms, `join`'s `Array.prototype.join.call`, the iteration tags,
`array_to_sentence_string`, `json`, and the `forloop` drop are unchanged. So the far routes are
`present_in_latest = yes`.

## General security property (written once, before routes)

While the own-property read restriction is in effect (its default), no value that exists only on
the prototype chain of data supplied to a render may be observable — neither in the rendered text
nor in a value the engine returns to a caller that resolves a path or expression — for any supplied
value and any way a template obtains or derives a value from it.

Every lever below falls under that sentence as written. The report never names a route beyond the
one concrete trigger.

## Levers

- **T1 (A, report target): negative numeric index.** `src/context/context.ts:128`. The resolver
  normalises a negative key to `length + key` and reads it raw. Dismiss: none, the report leads
  here; the HOW part is that the own check must run on the *normalised* index, or legitimate
  negative indexing on ordinary arrays breaks (functional test).
- **T2 (A far, second implementation + magic keys): end accessors and end filters.**
  `src/context/context.ts:133-152` (`first`/`last` magic keys, and the non-array object path) and
  `src/filters/array.ts:15-16` (`first`/`last` filters). Dismiss: the report shows index syntax,
  and the pinned docs say the restriction is "not a sandbox for filters"; these look like
  convenience accessors in another module. Shape: an object (not an array) with an inherited
  `first`/`last` is the same hole through a different branch.
- **T3 (B, HOW — producer off the sink's path): iteration.** `src/tags/for.ts:46-76`,
  `src/tags/tablerow.ts:42-56`, `src/tags/render.ts:72-79`. Dismiss: docs exclude tags. The HOW
  part: the `reversed`/`offset`/`limit` modifiers and `tablerow` copy the collection with
  `[...arr]` / `arr.slice(...)` *before* iterating; those operations turn inherited indices into
  own elements, so a per-element own check placed at the loop still leaks. The fix must sanitise
  before/at the copy (or at the read boundary).
- **T4 (B, HOW — a route where the protection never existed): filters and serialisation.**
  `src/filters/array.ts` (`join`, `compact`, `concat`, `slice`, `where`/`reject`, and the
  `toArray`-based filters `sort`/`map`/`sum`/`reverse`/`uniq`/`sample`), `src/util/underscore.ts:37-43`
  (`stringify`, direct output), `src/filters/misc.ts` (`json`, `inspect`),
  `src/filters/string.ts:210-222` (`array_to_sentence_string`). Dismiss: docs exclude filters;
  sequence-wide operations look like ordinary JS semantics. HOW: standard array methods read
  through the prototype, and spreads/slices materialise inherited slots.
- **T5 (B, HOW — coupled value + shape trap): the `size` convenience key.**
  `src/context/context.ts:154-158`. `readSize` accepts any inherited `size` before the structural
  size. Dismiss: `size` must keep working for Sets and Maps, whose `size` *is* a prototype getter,
  so a solver assumes the inherited lookup is deliberate; removing it wholesale breaks the coupled
  Set/Map contract (functional test). The correct fix distinguishes own `size`, structural length,
  built-in collection size, and own-key count, and keeps the mode-off behaviour. Upstream later
  made the same change on the v11 line (commit cd94bba73, "respect ownPropertyOnly for
  size/first/last magic keys"), confirming the gap.

## Injected siblings (our copy only; published fix never touches these files)

Candidates found in the source (O8/O8b + own search): `array_to_sentence_string` (real,
`filters/string.ts`); `stringify`/`toArray`/`toEnumerable` (real, `util/underscore.ts`); the
`for`/`tablerow`/`render` iteration tags and their copy helpers (real); `json`/`inspect` (real,
`filters/misc.ts`); `reverse`/spread transforms (real); `first`/`last` filter module (real,
published); a new element-reading filter in `filters/string.ts` or `filters/misc.ts`; a new window
filter (`take`) whose slice materialises inherited slots; a loop drop exposing the current item;
a `readSize`-style special key (real, T5); a `nth`/`at` filter. Chosen:

- **S1 — `at` filter (injected, `src/filters/misc.ts`).** A convenience index filter with the same
  negative-index normalisation, indexing the value directly. Dismiss: it is a new convenience
  filter in the misc module, not one of the named end filters. HOW: negative normalisation and the
  raw read.
- **S2 — `take` filter (injected, `src/filters/misc.ts`).** A window filter that copies with
  `slice` and returns the copy; after the copy the inherited values are *own* elements, so a sink
  that checks ownership of what it prints cannot detect them. This is the producer-off-the-check's-
  path shape in miniature. Dismiss: the returned value looks like ordinary own data and slicing
  looks harmless.
- **S3 — `forloop.item` (injected, `src/drop/forloop-drop.ts` + `src/tags/for.ts`,
  `src/tags/render.ts`, `src/tags/tablerow.ts`).** The loop drop keeps the evaluated collection and
  exposes the current item by index; drops are explicitly exempt from the own-property policy, so
  the resolver's guard never sees it. Dismiss: loop metadata is not scope data and Drops are
  exempt; reachable through the same `{% for %}`/`{% render ... for %}` entry points.

Why these beat the rest: S2/S3 are HOW-type (producer laundering, Drop exemption) rather than
another direct read; all three sit in modules the published fix leaves untouched; each has a
different dismissal. The real upstream routes above are kept as Pattern B tests, not as injected
code.

## Sites / routes / shapes the security tests cover

1. negative numeric index through template and through the public expression/path API;
2. `first`/`last` magic keys on arrays and on plain objects;
3. `first`/`last` filters;
4. sequence-wide filters (`join`, `compact`, `concat`, `slice`, `sort`, `reverse`);
5. iteration: plain `for`, `for reversed/limit`, `tablerow`, `render ... for`;
6. serialisation: direct output, `json`, `inspect`, `array_to_sentence_string`;
7. the `size` key on arrays and plain objects with an inherited `size`;
8. injected `at` (positive and negative);
9. injected `take`;
10. injected `forloop.item` through `for` and `render ... for`.

## Coupled must-keep-working (functional)

Dense arrays through every route above keep exact results; negative indexing on ordinary arrays;
`first`/`last` on ordinary arrays and strings; array/string length, object key count, Set and Map
size; own object properties visible and inherited object properties hidden; custom Drop APIs still
resolve through their prototype; the disable setting keeps inherited data visible for the governed
reads; the project's own tests for the touched areas.

## Oracle design

Two valid designs, both exercised:
- `solution/fix.patch` (oracle): sanitise array values at the read boundary in `Context` (own-dense
  copy when the restriction is on), with flag-aware `readFirst`/`readLast`/`readSize`; the copy
  shadows holes with own `undefined`, so every downstream consumer (filters, tags, output, drops)
  sees only own data; mode-off returns raw values.
- `pass-alt.patch`: site-by-site helpers (`readArrayElement`, own-dense copies in `toArray`/
  `toEnumerable`/`stringify`, filters, `array_to_sentence_string`, `json`/`inspect`, `at`, `take`,
  loop drop); demonstrates a different valid layer.
- `pass-hardening.patch`: oracle plus extra defensive checks (Drop-returned arrays, `getAll`).
- One `security_fail` patch per lever (T1, T2, T3, T4, T5, S1, S2, S3), each missing only that
  lever's protection; `functional_fail` is a fix that hides all array data regardless of the mode.

## Open items / risks

- The pinned docs say the restriction is not a sandbox for filters or tags; the report overrides
  that with a property stated over the outcome. This is an intentional dismissal reason, not a test
  requirement hidden from the solver.
- Whether the central oracle changes any project test: to be verified by running the selected
  project specs on all three trees (vulnerable, oracle, alt).
- The `'-1'` string-key behaviour differs between the upstream-style fix and the central fix; it is
  not tested (not required by the property).

## Final lever list (one line each)

- T1 (A, report target) `src/context/context.ts:128` — negative numeric index adjusts to length+key and reads raw; report leads here.
- T2 (A far, two sites) `src/context/context.ts:133-152` + `src/filters/array.ts:15-16` — end accessors (arrays and plain objects) and end filters; dismiss: docs exclude filters / convenience accessors elsewhere.
- T3 (B, how) `src/tags/for.ts:46-76`, `src/tags/tablerow.ts:42-56`, `src/tags/render.ts:72-79` — iteration; the modifier/tablerow copies launder inherited slots into own elements before the loop; dismiss: docs exclude tags.
- T4 (B, how) `src/filters/array.ts`, `src/util/underscore.ts:37-43`, `src/filters/string.ts:210-222`, `src/filters/misc.ts` — sequence-wide filters, direct output, json/inspect, sentence output; dismiss: docs exclude filters / ordinary JS semantics.
- T5 (B, how, coupled) `src/context/context.ts:154-158` — inherited `size` beats the structural size; dismiss: Sets/Maps need prototype size, so a naive removal breaks them.
- S1 (injected) `src/filters/misc.ts` `at` — direct positional lookup; dismiss: new convenience filter elsewhere.
- S2 (injected) `src/filters/misc.ts` `take` — slice copy makes inherited slots own; dismiss: the result looks like own data.
- S3 (injected) `src/drop/forloop-drop.ts` `item()` via for/tablerow/render — Drops are exempt; dismiss: loop metadata is not scope data.

## Verified locally

- Behavioural probe on the pinned tree (jest): every route above leaks; positive index and plain object members are already guarded.
- Oracle (context-boundary own-slot copies + flag-aware end/size): 39 security pass, 321 functional pass.
- Site-by-site alternative: 39 security pass, 321 functional pass.
- Hardening: 39 + 321 pass.
- Over-broad (ignores the disabled setting): 39 security pass, 3 functional fail (mode-off preservation) — `functional_fail`.
- Eight `security_fail` patches: each fails its own lever's tests (2–11 tests) and passes all 321 functional tests; repeated runs are deterministic.
- The injected tree (nop): 39/39 security fail, 321/321 functional pass; selected project specs 297/297 pass on pinned, injected, oracle, alternative and hardening trees.

## Could not verify

- Target-model behaviour (not run by design; the gate does not run trials).
- `present_in_latest` was checked by reading origin/master 920166e3f (10.30.0): T3, T4 and T5 remain; recorded as `yes`.
- The `'-1'` string-key behaviour differs between the upstream-style and context-boundary fixes; it is deliberately untested (not required by the property).
- Docker gate stages (static/nop/oracle/patches): see the report; static passed locally before the Docker runs.

## Docker gate log

- static: PASSED.
- nop: PASSED (security 39/39 fail, functional 320/320 pass). The Docker JUnit view has 320
  functional keys for 321 cases because the project's own `render.spec.ts` contains two tests with
  the same name (`tags/render should support render`); both pass and this is pre-existing.
- oracle: PASSED (3/3 runs, reward 1.0, identical security/functional result maps).

## Patches stage (first run, before the 10-minute background limit cut it)

The stage had completed six checks when the harness stopped the 10-minute background command; all six
behaved as declared (no functional failure; reward is the capped security fraction):
`sf-miss-t1-negative` 0.8974 (4 security fail), `sf-miss-t2-accessors` 0.8205 (7),
`sf-miss-t3-transform` 0.7179 (11), `sf-miss-t4-iteration` 0.8462 (6), `sf-miss-t5-size` 0.8974 (4),
`sf-miss-s1-at` 0.9487 (2). The stage was restarted from the beginning with a two-hour limit.
- patches: PASSED (all 11 checks declared-with-a-file behaved as expected: 8 security_fail with zero
  functional failures, ff-overbroad with 3 functional failures, pass-hardening 1.0, pass-alt 1.0;
  blind.patch skipped as the downstream blind-fix stage writes it).
End (UTC): 2026-10-24T03:52:45Z.
