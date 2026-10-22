# mockoon-admin-api-missing-auth — a task that DeepSeek V4.1 Flash and MiMo-V2.6-Pro both fail 3/3

**Status of 2026-10-21.** Sources: the delivered task, the task build and validation records, the fairness review, every counted attempt's transcript, final code and per-test results, and the independent audit of every counted attempt.

## Summary

- **Result: both target models failed all 3 counted attempts.**
  - DeepSeek V4.1 Flash: 0.93, 0.96, 0.93 (exact: 0.9259, 0.963, 0.9259).
  - MiMo-V2.6-Pro: 0.93, 0.93, 0.96 (exact: 0.9259, 0.9259, 0.963).
- Every attempt finished on its own within the 2-hour limit: DeepSeek in 12–24 minutes of agent time, MiMo in 47–58 minutes.
- Each counted attempt was audited independently and judged a genuine model failure ("model-failed", trustworthy, high confidence).
- No attempt broke legitimate behaviour: all 6 passed 15/15 functional tests.
- Why both fail: all 6 attempts redacted credentials only where they arrive (the header entries) and missed the same credential when a mocked response reproduces it elsewhere in the recorded traffic. 4 of 6 also kept accepting the secret as a query parameter on ordinary requests, which the report forbids.

## 1. The task

**Vulnerability (CWE-306, missing authentication for a critical function; also tagged CWE-352 and CWE-942).** Mockoon is a TypeScript tool that runs local mock APIs. Its server runtime also exposes a management API under `/mockoon-admin*`. The desktop app, the CLI and scripts use it to read recorded traffic, follow live events, and change global variables, environment variables, data buckets and the environment itself. At the pinned commit, this management API:
- requires no credential;
- grants cross-origin access to every web origin;
- exposes recorded request and response headers (credentials, cookies, API keys);
- lets a caller write arbitrary process-environment variables.

**Base advisory:** GHSA-RQX4-3F6Q-3X2V / CVE-2026-59148. Vulnerable commit b42bdfb, upstream fix c420b5a.

**What the task contains.** One rule (the configured secret is required, credentials never leave in recorded traffic, cross-origin grants only for listed origins, environment writes only under the configured prefix), reached through these routes:

| Route | What leaks | What must keep working next to it | Origin |
|---|---|---|---|
| T1. Every management route and verb (reads, writes, purge, environment update, event stream) | unauthenticated reads and changes; a query-string token accepted on an ordinary request | management with the configured token; the query-string token on the event stream | the advisory's own route |
| T2. Runtime transaction logging (a second, separate redaction routine) | cookie and API-key values written to the log (only `authorization` was masked) | transaction logging still records transactions | the advisory's fix, far site |
| T3. Event stream, replay and live | raw sensitive header values | live events delivered with the token | the advisory's fix, far site |
| T4. Environment-variable write | a key outside the configured prefix reaches the process environment under its bare name | prefixed writes; reads keep their automatic prefix | the advisory's fix, far site |
| T5. Serverless wrapper | the wrapper does not pass on the configured token and origins | the serverless listener serves mocks and management with the token | the advisory's fix, far site |
| T6. A management WebSocket log stream | answers without a token and streams raw records; upgrade requests bypass the web framework's middleware | the stream delivers records with the token | code added for the task |
| T7. A bulk environment-variable import | writes keys outside the prefix | prefixed bulk imports | code added for the task |
| T8. A mocked response that reproduces an incoming credential (Mockoon responses are templated) | the credential lands in the recorded response body and in a non-sensitive response header, outside the header slot that redaction visits | header names and non-sensitive values stay available | real upstream code the fix left open |
| Cross-origin grants on management responses | a grant to unlisted origins | listed origins are echoed; `*` only when listed | the advisory's own route |

T6 and T7 are added by a small patch applied in the image before the agent starts. They are written as a maintainer would write them: live log streaming next to the existing WebSocket route handling, and a bulk importer next to the existing environment-variable routes. The upstream fix never touches those lines.

**Report given to the agent.** It is written as a bug report, with no file, function or route names:
- the system, and the observed impact;
- the security property, including:
  - "State and recorded traffic that the runtime makes available to remote callers, and every update of it, are accessible only to a caller presenting the secret the operator configured. This holds for every exposure, every operation and every way the runtime is run or embedded."
  - "No record of served traffic that the runtime produces, in any form or for any consumer, may contain the value of a sensitive request or response header."
- the contracts: the option and environment names for the secret and the allowed origins, the list of sensitive headers, and the rule that a client that cannot set headers may send the secret as a `token` query parameter, but "that form is never a substitute for the header on a request that can carry one";
- the constraints, including "Fix the problem and its close variants, not just the examples above."

**Hidden tests.** 27 security tests and 15 functional tests:

| Group | Security tests |
|---|---|
| Authentication (T1, plus the WebSocket stream of T6) | 11 |
| Redaction (listing, event stream replay and live, WebSocket stream, runtime log, reproduced credential) | 6 |
| Cross-origin grants | 4 |
| Environment-write scope (T4, T7) | 4 |
| Serverless authentication (T5) | 2 |

