# seaweedfs-table-storage-authz — a task that DeepSeek V4.1 Flash and MiMo-V2.6-Pro both fail 3/3

**Status of 2026-10-21: confirmed both-model breaker.** Sources: the task build and validation records, the fairness review and its human sign-off, every counted attempt's transcript, final code and per-test results, and the independent audit of every counted attempt.

## Summary

- **Result: both target models failed all 3 counted attempts; neither reached 1.0.**
  - DeepSeek V4.1 Flash: 0.0, 0.0, 0.0.
  - MiMo-V2.6-Pro: 0.9032, 0.871, 0.0.
- Every attempt finished on its own (no timeout). Agent time: DeepSeek 34, 37 and 25 minutes; MiMo 103, 91 and 156 minutes, of a 3-hour limit.
- **Audited: yes.** Each counted attempt was audited independently and judged a genuine model failure ("model-failed", trustworthy, high confidence), with no access to the hidden tests and no lookup.
- The result does not hinge on one test. Every attempt failed at least two tests, and removing any single route's tests (security and coupled functional) still leaves all 6 attempts below 1.0.
- Why both fail: the rule has to be applied on a second front end (the Iceberg REST catalog) whose authenticator can report a caller **only by name**. All 6 attempts got that path wrong in one direction or the other: they either left a name-only remote caller open, or refused the credential-less request that the open default must keep serving. DeepSeek also made explicit denies override owners and administrators, and two attempts cut off the trusted local shell.

## 1. The task

**Vulnerability (CWE-863, incorrect authorization).** SeaweedFS (Go) is a multi-tenant object store whose S3 gateway also serves table storage: the S3 Tables API and an Iceberg REST catalog. An authenticated caller holding only ordinary permissions, in its own account, can read, change and delete table storage owned by another account. Two mechanisms combine: an identity is mis-derived as the shared administrator account, and the open-by-default fallback ("allow when no rule decides") is applied to authenticated callers instead of only to credential-less requests.

**Base advisory:** GHSA-HGPF-8634-G44C (CVE-2026-55873, GO-2026-6329). Vulnerable commit `b56d155b`, the direct parent of the published fix `b1346388`. The published fix changes principal derivation, the permission evaluator, the default-allow decision and the catalog's defaults. It does not cover the further routes below.

**What the task contains.** Twelve routes to the same rule, 31 security tests in all. Routes 1–3 are the advisory's own flaw (published-fix sites). Routes 4–7, 11 and 12 are real, unmodified upstream code at the pinned commit that the published fix left open. Routes 8–10 are sibling operations added for the task (`environment/injection.patch`) in files the published fix never touches.

| Route | Origin | What leaks | What must keep working next to it |
|---|---|---|---|
| 1. An identity in the shared admin account, or one whose configured account does not exist, is treated as administrator (6 tests) | advisory | other accounts' buckets read, deleted, deny policy bypassed | administrators and wildcard identities still manage any bucket, also through the admin console |
| 2. Open default applied to authenticated callers on every S3 Tables operation (10 tests) | advisory | get, list, delete, create, policy and tag operations on another account's storage | owners, explicit grants, recorded bucket policies, anonymous and no-identity deployments |
| 3. Catalog caller reported only by name falls open (4 tests) | advisory, second front end | namespaces listed and created in another account's bucket | embedded-authenticator owners, a credential-less request on an open-default catalog, the trusted shell and `weed mini` |
| 4. A credential-less request names its own account through an internal header (2 tests) | real code left open | acts as admin or owner, bypassing an explicit deny | no-identity deployments stay open and still honour a deny |
| 5. An identity-provider claim equal to `admin` (2 tests) | real code left open | administrator without admin permissions | catalog admin and owner |
| 6. A caller known only by the name `admin` (1 test) | real code left open | administrator through the catalog | trusted local tools that act as admin by name (console, shell) |
| 7. Catalog create writes metadata before authorizing (1 test) | real code left open | a refused create leaves files behind | owner creates a table through the catalog |
| 8. Bucket usage takes the owner from the caller-supplied ARN (1 test) | added for the task | another account's owner and namespace count | owner reads its usage |
| 9. Batch delete authorizes only the first table (1 test) | added for the task | another account's table deleted | owner batch-deletes its own tables |
| 10. Catalog-wide table index reads storage directly (1 test) | added for the task | other accounts' table names | owner's index lists its own tables |
| 11. Create-on-commit writes metadata and table path before authorizing (1 test) | real code left open | a refused commit leaves storage behind | owner creates a table on commit |
| 12. Catalog refusals answered as server errors (1 test) | real code left open | a refusal not answered as a client error | catalog owner operations |

