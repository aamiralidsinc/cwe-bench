# jackson-databind-jsonview-bypass — a task that DeepSeek V4.1 Flash and MiMo-V2.6-Pro both fail 3/3

**Status of 2026-10-21: confirmed both-model breaker, delivered.** The counted attempts were run on 2026-10-16. Sources: the delivered task, the build and validation records, the pre-trial fairness review, every attempt's transcript, final code and per-test results, and the independent audit of every counted attempt.

## Summary

- **Result: both target models failed all 3 counted attempts.**
  - DeepSeek V4.1 Flash: 0.0, 0.0, 0.58.
  - MiMo-V2.6-Pro: 0.0, 0.58, 0.0.
- Every counted attempt finished on its own (no timeout). Agent time was 18–34 minutes for DeepSeek and 40–76 minutes for MiMo, against a 2-hour limit.
- Every counted attempt was audited independently: all 6 were judged trustworthy and a genuine model failure, with high confidence.
- The result does not hinge on one test. Every attempt failed at least two independent parts of the task, and removing any one route's tests leaves all 6 attempts below 1.0.
- The task is a real library with real gaps. It is FasterXML jackson-databind at the commit before a published authorization fix. The advisory's own flaw sits next to three further real routes to the same rule. Nothing is planted in the code.
- Why both models fail: they find the routes they leave open, then either decide a route is out of scope, or close it in a way that breaks a legitimate value coupled to the hidden one.

## 1. The task

**Vulnerability (CWE-863, incorrect authorization).** A service binds untrusted JSON request bodies to Java objects and limits what each caller may set with `@JsonView`: a property marked for a privileged view must stay out of reach of a caller whose view does not include it. In the library, several deserialization routes ignore the active view, so an unprivileged request can set privileged fields.

- **Project and language:** FasterXML jackson-databind (Java).
- **Base advisory:** GHSA-mhm7-754m-9p8w.
- **Vulnerable commit:** d627a8a (`d627a8a86fcb062429282f79f3f256f181ed2c7b`). **Upstream fix:** c628b35, which changes only the external-type-id handler, the route the advisory describes.

**What the task contains.** Four real routes to the same rule. All are present, unmodified, at the vulnerable commit; the image checks out that commit with no injected code.

| Route | Origin | What leaks | What must keep working next to it |
|---|---|---|---|
| 1. A polymorphic property whose subtype is chosen by a separate type-id field | the advisory's own route | the restricted property, and a restricted type id | a visible type id must still bind when the value it selects is hidden, and a visible value must still bind when its type id is hidden |
| 2. The catch-all that collects unknown fields (`@JsonAnySetter`) | real upstream code the fix left open; this route has **no view check at all** | a privileged catch-all keeps collecting attacker keys (map field, setter method and JSON-node forms) | a catch-all with no view restriction keeps working under any view |
| 3. Object identity (`@JsonIdentityInfo` with a property-based id) | real upstream code the fix left open | a privileged record id is written from the request, on field-built and constructor-built records | the same id must still resolve visible links between records in the same request |
| 4. In-place update and merged defaults on array-shaped beans (`readerForUpdating(...).withView(...)`, `@JsonMerge`) | real upstream code the fix left open | restricted values are overwritten | a visible value after a hidden structured value binds in its own position |

The two neighbouring fresh-read methods for array-shaped beans already check views; only the in-place update method does not.

**Report given to the agent.** It is written as a real bug report:
- the system: request bodies bound with the caller's view active, for new records and partial updates;
- one example (route 1);
- the rule: "While a view is active, no input may set a property that is restricted to views the active view does not include. This holds for every kind of deserialization: whatever the type looks like, however the object is built or populated, and whether the input creates a new object or is applied to an existing one.";
- the contracts: restricted input is "ignored without an error"; visible properties "keep binding exactly as they do today, including when they sit next to a hidden value or depend on one"; privileged and no-view reads are unchanged;
- constraints: fix the library itself for every route, keep legitimate use working, do not special-case the example, do not look up an upstream fix.

Routes 2–4 are not named, and neither is any file, function or count of routes.

**Hidden tests.** 12 security tests (5 for route 1, 3 for route 2, 2 for route 3, 2 for route 4) and 25 functional tests (9, 6, 4 and 6 for the same areas). They compile the agent's version of the library and drive the public `ObjectMapper` reader API, for example `readerWithView(View).forType(T).readValue(json)` and `readerForUpdating(existing).withView(View)`. They assert behaviour only: that the restricted value did not land (the route 3 and route 4 security tests also accept a clean refusal), and that legitimate values still bind. **Reward** = 1.0 only if every test passes; otherwise the share of security tests passed, forced to 0 if any functional test fails.

## 2. How we know the task is fair

All checks below were completed on 2026-10-16. The fairness review was written before any model ran; the attempts were counted only after the scripted gate passed.

