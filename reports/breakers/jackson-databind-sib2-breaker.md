# jackson-databind-sib2 — a task that DeepSeek V4.1 Flash and MiMo-V2.6-Pro both fail 3/3

**Status of 2026-10-16.** Sources: the task build and validation records, the pre-trial fairness review, every attempt's transcript, final code and per-test results, and the independent audit of every counted attempt.

## Summary

- **Result: both target models failed all 3 counted attempts.**
  - DeepSeek V4.1 Flash: 0.0, 0.0, 0.58.
  - MiMo-V2.6-Pro: 0.0, 0.58, 0.0.
- Every attempt finished on its own (no timeout): DeepSeek in 17–35 minutes, MiMo in 41–76 minutes of a 2-hour limit. Each attempt was audited independently and judged a genuine model failure with high confidence.
- The result does not hinge on one test. Every attempt failed at least two independent parts of the task. Remove any single part's tests and all 6 attempts still score below 1.0.
- The task is a real library with real gaps. It is FasterXML jackson-databind at the commit before a published authorization fix. The advisory's own flaw is combined with three further real routes to the same rule. Nothing is planted in the code.
- Why both models fail: they find the routes they leave open. They then either decide the route is out of scope, or close it in a way that breaks a legitimate value next to it.

## 1. The task

**Vulnerability (CWE-863, incorrect authorization).** A service binds untrusted JSON request bodies to Java objects and limits what each caller may set with `@JsonView`: a property marked for a privileged view must stay out of reach of a caller whose view does not include it. In the library, several deserialization routes ignore the active view, so an unprivileged request can set privileged fields.

**Base advisory:** GHSA-mhm7-754m-9p8w. Vulnerable commit d627a8a, upstream fix c628b35. The upstream fix closes only the route the advisory describes.

**What the task contains.** Four real routes to the same rule, all present unmodified at that commit:

| Route | What leaks | What must keep working next to it |
|---|---|---|
| 1. The advisory's own route: a polymorphic property whose subtype is chosen by a separate type-id field | the restricted property (and a restricted type id) | a visible type id must still bind when the value it selects is hidden |
| 2. The catch-all that collects unknown fields (`@JsonAnySetter`) | a privileged catch-all keeps collecting attacker keys; this route has **no view check at all** | a catch-all with no view restriction keeps working |
| 3. Object identity (`@JsonIdentityInfo`) | a privileged record id is written from the request, on field-built and constructor-built records | the same id must still resolve visible links between records in the request |
| 4. In-place update and merged defaults (`readerForUpdating(...).withView(...)`, `@JsonMerge`) on array-shaped beans | restricted values are overwritten on update | visible values after a hidden one bind in their own position |

**Report given to the agent.** It is written as a real bug report:
- the system;
- one example (route 1);
- the rule: no input may set a restricted property "whatever the type looks like, however the object is built or populated, and whether the input creates a new object or is applied to an existing one";
- the contracts: hidden input is ignored without error, and visible properties keep binding exactly as today, "including when they sit next to a hidden value or depend on one".

Routes 2–4 are not named, and neither is any file, function or count.

**Hidden tests.** 12 security tests (5 for route 1, 3 for route 2, 2 for route 3, 2 for route 4) and 25 functional tests. They drive the public `ObjectMapper` reader API and assert behaviour: for example, that the restricted value did not land, while a clean refusal is also accepted. Reward = the security pass fraction, or 0 if any functional test fails.

## 2. How we know the task is fair

Before any model ran:

| Check | Result |
|---|---|
| Vulnerable code | fails all 12 security tests, passes all 25 functional tests |
| Reference fix | 1.0, three times, identically |
| Blind fix (a fresh model saw only the report and the code, never the tests or the reference) | 1.0: it found every route |
| Hardening fix and an alternative correct fix, written differently from the reference | 1.0 each |
| The upstream advisory fix alone | fails: routes 2–4 stay open |
| A fix for each route left out in turn | fails the matching security tests (one wrong-fix patch per route) |
| A fix that skips the whole record id, and one that crashes instead of ignoring | fail the functional tests (links break, or the "ignored without error" contract breaks) |
| Independent fairness review of every test against the report | every test rated low or medium-low risk; no test needs a name the solver must guess |

In total, 12 wrong-fix patches behaved as declared, and the scripted gate passed.

## 3. Results, attempt by attempt

| Model | Attempt | Score | Security | Functional | Left open | Broke |
|---|---|---|---|---|---|---|
| DeepSeek | 1 | 0.0 | 8/12 | 22/25 | catch-all (route 2); a restricted type id (route 1) | a visible type id; visible record links |
| DeepSeek | 2 | 0.0 | 4/12 | 23/25 | routes 2, 3 and 4; a restricted type id | a visible type id |
| DeepSeek | 3 | 0.58 | 7/12 | 25/25 | catch-all; record id (both forms) | nothing |
| MiMo | 1 | 0.0 | 6/12 | 24/25 | catch-all; record id (both forms); a restricted type id | a visible type id |
| MiMo | 2 | 0.58 | 7/12 | 25/25 | catch-all; record id (both forms) | nothing |
| MiMo | 3 | 0.0 | 8/12 | 23/25 | catch-all; constructor-built record id | a visible type id; visible record links |

- All 6 left the catch-all open.
- 5 of 6 left a record-id write open.
- 4 of 6 broke a visible value next to a hidden one.
- 5 of 6 closed the update/merge route.

