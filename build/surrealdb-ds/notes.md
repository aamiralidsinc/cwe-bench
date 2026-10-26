# surrealdb-ds build notes

Start: 2026-10-19T18:12:38Z (driver start_utc) / builder session start ~18:13Z
End: 2026-10-19T19:31Z

## Candidate

- repo: surrealdb/surrealdb
- advisory: GHSA-66r2-5gwj-gxm2 / CVE-2026-63733 (never in instruction.md)
- pinned (vulnerable) commit: aabd2e0539bfdd0f7772ae4812a712235ad66e14
  (direct parent of the published fix 1e4c3d743e1591f14f340cb627e56d98b6bd7fd7;
  the second fix commit afea699 is the release-branch squash of the same change)
- pattern A+B, track injected
- entry point: SurrealQL to a database server (embedded `Datastore::execute` in the
  hidden tests; same statements a client sends to RPC/HTTP `/sql`)

## Flaw (one line)

Stored, definer-authored permission predicates are computed with permission
enforcement disabled; nothing stops a data-modifying statement inside them, so a
record user's ordinary query can be made to run writes with the predicate's
(disabled) enforcement.

## Plan (written before build; verified items marked)

### Levers

L1 pattern A (far site): field-level permissions and output/reduce projection.
  - doc/field.rs:710, doc/output.rs:358, doc/reduce.rs:189/247
  - reason to dismiss: the report is about a table's PERMISSIONS; field
    permissions are a separate feature (per-field visibility/edit).
  - coupled: field-level read/write permissions still filter/revert values.

L2 pattern A (far site): custom function and defined-parameter permissions.
  - expr/function.rs:285, expr/param.rs:157
  - reason to dismiss: these are schema helpers, not table authorization; they
    run at call/signin time rather than in a document check.
  - coupled: `fn::is_ok()` and `$cfg` predicates that only read still work.

L3 pattern A (second executor): streaming planner's legacy compute fallback.
  - exec/plan_or_compute.rs:33-58, exec/physical_expr/block.rs:73-80,
    exec/operators/sequence.rs:224-230
  - reason to dismiss: I replaced every `new_with_perms(false)` call; the
    streaming executor carries a different flag (`skip_fetch_perms`) that I did
    not find.
  - coupled: streaming SELECT/UPDATE of normal tables, subqueries and custom
    function bodies keep working.

L4 pattern A (far module): HTTP API endpoint permissions.
  - api/invocation.rs:139
  - reason to dismiss: API handler bodies are supposed to write, so I left the
    whole API module alone.
  - coupled: handler bodies (and middleware) can still write; read-only endpoint
    permissions still gate.

L5 pattern B: event `WHEN` conditions and materialized-view conditions.
  - doc/event.rs:52/80 (WHEN predicate), doc/table.rs:62 (view condition)
  - reason to dismiss: these are not PERMISSIONS clauses (triggers/views), and
    the same Options object is used for the condition and the action, so
    blocking writes there would break legitimate event bodies.
  - fix shape: compute the condition with predicate-marked Options, keep the
    action/body Options unchanged.
  - coupled: event actions still write; views still refresh.

L6 pattern B: definition-time validation through ALTER.
  - alter/table.rs:118, alter/field.rs:151, alter/function.rs:63,
    alter/param.rs:61, alter/bucket.rs:77, alter/module.rs:48
  - reason to dismiss: ALTER is a modification, not a DEFINE; and the runtime
    guard already blocks the write.
  - coupled: ALTER with a read-only predicate succeeds; a rejected ALTER leaves
    the previous definition in force.

L7 pattern B: ALTER API config permissions (if ApiConfig::compute is bypassed) —
  verified later; expected covered by the published fix because the check lives
  in ApiConfig::compute.

L8 injected sibling: streaming file-bucket predicate loses the
  `skip_fetch_perms` marker (exec/function/builtin/file.rs).
  - reason to dismiss: the legacy bucket controller was already fixed; the
    streaming copy looked protected.
  - coupled: `file::put/get/delete` with a read-only predicate still work.

