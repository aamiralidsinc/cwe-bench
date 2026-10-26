# stk-bmoor-ghsa4m8h — build notes

Started 2026-10-26T12:17:00Z (build/stk-bmoor-ghsa4m8h/start_utc.txt). Ended 2026-10-26T12:29Z.

## Design

Stacked H3b2: pin = parent of the earlier published fix A (`7d4a086a1dc3`, `fix: prototype
pollution`), later fix B = `29b0162cc1dc` (`fix: bug with [__proto__]`). Four concepts, four
independent edit sites in the reference fix:

- **C1 [T1, T2, T5]** — the shared path writer `src/core.js set`. T1: dot path through the
  prototype hook or a constructor chain (advisory route). T2: the same writer reached through the
  flat-array, array-element and bracket/quoted notations the parser accepts. T5: `Config#assign`
  flattens a payload to a dotted key and feeds the same writer, so a check on the payload never
  runs. One fix (per parsed, string-coerced segment) closes all three.
- **C2 [T3]** — the setter factory `_makeSetter` (src/core.js:199-228) and `object.makeExploder`:
  closures that assign into their context and never call the shared writer. Reason to dismiss:
  developer-authored plumbing. Coupled value: it must keep creating missing intermediate objects.
- **C3 [T4]** — `object.merge` (src/object.js), a second deep-write implementation. Reason to
  dismiss: a deep copy of trusted in-memory objects. Coupled values: null replacement, array
  identity, and ordinary data keys that merely share a built-in member name (a name blacklist
  breaks that last one).
- **C4 [T6]** — `Config#sub` resolves a caller path with `core.get` and `Object.assign`s into the
  resolved object; a prototype-naming path resolves to the shared prototype. Reason to dismiss:
  a config helper whose path is supposed to name a branch the caller owns.

Recorded but not part of the stack: T7 `core.del` (deletion only, not a value landing on the
prototype) and T8 `move/Scheduler.js` (module not exported by the package entry; its sibling
`move/dom.js` requires a non-existent `./core.js`). Neither is tested.

## Verified

Local behaviour matrix (patch each variant onto the pinned tree, run both suites with the Node
test runner, unique probe key per test, cleanup in a `finally`):

| tree | security | functional |
|---|---|---|
| pinned | 0/18 | 11/11 |
| reference | 18/18 | 11/11 |
| hardening | 18/18 | 11/11 |
| alternative | 18/18 | 11/11 |
| upstream_fix (A+B) | 15/18 (merge open) | 11/11 |
| upstream_first_fix (A only) | 7/18 | 11/11 |
| miss_set_paths | 8/18 | 11/11 |
| miss_setter_factory | 14/18 | 11/11 |
| miss_merge | 15/18 | 11/11 |
| miss_config_sub | 17/18 | 11/11 |
| one_variant | 12/18 | 11/11 |
| reads_only | 1/18 | 11/11 |
| wrong_resource | 0/18 | 11/11 |
| check_after_adjustment | 0/18 | 11/11 |
| refuse_all | 18/18 | 2/11 |
| merge_name_blacklist | 18/18 | 10/11 |

Control (`stk-bmoor-ghsa4m8h-control`, set sink only): pinned 0/8 security + 11/11 functional;
control reference 8/8 + 11/11; `control_malformed_identity` 4/8 + 11/11; `control_overbroad`
8/8 + 10/11.

Project tests: `mocha src/core.spec.js src/object.spec.js src/lib/config.spec.js` -> 39 passing at
the pinned commit, run inside the agent image build. The full recursive suite cannot pass at the
pinned commit: `src/eventing/broadcast.spec.js` requires `./Broadcast.js`, which does not exist
(pre-existing upstream defect).

Pattern B register rows appended to `build/audit/uncovered-routes.tsv`: T5, T4, T6.

## Things worth knowing

- `Config#sub('__proto__', ...)` under a get-guard-only fix (the shape upstream B shipped) leaves
  an unhandled rejection: `Config#set` triggers `Broadcast`, whose `_listeners['__proto__']`
  resolves to `Object.prototype` and then fails `.slice`. That is a broadcast defect, not the
  property under test, so the suite tests the sub route through the constructor spelling only.
  Both the reference (refuses before resolving) and the B-style get guard pass it.
- The published fix A guards only `__proto__` and does not coerce array elements to strings;
  fix B adds `String(...)` and the `constructor`/`prototype` names. The reference fix is
  equivalent for writes but deliberately does not add the read guard (unnecessary for the
  property, and it would make the T6 site non-independent).

## Could not verify / guesses

- The two fix commits were read from the clone (their source diffs), not from the advisory text;
  which advisory corresponds to A vs B is inferred from the commit titles and the "incomplete
  fix" shape, not from the advisory bodies (both GHSA ids were taken from the build prompt).
- `present_in_latest` for the register rows was judged by reading current main `37ca577`:
  `merge` is unchanged (yes); the `Config` API was rewritten and `assign`/`sub` no longer exist
  (no).
- Container gate results are recorded in build/stk-bmoor-ghsa4m8h/gate_report.json as the stages run.
- The `move/` tree is not exercised; it is stale upstream code.
