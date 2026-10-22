# knowns-memory-id-path-injection — a task that DeepSeek V4.1 Flash and MiMo-V2.6-Pro both fail 3/3

**Status of 2026-10-21.** Sources: the delivered task package, its results entry, the task build and validation records, the fairness review, and every counted attempt's transcript, final code, per-test results and independent audit.

## Summary

- **Result: both target models failed all 3 counted attempts.**
  - DeepSeek V4.1 Flash: 0.89, 0.86, 0.86.
  - MiMo-V2.6-Pro: 0.86, 0.86, 0.96.
- Every attempt finished on its own within the 2-hour limit: DeepSeek in 14–21 minutes of agent time, MiMo in 77–104 minutes.
- Each counted attempt was audited independently and judged a genuine model failure (5 with high confidence, 1 with medium confidence).
- This is a near-miss task: every attempt scored high, kept every legitimate behaviour working (203/203 functional cases each time), and still stopped short of 1.0.
- Why both fail: the models built one strict path guard for document names and a weaker one for memory-note identifiers. In 5 of 6 attempts the memory check accepted an identifier spelled in an alternate filename form. In the sixth attempt (MiMo, attempt 3), one refusal path returned the wrong kind of error.

## 1. The task

**Vulnerability (CWE-22, path traversal).** Knowns is a local knowledge base for a software project, written in Go. It ships as a command-line tool, an assistant-facing MCP tool server and a local web UI. It keeps documents, memory notes and code-generation templates in folders inside the project, and memory notes can also be kept in a machine-level folder. Clients name items: a document by its path, a note by its identifier, a template by its name. At the pinned commit, the product joins that name to its managed folder and never checks that the result stays inside. A crafted name therefore reads, writes, renames or deletes files outside the folder.

**Base advisory:** GHSA-9GFJ-28HW-JCHP (CVE-2026-86439), project knowns-dev/knowns. Vulnerable commit `d3989829fb5095666d23d005b2f78a082832a396`, upstream fix `09c5a96fd5817b941dc86669278c1a17db10ed4e` (the direct child of the vulnerable commit). The upstream fix sends every such mapping through a new containment helper and validates memory identifiers.

**What the task contains.** Eight routes to the same rule. Five are real upstream code that the published fix covers at separate sites, far from the reported example. Three are views added for this task (marked "added"). Each added view follows the code patterns already in the same files.

| # | Route | What leaks | What must keep working next to it | Origin |
|---|---|---|---|---|
| T1 | Template library: template create, import-qualified template lookup, and the preview's template-file selector | template files created or read outside the template library | local template names, import-qualified names that contain a slash by design (`source/name`), nested template files | real upstream code (published-fix sites) |
| T2 | Document writes: create, update/rename (old and new path), delete | files written, renamed or removed outside the document library, including absolute and other-platform spellings | nested document paths, names with or without `.md`, dotted names such as `v1..2`, rename to a dotted folder | real upstream code (published-fix sites) |
| T3 | Spellings of the reported document read: imported-document lookup, a symlink inside the library pointing outside, URL-encoded traversal, absolute / backslash / volume / UNC / device spellings | outside files read | imported documents by full path and by short reference | the advisory's own route and its input forms |
| T4 | Memory identifiers from requests: get, delete, create through the review flow | outside notes read, removed or created; identifiers using a trailing dot, a backslash or a colon are accepted | identifiers made of letters, digits, dots, underscores and hyphens; title-slug references | real upstream code (published-fix sites) |
| T5 | Memory identifier read back from a stored record during promote/demote | a record whose own metadata carries a traversing identifier is moved outside the memory roots | promote and demote of ordinary notes (tool and web API) | real upstream code (published-fix site) |
| S1 | Memory snapshot view (pre-update copy of a note) | snapshot read with a traversing identifier reads outside | snapshot returns the pre-update copy | added for the task |
| S2 | Template preview showing the destination file's current contents | a request variable substituted into the destination reads a file outside the project | an in-project destination and its contents are still returned | added for the task |
| S3 | Raw document source view (`/docs/*/source`) | the raw view rejoins the requested path to the document folder and serves outside files | raw source of ordinary documents | added for the task |

**Report given to the agent.** It is written as a product bug report:
- the system and the three kinds of content, with the operations on each;
- one observed example: a web API request for the document `../notes` returns `notes.md` from outside the library. The report adds that the same kind of value reaches writes, memory notes and templates;
- the rule: "No value that names a document, a memory note, a template, a template file, or a generated destination may cause the product to read or write a file outside the folder it manages for that kind of content … whatever the operation is called and whatever it returns";
- stored identifiers: "An identifier read back from stored data … is as untrusted as one supplied by a client";
- spellings: the rule holds "however the value is spelled, including forms another platform would treat as a separator, an absolute reference, or an alternate file name", and for symlinks. "A value that uses path syntax is not a valid name for an item and must be refused";
- refusal form: "an error result from the assistant tools, a 4xx response from the web API";
- a keep-working list (nested paths, `.md` suffix, `v1..2`, imported references, memory identifier character set, promote/demote, `source/name` templates).

