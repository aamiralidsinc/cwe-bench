# seaweedfs-ds — a task that DeepSeek V4.1 Flash and MiMo-V2.6-Pro both fail 3/3

**Status of 2026-10-20. Both-model breaker on the counted trial; one dimension still provisional.** The auto-trial accepted this as a both-model failure (`deepseek: failed 0p/3f/0e; mimo: failed 0p/3f/1e`). Per-test grading results are available for every counted attempt and are reported below. Two caveats:

- **Fairness:** the pre-trial review returned **GATE_A: READY** but **NEEDS_HUMAN_REVIEW: YES** — two medium-risk rows are flagged as alternative designs the primary property legitimately rejects (not unfairness), awaiting a human sign-off.
- **Per-attempt audit not yet recorded.** The post-run audit is *prepared* (each counted attempt has an `AUDITOR_BRIEF.md`, a `PREPARED.json` and a full evidence bundle), but no auditor verdict has been recorded. `build/audit_results.py` still lists seaweedfs-ds as **awaiting audit / open**. So the §4 "why" is read off the per-test grading, not off a transcript audit, and the no-lookup / genuine-failure confirmations the jackson report relies on are **not yet produced** for this task. Treat §4 as structural, not audited.

Sources: the task build and validation records (`manifest.json`, `notes.md`), the pre-trial fairness review (`FAIRNESS.md`), the auto-trial record (`auto_trial.out`, `trial_detail.json`), and each counted attempt's per-test `verifier/results.json`.

## Summary

- **Result: both target models failed all 3 counted attempts; neither reached reward 1.0.**
  - DeepSeek V4.1 Flash: 0.0, 0.0, 0.0.
  - MiMo-V2.6-Pro: 0.9032, 0.871, 0.0 (never solved).
- Every counted attempt finished on its own (no timeout). DeepSeek ran 33–38 minutes; MiMo ran 91–157 minutes. One earlier MiMo start died as a provider exception at 10 s (`reward=None`, not graded) and is **not** counted — it is the `1e` in MiMo's record.
- The failures split into two shapes:
  - **DeepSeek closed every attack route but broke a legitimate behaviour.** All three DeepSeek attempts passed 28–31 of 31 security tests yet scored 0.0, because a functional test failed and any functional failure scores 0. In two attempts it closed all 31 security routes and still scored 0.0.
  - **MiMo left routes open.** Its two high attempts broke nothing but left 3–4 security routes open (0.9032 = 28/31, 0.871 = 27/31); its third attempt over-hardened, broke three functional tests and still left one route open (0.0).
- The task is a real library with real gaps. It is seaweedfs/seaweedfs at the commit before a published authorization fix (CVE-2026-55873 / GHSA-HGPF-8634-G44C), with further real routes plus three injected sibling operations that the published fix never touches. The hidden tests drive the real front ends only.
- The result does not hinge on one test. Every counted attempt failed for at least two independent reasons (a broken legitimate behaviour, an open route, or both).

## 1. The task

**Vulnerability (CWE-863, incorrect authorization).** A multi-tenant object store also serves table storage (S3 Tables API + an Iceberg REST catalog). An authenticated caller holding only ordinary permissions, in its own account, can read, change and delete table storage owned by another account. The flaw is a combination of **principal mis-derivation** (an identity is treated as the shared `admin` account) and an **open-by-default fallback** that is applied to authenticated callers instead of only to credential-less requests.

**Base advisory:** CVE-2026-55873 / GHSA-HGPF-8634-G44C / GO-2026-6329. Vulnerable commit `b56d155b`, published fix `b1346388`. The published fix closes only part of the surface.

**The rule given to the agent (instruction.md).** The instruction states one general property, with no file, function, route list or count:

> A caller may act on table storage, or on anything recorded within it, only if the caller's account owns it, the caller has been granted the permission the operation needs, or an access rule recorded on the resource allows it. … The owner of a resource, and the identity under which a request acts, come only from what the server has recorded; neither may be chosen by an identifier the request supplies. … The open-by-default fallback … applies only to requests that carry no credentials. … A refused request returns a client error (4xx) — never a success and never a server error — and performs no side effect.

