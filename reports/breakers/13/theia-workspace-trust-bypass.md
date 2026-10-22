# theia-workspace-trust-bypass — a task that DeepSeek V4.1 Flash and MiMo-V2.6-Pro both fail 3/3

**Status of 2026-10-21: both-model breaker, delivered.** The counted attempts were run from 2026-10-20 23:37 to 2026-10-21 07:26 UTC. Sources: the delivered task, the build and validation records, the fairness review, every attempt's transcript, final code and per-test results, and the independent audit of every counted attempt.

## Summary

- **Result: both target models failed all 3 counted attempts.**
  - DeepSeek V4.1 Flash: 0.0, 0.0, 0.0.
  - MiMo-V2.6-Pro: 0.0, 0.0, 0.0.
- Agent time: DeepSeek finished on its own in about 43, 31 and 34 minutes. MiMo finished its second attempt in about 113 minutes; its first and third attempts reached the 2-hour limit and were graded on the code as it stood (counted as failures).
- Every counted attempt was audited independently: all 6 were judged trustworthy and a genuine model failure, with high confidence.
- The task is Eclipse Theia, a real IDE with AI features, at the commit before a published fix that puts every AI feature behind workspace trust (Restricted Mode). The published fix covers six places. Three more real routes in the same code were left open by it, and two sibling routes were added for the task.
- Why both models fail: every attempt left at least three routes open. The most common reasoning was that a route does not matter because "no AI runs" in an untrusted workspace (the shell-command allow/deny lists and the tool-approval settings). Every attempt also broke at least one legitimate behaviour next to the gate, most often a language-model request in a trusted workspace.

## 1. The task

**Vulnerability (CWE-829, inclusion of functionality from an untrusted control sphere).** A workspace the user has opened but not trusted can still drive Theia's AI stack: AI commands run, language-model requests go out, and the workspace's own settings and files (tool auto-approval, agent settings, model aliases, prompt templates, skills, shell-command lists, provider endpoints) shape what the AI does. A hostile repository can therefore make an AI feature act for the user with the repository's configuration.

- **Project and language:** Eclipse Theia (TypeScript).
- **Base advisory:** GHSA-3JWW-HXQJ-WFQ2 / CVE-2026-44688.
- **Vulnerable commit:** de745e9 (`de745e95b4273fcb72358f0e34c5340beb359a74`). **Upstream fix:** e3fdfe6 (`e3fdfe6992389bc5fa611058d00c39d7408508ed`), its direct child.

**What the task contains.** Eleven routes to one rule. Each must be closed while a trusted workspace, the user's own values and the built-in defaults keep working.

| Route | Origin | What leaks while untrusted | What must keep working next to it |
|---|---|---|---|
| 1. AI activation state and the AI command wrapper | advisory, fixed upstream | AI enabled by preference means AI commands are executable, also by direct call | commands stay visible while untrusted; hidden when AI is disabled; enabled again when trust is granted |
| 2. Language-model request service | advisory, fixed upstream | a request reaches the provider and a session is recorded; workspace request settings apply | trusted requests are sent and merge workspace and user request settings |
| 3. Tool-approval settings | advisory, fixed upstream | a workspace wildcard, per-tool or folder value auto-approves tools | user values, the built-in default, session-only overrides and saving a user choice |
| 4. Agent settings reader | advisory, fixed upstream | workspace agent settings apply | user settings and the built-in default apply |
| 5. Model-alias registry | advisory, fixed upstream | a workspace alias selects the model | user selections and default models |
| 6. Prompt-template locations | advisory, fixed upstream | workspace template folders, files and extensions load, including a built-in default folder inside the workspace | all of them load in a trusted workspace |
| 7. Skills | real upstream code the fix left open | skills load from the workspace's skill folder and from workspace-configured folders | user skills keep loading; all load when trusted |
| 8. Shell-command allow and deny lists | real upstream code the fix left open | a workspace allowlist auto-approves commands; a workspace value removes the built-in deny list | user allowlist entries; the built-in deny list still blocks |
| 9. Anthropic provider configuration | real upstream code the fix left open | a workspace custom endpoint, model list, credential and proxy are registered | user endpoints, credential and proxy; the built-in model list |
| 10. A second AI-core command registered outside the wrapper | code added for the task | the command is enabled and runs while untrusted | it exists and runs while execution is allowed |
| 11. Copilot provider start-up | code added for the task | provider models are registered on start, gated only by the preference | configured models register while execution is allowed |

