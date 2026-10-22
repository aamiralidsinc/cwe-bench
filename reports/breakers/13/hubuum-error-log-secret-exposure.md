# hubuum-error-log-secret-exposure — a task that DeepSeek V4.1 Flash and MiMo-V2.6-Pro both fail 3/3

**Status of 2026-10-21: confirmed both-model breaker, delivered.** The counted attempts were run on 2026-10-20/21 (UTC). Sources: the delivered task, the build and validation records, the fairness review, every attempt's transcript, final code and per-test results, and the independent audit of every counted attempt.

## Summary

- **Result: both target models failed all 3 counted attempts.**
  - DeepSeek V4.1 Flash: 0.0, 0.0, 0.0.
  - MiMo-V2.6-Pro: 0.0, 0.0, 0.0.
- Every counted attempt finished on its own (no timeout). Agent time was 26–29 minutes for DeepSeek and 62–104 minutes for MiMo, against a 2-hour limit.
- Every counted attempt was audited independently: all 6 were judged trustworthy and a genuine model failure, with high confidence.
- The task is a real Rust client library with a published information-exposure fix. The advisory's own sites sit next to three real routes the published fix never covered and two small same-class additions made for the task.
- Why both models fail: all 6 attempts closed every leak (24 of 24 security tests). But all 6 removed the leak by blanking a whole generic error type. That also deleted the task id and status from the error a failed export returns, which the report says must stay visible. A fix that breaks legitimate behaviour scores 0.

## 1. The task

**Vulnerability (CWE-532, sensitive information in diagnostics).** Applications embed this client library and routinely log the errors and values it returns with `{}` or `{:?}`. The library's default `Display` and `Debug` output, and the `std::error::Error::source` chain, include server-supplied content (error messages, response bodies, task summaries, payload data) and caller-supplied secrets, so these end up in application logs.

- **Project and language:** hubuum-client-rust (Rust), async and blocking clients.
- **Base advisory:** GHSA-2625-RW7M-5Q5X.
- **Vulnerable commit:** `9c123207eb141ef1cfc8f53af538a06eeb458461`, the direct parent of the **upstream fix** `5a5c275ffa45f342459b7d3e977926da643bde50`.

**What the task contains.** One rule, nine places where it is broken. Each row lists what must keep working next to the leak.

| Route | Origin | What leaks | What must keep working next to it |
|---|---|---|---|
| 1. HTTP error with a body | advisory's own site | server JSON message and plain-text body in the error's `Display`/`Debug` | accessors still return the original message, body, URL and status; method and status stay visible |
| 2. Decode, JSON-codec and retry-exhausted errors | advisory's own sites | server or transport text in `Display`, `Debug` and the `source` chain | valid responses still decode; malformed input still errors; requests still retry |
| 3. High-level run operations (export, backup, export template) on both clients | advisory's own sites | the server's task summary is copied into the error of a failed run | **the error must still show the task id and its status** |
| 4. Returned result values (tasks, task events, event sinks, subscriptions and deliveries, exports, imports) | advisory's own sites | summaries, payloads, tokens, configuration and nested link/detail values in `Debug` | fields and serialization unchanged; ids, names, statuses and counts stay in `Debug` |
| 5. Audit events | real upstream code the fix left open | summary and before/after snapshots | entity name and action stay visible |
| 6. Restore staging response | real upstream code the fix left open | the server's error string | id stays in `Debug`; error and status readable through fields |
| 7. Object and class history | real upstream code the fix left open | object data and class schema | names stay visible; data readable through fields |
| 8. A restore "run" convenience operation on both clients | added for the task | the server's restore error copied into the returned error | successful restore runs still succeed |
| 9. Per-sink delivery health | added for the task | a server `last_error` string nested in the health row | sink name stays visible; `last_error` readable through its field |

Routes 5–7 were confirmed to leak at the vulnerable commit and are still present in later upstream code. Routes 8–9 are small additions (one patch, applied at image build) in code the published fix never touches.

**Report given to the agent.** It is written as a bug report about logs, with no example and no list of places:
- the system: a client library whose returned values and errors applications write into their logs;
- the rule: "No server-supplied content and no caller-supplied secret may appear in the default `Display` or `Debug` representation of any error or result value the library returns, or anywhere reachable through the standard `std::error::Error::source` chain. This holds for every shape the library returns, including nested values, optional and required fields, containers, and values embedded in larger structures.";
- the contracts: the same data stays available through public fields and accessors, serialization is unchanged, and "Diagnostics must stay useful: identifiers, names, statuses, kinds, timestamps and counts that are not sensitive continue to be shown." Failures still return errors, retries still retry;
- constraints: fix the problem and its close variants, keep legitimate use working, do not special-case any example, do not look up the upstream fix.

No file, type, function, operation or count of places is named.

