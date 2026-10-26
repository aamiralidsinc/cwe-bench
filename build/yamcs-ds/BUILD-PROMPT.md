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

Project root: `/home/mara/cwe-bench`. Task: `yamcs-ds`. Pattern: `B`. Track: `injected`.

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
- Advisory: ["GHSA-FWWW-CP23-7F5G", "CVE-2026-55545"]; yamcs/yamcs; missing authorization (CWE-862) on streaming/subscription API handlers
- Pinned (vulnerable) commit: unknown (parent of 0691731846c5a0aca81b88fabbd2cd51d56fe076; parent_commit null in candidate). Published fix: 0691731846c5a0aca81b88fabbd2cd51d56fe076, 12864af555e6ca4941b01c1f1217859cc0492ce0.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "screener_version": "screener-v2",
 "lessons_version": "lessons-v1",
 "model": "claude-opus-5-5",
 "entry_id": "25692",
 "advisory_ids": [
  "GHSA-FWWW-CP23-7F5G",
  "CVE-2026-55545"
 ],
 "repo": "yamcs/yamcs",
 "pinned_commit": "unknown (parent of 0691731846c5a0aca81b88fabbd2cd51d56fe076; parent_commit null in candidate)",
 "fix_commits": [
  "0691731846c5a0aca81b88fabbd2cd51d56fe076",
  "12864af555e6ca4941b01c1f1217859cc0492ce0"
 ],
 "trust_decision": {
  "summary": "Each WebSocket subscription handler in org.yamcs.http.api must decide, from ctx.user privileges, whether the caller may receive the streamed object (packet content, MDB override, algorithm status); at the pinned commit three handlers stream without any such decision.",
  "evidence": [
   "yamcs-core/src/main/java/org/yamcs/http/api/PacketsApi.java:500-513",
   "yamcs-core/src/main/java/org/yamcs/http/api/PacketsApi.java:518-520",
   "yamcs-core/src/main/java/org/yamcs/http/api/MdbOverrideApi.java:274-306",
   "yamcs-core/src/main/java/org/yamcs/http/api/ProcessingApi.java:473-487",
   "yamcs-core/src/main/java/org/yamcs/http/Context.java:181-187"
  ]
 },
 "landing_point": {
  "where": "yamcs-core/src/main/java/org/yamcs/http/api/PacketsApi.java:493",
  "why": "Summary says 'WebSocket subscription handlers' lack checks their REST siblings enforce; subscribePackets is the most sensitive subscription and its REST siblings in the same file filter per packet with ReadPacket (PacketsApi.java:128, :233)."
 },
 "fix_sites": [
  {
   "where": "yamcs-core/src/main/java/org/yamcs/http/api/PacketsApi.java:500-513",
   "entry_point": "WebSocket call PacketsApi.SubscribePackets with 'processor' set (per-packet ReadPacket filter added, fix.diff:39-40)",
   "module_kind": "API handler (HTTP/WebSocket RPC)"
  },
  {
   "where": "yamcs-core/src/main/java/org/yamcs/http/api/PacketsApi.java:518-520",
   "entry_point": "WebSocket call PacketsApi.SubscribePackets with 'stream' set (ReadTables system privilege added, fix.diff:61-62)",
   "module_kind": "API handler, low-level raw stream branch"
  },
  {
   "where": "yamcs-core/src/main/java/org/yamcs/http/api/MdbOverrideApi.java:274-276",
   "entry_point": "WebSocket call MdbOverrideApi.SubscribeMdbChanges (GetMissionDatabase added, fix.diff:9)",
   "module_kind": "API handler (HTTP/WebSocket RPC)"
  },
  {
   "where": "yamcs-core/src/main/java/org/yamcs/http/api/ProcessingApi.java:473-478",
   "entry_point": "WebSocket call ProcessingApi.SubscribeAlgorithmStatus (ReadAlgorithm added, fix.diff:84)",
   "module_kind": "API handler (HTTP/WebSocket RPC)"
  }
 ],
 "O1_entry_points": 3,
 "O2_out_of_scope_site": {
  "kind": "lower_level_api",
  "where": "yamcs-core/src/main/java/org/yamcs/http/api/PacketsApi.java:518-520 (stream branch of subscribePackets; raw stream has no packet names, so the fix gates it with ReadTables instead of ReadPacket, fix.diff:61-62)"
 },
 "O3_reason_to_dismiss": "The REST siblings named in the report (packets, MDB) look guarded, so a solver can argue the REST MDB-override readers listMdbOverrides/getAlgorithmOverrides are 'the REST side that already enforces checks' and that the raw-stream branch is already gated by the Stream object privilege in TableApi.verifyStream.",
 "O4_distance": {
  "files": 3,
  "packages": 1,
  "repo_mb": null
 },
 "O5_coupled_behaviour": {
  "what": "subscribePackets on a processor must keep streaming packets the user holds ReadPacket for (per-packet filtering, as the REST list does); requiring ReadTables/GetMissionDatabase or rejecting the whole subscription breaks ReadPacket-only users of the live packet view. Likewise the MDB REST API admits ReadAlgorithm holders without GetMissionDatabase.",
  "where": "yamcs-core/src/main/java/org/yamcs/http/api/PacketsApi.java:233; yamcs-core/src/main/java/org/yamcs/http/api/MdbApi.java:940-943"
 },
 "O6_input_shapes": [
  "SubscribePacketsRequest with processor (per-item filter on live container results)",
  "SubscribePacketsRequest with stream (raw tuples, no packet name; system privilege gate)",
  "SubscribeMdbChangesRequest (parameter-type overrides and algorithm-text overrides on one subscription)",
  "SubscribeAlgorithmStatusRequest by algorithm name"
 ],
 "O7_producer": {
  "kind": "none",
  "where": "",
  "check_calls_producer": null
 },
 "O8_uncovered_routes": [
  {
   "route": "REST ListMdbOverrides returns every algorithm-text and parameter-type override with no privilege check",
   "where": "yamcs-core/src/main/java/org/yamcs/http/api/MdbOverrideApi.java:55-81",
   "reason_to_dismiss": "Advisory is framed as WebSocket handlers missing checks 'their REST siblings enforce', so REST MDB-override readers look out of scope",
   "distance": "same file as fix site subscribeMdbChanges",
   "present_in_latest": "no",
   "latest_where": "latest/yamcs-core/src/main/java/org/yamcs/http/api/MdbOverrideApi.java:66"
  },
  {
   "route": "REST GetAlgorithmOverrides returns an algorithm's override text with no ReadAlgorithm/GetMissionDatabase check",
   "where": "yamcs-core/src/main/java/org/yamcs/http/api/MdbOverrideApi.java:118-136",
   "reason_to_dismiss": "Same as above: a REST route, and the report says REST is the guarded side",
   "distance": "same file as fix site subscribeMdbChanges",
   "present_in_latest": "no",
   "latest_where": "latest/yamcs-core/src/main/java/org/yamcs/http/api/MdbOverrideApi.java:130"
  },
  {
   "route": "WebSocket SubscribeStream delivers raw stream tuples (incl. packet bytes on TM streams) gated only by Stream object privilege, while the fix requires ReadTables for the same data via SubscribePackets(stream)",
   "where": "yamcs-core/src/main/java/org/yamcs/http/api/TableApi.java:177-197",
   "reason_to_dismiss": "Generic table/stream API whose REST sibling getStream uses the same verifyStream gate (TableApi.java:512-528), so it already matches REST",
   "distance": "different file (TableApi) in same package",
   "present_in_latest": "yes",
   "latest_where": "latest/yamcs-core/src/main/java/org/yamcs/http/api/TableApi.java:178-180"
  },
  {
   "route": "WebSocket SubscribeTMStatistics streams per-processor TM statistics with no privilege check or per-packet filtering",
   "where": "yamcs-core/src/main/java/org/yamcs/http/api/ProcessingApi.java:445-459",
   "reason_to_dismiss": "Statistics are metadata, not packet content; a neighbouring monitoring feature",
   "distance": "same file as fix site subscribeAlgorithmStatus",
   "present_in_latest": "yes",
   "latest_where": "latest/yamcs-core/src/main/java/org/yamcs/http/api/ProcessingApi.java:445-459"
  }
 ],
 "O8b_injection_room": [
  {
   "where": "yamcs-core/src/main/java/org/yamcs/http/api/ParameterArchiveApi.java:80-125",
   "sibling": "subscribeBackfilling has no ControlArchiving check while every REST sibling in the file requires it (ParameterArchiveApi.java:57, :329, :338)",
   "why_realistic": "Already present upstream; subscription endpoints were added later than REST ones and copied without the guard line"
  },
  {
   "where": "yamcs-core/src/main/java/org/yamcs/http/api/MdbOverrideApi.java:282-294",
   "sibling": "per-object ReadParameter/ReadAlgorithm filtering of emitted overrides inside subscribeMdbChanges listeners",
   "why_realistic": "Listener lambdas are written separately from the request-time check, so a maintainer could add a system check at entry and forget per-item filtering"
  },
  {
   "where": "yamcs-core/src/main/java/org/yamcs/http/api/CommandsApi.java:491-492",
   "sibling": "a second command-history listener callback (e.g. updatedCommand) emitting without the CommandHistory object check used in addedCommand",
   "why_realistic": "Multi-callback consumer where only the first callback carries the filter"
  }
 ],
 "O9_family": "missing authorization (CWE-862) on streaming/subscription API handlers",
 "O9_dos": false,
 "O10_build": {
  "language": "Java",
  "toolchain": "Maven (multi-module; yamcs-web also needs Node/Angular unless skipped)",
  "services": [],
  "offline_after_build": true,
  "project_tests": "tests/src/test/java/org/yamcs/tests/PermissionsTest.java (integration tests with in-process Yamcs server); no unit tests for these handlers in yamcs-core/src/test/java/org/yamcs/http/api"
 },
 "O11_fix_minutes": 35,
 "O12_red_flags": [],
 "O13_recall_risk": "low",
 "pattern_fit": "B",
 "j": {
  "j_multi_site": 1,
  "j_sites_touched": "yamcs-core/src/main/java/org/yamcs/http/api/PacketsApi.java, MdbOverrideApi.java, ProcessingApi.java",
  "j_sibling_sites": "yes",
  "j_cause_other_layer": 0,
  "j_defence_ineffective": 0,
  "j_overbroad_breaks_legit": 1,
  "j_tempting_wrong_fix": "Add a single upfront ctx.checkSystemPrivilege(...) to subscribePackets (rejecting ReadPacket-only users) and stop, missing the stream branch, MDB/algorithm subscriptions and the REST override readers."
 },
 "out_of_scope_notes": [
  "Cop1Api.getStatus and subscribeStatus (Cop1Api.java:129, :142) both lack checks; consistent REST/WS, different protection."
 ],
 "unverified": [
  "Pinned commit hash not given (parent_commit null); fix.diff hunk offsets match the pinned tree.",
  "repo_mb not measured (no shell); ~7.5k files incl. yamcs-web frontend, likely well under 1.5 GB.",
  "Advisory text itself was not available locally; scope inferred from summary and fix.diff.",
  "That TM Statistics messages carry packet names (subscribeTMStatistics route) was not confirmed in the proto.",
  "Whether listMdbOverrides/getAlgorithmOverrides gaps belong to one of the 4 sibling advisories (fixed later upstream) not confirmed.",
  "Buildability not exercised; offline_after_build assumes Maven deps pre-fetched."
 ]
}
  ```
- Published fix sites:   - yamcs-core/src/main/java/org/yamcs/http/api/PacketsApi.java:500-513 — entry point: WebSocket call PacketsApi.SubscribePackets with 'processor' set (per-packet ReadPacket filter added, fix.diff:39-40) [API handler (HTTP/WebSocket RPC)]
  - yamcs-core/src/main/java/org/yamcs/http/api/PacketsApi.java:518-520 — entry point: WebSocket call PacketsApi.SubscribePackets with 'stream' set (ReadTables system privilege added, fix.diff:61-62) [API handler, low-level raw stream branch]
  - yamcs-core/src/main/java/org/yamcs/http/api/MdbOverrideApi.java:274-276 — entry point: WebSocket call MdbOverrideApi.SubscribeMdbChanges (GetMissionDatabase added, fix.diff:9) [API handler (HTTP/WebSocket RPC)]
  - yamcs-core/src/main/java/org/yamcs/http/api/ProcessingApi.java:473-478 — entry point: WebSocket call ProcessingApi.SubscribeAlgorithmStatus (ReadAlgorithm added, fix.diff:84) [API handler (HTTP/WebSocket RPC)]
- Uncovered routes to confirm (pattern B):   - yamcs-core/src/main/java/org/yamcs/http/api/MdbOverrideApi.java:55-81 — REST ListMdbOverrides returns every algorithm-text and parameter-type override with no privilege check (reason to dismiss: Advisory is framed as WebSocket handlers missing checks 'their REST siblings enforce', so REST MDB-override readers look out of scope; still in latest: no)
  - yamcs-core/src/main/java/org/yamcs/http/api/MdbOverrideApi.java:118-136 — REST GetAlgorithmOverrides returns an algorithm's override text with no ReadAlgorithm/GetMissionDatabase check (reason to dismiss: Same as above: a REST route, and the report says REST is the guarded side; still in latest: no)
  - yamcs-core/src/main/java/org/yamcs/http/api/TableApi.java:177-197 — WebSocket SubscribeStream delivers raw stream tuples (incl. packet bytes on TM streams) gated only by Stream object privilege, while the fix requires ReadTables for the same data via SubscribePackets(stream) (reason to dismiss: Generic table/stream API whose REST sibling getStream uses the same verifyStream gate (TableApi.java:512-528), so it already matches REST; still in latest: yes)
  - yamcs-core/src/main/java/org/yamcs/http/api/ProcessingApi.java:445-459 — WebSocket SubscribeTMStatistics streams per-processor TM statistics with no privilege check or per-packet filtering (reason to dismiss: Statistics are metadata, not packet content; a neighbouring monitoring feature; still in latest: yes)
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

## Environment (`tasks/yamcs-ds/environment/Dockerfile`)
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

## Report to the solver (`tasks/yamcs-ds/instruction.md`)
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

## Tests (`tasks/yamcs-ds/tests/`)
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
- **Wrong-fix patches** go in `build/yamcs-ds/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/yamcs-ds/`:**
- `instruction.md`;
- `task.toml`, from `builder/templates/`, with `[metadata]` filled in and the network allowlist
  kept;
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/yamcs-ds/manifest.json`:**
- `slug`, `candidate`;
- `pattern`: `B`;
- `builder_prompt_version`: `build-v1`;
- `"strict_gate": true`;
- `verified`: entry point, sites, routes, services, project tests run;
- `leak_terms`, `patch_checks`, `wrong_fix_catalogue`;
- `traps`: one entry per lever, with `shape`, `where` (file:line), `security_tests`,
  `coupled_functional_tests`, `security_fail_patch`, and `realistic_because` (for pattern B: "real,
  unmodified upstream code");
- `status`.

**Also in `build/yamcs-ds/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `builder/templates/` and `harness/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I builder/gate.py yamcs-ds --only static
python3 -I builder/gate.py yamcs-ds --only nop
python3 -I builder/gate.py yamcs-ds --only oracle
python3 -I builder/gate.py yamcs-ds --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/yamcs-ds/`;
  - edit only `tasks/yamcs-ds/`, `build/yamcs-ds/` and, for pattern B, the register;
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
