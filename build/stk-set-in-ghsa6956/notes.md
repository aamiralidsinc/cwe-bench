# stk-set-in-ghsa6956 — build notes (ABANDONED before build)

- Start (UTC): 2026-10-26T12:31:12Z. The pipeline's own agent run failed immediately with
  `claude-code:unrecognized_model` (`stack_pipeline.log`); this analysis is the manual builder
  session.
- End (UTC): 2026-10-26T12:36:27Z.
- Advisory: GHSA-6956-83fg-5wc5 / CVE-2022-25354 (described by GitHub as an **incomplete fix** of
  GHSA-qr4p-c9wr-phr6 / CVE-2020-28273) — `ahdinosaur/set-in`, CWE-1321.
- Pinned: `a883c871573874037e92f309c270160a754e67be` (tag v2.0.0). Verified it is the parent of the
  first published fix `e431effa0019`.
- Published fixes named by the prompt: `e431effa0019` (v2.0.1, A) and `6bad255961d3` (v2.0.3, B).
- Reader records: the prompt mandates `pipelines/stacking/out/reader/h3-ghsa-6956-83fg-5wc5.json`
  (the `reader` record: `usable: false`, two independent groups) while the embedded design and the
  score row come from `pipelines/stacking/out/reader-ds/h3-ghsa-6956-83fg-5wc5.json`
  (`usable: true`, three groups). Both were checked against the pinned tree; the code agrees with
  the `reader` record.

## Outcome

**STOP — the pinned tree supports at most two independent security edit sites inside this
advisory's protection, and the stacked rule needs three.** Per the build prompt's stop rule, no
`tasks/stk-set-in-ghsa6956/` tree, no control task, no `checks/`, no Pattern-B register rows and no
gate stage were produced. The base code was not modified to manufacture a third lever.

## Verified on the pinned tree (probe through the only entry point, `setIn(object, path, value)`)

The package is 34 lines: one public function (`index.js:5-10`) delegating to `recursivelySetIn`
(`index.js:12-29`), which reads `object[key]` at `index.js:26` after taking `key = path[index]`
(`index.js:19`), and writes `object[key] = value` in `set` (`index.js:31-33`). The only other logic
is the `'-'` append rewrite (`index.js:21-24`).

| probe | pinned result |
|---|---|
| `setIn({foo:{bar:'baz'}}, ['__proto__','polluted'], 'x')` | `({}).polluted === 'x'` (Object.prototype polluted) |
| `setIn({}, ['constructor','prototype','polluted'], 'x')` | `({}).polluted === 'x'` |
| `setIn({}, ['toString','x'], 1)` | `Object.prototype.toString.x === 1` (shared built-in modified) |
| `setIn({a:{}}, ['a','__proto__'], {isAdmin:true})` | `a`'s prototype replaced; `a.isAdmin === true`, no own `__proto__` |
| `setIn({}, [new String('__proto__'),'polluted'], 'x')` | `({}).polluted === 'x'` |
| `setIn({}, [['__proto__'],'polluted'], 'x')` | `({}).polluted === 'x'` |
| `setIn([], ['__proto__','polluted'], 'x')` | `[].polluted === 'x'` (Array.prototype) |
| `setIn({a:{}}, ['a','constructor'], 5)` | own data field (works today) |
| `setIn({foo:['bar']}, ['foo','-'], 'x')`; numeric index; deep unresolved; null/undefined leaf | all work today |
| `JSON.parse('{"__proto__":{"safe":1}}')` then `['__proto__','safe']` | own data property, no pollution |

Upstream comparisons (same probes):

- **A = e431eff** rejects literal `__proto__` and `constructor`+`prototype` path segments before the
  recursion. It leaves the coerced-key routes open, leaves the `toString` built-in route open, and
  refuses a legitimate final own-data write named `__proto__` (a final `constructor` write still
  works).
- **B = 6bad255** moves a name denylist into `set` (after the recursion) and adds a path-type check.
  `setIn({}, ['__proto__','polluted'], 'x')` still **pollutes Object.prototype and only then
  throws** (verified: `({}).polluted === 'x'` after catching the refusal). The `toString` route is
  still open.