No file, function, test or count is named. The snapshot, preview-destination and raw-source views are not named either.

**Hidden tests.** 20 security test functions (28 JUnit cases, counting subcases) and 11 authored functional test functions. The functional group also re-runs the project's own tests for the three packages from pristine copies, 203 functional cases in all. The tests call the real MCP tool handlers, and drive the web API routes through the project's real HTTP router, against temporary project folders, as the project's own tests do. They assert outcomes: the call is refused (a tool error result or a 4xx), no outside bytes are returned, and no outside file is created, changed or removed. Reward = 1.0 only when every test passes. Otherwise it is the security pass fraction (capped below 1), or 0 if any functional case fails.

## 2. How we know the task is fair

| Check | Result |
|---|---|
| Vulnerable code (pinned commit plus the added views) | fails all 28 security cases, passes all 203 functional cases |
| Reference fix | 1.0, three times, identical results |
| Independent fix by a separate model (Opus 5.5). It worked from the report and the list of sites to cover, without the tests or the reference fix | 1.0 |
| Alternative correct fix and hardening fix, written differently from the reference | 1.0 each |
| Upstream fix alone | not run as a separate check; the three added views are outside the published fix by construction, and the patches that leave each of them open fail (next row) |
| One wrong-fix patch per route (8 patches: templates, document writes, document spellings, memory request identifiers, stored identifiers, snapshot, preview destination, raw source) | each fails exactly its route's security tests with all functional cases passing (rewards 0.71–0.96) |
| Over-broad fix (refuse any value containing `..`) | reward 0: breaks nested-document and dotted-folder rename tests |
| The published fix's own regression tests | absent at the vulnerable commit (no leaked tests) |
| Fairness review of every authored test against the report | 30 of 31 tests rated low risk, 1 medium (memory identifier spellings); verdict READY |

## 3. Results, attempt by attempt

| Model | Attempt | Score | Security | Functional | Left open | Broke |
|---|---|---|---|---|---|---|
| DeepSeek | 1 | 0.89 | 25/28 | 203/203 | trailing-dot memory identifier accepted and written (identifier-spelling test failed) | nothing |
| DeepSeek | 2 | 0.86 | 24/28 | 203/203 | trailing-dot memory identifier accepted and written (identifier-spelling test failed) | nothing |
| DeepSeek | 3 | 0.86 | 24/28 | 203/203 | trailing-dot memory identifier accepted and written (identifier-spelling test failed) | nothing |
| MiMo | 1 | 0.86 | 24/28 | 203/203 | trailing-dot memory identifier accepted and written (identifier-spelling test failed) | nothing |
| MiMo | 2 | 0.86 | 24/28 | 203/203 | trailing-dot memory identifier accepted and written (identifier-spelling test failed) | nothing |
| MiMo | 3 | 0.96 | 27/28 | 203/203 | traversing rename refused with a transport error, not a tool error result | nothing |

- All 6 attempts closed all three added views (snapshot, preview destination, raw source), the stored-identifier route, the template routes and every document spelling.
- 5 of 6 accepted a memory identifier ending in a dot through the review/create flow and wrote it as a note file.
- 1 of 6 (MiMo, attempt 3) handled every identifier correctly but delivered one refusal in the wrong form.
- No attempt broke legitimate behaviour: all 6 passed 203/203 functional cases.

## 4. Why both models failed

### 4.1 Memory identifiers checked more weakly than document names (5 of 6)

Each of these five attempts wrote two validators: a strict one for document paths, and a character-set check for memory identifiers built from the report's keep-working list. The identifier `zzbad.` passes such a check, and the tool wrote it as a note file (`memory-zzbad..md`). The report requires that a value spelled as "an alternate file name" on another platform be refused. A trailing dot is such a form, and the reference fix refuses it.
- DeepSeek, attempt 2, final summary: memory IDs are validated "against the documented character set". Its shared path layer, by contrast, "Rejects … trailing-dot/space alternate spellings" for document segments.
- DeepSeek, attempt 3, final summary: the path layer rejects "trailing-dot/space and reserved-device aliases", with "Separate validators for document paths, memory IDs, template references, and generated destinations." Its memory validator checks only the character set and the names `.` and `..`.
- MiMo, attempt 1: `ValidMemoryID` is commented "Memory ids are letters, digits, dots, underscores and hyphens. None of those is a path separator". Its final summary calls this a "strict charset".
- MiMo, attempt 2 routes memory identifiers through a single-segment name check that refuses separators, but not a trailing dot.

The audits record the same pattern in each run: "the model demonstrably knew the pattern … but used a weaker validator for memory ids".

### 4.2 Refusal delivered in the wrong form (MiMo, attempt 3)

