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

Project root: `/home/mara/cwe-bench`. Task: `stk-dagu-ghsaph8x`. Pattern: `A+B`. Track: `stacked`.

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
- Advisory: GHSA-6v48-fcq6-ff23; GHSA-ph8x-4jfv-v9v8
- Pinned (vulnerable) commit: 6c53bfdaa6beec62a3936b8c5b233efb8bd22c7b. Published fix: e2ed589105d7, 7d07fda8f9de.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "candidate_id": "h3-ghsa-ph8x-4jfv-v9v8",
 "pattern": "H3b",
 "repo": "dagu-org/dagu",
 "pinned_commit": "6c53bfdaa6beec62a3936b8c5b233efb8bd22c7b",
 "protections": [
  "P1: a DAG identifier supplied by an API client (path param fileName or body name/newFileName) must resolve only to a file inside the DAGs directory; the DAG store must not read, write, delete, rename or execute files outside it (internal/persis/filedag/store.go:493-527)",
  "P2: DAG files written by git sync must stay inside the DAGs directory even when the repo file name decodes to a traversal (internal/gitsync/service.go:1109-1117)"
 ],
 "traps": [
  {
   "id": "T1",
   "mechanism": "M3",
   "origin": "advisory_route",
   "locations": [
    "internal/persis/filedag/store.go:506",
    "internal/persis/filedag/store.go:507",
    "api/v1/api.gen.go:7463",
    "internal/service/frontend/api/v1/dags.go:204",
    "internal/service/frontend/api/v1/dags.go:185",
    "internal/service/frontend/api/v1/dags.go:307",
    "internal/service/frontend/api/v1/dags.go:579",
    "internal/service/frontend/api/v1/dags.go:668",
    "internal/service/frontend/api/v1/dags.go:970"
   ],
   "reason_to_dismiss": "the OpenAPI schema restricts DAGFileName to ^[a-zA-Z0-9_-]+$, so the path param looks validated already; in fact the validator only runs when StrictValidation is set, and nothing ever sets it",
   "distance": {
    "files": 2,
    "packages": 2
   },
   "protection_state": "absent",
   "tier_deepseek": "easy",
   "tier_mimo": "easy",
   "type": "neither",
   "evidence": [
    "internal/persis/filedag/store.go:505-511 locateDAG passes any name containing a separator straight to findDAGFile, with no base-dir containment",
    "internal/persis/filedag/store.go:699-714 findDAGFile resolves the raw path (absolute or cwd-relative) and only requires a .yaml/.yml suffix",
    "api/v1/api.gen.go:7463 fileName is bound with ParamLocationPath (oapi runtime unescapes, so %2F becomes /)",
    "api/v1/api.yaml:5445-5450 DAGFileName pattern ^[a-zA-Z0-9_-]+$",
    "internal/service/frontend/api/v1/api.go:244-246 request validator is mounted only if Server.StrictValidation",
    "internal/cmn/config/config.go:128 StrictValidation field; no loader assigns it (grep finds only api.go:244 and config.go:128)",
    "internal/persis/filedag/store.go:160-170 GetSpec returns the content of the located file",
    "internal/service/frontend/api/v1/dags.go:177-187 DeleteDAG -> Delete -> os.Remove (store.go:225-232)",
    "internal/service/frontend/api/v1/dags.go:281,307 RenameDAG source resolved via locateDAG (store.go:481)",
    "internal/service/frontend/api/v1/dags.go:572-579 ExecuteDAG needs only run permission and loads the located file as a DAG"
   ]
  },
  {
   "id": "T2",
   "mechanism": "M8",
   "origin": "advisory_route",
   "locations": [
    "internal/persis/filedag/store.go:513-519"
   ],
   "reason_to_dismiss": "once the separator early-return at :506 is removed, the search-path loop looks like a safe join under baseDir",
   "distance": {
    "files": 1,
    "packages": 1
   },
   "protection_state": "absent",
   "tier_deepseek": "medium",
   "tier_mimo": "medium",
   "type": "neither",
   "evidence": [
    "internal/persis/filedag/store.go:518 filepath.Join(absDir, nameOrPath) lexically resolves ../ out of absDir; the result is not checked for being under absDir",
    "internal/persis/filedag/store.go:87 search paths also include \".\" (process cwd), so containment must hold for every search dir"
   ]
  },
  {
   "id": "T3",
   "mechanism": "M11",
   "origin": "injection_room",
   "locations": [
    "internal/runtime/agent/dbclient.go:26",
    "internal/cmd/helper.go:110",
    "internal/cmd/migrator.go:428",
    "internal/runtime/executor/dag_runner.go:98"
   ],
   "reason_to_dismiss": "",
   "distance": {
    "files": 4,
    "packages": 3
   },
   "protection_state": "weak",
   "tier_deepseek": "medium",
   "tier_mimo": "hard",
   "type": "mimo",
   "evidence": [
    "internal/cmd/helper.go:97-115 the CLI passes .yaml file paths to GetMetadata, which reaches locateDAG",
    "internal/cmd/migrator.go:428 the migrator passes file paths to GetDetails",
    "internal/runtime/agent/dbclient.go:25-27 sub-DAG lookup (dag_runner.go:98) calls GetDetails with the child name from the spec",
    "internal/persis/filedag/store.go:504 locateDAG is documented as 'by its name or path'; rejecting every separator in the store breaks these trusted callers"
   ]
  },
  {
   "id": "T4",
   "mechanism": "M5",
   "origin": "advisory_route",
   "locations": [
    "internal/service/frontend/api/v1/dags.go:126",
    "internal/service/frontend/api/v1/dags.go:149-155",
    "internal/persis/filedag/store.go:213",
    "internal/persis/filedag/store.go:494-499"
   ],
   "reason_to_dismiss": "CreateNewDAG already validates the name through spec.LoadYAML(WithName), which calls ValidateDAGName; but that only happens when a spec is sent, and the default-template branch skips it",
   "distance": {
    "files": 4,
    "packages": 3
   },
   "protection_state": "bypassed",
   "tier_deepseek": "hard",
   "tier_mimo": "medium",
   "type": "deepseek",
   "evidence": [
    "internal/service/frontend/api/v1/dags.go:126-131 name validated only inside the non-empty-spec branch",
    "internal/core/spec/dag.go:580-583 buildName takes opts.Name; dag.go:544-547 ValidateDAGName applied to it",
    "internal/service/frontend/api/v1/dags.go:149-153 empty/whitespace spec falls to the default template with no name check",
    "internal/service/frontend/api/v1/dags.go:155 Create(ctx, request.Body.Name, ...) with the raw name",
    "internal/persis/filedag/store.go:494-499 a name containing a separator becomes filepath.Abs(name) and is written at store.go:217"
   ]
  },
  {
   "id": "T5",
   "mechanism": "M8",
   "origin": "uncovered_upstream",
   "locations": [
    "internal/core/validator.go:17",
    "internal/persis/filedag/store.go:500-501",
    "internal/service/frontend/api/v1/dags.go:273",
    "internal/service/frontend/api/v1/dags.go:307",
    "internal/persis/filedag/store.go:485"
   ],
   "reason_to_dismiss": "ValidateDAGName's regex has no slash, so the name looks like a plain basename; the dot-only names '.' and '..' still pass, and path.Join resolves them to baseDir or its parent",
   "distance": {
    "files": 3,
    "packages": 3
   },
   "protection_state": "weak",
   "tier_deepseek": "hard",
   "tier_mimo": "hard",
   "type": "mimo",
   "evidence": [
    "internal/core/validator.go:17 dagNameRegex ^[a-zA-Z0-9_.-]+$ accepts '.' and '..'",
    "internal/persis/filedag/store.go:500 path.Join(baseDir, \"..\") yields the parent dir; EnsureYAMLExtension (internal/cmn/fileutil/fileutil.go:135-147) appends .yaml, so the target is <parent>/<dagsdir-name>.yaml or <parent>.yaml, outside baseDir",
    "internal/service/frontend/api/v1/dags.go:273-279 RenameDAG relies solely on ValidateDAGName for NewFileName, then store.go:485-489 os.Rename to that path",
    "internal/core/validator.go:17 '.' is allowed on purpose so dotted names keep working; removing '.' from the regex over-hardens"
   ]
  },
  {
   "id": "T6",
   "mechanism": "M2",
   "origin": "uncovered_upstream",
   "locations": [
    "internal/gitsync/service.go:224",
    "internal/gitsync/service.go:231",
    "internal/gitsync/service.go:1109-1117",
    "internal/gitsync/service.go:249"
   ],
   "reason_to_dismiss": "the path comes from the configured internal repo (comment at service.go:234/241), and a safe variant safeDAGIDToFilePath already exists, so pull looks covered",
   "distance": {
    "files": 1,
    "packages": 1
   },
   "protection_state": "bypassed",
   "tier_deepseek": "xhard",
   "tier_mimo": "hard",
   "type": "deepseek",
   "evidence": [
    "internal/gitsync/service.go:1022-1032 filePathToDAGID keeps the repo file name verbatim",
    "internal/gitsync/service.go:1109-1116 dagIDToFilePath PathUnescapes the id and joins it with no containment check, so a repo file named with %2E%2E%2F decodes to ../",
    "internal/gitsync/service.go:246-249 pull writes repo content to that path",
    "internal/gitsync/service.go:1143-1163,1206-1213 normalizeDAGID/safeDAGIDToFilePath exist but are not used on the pull path"
   ]
  }
 ],
 "independent_groups": [
  [
   "T1",
   "T2",
   "T3"
  ],
  [
   "T4"
  ],
  [
   "T5"
  ],
  [
   "T6"
  ]
 ],
 "history": {
  "a_fix_leaves_b_open": true,
  "b_in_code_a_wrote": false,
  "masking": [],
  "dependency_bump_fix": false,
  "in_repo_fix_possible": true
 },
 "conflicts": [
  {
   "a": "T1",
   "b": "T3",
   "what": "the natural fix for T1, rejecting any separator or absolute path inside locateDAG, breaks CLI file-path lookups (internal/cmd/helper.go:110, internal/cmd/migrator.go:428) and sub-DAG resolution (internal/runtime/agent/dbclient.go:26). The fix must sit at the API boundary, or use containment that the trusted callers bypass."
  },
  {
   "a": "T5",
   "b": "T5",
   "what": "closing dot-only names by dropping '.' from dagNameRegex (internal/core/validator.go:17) breaks legitimate dotted DAG names; the correct fix rejects exactly '.'/'..' or adds containment in generateFilePath"
  }
 ],
 "fairness_risks": [
  "Trusted callers (CLI, sub-DAG run, migrator) must still resolve DAG files by path through the same store methods (internal/cmd/helper.go:110, internal/runtime/agent/dbclient.go:26); hidden tests must not require the store itself to refuse paths",
  "DAG names containing dots are accepted by ValidateDAGName (internal/core/validator.go:17); a test must not demand refusing all dots",
  "The empty-spec CreateNewDAG default template (internal/service/frontend/api/v1/dags.go:149-153) must keep working for valid names",
  "Nested git-sync IDs such as memory/... and skills/... (internal/gitsync/service.go:227) must keep syncing; a T6 fix must not reject every slash"
 ],
 "effort_minutes": 45,
 "usable": true,
 "design": {
  "traps": [
   "T1",
   "T4",
   "T5",
   "T6"
  ],
  "why": "Four independent fix sites, each with a different reason to dismiss. T1 (the B advisory route: the API fileName reaches locateDAG; the OpenAPI pattern looks protective but is never enforced) is coupled with T3, because the store must keep accepting paths for trusted callers. T4 (the A route: the default-spec branch of CreateNewDAG skips name validation) and T6 (git-sync decode-then-join; dismissable as internal repo input that already has a safe twin) are the deepseek-type traps. T5 (dot-only names pass the regex, and the fix must keep dotted names) is the mimo-type how/coupled trap. This beats a design built on T1+T2: those share one function and close together. It also beats a design that drops T6, which would leave no xhard absent-with-dismissal trap."
 },
 "unverified": [
  "The contents of the A fix (e2ed589105d7) and the B fix (7d07fda8f9de) are not in the pinned tree. a_fix_leaves_b_open=true and b_in_code_a_wrote=false rest on the advisory summary and szz_status H3b-elsewhere, not on reading those diffs.",
  "Whether the pinned commit predates A's fix could not be confirmed with git (no shell); the code shows A's route (T4) still open.",
  "That chi routes on RawPath, so an encoded %2F stays inside one fileName segment and is decoded only by oapi BindStyledParameter, was inferred from library behaviour, not from pinned code. The SSE routes (internal/service/frontend/sse/handler.go:45,52) use chi.URLParam without decoding and were judged not to be a trap on that basis.",
  "T6 exploitability assumes git permits a tracked file name containing literal %2E%2E%2F and that ListFiles (internal/gitsync/service.go:213) returns it unchanged.",
  "That dotted DAG names are used by existing tests or users is not confirmed by a test in the tree; only the regex allows them.",
  "The agent chat DAGContexts.dag_file (internal/agent/types.go:245, internal/agent/api.go:145) also reaches locateDAG. It is left out as a trap because it only exposes metadata/location to an agent that already has tool access; this judgement is not verified."
 ]
}
  ```
- Published fix sites:   - internal/persis/filedag/store.go:506 — T1 M3 (reason to dismiss: the OpenAPI schema restricts DAGFileName to ^[a-zA-Z0-9_-]+$, so the path param looks validated already; in fact the validator only runs when StrictValidation is set, and nothing ever sets it)
  - internal/persis/filedag/store.go:507 — T1 M3 (reason to dismiss: the OpenAPI schema restricts DAGFileName to ^[a-zA-Z0-9_-]+$, so the path param looks validated already; in fact the validator only runs when StrictValidation is set, and nothing ever sets it)
  - api/v1/api.gen.go:7463 — T1 M3 (reason to dismiss: the OpenAPI schema restricts DAGFileName to ^[a-zA-Z0-9_-]+$, so the path param looks validated already; in fact the validator only runs when StrictValidation is set, and nothing ever sets it)
  - internal/service/frontend/api/v1/dags.go:204 — T1 M3 (reason to dismiss: the OpenAPI schema restricts DAGFileName to ^[a-zA-Z0-9_-]+$, so the path param looks validated already; in fact the validator only runs when StrictValidation is set, and nothing ever sets it)
  - internal/service/frontend/api/v1/dags.go:185 — T1 M3 (reason to dismiss: the OpenAPI schema restricts DAGFileName to ^[a-zA-Z0-9_-]+$, so the path param looks validated already; in fact the validator only runs when StrictValidation is set, and nothing ever sets it)
  - internal/service/frontend/api/v1/dags.go:307 — T1 M3 (reason to dismiss: the OpenAPI schema restricts DAGFileName to ^[a-zA-Z0-9_-]+$, so the path param looks validated already; in fact the validator only runs when StrictValidation is set, and nothing ever sets it)
  - internal/service/frontend/api/v1/dags.go:579 — T1 M3 (reason to dismiss: the OpenAPI schema restricts DAGFileName to ^[a-zA-Z0-9_-]+$, so the path param looks validated already; in fact the validator only runs when StrictValidation is set, and nothing ever sets it)
  - internal/service/frontend/api/v1/dags.go:668 — T1 M3 (reason to dismiss: the OpenAPI schema restricts DAGFileName to ^[a-zA-Z0-9_-]+$, so the path param looks validated already; in fact the validator only runs when StrictValidation is set, and nothing ever sets it)
  - internal/service/frontend/api/v1/dags.go:970 — T1 M3 (reason to dismiss: the OpenAPI schema restricts DAGFileName to ^[a-zA-Z0-9_-]+$, so the path param looks validated already; in fact the validator only runs when StrictValidation is set, and nothing ever sets it)
  - internal/persis/filedag/store.go:513-519 — T2 M8 (reason to dismiss: once the separator early-return at :506 is removed, the search-path loop looks like a safe join under baseDir)
  - internal/service/frontend/api/v1/dags.go:126 — T4 M5 (reason to dismiss: CreateNewDAG already validates the name through spec.LoadYAML(WithName), which calls ValidateDAGName; but that only happens when a spec is sent, and the default-template branch skips it)
  - internal/service/frontend/api/v1/dags.go:149-155 — T4 M5 (reason to dismiss: CreateNewDAG already validates the name through spec.LoadYAML(WithName), which calls ValidateDAGName; but that only happens when a spec is sent, and the default-template branch skips it)
  - internal/persis/filedag/store.go:213 — T4 M5 (reason to dismiss: CreateNewDAG already validates the name through spec.LoadYAML(WithName), which calls ValidateDAGName; but that only happens when a spec is sent, and the default-template branch skips it)
  - internal/persis/filedag/store.go:494-499 — T4 M5 (reason to dismiss: CreateNewDAG already validates the name through spec.LoadYAML(WithName), which calls ValidateDAGName; but that only happens when a spec is sent, and the default-template branch skips it)
- Uncovered routes to confirm (pattern B):   - internal/core/validator.go:17 — T5 M8 (reason to dismiss: ValidateDAGName's regex has no slash, so the name looks like a plain basename; the dot-only names '.' and '..' still pass, and path.Join resolves them to baseDir or its parent)
  - internal/persis/filedag/store.go:500-501 — T5 M8 (reason to dismiss: ValidateDAGName's regex has no slash, so the name looks like a plain basename; the dot-only names '.' and '..' still pass, and path.Join resolves them to baseDir or its parent)
  - internal/service/frontend/api/v1/dags.go:273 — T5 M8 (reason to dismiss: ValidateDAGName's regex has no slash, so the name looks like a plain basename; the dot-only names '.' and '..' still pass, and path.Join resolves them to baseDir or its parent)
  - internal/service/frontend/api/v1/dags.go:307 — T5 M8 (reason to dismiss: ValidateDAGName's regex has no slash, so the name looks like a plain basename; the dot-only names '.' and '..' still pass, and path.Join resolves them to baseDir or its parent)
  - internal/persis/filedag/store.go:485 — T5 M8 (reason to dismiss: ValidateDAGName's regex has no slash, so the name looks like a plain basename; the dot-only names '.' and '..' still pass, and path.Join resolves them to baseDir or its parent)
  - internal/gitsync/service.go:224 — T6 M2 (reason to dismiss: the path comes from the configured internal repo (comment at service.go:234/241), and a safe variant safeDAGIDToFilePath already exists, so pull looks covered)
  - internal/gitsync/service.go:231 — T6 M2 (reason to dismiss: the path comes from the configured internal repo (comment at service.go:234/241), and a safe variant safeDAGIDToFilePath already exists, so pull looks covered)
  - internal/gitsync/service.go:1109-1117 — T6 M2 (reason to dismiss: the path comes from the configured internal repo (comment at service.go:234/241), and a safe variant safeDAGIDToFilePath already exists, so pull looks covered)
  - internal/gitsync/service.go:249 — T6 M2 (reason to dismiss: the path comes from the configured internal repo (comment at service.go:234/241), and a safe variant safeDAGIDToFilePath already exists, so pull looks covered)
- Design plan from the lead: TRACK = STACKED (H3b). Build the stacked design the reader chose: traps T1, T4, T5, T6. Why: Four independent fix sites, each with a different reason to dismiss. T1 (the B advisory route: the API fileName reaches locateDAG; the OpenAPI pattern looks protective but is never enforced) is coupled with T3, because the store must keep accepting paths for trusted callers. T4 (the A route: the default-spec branch of CreateNewDAG skips name validation) and T6 (git-sync decode-then-join; dismissable as internal repo input that already has a safe twin) are the deepseek-type traps. T5 (dot-only names pass the regex, and the fix must keep dotted names) is the mimo-type how/coupled trap. This beats a design built on T1+T2: those share one function and close together. It also beats a design that drops T6, which would leave no xhard absent-with-dismissal trap. Follow the stacked-task rules appended at the end of this prompt; they add to the rules above.
- Host notes: Reader fairness risks (resolve each in the report's contracts or the tests): Trusted callers (CLI, sub-DAG run, migrator) must still resolve DAG files by path through the same store methods (internal/cmd/helper.go:110, internal/runtime/agent/dbclient.go:26); hidden tests must not require the store itself to refuse paths | DAG names containing dots are accepted by ValidateDAGName (internal/core/validator.go:17); a test must not demand refusing all dots | The empty-spec CreateNewDAG default template (internal/service/frontend/api/v1/dags.go:149-153) must keep working for valid names | Nested git-sync IDs such as memory/... and skills/... (internal/gitsync/service.go:227) must keep syncing; a T6 fix must not reject every slash. Conflicts the reader found: the natural fix for T1, rejecting any separator or absolute path inside locateDAG, breaks CLI file-path lookups (internal/cmd/helper.go:110, internal/cmd/migrator.go:428) and sub-DAG resolution (internal/runtime/agent/dbclient.go:26). The fix must sit at the API boundary, or use containment that the trusted callers bypass. | closing dot-only names by dropping '.' from dagNameRegex (internal/core/validator.go:17) breaks legitimate dotted DAG names; the correct fix rejects exactly '.'/'..' or adds containment in generateFilePath

## Design: where difficulty comes from
Models find the code the report leads to and diagnose it correctly. They fail on scope. Build these
in, in order of evidence:
1. **Pattern A: the published fix's far sites.**
   - The report leads to one site. The tests cover every entry point the published fix protects,
     including one in a module that looks out of scope: a second implementation, a lower-level
     public API, a wrapper, a save/reload path, or a defaults or merge route.
   - Give it a plausible **reason to dismiss**, and **distance**: another file or package from the
     landing point.
   - **A second implementation is the strongest form of this**: separate code doing the same
     guarded operation (a fallback backend, another package, another transport, a legacy version),
     so fixing the reported copy changes nothing in the other. Models fix the copy the example hits,
     re-run the example and stop. Prefer a real one (Pattern A or B) over a planted one. Find
     candidates by searching for the low-level primitive across packages (redirect following,
     header copying, file writes, message construction). It only counts if the report never
     describes it.
2. **Pattern B: uncovered routes.**
   - Routes into the same protected sink where the advisory's own protection is missing at the
     pinned commit, and which the published fix did not touch.
   - They are unmodified upstream code. A solver may argue they were never covered, but the task's
     general property covers them, so leaving one open is a model failure, not out of scope. The
     same holds for a route where the protection never existed: the property requires it.
   - Make sure the property, read literally, really covers each route (no word that excludes it),
     and that its test fails only when the protection is really missing (it must pass a correct
     fix placed at any valid layer).
   - The strongest lever found so far: DeepSeek 6 of 6 on one; both models 0 of 3 on three combined.
3. **Shape traps: an input form that a plausible check mishandles.** Examples: a value given as an
   array where the check only handles a string; a name split on the first separator when it can
   contain the separator; a resolved path against a lexical check; a rename or rewrite that happens
   after the check; a nested expression the check never inspects. Two conditions: the general
   property must cover the form literally, and the form must not fall inside anything a
   must-keep-working clause or a test fixture calls legitimate. A pure spelling, encoding, verb,
   protocol or role variant of a stated input is NOT a shape trap: both models always catch those
   (see "Never add").
4. **A coupled must-keep-working behaviour** next to the sink, tested functionally, so an
   over-broad fix fails. MiMo tends to over-harden.
5. **Producer off the check's path.** The check depends on data produced elsewhere (a schema,
   serializer, cache, mapper, table builder or config loader) and does not call it; the data
   reaches the check on a separate path (saved and reloaded, rebuilt from config). The fix needs
   both the check and the producer. Models trace into what the check calls, never back to where
   its data comes from. Rules:
   - it counts only if the producer is infrastructure, not a request handler;
   - verify that the check does **not** call the producer; if it does, the model follows the call
     and fixes it;
   - the report describes impact only through the check's path and states the property abstractly
     ("including data saved earlier"); it never points at the producer or the reload path;
   - avoid fixes where the check cannot compile without the producer change (that forces the find);
   - hidden tests must not need a field or function name the solver would have to guess;
   - prefer a producer deep in internal machinery (a table or schema builder). One behind a path
     that is easy to follow falls as soon as anything points at it.
6. **Injected siblings**, only where the plan asks for them. Each must be:
   - code a maintainer could have written, with no deceptive names or comments;
   - reachable through the real entry point;
   - covered by the task's general property, never by a sentence of its own;
   - placed where the upstream fix never touches.
7. **Wrong object.** The authorization check exists but decides on a different object than the one
   the request actually touches: a neighbouring or proxy resource (a parent or container instead of
   the item written), or an identity field the caller supplies (an account inside a caller-provided
   resource name; a parent read from one part of the request while the write uses another). Models
   copy the nearby precedent. Rules:
   - the instruction names the protected object class in product terms ("the objects that hold the
     limits"), never the check or its location;
   - the security test denies exactly the object touched while the proxy object stays allowed;
   - a functional test keeps a legitimate request on that same object working.
8. **Ordering.** The check is right but runs at the wrong moment: after an adjustment turns the
   attacker's value into a different bad value (an offset, a clamp, a unit conversion, a
   normalisation), or after a side effect has already happened (a directory created, a file cleared,
   copied or re-permissioned, a request sent) before the refusal. Rules:
   - the instruction states the property over the attacker's input or the outcome ("nothing outside
     the folder is created or changed, even when the request is refused"), never the order of steps;
   - the security test checks the side effect itself, not only the response;
   - any fix that keeps the property passes, wherever it places the check.
9. **Route where the protection never existed.** Real code reaches the protected sink but never had
   the check at all, so its absence reads as design (DeepSeek missed one 6 of 6 times). Rules:
   - it needs a plausible reason to dismiss: an unsupported combination, a legacy path, a
     neighbouring feature. If the project documents the protection as applying everywhere with no
     exceptions, there is no reason to dismiss and the route adds nothing;
   - the general property must cover it literally; never describe it in the instruction;
   - confirm it with a behavioural test on the pinned copy, like any Pattern B route.
10. **Merged or defaults route.** The restricted value reaches the sink through defaults, a merge,
    inheritance, a patch, or stored configuration rather than the request field the report shows.
    Models treat the report's example fields as the whole set. Rules:
    - state the property over the sink ("anything a submitter supplies that ends up in X, however
      it gets there"), not over the entry or field;
    - the security test drives the merged or stored route through the real entry point;
    - a functional test keeps legitimate defaults and merges working.

Aim for at least two levers with **different** reasons to dismiss.

**At least one lever must be how-type**: its fix needs the mechanism understood, not only found.
How-type levers are a producer off the check's path (5), a coupled must-keep-working value (4), a
shape that a plausible check mishandles (3: a separator split, a rename after the check), and a
route where the protection never existed. Where-type levers (another entry point into the same code,
a second copy, injected siblings) only cost a search. They held only when the report stayed general,
so count them as extras, never as the task's main difficulty.

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

## Environment (`tasks/stk-dagu-ghsaph8x/environment/Dockerfile`)
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

## Report to the solver (`tasks/stk-dagu-ghsaph8x/instruction.md`)
**Write:**
- what the system is, at product level;
- one observed impact, with ONE concrete trigger at user level (HTTP request, CLI call or public API
  use);
- the security property as an **invariant**, stated once in general terms: who may do what to which
  data, or what attacker input must never achieve ("no value of X may …, however it arrives"). It is
  fair when, read literally, it covers every tested route and shape; it must not point at any of
  them. Write a second property only for a genuinely different protection, never one per route,
  and never a count;
- every **contract** the tests need, each stated once for the whole product, never per route:
  - the refusal form ("a client error with no side effect");
  - any interface or field name a test uses, stated so it applies everywhere. If a sibling's test
    would need a contract that only that sibling uses, change the test so it does not, or drop the
    sibling;
  - preservation clauses ("everything that works today keeps working exactly as today"). Name a
    coupled legitimate value in property terms ("visible values keep binding even next to a hidden
    one"), not by the feature or route it sits on;
  - a legitimate magnitude next to any attack magnitude;
- that examples are examples, not the full set;
- the standard constraints block: fix the problem and its close variants; keep legitimate use
  working; do not look up the upstream fix; do not special-case the
  example.

**Never write:**
- file, package, function, class, field or parameter names a user would not see;
- line numbers, the root cause, the fix approach, or a CVE or GHSA id;
- a list of routes, spellings or roles;
- restricting adverbs ("directly", "only via");
- anything that names or paraphrases a far site, an uncovered route or an injected sibling;
- any clause that describes where a far site, uncovered route or injected sibling lives, even in
  product terms: no route, operation, command, channel, object kind, stage or format that points
  at one of them. State each property once, over the protected data or outcome, so it covers every
  route without pointing at any;
- a word that is general but is also the name of one stage or entry point ("loading" when the
  product has a load call). Pick wording that cannot be read as one surface.

Check before you finish: for each sentence of the report, ask whether it exists to cover one
specific route or trap. If it does, delete it or widen it into the general property.

Put every identifier that must not appear in `manifest.leak_terms`.

## Tests (`tasks/stk-dagu-ghsaph8x/tests/`)
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
- **Wrong-fix patches** go in `build/stk-dagu-ghsaph8x/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/stk-dagu-ghsaph8x/`:**
- `instruction.md`;
- `task.toml`, from `builder/templates/`, with `[metadata]` (incl. the delivery fields) filled in and
  `network_mode = "no-network"` (no allowlist);
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/stk-dagu-ghsaph8x/manifest.json`:**
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

