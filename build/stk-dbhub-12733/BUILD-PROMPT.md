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

Project root: `/home/mara/cwe-bench`. Task: `stk-dbhub-12733`. Pattern: `A+B`. Track: `stacked`.

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
- Advisory: 12733; CWE-184 / CWE-636 / CWE-863: an incomplete keyword blacklist used as a
- Pinned (vulnerable) commit: d65c6b424e9d10678fb6f7dda93fba180d7baff9. Published fix: 872bb338f7d31f6afe517a076ac3e3edafaaaf08.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "candidate_id": "h4-12733",
 "pattern": "H4",
 "repo": "bytebase/dbhub",
 "pinned_commit": "d65c6b424e9d10678fb6f7dda93fba180d7baff9",
 "protections": [
  "execute_sql read-only gate: the request is split with splitSQLStatements and every statement's first keyword must be in the per-dialect allow-list after comments/strings are stripped (src/tools/execute-sql.ts:26-29,58-63; src/utils/allowed-keywords.ts:75-123).",
  "Custom-tool read-only gate: the same classifier is applied to the whole operator-configured statement, without splitting (src/tools/custom-tool-handler.ts:186 via src/utils/tool-handler-helpers.ts:36).",
  "Per-execution engine enforcement keyed on ExecuteOptions.readonly, declared in the connector contract but implemented by no connector (src/connectors/interface.ts:62-71).",
  "Connection-level read-only keyed on ConnectorConfig.readonly, implemented only for PostgreSQL (default_transaction_read_only) and SQLite (readOnly open), and unreachable from TOML (src/connectors/postgres/index.ts:175-178; src/connectors/sqlite/index.ts:184-194; src/config/toml-loader.ts:628-634)."
 ],
 "traps": [
  {
   "id": "T1",
   "mechanism": "M4",
   "origin": "advisory_route",
   "locations": [
    "src/connectors/postgres/index.ts:598",
    "src/connectors/postgres/index.ts:608",
    "src/connectors/postgres/index.ts:616",
    "src/connectors/postgres/index.ts:624",
    "src/connectors/postgres/index.ts:639",
    "src/connectors/postgres/index.ts:645"
   ],
   "reason_to_dismiss": "src/connectors/interface.ts:66-70 defines ExecuteOptions.readonly as application-level keyword validation already performed at the tool gate, and docs/tools/execute-sql.mdx:129 calls read-only mode a safety net rather than a security boundary, so the connector reads as the wrong layer.",
   "distance": {
    "files": 2,
    "packages": 1
   },
   "protection_state": "absent",
   "tier_deepseek": "hard",
   "tier_mimo": "hard",
   "type": "deepseek",
   "evidence": [
    "src/connectors/interface.ts:62-71",
    "src/tools/execute-sql.ts:58-71",
    "docs/tools/execute-sql.mdx:129",
    "src/connectors/postgres/index.ts:598-666"
   ]
  },
  {
   "id": "T2",
   "mechanism": "M2",
   "origin": "published_fix_far_site",
   "locations": [
    "src/connectors/mariadb/index.ts:593",
    "src/connectors/mariadb/index.ts:600",
    "src/connectors/mariadb/index.ts:623",
    "src/connectors/mariadb/index.ts:631"
   ],
   "reason_to_dismiss": "The mariadb connector is a line-for-line mirror of the mysql one and both are registered implementations of the same interface, so a fix made in src/connectors/mysql/index.ts is assumed to cover it.",
   "distance": {
    "files": 2,
    "packages": 1
   },
   "protection_state": "absent",
   "tier_deepseek": "medium",
   "tier_mimo": "medium",
   "type": "both",
   "evidence": [
    "src/connectors/mariadb/index.ts:1-19",
    "src/connectors/mysql/index.ts:1-19",
    "src/connectors/mariadb/index.ts:53",
    "src/connectors/mysql/index.ts:54"
   ]
  },
  {
   "id": "T3",
   "mechanism": "M4",
   "origin": "advisory_route",
   "locations": [
    "src/connectors/mysql/index.ts:606",
    "src/connectors/mysql/index.ts:613",
    "src/connectors/mysql/index.ts:636",
    "src/connectors/mysql/index.ts:644"
   ],
   "reason_to_dismiss": "MySQL is the dialect the tool gate already splits and classifies statement by statement, and the pooled connection is borrowed and released per call, so a guard inside executeSQL looks redundant.",
   "distance": {
    "files": 1,
    "packages": 1
   },
   "protection_state": "absent",
   "tier_deepseek": "medium",
   "tier_mimo": "medium",
   "type": "deepseek",
   "evidence": [
    "src/connectors/mysql/index.ts:606-662",
    "src/connectors/mysql/index.ts:54",
    "src/connectors/interface.ts:66-70"
   ]
  },
  {
   "id": "T4",
   "mechanism": "M4",
   "origin": "advisory_route",
   "locations": [
    "src/connectors/sqlite/index.ts:451",
    "src/connectors/sqlite/index.ts:464",
    "src/connectors/sqlite/index.ts:500",
    "src/connectors/sqlite/index.ts:508",
    "src/connectors/sqlite/index.ts:545"
   ],
   "reason_to_dismiss": "SQLite keeps one process-local handle opened at connect and a :memory: database cannot be opened read-only (src/connectors/sqlite/index.ts:185,192), so read-only can only be a keyword decision made above the connector.",
   "distance": {
    "files": 1,
    "packages": 1
   },
   "protection_state": "absent",
   "tier_deepseek": "hard",
   "tier_mimo": "hard",
   "type": "both",
   "evidence": [
    "src/connectors/sqlite/index.ts:184-196",
    "src/connectors/sqlite/index.ts:451-565",
    "src/connectors/interface.ts:85"
   ]
  },
  {
   "id": "T5",
   "mechanism": "M4",
   "origin": "uncovered_upstream",
   "locations": [
    "src/connectors/sqlserver/index.ts:609",
    "src/connectors/sqlserver/index.ts:633",
    "src/connectors/sqlserver/index.ts:677"
   ],
   "reason_to_dismiss": "T-SQL has no READ ONLY transaction, mssql is an optional driver, the published fix is scoped to the four dialects it patched, and the product docs call read-only mode a safety net rather than a security boundary (docs/tools/execute-sql.mdx:129).",
   "distance": {
    "files": 1,
    "packages": 1
   },
   "protection_state": "absent",
   "tier_deepseek": "xhard",
   "tier_mimo": "hard",
   "type": "deepseek",
   "evidence": [
    "src/connectors/sqlserver/index.ts:609-695",
    "src/connectors/sqlserver/index.ts:618-623",
    "src/connectors/sqlserver/index.ts:711-725"
   ]
  },
  {
   "id": "T6",
   "mechanism": "M11",
   "origin": "injection_room",
   "locations": [
    "src/utils/allowed-keywords.ts:13",
    "src/utils/allowed-keywords.ts:89",
    "src/connectors/sqlite/index.ts:468",
    "src/connectors/sqlite/index.ts:532"
   ],
   "reason_to_dismiss": "pragma is SQLite's introspection keyword and the pinned unit test requires PRAGMA table_info(users) to be read-only (src/utils/__tests__/allowed-keywords.test.ts:62-63), so rejecting pragmas or their parenthesised/equals forms would break legitimate schema discovery.",
   "distance": {
    "files": 2,
    "packages": 2
   },
   "protection_state": "weak",
   "tier_deepseek": "medium",
   "tier_mimo": "xhard",
   "type": "mimo",
   "evidence": [
    "src/utils/allowed-keywords.ts:75-80",
    "src/utils/allowed-keywords.ts:89-96",
    "src/connectors/sqlite/index.ts:464-472",
    "src/utils/__tests__/allowed-keywords.test.ts:62-63"
   ]
  },
  {
   "id": "T7",
   "mechanism": "M11",
   "origin": "injection_room",
   "locations": [
    "src/connectors/sqlite/index.ts:192",
    "src/connectors/sqlite/index.ts:196",
    "src/connectors/mysql/index.ts:613",
    "src/connectors/mysql/index.ts:660",
    "src/connectors/mariadb/index.ts:600",
    "src/connectors/manager.ts:231",
    "src/connectors/manager.ts:262",
    "src/connectors/postgres/index.ts:176"
   ],
   "reason_to_dismiss": "A source configured for read-only is read-only for every tool on it, so switching the connection or session at connect time is simpler and is assumed to cover every call.",
   "distance": {
    "files": 4,
    "packages": 1
   },
   "protection_state": "absent",
   "tier_deepseek": "medium",
   "tier_mimo": "xhard",
   "type": "mimo",
   "evidence": [
    "src/connectors/manager.ts:231-262",
    "src/connectors/postgres/index.ts:175-178",
    "src/connectors/sqlite/index.ts:186-196",
    "src/connectors/mysql/index.ts:613-660",
    "src/connectors/mariadb/index.ts:600-643"
   ]
  },
  {
   "id": "T8",
   "mechanism": "M1",
   "origin": "uncovered_upstream",
   "locations": [
    "src/tools/custom-tool-handler.ts:186",
    "src/utils/tool-handler-helpers.ts:36",
    "src/utils/allowed-keywords.ts:94"
   ],
   "reason_to_dismiss": "The statement is operator-authored TOML, the parameters are bound (src/tools/custom-tool-handler.ts:193-203), and docs/tools/custom-tools.mdx:233-252 say custom tools are not affected by execute_sql's readonly setting, so the route is not attacker-controlled.",
   "distance": {
    "files": 1,
    "packages": 1
   },
   "protection_state": "weak",
   "tier_deepseek": "xhard",
   "tier_mimo": "medium",
   "type": "deepseek",
   "evidence": [
    "src/tools/custom-tool-handler.ts:179-203",
    "src/tools/execute-sql.ts:26-29",
    "src/utils/allowed-keywords.ts:96-122",
    "docs/tools/custom-tools.mdx:233"
   ]
  },
  {
   "id": "T9",
   "mechanism": "M8",
   "origin": "advisory_route",
   "locations": [
    "src/utils/sql-parser.ts:15",
    "src/utils/sql-parser.ts:135",
    "src/utils/sql-parser.ts:168"
   ],
   "reason_to_dismiss": "Two dashes begin a comment in SQL, so the whitespace/control-character nuance of MySQL and MariaDB reads as an obscure lexical detail that the connector-level backstop will cover anyway.",
   "distance": {
    "files": 2,
    "packages": 2
   },
   "protection_state": "weak",
   "tier_deepseek": "hard",
   "tier_mimo": "hard",
   "type": "mimo",
   "evidence": [
    "src/utils/sql-parser.ts:15-20",
    "src/utils/sql-parser.ts:214-237",
    "src/connectors/mysql/index.ts:54",
    "src/connectors/mariadb/index.ts:53",
    "src/tools/execute-sql.ts:27",
    "src/utils/allowed-keywords.ts:77"
   ]
  },
  {
   "id": "T10",
   "mechanism": "M6",
   "origin": "published_fix_far_site",
   "locations": [
    "src/connectors/manager.ts:245",
    "src/connectors/manager.ts:247",
    "src/config/toml-loader.ts:629",
    "src/types/config.ts:49"
   ],
   "reason_to_dismiss": "Connection-level read-only already exists for PostgreSQL (src/connectors/postgres/index.ts:175-178) and SQLite (src/connectors/sqlite/index.ts:184-194), so the lower layer looks partly covered and the per-tool check above it looks sufficient.",
   "distance": {
    "files": 3,
    "packages": 2
   },
   "protection_state": "weak",
   "tier_deepseek": "hard",
   "tier_mimo": "hard",
   "type": "deepseek",
   "evidence": [
    "src/connectors/manager.ts:245-248",
    "src/config/toml-loader.ts:628-634",
    "src/types/config.ts:49-59",
    "src/tools/registry.ts:212-221",
    "src/tools/execute-sql.ts:56-71"
   ]
  },
  {
   "id": "T11",
   "mechanism": "M8",
   "origin": "advisory_route",
   "locations": [
    "src/utils/allowed-keywords.ts:89",
    "src/utils/allowed-keywords.ts:106",
    "src/connectors/postgres/index.ts:616"
   ],
   "reason_to_dismiss": "The statement starts with SELECT, the documented read-only keyword, and what a called function does to the database is the database's business, not the classifier's.",
   "distance": {
    "files": 2,
    "packages": 2
   },
   "protection_state": "weak",
   "tier_deepseek": "hard",
   "tier_mimo": "hard",
   "type": "mimo",
   "evidence": [
    "src/utils/allowed-keywords.ts:75-123",
    "src/connectors/postgres/index.ts:608-627",
    "src/tools/execute-sql.ts:26-29"
   ]
  }
 ],
 "independent_groups": [
  [
   "T1",
   "T10",
   "T11"
  ],
  [
   "T2"
  ],
  [
   "T3"
  ],
  [
   "T4",
   "T7"
  ],
  [
   "T5"
  ],
  [
   "T6"
  ],
  [
   "T8"
  ],
  [
   "T9"
  ]
 ],
 "history": {
  "a_fix_leaves_b_open": true,
  "b_in_code_a_wrote": false,
  "masking": [
   "Once a connector rejects the write at execution time, a hidden test that only asserts the write failed passes while the classifier still accepts SQLite PRAGMA setters (T6) and the MySQL/MariaDB dash-dash form (T9), so the tool gate's own contract (READONLY_VIOLATION) is no longer observed.",
   "The connect-time producer path (T10) is dead config: src/config/toml-loader.ts:628-634 rejects a source-level readonly and src/types/config.ts:49-59 has no field, so once per-execution enforcement works no test observes that the connection-level path never fires."
  ],
  "dependency_bump_fix": false,
  "in_repo_fix_possible": true
 },
 "conflicts": [
  {
   "a": "T1",
   "b": "T7",
   "what": "The simplest backstop for T1 (connection- or session-wide read-only: default_transaction_read_only, a session read-only flag, node:sqlite readOnly, PRAGMA query_only left on) breaks a writable tool on the same source, because there is one connector instance per source (src/connectors/manager.ts:231,262) and pooled connections are reused (src/connectors/mysql/index.ts:613,660) \u2014 exactly the coupled value T7 protects."
  },
  {
   "a": "T6",
   "b": "T4",
   "what": "Closing the PRAGMA setter hole by rejecting every pragma that carries an equals sign or parentheses also rejects PRAGMA table_info(users), which the pinned unit test (src/utils/__tests__/allowed-keywords.test.ts:62-63) and the SQLite connector's read classification (src/connectors/sqlite/index.ts:464-472) require."
  }
 ],
 "fairness_risks": [
  "PRAGMA table_info(users) must stay read-only-allowed (src/utils/__tests__/allowed-keywords.test.ts:62-63) while PRAGMA setters are the hole in T6; a reject-all-pragma rule contradicts a pinned test.",
  "EXPLAIN DELETE FROM users must stay allowed (src/utils/__tests__/allowed-keywords.test.ts:171-173) while EXPLAIN ANALYZE with DML must be rejected (src/utils/__tests__/allowed-keywords.test.ts:176-198); a rule that descends into the statement under EXPLAIN breaks the first.",
  "SELECT REPLACE(name,'a','b') must stay allowed (src/utils/__tests__/allowed-keywords.test.ts:75-82); a blanket rejection of the replace token breaks it.",
  "Tools with readonly false or undefined on the same source must keep writing (src/tools/__tests__/execute-sql.test.ts:215-233), so enforcement has to be per call and a connection-level switch is refused.",
  "A :memory: SQLite source cannot be opened read-only (src/connectors/sqlite/index.ts:185,192); an open-read-only rule breaks in-memory databases.",
  "MySQL/MariaDB executable comments /*! ... */ and /*M! ... */ must stay executable text (src/utils/__tests__/sql-parser.test.ts:49-73); a strip-all-comments simplification contradicts existing pinned behaviour.",
  "The custom-tool statement is operator-authored TOML with bound parameters (src/tools/custom-tool-handler.ts:193-203), so a rule that splits it at semicolons refuses a shape only an operator can produce \u2014 low security value, real fairness cost."
 ],
 "effort_minutes": 75,
 "usable": true,
 "design": {
  "traps": [
   "T1",
   "T2",
   "T4",
   "T6",
   "T9"
  ],
  "why": "Five independent fix sites across four layers, each with a different reason to leave it alone: the Postgres connector never consumes ExecuteOptions.readonly on either the single-statement or the batch path (M4, dismissal: the interface says this is application-level work already done above); MariaDB is a separately written connector that a MySQL fix does not reach (M2, dismissal: it mirrors MySQL); the SQLite connector has the same missing enforcement behind a shared in-process handle (M4, dismissal: :memory: cannot be opened read-only); the SQLite PRAGMA allow-list entry makes every pragma form read-only, coupled to the pinned PRAGMA table_info test (M11, MiMo-style over-hardening); and the two-dash comment scanner mis-splits exactly the MySQL/MariaDB form the engine executes (M8, how-type). It beats the alternatives because it needs no SQL Server instance, every trap is exercised by a site the published fix itself touches, and the two must-keep-working values (PRAGMA table_info, writable tools on the same source) make the naive over-broad fixes fail visibly. T5 (SQL Server, absent backstop plus the strongest dismissal) is the best extra reasoning trap but needs an injected sqlserver test and a well-specified T-SQL guard, so it is the first add-on rather than part of the core; T8 (custom tool) is excluded because its input is operator-authored; T10 and T11 are sub-decisions inside the T1 group (wrong layer and first-keyword-only shapes)."
 },
 "unverified": [
  "The published fix commit 872bb338f7d31f6afe517a076ac3e3edafaaaf08 was not readable in this worktree (HEAD is the pinned commit), so the claim that the fix adds a per-execution engine backstop in four connectors comes from the screener record, not from code.",
  "Whether a READ ONLY transaction permits EXPLAIN of a DML statement on PostgreSQL or MySQL was reasoned from documentation only; no database was run.",
  "SQL Server reachability of a write through the keyword gate was reasoned from code only; no SQL Server instance was run, and the connector's EXPLAIN path (src/connectors/sqlserver/index.ts:711-754) was not executed.",
  "The exact number of distinct fix hunks (16 per the candidate metadata) was not reconciled site-by-site; the sites recorded here are the ones groundable in the pinned tree.",
  "Repository size was not measured in this environment."
 ]
}
  ```
- Published fix sites:   - src/connectors/postgres/index.ts:598 — T1 M4 (reason to dismiss: src/connectors/interface.ts:66-70 defines ExecuteOptions.readonly as application-level keyword validation already performed at the tool gate, and docs/tools/execute-sql.mdx:129 calls read-only mode a safety net rather than a security boundary, so the connector reads as the wrong layer.)
  - src/connectors/postgres/index.ts:608 — T1 M4 (reason to dismiss: src/connectors/interface.ts:66-70 defines ExecuteOptions.readonly as application-level keyword validation already performed at the tool gate, and docs/tools/execute-sql.mdx:129 calls read-only mode a safety net rather than a security boundary, so the connector reads as the wrong layer.)
  - src/connectors/postgres/index.ts:616 — T1 M4 (reason to dismiss: src/connectors/interface.ts:66-70 defines ExecuteOptions.readonly as application-level keyword validation already performed at the tool gate, and docs/tools/execute-sql.mdx:129 calls read-only mode a safety net rather than a security boundary, so the connector reads as the wrong layer.)
  - src/connectors/postgres/index.ts:624 — T1 M4 (reason to dismiss: src/connectors/interface.ts:66-70 defines ExecuteOptions.readonly as application-level keyword validation already performed at the tool gate, and docs/tools/execute-sql.mdx:129 calls read-only mode a safety net rather than a security boundary, so the connector reads as the wrong layer.)
  - src/connectors/postgres/index.ts:639 — T1 M4 (reason to dismiss: src/connectors/interface.ts:66-70 defines ExecuteOptions.readonly as application-level keyword validation already performed at the tool gate, and docs/tools/execute-sql.mdx:129 calls read-only mode a safety net rather than a security boundary, so the connector reads as the wrong layer.)
  - src/connectors/postgres/index.ts:645 — T1 M4 (reason to dismiss: src/connectors/interface.ts:66-70 defines ExecuteOptions.readonly as application-level keyword validation already performed at the tool gate, and docs/tools/execute-sql.mdx:129 calls read-only mode a safety net rather than a security boundary, so the connector reads as the wrong layer.)
  - src/connectors/mariadb/index.ts:593 — T2 M2 (reason to dismiss: The mariadb connector is a line-for-line mirror of the mysql one and both are registered implementations of the same interface, so a fix made in src/connectors/mysql/index.ts is assumed to cover it.)
  - src/connectors/mariadb/index.ts:600 — T2 M2 (reason to dismiss: The mariadb connector is a line-for-line mirror of the mysql one and both are registered implementations of the same interface, so a fix made in src/connectors/mysql/index.ts is assumed to cover it.)
  - src/connectors/mariadb/index.ts:623 — T2 M2 (reason to dismiss: The mariadb connector is a line-for-line mirror of the mysql one and both are registered implementations of the same interface, so a fix made in src/connectors/mysql/index.ts is assumed to cover it.)
  - src/connectors/mariadb/index.ts:631 — T2 M2 (reason to dismiss: The mariadb connector is a line-for-line mirror of the mysql one and both are registered implementations of the same interface, so a fix made in src/connectors/mysql/index.ts is assumed to cover it.)
  - src/connectors/mysql/index.ts:606 — T3 M4 (reason to dismiss: MySQL is the dialect the tool gate already splits and classifies statement by statement, and the pooled connection is borrowed and released per call, so a guard inside executeSQL looks redundant.)
  - src/connectors/mysql/index.ts:613 — T3 M4 (reason to dismiss: MySQL is the dialect the tool gate already splits and classifies statement by statement, and the pooled connection is borrowed and released per call, so a guard inside executeSQL looks redundant.)
  - src/connectors/mysql/index.ts:636 — T3 M4 (reason to dismiss: MySQL is the dialect the tool gate already splits and classifies statement by statement, and the pooled connection is borrowed and released per call, so a guard inside executeSQL looks redundant.)
  - src/connectors/mysql/index.ts:644 — T3 M4 (reason to dismiss: MySQL is the dialect the tool gate already splits and classifies statement by statement, and the pooled connection is borrowed and released per call, so a guard inside executeSQL looks redundant.)
  - src/connectors/sqlite/index.ts:451 — T4 M4 (reason to dismiss: SQLite keeps one process-local handle opened at connect and a :memory: database cannot be opened read-only (src/connectors/sqlite/index.ts:185,192), so read-only can only be a keyword decision made above the connector.)
  - src/connectors/sqlite/index.ts:464 — T4 M4 (reason to dismiss: SQLite keeps one process-local handle opened at connect and a :memory: database cannot be opened read-only (src/connectors/sqlite/index.ts:185,192), so read-only can only be a keyword decision made above the connector.)
  - src/connectors/sqlite/index.ts:500 — T4 M4 (reason to dismiss: SQLite keeps one process-local handle opened at connect and a :memory: database cannot be opened read-only (src/connectors/sqlite/index.ts:185,192), so read-only can only be a keyword decision made above the connector.)
  - src/connectors/sqlite/index.ts:508 — T4 M4 (reason to dismiss: SQLite keeps one process-local handle opened at connect and a :memory: database cannot be opened read-only (src/connectors/sqlite/index.ts:185,192), so read-only can only be a keyword decision made above the connector.)
  - src/connectors/sqlite/index.ts:545 — T4 M4 (reason to dismiss: SQLite keeps one process-local handle opened at connect and a :memory: database cannot be opened read-only (src/connectors/sqlite/index.ts:185,192), so read-only can only be a keyword decision made above the connector.)
  - src/utils/sql-parser.ts:15 — T9 M8 (reason to dismiss: Two dashes begin a comment in SQL, so the whitespace/control-character nuance of MySQL and MariaDB reads as an obscure lexical detail that the connector-level backstop will cover anyway.)
  - src/utils/sql-parser.ts:135 — T9 M8 (reason to dismiss: Two dashes begin a comment in SQL, so the whitespace/control-character nuance of MySQL and MariaDB reads as an obscure lexical detail that the connector-level backstop will cover anyway.)
  - src/utils/sql-parser.ts:168 — T9 M8 (reason to dismiss: Two dashes begin a comment in SQL, so the whitespace/control-character nuance of MySQL and MariaDB reads as an obscure lexical detail that the connector-level backstop will cover anyway.)
  - src/connectors/manager.ts:245 — T10 M6 (reason to dismiss: Connection-level read-only already exists for PostgreSQL (src/connectors/postgres/index.ts:175-178) and SQLite (src/connectors/sqlite/index.ts:184-194), so the lower layer looks partly covered and the per-tool check above it looks sufficient.)
  - src/connectors/manager.ts:247 — T10 M6 (reason to dismiss: Connection-level read-only already exists for PostgreSQL (src/connectors/postgres/index.ts:175-178) and SQLite (src/connectors/sqlite/index.ts:184-194), so the lower layer looks partly covered and the per-tool check above it looks sufficient.)
  - src/config/toml-loader.ts:629 — T10 M6 (reason to dismiss: Connection-level read-only already exists for PostgreSQL (src/connectors/postgres/index.ts:175-178) and SQLite (src/connectors/sqlite/index.ts:184-194), so the lower layer looks partly covered and the per-tool check above it looks sufficient.)
  - src/types/config.ts:49 — T10 M6 (reason to dismiss: Connection-level read-only already exists for PostgreSQL (src/connectors/postgres/index.ts:175-178) and SQLite (src/connectors/sqlite/index.ts:184-194), so the lower layer looks partly covered and the per-tool check above it looks sufficient.)
  - src/utils/allowed-keywords.ts:89 — T11 M8 (reason to dismiss: The statement starts with SELECT, the documented read-only keyword, and what a called function does to the database is the database's business, not the classifier's.)
  - src/utils/allowed-keywords.ts:106 — T11 M8 (reason to dismiss: The statement starts with SELECT, the documented read-only keyword, and what a called function does to the database is the database's business, not the classifier's.)
  - src/connectors/postgres/index.ts:616 — T11 M8 (reason to dismiss: The statement starts with SELECT, the documented read-only keyword, and what a called function does to the database is the database's business, not the classifier's.)
- Uncovered routes to confirm (pattern B):   - src/connectors/sqlserver/index.ts:609 — T5 M4 (reason to dismiss: T-SQL has no READ ONLY transaction, mssql is an optional driver, the published fix is scoped to the four dialects it patched, and the product docs call read-only mode a safety net rather than a security boundary (docs/tools/execute-sql.mdx:129).)
  - src/connectors/sqlserver/index.ts:633 — T5 M4 (reason to dismiss: T-SQL has no READ ONLY transaction, mssql is an optional driver, the published fix is scoped to the four dialects it patched, and the product docs call read-only mode a safety net rather than a security boundary (docs/tools/execute-sql.mdx:129).)
  - src/connectors/sqlserver/index.ts:677 — T5 M4 (reason to dismiss: T-SQL has no READ ONLY transaction, mssql is an optional driver, the published fix is scoped to the four dialects it patched, and the product docs call read-only mode a safety net rather than a security boundary (docs/tools/execute-sql.mdx:129).)
  - src/tools/custom-tool-handler.ts:186 — T8 M1 (reason to dismiss: The statement is operator-authored TOML, the parameters are bound (src/tools/custom-tool-handler.ts:193-203), and docs/tools/custom-tools.mdx:233-252 say custom tools are not affected by execute_sql's readonly setting, so the route is not attacker-controlled.)
  - src/utils/tool-handler-helpers.ts:36 — T8 M1 (reason to dismiss: The statement is operator-authored TOML, the parameters are bound (src/tools/custom-tool-handler.ts:193-203), and docs/tools/custom-tools.mdx:233-252 say custom tools are not affected by execute_sql's readonly setting, so the route is not attacker-controlled.)
  - src/utils/allowed-keywords.ts:94 — T8 M1 (reason to dismiss: The statement is operator-authored TOML, the parameters are bound (src/tools/custom-tool-handler.ts:193-203), and docs/tools/custom-tools.mdx:233-252 say custom tools are not affected by execute_sql's readonly setting, so the route is not attacker-controlled.)
- Design plan from the lead: TRACK = STACKED (H4). Build the stacked design the reader chose: traps T1, T2, T4, T6, T9. Why: Five independent fix sites across four layers, each with a different reason to leave it alone: the Postgres connector never consumes ExecuteOptions.readonly on either the single-statement or the batch path (M4, dismissal: the interface says this is application-level work already done above); MariaDB is a separately written connector that a MySQL fix does not reach (M2, dismissal: it mirrors MySQL); the SQLite connector has the same missing enforcement behind a shared in-process handle (M4, dismissal: :memory: cannot be opened read-only); the SQLite PRAGMA allow-list entry makes every pragma form read-only, coupled to the pinned PRAGMA table_info test (M11, MiMo-style over-hardening); and the two-dash comment scanner mis-splits exactly the MySQL/MariaDB form the engine executes (M8, how-type). It beats the alternatives because it needs no SQL Server instance, every trap is exercised by a site the published fix itself touches, and the two must-keep-working values (PRAGMA table_info, writable tools on the same source) make the naive over-broad fixes fail visibly. T5 (SQL Server, absent backstop plus the strongest dismissal) is the best extra reasoning trap but needs an injected sqlserver test and a well-specified T-SQL guard, so it is the first add-on rather than part of the core; T8 (custom tool) is excluded because its input is operator-authored; T10 and T11 are sub-decisions inside the T1 group (wrong layer and first-keyword-only shapes). Follow the stacked-task rules appended at the end of this prompt; they add to the rules above.
- Host notes: Reader fairness risks (resolve each in the report's contracts or the tests): PRAGMA table_info(users) must stay read-only-allowed (src/utils/__tests__/allowed-keywords.test.ts:62-63) while PRAGMA setters are the hole in T6; a reject-all-pragma rule contradicts a pinned test. | EXPLAIN DELETE FROM users must stay allowed (src/utils/__tests__/allowed-keywords.test.ts:171-173) while EXPLAIN ANALYZE with DML must be rejected (src/utils/__tests__/allowed-keywords.test.ts:176-198); a rule that descends into the statement under EXPLAIN breaks the first. | SELECT REPLACE(name,'a','b') must stay allowed (src/utils/__tests__/allowed-keywords.test.ts:75-82); a blanket rejection of the replace token breaks it. | Tools with readonly false or undefined on the same source must keep writing (src/tools/__tests__/execute-sql.test.ts:215-233), so enforcement has to be per call and a connection-level switch is refused. | A :memory: SQLite source cannot be opened read-only (src/connectors/sqlite/index.ts:185,192); an open-read-only rule breaks in-memory databases. | MySQL/MariaDB executable comments /*! ... */ and /*M! ... */ must stay executable text (src/utils/__tests__/sql-parser.test.ts:49-73); a strip-all-comments simplification contradicts existing pinned behaviour. | The custom-tool statement is operator-authored TOML with bound parameters (src/tools/custom-tool-handler.ts:193-203), so a rule that splits it at semicolons refuses a shape only an operator can produce — low security value, real fairness cost.. Conflicts the reader found: The simplest backstop for T1 (connection- or session-wide read-only: default_transaction_read_only, a session read-only flag, node:sqlite readOnly, PRAGMA query_only left on) breaks a writable tool on the same source, because there is one connector instance per source (src/connectors/manager.ts:231,262) and pooled connections are reused (src/connectors/mysql/index.ts:613,660) — exactly the coupled value T7 protects. | Closing the PRAGMA setter hole by rejecting every pragma that carries an equals sign or parentheses also rejects PRAGMA table_info(users), which the pinned unit test (src/utils/__tests__/allowed-keywords.test.ts:62-63) and the SQLite connector's read classification (src/connectors/sqlite/index.ts:464-472) require.

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

## Environment (`tasks/stk-dbhub-12733/environment/Dockerfile`)
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

## Report to the solver (`tasks/stk-dbhub-12733/instruction.md`)
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

## Tests (`tasks/stk-dbhub-12733/tests/`)
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
- **Wrong-fix patches** go in `build/stk-dbhub-12733/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/stk-dbhub-12733/`:**
- `instruction.md`;
- `task.toml`, from `common/builder/templates/`, with `[metadata]` (incl. the delivery fields) filled in and
  `network_mode = "no-network"` (no allowlist);
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/stk-dbhub-12733/manifest.json`:**
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

**Also in `build/stk-dbhub-12733/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `common/builder/templates/` and `common/trial/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I common/gate/gate.py stk-dbhub-12733 --only static
python3 -I common/gate/gate.py stk-dbhub-12733 --only nop
python3 -I common/gate/gate.py stk-dbhub-12733 --only oracle
python3 -I common/gate/gate.py stk-dbhub-12733 --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/stk-dbhub-12733/`;
  - edit only `tasks/stk-dbhub-12733/`, `build/stk-dbhub-12733/` and, for pattern B, the register;
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
is missing. The reader's record lists them, with evidence: `/home/mara/cwe-bench/pipelines/stacking/out/reader/h4-12733.json`. Verify each trap on the
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

Stacked task slug: `stk-dbhub-12733`. Control task slug: `stk-dbhub-12733-control`. Manifest `stacking.reader_record`: `pipelines/stacking/out/reader/h4-12733.json`.
