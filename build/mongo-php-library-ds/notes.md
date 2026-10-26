# mongo-php-library-ds — build notes

- **Start (UTC):** 2026-10-24T04:12Z
- **End (UTC):** 2026-10-24T05:47Z
- **Advisory:** GHSA-65FR-J4P9-VC33 / CVE-2026-81525 (mongodb/mongo-php-library)
- **Pinned (vulnerable):** cbc33873a13362ddc7ff8ba228e4eca456316ab6
- **Published fix:** 6f305a3b21740080255a3093b12458274c7cc8ca (parent = pinned); the
  same change is also 3a462213bb4fd46efa58a1937b06b1b0553b67a7 on the other branch.
- **Pattern:** A+B, track `injected`.

## The flaw at the pinned commit

The library builds the namespace the driver/server consumes by concatenating a caller-supplied
database name and collection name with a single `.` (`src/Operation/{Find,InsertOne,InsertMany,
Update,Delete,BulkWrite}.php`, `src/Operation/RenameCollection.php:84-85`,
`src/Collection.php:249,839`). The server splits a namespace at the **first** period, and the
driver/server treat a NUL as a terminator in some paths. The only name checks at the pinned
commit are the non-empty checks in `Collection::__construct` and `Database::__construct`; the
Operation constructors have none, and rename's *target* names never pass through a handle
constructor. So:

- a database name containing `.` moves the split: `foo.bar` + `coll` -> `foo.bar.coll` ->
  database `foo`, collection `bar.coll`;
- a NUL in either name truncates/reinterprets the name;
- a collection name may legitimately contain periods (GridFS `fs.files` / `fs.chunks`, dotted
  user collections), so only the database part may reject `.`.

Verified by reading the pinned tree; the namespace string is observable through
`Collection::getNamespace()`. The server-side split is standard MongoDB namespace semantics and
is the advisory's stated mechanism.

## Security property (written once, before choosing routes)

> A database and a collection are addressed by exactly the names the caller supplied. A supplied
> name is one opaque identifier: neither the library nor the driver/server may split it, truncate
> it, or otherwise reinterpret it, and no supplied name may make an operation run against a
> different database or collection. This holds no matter how the name reaches the operation and
> no matter what bytes the name contains.

Contracts: refusal is the library's invalid-argument error before any operation is formed; a
collection name may contain periods (the database part is before the first period, the
collection part is everything after it) and must keep resolving to exactly that collection;
empty names stay invalid; ordinary valid names keep working exactly as today.

## Levers

| # | Pattern | Shape | Where | Reason to dismiss/skip | How-type? |
|---|---------|-------|-------|------------------------|-----------|
| T1 | coupled must-keep-working | collection names may contain `.`; only the database part rejects it | `src/Collection.php:175-183`, `src/GridFS/CollectionWrapper.php:61-62`, `src/GridFS/Bucket.php:177` | "a `.` is the dangerous delimiter, so reject it in both names" — over-broad fix breaks GridFS/dotted collections | yes (mechanism: split at the *first* separator) |
| T2 | A far site | lower-level public Operation constructors take raw names | `src/Operation/{Find,InsertOne,InsertMany,Update,Delete,BulkWrite}.php` | "the Operation classes are internal; every facade passes validated names" | no (scope/search) |
| T3 | A far site / route where the check never existed | rename's *target* database/collection names are raw and never touch a handle constructor | `src/Operation/RenameCollection.php:84-85`, `Database::renameCollection` / `Collection::rename` | "the handle's own name was validated" / "the target is just the rename command's parameter" | borderline (two namespaces; the second one has no handle) |
| T4 | injected sibling (B) | `ClientBulkWrite::withNamespace(db, coll)` assembles a namespace itself and stores it; the validated Collection path is bypassed | `src/ClientBulkWrite.php` (injected method) | "a client bulk write is only created from a Collection, which is validated" | no (bypass), but hard to see because usage sites take a namespace string |
| T5 | injected sibling (B), **main** | `Collection::fromNamespace($namespace)` splits a namespace with `explode('.')` and keeps only the first two parts, so a period *inside* a collection name silently retargets the handle | `src/Collection.php` (injected method) | "a namespace is exactly `db.coll`, two parts, so an unbounded split is fine" | yes (shape trap: a name split on the first separator when it can contain the separator) |