Routes 10 and 11 come from a 68-line patch applied to the task's copy of the repository. Each copies a pattern already present in the same package (a command enabled from the preference-only flag; start-up gated on the preference-only flag), and both are reachable through the real services.

**Report given to the agent.** It is written as a real bug report: the system; an illustrative observation; then one general property — "In a workspace the user has not trusted, no AI feature may start, run or act on the user's behalf, and nothing the workspace supplies may influence what an AI feature does or draws on." Five clauses spell it out:
- nothing runs: "Every attempt to use an AI feature is refused with an error, however it is reached";
- workspace values are never used as configuration, while user values and defaults keep applying, and a value naming a location inside the workspace is not applied;
- workspace content is not loaded, including content at an inside-workspace location that a default or user value names;
- unknown trust is untrusted, and trust changes apply at once in both directions;
- a trusted workspace is unchanged: "Whether AI is enabled still governs what is offered; trust governs only what may run."

A short contracts section names only what the hidden checks bind: `WorkspaceTrustService`, `PreferenceService`, and `AIActivationService` with `isActive` and `canRun`. No route, file, setting name or count is given.

**Hidden tests.** 27 security tests (6 for routes 1 and 10, 4 for route 2, 3 for route 3, 4 for routes 4–5, 3 for route 6, 2 for route 7, 3 for route 8, 1 each for routes 9 and 11) and 32 functional tests. They build the real Theia services in Theia's dependency-injection container from the packages' own modules, with test-side stand-ins only for preferences, workspace trust, files and provider managers, and they assert behaviour: whether a command is enabled and refuses, whether a provider is called, which value a reader returns, which folders load. Any rejection counts as a refusal. Reward = 1.0 only if all 59 pass; otherwise the security pass fraction, or 0 if any functional test fails.

## 2. How we know the task is fair

