# protobuf.js-ds — a task that DeepSeek V4.1 Flash and MiMo-V2.6-Pro both fail 3/3

**Status of 2026-10-20. PROVISIONAL on the audit dimension.** This is a **both-model breaker (clean)**: both target models failed all 3 counted attempts and neither reached 1.0, and no attempt broke a legitimate behaviour (no 0.0 — every attempt passed all functional tests and simply left security routes open). Its pre-trial fairness review returned **GATE_A: READY** (judged fair) with **NEEDS_HUMAN_REVIEW: YES**. **No per-attempt transcript audit has been run yet**, so the fairness verdict is confirmed but the per-attempt evidence the jackson report relies on does not exist for this task. Treat §3 and §4 as provisional (which specific routes each attempt left open is inferred from scores, not audited); §1 and §2 are from the build and fairness records and are solid.

Sources: the task build and validation records (`manifest.json`, `notes.md`, `checks/*.patch`), the pre-trial fairness review (`FAIRNESS.md`), and the counted trial log (`auto_trial.out`, confirmed by the `ACCEPTED` line in the pipeline trial log). The per-test route breakdown and transcript audit that the jackson report relies on have **not** been produced for this task.

## Summary

- **Result: both target models failed all 3 counted attempts; neither reached 1.0.** (`ACCEPTED: deepseek: failed (0p/3f/0e); mimo: failed (0p/3f/0e)`.)
  - DeepSeek V4.1 Flash: 0.9412, 0.9118, 0.9118 — best ≈ **0.94**.
  - MiMo-V2.6-Pro: 0.4706, 0.9118, 0.7941 — best ≈ **0.91**.