**Also in `build/stk-dagu-ghsaph8x/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `builder/templates/` and `harness/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I builder/gate.py stk-dagu-ghsaph8x --only static
python3 -I builder/gate.py stk-dagu-ghsaph8x --only nop
python3 -I builder/gate.py stk-dagu-ghsaph8x --only oracle
python3 -I builder/gate.py stk-dagu-ghsaph8x --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/stk-dagu-ghsaph8x/`;
  - edit only `tasks/stk-dagu-ghsaph8x/`, `build/stk-dagu-ghsaph8x/` and, for pattern B, the register;
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


## Stacked task: additional rules

You are building a **stacked** task: one checkout with several independent places where a protection
is missing. The reader's record lists them, with evidence: `/home/mara/cwe-bench/stacking/out/reader/h3-ghsa-ph8x-4jfv-v9v8.json`. Verify each trap on the
pinned code before you rely on it. The record is a lead.

**The stack**
1. **At least 3 independent concepts.** If one guard or one fix site would close two traps, they are
   ONE concept. Count your reference fix's independent edit sites, not advisories or routes.
2. **Each concept is hard on its own** for at least one target model (tier hard or xhard in the
   record).
3. **Both models covered.** At least one DeepSeek-type trap (a route where the protection never
   existed, with a plausible reason to dismiss it) and at least one MiMo-type trap (a coupled
   must-keep-working value next to a hidden one, or a how-type mechanism).
4. **No single trap carries the task.** A fix that closes every concept except the hardest must still
   fail. Add one `security_fail` check patch per concept (a fix that misses only that concept).
5. **A coupled must-keep-working value next to every hidden route**, tested functionally.
6. **Effort budget.** A careful engineer who knows where to look fixes everything in about 45-60
   minutes. If the stack needs more, drop the weakest concept.

**The report**
7. **One general property per distinct protection.** Never one per route, and never a count. Describe
   no surface, as the build template already requires. If the stack spans two protections, state two
   properties, each over its protected data or outcome.

**History rules** (by the record's `pattern`)
8. **H3a / H3b (fix of a fix):**
   - pin the parent of the earlier fix A's first commit;
   - the reference fix is the complete fix (A plus the later fix B, or an equivalent);
   - add `checks/upstream_first_fix.patch`, which is A's fix applied alone, with `expect: fail`, so
     upstream's first fix is proven to be a wrong fix.
9. **H3c (masking):** the masked bug's security test must fail on the pinned code through its own
   route, without relying on the masking bug, so the gate's nop stage holds.
10. **Conflicting fixes (F8):** when the record names a pair where the natural fix for one trap breaks
    a value another needs, test that value functionally. State it in the report as a
    must-keep-working behaviour, in property terms.
11. **Dependency-bump fixes (F5):** when upstream fixed a bug by upgrading a dependency, the task must
    be fixable inside the repository. The reference proves it. The report never asks for an upgrade,
    and the solver works offline.
12. **Recall check (every pattern):** add `checks/upstream_fix.patch` (every published fix commit for
    the stacked advisories, applied together) with `expect: fail`. If it passes, the stack adds
    nothing beyond what upstream shipped. Rework the design.

**The control task**
13. Also build `<slug>-control`: the same pinned code, the same report, but only the advisory's own
    route (the trap the report leads to) in the security tests and the reference. It isolates the
    effect of stacking from the effect of the host.

**Manifest:** add a `stacking` block containing:
- `pattern`;
- `reader_record`;
- `concepts` (groups of trap ids);
- `history`: advisories A and B with their fix commits, `pinned_commit` and its rule;
- `score_at_build`: from `stacking/score_stack.py`;
- `control_slug`.

**Exact manifest fields the static conformance check reads (step 5, `stacking/check_stack.py`). Emit these literally — the field NAMES and VALUES below must match, or the build is rejected before the container gate:**

`manifest.traps[]` — one object per trap:
- `id` (string) — referenced by `stacking.concepts`.
- `type` — exactly one of `"deepseek"`, `"mimo"`, or `"both"`. At least one trap must be `"deepseek"` or `"both"`, and at least one must be `"mimo"` or `"both"`.
- `origin` — for a hidden route, one of `"uncovered_upstream"`, `"published_fix_far_site"`, `"injection_room"`. Any trap with such an `origin` must also carry `coupled_functional_tests`: a non-empty list of the functional-test ids that keep its must-keep-working value honest.

`manifest.stacking` — an object with exactly these keys (all required):
- `pattern` — e.g. `"H3a"`, `"H3b1"`, `"H3b2"`, `"H4"`.
- `concepts` — a list of **at least 3** groups; each group is a list of trap `id`s forming one independent concept. Every id must exist in `manifest.traps`.
- `history`, `control_slug`, `score_at_build`, `reader_record` — as described above.

`manifest.patch_checks[]` — in addition to the task's normal patch checks, add:
- **One per concept** (a fix that closes every concept EXCEPT this one, so its security tests still fail):
  `{ "patch": "checks/miss_<concept>.patch", "kind": "security_fail", "expect": "fail", "misses": [<exactly this concept's trap ids>] }`.
  `misses` must be non-empty and be a subset of that concept's trap id group; one such check is required for every group in `stacking.concepts`.
- **Recall (always):** `{ "patch": "checks/upstream_fix.patch", "expect": "fail" }` — all published fix commits for the stacked advisories applied together.
- **Recall (H3a and every H3b variant):** also `{ "patch": "checks/upstream_first_fix.patch", "expect": "fail" }` — the earlier fix A applied alone.

Every `checks/*.patch` named above must be a real file in the task's `checks/` directory (the container gate then runs each with its `expect`ed outcome). A concept with no `security_fail` miss-check, a trap with no `type`, or a missing recall check/file each fails the conformance check.

**Report back:** also give the concept count, the DeepSeek-type and MiMo-type trap ids, the result of
each history check patch, and the control task's gate result.

Stacked task slug: `stk-dagu-ghsaph8x`. Control task slug: `stk-dagu-ghsaph8x-control`. Manifest `stacking.reader_record`: `stacking/out/reader/h3-ghsa-ph8x-4jfv-v9v8.json`.