The tests start real Mockoon server instances on loopback, and a serverless listener mounted on a real HTTP server. They send real HTTP, event-stream and WebSocket requests, and attach a logger to the runtime's own transaction-log hook. They assert outcomes:
- a refusal is any client error with no side effect, never one exact status;
- secret values are absent from every exposed form;
- header names are still present.

Reward = 1.0 if every test passes. Otherwise it is the security pass fraction (capped below 1), or 0 if any functional test fails.

## 2. How we know the task is fair

| Check | Result |
|---|---|
| Vulnerable code (pinned commit plus the added routes) | fails 27/27 security tests, passes 15/15 functional (scripted gate, container run) |
| Reference fix | passes 27/27 and 15/15 (scripted gate, container run) |
| Blind fix (a fresh model sees only the report and the code) | not run |
| An alternative correct fix (refuses outside-prefix writes instead of prefixing them) and a hardening fix (extra sensitive headers, `no-store` caching) | 1.0 each |
| The upstream advisory fix alone | not run as a separate patch. The closest check is the earlier reference fix: it covers every site the upstream fix touches plus T6 and T7, but redacts only the header entries. It scores 26/27: only the reproduced-credential test fails. |
| One wrong-fix patch per route | 12 patches, each failing security tests as declared: each of T1–T4, T6, T7 and T8 left open; refusal by crashing; only the logs route protected; only reads protected; any non-empty credential accepted; no configured secret means open |
| Over-broad fixes | 3 patches fail the functional tests as declared: refuse every management request; require the secret on ordinary mock routes too; serverless wrapper drops the configured token |
| Fairness review of every test against the report (run after the trials) | verdict READY: every test is derivable from the report; no test needs a name the solver must guess; refusals accept any client error or silence; environment tests accept both auto-prefixing and refusal. It flagged two judgement calls for human review; neither concerns a test that any counted attempt failed. |

In total, 17 declared patches (12 security-fail, 3 functional-fail, 2 correct) behaved as declared, and the scripted gate passed.

## 3. Results, attempt by attempt

| Model | Attempt | Score | Security | Functional | Left open | Broke |
|---|---|---|---|---|---|---|
| DeepSeek | 1 | 0.9259 | 25/27 | 15/15 | reproduced credential (T8); query token on an ordinary request | nothing |
| DeepSeek | 2 | 0.963 | 26/27 | 15/15 | reproduced credential (T8) | nothing |
| DeepSeek | 3 | 0.9259 | 25/27 | 15/15 | reproduced credential (T8); query token on an ordinary request | nothing |
| MiMo | 1 | 0.9259 | 25/27 | 15/15 | reproduced credential (T8); query token on an ordinary request | nothing |
| MiMo | 2 | 0.9259 | 25/27 | 15/15 | reproduced credential (T8); query token on an ordinary request | nothing |
| MiMo | 3 | 0.963 | 26/27 | 15/15 | reproduced credential (T8) | nothing |

- All 6 left the reproduced credential exposed.
- 4 of 6 accepted the query-string token on an ordinary request.
- All 6 closed T1–T7: every route and verb authenticated, the WebSocket stream and the bulk import covered, the serverless wrapper wired, all exposures redacted at the header level.
- All 6 kept every legitimate behaviour (15/15 functional).
- One further DeepSeek attempt was launched twice by mistake, a minute apart. The duplicate is not counted; it scored the same 0.9259 with the same two failures.

## 4. Why both models failed

### 4.1 The reproduced credential (all 6 left it open)

Every attempt placed redaction where records are created, and replaced the values in the sensitive header slots. DeepSeek, attempt 1, final summary: the seven header values "are replaced with `***` at record creation". None scrubbed the same value where a templated response reproduces it. Several attempts considered this path and ruled it out of scope:
- DeepSeek, attempt 1: "`Transaction` body could echo secrets? Not our concern (body is user data)."
- DeepSeek, attempt 3: "body may contain tokens) but spec only talks headers. Don't redact bodies."
- MiMo, attempt 1, on templating: "does the templating system or response rules have access to the raw request headers? Yes, but that's not a \"record\". That's the live request. Fine."
- MiMo, attempt 3: "What about the request body containing secrets? Not in scope — only headers."

MiMo, attempt 2 read "the value" strictly for the header slot itself ("Keeping a scheme prefix retains part of that value. Let me redact uniformly"), but did not apply the same reading to the value's other copies in the record.

The report asks that no record "in any form" contain "the value of a sensitive request or response header". The reference fix collects the sensitive values of each transaction, redacts the header entries, then scrubs those values from every string in the record. The runtime log uses the same function.

### 4.2 The query-string token (4 of 6 accepted it on ordinary requests)

The report allows the `token` query parameter only for a client that cannot set request headers, and says it "is never a substitute for the header on a request that can carry one". The failing attempts reinterpreted this as a precedence rule: if an `Authorization` header is present, ignore the query. A plain request with only `?token=` was then accepted on every management route.
- DeepSeek, attempt 1: "Enforcement could be: query param accepted on all admin routes; 'never a substitute' means if Authorization header is present and wrong, don't fall back to query token."
- DeepSeek, attempt 3: "if the header exists, use only header. If no Authorization header, allow `token` query param."
- MiMo, attempt 1: "it's a general allowance. I'll allow it on all admin endpoints when no Authorization header is present."
- MiMo, attempt 2 first reached the correct reading ("**require the header when possible**"). It then rejected it ("That seems too special-cased") and guessed: "I bet the actual upstream fix accepts both everywhere."