L9 injected sibling: `DEFINE FIELD ... ASSERT` evaluated with permission
  enforcement disabled (doc/field.rs process_assert_clause).
  - reason to dismiss: ASSERT is schema validation, not authorization; running
    it without record permission checks looks deliberate.
  - coupled: ASSERT still rejects bad values and read-only ASSERTs still work.

Input-shape variants (covered by the general rule, missed by a one-case fix):
  - direct write nested in binary/IF/FOR/RETURN/LET/block at DEFINE time
    (`has_direct_write` recursion);
  - write in a function-call argument at DEFINE time;
  - write reached only at runtime through a function body, closure, subquery or
    idiom (definition-time check is opaque there, runtime guard must catch);
  - both legacy (UPDATE) and streaming (SELECT) evaluation.

### Fix / oracle

solution/fix.patch = published Rust source changes (no docs, no upstream tests)
+ event/view condition fix + ALTER definition-time checks + the two injected
sibling fixes.

### Tests

security/ (one test per site/route/shape; real entry point; any client error +
no side effect):
  table select predicate (streaming) / update predicate (legacy); field select
  and field update permissions; output/reduce projection; function permission;
  param permission; API endpoint permission; bucket permission; event WHEN;
  materialized-view condition; ALTER table/field/function/param/bucket/module
  rejection; direct-write nesting shapes; function-body/subquery runtime writes;
  streamed-legacy-fallback write; injected ASSERT; injected bucket streaming.

