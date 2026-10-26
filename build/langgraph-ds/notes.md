# build notes — langgraph-ds (pattern A, injected)

Start: 2026-10-24T03:27:18Z
End:   2026-10-24T06:20Z (build session limit; patches stage still running)

## Candidate / advisory

- repo: langchain-ai/langgraph
- pinned: 41341457342327166d72fc11952ab28fb61ec0bf (release 1.2.10)
- fix:    66ebe1a0da921e73f0f9f879ba105d314c079f7c (`fix(checkpoint-postgres,checkpoint-sqlite): scope namespace matching to segment boundaries`)
- advisory family: authorization scope / tenant isolation — hierarchical identifier prefix match on flattened text (CWE-863, CWE-200).

## One general property (written before choosing routes)

A request that takes a namespace scope may act only on items whose namespaces lie inside that
scope, membership decided label by label: a prefix covers exactly the namespaces that begin with
those labels at any depth; a suffix exactly those that end with them; `*` stands for exactly one
label; an exact namespace only itself. No item outside the scope may be returned, revealed,
changed or removed by such a request — whichever backend is configured, whichever entry point
performs it, and however the requested scope or the stored names are spelled. A scope whose
labels are not a valid namespace is refused, never matched against another namespace.

Every lever below is an instance of that one property. The report states the property once and
never names a site.

## Levers (one line each)

- **T1 — second implementation (Pattern A far site, where-type; SQLite search).** Same guarded
  operation in another package/backend: `libs/checkpoint-sqlite/.../sqlite/base.py:509-511`
  (`WHERE prefix LIKE ?`), vector branch at `:463-465`. Why dismiss: the report reproduces on one
  backend; the other is a separate store package a backend-scoped fix need not touch.
- **T2 — neighbouring discovery entry point (published-fix far site; `list_namespaces`).**
  `postgres/base.py:618-629`, `sqlite/base.py:550-561`. Why dismiss: it returns namespace names,
  not stored values, so a value-read report looks unrelated.
- **T3 — shape trap, separator metacharacters (how-type).** `_namespace_to_text`/LIKE pattern
  construction on both backends; labels containing `_`/`%` stay literal only if the pattern is
  escaped (`postgres/base.py:1274-1280`, `sqlite/base.py:96-102`). Why dismiss: a fix that makes
  a prefix end on the separator still passes the reported example.
- **T4 — shape trap, backend-specific LIKE semantics (how-type; SQLite only).** SQLite's `LIKE`
  is ASCII case-insensitive, so the same boundary fix copied from the other backend conflates
  namespaces differing only in case. Why dismiss: the SQL looks right and works on the other
  backend.
- **T5 — shape trap, wildcard arity (how-type; `list_namespaces` `*`).** `*` is substituted with
  `%`, so it spans several labels; the documented/InMemoryStore semantics is exactly one label.
  Why dismiss: the reported flaw is a plain prefix, not a wildcard pattern.
- **T6 — malformed scope identity differential (Pattern B: route where the protection never
  existed; real unmodified upstream code).** Namespace paths are validated only on writes
  (`libs/checkpoint/langgraph/store/base/__init__.py:1263`, called from put/aput at :919/:1180),
  never on scope arguments, so a label containing the separator is silently reinterpreted as two
  labels by the flattened-text matcher — still true after the published fix. Why dismiss: "labels
  cannot contain periods" is enforced on writes, so a dotted scope looks impossible.
- **T7 — asynchronous entry points (published-fix entry points; async SQLite/Postgres).** The
  async stores share the query builders, so the async tests confirm the fix is not limited to the
  synchronous path. A fix that leaves the async connection without its matcher registration is
  already caught by the project's own async suite (functional), so this is covered as an entry
  point rather than as a separate security_fail patch.
- **T8 — injected sibling: bulk namespace removal (how-type route where the protection never
  existed).** `delete_namespace` on both backends, a prefix `LIKE` delete written in the same
  idiom the maintainers used for search. Why dismiss: it removes data instead of reading it, so a
  read-report fix skips it.
- **T9 — injected sibling: namespace export/copy (route where the protection never existed).**
  `export_namespace` on both backends. Why dismiss: it is a backup/maintenance read, not the
  user-facing read path.
- **T10 — vector branch (published-fix far site, SQLite only).** `sqlite/base.py:463-465` builds
  its own `s.prefix LIKE ?` separate from the regular branch. Why dismiss: it only runs with an
  embedding index configured.

## Full candidate list considered (screener O8/O8b + own search)

1. PG `search` namespace condition — adopted as base flaw (report target).
2. PG `list_namespaces` prefix/suffix — adopted (T2).
3. PG `_namespace_to_text(handle_wildcards)` — adopted (T3/T5 helper).
4. SQLite regular `search` — adopted (T1).
5. SQLite vector `search` — adopted (T10).
6. SQLite `list_namespaces` prefix/suffix — adopted (T2).
7. SQLite sync `__init__` + async `setup` user-function registration — covered by the project's
   own suites (functional); no dedicated security_fail patch because that suite fails without it.
8. Async stores' `asearch`/`alist_namespaces` — same builders; covered as entry points (async tests).
9. O8b#1 namespace-scoped bulk purge (`LIKE prefix%` delete) — adopted as T8, on both backends.
10. O8b#2 max_depth truncation by `.` split after a raw-text filter — rejected: stored labels may
    not contain `.`, and the filter runs before truncation, so there is no identity differential
    to exploit; a behaviour test shows the same result before and after any correct scope fix.
