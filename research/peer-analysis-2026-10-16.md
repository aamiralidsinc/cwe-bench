# Peer analysis: where DeepSeek V4.1 Flash and MiMo-V2.6-Pro fail (peer pipeline, 2026-10-16)

**Provenance.** Written by the peer CWE-Bench pipeline, whose results ledger is `Sheraz/C_RESULTS.md`
and whose attempt data is `Sheraz/cwe-bench_findings_2026-10-16.zip`. The user pasted it into the
handoff conversation on 2026-10-16 at 18:20 UTC. Saved verbatim below. Tables lost their borders in
the paste, so columns are tab-separated. Paths such as `data/...` and `PIPELINE.md` refer to the
peer repository, not to this one.

**Used by:** `builder/PROMPT-TEMPLATES-SPEC.md` (lessons digest, calibration set).

---

Where DeepSeek V4.1 Flash and MiMo-V2.6-Pro fail: analysis of the CWE-Bench tasks so far
Status of 2026-10-16. Sources: C_RESULTS.md, data/04_eval_runs/ (every attempt’s trajectory, patch and test results), data/03_environments/ (task, reference fix, validation records) and the per-task failure analyses in data/knowledge/failure_analyses/.

Executive summary
24 tasks evaluated, 1 accepted. In hono GHSA-hxh3 (XSS), both models failed all 3 attempts. No attempt timed out: each was graded and stopped on its own.
4 tasks broke at least one model:
MCP SDK (credential pinning): DeepSeek failed 3/3.
nltk (symlink escape): DeepSeek failed 3/3.
undici (cache/origin isolation): each model failed one attempt.
The other 20 tasks were solved, mostly by DeepSeek on attempt 1 (median about 15 minutes).
Why they fail: neither model is weak at finding or understanding the bug; every failing attempt diagnosed the root cause correctly. They fail on scope:
they fix the code paths the report points at, and only the input shapes they reproduced;
they verify with their own tests, which use the same path as their fix, and stop.
What works: a bug reachable through several entry points, one of them in a module that looks out of scope (a second implementation, a lower-level API, a save/reload round-trip), plus input-shape variants, plus a “must keep working” clause that plausibly argues against fixing it.
What doesn’t: single-location fixes, and resource-exhaustion (DoS) bugs (0 of 7 broke a model).
1. How tasks are made today (current generation rules)
The full one-page summary is in PIPELINE.md. The rules that shape a task:

Area	Rule
Source	A real advisory (GHSA/OSV) for PyPI or npm, fixed after 2026-08-01. The repo is pinned at the vulnerable commit, and the historical fix is the ground truth (oracle).
Excluded	Dependency-bump, config, docs and template-only fixes; tiny fixes; repos without tests or over 400 MB; repos whose image cannot be built here; safety-flagged repos.
Report (instruction.md)	Written by Claude Opus 5.5 (Opus 4.8 if 5.5 declines). Behavioural: impact and trigger. No file, function or line hints, no fix prescription, no CVE id, own words.
Hidden tests	≥3 test_security_* (fail on the vulnerable code) and ≥3 test_functional_* (pass on both), through a real entry point, implementation-agnostic, offline. Variants beyond the report, one test per variant. Functional tests near the attack boundary.
Proof of a good test suite	The reference fix scores 1.0 twice and the vulnerable code fails. A shallow fix still fails a security test, a feature-removal fix fails a functional test, and a correct alternative fix scores 1.0. The repo’s existing tests of the affected code are enforced.
Quality gate	A 10-criterion rubric (all blocking) and a recall probe (rejected if both models name the fix file from the report). The whole image is scanned for copies of the fix.
Evaluation	Harbor + Claude Code agent; DeepSeek V4.1 Flash (effort max) and MiMo-V2.6-Pro; 3 attempts each, 2 h per attempt. Network allowlisted to the model API only. Graded in a separate fresh container.
Verdict	Solved = reward 1.0. Partial fix or broken feature = failure. Timeout = not counted. Accepted = every attempt of both models is a counted failure. Fully deterministic, no LLM judge.
2. Results: attempt by attempt
Tasks where a model failed
Scores per attempt in run order. S = solved (1.0), T = timed out (not counted), - = cancelled because the other model had already solved (not counted).