This attempt used one name validator for documents, memory identifiers and templates, and it passed every identifier-spelling case. In the document update tool's rename branch, the code returned the validator's error as a Go error (`return nil, err`) instead of a tool error result. The traversing new path was refused and no file was written. But the report defines refusal as "an error result from the assistant tools", and the test reports "handler returned a transport error instead of a tool result". The audit notes that the same attempt returned proper error results in its other 11 tool-handler security cases.

### 4.3 What they got right

- Every attempt found and closed the three added views. Nothing in the report names them.
- Every attempt treated identifiers read back from stored records as untrusted (both stored-identifier tests passed in all 6), and refused symlink escapes and Windows-style spellings for document paths.
- No attempt over-blocked: dotted names, nested paths, imported references and promote/demote kept working in all 6.

The misses are not about understanding the bug. Both models applied a rule unevenly across item kinds, or delivered one refusal in the wrong form.

### 4.4 Model profiles on this task

- **DeepSeek V4.1 Flash:** fast (14–21 minutes, 177–231 turns). It built a central path package, probed attacks with throwaway programs, and missed the same memory-identifier spelling in all three attempts.
- **MiMo-V2.6-Pro:** slower (77–104 minutes, 234–279 turns). It mapped the name-to-file sites in tables before editing (attempts 2 and 3). Attempts 1 and 2 missed the same spelling. Attempt 3 unified its validators and missed only the refusal form on one branch.

## 5. Evaluation setup

- Harness: Harbor with the Claude Code agent.
- Models: DeepSeek V4.1 Flash (reasoning effort max) and MiMo-V2.6-Pro. 3 counted attempts each, 2 hours per attempt (agent timeout 7200 s).
- Offline: the agent could reach only the model API, and web search and fetch tools were disabled. The repository is checked out at the vulnerable commit with no git history, and the hidden tests are copied in only after the agent stops.
- In the counted runs, the agent was stopped before grading. The delivered package grades the agent's source diff in a fresh grader container, using the same tests and scoring script.
- Every counted attempt was audited by a separate model (Claude Opus 5.5, high effort) before it counted. The audit checks:
  - that the agent had no access to the hidden tests and made no lookups (no hidden-test strings in the transcripts, no reads under `/tests`);
  - that no tool calls happened during grading;
  - that the score reflects the model's own code.
- What counts: a run that times out counts as a failure, and a run cut off by a provider or network outage is not counted. All 6 runs on this task finished normally, and no runs were excluded.

## 6. Questions you may ask

**Is the failure the model's fault and not the task's?** The reference fix, an alternative fix, a hardening fix and an independently written fix all score 1.0. The fairness review mapped every test to a sentence of the report. The audit of each attempt found the shortfall in the model's own code: a weaker memory-identifier check than the attempt used for documents, or one refusal in the wrong form.

**Does it hinge on one test?** Each attempt fails one test function. In 5 attempts it is the memory identifier-spelling test (trailing dot), and in MiMo's attempt 3 it is the document-rename refusal test. Every other route was closed in every attempt.

**Could the model have seen the answer?** The agent could not reach the internet or the hidden tests, and the audits found no lookups. The three added views exist only in this task, so no published fix covers them.

**What does a 0.86 or 0.96 mean?**
- 0.86 means 24 of 28 security cases passed, with nothing broken.
- 0.96 means 27 of 28 passed.
- A 0 would mean a legitimate behaviour was broken. No attempt on this task scored 0.

## Appendix

**Task package** (`tasks/knowns-memory-id-path-injection/`):

| What | Contents |
|---|---|
| `instruction.md` | the report given to the agent |
| `task.toml` | metadata (CWE, advisory, commits, entry point), agent and verifier limits |
| `environment/` | Dockerfile (pinned checkout, added views, module cache, history removed) and `injection.patch` (the three added views) |
| `solution/` | reference fix (`fix.patch`, `solve.sh`) |
| `tests/` | hidden security and functional tests, the grader Dockerfile, `test.sh`, `score.py` |

**Internal slug:** `knowns-ds`.

**Sources used:**
- the delivered task package; `RESULTS.md` and `README.md` of the delivery;
- build record `build/knowns-ds/` (notes.md, manifest.json, FAIRNESS.md, gate_report.partial.json, checks/, runs_*.log, trial_detail.json);
- trial folders `knowns-ds-deepseek-r1-20261021-043055-n001`, `knowns-ds-deepseek-r2-20261021-044914-n002`, `knowns-ds-deepseek-r3-20261021-050419-n003`, `knowns-ds-mimo-r1-20261021-052608-n004`, `knowns-ds-mimo-r2-20261021-064818-n005` and `knowns-ds-mimo-r3-20261021-080533-n006`. From each: result.json, verifier results, final-code/changes.patch, and the audit (POSTMORTEM.json and evidence/transcript.md).