Three further attempts (one DeepSeek, two MiMo) were cut off at the same moment by a network outage on our side. They are not counted.

## 4. Why both models failed

### 4.1 The catch-all (all 6 attempts)

Both models found this route. They kept it open on purpose, or verified it with a probe that could not show the leak:
- DeepSeek, attempt 1, in its final summary: "One deliberate limit … still not honored."
- DeepSeek, attempt 3: its own probe printed the leak (`pub extra={a=1}` under the public view). It then reasoned that this was "arguably out of scope … upstream doesn't support it, I'll leave it".
- MiMo, attempt 1 decided "any-setter isn't a restricted property". Its probe used a catch-all without a view restriction, so it could not see the leak.
- MiMo, attempt 2: its own reproduction reported `FAIL any-setter hidden => {foo=bar}` (expected `{}`), and it still declared the bypass fixed.

What makes this route different is that the protection is not weak here, it is **absent**. Both models treat the absence as a design decision rather than as the same flaw.

### 4.2 The record id (5 of 6 left a write open; 2 broke visible links)

The library replaces the real id property with an internal stand-in that carries no view information. So a view check copied from other properties sees the id as visible.
- MiMo, attempt 2 added such a check to the stand-in; it checks the stand-in's own (empty) views, so the privileged id is still written.
- MiMo, attempt 3 gave the stand-in the id's views. That stops the field-built write but also stops the id from registering, so visible links between records no longer resolve. The constructor-built path, a separate site, still writes the id.
- DeepSeek, attempt 1 fixed the write but skipped the identity as well ("not set, not registered"), which broke the links.
- DeepSeek, attempt 3 listed the stand-in as a candidate but never probed or fixed it.

The correct fix keeps registering the identity and skips only the property write. The report asks for exactly this split ("visible properties keep binding … including when they … depend on one").

### 4.3 The advisory's own route (4 of 6 broke or missed a coupled value)

Even on the route the report describes, a hidden value and its visible type id are coupled.
- MiMo (attempts 1 and 3) and DeepSeek (attempts 1 and 2) skipped the hidden value early in a loop, which also skipped the code that assigns the visible type id: the visible field became null.
- DeepSeek (attempts 1 and 2) and MiMo (attempt 1) never checked the type id's own view, so a restricted type id still bound.

### 4.4 What they got right

Every attempt fixed the advisory's main example. 5 of 6 closed the update and merge route, and several hardened other creator paths beyond what was asked. The failures are not about understanding the bug: they come from scope decisions, and from fixes that do not respect a coupled legitimate value.

### 4.5 Model profiles on this task

- **DeepSeek V4.1 Flash:** fast (17–35 minutes). It audits widely, then explicitly rules routes out of scope ("deliberate limit", "upstream doesn't support it").
- **MiMo-V2.6-Pro:** slower (41–76 minutes), and more willing to add generic checks. A generic check closed the update route, but it missed routes the check does not reach (the catch-all, the stand-in id). In two attempts it declared success while its own probe showed a leak.

## 5. Evaluation setup

- Harness: Harbor with the Claude Code agent.
- Models: DeepSeek V4.1 Flash (reasoning effort max) and MiMo-V2.6-Pro; 3 counted attempts each, 2 hours per attempt.
- Offline: the agent could reach only the model APIs, and web tools were disabled. The repository has no git history, and the hidden tests are copied in only after the agent stops.
- Every counted attempt was audited before it counted:
  - no access to the hidden tests and no lookups;
  - grading started after the agent stopped, and the grader ran all 37 tests;
  - the score reflects real defects in the model's code.
- What counts: a timeout would not count as a failure, and an attempt cut off by a provider or network outage is not counted.

## 6. Where this sits among our tasks

- 30 task versions evaluated so far. This is the first that fails both models on every counted attempt.
- An earlier version of the same task (only the advisory route and the catch-all) failed DeepSeek in 6 of 6 attempts, but MiMo solved it. After the record-id and update routes were added, each with a coupled legitimate value, MiMo failed every attempt too.
- What doesn't break these models: mined advisories on their own, routes the report names, encoding variants, and extra verbs or protocols. Both models fix these reliably.
- What we are doing next: repeating this recipe on other libraries. The recipe is one authorization rule with several real routes, at least one route with no protection at all, and a legitimate value coupled to each hidden one.

## 7. Questions you may ask

**Is the failure the model's fault and not the task's?** A blind fix written from the report and the code alone scores 1.0, as do the reference, an alternative and a hardened fix. An independent review checked every test against the report before any trial. After each attempt, a separate audit read the transcript and code: in every attempt, the model found routes it then left open.

**Does it hinge on one test?** No. Every attempt failed at least two independent routes; discounting any one route's tests leaves all 6 attempts below 1.0.

**Could the model have seen the answer?** The routes beyond the advisory are not covered by the published fix. The agent could not reach the internet or the hidden tests, and the audit checked every transcript for this.

**What does a 0.58 or a 0.0 mean?**
- 0.58 means 7 of 12 attack routes were closed, with nothing broken.
- 0.0 means a legitimate behaviour was broken, since any functional failure scores 0. In every 0.0 attempt, routes were also left open.

## Appendix: what is in the task package

| What | Contents |
|---|---|
| Task | report (instruction.md), environment, reference fix, hidden tests |
| Validation | gate report, the 12 wrong-fix patches, the blind fix, the fairness review |
| Attempts | per attempt: score, per-test results, final code and the audit's findings |
