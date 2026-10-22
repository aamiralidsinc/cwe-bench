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

Project root: `/home/mara/cwe-bench`. Task: `seaweedfs-s3tables-authz`. Pattern: `A+B`. Track: `mined`.

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
- Advisory: GHSA-HGPF-8634-G44C / BIT-SEAWEEDFS-2026-55873 / CVE-2026-55873 / GO-2026-6329 - seaweedfs/seaweedfs - CWE-863 incorrect authorization: principal mis-derivation (shared admin account) plus open-by-default fallback applied to authenticated callers. Whether an S3Tables/Iceberg caller may act on a table bucket is decided by CheckPermissionWithContext from the principal that getAccountID derives (admin principal or owner match wins outright) plus the per-handler open-by-default flag; non
- Pinned (vulnerable) commit: b56d155b315777dab97caea4380528ace087b529. Published fix: b13463880c1fa62e255c058a9228b63cc95b4b36.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "screener_version": "screener-v2",
 "lessons_version": "lessons-v1",
 "model": "claude-opus-5-5",
 "entry_id": "17882",
 "advisory_ids": [
  "GHSA-HGPF-8634-G44C",
  "BIT-SEAWEEDFS-2026-55873",
  "CVE-2026-55873",
  "GO-2026-6329"
 ],
 "repo": "seaweedfs/seaweedfs",
 "pinned_commit": "parent of b13463880c1fa62e255c058a9228b63cc95b4b36 (parent_commit not given in candidate)",
 "fix_commits": [
  "b13463880c1fa62e255c058a9228b63cc95b4b36"
 ],
 "trust_decision": {
  "summary": "Whether an S3Tables/Iceberg caller may act on a table bucket is decided by CheckPermissionWithContext from the principal that getAccountID derives (admin principal or owner match wins outright) plus the per-handler open-by-default flag; non-admin identities whose Account.Id is the shared 'admin' account, and authenticated callers under default-allow, were treated as admin/allowed.",
  "evidence": [
   "weed/s3api/s3tables/permissions.go:94-127",
   "weed/s3api/s3tables/handler.go:178-235",
   "weed/s3api/s3tables/handler.go:208-216",
   "weed/s3api/s3tables/manager.go:22-26",
   "weed/s3api/s3tables/handler_bucket_get_list_delete.go:100-109"
  ]
 },
 "landing_point": {
  "where": "weed/s3api/s3tables/handler_bucket_get_list_delete.go:100-109",
  "why": "The summary names enumeration of table buckets; ListTableBuckets and its per-bucket filter (lines 198-206) is the obvious first stop."
 },
 "fix_sites": [
  {
   "where": "weed/s3api/s3tables/handler.go:208-216",
   "entry_point": "every S3Tables op via HandleRequest (handler.go:88) and Iceberg REST via Manager.Execute: getAccountID principal derivation",
   "module_kind": "shared principal helper (s3tables package)"
  },
  {
   "where": "weed/s3api/s3tables/permissions.go:200-205",
   "entry_point": "all S3Tables/Iceberg ops via CheckPermissionWithContext -> hasIdentityPermission (refactored into hasAdminAction)",
   "module_kind": "shared permission evaluator"
  },
  {
   "where": "fix.diff:423-439",
   "entry_point": "new defaultAllowFor helper in weed/s3api/s3tables/iam.go, used by all handlers",
   "module_kind": "shared auth helper"
  },
  {
   "where": "weed/s3api/s3tables/handler_bucket_get_list_delete.go:100-109",
   "entry_point": "S3Tables X-Amz-Target ListTableBuckets (account gate removed)",
   "module_kind": "HTTP handler"
  },
  {
   "where": "weed/s3api/s3tables/handler_bucket_get_list_delete.go:200-204",
   "entry_point": "S3Tables ListTableBuckets per-bucket filter",
   "module_kind": "HTTP handler"
  },
  {
   "where": "weed/s3api/s3tables/handler_bucket_get_list_delete.go:72-76",
   "entry_point": "S3Tables GetTableBucket",
   "module_kind": "HTTP handler"
  },
  {
   "where": "weed/s3api/s3tables/handler_bucket_get_list_delete.go:306",
   "entry_point": "S3Tables DeleteTableBucket",
   "module_kind": "HTTP handler"
  },
  {
   "where": "weed/s3api/s3tables/handler_bucket_create.go:54-57",
   "entry_point": "S3Tables CreateTableBucket; shell s3tables bucket create; mini bootstrap",
   "module_kind": "HTTP handler"
  },
  {
   "where": "weed/s3api/s3tables/handler_namespace.go:121",
   "entry_point": "S3Tables CreateNamespace; Iceberg POST /v1/namespaces (+ GetNamespace 262, ListNamespaces 349, DeleteNamespace 534)",
   "module_kind": "HTTP handler"
  },
  {
   "where": "weed/s3api/s3tables/handler_policy.go:97",
   "entry_point": "S3Tables Put/Get/Delete TableBucketPolicy, Put/Get/Delete TablePolicy, Tag/ListTags/Untag (lines 97,175,251,352,460,550,649,767,875)",
   "module_kind": "HTTP handler"
  },
  {
   "where": "weed/s3api/s3tables/handler_table.go:146",
   "entry_point": "S3Tables Create/Get/List/Delete/UpdateTable; Iceberg table routes (lines 146,156,389,398,528,535,580,919,928,1061,1070)",
   "module_kind": "HTTP handler"
  },
  {
   "where": "weed/s3api/s3tables/manager.go:39-42",
   "entry_point": "Manager public Go API: new SetTrusted (fix.diff:452-455)",
   "module_kind": "lower-level API / wrapper"
  },
  {
   "where": "weed/s3api/iceberg/server.go:47-55",
   "entry_point": "Iceberg REST catalog routes (iceberg/server.go:88-113): manager default-allow now mirrors gateway",
   "module_kind": "second front end (Iceberg REST) / defaults"
  },
  {
   "where": "weed/shell/s3tables_helpers.go:30",
   "entry_point": "weed shell s3tables.* commands: manager marked trusted",
   "module_kind": "CLI wrapper"
  }
 ],
 "O1_entry_points": 2,
 "O2_out_of_scope_site": {
  "kind": "defaults_or_merge_route",
  "where": "weed/s3api/s3tables/manager.go:22-26 (NewManager forces default-allow true) consumed by weed/s3api/iceberg/server.go:47-55; Manager.Execute forwards only an identity name, weed/s3api/s3tables/manager.go:56-59"
 },
 "O3_reason_to_dismiss": "Manager is documented as a helper 'for shell/admin without HTTP routing' (weed/s3api/s3tables/manager.go:16) and Iceberg is a separate REST protocol in another package, so a solver fixing the S3Tables ListTableBuckets handler can argue the catalog's default-allow is intended zero-config tooling behaviour.",
 "O4_distance": {
  "files": 11,
  "packages": 3,
  "repo_mb": null
 },
 "O5_coupled_behaviour": {
  "what": "Zero-config/anonymous access must keep default-allow, real admins (Admin/*/s3:*/s3tables:* actions) must keep the admin account, owners must still list their own buckets, and weed shell / mini bootstrap (name-only Manager callers) must keep working; flipping NewManager default-allow off or dropping default-allow globally breaks shell bucket creation and zero-config setups.",
  "where": "weed/s3api/s3tables/manager.go:24-25; weed/shell/s3tables_helpers.go:30; weed/command/mini.go:1948-1954; weed/s3api/s3api_tables.go:75-77"
 },
 "O6_input_shapes": [
  "identity struct with Account.Id = shared 'admin' account but non-admin actions (account-less legacy or unknown-account identity)",
  "identity name only, no identity struct (Manager/Iceberg path)",
  "anonymous identity struct (Name or Account.Id = anonymous)",
  "no identity at all (zero-config)",
  "admin action markers '*', 'Admin', 's3:*', 's3tables:*'",
  "trusted local tooling (shell) vs HTTP callers"
 ],
 "O7_producer": {
  "kind": "config_loader",
  "where": "weed/s3api/auth_credentials.go:631-637 and weed/s3api/auth_credentials.go:850-856 assign &AccountAdmin to identities whose configured account does not exist; weed/s3api/auth_credentials.go:407-409 env-credential identity; weed/s3api/auth_credentials.go:1392-1397 auth-disabled identity",
  "check_calls_producer": false
 },
 "O8_uncovered_routes": [
  {
   "route": "Unauthenticated caller under default-allow reaches getAccountID's X-Amz-Account-Id header fallback; a header value 'admin' becomes the admin principal, which bypasses even explicit Deny bucket policies.",
   "where": "weed/s3api/s3tables/handler.go:229-233",
   "reason_to_dismiss": "Only reachable when the gateway already falls open on failed auth (weed/s3api/s3api_tables.go:695-696, weed/s3api/iceberg/server.go:181-182), so it looks like 'default-allow is open anyway'.",
   "distance": "same file as the getAccountID fix site, 15 lines below; entry via weed/s3api/s3api_tables.go and weed/s3api/iceberg/server.go",
   "present_in_latest": "no",
   "latest_where": "latest/weed/s3api/s3tables/handler.go:284-289"
  },
  {
   "route": "getAccountID takes the principal from JWT/STS claims 'sub'/'preferred_username' before Account.Id, with no admin-action guard, so a federated identity whose claim normalizes to 'admin' is treated as admin.",
   "where": "weed/s3api/s3tables/handler.go:190-205",
   "reason_to_dismiss": "Claims come from the trusted IdP; the advisory is about static account-less identities sharing the admin account.",
   "distance": "same function as the fix site; producer in weed/s3api/auth_signature_v4.go:431-450",
   "present_in_latest": "yes",
   "latest_where": "latest/weed/s3api/s3tables/handler.go:241-256"
  }
 ],
 "O8b_injection_room": [
  {
   "where": "weed/s3api/s3tables/handler_table.go:146",
   "sibling": "A further table/namespace handler whose CheckPermissionWithContext context passes h.defaultAllow instead of the per-request helper.",
   "why_realistic": "28 near-identical PolicyContext literals are copy-pasted across 5 handler files; upstream later added handler_maintenance.go and handler_view.go with the same pattern."
  },
  {
   "where": "weed/s3api/s3tables/handler_bucket_create.go:41",
   "sibling": "IAM-path fallback that consults the raw h.defaultAllow flag to drop into the legacy path.",
   "why_realistic": "It already exists un-migrated at the pinned commit and in latest; a maintainer would see it as an IAM-only edge."
  },
  {
   "where": "weed/admin/dash/s3tables_management.go:78-88",
   "sibling": "Another Manager consumer (admin/worker) that forwards a caller-supplied identity name instead of the fixed admin id.",
   "why_realistic": "Manager.Execute takes a free-form identity string and several packages construct their own Manager."
  }
 ],
 "O9_family": "CWE-863 incorrect authorization: principal mis-derivation (shared admin account) plus open-by-default fallback applied to authenticated callers",
 "O9_dos": false,
 "O10_build": {
  "language": "Go",
  "toolchain": "go 1.25.0 (go.mod:3)",
  "services": [],
  "offline_after_build": true,
  "project_tests": "Unit tests in weed/s3api/s3tables (handler_identity_test.go, permissions_test.go) drive handlers with httptest and fake filer clients; fix adds manager_test.go with a recording filer client. test/s3tables has a Makefile-driven integration suite needing a running weed server."
 },
 "O11_fix_minutes": 50,
 "O12_red_flags": [],
 "O13_recall_risk": "medium",
 "pattern_fit": "A+B",
 "j": {
  "j_multi_site": 1,
  "j_sites_touched": "weed/s3api/iceberg/server.go, weed/s3api/s3tables/{handler.go, handler_bucket_create.go, handler_bucket_get_list_delete.go, handler_namespace.go, handler_policy.go, handler_table.go, iam.go, manager.go, permissions.go}, weed/shell/s3tables_helpers.go",
  "j_sibling_sites": "yes",
  "j_cause_other_layer": 1,
  "j_defence_ineffective": 1,
  "j_overbroad_breaks_legit": 1,
  "j_tempting_wrong_fix": "Tighten only ListTableBuckets' per-bucket filter (or its account gate) in the S3Tables handler, leaving getAccountID's admin-account mapping and the Iceberg Manager default-allow untouched."
 },
 "out_of_scope_notes": [
  "Plain S3 object/bucket API access to table-bucket paths (weed/s3api/bucket_paths.go:15) uses separate S3 IAM; not followed.",
  "Admin console lists table buckets straight from the filer (weed/admin/dash/s3tables_management.go:93-118); trusted admin surface, not followed.",
  "normalizePrincipalID collapses ARNs to the trailing segment (weed/s3api/s3tables/handler.go:242-258), so cross-account name collisions are possible; documented warning, not followed."
 ],
 "unverified": [
  "pinned_commit hash: candidate parent_commit is null; repo assumed to be the parent of the fix commit.",
  "repo_mb not measured (no shell); seaweedfs is believed to be well under 1.5 GB and over 5 MB, so no size flag set.",
  "O1 counts two HTTP surfaces (S3Tables JSON API dispatched at weed/s3api/s3tables/handler.go:104-159, about 22 ops, and Iceberg REST at weed/s3api/iceberg/server.go:88-113, 11 handlers); weed shell is trusted. Per-operation count would be about 33.",
  "O8 claims route: whether STS/OIDC session claims (weed/s3api/auth_signature_v4.go:431-434) actually carry a 'sub' or 'preferred_username' an attacker can set to 'admin' depends on the IdP; not verified.",
  "O8 header route: exploitable effect assumes a bucket policy with explicit Deny under default-allow; not exercised."
 ]
}
  ```
- Published fix sites:   - weed/s3api/s3tables/handler.go:208-216 — entry point: every S3Tables op via HandleRequest (handler.go:88) and Iceberg REST via Manager.Execute: getAccountID principal derivation [shared principal helper (s3tables package)]
  - weed/s3api/s3tables/permissions.go:200-205 — entry point: all S3Tables/Iceberg ops via CheckPermissionWithContext -> hasIdentityPermission (refactored into hasAdminAction) [shared permission evaluator]
  - fix.diff:423-439 — entry point: new defaultAllowFor helper in weed/s3api/s3tables/iam.go, used by all handlers [shared auth helper]
  - weed/s3api/s3tables/handler_bucket_get_list_delete.go:100-109 — entry point: S3Tables X-Amz-Target ListTableBuckets (account gate removed) [HTTP handler]
  - weed/s3api/s3tables/handler_bucket_get_list_delete.go:200-204 — entry point: S3Tables ListTableBuckets per-bucket filter [HTTP handler]
  - weed/s3api/s3tables/handler_bucket_get_list_delete.go:72-76 — entry point: S3Tables GetTableBucket [HTTP handler]
  - weed/s3api/s3tables/handler_bucket_get_list_delete.go:306 — entry point: S3Tables DeleteTableBucket [HTTP handler]
  - weed/s3api/s3tables/handler_bucket_create.go:54-57 — entry point: S3Tables CreateTableBucket; shell s3tables bucket create; mini bootstrap [HTTP handler]
  - weed/s3api/s3tables/handler_namespace.go:121 — entry point: S3Tables CreateNamespace; Iceberg POST /v1/namespaces (+ GetNamespace 262, ListNamespaces 349, DeleteNamespace 534) [HTTP handler]
  - weed/s3api/s3tables/handler_policy.go:97 — entry point: S3Tables Put/Get/Delete TableBucketPolicy, Put/Get/Delete TablePolicy, Tag/ListTags/Untag (lines 97,175,251,352,460,550,649,767,875) [HTTP handler]
  - weed/s3api/s3tables/handler_table.go:146 — entry point: S3Tables Create/Get/List/Delete/UpdateTable; Iceberg table routes (lines 146,156,389,398,528,535,580,919,928,1061,1070) [HTTP handler]
  - weed/s3api/s3tables/manager.go:39-42 — entry point: Manager public Go API: new SetTrusted (fix.diff:452-455) [lower-level API / wrapper]
  - weed/s3api/iceberg/server.go:47-55 — entry point: Iceberg REST catalog routes (iceberg/server.go:88-113): manager default-allow now mirrors gateway [second front end (Iceberg REST) / defaults]
  - weed/shell/s3tables_helpers.go:30 — entry point: weed shell s3tables.* commands: manager marked trusted [CLI wrapper]
- Uncovered routes to confirm (pattern B):   - weed/s3api/s3tables/handler.go:229-233 — Unauthenticated caller under default-allow reaches getAccountID's X-Amz-Account-Id header fallback; a header value 'admin' becomes the admin principal, which bypasses even explicit Deny bucket policies. (reason to dismiss: Only reachable when the gateway already falls open on failed auth (weed/s3api/s3api_tables.go:695-696, weed/s3api/iceberg/server.go:181-182), so it looks like 'default-allow is open anyway'.; still in latest: no)
  - weed/s3api/s3tables/handler.go:190-205 — getAccountID takes the principal from JWT/STS claims 'sub'/'preferred_username' before Account.Id, with no admin-action guard, so a federated identity whose claim normalizes to 'admin' is treated as admin. (reason to dismiss: Claims come from the trusted IdP; the advisory is about static account-less identities sharing the admin account.; still in latest: yes)
- Design plan from the lead: MAIN LEVER: reproduce the published fix in full. Hidden tests require closing EVERY published fix site through its real entry point, including the out-of-scope-looking site (defaults_or_merge_route at weed/s3api/s3tables/manager.go:22-26 (NewManager forces default-allow true) cons; dismissable because: Manager is documented as a helper 'for shell/admin without HTTP routing' (weed/s3api/s3tables/manager.go:16) and Iceberg is a separate REST protocol in another package, so a solver fixing the S3Tables). The tempting wrong fix that must FAIL: Tighten only ListTableBuckets' per-bucket filter (or its account gate) in the S3Tables handler, leaving getAccountID's admin-account mapping and the Iceberg Manager default-allow untouched..

INPUT-SHAPE / ROUTE VARIANTS (one security test each, through the real entry point, failing on pinned and passing on a correct fix): identity struct with Account.Id = shared 'admin' account but non-admin actions (account-less legacy or unknown-account identity); identity name only, no identity struct (Manager/Iceberg path); anonymous identity struct (Name or Account.Id = anonymous); no identity at all (zero-config); admin action markers '*', 'Admin', 's3:*', 's3tables:*'; trusted local tooling (shell) vs HTTP callers.

PRODUCER OFF THE CHECK'S PATH: state produced by a config_loader at weed/s3api/auth_credentials.go:631-637 and weed/s3api/auth_credentials.go:850-85 the check does not call; a fix only at the check misses it.

PATTERN B UNCOVERED ROUTES - confirm each with a behavioural test on the pinned copy, then add one row per route to build/audit/uncovered-routes.tsv: weed/s3api/s3tables/handler.go:229-233 (dismiss: Only reachable when the gateway already falls open on failed auth (weed/s3api/s3; latest=no); weed/s3api/s3tables/handler.go:190-205 (dismiss: Claims come from the trusted IdP; the advisory is about static account-less iden; latest=yes). Unmodified upstream code the published fix did not touch; the reference fix closes them too.

COUPLED MUST-KEEP-WORKING (one functional test per trap so an over-broad fix fails): Zero-config/anonymous access must keep default-allow, real admins (Admin/*/s3:*/s3tables:* actions) must keep the admin account, owners must still list their own buckets, and weed shell / mini bootstrap (name-only Manage (near weed/s3api/s3tables/manager.go:24-25; weed/shell/s3tables_he).

Aim for at least two levers with DIFFERENT reasons to dismiss. instruction.md stays at product level: system, one observed impact with one user-level trigger, security property as invariants covering every tested route/shape; keep legitimate use working; never name files/functions/fields/CVEs (all such identifiers go in manifest.leak_terms).
- Host notes: Language: Go. Offline after build, no external services. Security logic is testable without a live S3 server - call the permission/authorization functions directly with crafted principals/requests. Project's own tests for the area must pass at the pinned commit. Confirm each pattern-B route with a test on the pinned copy. Pin at the vulnerable commit; keep unrelated earlier fixes present.

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

## Environment (`tasks/seaweedfs-s3tables-authz/environment/Dockerfile`)
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

## Report to the solver (`tasks/seaweedfs-s3tables-authz/instruction.md`)
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

## Tests (`tasks/seaweedfs-s3tables-authz/tests/`)
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
- **Wrong-fix patches** go in `build/seaweedfs-s3tables-authz/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/seaweedfs-s3tables-authz/`:**
- `instruction.md`;
- `task.toml`, from `builder/templates/`, with `[metadata]` filled in and the network allowlist
  kept;
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/seaweedfs-s3tables-authz/manifest.json`:**
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

**Also in `build/seaweedfs-s3tables-authz/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `builder/templates/` and `harness/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I builder/gate.py seaweedfs-s3tables-authz --only static
python3 -I builder/gate.py seaweedfs-s3tables-authz --only nop
python3 -I builder/gate.py seaweedfs-s3tables-authz --only oracle
python3 -I builder/gate.py seaweedfs-s3tables-authz --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/seaweedfs-s3tables-authz/`;
  - edit only `tasks/seaweedfs-s3tables-authz/`, `build/seaweedfs-s3tables-authz/` and, for pattern B, the register;
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