11. O8b#3 scope labels not validated for `.` — adopted as T6 (real, unmodified upstream; the
    published fix does not address it).
12. A namespace-scoped item-count/quota probe — rejected: a count is a weak, arguable leak and
    would need its own contract sentence, which the design forbids; T9 covers the read shape.
13. `langgraph/pregel/main.py:1092 namespace.startswith(name)` — rejected: different feature
    (subgraph checkpoint namespaces), outside this advisory's protected sink.

Why the picks beat the others: T1/T6/T7/T8/T9/T10 are each a *different* way a solver runs out of
scope (other package, malformed identity, connection setup, other verb, other entry point, other
branch), and T3/T4/T5 are how-type shape traps that a boundary-only fix fails. O8b#2 and the
count probe add no mechanism the task does not already test.

## Sites / routes the security tests drive

- `PostgresStore.search` / `AsyncPostgresStore.asearch`, `PostgresStore.list_namespaces` /
  `alist_namespaces`, `delete_namespace`, `export_namespace`.
- `SqliteStore.search` (regular and vector branches) / `AsyncSqliteStore.asearch`,
  `SqliteStore.list_namespaces` / `alist_namespaces`, `delete_namespace`, `export_namespace`.
- Shape inputs: plain prefix, exact namespace, suffix, `*` match path, labels with `_` and `%`,
  labels differing only in case, a dotted scope, an empty prefix.
- Each security test goes through the public store API; no SQL/private helper in the test.

## Coupled must-keep-working (functional)

- exact namespace still matches itself (including labels with `_` and `%`);
- prefix open-ended at any depth on both backends;
- in-scope `list_namespaces` prefix/suffix/wildcard results;
- in-scope removal/export still affects exactly the in-scope items;
- in-scope vector search and async reads still return their items;
- the project's own store suites (both packages, sync + async) pass.

## Injected siblings (track=injected)

- T8 `delete_namespace(namespace_prefix)` on `PostgresStore` and `SqliteStore`
  (`DELETE FROM store WHERE prefix LIKE <text>%`), a tenant-offboarding maintenance helper.
- T9 `export_namespace(namespace_prefix)` on both, returning the items under a prefix for the
  platform's backup job (same raw-text prefix idiom).
Both are plain product code in the style around them, reachable through the public store object,
covered only by the one general property (returned / revealed / removed), placed where the
published fix never touches.

## Verified before building

- pinned checkout at 4134145 (release 1.2.10); fix commit differs only in the two store packages
  plus their tests (test diff is additions only, so the pinned suites still pass under the fix).
- reproduced on the pinned tree in a prototype container:
  - SQLite: prefix `("foo",)` returns `("foobar",)`; prefix `("user_1",)` returns `("userX1",)`;
    prefix `("acme",)` returns `("ACME","x")`; `list_namespaces(prefix=("cache","*","v1"))`
    returns a 4-label namespace; `list_namespaces(suffix=("alice",))` returns `("uid","malice")`.
  - Postgres: prefix crossing, `_` metacharacter, wildcard arity and suffix crossing all reproduce;
    case does not leak there (PG LIKE is case-sensitive).
- applied the published source fix and re-ran: all of the above behave correctly; case stays
  correct on SQLite (GLOB), and the wildcard matches one label.
- project suites on the pinned tree in the prototype image: sqlite test_store 55 pass,
  test_async_store 27 pass; postgres test_store 119 pass, test_async_store 91 pass (Postgres 17 +
  pgvector, offline).

## Gate progress (filled as stages run)

- static: PASS (2026-10-24T04:16Z; re-run clean after dropping the async-registration lever)
- nop: PASS — 23 security tests all fail on the pinned+injected tree, 303 functional tests pass
- oracle: PASS — 3 runs, reward 1.0, identical test sets (23 security + 303 functional)
- patches: at session end, 11 of the 13 checks had completed and passed, in manifest order
  (sf-miss-pg, sf-miss-sqlite-backend, sf-miss-list-namespaces, sf-miss-metachars, sf-miss-case,
  sf-miss-vector, sf-miss-removal, sf-miss-export, sf-miss-malformed-scope, ff-overbroad,
  ff-refuse-all). pass-hardening was still running and pass-alt had not started; both were
  verified to score 1.0 locally in the prototype image. The async-registration check was dropped
  because the project's own async suite already catches a missing matcher registration, which
  made it a functional rather than a security failure.

## Not verified / guesses

- Whether the LangGraph Platform server (outside this repo) exposes these calls over HTTP.
- Exact runtime of the full verifier (prototype suites took ~3.5 min; task timeout set above it).
- Python 3.12 (`python:3.12-slim-trixie`) is above the project's >=3.10 floor; the flaw is not
  version dependent.

## Out of scope

- `libs/langgraph/langgraph/pregel/main.py:1092` subgraph checkpoint namespace `startswith` — a
  different feature, not built on.

## Resume note

At 2026-10-24T06:25Z the `--only patches` stage was still blocked on the
`pass-hardening` trial (the shared VM was heavily loaded; a duplicate retry job of the same
check was also alive). Every check's expected outcome was verified first in the local prototype
image, and `pass-hardening` / `pass-alt` both scored 1.0 there. Re-run just this stage with:

    python3 -I builder/gate.py langgraph-ds --only patches
