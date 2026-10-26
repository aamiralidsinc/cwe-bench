# stk-hypequery-9256 — build notes

Start: 2026-10-26T12:20:49Z (builder launched by `common/launch/run_build.sh`).
End: see the gate report / this file's last edit (2026-10-26, afternoon UTC).

Pinned: `7a9ef6bf4867ef231067ee70b94cad1b2cbc8add` (hypequery/hypequery). Published fixes:
`2dc1df7b` / `4dfa9d77` (the same parameter-escaping fix on two branches) and `2879161a`
(logical-group precedence, issue #348). The stack: 4 concepts, 7 traps, 3 packages.

## Levers (one line each)

| id | concept | pattern | where | reason to dismiss |
|---|---|---|---|---|
| T1 | values | A (advisory) | `packages/clickhouse/src/core/utils.ts:8` | none — the reported route (a bound string ends with a backslash, the closing quote is escaped) |
| T2 | values | B (same advisory, other branch) | `utils.ts:11-13` | structured values are developer data, so the JSON branch looks like a convenience |
| T5 | composition | A (published fix far site) | `utils/predicate-builder.ts:144-155`, `formatters/sql-formatter.ts:45-49,179-189` | raw fragments are documented escape hatches and the project pins their exact SQL; blanket wrapping is the obvious wrong fix |
| T8 | names | B (uncovered) | `utils/predicate-builder.ts:139` | function names are developer constants |
| T9 | names | B (uncovered) | `query-builder.ts:355-360` | CTE aliases are developer-chosen, and the sibling scalar alias is already pattern-checked |
| T17 | names | B (uncovered) | `formatters/sql-formatter.ts:31-39,205-215`, `query-builder.ts:841-895`, `dialects/clickhouse-dialect.ts:73-78` | TypeScript types say columns and whole numbers, and every in-repo caller validates first |
| T11 | second renderer | B (uncovered, other package) | `packages/datasets/src/utils/filtered-aggregation-sql.ts:6-27` | measure filters are authored in the dataset definition, which the spec calls trusted |

Concepts: `[T1,T2]` values, `[T5]` composition, `[T8,T9,T17]` names, `[T11]` second renderer.
DeepSeek-type: T2, T8, T9, T17 (protection never existed, plausible dismissal). MiMo-type: T5
(coupled exact-SQL values punish over-wrapping) and T11 (a second implementation).

## What I verified

- Every lever reproduces on the pinned tree through the real public API (`createQueryBuilder(...).table()... toSQL()/execute()` with a recording ClickHouse client; `MetricExecutor.toSQL` for T11). Generated SQL inspected directly, e.g.
  `name = 'x\'' OR 1=1 --'`, `meta = '{"note":"x' OR 1=1 --"}'`, `tenant = 'acme' AND (owner = 'me') OR (is_public = 1)`,
  `tenant = 'acme' AND 1=1 -- AND status = 'open'`, `LIMIT 10 UNION SELECT 1`, `WITH y AS (SELECT 1), z AS (...)`,
  and the datasets renderer's `SUM(if((status = 'x\'' OR 1=1 --'), amount, 0))`.
- The hidden suites on the pinned code: 27 security tests fail, 31 functional tests pass.
- The reference fix (`solution/fix.patch`): all 58 pass, twice (local runs) — plus the container gate.
- Each miss patch leaves only its concept's security tests failing (10 / 8 / 6 / 3) and all functional tests passing.
- `upstream_fix.patch` (both published fixes ported onto the pinned tree: upstream's own
  `sql-parens.ts` scanner and `escapeValue`, the group/raw/having wrapping, fn-name and CTE-alias
  validation, without our extra routes) fails 7 security tests, functional green. The stack is
  not recalled by upstream's own fix.
- Over-broad fixes are caught: wrapping every condition fails 3 functional tests; refusing every
  value with an unusual character fails 6; escaping the documented `sql` tagged template fails 1.
- An alternative design (character-loop escaping, formatter-layer wrapping, quoted names) passes 58/58.
- Control task: oracle 37/37; nop 6 security failures, 31 functional passes.
- Project suites at the pinned commit: clickhouse 346 pass, datasets 64 pass. After the reference
  fix the clickhouse suite has 3 failures, all exact-SQL expectations that the published fix
  itself rewrote (function-predicate grouping); the graded functional suite asserts the
  equivalent meaning, not that text.
- Current upstream (checked read-only at `edc2fb34`): T8/T9 closed there, T11 moved behind a
  dialect whose `stringLiteral` doubles backslashes, T17 still unvalidated. Register rows appended
  to `build/audit/uncovered-routes.tsv`.

## What I could not verify

- No ClickHouse server was used. The tests judge the generated statement (literal decoding, token
  skeleton, and a WHERE/HAVING evaluator over in-memory rows); ClickHouse's own parsing of the
  escaped literals rests on its documented backslash handling and on upstream's regression tests.
- The serve copy of the measure-filter renderer (`packages/serve/.../filtered-aggregation-sql.ts`)
  is fixed by the reference but not exercised by the hidden suites: driving the serve dataset
  endpoint needs a built `@hypequery/datasets` dist and the full serve runtime. It is the same
  three-line renderer, so no fairness gap, but it is not a tested route.
- The screener's record claims identifier fix sites that do not exist at the pinned commit
  (`utils/insert-identifiers.ts` is added later); the identifier levers were verified directly
  against the pinned interpolation sites instead.
- T3 of the reader's record (the positional-`?` scanner) is not used as a lever: on the pinned
  code a `?` inside a value that is rendered at build time makes the second substitution throw a
  count-mismatch error, i.e. a failed request, not a statement whose structure or scope changes.
  Upstream's scanner is still included in `upstream_fix.patch` for fidelity.
- The effort estimate (45–60 min) is my judgement; the reader's own estimate for the 5-trap design
  was 95 min and this stack is one concept smaller.

## Fairness notes I see myself

- The report never names a file, function or package; the property is stated over "input a caller
  supplies" and over what a condition may do to another condition. The one judgement a solver has
  to make that the report does not spell out is that a *name* is input too; the sibling scalar
  alias check in the pinned code is the visible precedent.
- The datasets renderer is developer-authored configuration today; the report's "caller" covers
  whoever composes the query, and the value it carries is still a value. A solver could argue the
  semantic layer is trusted — that is exactly the dismissal the lever is built on.
- The pinned project tests pin the ungrouped SQL, so a correct fix turns 3 of them red; the report
  asks for the same results, not the same text. A solver who reverts because of those tests would
  fail, which is the honest outcome but worth watching in the trial audit.