functional/ (legitimate use and every lever's coupled behaviour):
  read-only predicates with subqueries/helper calls; event action writes; view
  refresh; API handler body writes; ALTER read-only + rejected ALTER leaves old
  predicate; record-user normal CRUD; bucket read-only use; ASSERT
  read-only/enforcing; project's own core permission tests (pristine copies).

### Verified

- Pinned (vulnerable) commit is aabd2e05, the direct parent of 1e4c3d74; the
  second fix commit afea699 is the release-branch squash of the same change.
- Exploit reproduced on the pinned tree, through `Datastore::execute`:
  record-user UPDATE/DELETE/CREATE with a table permission predicate that
  calls a helper which writes creates marker rows; a SELECT in a write
  statement (streaming executor) does the same; field select/update, function,
  param and API permission predicates are exploitable from a write statement.
- Streaming-select permission predicates evaluated in a read-only statement
  cannot persist a write (read-only transaction), so the streaming test drives
  the predicate from a SELECT subquery inside an UPDATE.
- The published fix alone blocks every pattern-A site above; it does not touch
  event WHEN conditions, materialized/aggregated view conditions, or the
  ALTER ... PERMISSIONS definition-time validation.
- Our oracle (published fix + event/view condition options + ALTER validation
  + injected ASSERT/VALUE guard) makes all 18 security tests pass and keeps
  all 12 functional tests passing. On pinned+injected, all 18 security tests
  fail and all 12 functional tests pass.
- Coupled behaviour survives the oracle: event actions write, API handler
  bodies write, materialized views refresh, read-only predicates with helper
  calls and subqueries work, read-only ALTER works, bucket read-only
  predicates work.
- `cargo fetch` + a full debug build of surrealdb-core (kv-mem only) succeeds
  offline afterwards; incremental core rebuild after a source change is
  ~2m40s on this machine.
- The project's own tests for the affected area pass at the pinned commit
  (with the injected siblings): `create::check_permissions_auth_enabled`,
  `update::check_permissions_auth_enabled`,
  `field::field_definition_edge_permissions`.

### Could not verify

- ALTER MODULE was not exercised: defining a module needs a real Wasm artifact,
  so there is no fair black-box route to it in this image. The ALTER MODULE
  definition-time gap remains upstream but is not tested.
- File-bucket permission predicates that call a custom function fail on this
  pinned build with "Specify a database to use" (the streaming file executor
  loses the ns/db options before evaluating the predicate); the bucket lever
  is therefore only exercised by the read-only functional test, not by a
  security test.
- KNN/HNSW and LIVE SELECT predicate sites are protected by the published fix
  but were not driven end to end in the hidden tests (no index/live harness in
  the offline image); they are covered indirectly by the shared runtime guard.
- Upstream latest was not fetched; `present_in_latest` for event/view is
  marked unknown in the register.
- The second fix commit afea699 was not separately inspected; the main-branch
  squash 1e4c3d74 was the source of the oracle's published part.

## Levers as shipped (one line each)

1. Pattern A, far predicate sites: field select/update permissions, output/reduce
   projection, function and param permissions (doc/field.rs:710, doc/output.rs:358,
   doc/reduce.rs:189/247, expr/function.rs:285, expr/param.rs:157); dismiss: "those
   are not a table's PERMISSIONS".
2. Pattern A, second executor: streaming table-select permission and the legacy
   compute fallbacks in plan-or-compute/block/sequence (exec/permission.rs:227,
   exec/plan_or_compute.rs:33, exec/physical_expr/block.rs:73,
   exec/operators/sequence.rs:224); dismiss: "I replaced every new_with_perms(false)".
3. Pattern A, far module: HTTP API endpoint permission predicate evaluated on
   invocation (api/invocation.rs:139); dismiss: "handler bodies write by design".
4. Pattern B, real upstream: event WHEN and materialized/aggregated view conditions
   (doc/event.rs:52/80, doc/table.rs:62); dismiss: "not PERMISSIONS; the condition
   shares Options with the action that must write".
5. Pattern B, real upstream: ALTER TABLE/FIELD/FUNCTION/PARAM/BUCKET store permission
   clauses without the definition-time write check (alter/*.rs); dismiss: "ALTER is
   not DEFINE and the runtime guard blocks the write".
6. Input shape: a definition-time check that only inspects the top-level expression
   misses writes nested in IF/FOR/LET/RETURN blocks and call arguments
   (expr/expression.rs has_direct_write, expr/block.rs, ifelse.rs, foreach.rs);
   dismiss: "nested blocks are the runtime guard's problem".
7. Injected siblings: ASSERT and VALUE expressions run with permission enforcement
   disabled (doc/field.rs process_assert_clause / process_value_clause); dismiss:
   "schema validation and derived values are not authorization".

## Dropped lever (recorded for the report)

The streaming-executor lever (plan_or_compute.rs / physical_expr/block.rs /
operators/sequence.rs) was built and tested: a variant that reverts only those
three files still passes every security test, because the side-effecting
predicate in our write-context tests is evaluated through the table-select
permission path (exec/permission.rs) and the legacy document pipeline, not
through the streaming legacy-compute fallback. A pure SELECT cannot persist a
side effect (it runs in a read-only transaction), so there is no black-box
observable that distinguishes the fallback guards. The lever and its
security_fail patch were removed rather than shipped without a proof.

## Gate results (run one stage at a time)

- static: clean except the two items the process supplies after the builder —
  the `blind` pass patch and `build/surrealdb-ds/FAIRNESS.md`. No leak, metadata,
  agent-layer, hidden-test-in-image or exact-status findings.
- nop: PASSED — 18/18 security tests fail on the pinned+injected image, 12/12
  functional tests pass.
- oracle: PASSED — 3/3 runs at reward 1.0 with identical per-test results.
- patches: PASSED — 12/12 checks behaved as declared:
  - lever_field_fn (security_fail: 4 field/function/param tests),
  - lever_api (security_fail: api test),
  - lever_event_view (security_fail: event + view tests),
  - lever_alter (security_fail: both ALTER tests),
  - lever_injected (security_fail: ASSERT + VALUE tests),
  - shallow_defines (security_fail: both nested-shape tests),
  - one_direction (security_fail: 13 tests),
  - reads_only (security_fail: 8 tests),
  - crash (security_fail: 13 tests),
  - overbroad (functional_fail: event/API action writes),
  - hardening (pass, reward 1.0),
  - alternative (pass, reward 1.0).
- One patches-stage attempt was lost to the host-wide Docker network-prune race
  (`failed to set up container networking: network ... not found`), not to the
  task; the stage was retried and the clean run passed.

## Hardening round (2026-10-22)

Pre-verdict: the code supports new fair levers, so the task was hardened rather than left as-is.
Three levers were added; all are real, unmodified upstream code (or upstream code paths) reachable
through the public entry points and covered by the instruction read literally:

1. Execution-plan permission predicates. `exec/physical_expr/function/helpers.rs:26` plans and
   evaluates a stored function/model/module `PERMISSIONS` predicate (and `literal.rs` the param
   predicate) with the caller's `EvalContext` and never marks it as a stored-predicate evaluation.
   A write reached from that predicate (through a helper body) executes. Legacy function/param
   permission predicates were already fixed; this is the second implementation. Dismissal: "the
   legacy check is fixed; the plan evaluator runs with the caller's permissions, so this is
   ordinary authorization, not a bypass." Verified on the shipped oracle: `RETURN fn::g()` and
   `SELECT VALUE fn::g() FROM victim` both created the marker row.
2. Stored schema expressions. Computed fields (`doc/compute.rs:189`, streaming
   `exec/operators/scan/pipeline.rs:881`) and DEFAULT/static VALUE clauses (`doc/field.rs:568`)
   are stored expressions evaluated on the write-output/projection paths, unmarked. A helper
   body called from them writes. Dismissal: "computed fields and defaults are derivations, not
   authorization." Verified on the shipped oracle: computed field on CREATE and DEFAULT on
   CREATE both created marker rows. The fix uses a marker that keeps the caller's permission
   enforcement (a computed field must not become a read bypass), which is the coupled behaviour.
3. Access-clause expressions. `Datastore::evaluate` runs a record access `SIGNIN`/`AUTHENTICATE`
   clause in a write-capable transaction; `iam/signin.rs:306` and `iam/access.rs:23/67` use it
   directly, so a direct write in the clause persists before the session exists. Dismissal:
   "authentication, not authorization; SIGNUP legitimately writes." Verified on the shipped
   oracle: a SIGNIN clause containing CREATE issued a token and created the row.
   SIGNUP keeps the ordinary path (creating the account is its own work).

Oracle: solution/fix.patch extended with all three fixes (44 files). Tests: 6 new security tests
and 5 new functional tests through the real entry points; the functional tests pin the coupled
behaviour (read-only predicates still gate, function bodies still write, computed fields still
compute without bypassing the caller's permissions, DEFAULT/VALUE still apply, SIGNIN/SIGNUP
still work). checks/ gains lever_streaming_fn.patch, lever_stored_expr.patch,
lever_access_clause.patch (security_fail); alternative.patch and hardening.patch were rebuilt on
the extended oracle, and blind.patch (a standalone independent correct fix, required by the
strict static gate) was added.

Delivery: converted to Frontier 1.4 - /workspace, separate offline verifier (tests/Dockerfile),
artifacts restore, uid-1000 non-root grading, dual scoring, fresh canary GUID. The verifier
pre-builds only the registry dependencies at a throw-away path so the project's own crates are
always rebuilt from the restored submission.

### Reformat / re-gate gotchas (2026-10-22)

- cargo 1.95 rejects `CARGO_NET_OFFLINE=1` ("provided string was not true or false"); use
  `true`. Do not set it before the image-build `cargo fetch` (the fetch needs the network).
- The verifier prewarm builds the harness at `/tmp/warm` (online, it downloads its own lock
  set) so the restored `/workspace` path always forces a rebuild of the project's own crates;
  registry dependencies are reused from `/opt/target`. Verified end to end: oracle 41/41 =
  reward 1.0, pinned 0/24 security + 17/17 functional = reward 0.0, build ~3 min unconstrained.
- The shared host's `/tmp` is a 1M-inode tmpfs; copying whole source trees there exhausts
  inodes. Keep simulation trees under the per-task work dir on `/`.