It preserves, in general terms, owners/admins/wildcards, explicit permissions and recorded bucket policies, anonymous and no-identity zero-config access, and trusted local tooling (shell / console / mini). The reported `ListTableBuckets` impact is named as "one example, not the full set".

**Twelve routes to the same rule.** Seven are real, unmodified code at the pinned commit (T1–T7, several at the published-fix sites); three are injected sibling operations added via `environment/injection.patch`, in files the published fix never touches (T8–T10); two more real-upstream routes were added in the 2026-10-20 sibling-injection upgrade (T11–T12).

| Route | Pattern | What leaks / what must still work |
|---|---|---|
| T1 principal mis-derivation | A | an identity in the shared `admin` account, or one whose configured account does not exist (mapped to admin by the config loader), is treated as administrator — vs admins/wildcards must keep managing any bucket |
| T2 open-by-default on authenticated callers | A | the no-rule-decides fallback grants authenticated callers on every handler — vs anonymous / no-identity zero-config access must stay open |
| T3 second front end (catalog name-only) | A | a catalog caller reported only by name falls open where no policy decides — vs embedded-authenticator owners and open-default must still work |
| T4 client-asserted principal | B | a credential-less request carrying the internal account header (`admin` or an owner account) is treated as that principal, bypassing a Deny |
| T5 IdP claim = admin | B | `sub`/`preferred_username` = `admin` becomes the admin principal without admin permissions |
| T6 name-only admin | B | a caller known to an embedding authenticator only by the name `admin` becomes admin — vs trusted local tools acting as admin by name must still work |
| T7 Iceberg create write-before-authorize | B | CreateTable writes `v1.metadata.json` and the table path before authorization; a refused create must leave nothing |
| T8 usage owner from caller ARN (injected) | B | GetTableBucketUsage authorizes against the account field of the caller-supplied ARN |
| T9 batch delete (injected) | B | BatchDeleteTables authorizes the first table once, deletes every listed table |
| T10 catalog table index (injected) | B | a catalog-wide index reads the filer directly, returns every table under the prefix |
| T11 create-on-commit write-before-authorize | B | the commit protocol's create route writes metadata + path before authorizing and reports a denial as 500; published fix guarded only the plain create route |
| T12 catalog refusal form | B | catalog namespace/table denials were mapped to 500 instead of 4xx |

**Hidden tests.** 31 security tests and a functional group of 226 (the task's `ZZ`-named functional tests plus the project's own pristine `s3tables`/`iceberg`/gateway suites). Reward = the security pass fraction, or **0 if any functional test fails**. 1.0 = solve.

## 2. How we know the task is fair

Before any model ran (build gate, `notes.md`): the pinned commit is the direct parent of the published fix; the vulnerable tree fails all 31 security tests and passes every functional test (nop); the reference patch scores 1.0 three times (oracle); all 20 check patches behaved as declared (the ten `miss_*` leave the matching security test failing with functionals passing; `refuse_all` and `no_trusted_shell` break functionals; `deny_as_500`, `header_admin_only`, `reads_only`, `list_only` leave security failing with functionals passing); and both a `hardening` patch and a differently-layered `alt_principal_default` patch score 1.0, so handler-, dispatcher- and manager-layer fixes are all accepted.

**Pre-trial fairness review (`FAIRNESS.md`): GATE_A READY, NEEDS_HUMAN_REVIEW YES.** Every security assertion was traced to the instruction's property clauses (P/E/O/A/S/U/R/L) and every functional assertion to the preservation bullets or the repository's own visible tests. The verdict, verbatim:

> **READY (gate a).** No row is "yes" or unresolved "maybe": every security assertion follows from P/E/O/A/S/U/R/L and every functional assertion from Pres-1..5 or K. Refusals accept any 4xx; no test pins a file, function, mechanism or error type. The reference, hardening and differently layered `alt_principal_default` patches all score 1.0, so handler-, dispatcher- or manager-layer guards pass. **The two medium-risk rows are alternative designs … that the primary property rejects, not unfairness.**

The two medium-risk rows held for human review:

