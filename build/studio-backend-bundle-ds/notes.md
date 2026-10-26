# studio-backend-bundle-ds — build notes

- Start UTC: 2026-10-24T04:17:00Z (driver attempt) / builder start 2026-10-24T04:20:00Z
- End UTC: (filled at the end)
- Gate (sequential, one stage at a time):
  - static: PASSED (2026-10-24T04:39Z)
  - nop: PASSED (security 17/17 fail, functional 20/20 pass; 2026-10-24T05:01Z)
  - oracle: PASSED, 3 runs, reward 1.0, identical results (2026-10-24T05:11Z)
  - patches: first run reached 7/11 checks green, then Harbor aborted `chk-sf-on-branch-only` with the
    known egress/allowlist capability-probe ValueError under load (classified infra, exit 2); retried
    the stage unchanged (no task file weakened).

- Repo: pimcore/studio-backend-bundle, pinned ea9d329686f5e5aea2eec378d63ac2deb965bb27, fix f532428cfbf4f5d6e299a13cedd5c29541802552
- Advisory: GHSA-79CW-HFCC-7MW9 / CVE-2026-55208 (CWE-89). Track: injected. Pattern: A+B.

## What the product does
Symfony bundle behind the Pimcore Studio UI. Every collection endpoint (notifications, recycle bin,
website settings, SEO redirects, translations, classification-store configuration grids, quantity
values, notes, GDPR providers, application logger) builds a Pimcore/Doctrine listing from a
request body: a list of column filters `{key, type, filterValue}` (notes use a JSON-string
`fieldFilters` with `{field, type, operator, value}`). Tagged `FilterInterface` implementations
interpolate the client-supplied key into the SQL condition.

## The security property (one, general)
A client-supplied column/field name is data: whatever its characters and whichever endpoint it
arrives at, it must name exactly one column (or one table-qualified column) and must never become
part of the SQL text - it may not add, remove or change clauses, operators, comments, literals or
parameter placeholders, and it may not choose how a value is bound. Qualified names (alias.column)
must keep working.

## Levers (one line each)
- L1 (A, base/report-led, where-type): identifier interpolated between backticks - date (on and
  comparison branches), equals, like. `src/Listing/Filter/DateFilter.php:50,64`,
  `EqualsFilter.php:42`, `LikeFilter.php:42`. Dismiss: the obvious landing point.
- L2 (A, second implementation, where-type): the Note module's own filter service, fed by a
  JSON-string `fieldFilters` and a `{field,...}` shape, not by the shared column filters.
  `src/Note/Service/FilterService.php:66,70`. Dismiss: "notes are a different feature with a
  different request field; the grid's listing filters do not cover it".
- L3 (B, real unmodified upstream route, where/howe-type): the translation-like filter is a globally
  tagged listing filter whose key is concatenated with NO quoting at all (`$key . '.text LIKE :' . $key`);
  the language check in `TranslatorService` only decides which joins are added, it never validates the
  filter, and the filter still runs for a key that is not a language. Coupled: `alias.text` must keep
  filtering. `src/Translation/ListingFilter/TranslationLikeFilter.php:43`. Dismiss: "translation-only,
  language codes are validated".
- L4 (HOW, shape trap): the same raw client key is reused as the bound-parameter name
  (`' :' . $key`), so a key containing non-word characters leaves raw SQL after the placeholder even
  when the identifier itself is quoted/escaped. Sites: DateFilter comparison branch, EqualsFilter,
  LikeFilter, Note FilterService, TranslationLikeFilter, and both injected siblings. Dismiss: "the
  identifier is quoted and `:name` is a bound parameter".
- S1 (injected, how-type shape): a classification-store configuration listing filter that trusts
  dotted names verbatim ("joined configuration columns are referenced by their table alias") and
  quotes only unqualified names. `src/ClassificationStore/ListingFilter/ConfigurationFieldFilter.php:52`.
  Dismiss: "qualified keys are table aliases and are used verbatim; the shared filters cover the grids".
- S2 (injected, where-type + guard illusion): the application-logger repository gains a
  keyword-column filter that copies the repository's `andWhere` idiom but bypasses `isKeyAllowed`.
  `src/Bundle/ApplicationLogger/Repository/LogRepository.php:161`. Dismiss: "the allowlist already
  restricts which columns can be filtered".

## Sites / routes / input shapes covered by the security tests
- POST collection routes through `ListingFilter::applyFilters` (driven through
  `CollectionParametersMapper`, the real request->parameter mapping): date on/from/to, equals, like.
- POST notes collection through the note filter service (fed by `NoteParameters`, the real DTO that
  json_decodes `fieldFilters`).
- POST translations collection through the same dispatcher (translationLike key).
- The classification-store configuration listing filter (S1) through the dispatcher.
- The application-logger listing repository (S2), SQL captured from the real Doctrine query builder.
- Shapes: backtick breakout in the identifier, dotted-name bypass, raw placeholder-name suffix,
  identity/array date filter value.

