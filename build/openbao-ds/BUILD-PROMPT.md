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

Project root: `/home/mara/cwe-bench`. Task: `openbao-ds`. Pattern: `A`. Track: `injected`.

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
- Advisory: ["GHSA-59W7-V8RR-PR4P", "BIT-OPENBAO-2026-71543", "CVE-2026-71543", "GO-2026-6556"]; openbao/openbao; CWE-863 incorrect authorization: template/pattern injection of metacharacters (glob '*', '+', '/', list ',') from identity data into authorization patterns
- Pinned (vulnerable) commit: parent of 2d4ebafec5c524408b3d4ac1198df909cb7ac8c1 (parent_commit not given in candidate; tree at hosts/15887/repo). Published fix: 2d4ebafec5c524408b3d4ac1198df909cb7ac8c1, e516ce508e1481504cadbfbf62052364339093bc.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "screener_version": "screener-v2",
 "lessons_version": "lessons-v1",
 "model": "claude-opus-5-5",
 "entry_id": "15887",
 "advisory_ids": [
  "GHSA-59W7-V8RR-PR4P",
  "BIT-OPENBAO-2026-71543",
  "CVE-2026-71543",
  "GO-2026-6556"
 ],
 "repo": "openbao/openbao",
 "pinned_commit": "parent of 2d4ebafec5c524408b3d4ac1198df909cb7ac8c1 (parent_commit not given in candidate; tree at hosts/15887/repo)",
 "fix_commits": [
  "2d4ebafec5c524408b3d4ac1198df909cb7ac8c1",
  "e516ce508e1481504cadbfbf62052364339093bc"
 ],
 "trust_decision": {
  "summary": "Identity-template substitutions (entity/alias/group metadata, names) are pasted unescaped into matching patterns: ACL policy paths (where '*', '+' and '/' widen the match), PKI allowed_domains/allowed_uri_sans (glob '*'), and SSH allowed_users/allowed_domains (comma-separated list), so attacker-influenced metadata can widen what the token/role allows.",
  "evidence": [
   "vault/policy/policy_store.go:679",
   "vault/policy/policy.go:351-362",
   "builtin/logical/pki/cert_util.go:272-282",
   "builtin/logical/pki/cert_util.go:564-598",
   "builtin/logical/ssh/path_issue_sign.go:166-181",
   "builtin/logical/ssh/path_issue_sign.go:195-200",
   "sdk/helper/identitytpl/templating.go:158"
  ]
 },
 "landing_point": {
  "where": "vault/policy/policy.go:351-362",
  "why": "Summary says 'Templated Policies ... Wildcard Characters'; an engineer goes to ACL policy templating (parsePaths substitution called from policy_store.go:679) or to identitytpl.PopulateString."
 },
 "fix_sites": [
  {
   "where": "sdk/helper/identitytpl/templating.go:158",
   "entry_point": "public SDK API identitytpl.PopulateString (new BlockedSubstitutions option, fix.diff:981,989-993)",
   "module_kind": "shared library (separate Go module sdk/v2, replaced into root)"
  },
  {
   "where": "vault/policy/policy.go:351-362",
   "entry_point": "any token-authenticated HTTP request whose token carries a templated ACL policy (ACL built per request)",
   "module_kind": "core authorization"
  },
  {
   "where": "vault/policy/policy_store.go:679",
   "entry_point": "same as above (Store.ACL computes blocked chars from policy flags, fix.diff:1498-1506)",
   "module_kind": "core authorization / policy store"
  },
  {
   "where": "vault/logical_system.go:2617",
   "entry_point": "POST /v1/sys/policy/:name and /v1/sys/policies/acl/:name (new allow_wildcards/slashes_in_substitutions flags, fix.diff:1270-1271); GET read response fix.diff:1261-1262",
   "module_kind": "system backend handler + schema (vault/logical_system_paths.go, fix.diff:1284-1336)"
  },
  {
   "where": "builtin/logical/pki/cert_util.go:275",
   "entry_point": "POST /v1/pki/issue/:role, /v1/pki/sign/:role (+ issuer/:ref variants) via validateURISAN (cert_util.go:1431,1451)",
   "module_kind": "secrets engine (second consumer of templating)"
  },
  {
   "where": "builtin/logical/pki/cert_util.go:567",
   "entry_point": "POST /v1/pki/issue/:role, /v1/pki/sign/:role via validateNames (cert_util.go:1314,1321); also ACME order path_acme_order.go:409",
   "module_kind": "secrets engine"
  },
  {
   "where": "builtin/logical/pki/path_roles.go:1135",
   "entry_point": "POST/PATCH /v1/pki/roles/:name (new allow_globs_in_substitutions in create, patch, roleEntry, response; fix.diff:275-331)",
   "module_kind": "secrets engine role schema/serializer"
  },
  {
   "where": "builtin/logical/ssh/path_issue_sign.go:166",
   "entry_point": "POST /v1/ssh/sign/:role (path_sign.go:122) and /v1/ssh/issue/:role (path_issue.go:138); renderPrincipal for allowed_users/allowed_domains/default_user",
   "module_kind": "secrets engine (third consumer)"
  },
  {
   "where": "builtin/logical/ssh/path_issue_sign.go:357",
   "entry_point": "same ssh sign/issue routes; calculateExtensions refactored to inline PopulateString, no blocking added (fix.diff:546-619)",
   "module_kind": "secrets engine"
  },
  {
   "where": "builtin/logical/ssh/path_roles.go:523",
   "entry_point": "POST /v1/ssh/roles/:name (new allow_commas_in_substitutions, fix.diff:631,639-652,695,751)",
   "module_kind": "secrets engine role schema/serializer"
  }
 ],
 "O1_entry_points": 5,
 "O2_out_of_scope_site": {
  "kind": "second_implementation",
  "where": "builtin/logical/pki/cert_util.go:275 and builtin/logical/pki/cert_util.go:567 (PKI glob '*'), builtin/logical/ssh/path_issue_sign.go:172 (SSH comma list) -- secrets engines that run their own identity templating via sdk/framework/identity.go:18, not the ACL policy code"
 },
 "O3_reason_to_dismiss": "The advisory title is about templated ACL *policies*; PKI/SSH role templates are a neighbouring feature configured by an admin on a role, so a solver can argue role allow-lists are 'not policies' and leave them alone (and in SSH, '*' is not a wildcard at all, only ',' matters).",
 "O4_distance": {
  "files": 9,
  "packages": 6,
  "repo_mb": null
 },
 "O5_coupled_behaviour": {
  "what": "Literal '*', '+' and '/' written in the policy/role template text itself (e.g. path \"secret/{{identity.entity.name}}/*\", PKI static glob domains with allow_glob_domains) must keep working; only substituted values are blocked. Opt-in flags (allow_wildcards/slashes_in_substitutions, allow_globs_in_substitutions, allow_commas_in_substitutions) must re-enable them; SSH default_user rendering still allows commas (fix.diff:459) because its result is re-validated against allowed_users; JSON-mode templating (OIDC tokens) must not be blocked.",
  "where": "vault/external_tests/policy/acl_templating_test.go:19; builtin/logical/pki/cert_util.go:593-597; builtin/logical/ssh/path_issue_sign.go:80-87; vault/identity/store_oidc.go:994"
 },
 "O6_input_shapes": [
  "ACL path substitution containing '*' (prefix glob)",
  "ACL path substitution containing '+' (segment wildcard)",
  "ACL path substitution containing '/' (path traversal into sibling segments)",
  "PKI allowed_uri_sans template value containing '*'",
  "PKI allowed_domains template value containing '*' (only matters with allow_glob_domains)",
  "SSH allowed_users / allowed_domains template value containing ',' (list injection)",
  "substitution sources: entity metadata, alias metadata/custom_metadata, group metadata/names (all through PopulateString)"
 ],
 "O7_producer": {
  "kind": "serializer",
  "where": "vault/policy/policy_store.go:168-177 (Entry) and vault/policy/policy_store.go:324-333 / 502-512: the persisted policy entry has no field for the new opt-in flags; the fix adds them only to the in-memory Policy (fix.diff:1406-1407). Tainted values themselves come from identity entity/alias/group metadata written via identity store handlers.",
  "check_calls_producer": false
 },
 "O8_uncovered_routes": [
  {
   "route": "Public SDK helper framework.PopulateIdentityTemplate still renders ACL-mode templates with no blocked substitutions; only a Deprecated comment was added, so any plugin (external PKI/SSH-like engines) using it keeps the glob/list injection.",
   "where": "sdk/framework/identity.go:18-45",
   "reason_to_dismiss": "No in-repo caller remains after the fix and it is marked deprecated; external plugins are 'not our code'.",
   "distance": "sdk/framework (separate sdk/v2 module) vs landing point in vault/policy",
   "present_in_latest": "yes",
   "latest_where": "latest/sdk/framework/identity.go:21"
  }
 ],
 "O8b_injection_room": [
  {
   "where": "builtin/logical/ssh/path_issue_sign.go:232-245",
   "sibling": "a glob-matching host-principal validator (e.g. allowed_domains glob support) fed by the templated allowed_domains, where '*' in a substitution widens the match and only ',' is blocked",
   "why_realistic": "PKI already has allow_glob_domains at builtin/logical/pki/cert_util.go:593-597; porting it to SSH host certs is a natural feature request."
  },
  {
   "where": "builtin/logical/pki/cert_util.go:612-640",
   "sibling": "templated allowed_other_sans / allowed_serial_numbers values matched with glob.Glob",
   "why_realistic": "Same role struct already has two *_template flags; a maintainer adding a third template flag would copy the old PopulateIdentityTemplate call."
  },
  {
   "where": "vault/login_mfa.go:887-893",
   "sibling": "if username_format output were matched against an allow-list/glob, the unblocked ACL-mode PopulateString would be a sibling",
   "why_realistic": "It already uses ACLTemplating mode without BlockedSubstitutions."
  }
 ],
 "O9_family": "CWE-863 incorrect authorization: template/pattern injection of metacharacters (glob '*', '+', '/', list ',') from identity data into authorization patterns",
 "O9_dos": false,
 "O10_build": {
  "language": "Go",
  "toolchain": "Go 1.25.8 (go.mod:12), sdk/v2 replaced locally (go.mod:22)",
  "services": [],
  "offline_after_build": true,
  "project_tests": "sdk/helper/identitytpl/templating_test.go (TestPopulate_Basic); vault/external_tests/policy/acl_templating_test.go (TestPolicyTemplating, in-process test cluster); builtin/logical/pki/backend_test.go (TestBackend_AllowedURISANsTemplate, TestBackend_AllowedDomainsTemplate); builtin/logical/ssh/backend_test.go (testAllowedUsersTemplate etc.); vault/logical_system_test.go policy CRUD"
 },
 "O11_fix_minutes": 75,
 "O12_red_flags": [],
 "O13_recall_risk": "medium",
 "pattern_fit": "A",
 "j": {
  "j_multi_site": 1,
  "j_sites_touched": "sdk/helper/identitytpl/templating.go, sdk/framework/identity.go (comment only), vault/policy/policy.go, vault/policy/policy_store.go, vault/logical_system.go, vault/logical_system_paths.go, builtin/logical/pki/cert_util.go, builtin/logical/pki/path_roles.go, builtin/logical/ssh/path_issue_sign.go, builtin/logical/ssh/path_roles.go",
  "j_sibling_sites": "yes",
  "j_cause_other_layer": 1,
  "j_defence_ineffective": 0,
  "j_overbroad_breaks_legit": 1,
  "j_tempting_wrong_fix": "Reject '*' and '+' in substituted values inside ACL policy templating only (or escape them), missing '/' in ACL paths, PKI glob '*' and the SSH comma list, or block globally in PopulateString and break JSON/OIDC templating and literal wildcards."
 },
 "out_of_scope_notes": [
  "Published fix does not persist the new policy opt-in flags in the storage Entry (vault/policy/policy_store.go:168-177, 324-333, 502-512); they are lost on cache eviction/restart (fails closed, functional bug, still absent in latest).",
  "vault/login_mfa.go:887 renders MFA username_format in ACL mode without blocked substitutions; different sink (external MFA username), not pursued.",
  "PKI allowed_domains with allow_subdomains: a substituted short value (e.g. a TLD) also widens HasSuffix matching (builtin/logical/pki/cert_util.go:585-590); different mechanism from wildcard characters, not pursued.",
  "Comment at fix.diff:981 claims BlockedSubstitutions defaults to [\"*\",\"+\"] in ACL mode, but no default is implemented; nil blocks nothing."
 ],
 "unverified": [
  "repo_mb not measured (no shell); OpenBao is clearly above 5 MB and below 1.5 GB.",
  "pinned_commit hash not provided in inputs; tree assumed to be parent of the first fix commit.",
  "Whether the second fix commit e516ce5 is fully contained in fix.diff was not checked separately.",
  "Exact ACL '+'/'*' matching semantics in vault/policy/acl.go not re-read; taken from changelog fix.diff:771-775.",
  "Whether ACME requests ever carry an EntityID (reaching the PKI template code) not verified."
 ]
}
  ```
- Published fix sites:   - sdk/helper/identitytpl/templating.go:158 — entry point: public SDK API identitytpl.PopulateString (new BlockedSubstitutions option, fix.diff:981,989-993) [shared library (separate Go module sdk/v2, replaced into root)]
  - vault/policy/policy.go:351-362 — entry point: any token-authenticated HTTP request whose token carries a templated ACL policy (ACL built per request) [core authorization]
  - vault/policy/policy_store.go:679 — entry point: same as above (Store.ACL computes blocked chars from policy flags, fix.diff:1498-1506) [core authorization / policy store]
  - vault/logical_system.go:2617 — entry point: POST /v1/sys/policy/:name and /v1/sys/policies/acl/:name (new allow_wildcards/slashes_in_substitutions flags, fix.diff:1270-1271); GET read response fix.diff:1261-1262 [system backend handler + schema (vault/logical_system_paths.go, fix.diff:1284-1336)]
  - builtin/logical/pki/cert_util.go:275 — entry point: POST /v1/pki/issue/:role, /v1/pki/sign/:role (+ issuer/:ref variants) via validateURISAN (cert_util.go:1431,1451) [secrets engine (second consumer of templating)]
  - builtin/logical/pki/cert_util.go:567 — entry point: POST /v1/pki/issue/:role, /v1/pki/sign/:role via validateNames (cert_util.go:1314,1321); also ACME order path_acme_order.go:409 [secrets engine]
  - builtin/logical/pki/path_roles.go:1135 — entry point: POST/PATCH /v1/pki/roles/:name (new allow_globs_in_substitutions in create, patch, roleEntry, response; fix.diff:275-331) [secrets engine role schema/serializer]
  - builtin/logical/ssh/path_issue_sign.go:166 — entry point: POST /v1/ssh/sign/:role (path_sign.go:122) and /v1/ssh/issue/:role (path_issue.go:138); renderPrincipal for allowed_users/allowed_domains/default_user [secrets engine (third consumer)]
  - builtin/logical/ssh/path_issue_sign.go:357 — entry point: same ssh sign/issue routes; calculateExtensions refactored to inline PopulateString, no blocking added (fix.diff:546-619) [secrets engine]
  - builtin/logical/ssh/path_roles.go:523 — entry point: POST /v1/ssh/roles/:name (new allow_commas_in_substitutions, fix.diff:631,639-652,695,751) [secrets engine role schema/serializer]
- Uncovered routes to confirm (pattern B): none
- Design plan from the lead: No lead plan is provided for this task — you are the lead as well as the builder. Using the Design section above and the screener record, design the task yourself and WRITE YOUR PLAN in `notes.md` BEFORE you build:
  - choose the main lever and at least one more, each with a DIFFERENT reason a solver would dismiss or skip it;
  - decide the sites, routes and input shapes the security tests will cover;
  - identify the coupled must-keep-working behaviour next to each lever, for the functional tests;
  - for the injected track: decide the realistic sibling gap(s) to add — each must be code a maintainer could plausibly have left, reachable through the real entry point, covered by a stated invariant, and placed where the published fix never touches. Add 2–4 siblings at a recurring trust decision, each with its own reason a solver would skip it;
  - if this candidate cannot support a fair task that meets the bar (flaw does not reproduce at the pinned commit through a real entry point, needs network/GPU/GUI at run time, or no design meets the bar), STOP and report why. Do not ship a weak task.
Follow every rule in the Design, Report, Tests and Proof sections exactly. You choose the design; the rules are fixed.
- Host notes: none

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

## Environment (`tasks/openbao-ds/environment/Dockerfile`)
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

## Report to the solver (`tasks/openbao-ds/instruction.md`)
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

## Tests (`tasks/openbao-ds/tests/`)
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
- **Wrong-fix patches** go in `build/openbao-ds/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/openbao-ds/`:**
- `instruction.md`;
- `task.toml`, from `builder/templates/`, with `[metadata]` filled in and the network allowlist
  kept;
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/openbao-ds/manifest.json`:**
- `slug`, `candidate`;
- `pattern`: `A`;
- `builder_prompt_version`: `build-v1`;
- `"strict_gate": true`;
- `verified`: entry point, sites, routes, services, project tests run;
- `leak_terms`, `patch_checks`, `wrong_fix_catalogue`;
- `traps`: one entry per lever, with `shape`, `where` (file:line), `security_tests`,
  `coupled_functional_tests`, `security_fail_patch`, and `realistic_because` (for pattern B: "real,
  unmodified upstream code");
- `status`.

**Also in `build/openbao-ds/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `builder/templates/` and `harness/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I builder/gate.py openbao-ds --only static
python3 -I builder/gate.py openbao-ds --only nop
python3 -I builder/gate.py openbao-ds --only oracle
python3 -I builder/gate.py openbao-ds --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/openbao-ds/`;
  - edit only `tasks/openbao-ds/`, `build/openbao-ds/` and, for pattern B, the register;
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