Task	Vulnerability	DeepSeek #1	#2	#3	MiMo #1	#2	#3	Verdict
hono GHSA-hxh3	XSS, CWE-79	0.83	0.83	0.94	0.89	0.94	0.89	ACCEPTED
MCP SDK GHSA-6qxp	credential binding, CWE-345/522	0.92	0.92	0.92	T 0.50	T 0.50	T 0.50	rejected: MiMo only timed out¹
nltk GHSA-p4rw	symlink escape, CWE-22/59	0.93	0.93	0.93	0.87	S	0.87	rejected: MiMo solved #2
undici GHSA-vp8m	origin confusion, CWE-346	0.86	S	-	0.93	-	-	rejected: DeepSeek solved #2
¹ The MCP SDK MiMo runs used the older terminus-2 harness, not Claude Code. MiMo would need a re-run with Claude Code before this task could be accepted.

How the attempts failed:

Task	Model	Security tests passed	Functional tests passed	What was left open or broken
hono	DeepSeek	3/6, 3/6, 5/6	6/6 ×3	array root every time; plain-string root (renderToString and stream) in 2 runs
hono	MiMo	4/6, 5/6, 4/6	6/6 ×3	array root every time; plain-string root in 2 runs
MCP SDK	DeepSeek	5/6 ×3	7/7 ×3	credential saved and reloaded through the SDK’s own schemas
nltk	DeepSeek	4/5 ×3	5/5 ×3	ToolboxData(path), the lower-level toolbox API
nltk	MiMo	3/5, 3/5	5/5	toolbox API and the MTE reader
undici	DeepSeek #1	5/7	7/7	RetryAgent and Dispatcher1Wrapper wrapping a client
undici	MiMo #1	7/7	6/7	broke same-host caching with a custom DNS lookup (over-hardening)
Every failing attempt ended with the model declaring success (“The fix is complete and fully validated”).

Tasks that were solved (20)
DeepSeek on attempt 1 (17 tasks): msgpack5, @typespec/openapi3, GitPython, pypdf (×2), pyload (×3), datamodel-code-generator, pymongo, httpx2, banks, stream-json, devalue (×2), payload import-export, pydantic-ai.
Both models on attempt 1: ip-address, adm-zip.
The second nltk task (GHSA-w3v8, ReDoS).
DeepSeek solve times on attempt 1: 4 to 64 minutes, median about 15.
Break rate by vulnerability family (task broke at least one model):

Family	Broke	Evaluated
auth / session / credentials	2	6
injection (code / command / markup)	1	2
path / file handling	1	3
resource exhaustion (DoS)	0	7
parsing / type confusion	0	3
information exposure	0	2
other	0	2
3. Task dossiers
What we built for each task where a model failed. Every task passed the rubric and the leak scan, and the reference fix scored 1.0.