The two attempts that passed this test (DeepSeek 2, MiMo 3) limited the query form to the streaming endpoints. DeepSeek, attempt 2: "On ordinary HTTP requests a query token is refused."

This is a left-open failure, not a broken behaviour: the event stream still had to accept the query token, and every attempt kept that working.

### 4.3 What they got right

Both models understood the bug and did a lot of real work. Every attempt:
- authenticated every route and verb, including the added WebSocket stream, which bypasses the web framework's middleware;
- scoped both environment-write paths to the prefix;
- wired the serverless wrapper;
- moved header redaction to record creation, so every consumer saw redacted headers.

The failures are scope decisions on two clauses of the report, not a misunderstanding of the vulnerability.

### 4.4 Model profiles on this task

- **DeepSeek V4.1 Flash:** fast (12–24 minutes, 146–191 turns). It reasons through the report clause by clause, then settles ambiguous clauses on the permissive side.
- **MiMo-V2.6-Pro:** slower (47–58 minutes, 129–170 turns). It writes larger self-check scripts (18 checks in attempt 1, 40 in attempt 3), but they test the reading it has chosen, not the clause it set aside.

## 5. Evaluation setup

- Harness: Harbor with the Claude Code agent.
- Models: DeepSeek V4.1 Flash (reasoning effort max) and MiMo-V2.6-Pro; 3 counted attempts each, 2 hours per attempt.
- Offline: the agent could reach only the model APIs, and web tools were disabled. The repository has no git history. The hidden tests are copied in only after the agent stops, and every agent process is stopped before grading.
- Every counted attempt was audited before it counted, by an independent reviewer (Claude Opus 5.5) that checked:
  - no access to the hidden tests and no lookups ("transcript /tests grep count = 0");
  - no agent activity after the agent stopped, and no tool calls during grading;
  - the grader ran both groups;
  - each failing test is stated in the report and passed by the reference fix.
- What counts: a timeout counts as a failure. An attempt cut off by a provider or network outage is not counted.
- The delivered package grades in a separate container: it applies the agent's source diff to a fresh copy and runs the same tests and the same scoring script. The counted attempts were graded in the agent's container, after the agent was stopped.

## 6. Questions you may ask

**Is the failure the model's fault and not the task's?** The reference, an alternative fix and a hardening fix all score 1.0. Each failing test is backed by a sentence in the report ("in any form or for any consumer"; "never a substitute for the header on a request that can carry one"). The transcripts show the models found both points and argued them away (section 4).

**Does it hinge on one test?** Partly. The reproduced-credential test is the one all 6 attempts fail. Without it, 4 of 6 attempts would still fail on the query-token test, and the other 2 (DeepSeek 2, MiMo 3) would score 1.0. An earlier version of the task without the reproduced-credential route was solved by DeepSeek in its one attempt and by MiMo in one of two.

**Could the model have seen the answer?** The reproduced-credential route is not covered by the published fix, and the added routes do not exist upstream. The agent was offline, with web tools disabled, and the audit found no reads of the hidden tests in any transcript.

**What do 0.93 and 0.96 mean?** No legitimate behaviour was broken in any attempt.
- 0.96 (26/27): every route closed except the reproduced credential.
- 0.93 (25/27): the query token is also accepted on an ordinary request.

The task counts as solved only at 1.0.

## Appendix

**Task package** (`tasks/mockoon-admin-api-missing-auth/`):

| What | Contents |
|---|---|
| Report | `instruction.md` |
| Environment | `environment/Dockerfile` (Node 24, pinned Mockoon commit, history removed), `environment/injection.patch` (the two added routes) |
| Reference fix | `solution/fix.patch`, `solution/solve.sh` |
| Hidden tests | `tests/security/` (5 files, 27 tests), `tests/functional/` (15 tests), `tests/support/env.ts`, `tests/score.py`, `tests/test.sh`, grader `tests/Dockerfile` |

**Internal slug:** `mockoon-ds` (build v3).

**Sources used:**
- the delivered task; `RESULTS.md` and `README.md` of the client repository;
- the build record: manifest with traps, build notes, fairness review, 17 check patches, gate reports and logs, trial summary;
- the counted attempts:
  - `mockoon-ds-deepseek-r1-20261020-233228-n001`
  - `mockoon-ds-deepseek-r2-20261020-234558-n002`
  - `mockoon-ds-deepseek-r3-20261021-001116-n003`
  - `mockoon-ds-mimo-r1-20261021-003227-n004`
  - `mockoon-ds-mimo-r2-20261021-012054-n005`
  - `mockoon-ds-mimo-r3-20261021-022016-n006`
- for each attempt: per-test results, final code, full transcript (including reasoning) and audit.