**Report given to the agent.** A short bug report: the product, the observed cross-account impact, one general security property, contracts, and constraints. It names no file, function, route, count or advisory. The key rule:

> A caller may act on table storage, or on anything recorded within it, only if the caller's account owns it, the caller has been granted the permission the operation needs, or an access rule recorded on the resource allows the caller. This holds for every operation on every entry point that serves remote callers …

It adds that owner and acting identity "come only from what the server has recorded", that "only an identity granted administrative permissions is an administrator", that the open-by-default fallback "applies only to requests that carry no credentials", and that a refusal returns a 4xx and has no side effect. A **Preservation** list says these "keep working exactly as today": owners, administrative or wildcard identities, explicit grants and recorded access rules, credential-less requests on a zero-config or anonymous deployment, and "trusted local administration tooling … that act for an account they name". The reported impact is called "one example, not the full set".

**Hidden tests.** 31 security tests and a functional group of 226 results: 28 task-written preservation tests (32 results with subtests) and the project's own tests for the S3 Tables, Iceberg and gateway routing packages (194 results). They drive the real front ends: SigV4-signed S3 Tables requests to the real gateway with identities from the real config loader, Iceberg REST requests to the catalog as the product wires it (or with an embedding authenticator), and the real `weed shell`, admin console and `weed mini` code paths. Storage is an in-memory filer. Refusals accept any 4xx. Reward = the security pass fraction, or 0 if any functional test fails; 1.0 = solved.

## 2. How we know the task is fair