- **`TestSecZZCatalogOtherUserCannotListNamespaces`** — any 2xx fails, even an empty list. The review reads this as P + E (a namespace listing is itself an act on a bucket the caller may not touch): filtering rather than refusing would still serve an operation on that bucket. "Borderline reading."
- **`TestSecZZBatchDeleteChecksEveryTable`** — neither the caller's nor the other account's table may be removed. The review reads an all-or-nothing refusal as following from R ("a refused request … removes nothing"); a per-element partial success is not a compliant refusal. "Borderline."

The review's explicit human-review ask: *confirm the two borderline readings — catalog namespace listings must be refused with 4xx rather than served empty, and a refused batch delete must perform no per-element partial success.*

The review also flagged, as **quality (non-blocking)**, three instruction hint phrases to neutralize and **one required generalization**: the clause "and for every element of a request that names more than one resource" is redundant (P already covers each resource an act touches) and should be reworded to *"This holds for every request that acts on table storage, whatever its shape."* These are tightening items, not fairness blockers.

## 3. Results, attempt by attempt

Per-test counts are read from each counted attempt's `verifier/results.json`. "Open routes" = security traps with at least one failing test; "broke" = failing functional tests.

| Model | Attempt | Score | Security | Functional | Open routes | Broke (functional) |
|---|---|---|---|---|---|---|
| DeepSeek | 1 | 0.0 | 31/31 | 224/226 | none | AdminsBypassBucketPolicy; CatalogEmbeddedAuthenticatorOpenDefault |
| DeepSeek | 2 | 0.0 | 31/31 | 223/226 | none | AdminsBypassBucketPolicy; CatalogEmbeddedAuthenticatorOpenDefault; ShellManagesAnyAccountsBucket |
| DeepSeek | 3 | 0.0 | 28/31 | 225/226 | T3 (catalog name-only, 2/4); T6 (name-only admin) | CatalogEmbeddedAuthenticatorOpenDefault |
| MiMo | 1 | 0.9032 | 28/31 | 226/226 | T3 (catalog name-only, 2/4); T6 (name-only admin) | none |
| MiMo | 2 | 0.871 | 27/31 | 226/226 | T3 (catalog name-only, 3/4); T12 (catalog refusal form) | none |
| MiMo | 3 | 0.0 | 30/31 | 223/226 | T12 (catalog refusal form) | CatalogEmbeddedAuthenticatorOpenDefault; ShellCreatesBucketForAccount; ShellManagesAnyAccountsBucket |

(The uncounted MiMo start — `reward=None`, provider exception at 10 s — is excluded per house rule.)

- DeepSeek scored 0.0 every time **despite closing most or all attack routes**: two attempts closed all 31 security routes and still scored 0.0 on a broken functional.
- The recurring open route is **T3 (the second front end, catalog name-only open-default)** — open in 3 of 6 attempts — with **T6** and **T12** next.
- The recurring broken legitimate behaviours are exactly the two preservation rows the fairness review called "medium-risk, alternative design": **`TestFuncZZAdminsBypassBucketPolicy`** (owner/admin bypass of a deny-all bucket) and **`TestFuncZZCatalogEmbeddedAuthenticatorOpenDefault`** / the trusted-shell preservations.

## 4. Why both models failed (provisional — from grading, not a transcript audit)

No per-attempt transcript audit has been recorded, so this section reads the structure off the per-test grading rather than off the models' own reasoning. It describes what each fix did, not why the model chose it.

### 4.1 DeepSeek — over-hardening breaks a coupled legitimate behaviour (all 3 attempts)

DeepSeek closed the attack surface aggressively (28–31 of 31 security routes) but, in every attempt, a fix broke a behaviour the property preserves:

- `TestFuncZZAdminsBypassBucketPolicy` failed in attempts 1 and 2 — a fix tightened the deny evaluation so that an admin/owner no longer bypasses a deny-all bucket policy, which the instruction keeps "exactly as today". This is the standard deny-overrides rewrite the fairness review predicted would fail (medium-risk row).
- `TestFuncZZCatalogEmbeddedAuthenticatorOpenDefault` failed in all three — a fix refused the credential-less / name-only catalog path too broadly, breaking the open-default and embedded-authenticator preservation.