- **C = d87c1a0** (v2.0.4, no advisory in this task's history) moves the denylist before the
  recursion: the route above is refused with no side effect, but the `toString` route is still open
  and legitimate own-data writes of `constructor`/`__proto__` are refused.
- Current upstream v2.0.5 (`80caa14`) still has the `toString` route open.

## Why the stack cannot reach three concepts (build rule 1)

Rule: "If one guard or one fix site would close two traps, they are ONE concept. Count your
reference fix's independent edit sites."

The reference fix that keeps today's behaviour working has exactly two edit sites:

1. **Read guard** at `index.js:19/26` (non-final segments): descend only into an own property or
   an absent key; never into an inherited value. Closes the `__proto__`, `constructor`+`prototype`,
   `toString`/`hasOwnProperty`, array-prototype and coerced-key routes.
2. **Write helper** at `index.js:31-33`: create an own data property (for example
   `Object.defineProperty`) instead of invoking an inherited setter. Closes the trailing-`__proto__`
   reparenting route and preserves ordinary own-data writes.

Mapping every trap of both reader records to an independent edit site:

| trap | mechanism | independent edit site? | why |
|---|---|---|---|
| reader T1 / reader-ds T1 — `__proto__` traversal | M4 | **yes** — read guard | advisory's own route |
| reader T2 / reader-ds T2 — `constructor`+`prototype` traversal | M8 | **no** | the same own-property read guard closes it; a `__proto__`-only denylist missing it is a *wrong fix shape*, not a second mechanism |
| reader T3 — coerced non-string keys | M8 | **no** | a correct read guard (`hasOwnProperty` coerces) and a correct write helper (`defineProperty` coerces) both handle it; only a raw-key denylist misses it, and that shape also breaks the must-keep below |
| reader T4 — inherited built-ins (`toString`, `hasOwnProperty`) | M10 | **no** | same own-property read guard |
| reader-ds T3 — guard at the sink runs after the recursion | M7 | **no** | the fix is the read guard; a guard placed at `set` is the published B's wrong placement, not a second protection |
| reader-ds T4 — legitimate own-data write of a prototype-like name | M11 | **no** | a coupled must-keep value, not a missing protection (see below) |

Proof that one edit site cannot do both:

- Read guard only (`index.js:19/26`, final segment untouched): closes every traversal route but still
  reparents on `setIn({a:{}}, ['a','__proto__'], payload)`.
- Write helper only (`index.js:31-33`): closes the reparent but the inner recursion still writes
  `polluted` onto `Object.prototype` through a *safe* key.
- A single name denylist at one site closes traversal and reparenting, but refuses final own-data
  writes of `constructor`/`prototype` that work today (upstream d87c1a0 does exactly this), so it
  fails the must-keep / `functional_fail` checks.

The lead's three groups also cannot each carry an honest `security_fail` miss patch:

- **[T1, T3]** and **[T2]** are both the read guard, so they are one concept.
- **[T4]** is a coupled must-keep. A `security_fail` patch must leave a *security* test failing while
  all functional tests pass; no partial fix of the write site can do that. Naive assignment reparents
  and also fails the own-data functional value; refusal passes security but fails the same functional
  value.

Additionally, the lead's stated T4 value ("a data field named `__proto__` written as an own
property") **cannot be a functional test at all**: on the pinned code that call reparents instead of
creating an own field, so the test would fail the gate's `nop` stage, which requires every
functional test to pass on the untouched vulnerable tree. The only nop-safe coupled values are the
final own-data writes of `constructor`/`prototype`, ordinary new and existing keys, the `-` append,
numeric indexes, deep unresolved paths and null/undefined leaves. With the `__proto__` component
excluded, the write-site concept and the must-keep are one edit site; with it included, no
conformance-valid per-concept patch exists. Either way the 3-concept bar is not met.

This is the same conclusion the on-disk `reader` record reaches (`usable: false`, two groups); its
unverified note ("if the hidden tests do not require it, T4 collapses and only two independent
groups remain") is confirmed above from both directions.

## Reader-input discrepancy

The prompt's `stacking.reader_record` path points at the `reader` record, but the design plan, the
trap ids/types and `score_at_build` (0.053, flags `single-trap-carries`) come from the `reader-ds`
record. The two disagree on T3/T4 and on `usable`. The `reader-ds` three-group split mixes the read
site (`T1`, `T2`) and the write site (`T3`) in different groups and counts a must-keep (`T4`) as a
third concept, so it does not satisfy build rule 1 as written.

## Fairness concerns seen here

- The library's stated contract is arbitrary nested associative structures (`package.json:4`,
  `README.md`), so refusing `constructor`/`prototype`/`__proto__` names outright breaks legitimate
  data fields; the correct fix must distinguish a traversal segment from a final own-data key.
- The `-` append sentinel, numeric indexes, deep unresolved paths and null/undefined leaves must keep
  working; a guard that refuses to create intermediates breaks them.
- The coerced-key (`new String('__proto__')`, `['__proto__']`) shapes are type/encoding variants of
  the same read guard; the build prompt's "never add encoding variants" rule argues against using
  them as a separate lever, and they are not independent of the read guard anyway.
- No upstream test or README example demonstrates a legitimate own-data field literally named
  `__proto__`, so the lead's T4 must-keep is not grounded in the project's own usage.

## What could not be verified

- The exact hidden-test expectations are not known (none were written). The analysis above does not
  depend on them: the code has one read site and one write site.
- Whether the advisories intended the own-data-name compatibility at all. GHSA-6956-83fg-5wc5 only
  says "incomplete fix of CVE-2020-28273"; it names no `constructor`/`prototype` route. Upstream's
  v2.0.4 and v2.0.5 fixes refuse those names outright, which suggests the must-keep is not an
  upstream requirement.
- The published fix set named by the prompt (A+B) is itself still vulnerable: B = 6bad255 pollutes
  Object.prototype before throwing. The first genuinely non-polluting upstream fix is the later,
  unadvertised v2.0.4 commit d87c1a0, which still leaves the inherited-built-in route open.

## Out of scope (one line)

Current upstream v2.0.5 still writes through inherited built-ins such as `toString`; that is a real
uncovered route but it is the same read site, so it does not change the concept count and was not
built on.
