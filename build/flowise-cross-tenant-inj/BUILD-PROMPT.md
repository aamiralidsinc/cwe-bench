# Build one security-fix benchmark task (build-v1)

## What this is
We build a security-fix benchmark from published, already-fixed advisories in open-source projects.
You build ONE task, from the advisory below.

The task pins the project at the commit just before the published fix and gives a solver agent that
code plus a short problem report (`instruction.md`). Hidden behavioural tests then score the
solver's fix. The tests check that the flaw is closed, using harmless inputs and markers, and that
legitimate use still works.

Everything stays on this machine. Describe each mechanism in one line in notes and reports; the
tests hold the detail, so never write exploitation steps out in prose. Stay inside this advisory's
own protection, in this repository, at the pinned commit. Note anything outside that scope in one
line in your report, and do not build on it.

Project root: `/home/mara/cwe-bench`. Task: `flowise-cross-tenant-inj`. Pattern: `A+B`. Track: `injected`.

## Goal and acceptance
- **The bar.** Two target models (DeepSeek V4.1 Flash, MiMo-V2.6-Pro) must each fail all 3
  finished attempts because of their own judgement.
- **Fairness.** Everything the tests require must be findable from `instruction.md` plus the code,
  or be standard expert knowledge. A careful engineer who knows where to look fixes it in about
  45 minutes.
- **What never counts as a failure:** timeouts, and runs cut by API or network errors.
- **Proof.** A task is built only when the gate passes. A task that misses the bar is reported as
  such, never shipped weaker.