## Coupled must-keep-working behaviour (functional tests)
- Plain and mixed-case column names (`creationDate`), all date operators (on/from/to), equals/like.
- Qualified identifier `de.text` in the translation grid (whole-quote or dotted-verbatim fixes fail).
- Note field filters: date-eq BETWEEN branch, numeric/boolean/list, the `user` special case (the
  pinned project's own FilterServiceTest is restored and run verbatim).
- S1: a qualified classification-store key still filters; S2: a legitimate search column still filters.

## Candidate sibling list (all found, reason discarded or picked)
1. `src/Email/Repository/EmailLogRepository.php` (GDPR sent mails, getFilteredListing) — picked first,
   then DROPPED: the method ends in `applySearchOptions()` -> `setOrderKey()` ->
   `Pimcore\Db::get()` -> kernel container, so it cannot be driven in the project's DB-free unit
   environment. Not testable without a booted Pimcore kernel.
2. `src/Gdpr/Provider/PimcoreUserProvider.php` generic column loop — DROPPED: `findData()` calls
   `$listing->getUsers()`, i.e. a DB load, and `setOrderKey`; not reachable DB-free.
3. `src/Bundle/ApplicationLogger/Repository/LogRepository.php` — PICKED (S2): own Doctrine
   QueryBuilder, no listing order-key quoting, has an allowlist that lulls the reader, captured SQL
   is a faithful "what the DB receives" oracle.
4. `src/Bundle/Seo/Repository/RedirectsRepository.php` — dropped: it already routes through the
   shared dispatcher, so a sibling there duplicates L1 without adding a distinct reason.
5. `src/Unit/Repository/QuantityValueRepository.php`, `src/Property/Repository/PropertyRepository.php`,
   `src/Notification/Repository/NotificationRepository.php`, `src/WebsiteSetting/...` — all already
   route through the shared dispatcher; nothing to add.
6. `src/ClassificationStore/Repository/Configuration/*` + `SearchHelperService` — the joined
   configuration listings are the natural home of qualified (alias.column) keys; PICKED as S1's
   new listing filter.
7. `src/Translation/Repository/TranslationRepository::getTranslationKeysWithTextFilter` and
   `addSearchCondition` — fixed columns / quoted, no client key; not a candidate.
8. `src/ExecutionEngine/Repository/JobRunRepository.php` — DQL `orderBy` on a client sort key; a
   different sink (ORDER BY, DQL, not the listing WHERE) and outside this advisory's family; not used.
9. `src/User/Repository/UserRepository.php`, `src/DataObject/...` — fixed columns; not candidates.
Why the picks beat the rest: S2 is the only DB-free far site with its own query plumbing and a
guard that makes it read as already-safe; S1 is the only DB-free site where the *legitimate*
qualified-identifier shape and the vulnerability are the same code path.

## Verified
- Pinned commit fetched; fix diff inspected (quoteIdentifier in the 4 files + quoteIdentifier-based
  unit tests added by the fix; the pinned tree does NOT contain those regression tests).
- `composer install` succeeds offline afterwards (COMPOSER_ROOT_VERSION=2025.4.3, php 8.3 + intl,
  zip, exif, gd, bcmath, curl); `vendor/bin/codecept run Unit tests/Unit/Note/Service/FilterServiceTest.php`
  -> 7/7 green on the pinned tree.
- Attacks reproduced against the pinned tree with the real dispatcher/DTOs (conditions + DBAL
  `SQL\Parser` show the payload reaching the SQL text; DBAL NAMED_PARAMETER is `[A-Za-z0-9_]+`, which
  is what makes the placeholder-suffix shape bite).
- S1/S2 prototypes build conditions/SQL through their real services (see probe transcripts in
  `~/.tb-graders/cwe/work/studio-backend-bundle-ds/proto/`).

## Could not verify / guesses
- No HTTP-level tests: a booted Pimcore kernel + MySQL is not available offline. Tests drive the
  bundle's real service/DTO/repository entry points (the project's own unit-test idiom; the fix's
  own tests do the same).
- Whether any Pimcore core code quotes a listing condition key on its own (unverified; the pinned
  condition text is what the Dao passes to Doctrine).

## Upstream latest read-only check (2026-10-24)
- `git fetch --depth 1 origin HEAD` (4eb9817, 2026.x). The later upstream rewrote
  `TranslationLikeFilter` to validate the key against `$listing->getLanguages()` and to use
  `quoteIdentifier($key) . '.text LIKE :translationLikeValue'.$index`, and the note filter service to
  use `filter_{index}` parameter names with `quoteIdentifier`. So the uncovered route is fixed in
  latest (register `present_in_latest=no`) and the placeholder-name shape (L4) was a real defect that
  the advisory's own fix did not close.


## Out of scope (one line)
- Client sort keys go to Pimcore core `setOrderKey` (core quoting unverified) and
  `JobRunRepository` concatenates a client sort key into a DQL ORDER BY; neither is pursued.

## Local verification matrix (Codeception Unit suite, pinned+injection image tree)

- pinned (nop): security 17/17 FAIL, functional 13/13 PASS, project 7/7 PASS.
- oracle (`solution/fix.patch`): security 17/17 PASS, functional 13/13 PASS, project 7/7 PASS.
- `sf-miss-L1`: 4 shared identifier tests fail, functional + project pass.
- `sf-miss-L2`: 3 note tests fail, functional + project pass.
- `sf-miss-L3`: 2 translation tests fail, functional + project pass.
- `sf-miss-L4`: 8 parameter-name tests fail (date/equals/like/note/translation/logger), functional + project pass.
- `sf-miss-S1`: 3 classification-store tests fail, functional pass.
- `sf-miss-S2`: 2 logger tests fail, functional pass.
- `sf-on-branch-only`: exactly the date-range test fails (one direction only).
- `ff-overbroad` (whole dotted name quoted as one identifier): security all pass, the two qualified-identifier
  functional tests fail.
- `ff-refuse-all`: security all pass (rejected), all hidden functional tests error -> functional_fail.
- `pass-alt` (validate/reject instead of escape): all pass.
- `pass-hardening` (oracle + key type/length/control-char validation): all pass.

## Pattern B register
Rows for L3 (real upstream route) and the two injected siblings S1/S2 are appended to
`build/audit/uncovered-routes.tsv`.

