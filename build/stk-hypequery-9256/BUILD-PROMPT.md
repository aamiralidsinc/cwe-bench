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

Project root: `/home/mara/cwe-bench`. Task: `stk-hypequery-9256`. Pattern: `A+B`. Track: `stacked`.

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
- Advisory: 9256; SQL injection (CWE-89): missing neutralisation of string literals, raw
- Pinned (vulnerable) commit: 7a9ef6bf4867ef231067ee70b94cad1b2cbc8add. Published fix: 2879161a810fed2c2222f785816ff05510976960, 2dc1df7bae9a67d71d242fac5df76853db99f649, 4dfa9d77d70a08b970e722268b75ca7d13db0bdf.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "candidate_id": "h4-9256",
 "pattern": "H4",
 "repo": "hypequery/hypequery",
 "pinned_commit": "7a9ef6bf4867ef231067ee70b94cad1b2cbc8add",
 "protections": [
  "Runtime values reach SQL only as `?` placeholders rendered client-side by escapeValue (single-quote wrapping plus quote doubling), because ClickHouseAdapter uses substituteParameters as the sole rendering step - packages/clickhouse/src/core/utils.ts:1-32, packages/clickhouse/src/core/adapters/clickhouse-adapter.ts:42-51",
  "Raw SQL text (expr.raw(), .raw(), .having(), the sql tag, field-level sql expressions) is inserted verbatim and treated as developer-trusted code - packages/clickhouse/src/core/formatters/sql-formatter.ts:45-49, packages/clickhouse/src/dataset/sql-tag.ts:48-51",
  "Interpolated identifiers are trusted everywhere except the withScalar alias, which is checked against ^[A-Za-z_][A-Za-z0-9_]*$; the datasets package has its own validateSQLIdentifier/quoteSQLIdentifier for generated SQL - packages/clickhouse/src/core/query-builder.ts:367-371, packages/datasets/src/sql-utils.ts:23-43",
  "Dataset and metric filter field names are whitelisted against the dataset contract before SQL generation - packages/datasets/src/executor.ts:82-86, packages/serve/src/semantic/datasets/utils/dataset-query-validation.ts:38-50"
 ],
 "traps": [
  {
   "id": "T1",
   "mechanism": "M8",
   "origin": "advisory_route",
   "locations": [
    "packages/clickhouse/src/core/utils.ts:8"
   ],
   "reason_to_dismiss": "",
   "distance": {
    "files": 0,
    "packages": 0
   },
   "protection_state": "weak",
   "tier_deepseek": "easy",
   "tier_mimo": "easy",
   "type": "neither",
   "evidence": [
    "packages/clickhouse/src/core/utils.ts:7-8",
    "packages/clickhouse/src/core/tests/query-builder.where.test.ts:33"
   ]
  },
  {
   "id": "T2",
   "mechanism": "M4",
   "origin": "advisory_route",
   "locations": [
    "packages/clickhouse/src/core/utils.ts:11-13",
    "packages/clickhouse/src/core/utils.ts:5-6"
   ],
   "reason_to_dismiss": "Object/array values are developer-supplied structured data and a JSON payload is not a value shape ClickHouse columns accept, so the fallback branch is read as a convenience rather than a user-data route.",
   "distance": {
    "files": 0,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "easy",
   "tier_mimo": "easy",
   "type": "neither",
   "evidence": [
    "packages/clickhouse/src/core/utils.ts:9-13",
    "packages/clickhouse/src/core/utils.ts:1-14"
   ]
  },
  {
   "id": "T3",
   "mechanism": "M8",
   "origin": "advisory_route",
   "locations": [
    "packages/clickhouse/src/core/utils.ts:20"
   ],
   "reason_to_dismiss": "The SQL text is developer-authored; a `?` inside a quoted literal or comment is a coding error and the placeholder/parameter count check throws instead of executing.",
   "distance": {
    "files": 0,
    "packages": 0
   },
   "protection_state": "weak",
   "tier_deepseek": "medium",
   "tier_mimo": "hard",
   "type": "both",
   "evidence": [
    "packages/clickhouse/src/core/utils.ts:16-31",
    "packages/clickhouse/src/core/adapters/clickhouse-adapter.ts:43",
    "packages/clickhouse/src/core/tests/query-builder.basic.test.ts:244-245"
   ]
  },
  {
   "id": "T4",
   "mechanism": "M7",
   "origin": "published_fix_far_site",
   "locations": [
    "packages/clickhouse/src/core/features/analytics.ts:26"
   ],
   "reason_to_dismiss": "Scalar expressions are developer-authored CTE definitions built from literals and column references, and rendering their parameters at build time is deliberate so the CTE text matches the expression.",
   "distance": {
    "files": 1,
    "packages": 0
   },
   "protection_state": "weak",
   "tier_deepseek": "hard",
   "tier_mimo": "hard",
   "type": "both",
   "evidence": [
    "packages/clickhouse/src/core/features/analytics.ts:24-31",
    "packages/clickhouse/src/core/features/executor.ts:30-32",
    "packages/clickhouse/src/core/tests/query-builder-analytics.test.ts:212-223"
   ]
  },
  {
   "id": "T5",
   "mechanism": "M4",
   "origin": "published_fix_far_site",
   "locations": [
    "packages/clickhouse/src/core/formatters/sql-formatter.ts:62-73",
    "packages/clickhouse/src/core/features/filtering.ts:107-124"
   ],
   "reason_to_dismiss": "expr.raw() and .raw() values are documented raw-SQL escape hatches, and the project's where tests pin the exact flat SQL, so a solver can argue composition is the caller's responsibility.",
   "distance": {
    "files": 1,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "hard",
   "tier_mimo": "hard",
   "type": "mimo",
   "evidence": [
    "packages/clickhouse/src/core/formatters/sql-formatter.ts:62-73",
    "packages/clickhouse/src/core/features/filtering.ts:107-124",
    "packages/clickhouse/src/core/tests/query-builder.where.test.ts:275",
    "packages/clickhouse/src/core/tests/query-builder.where.test.ts:291"
   ]
  },
  {
   "id": "T6",
   "mechanism": "M4",
   "origin": "published_fix_far_site",
   "locations": [
    "packages/clickhouse/src/core/formatters/sql-formatter.ts:179-189",
    "packages/clickhouse/src/core/query-builder.ts:412-417",
    "packages/clickhouse/src/core/features/query-modifiers.ts:78-93"
   ],
   "reason_to_dismiss": "having() and .raw() take raw SQL text by design and several fragments are already documented as joined with AND, so the fragment text is treated as the caller's syntax.",
   "distance": {
    "files": 2,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "hard",
   "tier_mimo": "hard",
   "type": "both",
   "evidence": [
    "packages/clickhouse/src/core/formatters/sql-formatter.ts:179-189",
    "packages/clickhouse/src/core/tests/query-builder-analytics.test.ts:69-78",
    "packages/clickhouse/src/core/tests/query-builder.joins.test.ts:258-259"
   ]
  },
  {
   "id": "T7",
   "mechanism": "M4",
   "origin": "published_fix_far_site",
   "locations": [
    "packages/clickhouse/src/core/utils/predicate-builder.ts:144-155",
    "packages/clickhouse/src/core/formatters/sql-formatter.ts:45-49"
   ],
   "reason_to_dismiss": "buildLogical already parenthesises every child expression, so the expression is unambiguous on its own; the remaining risk appears only when a caller mixes it into a flat sequence, which is the caller's composition.",
   "distance": {
    "files": 1,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "hard",
   "tier_mimo": "hard",
   "type": "mimo",
   "evidence": [
    "packages/clickhouse/src/core/utils/predicate-builder.ts:144-155",
    "packages/clickhouse/src/core/formatters/sql-formatter.ts:45-49",
    "packages/clickhouse/src/core/tests/query-builder.where.test.ts:361-370"
   ]
  },
  {
   "id": "T8",
   "mechanism": "M4",
   "origin": "published_fix_far_site",
   "locations": [
    "packages/clickhouse/src/core/utils/predicate-builder.ts:139",
    "packages/clickhouse/src/core/utils/predicate-builder.ts:159-160"
   ],
   "reason_to_dismiss": "fn() names are developer constants written in application code, not request input, so no runtime allowlist is expected.",
   "distance": {
    "files": 1,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "medium",
   "tier_mimo": "medium",
   "type": "deepseek",
   "evidence": [
    "packages/clickhouse/src/core/utils/predicate-builder.ts:134-142",
    "packages/clickhouse/src/core/utils/predicate-builder.ts:159-160",
    "packages/clickhouse/src/core/tests/query-builder.where.test.ts:430-434"
   ]
  },
  {
   "id": "T9",
   "mechanism": "M4",
   "origin": "published_fix_far_site",
   "locations": [
    "packages/clickhouse/src/core/features/analytics.ts:20",
    "packages/clickhouse/src/core/query-builder.ts:355-360"
   ],
   "reason_to_dismiss": "CTE aliases are developer-chosen identifiers written at the call site, and the sibling withScalar path already enforces an identifier regex, so the API looks consistently trusted.",
   "distance": {
    "files": 2,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "medium",
   "tier_mimo": "medium",
   "type": "deepseek",
   "evidence": [
    "packages/clickhouse/src/core/features/analytics.ts:15-22",
    "packages/clickhouse/src/core/query-builder.ts:355-360",
    "packages/clickhouse/src/core/query-builder.ts:367-371"
   ]
  },
  {
   "id": "T10",
   "mechanism": "M4",
   "origin": "uncovered_upstream",
   "locations": [
    "packages/clickhouse/src/core/features/aggregations.ts:61",
    "packages/clickhouse/src/core/features/aggregations.ts:99"
   ],
   "reason_to_dismiss": "Aggregate aliases and columns are typed by schema-derived TypeScript template literals, so they are compile-time-trusted identifiers rather than runtime data.",
   "distance": {
    "files": 1,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "xhard",
   "tier_mimo": "hard",
   "type": "deepseek",
   "evidence": [
    "packages/clickhouse/src/core/features/aggregations.ts:56-76",
    "packages/clickhouse/src/core/features/aggregations.ts:98-114",
    "packages/datasets/src/query-planner.ts:62-90"
   ]
  },
  {
   "id": "T11",
   "mechanism": "M2",
   "origin": "uncovered_upstream",
   "locations": [
    "packages/datasets/src/utils/filtered-aggregation-sql.ts:12",
    "packages/datasets/src/utils/filtered-aggregation-sql.ts:56",
    "packages/datasets/src/utils/filtered-aggregation-sql.ts:64"
   ],
   "reason_to_dismiss": "Measure-level filter values are developer-authored in the measure definition and the project spec calls custom SQL in field definitions trusted code, so this literal renderer is read as a second, developer-only implementation.",
   "distance": {
    "files": 1,
    "packages": 1
   },
   "protection_state": "absent",
   "tier_deepseek": "hard",
   "tier_mimo": "hard",
   "type": "both",
   "evidence": [
    "packages/datasets/src/utils/filtered-aggregation-sql.ts:6-27",
    "packages/datasets/src/measure.ts:4-12",
    "packages/serve/DATASETS_AND_METRICS_SPEC.md:891",
    "packages/datasets/src/datasets.test.ts:624-632"
   ]
  },
  {
   "id": "T12",
   "mechanism": "M2",
   "origin": "uncovered_upstream",
   "locations": [
    "packages/serve/src/semantic/datasets/utils/filtered-aggregation-sql.ts:22",
    "packages/serve/src/semantic/datasets/utils/filtered-aggregation-sql.ts:67",
    "packages/serve/src/semantic/datasets/utils/filtered-aggregation-sql.ts:75"
   ],
   "reason_to_dismiss": "This is a byte-for-byte copy of the datasets renderer fed from the same developer-authored measure definitions, so the same trusted-code argument applies and a solver who fixed the datasets copy sees no reason to open the second one.",
   "distance": {
    "files": 2,
    "packages": 2
   },
   "protection_state": "absent",
   "tier_deepseek": "hard",
   "tier_mimo": "hard",
   "type": "both",
   "evidence": [
    "packages/serve/src/semantic/datasets/utils/filtered-aggregation-sql.ts:16-37",
    "packages/serve/src/semantic/datasets/query-planner.ts:66-78",
    "packages/serve/DATASETS_AND_METRICS_SPEC.md:891"
   ]
  },
  {
   "id": "T13",
   "mechanism": "M4",
   "origin": "uncovered_upstream",
   "locations": [
    "packages/clickhouse/src/core/utils/sql-expressions.ts:106-110",
    "packages/clickhouse/src/core/utils/sql-expressions.ts:128",
    "packages/clickhouse/src/core/dialects/clickhouse-dialect.ts:70-76"
   ],
   "reason_to_dismiss": "Format strings, timezones and intervals are code-level constants passed to SELECT-expression helpers, and ClickHouse requires them inside literal or INTERVAL syntax.",
   "distance": {
    "files": 1,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "hard",
   "tier_mimo": "medium",
   "type": "deepseek",
   "evidence": [
    "packages/clickhouse/src/core/utils/sql-expressions.ts:99-130",
    "packages/clickhouse/src/core/dialects/clickhouse-dialect.ts:70-76",
    "packages/clickhouse/src/core/tests/sql-expressions.test.ts:43-56"
   ]
  },
  {
   "id": "T14",
   "mechanism": "M4",
   "origin": "uncovered_upstream",
   "locations": [
    "packages/clickhouse/src/core/utils/sql-expressions.ts:49-56"
   ],
   "reason_to_dismiss": "rawAs()/selectExpr() are the documented select-expression escape hatch and the alias is a developer-chosen label, not request data.",
   "distance": {
    "files": 1,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "hard",
   "tier_mimo": "medium",
   "type": "deepseek",
   "evidence": [
    "packages/clickhouse/src/core/utils/sql-expressions.ts:49-56",
    "packages/clickhouse/src/core/tests/query-builder.aggregations.test.ts:36-40"
   ]
  },
  {
   "id": "T15",
   "mechanism": "M4",
   "origin": "uncovered_upstream",
   "locations": [
    "packages/clickhouse/src/core/formatters/sql-formatter.ts:123-140",
    "packages/clickhouse/src/core/features/filtering.ts:83-92"
   ],
   "reason_to_dismiss": "inSubquery/inTable values are documented as raw subquery and table SQL strings, not as bound values, and the operator names say so.",
   "distance": {
    "files": 0,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "medium",
   "tier_mimo": "medium",
   "type": "deepseek",
   "evidence": [
    "packages/clickhouse/src/core/formatters/sql-formatter.ts:123-140",
    "packages/clickhouse/src/core/features/filtering.ts:83-92",
    "packages/clickhouse/src/core/tests/advanced-in-operators.test.ts:238-246"
   ]
  },
  {
   "id": "T16",
   "mechanism": "M1",
   "origin": "published_fix_far_site",
   "locations": [
    "packages/clickhouse/src/dataset/sql-tag.ts:48-51"
   ],
   "reason_to_dismiss": "The published fix re-documented the sql tag as an intentional raw-SQL authoring API and the project pins verbatim interpolation, so it is treated as developer code rather than a to-be-escaped sink.",
   "distance": {
    "files": 1,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "xhard",
   "tier_mimo": "xhard",
   "type": "both",
   "evidence": [
    "packages/clickhouse/src/dataset/sql-tag.ts:35-69",
    "packages/clickhouse/src/dataset/sql-tag.test.ts:17-22",
    "packages/serve/DATASETS_AND_METRICS_SPEC.md:890-891"
   ]
  },
  {
   "id": "T17",
   "mechanism": "M4",
   "origin": "uncovered_upstream",
   "locations": [
    "packages/clickhouse/src/core/formatters/sql-formatter.ts:31-39",
    "packages/clickhouse/src/core/formatters/sql-formatter.ts:205-234"
   ],
   "reason_to_dismiss": "Table names, join aliases, order/limit-by columns and select expressions all originate from schema-typed columns or builder arguments, and every request-facing path whitelists field names first.",
   "distance": {
    "files": 1,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "hard",
   "tier_mimo": "hard",
   "type": "deepseek",
   "evidence": [
    "packages/clickhouse/src/core/formatters/sql-formatter.ts:31-39",
    "packages/clickhouse/src/core/formatters/sql-formatter.ts:205-234",
    "packages/datasets/src/executor.ts:114-120",
    "packages/serve/src/semantic/datasets/utils/dataset-query-validation.ts:80-85"
   ]
  }
 ],
 "independent_groups": [
  [
   "T1",
   "T2"
  ],
  [
   "T3",
   "T4"
  ],
  [
   "T5",
   "T6",
   "T7"
  ],
  [
   "T8",
   "T9",
   "T10",
   "T14",
   "T17"
  ],
  [
   "T11",
   "T12"
  ],
  [
   "T13"
  ],
  [
   "T15"
  ],
  [
   "T16"
  ]
 ],
 "history": {
  "a_fix_leaves_b_open": null,
  "b_in_code_a_wrote": null,
  "masking": [
   "T4 is masked by T3: withScalar renders its own parameters at build time (analytics.ts:26) and the executor substitutes the whole query again (executor.ts:30-32), so a `?` inside a scalar literal only corrupts SQL through the lexical split; a test written after the scanner lands will not see T4 at all.",
   "T11/T12 only surface through T3 when a measure-filter literal itself contains `?`: the datasets renderer pastes the literal into the same SQL string that is later handed to substituteParameters (datasets/src/query-planner.ts:68 -> datasets/src/executor.ts:265-269 -> clickhouse-adapter.ts:43), so the cross-package literal gap is hidden while the clickhouse escaper is the only thing under review."
  ],
  "dependency_bump_fix": false,
  "in_repo_fix_possible": true
 },
 "conflicts": [
  {
   "a": "T1",
   "b": "T11",
   "what": "The natural escaping fix for T1 (double backslashes, keep quote doubling) has to be duplicated in T11/T12, but datasets.test.ts:624-632 pins the exact measure-filter SQL `(status = 'completed')`; routing measure filters through placeholders or rewriting them instead of escaping breaks that pinned output and the sum()-takes-a-column-string contract."
  },
  {
   "a": "T5",
   "b": "T1",
   "what": "Blanket-parenthesising composed fragments to close T5-T7 changes the exact SQL that the escaping suite pins (query-builder.where.test.ts:33, 307, 370, 414, 449 and query-builder-analytics.test.ts:69-78), so the composition guard must wrap only fragments carrying top-level AND/OR and leave condition values and flat sequences untouched."
  },
  {
   "a": "T16",
   "b": "T1",
   "what": "Extending the escaping rule to the sql tag closes T16 on paper but breaks the test-pinned verbatim interpolation (sql-tag.test.ts:17-22) and the documented trusted-SQL authoring route (DATASETS_AND_METRICS_SPEC.md:890-891); any rule for T1/T2 must stop at the documented raw-SQL entry points."
  }
 ],
 "fairness_risks": [
  "The sql tagged template must keep inserting interpolated strings verbatim (sql-tag.test.ts:17-22) and custom sql in field definitions is declared trusted code (DATASETS_AND_METRICS_SPEC.md:891); a security rule that escapes every interpolated string contradicts a documented, test-pinned authoring API.",
  "expr.raw(), .raw() and .having() fragments must stay byte-identical (query-builder-analytics.test.ts:69-78, query-builder.where.test.ts:427-434); blanket escaping or blanket wrapping breaks them.",
  "Quote doubling for single quotes is pinned (query-builder.where.test.ts:33, 307): switching the quote escape to a backslash form for T1 breaks existing output, so backslash doubling must be added on top of doubling.",
  "Flat AND/OR sequences are pinned as intentional SQL (query-builder.where.test.ts:275, 291), so the composition fix must not parenthesise ordinary conditions.",
  "Filtered-measure SQL is pinned exactly (datasets.test.ts:624-632), so T11/T12 must add backslash handling without changing the simple-value rendering.",
  "formatDateTime output is pinned with single-quoted format and timezone literals (sql-expressions.test.ts:43-56), so any escaping in T13 must leave the common case unchanged.",
  "substituteParameters must return parameterless SQL untouched (utils.ts:17-19); a scanner must not rewrite SQL that has no parameters, otherwise rawQuery and every parameterless builder query change.",
  "Refused input shapes that legitimate uses need: rendering object/array values is the only route for a developer to bind JSON today (utils.ts:11-13), null must still render, and `?` characters legitimately appear in LIKE patterns and comments of developer SQL."
 ],
 "effort_minutes": 95,
 "usable": true,
 "design": {
  "traps": [
   "T1",
   "T3",
   "T5",
   "T9",
   "T11"
  ],
  "why": "Five independent groups, each needing a different judgement rather than a different spelling of one. T1 is the reported anchor (escapeValue's string literal) with no dismissal; T3 is the lexical placeholder split in the same file, dismissed as developer-authored SQL, and needs a real scanner that understands quotes, comments and heredocs; T5 is the composition group where a fragment with top-level AND/OR is spliced into a flat sequence, dismissed as a documented raw-SQL escape hatch and punished by pinned exact SQL if over-hardened; T9 is the identifier sink for CTE aliases in a different feature module, dismissed as developer-chosen names and easy to miss because the sibling withScalar alias is already validated; T11 is the second, duplicated literal renderer in another package, dismissed as trusted developer measure filters and invisible to anyone who only audits the clickhouse escaper. Deepseek-type groups are T3, T9 and T11 (absent protection plus a dismissal), and T5 is the clean mimo-type group (coupled exact-SQL), so both model failure modes are probed; the groups span three packages and five modules, and the distance-0 anchor keeps the task solvable while the far sites do the stacking work. T16 and T17 are left out of the design: T16 is the project's documented raw-SQL authoring API and would be unfair to require, and T17's request paths are all whitelisted before SQL generation."
 },
 "unverified": [
  "No fix.diff is present under the worktree, so the fix-site attribution in the screener could not be re-read; trap origins that say published_fix_far_site rest on the screener record plus the pinned sinks.",
  "The screener records a fix-diff base mismatch: the predicate-builder.ts and query-builder.ts hunks import assertSafeIdentifier from './utils/insert-identifiers.js' and query-builder.ts also imports './insert-builder.js', and neither module exists at the pinned commit (packages/clickhouse/src/core/utils/ contains no insert-identifiers.ts). The identifier traps T8/T9/T10/T14/T17 therefore rest on reading the pinned interpolation sinks, not on an applied diff.",
  "The fix's new utils/sql-parens.ts is absent from the pinned tree; the composition traps T5-T7 are inferred from the pinned unparenthesised joins (sql-formatter.ts:62-73, 179-189; predicate-builder.ts:152) plus the screener's fix_sites.",
  "ClickHouse's runtime acceptance of a trailing backslash inside a single-quoted literal was not executed (no project code was run); the T1 claim rests on ClickHouse's default backslash-escape handling, the screener's changelog note, and the project's own escapeStringLiteral precedent in packages/schema/src/sql/render.ts:394-405.",
  "O8b siblings that are not recorded as traps because they are not real at the pinned commit: the IN/array renderers already emit `?` placeholders (sql-formatter.ts:107, 119, 152); features/aggregations.ts has no countIf helper; ClickHouseDialect.formatSettings (clickhouse-dialect.ts:78-82) is never called from compileQuery and is dead as an injection route today.",
  "O4 repo_mb could not be measured (no shell), so the tiny/giant-repo prior was not evaluated.",
  "Whether hidden behavioural tests exercise the datasets/serve measure-filter renderers (T11/T12) or the select-expression helpers (T13/T14) is unknown; none of those sites appears in the screener's fix_sites.",
  "The claim that measure filters are developer-authored rests on measure.ts, types.ts, query-planner.ts and DATASETS_AND_METRICS_SPEC.md:891, not on tracing every request path; the request-facing metric filter path goes through builder.where() with `?` placeholders instead (metric-endpoint.ts:150-158, datasets/src/executor.ts:307-316).",
  "The screener's kind list includes M6; I recorded the measure-definition producer path (query-planner.ts:68) as part of the M2 duplicate-renderer traps T11/T12 rather than as a separate M6 trap, because the same one-line literal renderer is what the producer feeds."
 ]
}
  ```
- Published fix sites:   - packages/clickhouse/src/core/utils.ts:8 — T1 M8 (reason to dismiss: none)
  - packages/clickhouse/src/core/utils.ts:11-13 — T2 M4 (reason to dismiss: Object/array values are developer-supplied structured data and a JSON payload is not a value shape ClickHouse columns accept, so the fallback branch is read as a convenience rather than a user-data route.)
  - packages/clickhouse/src/core/utils.ts:5-6 — T2 M4 (reason to dismiss: Object/array values are developer-supplied structured data and a JSON payload is not a value shape ClickHouse columns accept, so the fallback branch is read as a convenience rather than a user-data route.)
  - packages/clickhouse/src/core/utils.ts:20 — T3 M8 (reason to dismiss: The SQL text is developer-authored; a `?` inside a quoted literal or comment is a coding error and the placeholder/parameter count check throws instead of executing.)
  - packages/clickhouse/src/core/features/analytics.ts:26 — T4 M7 (reason to dismiss: Scalar expressions are developer-authored CTE definitions built from literals and column references, and rendering their parameters at build time is deliberate so the CTE text matches the expression.)
  - packages/clickhouse/src/core/formatters/sql-formatter.ts:62-73 — T5 M4 (reason to dismiss: expr.raw() and .raw() values are documented raw-SQL escape hatches, and the project's where tests pin the exact flat SQL, so a solver can argue composition is the caller's responsibility.)
  - packages/clickhouse/src/core/features/filtering.ts:107-124 — T5 M4 (reason to dismiss: expr.raw() and .raw() values are documented raw-SQL escape hatches, and the project's where tests pin the exact flat SQL, so a solver can argue composition is the caller's responsibility.)
  - packages/clickhouse/src/core/formatters/sql-formatter.ts:179-189 — T6 M4 (reason to dismiss: having() and .raw() take raw SQL text by design and several fragments are already documented as joined with AND, so the fragment text is treated as the caller's syntax.)
  - packages/clickhouse/src/core/query-builder.ts:412-417 — T6 M4 (reason to dismiss: having() and .raw() take raw SQL text by design and several fragments are already documented as joined with AND, so the fragment text is treated as the caller's syntax.)
  - packages/clickhouse/src/core/features/query-modifiers.ts:78-93 — T6 M4 (reason to dismiss: having() and .raw() take raw SQL text by design and several fragments are already documented as joined with AND, so the fragment text is treated as the caller's syntax.)
  - packages/clickhouse/src/core/utils/predicate-builder.ts:144-155 — T7 M4 (reason to dismiss: buildLogical already parenthesises every child expression, so the expression is unambiguous on its own; the remaining risk appears only when a caller mixes it into a flat sequence, which is the caller's composition.)
  - packages/clickhouse/src/core/formatters/sql-formatter.ts:45-49 — T7 M4 (reason to dismiss: buildLogical already parenthesises every child expression, so the expression is unambiguous on its own; the remaining risk appears only when a caller mixes it into a flat sequence, which is the caller's composition.)
  - packages/clickhouse/src/core/utils/predicate-builder.ts:139 — T8 M4 (reason to dismiss: fn() names are developer constants written in application code, not request input, so no runtime allowlist is expected.)
  - packages/clickhouse/src/core/utils/predicate-builder.ts:159-160 — T8 M4 (reason to dismiss: fn() names are developer constants written in application code, not request input, so no runtime allowlist is expected.)
  - packages/clickhouse/src/core/features/analytics.ts:20 — T9 M4 (reason to dismiss: CTE aliases are developer-chosen identifiers written at the call site, and the sibling withScalar path already enforces an identifier regex, so the API looks consistently trusted.)
  - packages/clickhouse/src/core/query-builder.ts:355-360 — T9 M4 (reason to dismiss: CTE aliases are developer-chosen identifiers written at the call site, and the sibling withScalar path already enforces an identifier regex, so the API looks consistently trusted.)
  - packages/clickhouse/src/dataset/sql-tag.ts:48-51 — T16 M1 (reason to dismiss: The published fix re-documented the sql tag as an intentional raw-SQL authoring API and the project pins verbatim interpolation, so it is treated as developer code rather than a to-be-escaped sink.)
- Uncovered routes to confirm (pattern B):   - packages/clickhouse/src/core/features/aggregations.ts:61 — T10 M4 (reason to dismiss: Aggregate aliases and columns are typed by schema-derived TypeScript template literals, so they are compile-time-trusted identifiers rather than runtime data.)
  - packages/clickhouse/src/core/features/aggregations.ts:99 — T10 M4 (reason to dismiss: Aggregate aliases and columns are typed by schema-derived TypeScript template literals, so they are compile-time-trusted identifiers rather than runtime data.)
  - packages/datasets/src/utils/filtered-aggregation-sql.ts:12 — T11 M2 (reason to dismiss: Measure-level filter values are developer-authored in the measure definition and the project spec calls custom SQL in field definitions trusted code, so this literal renderer is read as a second, developer-only implementation.)
  - packages/datasets/src/utils/filtered-aggregation-sql.ts:56 — T11 M2 (reason to dismiss: Measure-level filter values are developer-authored in the measure definition and the project spec calls custom SQL in field definitions trusted code, so this literal renderer is read as a second, developer-only implementation.)
  - packages/datasets/src/utils/filtered-aggregation-sql.ts:64 — T11 M2 (reason to dismiss: Measure-level filter values are developer-authored in the measure definition and the project spec calls custom SQL in field definitions trusted code, so this literal renderer is read as a second, developer-only implementation.)
  - packages/serve/src/semantic/datasets/utils/filtered-aggregation-sql.ts:22 — T12 M2 (reason to dismiss: This is a byte-for-byte copy of the datasets renderer fed from the same developer-authored measure definitions, so the same trusted-code argument applies and a solver who fixed the datasets copy sees no reason to open the second one.)
  - packages/serve/src/semantic/datasets/utils/filtered-aggregation-sql.ts:67 — T12 M2 (reason to dismiss: This is a byte-for-byte copy of the datasets renderer fed from the same developer-authored measure definitions, so the same trusted-code argument applies and a solver who fixed the datasets copy sees no reason to open the second one.)
  - packages/serve/src/semantic/datasets/utils/filtered-aggregation-sql.ts:75 — T12 M2 (reason to dismiss: This is a byte-for-byte copy of the datasets renderer fed from the same developer-authored measure definitions, so the same trusted-code argument applies and a solver who fixed the datasets copy sees no reason to open the second one.)
  - packages/clickhouse/src/core/utils/sql-expressions.ts:106-110 — T13 M4 (reason to dismiss: Format strings, timezones and intervals are code-level constants passed to SELECT-expression helpers, and ClickHouse requires them inside literal or INTERVAL syntax.)
  - packages/clickhouse/src/core/utils/sql-expressions.ts:128 — T13 M4 (reason to dismiss: Format strings, timezones and intervals are code-level constants passed to SELECT-expression helpers, and ClickHouse requires them inside literal or INTERVAL syntax.)
  - packages/clickhouse/src/core/dialects/clickhouse-dialect.ts:70-76 — T13 M4 (reason to dismiss: Format strings, timezones and intervals are code-level constants passed to SELECT-expression helpers, and ClickHouse requires them inside literal or INTERVAL syntax.)
  - packages/clickhouse/src/core/utils/sql-expressions.ts:49-56 — T14 M4 (reason to dismiss: rawAs()/selectExpr() are the documented select-expression escape hatch and the alias is a developer-chosen label, not request data.)
  - packages/clickhouse/src/core/formatters/sql-formatter.ts:123-140 — T15 M4 (reason to dismiss: inSubquery/inTable values are documented as raw subquery and table SQL strings, not as bound values, and the operator names say so.)
  - packages/clickhouse/src/core/features/filtering.ts:83-92 — T15 M4 (reason to dismiss: inSubquery/inTable values are documented as raw subquery and table SQL strings, not as bound values, and the operator names say so.)
  - packages/clickhouse/src/core/formatters/sql-formatter.ts:31-39 — T17 M4 (reason to dismiss: Table names, join aliases, order/limit-by columns and select expressions all originate from schema-typed columns or builder arguments, and every request-facing path whitelists field names first.)
  - packages/clickhouse/src/core/formatters/sql-formatter.ts:205-234 — T17 M4 (reason to dismiss: Table names, join aliases, order/limit-by columns and select expressions all originate from schema-typed columns or builder arguments, and every request-facing path whitelists field names first.)
- Design plan from the lead: TRACK = STACKED (H4). Build the stacked design the reader chose: traps T1, T3, T5, T9, T11. Why: Five independent groups, each needing a different judgement rather than a different spelling of one. T1 is the reported anchor (escapeValue's string literal) with no dismissal; T3 is the lexical placeholder split in the same file, dismissed as developer-authored SQL, and needs a real scanner that understands quotes, comments and heredocs; T5 is the composition group where a fragment with top-level AND/OR is spliced into a flat sequence, dismissed as a documented raw-SQL escape hatch and punished by pinned exact SQL if over-hardened; T9 is the identifier sink for CTE aliases in a different feature module, dismissed as developer-chosen names and easy to miss because the sibling withScalar alias is already validated; T11 is the second, duplicated literal renderer in another package, dismissed as trusted developer measure filters and invisible to anyone who only audits the clickhouse escaper. Deepseek-type groups are T3, T9 and T11 (absent protection plus a dismissal), and T5 is the clean mimo-type group (coupled exact-SQL), so both model failure modes are probed; the groups span three packages and five modules, and the distance-0 anchor keeps the task solvable while the far sites do the stacking work. T16 and T17 are left out of the design: T16 is the project's documented raw-SQL authoring API and would be unfair to require, and T17's request paths are all whitelisted before SQL generation. Follow the stacked-task rules appended at the end of this prompt; they add to the rules above.
- Host notes: Reader fairness risks (resolve each in the report's contracts or the tests): The sql tagged template must keep inserting interpolated strings verbatim (sql-tag.test.ts:17-22) and custom sql in field definitions is declared trusted code (DATASETS_AND_METRICS_SPEC.md:891); a security rule that escapes every interpolated string contradicts a documented, test-pinned authoring API. | expr.raw(), .raw() and .having() fragments must stay byte-identical (query-builder-analytics.test.ts:69-78, query-builder.where.test.ts:427-434); blanket escaping or blanket wrapping breaks them. | Quote doubling for single quotes is pinned (query-builder.where.test.ts:33, 307): switching the quote escape to a backslash form for T1 breaks existing output, so backslash doubling must be added on top of doubling. | Flat AND/OR sequences are pinned as intentional SQL (query-builder.where.test.ts:275, 291), so the composition fix must not parenthesise ordinary conditions. | Filtered-measure SQL is pinned exactly (datasets.test.ts:624-632), so T11/T12 must add backslash handling without changing the simple-value rendering. | formatDateTime output is pinned with single-quoted format and timezone literals (sql-expressions.test.ts:43-56), so any escaping in T13 must leave the common case unchanged. | substituteParameters must return parameterless SQL untouched (utils.ts:17-19); a scanner must not rewrite SQL that has no parameters, otherwise rawQuery and every parameterless builder query change. | Refused input shapes that legitimate uses need: rendering object/array values is the only route for a developer to bind JSON today (utils.ts:11-13), null must still render, and `?` characters legitimately appear in LIKE patterns and comments of developer SQL.. Conflicts the reader found: The natural escaping fix for T1 (double backslashes, keep quote doubling) has to be duplicated in T11/T12, but datasets.test.ts:624-632 pins the exact measure-filter SQL `(status = 'completed')`; routing measure filters through placeholders or rewriting them instead of escaping breaks that pinned output and the sum()-takes-a-column-string contract. | Blanket-parenthesising composed fragments to close T5-T7 changes the exact SQL that the escaping suite pins (query-builder.where.test.ts:33, 307, 370, 414, 449 and query-builder-analytics.test.ts:69-78), so the composition guard must wrap only fragments carrying top-level AND/OR and leave condition values and flat sequences untouched. | Extending the escaping rule to the sql tag closes T16 on paper but breaks the test-pinned verbatim interpolation (sql-tag.test.ts:17-22) and the documented trusted-SQL authoring route (DATASETS_AND_METRICS_SPEC.md:890-891); any rule for T1/T2 must stop at the documented raw-SQL entry points.

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

## Environment (`tasks/stk-hypequery-9256/environment/Dockerfile`)
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

## Report to the solver (`tasks/stk-hypequery-9256/instruction.md`)
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

## Tests (`tasks/stk-hypequery-9256/tests/`)
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
- **Wrong-fix patches** go in `build/stk-hypequery-9256/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/stk-hypequery-9256/`:**
- `instruction.md`;
- `task.toml`, from `common/builder/templates/`, with `[metadata]` (incl. the delivery fields) filled in and
  `network_mode = "no-network"` (no allowlist);
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/stk-hypequery-9256/manifest.json`:**
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

**Also in `build/stk-hypequery-9256/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `common/builder/templates/` and `common/trial/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I common/gate/gate.py stk-hypequery-9256 --only static
python3 -I common/gate/gate.py stk-hypequery-9256 --only nop
python3 -I common/gate/gate.py stk-hypequery-9256 --only oracle
python3 -I common/gate/gate.py stk-hypequery-9256 --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/stk-hypequery-9256/`;
  - edit only `tasks/stk-hypequery-9256/`, `build/stk-hypequery-9256/` and, for pattern B, the register;
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
is missing. The reader's record lists them, with evidence: `/home/mara/cwe-bench/pipelines/stacking/out/reader/h4-9256.json`. Verify each trap on the
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

Stacked task slug: `stk-hypequery-9256`. Control task slug: `stk-hypequery-9256-control`. Manifest `stacking.reader_record`: `pipelines/stacking/out/reader/h4-9256.json`.