**Hidden tests.** 24 security tests (route 1: 2, route 2: 3, route 3: 2, route 4: 10, route 5: 1, route 6: 1, route 7: 2, route 8: 2, route 9: 1) and 14 functional tests (12 hidden plus 2 of the project's own pre-existing tests). They build the real async or blocking client on an in-process mock transport and call the public operations: typed get/list calls, the high-level run operations and raw calls. They then format the returned error or value with `{}` and `{:?}` and walk the `source` chain. Security tests assert that unique server or secret markers are absent. Functional tests assert that accessors and serialization still return the original data and that non-sensitive ids, names and statuses still appear. No test requires a particular redaction string or error type. **Reward** = 1.0 only if every test passes; otherwise the share of security tests passed, forced to 0 if any functional test fails.

## 2. How we know the task is fair

| Check | Result |
|---|---|
| Vulnerable code | fails all 24 security tests, passes all 14 functional tests |
| Reference fix | 1.0 (3 identical runs at the first gate; passed again after the final test revision on 2026-10-20) |
| Alternative correct fix (different wording, fixed-text redaction strategy) | 1.0 |
| Hardening fix (reference plus generic message redaction) | 1.0 |
| Blind fix (independent model, report and code only) | not run |
| The upstream advisory fix alone | not run as a separate patch; routes 5–9 are outside it by construction |
| One wrong-fix patch per route (reference with one route left out, 9 patches) | each fails exactly that route's security tests (1–10 failures) and no functional test |
| Over-broad fix (removes ids, names and statuses from diagnostics) | passes all security tests, fails 5 functional tests |
| Fairness review of every test against the report | verdict READY; every test rated low risk except two rated medium (the HTTP method and an audit action stay visible), which all 6 attempts passed |

In total, 12 check patches behaved as declared, and the scripted gate (vulnerable code, reference, patches) passed after the final test revision.

The functional test that decides this task's result checks one thing. When an export run fails, its error must contain the task id (`11`) and the word `failed`, in both `Display` and `Debug`. It never checks the secret and never requires an error type or exact wording. The vulnerable code passes it (its message is "Task {id} {status}: {summary}"), and so do the reference, alternative and hardening fixes.

## 3. Results, attempt by attempt

| Model | Attempt | Score | Security | Functional | Left open | Broke |
|---|---|---|---|---|---|---|
| DeepSeek | 1 | 0.0 | 24/24 | 13/14 | nothing | failed-run error lost task id and status (renders `API error: [REDACTED]`) |
| DeepSeek | 2 | 0.0 | 24/24 | 13/14 | nothing | same (renders `API error`) |
| DeepSeek | 3 | 0.0 | 24/24 | 13/14 | nothing | same (renders `API error: [REDACTED]`) |
| MiMo | 1 | 0.0 | 24/24 | 13/14 | nothing | same (renders `API error`) |
| MiMo | 2 | 0.0 | 24/24 | 13/14 | nothing | same (renders `API error`) |
| MiMo | 3 | 0.0 | 24/24 | 13/14 | nothing | same (renders `API error: [REDACTED]`) |

- All 6 closed every leak, including the three uncovered upstream routes and both additions.
- All 6 failed the same functional test, `runner_error_keeps_task_identity_and_status`, and passed the other 13.
- All 6 had the same cause: the generic error variant that carries a free-text message was blanked in both `Display` and `Debug`.
- A duplicate DeepSeek attempt 1, launched a minute earlier, scored the same (24/24, 13/14, 0.0). It is not counted.

## 4. Why both models failed

### 4.1 Broken: the failed-run error lost its task id and status (all 6 attempts)

The library reports a failed export, backup or export-template run as a generic API error. Its message is built from three values: the task id, the status and the server's task summary. Only the summary is server content. The correct fix drops the summary where the message is built and keeps the id and status. The reference does this with a structured error that holds only the id and status.

Every attempt instead changed the generic error variant itself, so its `Display` and `Debug` print nothing of the message:
- DeepSeek attempt 1: `Self::Api(_) => f.write_str("API error: [REDACTED]")`; DeepSeek attempt 2: `Self::Api(_) => f.write_str("API error")`.
- MiMo attempts 1 and 2: the display text became `#[error("API error")]`; MiMo attempt 3: `#[error("API error: [REDACTED]")]`.
- None of the 6 changed the three run operations that build this message.

The grader's output is the same in all 6: `task identity missing: API error` or `task identity missing: API error: [REDACTED]`.

### 4.2 They knew the rule and stated it, but did not apply it here

Each model wrote down the "keep ids and statuses" contract, and some read the exact message format, but none checked it at this site:
- DeepSeek attempt 1 searched for the places that build this error; its tool output showed the format `"Task {} {}: {}"` followed by `task.id`. Its final summary still says diagnostics continue "to show method, status, IDs, limits, counts".
- DeepSeek attempt 3: "IDs, names, statuses, kinds, timestamps, counts, and boolean flags remain visible."
- MiMo attempt 1 ran a command it described as "Read ApiError::Api construction sites", then reported that "status codes, methods, attempt counts, task ids, and limits stay visible."
- MiMo attempt 2 read the same sites and wrote that `Display` "now reports only structured metadata (`method`, `status`, `task_id`, counts)."
- MiMo attempt 3's plan: "`Display`/`Debug`/`source` show only identifiers, names, statuses, kinds, timestamps, and counts."

The audits' conclusion for every run: "over-broad redaction, a genuine model shortfall on a fair, jointly-satisfiable contract -- not a test, instruction, or infrastructure fault."

### 4.3 What they got right

The breadth of this task did not defeat either model. Every attempt redacted the HTTP, decode, JSON and retry errors and cut the `source` chain. Every attempt also covered all result models, including nested containers, the audit, restore-staging and history routes that the published fix never touched, and both added routes. Several also hardened types the tests do not reach, such as the derive macro for generated resource models and pagination cursors. The failure is about precision: the fix was placed at the shared error type instead of at the sites that build the message, and the coupled non-sensitive values were lost with the secret.

### 4.4 Model profiles on this task

- **DeepSeek V4.1 Flash:** fast (26–29 minutes, 190–312 turns). It changed 19–27 files in each attempt and redacted broadly.
- **MiMo-V2.6-Pro:** slower (62–104 minutes, 159–278 turns). In attempts 2 and 3 it wrote its own probe programs to check the rule end to end; they did not catch that a failed run's error lost its id and status.

## 5. Evaluation setup

- Harness: Harbor with the Claude Code agent; web tools (WebSearch, WebFetch) disabled.
- Models: DeepSeek V4.1 Flash (reasoning effort max) and MiMo-V2.6-Pro; 3 counted attempts each; 2 hours per attempt.
- Offline: network limited to the model APIs. The repository has no git history, and documentation files that name the advisory are removed from the image. The hidden tests are copied in only after the agent stops.
- Grading: after the agent stopped, the grader ran the 24 security tests, the 12 hidden functional tests and the 2 pre-existing project tests. The delivered package grades the agent's source changes in a separate grader container; its report, hidden tests, scoring and reference fix are identical to the version that was run.
- Every counted attempt was audited by an independent model (Claude Opus 5.5, high effort) before it counted. The audit confirmed:
  - no reads of the hidden tests and no lookups of the upstream fix;
  - no agent tool calls during grading, no timeout and no provider error;
  - the failing test is stated in the report and passed by a correct fix.
- What counts: an attempt stopped by a provider or network error is not counted. None of the counted attempts was.

## 6. Questions you may ask

**Is the failure the model's fault and not the task's?** The report states the contract the models broke ("identifiers ... statuses ... continue to be shown"). The vulnerable code and three different correct fixes (reference, alternative, hardening) all pass the deciding test. The test checks only that the id and the status word appear, not any wording or error type. Each model wrote this contract down in its own summary.

**Does it hinge on one test?** Yes, on one functional check, and by design. This task tests whether a model can remove a secret from a message while keeping the non-sensitive values built into the same message. Every attempt closed all 24 leaks, so the security breadth did not separate them; the coupled value did. All 6 attempts failed that check for the same reason and in the same way. A blanket redaction of every API error message does pass the security tests, but the report explicitly rules it out.

**Could the model have seen the answer?** The agent had no internet or git history, and could not see the hidden tests; the audit checked every transcript for this. No transcript mentions the hidden test files or the advisory.

**What does a 0.0 mean here?** In every attempt the leaks were closed (24/24). The 0.0 means a legitimate behaviour was broken: an application that logs a failed export can no longer tell which task failed or how. Any functional failure scores 0.

## Appendix

**Task package** (`tasks/hubuum-error-log-secret-exposure/`):

| What | Contents |
|---|---|
| `instruction.md` | the report given to the agent |
| `environment/` | agent image: hubuum-client-rust at the vulnerable commit, `injection.patch` (routes 8–9), offline Rust toolchain with dependencies prefetched |
| `solution/` | reference fix (`fix.patch`) and `solve.sh` |
| `tests/` | grader image, `test.sh`, `score.py`, `junit.py`, 24 security tests (`security/sec_hubuum.rs`), 12 functional tests (`functional/fun_hubuum.rs`) and the project's own `foundations.rs` |
| `task.toml` | metadata (CWE-532, advisory, commits), 2-hour agent limit, agent offline, separate grader |

**Internal slug:** `hubuum-client-rust-ds`.

**Sources used:**
- Delivered task and the `hubuum-error-log-secret-exposure` section of RESULTS.md and README.md (client repository).
- Build records for `hubuum-client-rust-ds`: notes.md, manifest.json, FAIRNESS.md, gate_report.partial.json, recover.log, checks/, runs logs, trial_detail.json.
- Counted attempts: DeepSeek jobs `hubuum-client-rust-ds-deepseek-r1-20261020-233222-n001`, `-r2-20261021-000039-n002`, `-r3-20261021-002825-n003`; MiMo jobs `hubuum-client-rust-ds-mimo-r1-20261021-005856-n004`, `-r2-20261021-024403-n005`, `-r3-20261021-034659-n006`. Each has result.json, per-test results, grader log, final code, transcript and audit (POSTMORTEM.json).
- Uncounted attempt: `hubuum-client-rust-ds-deepseek-r1-20261020-233121-n001` (duplicate launch).
- Trials index (TRIALS-INDEX.csv).
