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

Project root: `/home/mara/cwe-bench`. Task: `surrealdb-ds`. Pattern: `A+B`. Track: `injected`.

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
- Advisory: ["GHSA-66R2-5GWJ-GXM2", "CVE-2026-63733"]; surrealdb/surrealdb; authorization: side effects inside definer-authored permission predicates evaluated with enforcement disabled (CWE-863)
- Pinned (vulnerable) commit: unknown (parent_commit null in candidate; parent of 1e4c3d743e1591f14f340cb627e56d98b6bd7fd7). Published fix: 1e4c3d743e1591f14f340cb627e56d98b6bd7fd7, afea699dfb3c8f274ab36861f8a95f5e98d82f1b.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "screener_version": "screener-v2",
 "lessons_version": "lessons-v1",
 "model": "claude-opus-5-5",
 "entry_id": "20603",
 "advisory_ids": [
  "GHSA-66R2-5GWJ-GXM2",
  "CVE-2026-63733"
 ],
 "repo": "surrealdb/surrealdb",
 "pinned_commit": "unknown (parent_commit null in candidate; parent of 1e4c3d743e1591f14f340cb627e56d98b6bd7fd7)",
 "fix_commits": [
  "1e4c3d743e1591f14f340cb627e56d98b6bd7fd7",
  "afea699dfb3c8f274ab36861f8a95f5e98d82f1b"
 ],
 "trust_decision": {
  "summary": "A stored PERMISSIONS WHERE predicate (definer-authored) is evaluated with permission enforcement disabled (new_with_perms(false) / skip_fetch_perms); whether that evaluation may run data-modifying statements is decided nowhere at the pinned commit. The fix adds a runtime guard in Expr::compute keyed on Options::permission_predicate plus definition-time rejection (has_direct_write) in DEFINE statements.",
  "evidence": [
   "surrealdb/core/src/doc/check.rs:459-461",
   "surrealdb/core/src/expr/expression.rs:366",
   "surrealdb/core/src/exec/permission.rs:91-99",
   "SECURITY_GUIDE.md:156-157",
   "fix.diff:664-685",
   "fix.diff:257-263"
  ]
 },
 "landing_point": {
  "where": "surrealdb/core/src/doc/check.rs:461",
  "why": "Summary says 'table permissions'; this is the legacy table-permission check that computes the Specific predicate with new_with_perms(false) for SELECT/UPDATE/DELETE on records."
 },
 "fix_sites": [
  {
   "where": "surrealdb/core/src/doc/check.rs:461",
   "entry_point": "SurrealQL SELECT/CREATE/UPDATE/UPSERT/DELETE/RELATE on a table with PERMISSIONS (RPC/HTTP /sql)",
   "module_kind": "legacy document pipeline (table permission check)"
  },
  {
   "where": "surrealdb/core/src/doc/field.rs:710",
   "entry_point": "CREATE/UPDATE writing a field with DEFINE FIELD ... PERMISSIONS FOR create/update",
   "module_kind": "legacy document pipeline (field write permission)"
  },
  {
   "where": "surrealdb/core/src/doc/output.rs:358",
   "entry_point": "query output of records with field SELECT permissions",
   "module_kind": "legacy document pipeline (output projection)"
  },
  {
   "where": "surrealdb/core/src/doc/reduce.rs:189",
   "entry_point": "field select permission reduction on returned/compared documents",
   "module_kind": "legacy document pipeline (reduce)"
  },
  {
   "where": "surrealdb/core/src/doc/reduce.rs:247",
   "entry_point": "field select permission reduction (second loop)",
   "module_kind": "legacy document pipeline (reduce)"
  },
  {
   "where": "surrealdb/core/src/doc/lives.rs:577",
   "entry_point": "LIVE SELECT notifications to record users",
   "module_kind": "live-query notification path"
  },
  {
   "where": "surrealdb/core/src/expr/function.rs:285",
   "entry_point": "calling fn::name() with DEFINE FUNCTION ... PERMISSIONS WHERE",
   "module_kind": "expression evaluator (custom function permission)"
  },
  {
   "where": "surrealdb/core/src/expr/model.rs:91",
   "entry_point": "calling ml::model with PERMISSIONS WHERE",
   "module_kind": "expression evaluator (ML model permission)"
  },
  {
   "where": "surrealdb/core/src/expr/param.rs:157",
   "entry_point": "reading $param with DEFINE PARAM ... PERMISSIONS WHERE",
   "module_kind": "expression evaluator (param permission)"
  },
  {
   "where": "surrealdb/core/src/api/invocation.rs:139",
   "entry_point": "HTTP request to a user-defined /api endpoint (DEFINE API / DEFINE CONFIG API PERMISSIONS)",
   "module_kind": "HTTP API invocation"
  },
  {
   "where": "surrealdb/core/src/buc/controller.rs:291",
   "entry_point": "file:: functions on a bucket with PERMISSIONS WHERE (legacy)",
   "module_kind": "file bucket controller"
  },
  {
   "where": "surrealdb/core/src/exec/permission.rs:227",
   "entry_point": "KNN (HNSW/DiskANN) SELECT with table select permission",
   "module_kind": "streaming executor (second implementation)"
  },
  {
   "where": "surrealdb/core/src/exec/operators/sequence.rs:224-230",
   "entry_point": "block/sequence inside a predicate on the streaming planner, falling back to legacy compute",
   "module_kind": "streaming executor legacy fallback"
  },
  {
   "where": "surrealdb/core/src/exec/physical_expr/block.rs:73-80",
   "entry_point": "custom function body / block evaluated in a predicate on the streaming path",
   "module_kind": "streaming executor legacy fallback"
  },
  {
   "where": "surrealdb/core/src/exec/plan_or_compute.rs:33-58",
   "entry_point": "any streaming legacy fallback (incl. graph mutate ops via mutate.rs legacy_handles)",
   "module_kind": "streaming executor legacy fallback"
  },
  {
   "where": "surrealdb/core/src/expr/expression.rs:366",
   "entry_point": "every Expr::compute (central runtime guard)",
   "module_kind": "expression evaluator core"
  },
  {
   "where": "surrealdb/core/src/dbs/options.rs:33",
   "entry_point": "Options struct (new permission_predicate flag + constructor)",
   "module_kind": "execution options"
  },
  {
   "where": "surrealdb/core/src/expr/statements/define/table.rs:87",
   "entry_point": "DEFINE TABLE ... PERMISSIONS",
   "module_kind": "DDL definition-time validation"
  },
  {
   "where": "surrealdb/core/src/expr/statements/define/field.rs:163",
   "entry_point": "DEFINE FIELD ... PERMISSIONS",
   "module_kind": "DDL definition-time validation"
  },
  {
   "where": "surrealdb/core/src/expr/statements/define/function.rs:44",
   "entry_point": "DEFINE FUNCTION ... PERMISSIONS",
   "module_kind": "DDL definition-time validation"
  },
  {
   "where": "surrealdb/core/src/expr/statements/define/param.rs:36",
   "entry_point": "DEFINE PARAM ... PERMISSIONS",
   "module_kind": "DDL definition-time validation"
  },
  {
   "where": "surrealdb/core/src/expr/statements/define/model.rs:38",
   "entry_point": "DEFINE MODEL ... PERMISSIONS",
   "module_kind": "DDL definition-time validation"
  },
  {
   "where": "surrealdb/core/src/expr/statements/define/module.rs:42",
   "entry_point": "DEFINE MODULE ... PERMISSIONS",
   "module_kind": "DDL definition-time validation"
  },
  {
   "where": "surrealdb/core/src/expr/statements/define/bucket.rs:50",
   "entry_point": "DEFINE BUCKET ... PERMISSIONS",
   "module_kind": "DDL definition-time validation"
  },
  {
   "where": "fix.diff:757-768",
   "entry_point": "DEFINE CONFIG API ... PERMISSIONS",
   "module_kind": "DDL definition-time validation"
  },
  {
   "where": "fix.diff:191-215",
   "entry_point": "Permission/Permissions::has_direct_write helpers (catalog)",
   "module_kind": "catalog schema"
  },
  {
   "where": "fix.diff:599-655",
   "entry_point": "Expr/Block/IfElse/Foreach::has_direct_write AST walk",
   "module_kind": "expression AST"
  }
 ],
 "O1_entry_points": 8,
 "O2_out_of_scope_site": {
  "kind": "second_implementation",
  "where": "surrealdb/core/src/exec/plan_or_compute.rs:33-58 (streaming executor legacy fallback; also exec/physical_expr/block.rs:73 and exec/operators/sequence.rs:224) \u2014 predicate runs on the new planner path, where the guard depends on skip_fetch_perms rather than Options"
 },
 "O3_reason_to_dismiss": "ALTER ... PERMISSIONS routes: 'the runtime guard already blocks writes, so the definition-time check is only defence-in-depth and ALTER is a modification, not a DEFINE'; streaming function/param predicates: 'they run with the caller's permissions still enabled, so there is no permission bypass'.",
 "O4_distance": {
  "files": 24,
  "packages": 1,
  "repo_mb": null
 },
 "O5_coupled_behaviour": {
  "what": "Events and foreign-table views also run with new_with_perms(false) and must still write; HTTP API handler bodies run with perms disabled and may write; read-only subqueries and fn::helper() calls in predicates must keep working. An over-broad fix keyed on perms==false (or rejecting any function call / subquery at DEFINE) breaks these.",
  "where": "surrealdb/core/src/doc/event.rs:52; surrealdb/core/src/doc/event.rs:80; surrealdb/core/src/doc/table.rs:62; surrealdb/core/src/api/invocation.rs:182-183; fix.diff:145-152"
 },
 "O6_input_shapes": [
  "direct write statement inside predicate (CREATE/UPDATE/UPSERT/DELETE/RELATE/INSERT)",
  "DDL inside predicate (DEFINE/REMOVE/REBUILD/ALTER)",
  "write nested in binary/prefix/postfix/throw, RETURN, LET, block, IF/ELSE, FOR",
  "write in function-call arguments",
  "write inside a custom function body called from the predicate (runtime only)",
  "write inside subquery/idiom/closure (runtime only)",
  "legacy compute path vs streaming planner path"
 ],
 "O7_producer": {
  "kind": "schema",
  "where": "surrealdb/core/src/expr/statements/alter/table.rs:118-120 (ALTER writes the stored catalog permission without the has_direct_write check that DEFINE gained)",
  "check_calls_producer": false
 },
 "O8_uncovered_routes": [
  {
   "route": "ALTER TABLE ... PERMISSIONS stores a predicate with no definition-time write check",
   "where": "surrealdb/core/src/expr/statements/alter/table.rs:118-120",
   "reason_to_dismiss": "runtime guard already blocks; ALTER is not DEFINE",
   "distance": "different directory (statements/alter vs statements/define), same crate",
   "present_in_latest": "yes",
   "latest_where": "latest/surrealdb/core/src/expr/statements/alter/table.rs:119"
  },
  {
   "route": "ALTER FIELD ... PERMISSIONS stores select/create/update predicates unchecked",
   "where": "surrealdb/core/src/expr/statements/alter/field.rs:151-154",
   "reason_to_dismiss": "runtime guard already blocks; ALTER is not DEFINE",
   "distance": "statements/alter, same crate",
   "present_in_latest": "yes",
   "latest_where": "latest/surrealdb/core/src/expr/statements/alter/field.rs:147"
  },
  {
   "route": "ALTER FUNCTION ... PERMISSIONS stored unchecked",
   "where": "surrealdb/core/src/expr/statements/alter/function.rs:63-64",
   "reason_to_dismiss": "same as above",
   "distance": "statements/alter, same crate",
   "present_in_latest": "yes",
   "latest_where": "latest/surrealdb/core/src/expr/statements/alter/function.rs:64"
  },
  {
   "route": "ALTER PARAM ... PERMISSIONS stored unchecked",
   "where": "surrealdb/core/src/expr/statements/alter/param.rs:61-62",
   "reason_to_dismiss": "same as above",
   "distance": "statements/alter, same crate",
   "present_in_latest": "yes",
   "latest_where": "latest/surrealdb/core/src/expr/statements/alter/param.rs:62"
  },
  {
   "route": "ALTER BUCKET ... PERMISSIONS stored unchecked",
   "where": "surrealdb/core/src/expr/statements/alter/bucket.rs:77-78",
   "reason_to_dismiss": "same as above",
   "distance": "statements/alter, same crate",
   "present_in_latest": "yes",
   "latest_where": "latest/surrealdb/core/src/expr/statements/alter/bucket.rs:78"
  },
  {
   "route": "ALTER MODULE ... PERMISSIONS stored unchecked",
   "where": "surrealdb/core/src/expr/statements/alter/module.rs:48-49",
   "reason_to_dismiss": "same as above",
   "distance": "statements/alter, same crate",
   "present_in_latest": "yes",
   "latest_where": "latest/surrealdb/core/src/expr/statements/alter/module.rs:49"
  },
  {
   "route": "streaming-planner function PERMISSIONS predicate evaluated without skip_fetch_perms, so writes in it are not blocked by the new guard",
   "where": "surrealdb/core/src/exec/physical_expr/function/helpers.rs:37-41",
   "reason_to_dismiss": "evaluated with caller's permissions enabled, so not a permission bypass; legacy function.rs was fixed",
   "distance": "exec/physical_expr/function vs doc/check.rs",
   "present_in_latest": "yes",
   "latest_where": "latest/surrealdb/core/src/exec/physical_expr/function/helpers.rs:41"
  },
  {
   "route": "streaming-planner param PERMISSIONS predicate evaluated without skip_fetch_perms / predicate guard",
   "where": "surrealdb/core/src/exec/physical_expr/literal.rs:79-88",
   "reason_to_dismiss": "evaluated with caller's permissions enabled; legacy param.rs was fixed",
   "distance": "exec/physical_expr vs doc/check.rs",
   "present_in_latest": "yes",
   "latest_where": "latest/surrealdb/core/src/exec/physical_expr/literal.rs:88"
  }
 ],
 "O8b_injection_room": [
  {
   "where": "surrealdb/core/src/exec/function/builtin/file.rs:113-145",
   "sibling": "streaming bucket predicate evaluated via a fresh exec ctx that omits with_skip_fetch_perms(true)",
   "why_realistic": "the streaming bucket check builds its own context and planner; helpers.rs/literal.rs already show the flag being omitted at sibling sites"
  },
  {
   "where": "surrealdb/core/src/exec/operators/scan/pipeline.rs:368-374",
   "sibling": "field-select permission evaluated in the scan pipeline with only EvalContext.skip_fetch_perms, while sequence.rs/plan_or_compute.rs fallbacks read root().skip_fetch_perms",
   "why_realistic": "two different carriers of the same flag (eval-context vs root) exist; a maintainer could easily pick the wrong one"
  },
  {
   "where": "surrealdb/core/src/expr/statements/alter/table.rs:118-120",
   "sibling": "ALTER keeps an unvalidated permissions write while DEFINE validates",
   "why_realistic": "ALTER was added separately and copies the field directly; already present upstream"
  }
 ],
 "O9_family": "authorization: side effects inside definer-authored permission predicates evaluated with enforcement disabled (CWE-863)",
 "O9_dos": false,
 "O10_build": {
  "language": "Rust",
  "toolchain": "cargo, rust 1.95 (rust-toolchain.toml:5)",
  "services": [],
  "offline_after_build": true,
  "project_tests": "language-tests/ .surql reproductions (e.g. language-tests/tests/reproductions/perm_predicate_subquery.surql, skip_fetch_perms_subquery_dereference.surql) run by the language-tests crate (language-tests/Cargo.toml); in-memory kv engine"
 },
 "O11_fix_minutes": 80,
 "O12_red_flags": [
  "protection_documented_without_exceptions"
 ],
 "O13_recall_risk": "low",
 "pattern_fit": "A+B",
 "j": {
  "j_multi_site": 1,
  "j_sites_touched": "SECURITY_GUIDE.md (doc); surrealdb/core/src/{api/invocation.rs, buc/controller.rs, catalog/schema/mod.rs, dbs/options.rs, doc/check.rs, doc/field.rs, doc/lives.rs, doc/output.rs, doc/reduce.rs, err/mod.rs, exec/operators/sequence.rs, exec/permission.rs, exec/physical_expr/block.rs, exec/plan_or_compute.rs, expr/block.rs, expr/expression.rs, expr/function.rs, expr/model.rs, expr/param.rs, expr/statements/define/{bucket,config/api,field,function,model,module,param,table}.rs, expr/statements/foreach.rs, expr/statements/ifelse.rs}",
  "j_sibling_sites": "yes",
  "j_cause_other_layer": 1,
  "j_defence_ineffective": 0,
  "j_overbroad_breaks_legit": 1,
  "j_tempting_wrong_fix": "Reject write statements in DEFINE TABLE PERMISSIONS (or swap new_with_perms(false) in doc/check.rs only), missing function-body writes, the streaming executor fallbacks and the other predicate sites."
 },
 "out_of_scope_notes": [
  "Streaming function/param permission predicates (exec/physical_expr/function/helpers.rs:41, exec/physical_expr/literal.rs:88) run with caller perms, unlike the legacy perms-disabled path; this is a parity difference that may be a separate issue."
 ],
 "unverified": [
  "Pinned commit hash not given (parent_commit null); line numbers are from the provided repo tree.",
  "Repo size in MB not measured (no shell); surrealdb is large, so tiny_repo is unlikely; giant_repo not checked.",
  "Whether the scan-pipeline EvalContext.skip_fetch_perms (pipeline.rs:374) reaches root().skip_fetch_perms used by sequence.rs/plan_or_compute.rs fallbacks was not traced end to end; the fix's own test asserts the SELECT streaming path errors.",
  "Whether streaming ML-model permission checks exist separately was not checked.",
  "O1 count (8) groups entry points as: record DML/SELECT, field writes, LIVE SELECT, custom function call, param read, ML model call, HTTP /api, file buckets; KNN and DEFINE statements are counted inside these.",
  "protection_documented_without_exceptions is based on SECURITY_GUIDE.md:156-157 stating the rule for all permission expressions; it is a reviewer checklist, not user docs.",
  "Second fix commit afea699 was not separately inspected; fix.diff assumed to cover both commits.",
  "Recall risk judged from publication date (2026-09-04) only."
 ]
}
  ```
- Published fix sites:   - surrealdb/core/src/doc/check.rs:461 — entry point: SurrealQL SELECT/CREATE/UPDATE/UPSERT/DELETE/RELATE on a table with PERMISSIONS (RPC/HTTP /sql) [legacy document pipeline (table permission check)]
  - surrealdb/core/src/doc/field.rs:710 — entry point: CREATE/UPDATE writing a field with DEFINE FIELD ... PERMISSIONS FOR create/update [legacy document pipeline (field write permission)]
  - surrealdb/core/src/doc/output.rs:358 — entry point: query output of records with field SELECT permissions [legacy document pipeline (output projection)]
  - surrealdb/core/src/doc/reduce.rs:189 — entry point: field select permission reduction on returned/compared documents [legacy document pipeline (reduce)]
  - surrealdb/core/src/doc/reduce.rs:247 — entry point: field select permission reduction (second loop) [legacy document pipeline (reduce)]
  - surrealdb/core/src/doc/lives.rs:577 — entry point: LIVE SELECT notifications to record users [live-query notification path]
  - surrealdb/core/src/expr/function.rs:285 — entry point: calling fn::name() with DEFINE FUNCTION ... PERMISSIONS WHERE [expression evaluator (custom function permission)]
  - surrealdb/core/src/expr/model.rs:91 — entry point: calling ml::model with PERMISSIONS WHERE [expression evaluator (ML model permission)]
  - surrealdb/core/src/expr/param.rs:157 — entry point: reading $param with DEFINE PARAM ... PERMISSIONS WHERE [expression evaluator (param permission)]
  - surrealdb/core/src/api/invocation.rs:139 — entry point: HTTP request to a user-defined /api endpoint (DEFINE API / DEFINE CONFIG API PERMISSIONS) [HTTP API invocation]
  - surrealdb/core/src/buc/controller.rs:291 — entry point: file:: functions on a bucket with PERMISSIONS WHERE (legacy) [file bucket controller]
  - surrealdb/core/src/exec/permission.rs:227 — entry point: KNN (HNSW/DiskANN) SELECT with table select permission [streaming executor (second implementation)]
  - surrealdb/core/src/exec/operators/sequence.rs:224-230 — entry point: block/sequence inside a predicate on the streaming planner, falling back to legacy compute [streaming executor legacy fallback]
  - surrealdb/core/src/exec/physical_expr/block.rs:73-80 — entry point: custom function body / block evaluated in a predicate on the streaming path [streaming executor legacy fallback]
  - surrealdb/core/src/exec/plan_or_compute.rs:33-58 — entry point: any streaming legacy fallback (incl. graph mutate ops via mutate.rs legacy_handles) [streaming executor legacy fallback]
  - surrealdb/core/src/expr/expression.rs:366 — entry point: every Expr::compute (central runtime guard) [expression evaluator core]
  - surrealdb/core/src/dbs/options.rs:33 — entry point: Options struct (new permission_predicate flag + constructor) [execution options]
  - surrealdb/core/src/expr/statements/define/table.rs:87 — entry point: DEFINE TABLE ... PERMISSIONS [DDL definition-time validation]
  - surrealdb/core/src/expr/statements/define/field.rs:163 — entry point: DEFINE FIELD ... PERMISSIONS [DDL definition-time validation]
  - surrealdb/core/src/expr/statements/define/function.rs:44 — entry point: DEFINE FUNCTION ... PERMISSIONS [DDL definition-time validation]
  - surrealdb/core/src/expr/statements/define/param.rs:36 — entry point: DEFINE PARAM ... PERMISSIONS [DDL definition-time validation]
  - surrealdb/core/src/expr/statements/define/model.rs:38 — entry point: DEFINE MODEL ... PERMISSIONS [DDL definition-time validation]
  - surrealdb/core/src/expr/statements/define/module.rs:42 — entry point: DEFINE MODULE ... PERMISSIONS [DDL definition-time validation]
  - surrealdb/core/src/expr/statements/define/bucket.rs:50 — entry point: DEFINE BUCKET ... PERMISSIONS [DDL definition-time validation]
  - fix.diff:757-768 — entry point: DEFINE CONFIG API ... PERMISSIONS [DDL definition-time validation]
  - fix.diff:191-215 — entry point: Permission/Permissions::has_direct_write helpers (catalog) [catalog schema]
  - fix.diff:599-655 — entry point: Expr/Block/IfElse/Foreach::has_direct_write AST walk [expression AST]
- Uncovered routes to confirm (pattern B):   - surrealdb/core/src/expr/statements/alter/table.rs:118-120 — ALTER TABLE ... PERMISSIONS stores a predicate with no definition-time write check (reason to dismiss: runtime guard already blocks; ALTER is not DEFINE; still in latest: yes)
  - surrealdb/core/src/expr/statements/alter/field.rs:151-154 — ALTER FIELD ... PERMISSIONS stores select/create/update predicates unchecked (reason to dismiss: runtime guard already blocks; ALTER is not DEFINE; still in latest: yes)
  - surrealdb/core/src/expr/statements/alter/function.rs:63-64 — ALTER FUNCTION ... PERMISSIONS stored unchecked (reason to dismiss: same as above; still in latest: yes)
  - surrealdb/core/src/expr/statements/alter/param.rs:61-62 — ALTER PARAM ... PERMISSIONS stored unchecked (reason to dismiss: same as above; still in latest: yes)
  - surrealdb/core/src/expr/statements/alter/bucket.rs:77-78 — ALTER BUCKET ... PERMISSIONS stored unchecked (reason to dismiss: same as above; still in latest: yes)
  - surrealdb/core/src/expr/statements/alter/module.rs:48-49 — ALTER MODULE ... PERMISSIONS stored unchecked (reason to dismiss: same as above; still in latest: yes)
  - surrealdb/core/src/exec/physical_expr/function/helpers.rs:37-41 — streaming-planner function PERMISSIONS predicate evaluated without skip_fetch_perms, so writes in it are not blocked by the new guard (reason to dismiss: evaluated with caller's permissions enabled, so not a permission bypass; legacy function.rs was fixed; still in latest: yes)
  - surrealdb/core/src/exec/physical_expr/literal.rs:79-88 — streaming-planner param PERMISSIONS predicate evaluated without skip_fetch_perms / predicate guard (reason to dismiss: evaluated with caller's permissions enabled; legacy param.rs was fixed; still in latest: yes)
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

## Environment (`tasks/surrealdb-ds/environment/Dockerfile`)
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

## Report to the solver (`tasks/surrealdb-ds/instruction.md`)
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

## Tests (`tasks/surrealdb-ds/tests/`)
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
- **Wrong-fix patches** go in `build/surrealdb-ds/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/surrealdb-ds/`:**
- `instruction.md`;
- `task.toml`, from `builder/templates/`, with `[metadata]` filled in and the network allowlist
  kept;
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/surrealdb-ds/manifest.json`:**
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

**Also in `build/surrealdb-ds/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `builder/templates/` and `harness/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I builder/gate.py surrealdb-ds --only static
python3 -I builder/gate.py surrealdb-ds --only nop
python3 -I builder/gate.py surrealdb-ds --only oracle
python3 -I builder/gate.py surrealdb-ds --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/surrealdb-ds/`;
  - edit only `tasks/surrealdb-ds/`, `build/surrealdb-ds/` and, for pattern B, the register;
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