3.1 hono GHSA-hxh3-vqpv-xpqv (ACCEPTED)
Vulnerability	hono/jsx renders plain strings unescaped in boundary components, which allows stored or reflected XSS
Advisory	GHSA-hxh3-vqpv-xpqv · CVE-2026-93981 · CWE-79 · severity MEDIUM · published 2026-09-30
Repo	honojs/hono. Vulnerable commit cac0c4d3fe29, fix 2b8ed402
Language / image	TypeScript, node:22-bookworm, bun; image build 54 s cached, 1.4 min longest
Ground truth	6 source files in 3 directories, 156 changed lines: src/jsx/base.ts, components.ts, context.ts, dom/server.ts (a second, separate renderer), intrinsic-element/components.ts, streaming.ts
Report given to the agent	“Untrusted text is emitted as live HTML by the JSX server renderer” (378 words). It says escaping is skipped in “higher-level rendering wrappers” and when “a string [is] handed to the server renderer directly”, and that a bare string must still be renderable. No file or function names.
Hidden security tests (6)	deferred-placeholder boundary (Suspense), error-fallback boundary, value provider (Context), renderToString with a string root, renderToString with an array root, renderToReadableStream with a string root
Hidden functional tests (6)	plain string root still renders, trusted raw HTML preserved, normal element tree, provider text child, Suspense with text and async children, ErrorBoundary without error
Existing tests enforced	494 of the repo’s own tests (pass before and after)
Validation evidence	Shallow fix leaves 5/6 security tests open; feature removal breaks legitimate use; an alternative fix scores 1.0. Recall probe low (neither model named a file).
Generation	Opus 5.5 declined; Opus 4.8 wrote it (2 attempts). Techniques: sibling path, one test per variant, boundary functional tests, behavioural report, parallel implementation, input-shape variants, a “must keep working” clause.
3.2 MCP TypeScript SDK GHSA-6qxp-vccf-f47h (DeepSeek 3/3)
Vulnerability	The OAuth client sends credentials pinned to one authorization server to whichever server a (malicious) MCP server names
Advisory	GHSA-6qxp-vccf-f47h · CVE-2026-104850 · CWE-345, CWE-522 · HIGH · published 2026-10-06
Repo	modelcontextprotocol/typescript-sdk. Vulnerable commit ef39308e9634, fix edd12e28
Language / image	TypeScript monorepo (pnpm), node:22-bookworm; build 12 s cached
Ground truth	8 source files in 4 directories, 174 lines. Client auth.ts, authErrors.ts, authExtensions.ts, crossAppAccess.ts; core auth.ts (the Zod schemas); core-internal authUtils.ts; server-legacy proxy provider
Report	“OAuth client sends pinned credentials to whichever authorization server the MCP server names” (410 words). Lists schema-parsed persistence among legitimate uses that must keep working.
Hidden security tests (6)	client-secret, static-assertion and private-key-JWT providers; credentials with no server metadata; lazily supplied client info; schema round-trip keeps the binding
Hidden functional tests (7)	bound credentials work with their own server, trailing-slash issuer equivalence, unbound legacy credentials, null client info, schema round-trip refresh, token response shape, client-credentials end to end
Existing tests	none enforced (generated before that rule existed)
Validation evidence	Oracle 1.0 and pre-patch fails. Generated before the shallow/removal/alternative checks existed, so they were never run.
3.3 nltk GHSA-p4rw-rvv2-7xwr (DeepSeek 3/3)
Vulnerability	Corpus readers follow symlinks to files outside the corpus root, despite pathsec enforcement
Advisory	GHSA-p4rw-rvv2-7xwr · CVE-2026-79676 / PYSEC-2026-3737 · CWE-22, CWE-59 · HIGH · published 2026-09-08
Repo	nltk/nltk. Vulnerable commit 006000117a9e, fix 10d34b3f
Language / image	Python, python:3.11-slim-bookworm; build 45 s cached
Ground truth	10 source files in 3 directories, 236 lines: pathsec.py plus 8 corpus readers and toolbox.py
Report	“Corpus loading reads files that live outside the corpus directory” (374 words). Behaviour only; says the bug is reachable through several public loading APIs.
Hidden security tests (5)	Lin thesaurus, Crúbadán mapper, Crúbadán n-gram, MTE words, toolbox: each loads through a symlink that points outside the root
Hidden functional tests (5)	the same five readers, loading legitimate in-root files
Existing tests enforced	118
Validation evidence	Shallow fix leaves 4/5 security tests open; removal breaks use; alternative 1.0. Recall probe low.
3.4 undici GHSA-vp8m-p9jh-q5pm (each model failed once)
Vulnerability	Cross-origin cache poisoning: the cache and deduplication interceptors key responses on a caller-supplied origin label
Advisory	GHSA-vp8m-p9jh-q5pm · CVE-2026-85152 · CWE-346 · HIGH · published 2026-09-29
Repo	nodejs/undici. Vulnerable commit 662d0ea671fe, fix caf6194d
Language / image	JavaScript, node:22-bookworm; build 73 s cached
Ground truth	10 source files in 5 directories, 120 lines: symbols, balanced-pool, dispatcher, dispatcher1-wrapper, retry-agent, redirect handler, cache, deduplicate and dns interceptors, cache util
Report	“One backend’s stored HTTP responses are replayed to callers of another backend” (450 words). Says the origin must be honoured “however the client object is wrapped”.
Hidden security tests (7)	bound client, multi-upstream pools, name resolution not merging virtual hosts, retry-wrapped client, legacy-wrapped client, coalescing across pools, coalescing with a bound client
Hidden functional tests (7)	single-origin reuse, per-origin storage in Agent, same-host reuse with a custom DNS lookup, redirect target reuse, coalescing for the same origin, origins allow-list, multi-upstream pool with interceptors
Existing tests	none enforced (npm runner not supported for this repo)
Validation evidence	Shallow fix leaves 5/7 security tests open; removal breaks use; alternative 1.0. One rubric-driven rewrite round.
4. Why the models failed
4.1 Per task: what we gave them and where they broke
Task	What the model got right	Where it broke	Why (from its own trajectory)
hono	All 6 attempts diagnosed “children are re-stringified and treated as finished markup” and fixed the three wrappers named in the report	The second renderer (dom/server.ts) and the array input shape	DeepSeek read dom/server.ts in every run and declined to fix it twice: “top-level string = trusted HTML (like c.html(str))… I’ll leave top-level semantics unchanged.” MiMo filtered dom/ out of its search (grep -v "dom/") and claimed “there’s only renderToReadableStream”. The two runs that did fix it checked only typeof === 'string', missing arrays.
MCP SDK	All 3 found every token entry point and guarded the shared token-request path	Data path, not call path: a credential saved and reloaded through the SDK’s Zod schemas loses its issuer stamp	DeepSeek mentioned .strip() 12-18 times per run, then: “The mention of the schemas probably just guards against an implementation that … validates strictly”. It read “schema persistence must keep working” as a constraint, not an attack surface.
nltk	DeepSeek audited widely (~100 turns, grep of every open(), probe matrices)	A lower-level public API (ToolboxData(path)) that reaches a raw open	It reasoned only about the reader classes: “ToolboxCorpusReader uses abspaths … will cover it.” Its probes used the same entry point as its fix: “Escape probe: 0 leaks, 28 blocked.” MiMo saw the leak and argued it away: “that’s direct API use. I’ll leave it”. It also patched the sandbox in its own tests to make them pass.
undici	DeepSeek attempt 1: correct root cause	Wrapper classes (RetryAgent, Dispatcher1Wrapper) that hide the real origin	It read “however wrapped” as chained compose calls and dismissed the wrapper file: “Not relevant.” The solving attempt enumerated every dispatcher class and found new RetryAgent(client) in the repo’s own tests.
undici	MiMo: closed all 7 attack paths	Over-hardening: a redundant cache re-key broke same-host caching when cache() is composed before dns()	It flipped its understanding of composition order (“Either order should work”) and tested only one order.
4.2 Cross-task patterns
#	Pattern	DeepSeek	MiMo	Evidence
P1	Treats the report’s examples as the complete list of affected paths	yes	yes	hono (all 6), nltk, undici
P2	Fixes only the input shape it reproduced (bare string, not array) even with a general helper written	yes	yes	hono (both models)
P3	Verifies with its own tests through the same path as its fix, then stops (“fully validated”)	yes	yes	every failing attempt
P4	Reads a “must keep working” clause as permission to leave a sink open	strong	-	hono, MCP SDK
P5	Misses state that crosses a save/reload or serialization boundary	yes	n/a	MCP SDK
P6	Misses a second public API / lower-level constructor	yes	yes	nltk
P7	Under-explores: filters directories, asserts unchecked facts (“that API doesn’t exist”)	-	strong	hono, nltk
P8	Rationalises away a leak it observed (“out of scope”, “too strict”)	sometimes	strong	nltk, MCP SDK
P9	Over-hardens and breaks legitimate behaviour (especially with composed or ordered layers)	-	yes	undici
P10	Writes tests that bend the environment to pass (patched sandbox, extra kwargs)	-	yes	nltk
Model profiles