| Check | Result |
|---|---|
| Vulnerable code | fails all 12 security tests, passes all 25 functional tests |
| Reference fix | 1.0 in three separate runs |
| Blind fix (an independent model saw only the report and the code, never the tests or the reference) | 1.0; its notes show it found every route by reading the code |
| Alternative correct fix, written differently in every part | 1.0 |
| Hardening fix (reference plus extra view checks) | 1.0 |
| The upstream advisory fix alone | fails: 5/12 security, routes 2–4 stay open |
| The predecessor task's reference (route 1 + route 2 only) | fails: 8/12 security |
| One wrong-fix patch per gap in routes 3 and 4 (skip route 3; skip only its constructor form; skip route 4; check the id stand-in's own views) | each fails the matching security tests |
| Over-broad or crashing fixes (drop the record id entirely; refuse with an error; drop every catch-all under a view) | each fails the functional tests (links break, the "ignored without an error" contract breaks, or legitimate catch-alls break) |
| Independent fairness review of every test against the report | verdict READY; every test rated low risk except the two record-link tests, rated medium-low; no wording change required |

In total, 12 check patches behaved as declared, and the scripted gate (vulnerable run, reference runs, patch checks) passed.

## 3. Results, attempt by attempt

| Model | Run | Score | Security | Functional | Left open | Broke |
|---|---|---|---|---|---|---|
| DeepSeek | 1 | 0.0 | 8/12 | 22/25 | catch-all (route 2); a restricted type id (route 1) | a visible type id; visible record links (both forms) |
| DeepSeek | 2 | 0.0 | 4/12 | 23/25 | routes 2, 3 and 4; a restricted type id | a visible type id; a visible value whose type id is hidden |
| DeepSeek | 3 | 0.58 | 7/12 | 25/25 | catch-all; record id (both forms) | nothing |
| MiMo | 1 | 0.0 | 6/12 | 24/25 | catch-all; record id (both forms); a restricted type id | a visible type id |
| MiMo | 2 | 0.58 | 7/12 | 25/25 | catch-all; record id (both forms) | nothing |
| MiMo | 3 | 0.0 | 8/12 | 23/25 | catch-all; constructor-built record id | a visible type id; visible record links (field-built form) |

- All 6 attempts left the catch-all open.
- 5 of 6 left a record-id write open.
- 4 of 6 broke a visible value next to a hidden one, which forces the score to 0.
- 5 of 6 closed the in-place update and merged-defaults route.
- No attempt scored above 0.58; the best attempts closed 7 of 12 attack cases.

Three further attempts (one DeepSeek, two MiMo) stopped at the same moment with an API error ("Can't reach the API server … (EAI_AGAIN)"). They are not counted.

## 4. Why both models failed

### 4.1 Left open: the catch-all (all 6 attempts)

Both models found this route. They kept it open on purpose, or checked it with a probe that could not show the leak:
- DeepSeek, run 1, in its final summary: "One deliberate limit: `@JsonView` on an `@JsonAnySetter` is still not honored … and they are not named properties."
- DeepSeek, run 3: its own probe printed the leak (`pub extra={a=1}` under the public view). It then reasoned that the case was "arguably out of scope" and concluded: "Given upstream doesn't support it, and the described example is about external type ids, I'll leave it."
- MiMo, run 1, while planning: "Maybe `@JsonAnySetter`? (probably not - any-setter isn't a restricted property)". Its probe used a catch-all with no view restriction, so it could not see the leak.
- MiMo, run 2: its own reproduction printed `FAIL any-setter hidden => {foo=bar} (expected {})`, and it still declared the bypass fixed (audit).
- DeepSeek run 2 and MiMo run 3 never changed the catch-all; MiMo run 3's only probe also used an unrestricted catch-all.

On this route the protection is not weak, it is **absent**. Both models treat the absence as a design decision rather than as the same flaw the report describes.

### 4.2 Left open or broken: the record id (5 of 6 left a write open; 2 broke visible links)

The library replaces the real id property with an internal stand-in that carries no view information, so a view check copied from ordinary properties sees the id as visible.
- MiMo, run 2, added a view check to the stand-in. It checks the stand-in's own (empty) views, so the privileged id is still written; the constructor-built path was not touched.
- MiMo, run 3, gave the stand-in the real id's views. That stops the field-built write, but it also stops the identity from registering, so the visible link `"next": 7` no longer resolves. The constructor-built path, a separate site, still writes the id.
- DeepSeek, run 1, fixed the write but also skipped the identity: hidden ids are "not set, not registered". This broke the links in both forms.
- DeepSeek, run 3, listed the stand-in as a candidate but never probed or fixed it. DeepSeek run 2 and MiMo run 1 did not reach it.

The correct fix keeps registering the identity and skips only the property write. The report asks for this split: visible properties keep binding "including when they … depend on one", and hidden input is "ignored without an error".

### 4.3 Broken: the advisory's own route (4 of 6 broke a coupled value)

Even on the route the report describes, a hidden value and its visible type id are coupled.
- DeepSeek (runs 1 and 2) and MiMo (runs 1 and 3) skipped the hidden value early in a loop, which also skipped the code that assigns the visible type id. The visible field became null.
- DeepSeek run 2 also dropped a hidden type id before it was recorded, so a visible value could no longer resolve its subtype.
- DeepSeek (runs 1 and 2) and MiMo (run 1) never checked the type id's own view, so a restricted type id still bound.
- The probes did not cover the coupled case: DeepSeek run 2 checked "only a field-based bean", and MiMo run 3's probe "tested only the reverse case" and it reported "All probes pass" (audits).

### 4.4 What they got right

Every attempt fixed the advisory's main example. 5 of 6 closed the in-place update and merged-defaults route, and several hardened other creator paths beyond what was asked. The failures are not about understanding the bug: they come from scope decisions, and from fixes that do not respect a coupled legitimate value.

### 4.5 Model profiles on this task

- **DeepSeek V4.1 Flash:** fast (18–34 minutes). It audits widely, then explicitly rules routes out of scope ("deliberate limit", "upstream doesn't support it").
- **MiMo-V2.6-Pro:** slower (40–76 minutes), and more willing to add generic checks. In run 1 a generic check on ordinary properties closed the update route, but it does not reach the catch-all or the id stand-in. In run 2 it declared success while its own reproduction showed a leak.

## 5. Evaluation setup

- Harness: Harbor with the Claude Code agent.
- Models: DeepSeek V4.1 Flash (reasoning effort max) and MiMo-V2.6-Pro; 3 counted attempts each; 2 hours per attempt.
- Offline: the agent could reach only the model APIs, and web tools were disabled. The repository has no git history, and the hidden tests are not in the agent's environment.
- Grading: after the agent stopped, the grader compiled the agent's library and ran all 37 hidden tests. The delivered package grades the agent's source changes in a separate grader container; its report, hidden tests and reference fix are identical to the version that was run.
- Every counted attempt was audited by an independent model before it counted. The audit confirmed:
  - no access to the hidden tests, no network and no lookups;
  - the session ended on its own, and the agent made no tool calls during grading;
  - every failing test is stated in the report and passed by a correct fix, so the score reflects real defects in the model's code.
- What counts: an attempt stopped by a provider or network error is not counted.

## 6. Questions you may ask

**Is the failure the model's fault and not the task's?** A blind fix written from the report and the code alone scores 1.0, as do the reference, an alternative and a hardened fix. An independent review checked every test against the report before any attempt. After each attempt, a separate audit read the transcript and code: in every attempt, the model left routes open that it had found or listed.

**Is a view-restricted catch-all really a "restricted property"?** The report's rule covers every property annotated for a view the caller lacks, "whatever the type looks like", and says other ways of reading input leak "in the same way". The fairness review and all six audits judged the catch-all tests fair, and in two attempts the model's own probe showed the leak.

**Does it hinge on one test?** No. Every attempt failed at least two independent routes; discounting any one route's tests leaves all 6 attempts below 1.0.

**Could the model have seen the answer?** The published fix covers only route 1, so routes 2–4 cannot be copied from it. The agent could not reach the internet or the hidden tests, and the audit checked every transcript for this.

**What do the scores mean?**
- 0.58 means 7 of 12 attack cases were closed, with nothing broken.
- 0.0 means a legitimate behaviour was broken, since any functional failure scores 0. In every 0.0 attempt, routes were also left open.

**How does it relate to simpler versions?** The plain advisory task (route 1 only) was solved by both models. A version with routes 1 and 2 failed DeepSeek in 6 of 6 attempts, but MiMo solved it. Adding routes 3 and 4, each with a coupled legitimate value, made MiMo fail every attempt too.

## Appendix

**Task package** (`tasks/jackson-databind-jsonview-bypass/`):

| What | Contents |
|---|---|
| `instruction.md` | the report given to the agent |
| `environment/` | agent image: jackson-databind at the vulnerable commit, offline Java toolchain, `compile-lib.sh` |
| `solution/` | reference fix (`fix.patch`, five library files) and `solve.sh` |
| `tests/` | grader image, `test.sh`, `score.py`, 12 security and 25 functional JUnit tests with a shared model file |
| `task.toml` | metadata (CWE-863, advisory, commits), 2-hour agent limit, agent offline, separate grader |

**Internal slug:** `jackson-databind-sib2`.

**Sources used:**
- Delivered task and the `jackson-databind-jsonview-bypass` section of RESULTS.md (client repository).
- Build records for `jackson-databind-sib2`: notes.md, manifest.json, gate_report.json, FAIRNESS.md, blind_mechanisms.md, checks/, runs logs.
- Counted attempts (2026-10-16): DeepSeek jobs r11, r12, r14 and MiMo jobs r11, r13, r22, each with result.json, per-test results, final code, trajectory, audit (POSTMORTEM.json) and readable transcript.
- Uncounted attempts: DeepSeek r13, MiMo r12 and r21 (API error).
- Audit ledger (build/audit/ledger.md) and the trials index.