| Check | Result |
|---|---|
| Vulnerable code | fails all 27 security tests, passes all 32 functional tests |
| Reference fix | 1.0 (the gate's oracle stage; the build record shows three identical 1.0 trials) |
| Blind fix (a fresh model with only the report and the code) | not run |
| Hardening fix, and an alternative design of the execution gate | 1.0 each |
| The upstream advisory fix alone | fails 9 security tests (routes 7–11 and direct command execution); 32/32 functional |
| One wrong-fix patch per route (12 patches, each leaves one route at the vulnerable code) | each fails that route's security tests, with all 32 functional tests passing |
| Trust assumed until it resolves (fail-open); a crash instead of a clean refusal | fail 3 security tests each |
| Over-broad fixes: hide AI commands while untrusted; drop user and default values | fail the functional tests (reward 0) |
| Independent fairness review of every test against the report | READY: each of the 59 tests is covered by a literal reading of the report |

In total, 18 check patches behaved as declared, and the scripted gate passed on the delivered version (2026-10-20 23:37 UTC). A review of the previous version found one contradiction (prompt-template defaults that name a folder inside the workspace). It was fixed in the report wording before these attempts were run, with no test weakened.

## 3. Results, attempt by attempt

| Model | Attempt | Score | Security | Functional | Left open | Broke |
|---|---|---|---|---|---|---|
| DeepSeek | 1 | 0.0 | 11/27 | 28/32 | added AI-core command (10); tool approval (3); shell lists (8); provider endpoint (9); alias trust change | request service and template loader can no longer be built (asynchronous start-up, duplicate binding): trusted requests and trusted templates fail |
| DeepSeek | 2 | 0.0 | 20/27 | 24/32 | added AI-core command (10); shell lists (8) | AI reported as disabled while untrusted, so commands are hidden; trusted requests refused; trusted workspace tool-approval, template and skill values not applied |
| DeepSeek | 3 | 0.0 | 19/27 | 30/32 | added AI-core command (10); tool approval (3); shell lists (8); runtime change event | the first requests in a trusted workspace refused |
| MiMo | 1 (2-hour limit) | 0.0 | 3/27 | 5/32 | nearly every route | most services can no longer be built (asynchronous start-up, a new dependency not bound) |
| MiMo | 2 | 0.0 | 7/27 | 28/32 | added AI-core command (10); tool approval; agent settings and aliases; templates incl. the default folder; configured skill folders; shell lists; provider endpoint; Copilot start-up (11) | AI reported as disabled while untrusted, so commands are hidden; trusted requests refused |
| MiMo | 3 (2-hour limit) | 0.0 | 9/27 | 29/32 | commands still executable while untrusted; added AI-core command (10); tool approval; agent settings and aliases; template extension; configured skill folders; shell lists; provider endpoint; Copilot start-up (11) | trusted requests refused |

- All 6 failed the added AI-core command test and all 3 shell-list tests.
- 5 of 6 left tool approval open (all but DeepSeek 2).
- 4 of 6 registered the workspace-supplied provider endpoint.
- All 6 failed at least one trusted-workspace language-model request test.
- 2 of 6 (MiMo 1 and 3) reached the 2-hour limit.

## 4. Why both models failed

### 4.1 Left open: shell-command lists and tool approval (6 of 6 and 5 of 6)

Both models found these routes and argued that they could not matter, because nothing runs in an untrusted workspace:
- DeepSeek, attempt 2: "AI-terminal allow/deny lists: tool permissions; if AI can't run no effect. … Skip." Later: "In untrusted no AI runs. In trusted, workspace settings legitimately apply. Fine."
- DeepSeek, attempt 3, on tool approval: "'No value … may have any effect' strictly, but effects only observable in AI behavior; since nothing runs, no." On the shell lists: "hidden tests could check `ai-terminal` allowlist workspace value doesn't influence AI untrusted; no AI run. Skip."

The report's rule is not limited to what runs: "nothing the workspace supplies may influence what an AI feature does." A workspace allowlist pre-approves commands, and a workspace value can remove the built-in deny list. Both are live as soon as trust is granted or a gate is missed.

DeepSeek attempt 1 named the risk ("`ai-features.terminal.shellCommandAllowlist` from workspace could allow dangerous commands!") and chose a filter inside the core preference service. MiMo attempts 2 and 3 did the same ("Intercept in `PreferenceServiceImpl` … centralized and automatically covers all AI code"). The report's contracts say that the hidden checks supply preferences through `PreferenceService`, and with these attempts the services the checks drive still returned the workspace values (tool approval, shell lists and the provider endpoint; for MiMo also agent settings and aliases).

### 4.2 Left open: the AI-core command outside the wrapper (6 of 6)

Every attempt that mapped the commands found this one and kept it enabled from the preference alone:
- DeepSeek, attempt 1: "It's a settings command, not AI execution; but command factory not used. Trust shouldn't hide. Leave."
- DeepSeek, attempt 3: "Opening prefs doesn't run; keep visible/active."
- MiMo, attempt 2: "`AI_SHOW_MODEL_STATUS_COMMAND` — opens preferences. Not AI acting."

The report requires every AI feature to be refused "however it is reached". In the same file, the neighbouring AI-settings command goes through the command wrapper, so the attempts that gated the wrapper refuse it while untrusted.

### 4.3 Left open: provider configuration, Copilot start-up and content (MiMo mostly)

- 4 of 6 attempts registered a workspace-supplied custom endpoint (check message: "workspace endpoint registered: https://evil.example").
- MiMo attempts 2 and 3 still registered Copilot models on start-up while untrusted (route 11).
- MiMo attempt 2 still loaded the built-in default template folder inside the workspace ("default workspace directory leaked: /workspace/.prompts"), which the report covers explicitly. MiMo attempts 2 and 3 loaded a skill from a workspace-configured folder.

### 4.4 Broke: the execution gate itself

- DeepSeek attempt 2 and MiMo attempt 2 read the AI-enabled preference through their own trust filter. While untrusted they reported AI as disabled, so commands were hidden ("the command stays visible: false !== true"); MiMo attempt 1 failed the same checks. The report says "withholding trust must not take them out of view."
- MiMo attempt 3 left the wrapped commands executable while untrusted and before trust resolved.
- DeepSeek attempt 3 published its runtime event as `onDidChangeCanRunStatus`; the check subscribes to `onDidChangeCanRun` ("activation.onDidChangeCanRun is not a function").

### 4.5 Broke: legitimate requests and service start-up

- DeepSeek attempt 1 and MiMo attempt 1 gave services an asynchronous start-up, so the dependency-injection container could no longer build them synchronously ("You are attempting to construct Symbol(LanguageModelService) in a synchronous way but it has asynchronous dependencies"). DeepSeek attempt 1 also bound the template contribution twice ("Ambiguous match found"). These failures hit both the security and the functional tests of those routes.
- In the other four attempts, the request service checked a cached trust flag and refused requests in a trusted workspace (DeepSeek 3: "AI features cannot run in the current workspace. Make sure AI features are enabled and the workspace is trusted."). For MiMo attempts 2 and 3 this also failed the request made after trust is granted at runtime. The reference reads the trust state at the time of each request.

### 4.6 What they got right

DeepSeek closed most routes the published fix covers: attempt 2 passed 20 of 27 security tests (request gate, tool approval, agent settings, aliases, templates, skills, provider configuration and Copilot start-up), and attempt 3 passed 19. All three DeepSeek attempts closed the skills route, which the published fix leaves open. The failures are not about understanding the bug. They come from deciding that a route is out of scope, and from gates that disturb the trusted behaviour next to them.

### 4.7 Model profiles on this task

- **DeepSeek V4.1 Flash:** fast (31–43 minutes) and wide. It edited 30–48 files across 12–16 packages, then ruled specific routes out of scope with "no AI run. Skip."
- **MiMo-V2.6-Pro:** slow (113 minutes, or the full 2 hours). It spent long stretches mapping entry points with sub-agents and preferred one central filter in the core preference layer. Two attempts ran out of time with the work incomplete, and one broke service start-up across the AI packages.

## 5. Evaluation setup

- Harness: Harbor with the Claude Code agent (2.1.304).
- Models: DeepSeek V4.1 Flash (reasoning effort max) and MiMo-V2.6-Pro; 3 counted attempts each, 2 hours per attempt.
- Offline: the agent could reach only the model API, and web tools were disabled. The repository has no git history, and the hidden tests are not in the environment while the agent works; grading starts after the agent is stopped.
- Every counted attempt was audited before it counted, by an independent Claude Opus 5.5 reviewer:
  - no access to the hidden tests and no lookups;
  - grading after the agent stopped, with all 59 tests run;
  - the score reflects defects in the model's code.
  All 6 audits: model failed, trustworthy, high confidence. For the two MiMo attempts at the 2-hour limit, the audit confirmed continuous work and no provider errors.
- What counts: an attempt that reaches the 2-hour limit is graded on the code it left and counts as a failure. An attempt cut off by a provider or network outage would not count; none occurred here.

## 6. Questions you may ask

**Is the failure the model's fault and not the task's?** The reference, a hardened fix and an alternative design each score 1.0. The upstream fix alone and every one-route-short patch fail. A fairness review mapped every test to a sentence of the report. In the transcripts, the models found the routes they left open and argued them out of scope.

**Does it hinge on one test?** No. Every attempt failed security tests on at least three separate routes, and every attempt also failed functional tests. Removing any single route's tests leaves all 6 attempts below 1.0.

**Could the model have seen the answer?** Routes 7–11 are not covered by the published fix, and two of them do not exist upstream. The agent could reach neither the internet nor the hidden tests, and the audit checked every transcript for this.

**What does a 0.0 mean here?** Every attempt broke at least one legitimate behaviour (a functional failure forces 0). Without that rule, the scores would have ranged from 0.11 to 0.74 (3 to 20 of 27 security tests), and none would have reached 1.0.

## Appendix

**Task package** (`tasks/theia-workspace-trust-bypass/`):

| What | Contents |
|---|---|
| Report and metadata | `instruction.md`, `task.toml` |
| Environment | `environment/Dockerfile` (pinned commit, history removed, project built), `environment/injection.patch` (routes 10 and 11) |
| Reference | `solution/fix.patch` (25 files), `solution/solve.sh` |
| Hidden tests | `tests/security/` and `tests/functional/` (9 files each), `tests/support/` (harness), `tests/test.sh`, `tests/score.py`, `tests/Dockerfile` and `tests/injection.patch` (grader image) |

**Internal slug:** `theia-ds` (task version v4).

**Sources used:** the delivered task; `RESULTS.md` and `README.md` in the delivery repository; the internal build record (`manifest.json`, `notes.md`, `FAIRNESS.md`, the gate report and the 18 check patches); the six counted trials (`theia-ds-deepseek-r1/r2/r3`, `theia-ds-mimo-r1/r2/r3`, 2026-10-20/21): results, per-test outcomes, final code, agent transcripts and the audit records.