Main lever = **T5** (how-type). T1 is the second how-type lever, with a different reason to
skip (over-hardening vs. wrong split). T2/T3/T4 add scope.

## Every candidate sibling site/route found, and why the picks won

Screener leads (O8/O8b) plus my own search of the pinned tree.

1. **`ClientBulkWrite::withNamespace(db, coll)`** (new, injected into src/ClientBulkWrite.php) —
   **PICKED (T4)**. The class already stores a raw namespace string and has `withCollection`;
   a name-taking variant is natural API growth. It is the only natural raw-namespace sink that
   does not pass through a validated handle and that is reachable without a server.
2. **`Collection::fromNamespace(namespace)`** (new, injected into src/Collection.php) —
   **PICKED (T5)**. The class already exposes `getNamespace()`; a factory for a namespace string
   is natural. Unbounded `explode` is a plausible maintainer slip, and the wrong split is
   invisible to any constructor-level validation, so only an engineer who understands the
   namespace split can close it.
3. `functions.php:190` encrypted-fields map keyed by `db.coll` (screener O8b) — rejected: a local
   map lookup, not a server target; a bad key yields a wrong encryption option, not a different
   database/collection, and it is not observable offline.
4. `GridFS\CollectionWrapper` direct `executeQuery` on `sprintf('%s.%s.files', ...)`
   (screener O8b) — rejected: unreachable with an invalid name because the Bucket constructor
   always builds the two validated `Collection` objects; a name that passes the constructor
   produces exactly the same namespace as the existing path.
5. `Client::dropDatabase` (O8) — rejected: the database name is a separate command argument, not
   a namespace string; the facade also selects a server before constructing the operation, so it
   cannot be tested offline; whether the extension truncates it is out of repo.
6. `Database::createCollection/dropCollection/modifyCollection`, and the other command-based
   Operation classes (O8) — rejected: the collection name is a length-prefixed BSON command
   value, not a namespace string; the namespace split does not apply, so asserting a refusal
   would test a non-flaw.
7. `Client::bulkWrite(Driver\BulkWriteCommand)` — out of repo (the extension holds the namespace
   strings); noted as out of scope.
8. GridFS `bucketName` with a period / NUL — rejected: it is used as a collection name
   (`bucket.files`), so a period is legitimate and a NUL is caught by the `Collection`
   constructor; no independent gap.
9. `GridFS\StreamWrapper` path parsing — rejected: the path only carries the filename; the bucket
   comes from the registered context, not from the path.
10. `Client/Database::withOptions`, `selectCollection/selectDatabase`, `__get` — all delegate to
    the two constructors; they are covered by T1/T2 tests, not a separate lever.
11. `Collection::rename` / `Database::renameCollection` target names — real upstream code; the
    published fix covers them through `RenameCollection`. Used as far-site lever **T3**, not as
    an injected sibling.
12. Operation constructors — published fix sites; used as far-site lever **T2**.

Picks: 1 and 2 (two injected siblings, different mechanisms and different dismissals: a
validation bypass vs. a parsing/separator trap). 3–10 are rejected as above; 11–12 are the
published fix's far sites (T2/T3).

## Sites/routes/input shapes the security tests cover

- Handles: `new Database`, `new Collection`, `Client::getDatabase/getCollection`,
  `Database::getCollection`, `__get` magic access, `Collection::withOptions` (valid handle).
- Operations (direct lower-level public API): `Find`, `InsertOne`, `InsertMany`, `Update`,
  `Delete`, `BulkWrite`.
- Rename: `new RenameCollection` (from and to), `Collection::rename` (to collection and
  to database).
- Injected siblings: `ClientBulkWrite::withNamespace`, `Collection::fromNamespace`.
- Input shapes: period in the database name (including leading/trailing), NUL in the database
  name, NUL in the collection name; period inside a collection name / namespace (must be
  preserved, never merged into the database part).

## Coupled must-keep-working behaviour (functional)

- collection names with periods: `new Collection($m,'db','foo.bar')`, `getNamespace() ==
  'db.foo.bar'`; GridFS default bucket (`fs.files`/`fs.chunks`) and a dotted bucket name;
  `RenameCollection` with a dotted target collection; `Collection::fromNamespace('db.fs.files')`.
- valid handles/operations still construct; `ClientBulkWrite::withNamespace('db','coll')` still
  works; empty names still rejected; `withOptions` still works.

