# reactpress-ds — build notes (ABANDONED before build)

- Start (UTC): 2026-10-24T04:15:23Z
- End (UTC): 2026-10-24T04:24:09Z
- Advisory: GHSA-WMW4-MW6X-6VFM / CVE-2026-61685 — fecommunity/reactpress, CWE-89
  ("unvalidated column name in an ORM query builder").
- Pinned: `c3dd10681b3d2b5e224f7ac647b3769557603975`; fix:
  `78ecb70af1c021455c05fdcbe137212c70e310d6`. Pattern B, track injected.

## Outcome

**STOP — the published flaw does not reproduce through a real entry point at the
pinned commit.** Per the build prompt's stop rule, no task was written and no gate
stage was run. The base code was not modified to fabricate exploitability.

## Why (verified, not inferred)

The vulnerable loop in every published list service is:

```ts
query.andWhere(`article.${key} LIKE :${key}`)
     .setParameter(`${key}`, `%${otherParams[key]}%`);
```

TypeORM 0.2.45 (the version pinned by `pnpm-lock.yaml`; 0.2.45 is the final 0.2.x)
validates the **parameter key** inside `QueryBuilder.setParameter`
(`query-builder/QueryBuilder.js:190`):

```js
if (!key.match(/^([A-Za-z0-9_.]+)$/))
    throw new TypeORMError("QueryBuilder parameter keys may only contain numbers, letters, underscores, or periods.");
```

The key reaches `setParameter` unchanged, so keys containing whitespace, quotes,
`--`, `#`, `/*`, parentheses, etc. throw before any SQL executes. Keys made only of
`[A-Za-z0-9_.]` can only form an ordinary identifier (the only metacharacter is the
`.` qualifier), which cannot restructure the query. The filter **value** is a bound
parameter.

Verified end-to-end against MariaDB 10.11 with the real `AppModule` (`NestFactory`
+ supertest, `/api` prefix, real controllers/services/repositories):

| request on `GET /api/article` | result |
|---|---|
| `?title=public` | 200, matching row |
| `?title=' OR '1'='1` | 200, **0 rows** (value bound; no injection) |
| `?title=zzz&<key with spaces / metachars>` | **500** Internal Server Error before any query runs |
| `?title=zzz&nosuchcolumn=x` | 500 (unknown identifier error) |
| `?title=zzz&a.b=x` | 500 (invalid qualified identifier) |
| `?title=zzz&password=x` | 200 (valid hidden column is usable as a filter — out-of-scope info exposure) |

No request shape returned rows that did not match the bound value, and no key
reached the SQL as executable syntax. The screener's `unverified` item ("whether
typeorm 0.2.45 escapes or rejects any identifier characters") resolves to **rejects
the parameter-name characters and leaves only plain identifiers**, so the advisory's
injection is blocked by the ORM, not by the application.

## Alternatives considered, not built

- A real identifier sink that *is* injectable exists in TypeORM's `orderBy(field)`
  (the field is interpolated raw; the direction is validated). Reproduced locally:
  a `CASE` expression in the OrderBy field changed the row order. But no list
  endpoint at the pinned commit accepts a client sort field, so using one requires
  **adding a new feature/sink**. That is fabricating the reported vulnerability, not
  a Pattern-B uncovered route, and it is outside the pinned code's own protection.
  Considered and rejected under the stop rule.
- Altering the base loops (e.g. sanitising the parameter name separately from the
  identifier) would make the advisory's claim true, but it changes the "pinned
  commit just before the fix" into an invented tree. Rejected.
- The `password` LIKE filter oracle is a real information-exposure issue, but the
  screener already marked it out of scope and the published fix keeps `password`
  in the allow-list; not built on.

## What I could not verify

- No public PoC exists for CVE-2026-61685 (advisory pages repeat the mechanism only).
- The exact TypeORM version the reporter used is unknown; 0.2.45 is what this commit
  pins. A pre-validation TypeORM could be injectable, but that is not this tree.
- `present_in_latest` for the uncovered view/search/smtp/user routes was not needed
  (nothing was built).

## Out of scope (one line)

The same fix commit also adds `JwtAuthGuard` to POST /comment, HTML sanitisation,
and a CSP; those are separate XSS/auth changes and were not built on.
