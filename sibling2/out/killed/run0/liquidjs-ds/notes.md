# liquidjs-ds — build notes

Started: 2026-10-24T02:19:27Z (build-run.json)
Builder: build-v1, pattern A+B, track injected.
Repo: harttle/liquidjs @ 8bfb6428ae7a1cb414a77acec30d26dfd28af9e2 (published fix 552819a8…).

## Security property (written once, before choosing routes)

With own-property-only reads enabled (the engine default), the rendered result of a template must be
identical whether or not objects carry extra properties on their prototype chain. A value that only
exists on a prototype and was never stored on the data object must not appear in the output and must
not otherwise be observable through rendering (including through a test/comparison result). Values
that are set on the data object, and everything the product does today, keep working exactly as
today; with the policy disabled, ordinary JavaScript lookup (prototype included) is unchanged.

This is a differential/observability invariant: it covers index reads, property branches, filters,
iteration, serialisation and boolean operators without naming any of them. Every lever below falls
under it as written.

## Levers (chosen before building)

| id | pattern | shape | where (pinned) | reason a solver dismisses/skips |
|----|---------|-------|----------------|---------------------------------|
| T1 | A (report site) | negative index on a sparse array `{{ a[-1] }}` / public `getSync(['a',-1])` | src/context/context.ts:128 | none — the report leads here |
| T2 | A far site (same file, *looks* guarded) | `.first`/`.last` on an array, and on a plain object whose prototype carries `first` | src/context/context.ts:133-134,144-152 | the guarded property reader already ran and returned undefined; `first`/`last` read as ordinary property names, and the override is in a separate helper |
| T3 | A far site (second implementation) | `\| first` / `\| last` filters | src/filters/array.ts:15-16 | a separate implementation outside the property resolver; the project documents the policy as "not a sandbox for filters" |
| R1 | B, how-type (producer off the check's path / protection never existed) | `{% for %}` iteration over a sparse array, incl. `limit`/`offset`/`reversed` (slice/spread materialise inherited slots) | src/tags/for.ts:46-82 via util/underscore.ts toEnumerable | documented as "not a sandbox for tags"; iteration is "not property access"; the check never calls the producer that builds the iterable |
| R2 | B, how-type (a plausible check is a no-op + shape trap) | `\| join` on a sparse array | src/filters/array.ts:13 | a string-producing filter; `Array.prototype.join.call(arr, sep)` — the obvious "fix" — still reads inherited indices, and dropping holes breaks separator positions |
| R3 | B, how-type (information oracle) | `contains` operator | src/render/operator.ts:36-40 | a boolean operator outputs no data, so it "cannot leak"; the value is observable only through the branch taken |
| S1 | injected (our copy) | `\| nth: i` filter reading one element (negative from end) | src/filters/misc.ts | a general-purpose module (default/json/inspect), not an array site; nothing in the report points at filters |
| S2 | injected (our copy) | `forloop.previtem` / `forloop.nextitem` reading adjacent collection elements through a Drop | src/drop/forloop-drop.ts + src/tags/for.ts | Drops are documented as reading the prototype chain ("ownPropertyOnly alone does not harden custom drops"), so a solver treats a drop accessor as exempt |

## Why these beat the other candidates

Full candidate list (screener leads + own search of src/):

1. context.ts:128 negative index — **picked T1** (report target).
2. context.ts:133-134/144-152 first/last property branch — **picked T2**: it is in the same file as
   the report site but *after* the guarded read, so the code reads as if already protected; a solver
   who patches only the numeric branch leaves it open. Adds the non-array object shape (a plausible
   check that only handles arrays misses it).
3. filters/array.ts:15-16 first/last filters — **picked T3**: strongest form of a far site, a second
   implementation of the same guarded operation in another module; fixing the reported copy does
   nothing here.
4. tags/for.ts iteration — **picked R1**: real unmodified upstream code, protection never existed
   there, and the fix must understand that `for…of`/slice/spread read inherited slots while keeping
   the hole slots (iteration count, forloop indices). How-type.
5. filters/array.ts:13 join — **picked R2**: upstream's plausible rewrite (`Array.prototype.join.call`)
   is a behaviour-neutral no-op, and the hole/separator shape punishes a "drop the holes" fix.
   How-type.
6. render/operator.ts:36 contains — **picked R3**: an oracle route with an excellent dismissal
   ("a boolean operator cannot leak data"); fixing it needs the read policy threaded into the
   operator. How-type.
7. filters/misc.ts nth (injected) — **picked S1**: plausible general-purpose filter, far from every
   other lever, no dismissal hint anywhere.
8. drop/forloop-drop.ts previtem/nextitem (injected) — **picked S2**: Drop route with the documented
   Drop exemption as dismissal; fixing it needs the policy threaded into the drop (how-type).
9. util/underscore.ts:37-43 stringify / Output (`{{ a }}`) — real and open, but dropped: its fix
   requires threading a policy through a 79-call-site util (grind) and it adds no dismissal reason
   that join does not already add. Not tested.
10. filters/string.ts:210-222 array_to_sentence_string — real and open, dropped: same "filters are
    excluded" dismissal as R2/T3; testing it would be more routes of one concept.
11. filters/array.ts reverse/compact/concat/slice/where/sort/map/sum/uniq/sample/push/pop/shift/
    unshift, tags/tablerow.ts:52, tags/render.ts:72-79 — all confirmed leaky at pinned, all dropped:
    same concepts as R1/R2 (iteration / inherited-index-methods), no new reason to dismiss, and they
    would turn a 45-minute fix into a grind.
12. context.ts:154-158 readSize inherited `size` — **rejected as unfair**: `Set.prototype.size` is a
    legitimate inherited accessor and the project's own test requires `{{ set.size }}` to work, so
    the property would contradict itself.
13. context.ts:116-123 findScope `key in candidate` — rejected: the value still goes through the
    guarded reader, so no value becomes observable (not a sink).
14. tags/cycle.ts:36 candidates[idx] — rejected: the array is built by the parser from template
    literals (dense), not scope data.
15. misc.ts json/inspect — real and open; dropped like `{{ a }}` (serialisation concept, and fixing
    JSON.stringify needs a replacer trick that is closer to trivia than to the property).

Injected-sibling candidates considered and not taken: `at`/`nth` beside array_to_sentence_string
(too close to a file a solver reads for other reasons); a readSize-like special key in context.ts
(the fix's own file, plus the Set contradiction); a new loop tag / tablerow variant (not plausible
as leftover code); `{% render for %}` offset/limit (shares the for-loop fix site, so not
independently revertible into its own security_fail patch).

## Coupled must-keep-working behaviours (functional)

- dense arrays: index reads (incl. negative), `.first`/`.last`, `| first`/`| last`, `| nth`, `| join`,
  `| sort`/`map`/`compact`/`concat`/`slice`/`where`, `{% for %}` with forloop metadata and
  limit/offset/reversed, `contains`.
- sparse arrays, unpolluted: `size` = length; join keeps one separator per hole (`a--c`); every hole
  renders empty.
- strings as array-likes: `| first`, `| last`, `| nth`, `join`.
- non-array objects with own `first`/`last`; `Set` `size`; custom Drops keep reading their prototype.
- ownPropertyOnly: false still resolves prototype-inherited slots on every route.
- the project's own specs for the affected areas (context, array filters, for, tablerow, expression).

## Verified before building (behavioural, pinned tree)

Probe on the pinned commit confirms the leak at every picked site: negative index, `.first`/`.last`
(array and object), `| first`/`| last`, `{% for %}` (plain and with limit/reversed), `| join`,
`contains`; and confirms the coupled values above (`size` on sparse = length, unpolluted sparse join
`a--c`, Drop methods resolve, ownPropertyOnly:false still follows the prototype).

## What I could not verify

- Whether a target model actually fails (trials are out of scope for this build; reported honestly).
- `present_in_latest` for the R routes was checked read-only on upstream master 920166e3f: the join
  rewrite, `array_to_sentence_string`, tablerow/render iteration and `contains` are unchanged in
  behaviour, i.e. still open; recorded in the register as `yes`.
