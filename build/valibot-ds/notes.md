# valibot-ds — build notes

- Start (UTC): 2026-10-24T03:27Z (pipeline), work began 03:35Z.
- End (UTC): 2026-10-24T05:21Z.
- Advisory: GHSA-5QJJ-4XWW-7PHC / CVE-2026-59952 — open-circle/valibot.
- Pinned: 752c6369bbd05904bab22149bf79f716a274c99d. Published fix: 1bd01c304657cd0809cc92694360b6cc60f700bf.
- Track: injected, pattern A+B. Delivery follows the current Frontier 1.4 template (separate
  verifier, /workspace, tests/Dockerfile), which supersedes the older /app wording in the prompt.

## Levers (one line each)

1. **L1 (A, reported)** — the flattening helper's nested accumulator decides presence with a truthy
   lookup, so a collected entry named like an inherited member makes it throw.
   `library/src/methods/flatten/flatten.ts:104`.
2. **L2 (B/how, main)** — a refused undeclared name that is an inherited accessor defeats the
   obvious own-property fix: the check is false, the plain assignment then stores the messages
   through the inherited setter (lost, and the result's prototype is replaced). The name is
   produced by a route the formatter never calls, so a fix that only verifies the reported crash
   misses it. `flatten.ts:104-108` with the producer at `strictObject.ts:203`.
3. **L3 (A far)** — the combination merge and its plain-object test both read a name input data can
   shadow; an own `constructor` field defeats the object test itself. `_merge.ts:34-44`.
4. **L4 (B)** — the strict schema's unknown-name check treats an undeclared supplied name as a
   declared entry. `library/src/schemas/strictObject/strictObject.ts:203`.
5. **L5 (B)** — the catch-all loop never applies the rest schema to such a name, so an invalid
   value is accepted and a valid one dropped. `objectWithRest.ts:231`.
6. **L6 (B)** — the pass-through schema drops such an undeclared name from its output.
   `looseObject.ts:208`.
7. **L7 (injected)** — a maintained one-message-per-path helper skips the name because its
   presence lookup sees an inherited member (silent loss, no crash).
   `library/src/methods/uniqueMessages/uniqueMessages.ts:29`.
8. **L8 (injected)** — a maintained first-value-wins guard in the collection output drops an
   accepted entry for the same reason. `record.ts:222` (and `recordAsync.ts:240`).

## Sibling candidate list and picks

Every candidate found (O8/O8b plus a search of the tree):

| # | candidate | verdict |
|---|-----------|---------|
| 1 | `strictObject.ts` unknown-key `key in this.entries` | **picked (L4)** — real upstream, input-controlled key, three different dismissal reasons exist for the group |
| 2 | `strictObjectAsync.ts` same check | not picked — same concept, async twin |
| 3 | `objectWithRest.ts` rest loop | **picked (L5)** — real upstream, and it looks guarded by the key-validity helper |
| 4 | `objectWithRestAsync.ts` rest loop | not picked — async twin |
| 5 | `looseObject.ts` rest copy | **picked (L6)** — real upstream, silent output difference rather than a crash |
| 6 | `looseObjectAsync.ts` rest copy | not picked — async twin |
| 7 | `flatten` root/other branches | not affected by the mechanism |
| 8 | `summarize` | no keyed accumulator |
| 9 | `getDefaults` / `getFallbacks` | enumerate developer-declared entries only |
| 10 | `keyof` / `picklist` | uses `Object.keys` + array membership |
| 11 | `variant` discriminator `currentKey in input` | developer-declared key; a missing input key is not output loss |
| 12 | `object` / `looseObject` / `strictObject` `key in input` declared-key presence checks | out of scope (developer-controlled key; see below) |
| 13 | `_isValidObjectKey` filters | deliberate prototype-safety filters; must keep working |
| 14 | `map` key path producer | a lead only; not tested (a producer-side filter would be a defensible but different behaviour) |
| 15 | new error helper with a truthy accumulator | **picked (L7)** — injected, silent loss, no crash |
| 16 | collection output presence guard | **picked (L8)** — injected, producer-side, looks already filtered |

Why the picks beat the rest: 1/3/5 are real unmodified upstream code at the pinned commit, are
reachable through public entry points, and are untouched by the published fix — with three
*different* reasons a solver would skip them (a lookup against “schema entries” that reads as
developer-controlled; a call that already looks guarded by a security helper; a silent output
difference instead of a throw). The async twins are the same concept, so adding them would only
add routes of one concept. 11/12 are presence questions over developer-declared names, not over a
supplied key, so the stated property does not require them. 15 and 16 are the most complex
plausible maintainer code that is still reachable through the public entry point and far from the
reported helper: one is a convenience helper that fails silently, the other a producer-side guard
that looks like it is already protecting the output.

## Verified

- Behavioural probes at the pinned commit: the reported crash; the inherited-accessor loss after
  the published approach; the combination failure for four inherited names (`constructor` included);
  the strict/catch-all/pass-through routes; and both injected siblings. Each was driven through the
  public exports.
- `tsc --noEmit` on the full injected+reference tree: clean.
- The project's own tests for the affected areas (flatten 9, summarize 5, intersect 10, _merge 11,
  strictObject 31, objectWithRest 33, looseObject 32, record 21, map 21, getDotPath 4; 177 cases)
  pass on the pinned+injected tree and on the reference fix.
- Local dry runs of every suite: nop 28/28 security fail, 200/200 functional pass; reference 28/28
  + 200/200; every patch check produced the declared outcome (security_fail / functional_fail /
  pass) before the Harbor run.
- Gate stages: static PASS, nop PASS (28/28 security fail, 200/200 functional pass), oracle PASS
  (3 runs, reward 1.0, identical results), patches PASS (14/14 checked; the not-yet-written blind
  patch is the only skipped entry, as allowed for the static stage).
- The first `patches` run was stopped by the harness's 10-minute background limit mid-way; it was
  restarted detached (`setsid nohup`) and completed with all 14 checks green.

## Could not verify

- The background `patches` stage result at the time these notes were started (it is reported in
  the final report).
- Target-model behaviour: no trials were run here (the pipeline runs them).
- Current-upstream status was checked at 2d29dbf (2026-10-09): the strict/catch-all/pass-through
  routes now use own-property checks there, while the flatten inherited-accessor loss and the
  merge plain-object detection are still present.

## Out of scope (one line)

`object`/`looseObject`/`strictObject` use `key in input` for schema-*declared* keys, so an absent
declared key whose name is inherited can read the inherited member; the key is developer-chosen,
not supplied by the attacker, so it was left unfixed and untested.

## Fairness notes

- The `constructor` case is covered literally by the property (“a name that every JavaScript object
  inherits”), and the same name set appears in the project's own regression test for the reported
  helper; a careful engineer testing the combination route with that set finds it.
- The inherited-accessor case requires the message to land as an ordinary nested entry. The
  instruction states that a supplied name must not be dropped and must be reported like an ordinary
  name, and that the library's existing prototype-safety refusals stay as they are; a fix that
  silently drops the message or reroutes it to the fallback group contradicts the stated contract.
- Asynchronous twins are fixed by the reference solution but are not tested (same concept).
