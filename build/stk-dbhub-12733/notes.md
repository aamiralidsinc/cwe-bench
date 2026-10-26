# stk-dbhub-12733 — build notes

## Window

- Start (UTC): 2026-10-26T02:07Z (pipeline start file); build work began 2026-10-26T02:10Z.
- End (UTC): filled in when the gate finishes (see the final report).

## Task

`bytebase/dbhub` at `d65c6b424e9d10678fb6f7dda93fba180d7baff9`; published fix
`872bb338f7d31f6afe517a076ac3e3edafaaaf08` (PR #342). The task asks for read-only mode to be
enforced when a statement runs, not only in the admission classifier.

## Levers (one line each)

1. T1 — A, deepseek, `src/connectors/postgres/index.ts:598-666`: the connector never reads
   `ExecuteOptions.readonly`; a function call, a data-selecting CTE or a later batch statement
   writes. Dismissal: the contract calls it application-level validation already done above.
2. T2 — A, both, `src/connectors/mariadb/index.ts:593-643`: the MariaDB connector is a separate
   implementation; a MySQL fix does not reach it. Dismissal: it is a line-for-line mirror.
3. T4 — A, both, `src/connectors/sqlite/index.ts:451-565`: one process-local handle and no per-call
   engine guard; a write handed to a read-only execution runs. Dismissal: `:memory:` cannot be
   opened read-only, so the guard reads as impossible below the gate.
4. T6 — B/how, mimo, `src/utils/allowed-keywords.ts:89-122`: every pragma form is read-only,
   including assignment and parenthesized setters; rejecting pragmas wholesale breaks the
   introspection forms the pinned tests require. Dismissal: `pragma` is the introspection keyword.
5. T9 — A/how, mimo, `src/utils/sql-parser.ts:15-20`: two dashes are always a comment, while
   MySQL/MariaDB need whitespace/control/EOL, so a statement hidden after `--x` is admitted and
   executed. Dismissal: a lexical nuance the execution backstop will catch.
6. T5 — B, deepseek, `src/connectors/sqlserver/index.ts:609-695`: the SQL Server connector has no
   read-only enforcement and the published fix never touches it. Dismissal: T-SQL has no
   READ ONLY transaction and the remediation is scoped to the patched dialects.

Concepts: `[T1] [T2] [T4] [T6] [T9] [T5]` (six independent edit sites). DeepSeek-type: T1, T5.
MiMo-type: T6, T9 (T2/T4 are `both`).

## What I verified

- The advisory text and the four consolidated advisories (one canonical GHSA; GHSA-j656 is the
  separate MySQL/MariaDB comment root cause). The published fix's source diff was fetched from the
  repository; the pinned commit is its parent (`git rev-parse 872bb338^ == d65c6b4`).
- Every security case fails on the pinned tree through the real `execute_sql` handler or the public
  `Connector.executeSQL` contract, and passes on the reference fix. The database stand-ins follow
  the real rules: PostgreSQL read-only transactions, MySQL/MariaDB READ ONLY transactions and
  implicit-commit DDL, SQLite `PRAGMA query_only` (including that it blocks pragma writes but not
  `PRAGMA query_only = OFF`), SQL Server transactional rollback.
- The project's own unit tests for the affected area pass on the pinned tree, on the reference and
  on every check patch (211 functional tests, including `allowed-keywords`, `sql-parser` and
  `execute-sql`).
- All six `security_fail` miss patches leave exactly their concept's security tests failing and all
  functional tests passing; `upstream_fix.patch` (the published fix alone) leaves only the SQL
  Server concept failing; the wrong-fix and alternative patches behave as declared.
- Local layout simulation: the restored `/workspace` with `node_modules` symlinked to a pristine
  dependency tree runs both suites under the same paths `test.sh` uses.

## What I could not verify

- No real PostgreSQL/MySQL/MariaDB/SQL Server instance was run; the connector behaviour is asserted
  against in-process stand-ins that model the engine rules named above. The reference fix's SQL is
  the upstream fix's own SQL, so the engine semantics are the project's documented ones.
- The reader record at `pipelines/stacking/out/reader/h4-12733.json` named in the build prompt does
  not exist; the file actually present is `pipelines/stacking/out/reader-ds/h4-12733.json`, which is
  what `stacking.reader_record` points at.
- Current upstream `main` has since added SQL Server read-only enforcement (transaction + ROLLBACK),
  so T5 is no longer open there; it is open at the pinned commit, which is what the task grades.
- The exact number of published fix hunks was not reconciled; the reference fix is the published
  source diff plus the SQL Server guard, and the recall check proves the published fix alone fails.

## Fairness notes

- The instruction states two protections (admission classification and execution-time enforcement)
  and a refusal contract, and nothing per route. The coupled values (ordinary reads, writable tools,
  SQLite introspection pragmas, existing comment handling) are covered only by the general
  keep-working sentence.
- The SQL Server route is findable from the code: the connector is one of five registered
  implementations and has no read-only branch; the instruction says execution must not weaken the
  decision.
- The security tests accept any refusal shape (thrown error or a silently-effect-free execution) for
  the execution-layer concepts; only the admission concepts assert the product's read-only error,
  which the instruction states as a contract.

## Gate

Main task, run one stage at a time with `common/gate/gate.py --only <stage>`:

- static: PASSED (check_stack: conforming, 6 concepts, pattern H4; strict patch checks and
  the wrong-fix catalogue present).
- nop: PASSED — 19 security tests fail on the pinned tree, 211 functional pass.
- oracle: PASSED — three runs, reward 1.0, identical results.
- patches: PASSED — every check behaved as declared:
  - miss_postgres 0.8421 (3 security failing, 0 functional)
  - miss_mysql_family 0.8421 (3/0)
  - miss_sqlite_engine 0.8947 (2/0)
  - miss_sqlite_pragma 0.6842 (6/0)
  - miss_comment_scanner 0.8947 (2/0)
  - miss_sqlserver 0.8421 (3/0)
  - upstream_fix 0.8421 (3/0; the SQL Server route stays open, so the stack adds something)
  - security_fail_source_only 0.4211 (11/0)
  - functional_fail_refuse_all 0.0 (0/11)
  - functional_fail_overbroad 0.0 (0/4)
  - functional_fail_crash 0.0 (0/1)
  - pass_hardening 1.0, pass_alternative 1.0

Control task: its four security tests cover only the advisory's PostgreSQL route; the same
instruction and the same functional suite. Gate results are recorded in
`build/stk-dbhub-12733-control/` (see the final report).