Because any functional failure scores 0, closing all 31 security routes (attempts 1 and 2) still yielded 0.0.

### 4.2 MiMo — routes left open, and one over-hardening attempt

MiMo's two high attempts broke nothing but never reached every route:

- The **catalog second front end (T3)** stayed open in both (name-only caller on open-default, and the catalog name-only / other-user listing variants). This is the route that lives in a different package (the Iceberg catalog / Manager) from the reported S3 gateway flaw.
- The **catalog refusal form (T12)** — mapping a denial to 4xx instead of 500 — stayed open in attempt 2.
- Its third attempt over-hardened like DeepSeek (broke the embedded-authenticator open-default and both shell preservations) and still left T12 open, scoring 0.0.

### 4.3 What this looks like structurally

The task couples a legitimate behaviour to every tightening: the open-by-default fallback must stay for credential-less and zero-config deployments while being removed for authenticated callers; admins/owners must keep bypassing a deny-all policy; trusted local tooling must keep acting by name while a remote name-only caller must not. A blunt tighten-everything fix breaks a preservation test (DeepSeek's 0.0s); a fix that respects preservation but stops at the obvious S3-gateway sites leaves the second-front-end and refusal-form routes open (MiMo's 0.9032/0.871). Neither model, in any counted attempt, both closed all 31 routes and preserved everything.

## 5. Evaluation setup

- Harness: Harbor with the Claude Code agent.
- Models: DeepSeek V4.1 Flash and MiMo-V2.6-Pro; up to 3 counted attempts each, early-exit on a solve; 3-hour limit per attempt.
- Offline: the agent could reach only the model APIs; web tools disabled; the repository has no git history; hidden tests are copied in only after the agent stops.
- Reward = security pass fraction, 0 if any functional test fails, 1.0 = solve.
- What counts: a 3-hour timeout would count as a FAIL; an attempt cut off by a provider or network outage is not counted (the uncounted MiMo provider exception above).
- **Audit status: prepared, not recorded.** Each counted attempt has a postmortem evidence bundle (`AUDITOR_BRIEF.md`, `PREPARED.json`, grading + final-code + tests evidence), but no auditor verdict is on file; `build/audit_results.py` lists the task as awaiting audit / open. The per-test numbers in §3 come from the verifier grading, which is independent of the audit.

## 6. Where this sits among our tasks

- Track INJECTED: three of the twelve routes (T8–T10) are injected siblings of the same authorization class, in files the published fix never touches; the other nine are real, unmodified upstream code at the pinned commit, several at the published-fix sites.
- The recipe matches jackson-databind-sib2: one authorization rule, many real routes, at least one route on a second surface the published fix never reached (here the Iceberg catalog / Manager), and a legitimate behaviour coupled to each tightening (open-default preservation, admin/owner deny bypass, trusted local tooling).
- This is a both-model failure on the counted trial, but unlike jackson it is **not yet audit-confirmed** and carries an open NEEDS_HUMAN_REVIEW on two borderline fairness readings. It should not be reported as a fully confirmed breaker until the audit is recorded and the two borderline rows are signed off.

## 7. What is needed before this is a fully confirmed breaker

1. Record the per-attempt audit (the evidence bundles are prepared) so `audit_results.py` moves the task off "awaiting audit / open" with a genuine-failure verdict per counted attempt.
2. Resolve the NEEDS_HUMAN_REVIEW item: confirm the two borderline readings (catalog namespace listings refused with 4xx rather than served empty; a refused batch delete performs no per-element partial success).
3. Apply the fairness quality items (neutralize the three hint phrases; reword the redundant multi-resource clause). These do not change the verdict but tighten the instruction.

## Appendix: what is in the task package

| What | Contents |
|---|---|
| Task | instruction.md (one general property), environment (`injection.patch`, Dockerfile), reference `solution/fix.patch`, 31 security + 226 functional hidden tests |
| Validation | gate report, 20 check patches (`checks/*.patch`), `hardening` + `alt_principal_default` pass patches, `notes.md`, `FAIRNESS.md` |
| Attempts | per counted attempt: `verifier/results.json` (per-test), `trial_detail.json`, final code, and a prepared (not yet recorded) postmortem evidence bundle |