- This is a **clean** breaker: reward is a pure security-pass fraction here because **every counted attempt passed all functional tests** (no 0.0). Reward × 34 is an integer in every attempt, so the scores are 32/34, 31/34, 31/34 (DeepSeek) and 16/34, 31/34, 27/34 (MiMo) security tests passed. Each model left at least 2 security routes open on its best attempt.
- Every attempt finished on its own — all six reported `finish=success`, `rc=0`; none was cut by a timeout. Wall times: DeepSeek 32–56 min; MiMo 62–178 min.
- The task is a real library with many real routes to one rule. It is protobufjs/protobuf.js at the commit before the published prototype-pollution fix. Ten published-fix routes (T1–T10), two real uncovered-upstream routes (R1, R2) and two injected sibling gaps (S1, S2) all reach the same rule.
- **Fairness: GATE_A READY** (every security test is covered by the instruction's one general rule read literally; no route-naming sentence needed). **NEEDS_HUMAN_REVIEW: YES** on two borderline points (below). The review also lists non-blocking quality/leniency gaps.
- **Not yet done:** per-attempt transcript audit; a `blind.patch` (intentionally absent, to be added as `expect=pass`); the full combined nop/oracle/patches re-gate after the 2026-10-20 sibling-injection upgrade (components verified locally, one combined run pending).

## 1. The task

**Vulnerability (CWE-1321, prototype pollution / inherited-property confusion).** A JavaScript library builds objects, tables and recorded configuration from structured input whose names are untrusted strings. At the pinned commit, a name taken from input can reach an object's prototype: a text-format map entry keyed `__proto__` becomes the returned map's prototype (the own key disappears and the value's members appear to belong to the map), and relatedly an absent name is sometimes answered with an inherited property, while a name that merely coincides with an inherited property is lost, crashes, or is combined with the inherited value.

**Base advisory:** GHSA-JFJ6-75FJ-8934 / CVE-2026-59876. Vulnerable commit `1aca107aa7938d1e49a25f9653186db2f40a0253`, published fix `9f97fe413072d3beb52c74e62d88ea8adc9444d8` (the fix commit is the direct child of the pinned commit). **Track: injected.** The published fix lands at the text-format site and several other sites; it leaves R1 and R2 open, and S1/S2 are injected sibling gaps our copy adds.

**What the task contains — one rule, 14 real levers to it, none named in the instruction** (no file, function, surface, format or count is given; the instruction states a single general property over the protected outcome):

| Lever | Class | Where | What reaches the rule |
|---|---|---|---|
| T1 | A — report target / published-fix landing point | `ext/textformat.js` (addMapEntry) | a text-format map entry keyed `__proto__` (brace, angle, list, scalar-map forms) |
| T2 | A — far site, same parser | `ext/textformat.js` (parseMapField/addField) | repeated/map field names that coincide with inherited properties |
| T3 | A — far, lower-level producer for both parsers | `src/enum.js` (values table) | an enum name inherited from `Object.prototype`, in text format and JSON |
| T4 | A — far, defaults/merge + reflection option API | `src/object.js` (getOption/setOption), `src/util/minimal.js` (merge) | an unset option read from the prototype; `ifNotSet` merge treating an inherited name as present |
| T5 | A — far, second parser (.proto source) | `src/parse.js` (aggregate option member) | an aggregate `.proto` option member named like an inherited property |
| T6 | A — far, second implementation (descriptor import) | `ext/descriptor.js` (Enum.fromDescriptor) | an imported enum value named `__proto__` carrying options |
| T7 | A — far, code-generation wrapper | `cli/targets/static.js` (emitted enum table) | an enum table emitted by the bundled static generator |
| T8 | A — far, descriptor importer lookup | `ext/descriptor.js` (mapEntries) | an imported field whose type name ends in an inherited property is built as a map entry |
| T9 | A — far, descriptor importer lookup | `ext/descriptor.js` (groupTypeNames) | an imported nested type named like an inherited property is marked a group |
| T10 | A — far, schema-text target | `cli/targets/proto.js` (consolidateExtends) | an extension whose target name coincides with an inherited property |
| R1 | B — real, unmodified upstream (still in current upstream) | `src/util.js` (setProperty) | a dotted setting whose segment matches an inherited property |
| R2 | B — real, unmodified upstream (still in current upstream) | `src/converter.js` (fromObject reads) | a converter reads each field from the input object without an own-property check |
| S1 | injected sibling (our copy only) | `src/object.js` (setParsedOption) | a single-segment fast path reads/writes the segment name directly |
| S2 | injected sibling (our copy only) | `src/util.js` (setProperty) | the unsafe-name guard applies only while recursing, so a final unsafe segment is written |

Each lever is reachable through the public API (`textformat.fromText` / `Type.fromText`, JSON parsing, `protobuf.parse`, `Type.fromObject`, `Enum` / `Enum.fromDescriptor` / `Root.fromDescriptor`, `getOption`/`setOption`, `util.merge`, `util.setProperty`, and the bundled `pbjs` static-module and proto targets).

**The rule (as given to the agent).** "A name the library takes from input is always treated as a name, never as a way to reach the machinery of the object that holds it." It is stated as one general property with sub-clauses: no prototype access or shared-built-in modification; data is stored as an own enumerable property under exactly that name with the ordinary prototype kept; lookups are exact (an entry not present as an own property is absent, never answered with an inherited property, for returned, internal and given tables, whether written, looked up or read back); ordinary inherited-looking declared names are ordinary data; everything built follows this; prototype-replacing names in recorded configuration are ignored (not stored, no error, the rest of the work proceeds); fill-only-absent counts an entry present only when it is own. No route, surface, file, function or count is named.

**Hidden tests.** 34 security tests (across `security/01…10_*.js`) and 23 functional tests (across `functional/01…09_*.js`). They drive the public API and assert behaviour (the `__proto__` key stays own data and the container keeps its ordinary prototype; inherited names are absent from returned/internal tables; declared shadowing names round-trip; unsafe settings are ignored while the surviving container stays). Reward = security pass fraction, or **0 if any functional test fails**.

## 2. How we know the task is fair

Before any model ran (build gate + fairness review):

| Check | Result |
|---|---|
| Vulnerable (nop) tree | fails all security tests, passes all functional tests (pre-upgrade: 0/31 sec, 22/22 func; the three new sibling-upgrade security tests also fail on the injected tree) |
| Reference fix (oracle) | 1.0 — closes every route (pre-upgrade 31/31 sec, 22/22 func; verified again for T8–T10 on the upgraded tree) |
| Each route left out in turn | fails only its own security test(s) with functional all passing — 15 `sf-miss-*` patches (T1–T10 incl. t4b, R1, R2, S1, S2, t8/t9/t10) |
| Over-broad fix (null-prototype maps) and refuse-all fix | each fails a functional test (`ff-overbroad.patch`, `ff-refuse-all.patch`) |
| Hardening fix and an alternative correct fix (`pass-alt` uses `Object.defineProperty` instead of the shared helper) | 1.0 each |
| Project's own suites | 270 area cases and the full `npm run test:sources` (2585 cases) pass on pinned+injected and on oracle |
| Independent pre-trial fairness review of every test against the instruction | **GATE_A: READY** — every security test covered by the one general rule read literally; no route-naming sentence needed |

In the 2026-10-20 patches stage, 16 checks matched their declared expectation in one clean run; the three sibling-upgrade checks (t8/t9/t10) were verified locally against the injected and oracle trees. **One combined full nop/oracle/patches re-gate after the sibling-injection upgrade is still pending** (manifest status: "Full nop/oracle/patches gate pending"); no image rebuild was needed for that upgrade.

**Fairness verdict (quoted).** "UNFAIRNESS gate: READY. Every security test is covered by P1–P7 read literally over the protected data/outcome; none needs a route-naming sentence. The natural correct fix following the stated mechanism (own-property lookups, null-prototype name tables, per-segment ignore of the prototype-replacing name) passes every test." The review marked only three tests medium-risk (never high) and all with "could a correct fix fail? — no". It recorded:

- **NEEDS_HUMAN_REVIEW: YES**, on two borderline points: confirm that "the rest of that work is carried out" is intended to keep the parent container after a lone unsafe final segment (`security/08` tests 4–5), and that `setOption` falls under "recorded configuration".
- **Required: generalize** — six instruction quotes that named object kinds/stages, to reword as the single property. Per `notes.md`, the subsequent sibling-injection upgrade rewrote `instruction.md` to one general property, removing every route/surface/stage/file/format sentence; the instruction now on disk is that general version.
- **Non-blocking quality/leniency gaps** (the review's §2c, "wrong fixes no test catches"): a name blacklist tuned to the probed names (`toLocaleString`, `__defineGetter__` never probed); JSON map keys named `__proto__` and JSON fields whose schema name shadows an inherited property (JSON covered only for enum names); a field literally named `__proto__` in text format / converter; descriptor option members of prototype-replacing shape outside enum options; storing a descriptor `__proto__` value as own data instead of ignoring it; shared built-ins beyond two probed ones; partial-record cleanup asserted only for enum lookups. These were flagged as quality-to-tighten, not fairness blockers.

## 3. Results, attempt by attempt (provisional — scores only, routes not yet audited)

Counted runs are the 2026-10-20 post-upgrade `auto_trial.out` set (the `[trial-done]` line in the pipeline log shows six values per model because logs accumulate; the first three per model — DeepSeek 0.8889/0.0/0.0, MiMo 0.0/0.0/0.0 — are from the earlier pre-upgrade trial and are **not** the counted set; the counted three match `auto_trial.out` and the `ACCEPTED` tally of 0p/3f/0e each):

| Model | Attempt | Reward | Security | Functional | Finish | Wall |
|---|---|---|---|---|---|---|
| DeepSeek | 1 | 0.9412 | 32/34 | all pass | success | ~32 min |
| DeepSeek | 2 | 0.9118 | 31/34 | all pass | success | ~56 min |
| DeepSeek | 3 | 0.9118 | 31/34 | all pass | success | ~33 min |
| MiMo | 1 | 0.4706 | 16/34 | all pass | success | ~178 min |
| MiMo | 2 | 0.9118 | 31/34 | all pass | success | ~62 min |
| MiMo | 3 | 0.7941 | 27/34 | all pass | success | ~77 min |

- No attempt reached 1.0; no attempt scored 0.0. Reward is a clean security fraction in every attempt (all functional passed), so each attempt's miss is **routes left open, nothing broken**.
- DeepSeek was tight and consistent (2–3 routes open each time). MiMo was more variable (one attempt matched DeepSeek's best at 31/34, but its other two left 7 and 18 security tests failing).
- **Which specific routes each attempt left open is not known.** No per-attempt transcript audit or per-test breakdown has been extracted. The security pass counts above are derived from reward × 34 (each an exact integer) and are defensible; the route-level attribution is not.

## 4. Why both models failed (provisional — not yet audited)

No transcript audit exists yet, so this section is inference from the task shape and the scores, not confirmed findings. What is defensible:

- Both models consistently closed most routes without breaking any legitimate behaviour (all functional tests passed on all six attempts), but neither closed all 34 security tests on any attempt.
- The task's lever set is the likely reason: the published-fix "near" sites (T1, T2) plus a long tail of "far" sites in different files, layers and tools — the lower-level enum values table (T3), the option/merge plumbing (T4), a second `.proto` parser (T5), the descriptor importer (T6, T8, T9), the static/proto code generators (T7, T10) — and two routes the published fix itself leaves open (R1, R2) plus two injected sibling gaps (S1, S2). A fix anchored on the parser or on the obvious `__proto__` key does not reach the tables and lookups two layers below or the build-time generators. The fairness review's leniency table names exactly these as the plausible partial fixes (e.g. "patch parser lookups, leave the values table"; "fix returned tables, leave internal/given tables"; "runtime-only generator fix").
- This matches MiMo's and DeepSeek's profiles on jackson-databind-sib2: a generic containment check covers the obvious sinks but misses routes living in a different file/feature.

The transcript audit (which routes each attempt left open, and why) must be run before any of this is stated as fact.

## 5. Evaluation setup

- Harness: Harbor with the Claude Code agent.
- Models: DeepSeek V4.1 Flash and MiMo-V2.6-Pro; up to 3 counted attempts each, early-exit on a solve (neither solved, so all 3 counted for both).
- Offline: the agent could reach only the model APIs; web tools disabled; the repository has no git history; hidden tests are copied in only after the agent stops.
- Reward = security pass fraction, 0 if any functional test fails; 1.0 = solve.
- What counts: a timeout counts as a failure; a provider or network-outage cut is not counted. All six counted attempts here reported `finish=success`, `rc=0` — none was a timeout.

## 6. What is needed before this is a fully confirmed breaker

1. Run the per-attempt transcript audit (per-test results + transcript) for all six counted attempts, to confirm which routes each model left open and that each failure is a genuine model defect.
2. Resolve the two **NEEDS_HUMAN_REVIEW** points (the surviving-container reading of `security/08` tests 4–5; `setOption` as "recorded configuration").
3. Write and wire `blind.patch` (`expect=pass`, `kind=blind`) and confirm a from-instruction blind fix scores 1.0 — currently intentionally absent.
4. Run the one combined full nop/oracle/patches re-gate after the 2026-10-20 sibling-injection upgrade (components already verified locally).
5. Optionally tighten the non-blocking leniency gaps from the fairness §2c (unprobed inherited names, JSON map-key/field cases, a literal `__proto__` field, extra shared built-ins).

Until items 1–4 are done, this is a **CONFIRMED-fairness, NOT-yet-audited both-model breaker**: the both-fail-3/3 result is real and the task is judged fair, but the per-attempt evidence and the final gate are outstanding.

## Appendix: what is in the task package

| What | Contents |
|---|---|
| Task | instruction (one general rule), environment (pinned + injection), reference fix, 34 security + 23 functional hidden tests |
| Validation | partial gate report, 19 patch checks (15 `sf-miss-*`, `ff-overbroad`, `ff-refuse-all`, `pass-hardening`, `pass-alt`), fairness review; blind patch pending |
| Attempts | per attempt: reward and finish status (counted set in `auto_trial.out`); per-test breakdown and transcript audit **not yet produced** |