## Inputs
- Advisory: GHSA-CHM3-VQCF-52RX / CVE-2026-70472 - flowiseai/flowise - broken access control / cross-tenant IDOR on credential reference (CWE-285/863). A credential id supplied by the caller must belong to the caller's active workspace (or be shared to it through WorkspaceShared) before the server decrypts it a
- Pinned (vulnerable) commit: 700137738bcaebefd4709021f6d6b0abcd7df0ac. Published fix: d81483b70c997ddf981acc9c49fbd9a02fa345cd.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "screener_version": "screener-v2",
 "lessons_version": "lessons-v1",
 "model": "claude-opus-5-5",
 "entry_id": "10700",
 "advisory_ids": [
  "GHSA-CHM3-VQCF-52RX",
  "CVE-2026-70472"
 ],
 "repo": "flowiseai/flowise",
 "pinned_commit": "parent of d81483b70c997ddf981acc9c49fbd9a02fa345cd (parent_commit not given in candidate)",
 "fix_commits": [
  "d81483b70c997ddf981acc9c49fbd9a02fa345cd"
 ],
 "trust_decision": {
  "summary": "A credential id supplied by the caller must belong to the caller's active workspace (or be shared to it through WorkspaceShared) before the server decrypts it and uses its OpenAI key. At the pinned commit the services look credentials up by id alone.",
  "evidence": [
   "packages/server/src/services/openai-assistants-vector-store/index.ts:13-15",
   "packages/server/src/controllers/openai-assistants-vector-store/index.ts:21",
   "fix.diff:1362-1389",
   "packages/server/src/services/credentials/index.ts:130-133"
  ]
 },
 "landing_point": {
  "where": "packages/server/src/services/openai-assistants-vector-store/index.ts:13",
  "why": "The advisory title names openai-assistants-vector-store, and that service looks up req.query.credential by id with no workspaceId filter."
 },
 "fix_sites": [
  {
   "where": "packages/server/src/controllers/openai-assistants-vector-store/index.ts:7",
   "entry_point": "GET /api/v1/openai-assistants-vector-store/:id",
   "module_kind": "controller (primary)"
  },
  {
   "where": "packages/server/src/controllers/openai-assistants-vector-store/index.ts:28",
   "entry_point": "GET /api/v1/openai-assistants-vector-store",
   "module_kind": "controller (primary)"
  },
  {
   "where": "packages/server/src/controllers/openai-assistants-vector-store/index.ts:43",
   "entry_point": "POST /api/v1/openai-assistants-vector-store",
   "module_kind": "controller (primary)"
  },
  {
   "where": "packages/server/src/controllers/openai-assistants-vector-store/index.ts:64",
   "entry_point": "PUT /api/v1/openai-assistants-vector-store/:id",
   "module_kind": "controller (primary)"
  },
  {
   "where": "packages/server/src/controllers/openai-assistants-vector-store/index.ts:95",
   "entry_point": "DELETE /api/v1/openai-assistants-vector-store/:id",
   "module_kind": "controller (primary)"
  },
  {
   "where": "packages/server/src/controllers/openai-assistants-vector-store/index.ts:119",
   "entry_point": "POST /api/v1/openai-assistants-vector-store/:id (file upload)",
   "module_kind": "controller (primary)"
  },
  {
   "where": "packages/server/src/controllers/openai-assistants-vector-store/index.ts:168",
   "entry_point": "PATCH /api/v1/openai-assistants-vector-store/:id (delete files)",
   "module_kind": "controller (primary)"
  },
  {
   "where": "packages/server/src/services/openai-assistants-vector-store/index.ts:10",
   "entry_point": "same 7 routes; the credential lookup in each service function is replaced by resolveCredentialForWorkspace (fix.diff:1362)",
   "module_kind": "service (primary)"
  },
  {
   "where": "packages/server/src/routes/oauth2/index.ts:80",
   "entry_point": "POST /api/v1/oauth2-credential/authorize/:credentialId",
   "module_kind": "separate router with inline DB access (looks out of scope: OAuth2 feature, not assistants)"
  },
  {
   "where": "fix.diff:942-1009",
   "entry_point": "new helper module tenantRequestGuards (getActiveWorkspaceIdForRequest used by oauth2)",
   "module_kind": "new shared util"
  },
  {
   "where": "packages/server/src/controllers/chat-messages/index.ts:169",
   "entry_point": "DELETE /api/v1/chatmessage/:id (bundled, chatflow IDOR, outside this advisory)",
   "module_kind": "bundled sibling-advisory fix"
  }
 ],
 "O1_entry_points": 8,
 "O2_out_of_scope_site": {
  "kind": "wrapper_or_composition",
  "where": "packages/server/src/routes/oauth2/index.ts:80-82 (POST /oauth2-credential/authorize/:credentialId does the same unscoped credential lookup inline in a router file, outside the assistants module)"
 },
 "O3_reason_to_dismiss": "The OAuth2 routes belong to a separate credential-OAuth feature, and /refresh is whitelisted as unauthenticated (packages/server/src/utils/constants.ts:41), so there is no session workspace to check against. That is a plausible reason to leave it alone.",
 "O4_distance": {
  "files": 4,
  "packages": 1,
  "repo_mb": null
 },
 "O5_coupled_behaviour": {
  "what": "A credential owned by another workspace but shared into the caller's workspace through WorkspaceShared (itemType 'credential') must still resolve. A fix that only adds workspaceId to findOneBy breaks shared credentials.",
  "where": "fix.diff:1373-1383; packages/server/src/services/credentials/index.ts:149-155"
 },
 "O6_input_shapes": [
  "credential id in the query string (req.query.credential), vector-store routes",
  "credential id in the path (req.params.credentialId), oauth2 /authorize",
  "session user vs API-key user (no req.user.id), handled by getActiveWorkspaceIdForRequest (fix.diff:966-975)"
 ],
 "O7_producer": {
  "kind": "none",
  "where": "",
  "check_calls_producer": null
 },
 "O8_uncovered_routes": [
  {
   "route": "GET /api/v1/openai-assistants?credential= (list assistants) decrypts a credential looked up by id only",
   "where": "packages/server/src/services/openai-assistants/index.ts:18-20",
   "reason_to_dismiss": "A different module (openai-assistants, not -vector-store). The advisory names only the vector-store routes.",
   "distance": "sibling service directory plus controller packages/server/src/controllers/openai-assistants/index.ts:22",
   "present_in_latest": "no",
   "latest_where": "latest/packages/server/src/services/openai-assistants/index.ts:18-20"
  },
  {
   "route": "GET /api/v1/openai-assistants/:id?credential= (single assistant) does an unscoped credential lookup",
   "where": "packages/server/src/services/openai-assistants/index.ts:46-48",
   "reason_to_dismiss": "Same as above: a neighbouring feature that the report does not name.",
   "distance": "sibling service; controller packages/server/src/controllers/openai-assistants/index.ts:44",
   "present_in_latest": "no",
   "latest_where": "latest/packages/server/src/services/openai-assistants/index.ts:47-49"
  },
  {
   "route": "POST /api/v1/openai-assistants-file/upload?credential= does an unscoped credential lookup",
   "where": "packages/server/src/services/openai-assistants/index.ts:87-89",
   "reason_to_dismiss": "Mounted under a third router name (openai-assistants-file, packages/server/src/routes/openai-assistants-files/index.ts:8) whose download sibling is public, so it reads as a file-upload helper.",
   "distance": "third router, shares the openai-assistants controller packages/server/src/controllers/openai-assistants/index.ts:119",
   "present_in_latest": "no",
   "latest_where": "latest/packages/server/src/services/openai-assistants/index.ts:89-91"
  },
  {
   "route": "POST /api/v1/oauth2-credential/refresh/:credentialId decrypts, uses and rewrites a credential looked up by id only",
   "where": "packages/server/src/routes/oauth2/index.ts:314-316",
   "reason_to_dismiss": "Whitelisted as an unauthenticated route (packages/server/src/utils/constants.ts:41), so it has no session workspace. It looks like a token-refresh feature by design.",
   "distance": "same file as the fixed /authorize handler, 230 lines below",
   "present_in_latest": "yes",
   "latest_where": "latest/packages/server/src/routes/oauth2/index.ts:357-359"
  },
  {
   "route": "DELETE assistant (OpenAI type) reloads the stored assistant.credential by id without workspaceId",
   "where": "packages/server/src/services/assistants/index.ts:185-187",
   "reason_to_dismiss": "The assistant row itself is workspace-scoped (line 172-175), and its credential was checked at create time (line 57-60), so it reads as already protected.",
   "distance": "packages/server/src/services/assistants (third directory)",
   "present_in_latest": "no",
   "latest_where": "latest/packages/server/src/services/assistants/index.ts:186-187"
  }
 ],
 "O8b_injection_room": [
  {
   "where": "packages/server/src/services/evaluations/index.ts:176-178",
   "sibling": "LLM-evaluation credentialId is looked up unscoped; our copy could make it decrypt and use the key the way the vector-store service does",
   "why_realistic": "At the pinned commit it is only an existence check, written in the same copy-paste style as the vector-store lookups, and it is still unscoped in latest (latest/packages/server/src/services/evaluations/index.ts:177)."
  },
  {
   "where": "packages/server/src/controllers/openai-assistants/index.ts:14",
   "sibling": "an assistants 'list files' or 'list vector stores' helper that calls an unscoped credential lookup",
   "why_realistic": "The openai-assistants service already repeats the same unscoped lookup three times, so a fourth copy would look natural."
  }
 ],
 "O9_family": "broken access control / cross-tenant IDOR on credential reference (CWE-285/863)",
 "O9_dos": false,
 "O10_build": {
  "language": "TypeScript (Node ^20)",
  "toolchain": "pnpm monorepo + turbo; jest in packages/server",
  "services": [
   "sqlite (default, embedded)"
  ],
  "offline_after_build": true,
  "project_tests": "packages/server package.json:50 runs jest. At the pinned commit there are no tests for openai-assistants*, oauth2 or tenantRequestGuards; the fix adds only tenantRequestGuards.test.ts (fix.diff:645-937)."
 },
 "O11_fix_minutes": 50,
 "O12_red_flags": [],
 "O13_recall_risk": "medium",
 "pattern_fit": "A+B",
 "j": {
  "j_multi_site": 1,
  "j_sites_touched": "controllers/openai-assistants-vector-store/index.ts, services/openai-assistants-vector-store/index.ts, routes/oauth2/index.ts, enterprise/utils/tenantRequestGuards.ts (plus 18 bundled files for sibling IDOR advisories)",
  "j_sibling_sites": "yes",
  "j_cause_other_layer": 0,
  "j_defence_ineffective": 1,
  "j_overbroad_breaks_legit": 1,
  "j_tempting_wrong_fix": "Add workspaceId to findOneBy in the seven vector-store service functions only. This breaks shared credentials and misses openai-assistants and oauth2."
 },
 "out_of_scope_notes": [
  "The fix commit bundles several unrelated tenant-isolation fixes (chatflow lookups, leads, upsert-history, document-store preview, evaluations/dataset delete, enterprise user/role/workspace/org reads). c_fix_sites=60 overstates this advisory's own scope.",
  "packages/server/src/controllers/openai-assistants/index.ts:63-65 getFileFromAssistant loads a chatflow by id without a workspace (public download route); this is a chatflow concern, not credential scope.",
  "packages/server/src/services/credentials/index.ts:130-156 filters by workspaceId before checking WorkspaceShared, so shared credentials may never resolve through getCredentialById; this is a correctness issue."
 ],
 "unverified": [
  "pinned_commit hash: the candidate gives parent_commit null; the repo directory is assumed to be the parent of the fix commit.",
  "repo_mb not measured (no shell used).",
  "O1 counts 7 vector-store routes plus oauth2 /authorize. The route-to-handler mapping was read from packages/server/src/routes/openai-assistants-vector-store/index.ts:9-36.",
  "j_defence_ineffective=1 rests on the RBAC checkPermission('assistants:*') middleware (packages/server/src/routes/openai-assistants-vector-store/index.ts:9-36). It is present but checks role only, not tenant.",
  "Hidden tests must mock the OpenAI SDK. The workspace check runs before any outbound call, so offline testing is feasible, but this was not verified by running anything.",
  "The openai-assistants routes were fixed in latest, probably by one of the 4 sibling advisories (c_sibling_advisories=4). This raises recall risk for those O8 routes in particular.",
  "The oauth2 /refresh being whitelisted may be intentional; whether the maintainers count it as in scope is unknown."
 ]
}
  ```
- Published fix sites:   - packages/server/src/controllers/openai-assistants-vector-store/index.ts:7 — entry point: GET /api/v1/openai-assistants-vector-store/:id [controller (primary)]
  - packages/server/src/controllers/openai-assistants-vector-store/index.ts:28 — entry point: GET /api/v1/openai-assistants-vector-store [controller (primary)]
  - packages/server/src/controllers/openai-assistants-vector-store/index.ts:43 — entry point: POST /api/v1/openai-assistants-vector-store [controller (primary)]
  - packages/server/src/controllers/openai-assistants-vector-store/index.ts:64 — entry point: PUT /api/v1/openai-assistants-vector-store/:id [controller (primary)]
  - packages/server/src/controllers/openai-assistants-vector-store/index.ts:95 — entry point: DELETE /api/v1/openai-assistants-vector-store/:id [controller (primary)]
  - packages/server/src/controllers/openai-assistants-vector-store/index.ts:119 — entry point: POST /api/v1/openai-assistants-vector-store/:id (file upload) [controller (primary)]
  - packages/server/src/controllers/openai-assistants-vector-store/index.ts:168 — entry point: PATCH /api/v1/openai-assistants-vector-store/:id (delete files) [controller (primary)]
  - packages/server/src/services/openai-assistants-vector-store/index.ts:10 — entry point: same 7 routes; the credential lookup in each service function is replaced by resolveCredentialForWorkspace (fix.diff:1362) [service (primary)]
  - packages/server/src/routes/oauth2/index.ts:80 — entry point: POST /api/v1/oauth2-credential/authorize/:credentialId [separate router with inline DB access (looks out of scope: OAuth2 feature, not assistants)]
  - fix.diff:942-1009 — entry point: new helper module tenantRequestGuards (getActiveWorkspaceIdForRequest used by oauth2) [new shared util]
  - packages/server/src/controllers/chat-messages/index.ts:169 — entry point: DELETE /api/v1/chatmessage/:id (bundled, chatflow IDOR, outside this advisory) [bundled sibling-advisory fix]
- Uncovered routes to confirm (pattern B):   - packages/server/src/services/openai-assistants/index.ts:18-20 — GET /api/v1/openai-assistants?credential= (list assistants) decrypts a credential looked up by id only (reason to dismiss: A different module (openai-assistants, not -vector-store). The advisory names only the vector-store routes.; still in latest: no)
  - packages/server/src/services/openai-assistants/index.ts:46-48 — GET /api/v1/openai-assistants/:id?credential= (single assistant) does an unscoped credential lookup (reason to dismiss: Same as above: a neighbouring feature that the report does not name.; still in latest: no)
  - packages/server/src/services/openai-assistants/index.ts:87-89 — POST /api/v1/openai-assistants-file/upload?credential= does an unscoped credential lookup (reason to dismiss: Mounted under a third router name (openai-assistants-file, packages/server/src/routes/openai-assistants-files/index.ts:8) whose download sibling is public, so it reads as a file-upload helper.; still in latest: no)
  - packages/server/src/routes/oauth2/index.ts:314-316 — POST /api/v1/oauth2-credential/refresh/:credentialId decrypts, uses and rewrites a credential looked up by id only (reason to dismiss: Whitelisted as an unauthenticated route (packages/server/src/utils/constants.ts:41), so it has no session workspace. It looks like a token-refresh feature by design.; still in latest: yes)
  - packages/server/src/services/assistants/index.ts:185-187 — DELETE assistant (OpenAI type) reloads the stored assistant.credential by id without workspaceId (reason to dismiss: The assistant row itself is workspace-scoped (line 172-175), and its credential was checked at create time (line 57-60), so it reads as already protected.; still in latest: no)
- Design plan from the lead: TRACK = INJECTED. This is the breaker recipe (the only tasks that beat both models were injected-sibling tasks at a recurring trust decision).

THE RECURRING DECISION / PROTECTED SINK: A credential id supplied by the caller must belong to the caller's active workspace (or be shared to it through WorkspaceShared) before the server decrypts it and uses its OpenAI key. At the pinned commit the services look credentials up by id alone.

STEP 1 - confirm the published fix's sites and the uncovered routes with tests on the pinned copy. Uncovered routes (pattern B leads to confirm): packages/server/src/services/openai-assistants/index.ts:18-20 (GET /api/v1/openai-assistants?credential= (list assistants) ; dismiss: A different module (openai-assistants, not -vector); packages/server/src/services/openai-assistants/index.ts:46-48 (GET /api/v1/openai-assistants/:id?credential= (single assist; dismiss: Same as above: a neighbouring feature that the rep); packages/server/src/services/openai-assistants/index.ts:87-89 (POST /api/v1/openai-assistants-file/upload?credential= does ; dismiss: Mounted under a third router name (openai-assistan); packages/server/src/routes/oauth2/index.ts:314-316 (POST /api/v1/oauth2-credential/refresh/:credentialId decrypt; dismiss: Whitelisted as an unauthenticated route (packages/); packages/server/src/services/assistants/index.ts:185-187 (DELETE assistant (OpenAI type) reloads the stored assistant.; dismiss: The assistant row itself is workspace-scoped (line).

STEP 2 - INJECT 2 to 4 sibling vulnerabilities of the SAME mechanism into our pinned copy, at these recurring sites (screener injection-room leads; verify each by reading the code): packages/server/src/services/evaluations/index.ts:176-178 -> LLM-evaluation credentialId is looked up unscoped; our copy could make (realistic because: At the pinned commit it is only an existence check, written in the sam); packages/server/src/controllers/openai-assistants/index.ts:14 -> an assistants 'list files' or 'list vector stores' helper that calls a (realistic because: The openai-assistants service already repeats the same unscoped lookup). Each injected sibling MUST: be code a maintainer could plausibly have written (NO tell-tale names, comments, or shortcuts; match the surrounding style); be reachable through the real public entry point; be covered by a stated invariant in instruction.md; be placed where the published upstream fix never touches; and carry a DIFFERENT, plausible reason-to-dismiss from the others (e.g. one looks like a legacy/compat path, one like an internal/trusted caller, one like an unsupported-combination, one like a neighbouring feature). Distinct reasons-to-dismiss are what make a solver fix some sites and miss others - that is the whole lever.

STEP 3 - the hidden security tests require closing the base flaw, every uncovered route, AND every injected sibling, through the real entry point. The oracle (solution/fix.patch) closes all of them. A fix that closes only the sites the report obviously points at must score < 1.0 (add a security_fail check patch modelling exactly that partial fix).

STEP 4 - COUPLED MUST-KEEP-WORKING (one functional test per trap so an over-broad fix fails): A credential owned by another workspace but shared into the caller's workspace through WorkspaceShared (itemType 'credential') must still resolve. A fix that only adds workspaceId to findOneBy breaks  (near fix.diff:1373-1383; packages/server/src/services/c). Also keep every legitimate use of the recurring mechanism working.

Aim for at least 3 levers with DIFFERENT reasons to dismiss (base + uncovered routes + injected siblings). Every sibling must be findable by a blind engineer from instruction.md + the code; if the blind fix cannot find one, it is unfair - drop it. instruction.md stays product-level: the system, one impact with one user-level trigger, the security property as invariants worded to cover EVERY route and sibling ('no value of X may ...'), a natural list not a count; keep legitimate use working; never name files/functions/fields/CVEs (all go in manifest.leak_terms). Register each injected sibling and uncovered route in build/audit/uncovered-routes.tsv.
- Host notes: Language: TypeScript (Node ^20). Offline after build, no external services. INJECTED track: siblings go in OUR copy only, never shipped upstream - register them. The host has a recurring trust decision (8 entry points) and screener-noted injection room. Build + test the security logic via the real entry points; the project's own tests for the area must pass at the pinned commit. Pin at the vulnerable commit; keep unrelated earlier fixes present.

## Design: where difficulty comes from
Models find the code the report leads to and diagnose it correctly. They fail on scope. Build these
in, in order of evidence:
1. **Pattern A: the published fix's far sites.**
   - The report leads to one site. The tests cover every entry point the published fix protects,
     including one in a module that looks out of scope: a second implementation, a lower-level
     public API, a wrapper, a save/reload path, or a defaults or merge route.
   - Give it a plausible **reason to dismiss**, and **distance**: another file or package from the
     landing point.
2. **Pattern B: uncovered routes.**
   - Routes into the same protected sink where the advisory's own protection is missing at the
     pinned commit, and which the published fix did not touch.
   - They are unmodified upstream code, so a solver can argue they were never covered.
   - The strongest lever found so far: DeepSeek 6 of 6 on one; both models 0 of 3 on three combined.
3. **Input-shape variants** that the general rule covers but a one-case fix misses (a plain string
   and an array).
4. **A coupled must-keep-working behaviour** next to the sink, tested functionally, so an
   over-broad fix fails. MiMo tends to over-harden.
5. **Producer off the check's path.** The check depends on data produced elsewhere (a schema,
   serializer, cache, mapper or config loader) and does not call it. It counts only if the producer
   is infrastructure, not a request handler.
6. **Injected siblings**, only where the plan asks for them. Each must be:
   - code a maintainer could have written, with no deceptive names or comments;
   - reachable through the real entry point;
   - covered by a stated invariant;
   - placed where the upstream fix never touches.

Aim for at least two levers with **different** reasons to dismiss.

Never add:
- encoding, verb, protocol or role/direction variants;
- more routes of one concept;
- resource-exhaustion traps.

Every lever must be findable by a blind engineer from the report and the code. A lever that a blind
fix cannot find is unfair: remove it.

**Pattern B rules:**
- Confirm each route with a behavioural test on the pinned copy before relying on it. The
  screener's claim is only a lead.
- Append one row per route to `/home/mara/cwe-bench/build/audit/uncovered-routes.tsv`, using its existing
  header. Columns:
  - `task`, `repo`, `advisory`;
  - `trap_ref` (the manifest trap id only; no mechanism text, since the manifest holds the detail);
  - `real_upstream`;
  - `present_in_latest` (`yes`, `no` or `unknown`, from a read-only look at current upstream code if
    you can reach it);
  - `public_upstream_report`, `in_current_scope`, `built`, `note`;
  - `disclosure_status` (`pending client decision`).

## Environment (`tasks/flowise-cross-tenant-inj/environment/Dockerfile`)
- **Base and code.** A small official base image. The repo goes into `/app` at the pinned commit,
  and `/app/.git` is then deleted.
- **Offline.** Install every dependency, tool and service the project and tests need; nothing may
  be downloaded at test time. Services start from `test.sh`.
- **Packages:** `patch`, `curl`, `ca-certificates`, `bash`, `git`.
- **Agent layer.** Append `harness/claude-code.Dockerfile.snippet` unchanged at the end.
- **No test code in the image.** The agent shares the container. Pre-build against stubs; `test.sh`
  copies the real tests in at grading time.
- **Project tests.** The project's own tests for the affected area must pass in the image at the
  pinned commit.
- **No leaked regression tests.** The pinned commit must not already contain the advisory's
  regression tests (check `git log` between the pinned and fix commits).

## Report to the solver (`tasks/flowise-cross-tenant-inj/instruction.md`)
**Write:**
- what the system is, at product level;
- one observed impact, with ONE concrete trigger at user level (HTTP request, CLI call or public API
  use);
- the security properties as **invariants**: who may do what to which data, or what attacker input
  must never achieve. Word each so it covers every tested route and shape ("no value of X may …").
  If there are several, give one natural list, never a count;
- every **contract** the tests need:
  - the refusal form ("a client error with no side effect");
  - any interface or field name a test uses;
  - preservation clauses ("works exactly as today");
  - a legitimate magnitude next to any attack magnitude;
- that examples are examples, not the full set;
- the standard constraints block: fix the problem and its close variants; keep legitimate use
  working; do not modify or add tests; do not look up the upstream fix; do not special-case the
  example.

**Never write:**
- file, package, function, class, field or parameter names a user would not see;
- line numbers, the root cause, the fix approach, or a CVE or GHSA id;
- a list of routes, spellings or roles;
- restricting adverbs ("directly", "only via");
- anything that names or paraphrases a far site, an uncovered route or an injected sibling.

Put every identifier that must not appear in `manifest.leak_terms`.

## Tests (`tasks/flowise-cross-tenant-inj/tests/`)
- **`security/`:** one test per site, route, input shape and form. Each one:
  - goes through the real entry point;
  - fails on the pinned code and passes on a correct fix;
  - asserts the attack is blocked: any client error plus no side effect, never one exact status.
- **`functional/`:**
  - legitimate use, including the coupled behaviour of every lever;
  - where they exist, the project's own tests for the area.
- **No product code in a test's bookkeeping.** Compute expected values and clean-ups in the test
  itself, because a hardened helper must not crash a test.
- **Stubs** of permission or authority answer per resource and verb, like the real thing.
- **Scope.** A test may vary only what the instruction names, and drive only the entry point it
  names.
- **No network**, and nothing that depends on the fix commit being present.
- **Templates.** JUnit XML into the two directories the template names. Copy `score.py` unchanged.
  Edit only the marked command lines of `test.sh`, and keep its agent-kill block.

## Proof
- **The oracle.** `solution/fix.patch` is the published fix reduced to source changes, plus fixes
  for every uncovered route and injected sibling in the task. `solution/solve.sh` applies it to
  `/app`.
- **Wrong-fix patches** go in `build/flowise-cross-tenant-inj/checks/`, listed in `manifest.patch_checks`:
  - one `security_fail` per lever (the fix that misses only that lever);
  - a `functional_fail` (an over-broad or feature-removing fix);
  - a `pass` of kind `hardening` (the oracle plus defensive hardening of the product code the
    security tests import);
  - a `pass` alternative fix where a second valid design is plausible.
- **`manifest.wrong_fix_catalogue`:** for each class, a `checks/` patch, or `n/a: <why>`:
  `refuse_all`, `crash_as_refusal`, `wrong_resource`, `one_role_or_direction`, `reads_only`,
  `check_after_adjustment`, `unlisted_route`, `malformed_identity`, `missing_authority`,
  `adjacent_api`.

## Deliverables
**`tasks/flowise-cross-tenant-inj/`:**
- `instruction.md`;
- `task.toml`, from `builder/templates/`, with `[metadata]` filled in and the network allowlist
  kept;
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/flowise-cross-tenant-inj/manifest.json`:**
- `slug`, `candidate`;
- `pattern`: `A+B`;
- `builder_prompt_version`: `build-v1`;
- `"strict_gate": true`;
- `verified`: entry point, sites, routes, services, project tests run;
- `leak_terms`, `patch_checks`, `wrong_fix_catalogue`;
- `traps`: one entry per lever, with `shape`, `where` (file:line), `security_tests`,
  `coupled_functional_tests`, `security_fail_patch`, and `realistic_because` (for pattern B: "real,
  unmodified upstream code");
- `status`.

**Also in `build/flowise-cross-tenant-inj/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `builder/templates/` and `harness/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I builder/gate.py flowise-cross-tenant-inj --only static
python3 -I builder/gate.py flowise-cross-tenant-inj --only nop
python3 -I builder/gate.py flowise-cross-tenant-inj --only oracle
python3 -I builder/gate.py flowise-cross-tenant-inj --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/flowise-cross-tenant-inj/`;
  - edit only `tasks/flowise-cross-tenant-inj/`, `build/flowise-cross-tenant-inj/` and, for pattern B, the register;
  - do not commit.

## Stop and report instead of shipping when
- the flaw does not reproduce through a real entry point at the pinned commit;
- a planned route or site is not reachable, or the check calls the producer directly (substitute
  another lever the code supports if you can, and say so);
- the task needs network at run time, or a GPU, kernel or GUI;
- the tests are flaky;
- no design meets the bar.

## Report back (under 400 words)
- The gate result for each stage.
- Each lever in one line: pattern, shape, file:line, reason to dismiss.
- Pattern B: each register row.
- The instruction's word count.
- Every guess you could not verify.
- Any fairness concern you see yourself.
- Anything noticed outside the scope, in one line.
- If abandoned, exactly why.
