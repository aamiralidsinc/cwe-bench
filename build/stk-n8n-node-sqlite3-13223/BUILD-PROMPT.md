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

Project root: `/home/mara/cwe-bench`. Task: `stk-n8n-node-sqlite3-13223`. Pattern: `A+B`. Track: `stacked`.

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
- Advisory: 13223; path traversal / expression injection into a filesystem path (CWE-22)
- Pinned (vulnerable) commit: 8a3493f19a426bd99ea91b2c337978e0488cc1c9. Published fix: 145a8876ff12375813bdcd4ae4fe78f460c53a98.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "candidate_id": "h4-13223",
 "pattern": "H4",
 "repo": "dangerblack/n8n-node-sqlite3",
 "pinned_commit": "8a3493f19a426bd99ea91b2c337978e0488cc1c9",
 "protections": [
  "The v1 node's Database Path parameter must not be expression-evaluable: db_path is resolved per input item at nodes/SqliteNode/v1/SqliteV1.node.ts:193 and handed straight to new Database(dbPath, bindings) at :224, so its descriptor (:110-118) needs noDataExpression:true, exactly as the sibling query_type already has it at :124.",
  "The v1 additionalOptions.use_custom_bindings parameter is a second expression-reachable filesystem path: it is read from the same per-item additionalOptions at :198, tested with fs.existsSync at :65 and passed into the same Database constructor as nativeBinding at :68 and :224, and its descriptor (:176-182) also lacks noDataExpression.",
  "The v2 implementation's database path must not be workflow-data-controlled: the only path input is the sqliteCredentials.databasePath credential (credentials/SqliteCredentials.credentials.ts:11-19), read by createConnection (nodes/SqliteNode/v2/transport/index.ts:15) and opened at :35 for every v2 route (actions/router.ts:14-16, methods/credentialTest.ts:18, methods/loadOptions.ts:12, methods/listSearch.ts:7).",
  "The v1 free-form SQL parameter query (:135-144) is not marked noDataExpression although v2's equivalent is (nodes/SqliteNode/v2/actions/database/executeQuery.operation.ts:26) \u2014 an adjacent but different protection (data reaching SQL text, not a filesystem path)."
 ],
 "traps": [
  {
   "id": "T1",
   "mechanism": "M4",
   "origin": "advisory_route",
   "locations": [
    "nodes/SqliteNode/v1/SqliteV1.node.ts:110-118",
    "nodes/SqliteNode/v1/SqliteV1.node.ts:193",
    "nodes/SqliteNode/v1/SqliteV1.node.ts:224"
   ],
   "reason_to_dismiss": "",
   "distance": {
    "files": 0,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "easy",
   "tier_mimo": "easy",
   "type": "neither",
   "evidence": [
    "nodes/SqliteNode/v1/SqliteV1.node.ts:110-118 (db_path descriptor: displayName 'Database Path' :111, name 'db_path' :112, type 'string' :113, default '' :114, required :117, no noDataExpression)",
    "nodes/SqliteNode/v1/SqliteV1.node.ts:124 (query_type in the same properties array already sets noDataExpression:true, so the flag is the file's own idiom)",
    "nodes/SqliteNode/v1/SqliteV1.node.ts:193 (db_path resolved per input item through getNodeParameter)",
    "nodes/SqliteNode/v1/SqliteV1.node.ts:200 (the only check on the value is non-emptiness)",
    "nodes/SqliteNode/v1/SqliteV1.node.ts:224 (the resolved string is opened by new Database(dbPath, bindings))"
   ]
  },
  {
   "id": "T2",
   "mechanism": "M1",
   "origin": "injection_room",
   "locations": [
    "nodes/SqliteNode/v1/SqliteV1.node.ts:176-182",
    "nodes/SqliteNode/v1/SqliteV1.node.ts:62-71",
    "nodes/SqliteNode/v1/SqliteV1.node.ts:224"
   ],
   "reason_to_dismiss": "It is the better-sqlite3 binding-binary path (nativeBinding), not the SQLite database file the advisory names; it reads as a non-docker portability option, and the only check on it (fs.existsSync at :65) makes any existing path acceptable rather than refusing a data-supplied one.",
   "distance": {
    "files": 0,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "hard",
   "tier_mimo": "medium",
   "type": "deepseek",
   "evidence": [
    "nodes/SqliteNode/v1/SqliteV1.node.ts:176-182 (use_custom_bindings is a plain string in the additionalOptions collection, default binaryPath at :180, description 'provide your own better-sqlite3 bindings', no noDataExpression)",
    "nodes/SqliteNode/v1/SqliteV1.node.ts:198 (additionalOptions is read per item, so a nested expression is resolved the same way as db_path)",
    "nodes/SqliteNode/v1/SqliteV1.node.ts:62-71 (getBindings: fs.existsSync :65, return { nativeBinding: opts.use_custom_bindings } :68)",
    "nodes/SqliteNode/v1/SqliteV1.node.ts:224 (the same new Database(dbPath, bindings) call receives it as the options argument)",
    "nodes/SqliteNode/v1/__tests__/SqliteV1.node.test.ts:216 (a literal absolute path '/custom/path/to/bindings' must keep working)"
   ]
  },
  {
   "id": "T3",
   "mechanism": "M2",
   "origin": "uncovered_upstream",
   "locations": [
    "credentials/SqliteCredentials.credentials.ts:11-19",
    "nodes/SqliteNode/v2/transport/index.ts:15",
    "nodes/SqliteNode/v2/transport/index.ts:35",
    "nodes/SqliteNode/v2/actions/router.ts:14-16"
   ],
   "reason_to_dismiss": "It is an administrator-set credential field rather than a node parameter: n8n resolves expressions on node parameters, not on stored credentials, and the published fix was scoped to v1, so the v2 route can be argued out of the advisory entirely.",
   "distance": {
    "files": 3,
    "packages": 2
   },
   "protection_state": "absent",
   "tier_deepseek": "xhard",
   "tier_mimo": "hard",
   "type": "deepseek",
   "evidence": [
    "credentials/SqliteCredentials.credentials.ts:11-19 (databasePath string, required at :18, no noDataExpression)",
    "nodes/SqliteNode/v2/transport/index.ts:15 (dbPath = credentials.databasePath) and :35 (return new Database(dbPath))",
    "nodes/SqliteNode/v2/actions/router.ts:14-16 (every v2 execution opens the connection from that credential before any operation runs)",
    "nodes/SqliteNode/v2/methods/credentialTest.ts:18, nodes/SqliteNode/v2/methods/loadOptions.ts:12, nodes/SqliteNode/v2/methods/listSearch.ts:7 (the other three createConnection callers \u2014 one credential property is the single fix site covering all four routes the screener listed separately in O8)",
    "nodes/SqliteNode/SqliteNode.node.ts:13 (defaultVersion: 2, so this is the default route for new workflows while v1 stays registered at :19)"
   ]
  },
  {
   "id": "T4",
   "mechanism": "M4",
   "origin": "injection_room",
   "locations": [
    "nodes/SqliteNode/v1/SqliteV1.node.ts:135-144",
    "nodes/SqliteNode/v1/SqliteV1.node.ts:194",
    "nodes/SqliteNode/v1/SqliteV1.node.ts:203",
    "nodes/SqliteNode/v1/SqliteV1.node.ts:237"
   ],
   "reason_to_dismiss": "It is the SQL text, not a filesystem path: a SQL node is normally expected to accept data-built queries, the advisory names db_path only, and removing expression support from Query is a breaking change for existing workflows.",
   "distance": {
    "files": 0,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "hard",
   "tier_mimo": "medium",
   "type": "deepseek",
   "evidence": [
    "nodes/SqliteNode/v1/SqliteV1.node.ts:135-144 (query string, required :142, typeOptions rows :143, no noDataExpression)",
    "nodes/SqliteNode/v1/SqliteV1.node.ts:194 (query read per item) and :203 (query.replace(/\\$/g,'@')) before execution at :232-237",
    "nodes/SqliteNode/v2/actions/database/executeQuery.operation.ts:26 (the v2 equivalent already sets noDataExpression:true on the same 'query' name)"
   ]
  },
  {
   "id": "T5",
   "mechanism": "M11",
   "origin": "advisory_route",
   "locations": [
    "nodes/SqliteNode/v1/SqliteV1.node.ts:114",
    "nodes/SqliteNode/v1/SqliteV1.node.ts:208-222",
    "nodes/SqliteNode/v1/__tests__/SqliteV1.node.test.ts:34"
   ],
   "reason_to_dismiss": "Relative and absolute literal paths plus auto-created parent directories are ordinary, tested feature behaviour (README.md:41), so the site does not look security-relevant at all and a guard placed there reads as new policy rather than as closing a hole.",
   "distance": {
    "files": 1,
    "packages": 0
   },
   "protection_state": "weak",
   "tier_deepseek": "medium",
   "tier_mimo": "hard",
   "type": "mimo",
   "evidence": [
    "nodes/SqliteNode/v1/SqliteV1.node.ts:114 (db_path default '') and :117 (required) \u2014 the descriptor places no constraint on the literal path shape, which is what makes it usable",
    "nodes/SqliteNode/v1/SqliteV1.node.ts:208-222 (path.dirname then fs.mkdirSync(dir,{recursive:true}) at :211 creates a missing parent directory for whatever literal path is supplied)",
    "nodes/SqliteNode/v1/__tests__/SqliteV1.node.test.ts:34 (a relative 'test.sqlite' path is the must-keep-working value exercised by the suite)",
    "README.md:41 (documented usage: 'Configure Database Path: Set the path to your SQLite database file')"
   ]
  }
 ],
 "independent_groups": [
  [
   "T1",
   "T5"
  ],
  [
   "T2"
  ],
  [
   "T3"
  ],
  [
   "T4"
  ]
 ],
 "history": {
  "a_fix_leaves_b_open": true,
  "b_in_code_a_wrote": true,
  "masking": [
   "A sink-level runtime check for T1 is masked by the ordering in the handler: fs.mkdirSync(dir,{recursive:true}) at nodes/SqliteNode/v1/SqliteV1.node.ts:211 runs on the supplied path before new Database at :224, so any validation placed at the open site runs after the filesystem side effect has already happened.",
   "T2 and T3 are not made reachable by fixing T1; they are already reachable in the pinned tree. The only masking is attentional: a solver who closes T1 sees the reported path gone while the second v1 path (T2) and the v2 implementation (T3) still accept data-supplied paths."
  ],
  "dependency_bump_fix": false,
  "in_repo_fix_possible": true
 },
 "conflicts": [
  {
   "a": "T1",
   "b": "T5",
   "what": "The natural fix for T1 \u2014 validate the path at runtime before new Database (path.resolve plus an allowed root, or rejecting '..'/absolute paths) \u2014 is exactly what breaks T5's must-keep-working values: the relative 'test.sqlite' case at SqliteV1.node.test.ts:34 and the auto-created missing parent directory at SqliteV1.node.ts:208-222."
  },
  {
   "a": "T2",
   "b": "T5",
   "what": "Reusing the same runtime path policy on use_custom_bindings breaks its legitimate default (the absolute binaryPath at SqliteV1.node.ts:180) and the test that passes '/custom/path/to/bindings' (SqliteV1.node.test.ts:216); the only fix that preserves both is the metadata flag, not a path policy."
  },
  {
   "a": "T1",
   "b": "T4",
   "what": "If T1 is fixed by a node-wide 'no data expressions in this node' policy rather than a per-property flag, T4's free-form SQL field loses the data-built queries the node supports; conversely leaving T4 alone keeps the same data-to-interpreter shape alive in the same properties array, so the fix has to be scoped property by property."
  }
 ],
 "fairness_risks": [
  "Forbidding data expressions on db_path removes the per-tenant shape '=/data/{{ $json.tenant }}.sqlite', which the per-item getNodeParameter at SqliteV1.node.ts:193 currently enables; the README does not document it, but a security rule for P1 refuses an input shape a legitimate workflow can use.",
  "The published fix has no behavioural code and no tests; neither v1 nor v2 test file asserts node-description metadata (grep for noDataExpression across both __tests__ files finds nothing), so the only in-repo way to grade P1/P2/P4 is to instantiate the node type and read .description.properties \u2014 a security-equivalent runtime validation would fail such a test.",
  "T3's fix may be vacuous: n8n credentials are administrator-set and, per the screener's own open question, may never be expression-evaluated, so a hidden test asserting noDataExpression on SqliteCredentials.properties[0] would grade a flag with no behavioural effect, and a solver who correctly judges the credential route out of scope would be marked wrong.",
  "T4 asks for a breaking change to the v1 SQL field that no advisory names; workflows that assemble SQL from item data would stop working, so a hidden test on it penalises correct scope judgement.",
  "db_path must keep accepting arbitrary literal paths: relative names ('test.sqlite', SqliteV1.node.test.ts:34), absolute paths, and paths whose parent directory does not exist yet (:208-222); an allowlist or traversal-reject rule contradicts README.md:41.",
  "use_custom_bindings must keep accepting an arbitrary literal absolute path (default binaryPath at SqliteV1.node.ts:180, test :216); a 'reject absolute paths' rule applied to the family breaks the node's non-docker install story (README.md:89-93).",
  "Any node-wide 'no data expressions' policy would also have to leave v2's table resourceLocator (nodes/SqliteNode/v2/actions/common.descriptions.ts:16-41) and queryReplacement (:116-123) expression-capable, because those are the intended data-in path for select/insert/upsert."
 ],
 "effort_minutes": 10,
 "usable": true,
 "design": {
  "traps": [
   "T1",
   "T5",
   "T2",
   "T3"
  ],
  "why": "T1 is the reported fix and costs one line, so it is the easy anchor. T5 rides on the same fix site and supplies the MiMo-shaped judgement: the metadata flag satisfies both because it does not change how literal paths behave, while the instinctive 'path traversal' fix in execute() (:193/:224) or a reject-relative/absolute rule breaks the 'test.sqlite' case (:34) and the auto-created parent directory (:208-222). T2 is the strongest independent missing guard in the same file: a second expression-reachable filesystem path 60 lines from the fixed descriptor, with a clean honest dismissal ('it is the bindings binary, not the database file') and a different consumer of the same constructor call \u2014 a deepseek-type absent protection. T3 is the second implementation of the same operation, two subsystems away, guarded by the strongest dismissal of all ('an admin credential, not a node parameter; the fix was fix(v1)') \u2014 the route the report would have to point at, hence the most likely to be missed. The screener's four v2 routes (router, credentialTest, loadOptions, listSearch) collapse to this one credential property and therefore one independent group, not four. T4 is recorded as a fifth candidate but excluded from the design because it demands a breaking change no advisory names and would penalise a solver who stays inside the advisory; it is only worth adding if the task wants five traps at the cost of fairness."
 },
 "unverified": [
  "The published fix commit 145a8876ff12375813bdcd4ae4fe78f460c53a98 is not present in this worktree and there is no fix.diff; all statements about what the fix changed (only the v1 db_path property) come from the screener record, not from the pinned tree.",
  "n8n-workflow is a peerDependency and node_modules is absent, so neither the expression engine's behaviour on node parameters nor its behaviour (if any) on credential fields could be read; P1's premise rests on the advisory summary and the in-repo presence of the noDataExpression idiom, and P3's weakness rests on the screener's unverified note.",
  "Whether noDataExpression is honoured on a collection sub-option such as use_custom_bindings (:176-182) in the peer n8n-workflow version was not checked; the flag appears only on top-level properties and the operation dropdown in this tree.",
  "Which commit introduced credentials/ and nodes/SqliteNode/v2 was not checked (no shell/git access in this session); the H3 answer that the v2 gap lives in code an earlier refactor wrote is inferred from the recent-commit list ('Modernize the UI and refactor the code to follow PostgreSQL node implementation') and the file layout.",
  "Distance counts are hop counts over the file list, not measured path lengths or repo size; the screener's O4 (3 files / 3 packages) counts the whole v2 plus credentials area rather than a single trap.",
  "No release or later commit was in scope, so present_in_latest is unknown for every route.",
  "Whether a hidden test can assert node-description metadata at all depends on how the node type is instantiated; no existing test does it, and the v1 constructor builds description as a class field with no required arguments (SqliteV1.node.ts:97-186), so it is mechanically possible but unproven in this tree.",
  "T4's premise that n8n's own nodes deliberately set noDataExpression on a raw SQL field is supported only by the in-repo v2 counterpart (executeQuery.operation.ts:26), not by the upstream n8n source."
 ]
}
  ```
- Published fix sites:   - nodes/SqliteNode/v1/SqliteV1.node.ts:110-118 — T1 M4 (reason to dismiss: none)
  - nodes/SqliteNode/v1/SqliteV1.node.ts:193 — T1 M4 (reason to dismiss: none)
  - nodes/SqliteNode/v1/SqliteV1.node.ts:224 — T1 M4 (reason to dismiss: none)
  - nodes/SqliteNode/v1/SqliteV1.node.ts:114 — T5 M11 (reason to dismiss: Relative and absolute literal paths plus auto-created parent directories are ordinary, tested feature behaviour (README.md:41), so the site does not look security-relevant at all and a guard placed there reads as new policy rather than as closing a hole.)
  - nodes/SqliteNode/v1/SqliteV1.node.ts:208-222 — T5 M11 (reason to dismiss: Relative and absolute literal paths plus auto-created parent directories are ordinary, tested feature behaviour (README.md:41), so the site does not look security-relevant at all and a guard placed there reads as new policy rather than as closing a hole.)
  - nodes/SqliteNode/v1/__tests__/SqliteV1.node.test.ts:34 — T5 M11 (reason to dismiss: Relative and absolute literal paths plus auto-created parent directories are ordinary, tested feature behaviour (README.md:41), so the site does not look security-relevant at all and a guard placed there reads as new policy rather than as closing a hole.)
- Uncovered routes to confirm (pattern B):   - credentials/SqliteCredentials.credentials.ts:11-19 — T3 M2 (reason to dismiss: It is an administrator-set credential field rather than a node parameter: n8n resolves expressions on node parameters, not on stored credentials, and the published fix was scoped to v1, so the v2 route can be argued out of the advisory entirely.)
  - nodes/SqliteNode/v2/transport/index.ts:15 — T3 M2 (reason to dismiss: It is an administrator-set credential field rather than a node parameter: n8n resolves expressions on node parameters, not on stored credentials, and the published fix was scoped to v1, so the v2 route can be argued out of the advisory entirely.)
  - nodes/SqliteNode/v2/transport/index.ts:35 — T3 M2 (reason to dismiss: It is an administrator-set credential field rather than a node parameter: n8n resolves expressions on node parameters, not on stored credentials, and the published fix was scoped to v1, so the v2 route can be argued out of the advisory entirely.)
  - nodes/SqliteNode/v2/actions/router.ts:14-16 — T3 M2 (reason to dismiss: It is an administrator-set credential field rather than a node parameter: n8n resolves expressions on node parameters, not on stored credentials, and the published fix was scoped to v1, so the v2 route can be argued out of the advisory entirely.)
- Design plan from the lead: TRACK = STACKED (H4). Build the stacked design the reader chose: traps T1, T5, T2, T3. Why: T1 is the reported fix and costs one line, so it is the easy anchor. T5 rides on the same fix site and supplies the MiMo-shaped judgement: the metadata flag satisfies both because it does not change how literal paths behave, while the instinctive 'path traversal' fix in execute() (:193/:224) or a reject-relative/absolute rule breaks the 'test.sqlite' case (:34) and the auto-created parent directory (:208-222). T2 is the strongest independent missing guard in the same file: a second expression-reachable filesystem path 60 lines from the fixed descriptor, with a clean honest dismissal ('it is the bindings binary, not the database file') and a different consumer of the same constructor call — a deepseek-type absent protection. T3 is the second implementation of the same operation, two subsystems away, guarded by the strongest dismissal of all ('an admin credential, not a node parameter; the fix was fix(v1)') — the route the report would have to point at, hence the most likely to be missed. The screener's four v2 routes (router, credentialTest, loadOptions, listSearch) collapse to this one credential property and therefore one independent group, not four. T4 is recorded as a fifth candidate but excluded from the design because it demands a breaking change no advisory names and would penalise a solver who stays inside the advisory; it is only worth adding if the task wants five traps at the cost of fairness. Follow the stacked-task rules appended at the end of this prompt; they add to the rules above.
- Host notes: Reader fairness risks (resolve each in the report's contracts or the tests): Forbidding data expressions on db_path removes the per-tenant shape '=/data/{{ $json.tenant }}.sqlite', which the per-item getNodeParameter at SqliteV1.node.ts:193 currently enables; the README does not document it, but a security rule for P1 refuses an input shape a legitimate workflow can use. | The published fix has no behavioural code and no tests; neither v1 nor v2 test file asserts node-description metadata (grep for noDataExpression across both __tests__ files finds nothing), so the only in-repo way to grade P1/P2/P4 is to instantiate the node type and read .description.properties — a security-equivalent runtime validation would fail such a test. | T3's fix may be vacuous: n8n credentials are administrator-set and, per the screener's own open question, may never be expression-evaluated, so a hidden test asserting noDataExpression on SqliteCredentials.properties[0] would grade a flag with no behavioural effect, and a solver who correctly judges the credential route out of scope would be marked wrong. | T4 asks for a breaking change to the v1 SQL field that no advisory names; workflows that assemble SQL from item data would stop working, so a hidden test on it penalises correct scope judgement. | db_path must keep accepting arbitrary literal paths: relative names ('test.sqlite', SqliteV1.node.test.ts:34), absolute paths, and paths whose parent directory does not exist yet (:208-222); an allowlist or traversal-reject rule contradicts README.md:41. | use_custom_bindings must keep accepting an arbitrary literal absolute path (default binaryPath at SqliteV1.node.ts:180, test :216); a 'reject absolute paths' rule applied to the family breaks the node's non-docker install story (README.md:89-93). | Any node-wide 'no data expressions' policy would also have to leave v2's table resourceLocator (nodes/SqliteNode/v2/actions/common.descriptions.ts:16-41) and queryReplacement (:116-123) expression-capable, because those are the intended data-in path for select/insert/upsert.. Conflicts the reader found: The natural fix for T1 — validate the path at runtime before new Database (path.resolve plus an allowed root, or rejecting '..'/absolute paths) — is exactly what breaks T5's must-keep-working values: the relative 'test.sqlite' case at SqliteV1.node.test.ts:34 and the auto-created missing parent directory at SqliteV1.node.ts:208-222. | Reusing the same runtime path policy on use_custom_bindings breaks its legitimate default (the absolute binaryPath at SqliteV1.node.ts:180) and the test that passes '/custom/path/to/bindings' (SqliteV1.node.test.ts:216); the only fix that preserves both is the metadata flag, not a path policy. | If T1 is fixed by a node-wide 'no data expressions in this node' policy rather than a per-property flag, T4's free-form SQL field loses the data-built queries the node supports; conversely leaving T4 alone keeps the same data-to-interpreter shape alive in the same properties array, so the fix has to be scoped property by property.

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

## Environment (`tasks/stk-n8n-node-sqlite3-13223/environment/Dockerfile`)
- **Base and code.** A small official base image. The repo goes into `/app` at the pinned commit,
  and `/app/.git` is then deleted.
- **Offline.** Install every dependency, tool and service the project and tests need; nothing may
  be downloaded at test time. Services start from `test.sh`.
- **Packages:** `patch`, `curl`, `ca-certificates`, `bash`, `git`.
- **Agent layer.** Append `common/trial/claude-code.Dockerfile.snippet` unchanged at the end.
- **No test code in the image.** The agent shares the container. Pre-build against stubs; `test.sh`
  copies the real tests in at grading time.
- **Project tests.** The project's own tests for the affected area must pass in the image at the
  pinned commit.
- **No leaked regression tests.** The pinned commit must not already contain the advisory's
  regression tests (check `git log` between the pinned and fix commits).

## Report to the solver (`tasks/stk-n8n-node-sqlite3-13223/instruction.md`)
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

## Tests (`tasks/stk-n8n-node-sqlite3-13223/tests/`)
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
- **Wrong-fix patches** go in `build/stk-n8n-node-sqlite3-13223/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/stk-n8n-node-sqlite3-13223/`:**
- `instruction.md`;
- `task.toml`, from `common/builder/templates/`, with `[metadata]` (incl. the delivery fields) filled in and
  `network_mode = "no-network"` (no allowlist);
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/stk-n8n-node-sqlite3-13223/manifest.json`:**
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

**Also in `build/stk-n8n-node-sqlite3-13223/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `common/builder/templates/` and `common/trial/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I common/gate/gate.py stk-n8n-node-sqlite3-13223 --only static
python3 -I common/gate/gate.py stk-n8n-node-sqlite3-13223 --only nop
python3 -I common/gate/gate.py stk-n8n-node-sqlite3-13223 --only oracle
python3 -I common/gate/gate.py stk-n8n-node-sqlite3-13223 --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/stk-n8n-node-sqlite3-13223/`;
  - edit only `tasks/stk-n8n-node-sqlite3-13223/`, `build/stk-n8n-node-sqlite3-13223/` and, for pattern B, the register;
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
is missing. The reader's record lists them, with evidence: `/home/mara/cwe-bench/pipelines/stacking/out/reader/h4-13223.json`. Verify each trap on the
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
5. **A coupled must-keep-working value next to every hidden route**, tested functionally. The
   report covers it ONLY through the general keep-working sentence ("everything that works today
   keeps working"); it never names or describes the value. If a security rule, read literally, would
   forbid that value, reword the security rule over its protected outcome instead of adding an
   exception that names the value.
6. **Effort budget.** A careful engineer who knows where to look fixes everything in about 45-60
   minutes. If the stack needs more, drop the weakest concept.

**The report**
7. **One general property per distinct protection, and nothing per trap.** Never one per route, and
   never a count. Describe no surface, as the build template already requires. If the stack spans two
   protections, state two properties, each over its protected data or outcome.
   - **The one-bug test:** for every sentence of the report, ask "would this sentence be here if the
     task had only the advisory's own route?" If not, delete it. That covers forms ("in every form it
     can be named"), timing ("and again when the call connects"), sources ("whichever response
     supplies it"), encodings, aliases, example values in keep-working lines, and lists of resources.
   - Only the advisory's own route may be shown, in the impact example.
   - General contracts that hold for every route stay: the refusal form (for example "a client
     error, with no effect"), an operator opt-in, "keep every legitimate use working".
   - Keep the report short: the goal in a few lines, the property, the general contracts.
   - After the build, `pipelines/stacking/4-listing/run_listing_check.sh` classifies every hidden trap against the
     report. One NAMED hidden trap, or more than one DESCRIBED hidden trap, is a FAIL. Once the
     reviewer is calibrated (`pipelines/stacking/4-listing/LISTING_ENFORCE`), a FAIL means the task is not marked sound.

**History rules** (by the record's `pattern`)
8. **H3a / H3b (fix of a fix):**
   - pin the parent of the earlier fix A's first commit;
   - the reference fix is the complete fix (A plus the later fix B, or an equivalent);
   - add `checks/upstream_first_fix.patch`, which is A's fix applied alone, with `expect: fail`, so
     upstream's first fix is proven to be a wrong fix.
9. **H3c (masking):** the masked bug's security test must fail on the pinned code through its own
   route, without relying on the masking bug, so the gate's nop stage holds.
10. **Conflicting fixes (F8):** when the record names a pair where the natural fix for one trap breaks
    a value another needs, test that value functionally. The report covers it only through the
    general keep-working sentence, as in rule 5; never by naming the value.
11. **Dependency-bump fixes (F5):** when upstream fixed a bug by upgrading a dependency, the task must
    be fixable inside the repository. The reference proves it. The report never asks for an upgrade,
    and the solver works offline.
12. **Recall check (every pattern):** add `checks/upstream_fix.patch` (every published fix commit for
    the stacked advisories, applied together) with `expect: fail`. If it passes, the stack adds
    nothing beyond what upstream shipped. Rework the design.

**The control task**
13. Also build `<slug>-control`: the same pinned code, the same report, but only the advisory's own
    route (the trap the report leads to) in the security tests and the reference. It isolates the
    effect of stacking from the effect of the host. The two `instruction.md` files stay byte-identical
    for the task's whole life: any later change to the stacked report (fairfix, upgrade) is copied to
    the control. `check_stack.py` checks it.

**Manifest:** add a `stacking` block containing:
- `pattern`;
- `reader_record`;
- `concepts` (groups of trap ids);
- `history`: advisories A and B with their fix commits, `pinned_commit` and its rule;
- `score_at_build`: copy the `score` of your job's row in `pipelines/stacking/out/stack_scores_ds.tsv` (do NOT run
  `score_stack.py`: it rewrites the shared selection file);
- `control_slug`.

**Exact manifest fields the static conformance check reads (step 5, `pipelines/stacking/3-build-gate/check_stack.py`). Emit these literally — the field NAMES and VALUES below must match, or the build is rejected before the container gate:**

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
  `{ "patch": "checks/miss_<concept>.patch", "kind": "security_fail", "expect": "security_fail", "misses": [<exactly this concept's trap ids>] }`.
  `misses` must be non-empty and be a subset of that concept's trap id group; one such check is required for every group in `stacking.concepts`.
- **Recall (always):** `{ "patch": "checks/upstream_fix.patch", "expect": "security_fail" }` — all published fix commits for the stacked advisories applied together.
- **Recall (H3a and every H3b variant):** also `{ "patch": "checks/upstream_first_fix.patch", "expect": "security_fail" }` — the earlier fix A applied alone.

Every `checks/*.patch` named above must be a real file in the task's `checks/` directory (the container gate then runs each with its `expect`ed outcome). A concept with no `security_fail` miss-check, a trap with no `type`, or a missing recall check/file each fails the conformance check.

**Report back:** also give the concept count, the DeepSeek-type and MiMo-type trap ids, the result of
each history check patch, and the control task's gate result.

Stacked task slug: `stk-n8n-node-sqlite3-13223`. Control task slug: `stk-n8n-node-sqlite3-13223-control`. Manifest `stacking.reader_record`: `pipelines/stacking/out/reader/h4-13223.json`.