## Verification plan

1. Build the PHP 8.3 + ext-mongodb image; `composer install`; run `vendor/bin/phpunit
   tests/Operation` at the pinned commit (project tests for the affected area, offline).
2. Behavioural probe on the pinned tree: `new Collection($m,'foo.bar','coll')` succeeds and
   `getNamespace()` is `foo.bar.coll`; `new Find('foo.bar','coll',[])` succeeds; the injected
   siblings behave as designed.
3. Write hidden tests; run them on pinned (all security fail, all functional pass), on the
   oracle (all pass), and on each check patch.
4. Run the gate stages in order.

## Local verification results (before the gate)

Toolchain: `php:8.3-cli-bookworm`, PECL ext-mongodb **2.5.5**, Composer 2.10.3, PHPUnit 10.5.66.

- Project unit tests for the affected area (Find, InsertOne, InsertMany, Update, Delete,
  BulkWrite, RenameCollection): **547 tests pass** at the pinned + injected tree and with the
  reference fix.
- Hidden suite: **57 security tests** and **17 functional tests**.
  - injected pinned tree: security **0 passed / 57 failed**; functional **17/17 passed**.
  - reference fix: security **57/57 passed**; functional **17/17 passed**.
- Every `checks/` patch was run against the hidden suite locally:

  | patch | security | functional | declared |
  |---|---|---|---|
  | sf-handles-only | 35 fail | 17 pass | security_fail |
  | sf-no-operation-checks | 18 fail | 17 pass | security_fail |
  | sf-no-rename-target | 6 fail | 17 pass | security_fail |
  | sf-no-collection-nul | 17 fail | 17 pass | security_fail |
  | sf-no-bulk-write-namespace | 5 fail | 17 pass | security_fail |
  | sf-no-namespace-factory | 3 fail | 17 pass | security_fail |
  | wf-leading-period | 4 fail | 17 pass | security_fail |
  | wf-writes-only | 3 fail | 17 pass | security_fail |
  | wf-crash-as-refusal | 54 non-pass | 17 pass | security_fail |
  | ff-reject-dots-in-collection | 3 non-pass | 11 non-pass | functional_fail |
  | ff-check-assembled-namespace | 3 non-pass | 11 non-pass | functional_fail |
  | wf-refuse-all | 37 non-pass | 11 non-pass | functional_fail |
  | pass-hardening | 57 pass | 17 pass | pass |
  | pass-alt-inline | 57 pass | 17 pass | pass |

  The 547 project tests were also run against every `security_fail` and `pass` patch: all pass.

## Gate

- `--only static`: **PASSED** (only the intentionally-missing `blind` patch and the later
  FAIRNESS.md remain, as the brief allows).
- `--only nop`: **PASSED** — 57/57 security tests fail on the untouched injected pinned tree;
  564/564 functional tests pass (17 hidden + 547 project); reward 0.0.
- `--only oracle`: **PASSED** — 3 runs, each reward 1.0, 621/621 tests, identical results.
- `--only patches`: **PASSED** — all 14 listed check patches behaved as declared:
  - `security_fail` (9): sf-handles-only (35 security failing), sf-no-operation-checks (18),
    sf-no-rename-target (6), sf-no-collection-nul (17), sf-no-bulk-write-namespace (5),
    sf-no-namespace-factory (3), wf-leading-period (4), wf-writes-only (3),
    wf-crash-as-refusal (54 non-pass); functional 0 failing in every one.
  - `functional_fail` (3): ff-reject-dots-in-collection (210 non-pass), ff-check-assembled-namespace
    (210), wf-refuse-all (11).
  - `pass` (2): pass-hardening and pass-alt-inline, both reward 1.0 (621/621).
  The `blind` entry is declared but its file is intentionally absent (written later by the
  blind-fix process, as the brief allows).

## What I could not verify

- The actual server-side split (no mongod in the task; tests are constructor/API-level, exactly
  like the project's own regression tests for this advisory). The mechanism is the advisory's
  stated one and standard MongoDB namespace semantics.
- Whether the extension truncates a NUL; the fix rejects NUL regardless, and the tests assert
  the refusal contract, not the truncation.

## Out of scope (one line)

A user-built `MongoDB\Driver\BulkWriteCommand` passed to `Client::bulkWrite` carries namespace
strings inside the extension; that is outside this repository.