| Check | Result |
|---|---|
| Vulnerable code | fails all 31 security tests, passes every functional test |
| Reference fix | 1.0, three times, identically |
| A hardened reference and an alternative fix with a different layering (centralized principal and default-allow helpers) | 1.0 each |
| One wrong-fix patch per route (12 patches, each leaving out that route's fix) | each fails the security tests of its route, with every functional test passing |
| Other plausible partial fixes: tighten only the reported listing; guard reads only; block only the `admin` header value; answer a denial with a 500 | each fails security tests |
| Over-broad fixes: refuse every table action; drop the trusted marker for the local shell | each fails functional tests |
| Independent fairness review of every test against the report | READY: every security assertion traced to a clause of the property, every functional assertion to a Preservation bullet or the project's own tests; two rows held for human review |
| Human review of the two held rows and of the tests that decided DeepSeek's scores | confirmed, task kept unchanged |
| Blind fix written from the report alone | not run |
| Upstream fix alone | not run as a separate check |

In total, 20 check patches behaved as declared and the scripted gate passed (vulnerable code, reference, patches).

## 3. Results, attempt by attempt

| Model | Run | Score | Security | Functional | Left open | Broke |
|---|---|---|---|---|---|---|
| DeepSeek | 1 | 0.0 | 31/31 | 224/226 | nothing | admin/owner on a deny-all bucket; credential-less catalog request on an open default |
| DeepSeek | 2 | 0.0 | 31/31 | 223/226 | nothing | the same two, plus the shell managing another account's bucket |
| DeepSeek | 3 | 0.0 | 28/31 | 225/226 | name-only catalog caller (route 3, 2 tests); name-only `admin` (route 6) | credential-less catalog request on an open default |
| MiMo | 1 | 0.9032 | 28/31 | 226/226 | name-only catalog caller (route 3, 2 tests); name-only `admin` (route 6) | nothing |
| MiMo | 2 | 0.871 | 27/31 | 226/226 | name-only catalog caller (route 3, 2 tests); catalog namespace listing of another account's bucket served with 200 (route 3, and the route 12 check of the same request) | nothing |
| MiMo | 3 | 0.0 | 30/31 | 223/226 | a catalog refusal answered with 500 (route 12) | credential-less catalog request on an open default; both shell preservation tests |

- 0 of 6 attempts solved the task.
- Every security failure in every attempt is on the Iceberg catalog. All S3 Tables API routes, both write-before-authorize routes and the three added siblings were closed in all 6 attempts.
- All 6 mishandled the catalog's name-only authenticator path: 3 left a name-only remote caller open (DeepSeek 3, MiMo 1 and 2), and 4 refused the credential-less request the open default must keep serving (DeepSeek 1–3, MiMo 3). DeepSeek 3 did both.
- 2 of 6 made explicit denies override owners and administrators (DeepSeek 1 and 2); 2 of 6 broke the trusted local shell (DeepSeek 2, MiMo 3).
- One MiMo start ended with a provider error after a few seconds, before any work. It was not graded or counted, and was replaced by a fresh run.

## 4. Why both models failed

### 4.1 Left open: the catalog's name-only caller (routes 3 and 6)

The catalog accepts an embedding authenticator that may report a caller only by name, with no identity object. Both models split "remote caller" from "trusted local tool" by whether an identity object is present, so a name-only remote caller lands on the trusted-tool path.
- MiMo, run 1, in its summary: "Remote callers are authenticated callers; only weed shell and the admin UI (which pass a context with no identity) take the tooling path." The name-only remote caller also passes no identity object; the grader then saw it create a namespace in another account's bucket and list `[["sales"]]` from it, and a caller named only `admin` act as administrator on a deny-all bucket.
- DeepSeek, run 3: "`Manager.Execute` still acts as an administrator for the explicitly named account when called from process-local tooling … When a server-authenticated identity is present in the context (Iceberg), that identity is used." Same three tests failed.
- MiMo, run 2 propagated the identity object for remote callers ("Iceberg remote callers keep the non-trusted path") but the name-only caller on an open-default catalog still created a namespace in another account's bucket and listed its namespaces.

### 4.2 Left open: the catalog refusal form (route 12)

- MiMo, run 3 stated "Refusals now map to 4xx (`AccessDenied` → 403) everywhere", yet a refused listing of another account's bucket returned `500` with "table bucket alice-tb not found": the "not found" path was still mapped to a server error.
- MiMo, run 2 answered the same refused listing with `200 {"namespaces":[]}`. The tests require a refusal there, so this failed both the route 3 listing test and the route 12 check.

### 4.3 Broke legitimate behaviour: over-hardening (DeepSeek in all 3 runs, MiMo run 3)

- **Owner and admin on a deny-all bucket** (DeepSeek 1 and 2). DeepSeek's summary: "explicit resource-policy denies are evaluated first, so denies always apply." An administrator then got `403` on a deny-all bucket. The report keeps administrators and owners working "exactly as today"; the audit marked both "stated in instruction, correct fix would pass".
- **The credential-less catalog request on an open default** (4 of 6). DeepSeek 3: "Auth failures are final: removed the 'proceed when DefaultAllow is true' fallbacks in `authenticateS3Tables` and the Iceberg server." The audit: the fix "did not treat an embedded authenticator with DefaultAllow()=true serving an anonymous (no-token) request as open-default", so a request the report keeps open got `403`.
- **The trusted local shell** (DeepSeek 2, MiMo 3). The audit: the fix "applied remote-caller authorization to the local admin shell command". MiMo 3's summary lists "dash's `ExecuteLocal` trusted tooling path" as preserved; the shell was not routed through it, so it could no longer create or manage another account's bucket.

### 4.4 What they got right

Every attempt closed the advisory's own S3 Tables routes, the client-asserted header, the identity-provider claim, both write-before-authorize routes on the catalog, and the three added siblings (usage owner, batch delete, catalog index). DeepSeek 1 and 2 closed all 31 security routes. The failures are not about finding the bug: they come from one coupled boundary (who counts as a remote caller on the catalog) and from fixes that do not respect a behaviour the report keeps.

### 4.5 Model profiles on this task

- **DeepSeek V4.1 Flash:** fast (25–37 minutes) and aggressive. It closes the surface widely, then breaks a preserved behaviour every time (deny precedence, the credential-less open default, the shell).
- **MiMo-V2.6-Pro:** slow (91–156 minutes) and careful about preservation (two attempts broke nothing), but it trusted the "no identity object means local tool" split and left the catalog's name-only caller or refusal form open. Its longest attempt over-hardened and broke the shell.

## 5. Evaluation setup

- Harness: Harbor with the Claude Code agent.
- Models: DeepSeek V4.1 Flash (reasoning effort max) and MiMo-V2.6-Pro; 3 counted attempts each.
- Time limit: 3 hours per attempt (the task's 2-hour agent limit with a 1.5 multiplier). No attempt reached it.
- Offline: the agent could reach only the model APIs, and web tools were disabled. The repository has no git history, and the hidden tests are copied in only after the agent stops.
- Every counted attempt was audited before it counted (an independent Claude Opus 5.5 reviewer reading the transcript, final code and grading):
  - no access to the hidden tests and no lookup of the advisory or upstream fix;
  - grading started after the agent stopped, with no agent activity during grading;
  - every failing test is stated in the report, and a correct fix would pass it.
- What counts: a timeout counts as a failure; an attempt cut off by a provider or network error before grading is not counted.

## 6. Questions you may ask

**Is the failure the model's fault and not the task's?** The reference, a hardened variant and a differently layered alternative all score 1.0, and each wrong-fix patch fails exactly where declared. A fairness review traced every test to the report, and a human review confirmed the borderline rows. After each attempt, an independent audit read the transcript and code: every failure was judged genuine with high confidence.

**Does it hinge on one test?** No. Every attempt failed at least two tests. Removing any single route's security tests together with its coupled functional tests still leaves all 6 attempts below 1.0.

**Could the model have seen the answer?** Routes 4–12 are not covered by the published fix, and routes 8–10 exist only in this task. The agent had no internet and no access to the hidden tests; the audit checked every transcript for hidden-test names, the advisory id, the fix commit and any fetch. An earlier, smaller version of this task (6 routes, 24 security tests) was solved by both models on the first attempt (1.0 each).

**What does a 0.9032, 0.871 or 0.0 mean?**
- 0.9032 and 0.871 mean 28 and 27 of 31 attack tests passed, with nothing broken.
- 0.0 means a legitimate behaviour was broken, since any functional failure scores 0. Two DeepSeek attempts closed every attack route and still scored 0.0 for that reason.

## Appendix

| What | Contents |
|---|---|
| Task package | `instruction.md`, `task.toml`, `environment/` (Dockerfile and `injection.patch`), `solution/` (reference `fix.patch`, `solve.sh`), `tests/` (31 security and 28 preservation tests, test harness, the project's own tests restored from pristine copies, `test.sh`, `score.py`, grader `Dockerfile`) |
| Delivered format | grading in a separate container that applies only the agent's source diff; the instruction, hidden tests, reference fix and scoring are the same as in the version the counted runs used |
| Validation | gate results, 20 check patches, build notes, fairness review, human review |
| Attempts | per counted attempt: score, per-test results, final code, transcript and audit |

- Internal slug: `seaweedfs-ds` (task version 2).
- Counted runs: `seaweedfs-ds-deepseek-r1-20261020-074640-n001`, `-deepseek-r2-20261020-082205-n002`, `-deepseek-r3-20261020-090018-n003`, `-mimo-r1-20261020-093340-n005`, `-mimo-r2-20261020-111746-n006`, `-mimo-r3-20261020-124944-n007`.
- Sources used: the delivered task and `RESULTS.md`; the build record (`manifest.json`, `notes.md`, `FAIRNESS.md`, `HUMAN-REVIEW.md`, `gate_report.partial.json`, gate logs, `trial_detail.json`); per trial `result.json`, `config.json`, verifier JUnit output and `results.json`, transcripts, and `POSTMORTEM.json`.