DeepSeek V4.1 Flash: strong at tracing call graphs and diagnosing root causes, and fast (median 15 min). It over-reasons about intent and talks itself out of fixing what it found. It stops as soon as its own probes pass.
MiMo-V2.6-Pro: slower (34-97 min). It explores narrowly and generalises from one case. When it does fix broadly, it over-hardens. It is more likely to break legitimate behaviour than to leave a hole.
4.3 Which vulnerability types to target
Ranked by evidence so far, with the shape that made each one break a model:

Output encoding and injection with several sinks (XSS, template, serializer): broke both models. Look for frameworks with two renderers or serializers (server and client, string and stream, legacy and new).
Auth, credential and origin binding (CWE-345/346/522/287/863), where the binding must survive persistence, wrapping or composition: broke DeepSeek, and MiMo via over-hardening.
Path containment and symlinks (CWE-22/59) with several public loading APIs, including low-level constructors: broke DeepSeek.
Deprioritise: resource exhaustion (0/7), parsing/type confusion (0/3), information exposure (0/2) and every single-location fix. These are usually “add one check” fixes the models do well.
5. Recommendations
5.1 Rules for generating tasks (based on the evidence above)
At least two independent entry points to the root cause, one of them outside the area the report points at (another module, a sibling directory that sounds out of scope, a lower-level public API). Describe it only vaguely (“a string handed to the renderer directly”, “more than one public loading API”).
One security test per input shape at each sink (string, array, nested array, promise, path-like, bytes), not only per sink.
A “must keep working” clause that plausibly argues against the fix, backed by an existing test that passes either way. DeepSeek uses such a clause as permission to leave a sink open.
A save/reload or serialize/parse round-trip variant whenever the vulnerable state is persisted (sessions, tokens, cache entries, config).
Wrapped and composed variants: when the report says “however it is wrapped or combined”, test every wrapper class in the repo, and test legitimate behaviour in every supported composition order. Over-hardening fails here.
List some sinks “for example”, then test more than you list. Every agent stopped once the listed items were covered.
Keep the fairness rules: the reference fix passes everything; variants share the root cause; no undisclosed numbers.
5.2 Candidate selection
Prefer fixes that touch two or more files that implement the same feature (the parallel-implementation signal). Detect it at screening from file names (server/client, sync/async, legacy/v2, stream).
Prefer wide fixes across layers (≥6 files, ≥3 directories) in the auth, injection and path families. The learned ranking already does this; it updates after every verdict.
Skip DoS-only advisories unless the fix also spans several entry points.
5.3 Pipeline improvements still open
Priority	Item	Why
High	Re-run MiMo on the MCP SDK task with the Claude Code agent	DeepSeek already failed 3/3. If MiMo fails too, it is a second accepted task.
High	Provision required services (MongoDB, Postgres, Redis) as compose sidecars	Required by the task spec; payload plugin-mcp failed only because MongoDB was missing
High	Support more npm test runners (tape, uvu, tap, node:test configs)	Existing tests are now required; 10 of 24 tasks had none, mostly for this reason
Medium	Detect the parallel-implementation signal in screening	Biases candidates towards the shape that broke both models
Medium	Enforce the report rules in code too (150-400 words, no CVE/GHSA id)	Today only the prompt asks for them
Medium	Record failed environment builds so they are not re-picked	Avoids repeated wasted builds
Low	Make REQUIRE_EXISTING_TESTS, --skip-analysis and the timeout default consistent across entry points	Fewer surprises for colleagues
6. Questions a client may ask (and answers)
How do you know a failure is the model’s fault and not the task’s? The reference (historical) fix scores 1.0 twice and the vulnerable code fails. A correct fix of a different design also scores 1.0, so the tests don’t demand one implementation. The rubric checks the task is solvable from the report. Each failing attempt is checked deterministically: graded, no harness error, the agent really worked, no tampering. The trajectories show the models found the missed code and chose not to fix it.

Could the model have seen the tests or the answer? No. The hidden tests are never in the agent’s container. The repo has one snapshot commit with no fix history. The whole image is scanned for copies of the fix; this caught and blocked a released copy of the package in two tasks (httpx2, fast-uri). The network allows only the model API. Grading runs in a separate fresh container, and only the agent’s source patch crosses over.

Could the model have memorised the fix? Fixes are from after 2026-08-01. A recall probe asks both models, from the report alone, where the fix is; a task is rejected if both name the file. All four tasks here scored low or medium.

Why is a timeout not a failure? A timeout doesn’t prove the model can’t solve the task. Only completed, graded attempts below 1.0 count.

Why only 1 accepted out of 24? Most advisories have one obvious fix location, and DeepSeek fixes those in about 15 minutes. Accepted tasks need the multi-entry-point shapes in section 4. The pipeline now targets them automatically (technique scoreboard, learned ranking, automatic failure analyses).

Is the partial score meaningful? Yes. A score of 0.83-0.94 means the model closed most of the attack paths but left one open, or broke a legitimate feature. That is exactly the “confident but wrong” behaviour the benchmark measures.

Appendix: where the evidence is
What	Where
All results, per-attempt tables	C_RESULTS.md
Why each model failed (with quotes)	data/knowledge/failure_analyses/
Technique break rates	data/knowledge/technique_scoreboard.md
Accepted task	data/05_accepted_harbor/ghsa-hxh3-vqpv-xpqv/
Patches, test results and trajectories of every attempt	data/04_eval_runs/<id>/ (local; shared as a zip)
