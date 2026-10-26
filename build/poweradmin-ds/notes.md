# poweradmin-ds — build notes

Start (UTC): 2026-10-24T05:16Z (build job start; design work from 05:17Z)
End (UTC): 2026-10-24T06:24Z

## Task

Poweradmin (PHP, PowerDNS control panel), pinned at `0ac312c397155522cde337bbeee046f77cf2ea58`,
published fix `cbb78f401a9cc77c976939e93b558f39cb738965` (GHSA-CMWH-G2H8-C222). The published
fix forces a binary collation on the OIDC/SAML subject and provider comparisons and on the two
stored identity columns. Track: injected (two realistic sibling gaps in the same service).

## Levers (one line each)

1. **schema-and-binding (how, main)** — the stored identity columns and their uniqueness are
   produced by `sql/poweradmin-mysql-db-structure.sql`, which no lookup query reads; a distinct
   identity that differs only by case can be looked up exactly yet still collide with the stored
   unique key, so it never keeps its own binding. Dismissal: "once the query forces a binary
   collation the stored collation no longer matters". Fix needs the stored key understood.
2. **exact-bytes (how, shape)** — MySQL's binary collations are still PAD SPACE, so an identifier
   differing from a stored one by a trailing space compares equal; a fix that only appends a
   binary collation still signs the attacker into the existing account. Dismissal: "case and
   accent are the reported family, a binary comparison must cover them all".
3. **legacy-charset (how, coupled must-keep-working)** — installations created with a non-utf8mb4
   character set (the installer offers latin1 collations and the shipped DB default was latin1)
   reject a `COLLATE utf8mb4_bin` clause; the lookup error is swallowed, so every sign-in silently
   creates a duplicate account. Dismissal: "every supported backend uses utf8mb4".
4. **link-write-path (where, injected)** — the two functions that store a binding
   (`linkOidcToExistingUser`, `linkSamlToExistingUser`) were refactored to key on the asserted
   identity and move an existing row to the signing-in account; reached whenever an account is
   auto-provisioned or linked by email, and never touched by the published fix. Dismissal: "the
   report is about finding an account, not about writing a link".

Coupled must-keep-working: exact legitimate sign-in, auto-provisioning and its repeat sign-in,
configured email linking, distinct providers, SQLite backend, latin1 installation, and the four
project unit-test files for the affected area.

## Design decisions

- The security property is stated once, over the identity→account outcome and the stored binding,
  and covers all four levers without naming any site.
- Tests drive `UserProvisioningService::provisionUser()` — the shared sink that both callback
  controllers (`GET /oidc/callback`, `POST /saml/acs`) call — with the production
  `OidcUserInfo`/`SamlUserInfo` value objects and a real database. Driving the OIDC callback
  itself would need a live token/userinfo endpoint; driving SAML would need a signed assertion.
  The verifier has no network beyond loopback, so the service seam is used.
- Each hidden test creates its own MySQL database from the **submission's** shipped schema file,
  so a schema fix is exercised rather than prescribed; SQLite tests use the shipped SQLite schema.
  The latin1 scenario converts the two identity tables after creation, simulating a legacy install.
- Reference fix: `DbCompat::exactIdentityColumn()` / `exactIdentityValue()` return
  `CAST(CONVERT(col USING utf8mb4) AS BINARY)` (MySQL) or the bare column/placeholder (SQLite,
  PostgreSQL), applied to both protocol lookups, both orphan-cleanup lookups and both injected
  link-writing lookups; the shipped schema gets `COLLATE utf8mb4_bin` on the four identity
  columns, plus a migration file.

## Injected-sibling candidate list (and why the two picks won)

Every candidate found by searching the code for external identifiers reaching a stored record:

1. `linkOidcToExistingUser` upsert keyed by (subject, provider) — **picked**. Reached on
   auto-provision and email-link paths; a natural refactor of the existing check-then-update code;
   the published fix never touches the function.
2. `linkSamlToExistingUser` — **picked**. Protocol twin of (1); separately reachable; the same
   maintainer refactor applied to the SAML copy.
3. `SamlService::handleSingleLogout` resolving the session/NameID through `saml_user_links` — not
   picked: Poweradmin sessions are PHP file sessions keyed by cookie, so a loose NameID lookup has
   no observable effect on another user's session; adding one would mean inventing a side effect.
4. `cleanupOrphanedAuthLinks` (public, no caller) subject-scoped variant — not picked: no caller,
   so not reachable through a real entry point.
5. `findGroupByName` / `permission_template_mapping` (external group → local group) — not picked:
   a different protection (group-name authorization), not identity resolution; the advisory does
   not protect it.
6. `findUserByEmail` / `link_by_email` — not picked: the screener already lists email-based linking
   as a separate trust decision, outside this advisory.
7. `DbUserRepository::cleanupExternalAuthLinks`, `UserManager::deleteUser`, `getDatabaseUsername` —
   not picked: keyed by user id, no identifier comparison.
8. API-key/token comparisons — not picked: not external-IdP identity resolution.
9. Web-installer schema producer (`install/helpers/DatabaseStructureHelper.php`) — not picked as a
   scored route; see register note. It creates the identity tables without any unique index and
   with the admin-chosen collation, so the published schema DDL never reaches it; after a correct
   charset-independent query fix its lookups are exact, and the only residual issue is the latin1
   breakage already covered by lever 3. Testing the installer would need its internal class API.

Picks vs. runners-up: (1)+(2) are the only candidates that are (a) reachable through the real
provisioning entry, (b) exercised by default configuration (auto-provision on, email link on),
(c) separate stored code the published fix leaves alone, and (d) protect the same outcome as the
reported lookup while requiring the mechanism (a write path that resolves identity) to be
understood.

## What was verified (behavioural, on the pinned tree unless stated)

- Pinned/injected tree, MySQL utf8mb4_unicode_ci: case-, accent-, trailing-space- and
  provider-case variants all resolve to the victim's user id and overwrite the victim's email.
- Published fix (query `COLLATE utf8mb4_bin` + schema DDL) still fails: trailing-space variant
  resolves to the victim (PAD SPACE), and the latin1 functional scenario duplicates accounts
  (`ERROR 1253 COLLATION 'utf8mb4_bin' is not valid for CHARACTER SET 'latin1'`, swallowed).
- Query-only published fix (no schema change) also fails binding stability (the unique key
  collides and the second sign-in creates another account) and both injected link write paths.
- Reference fix: 95/95 hidden+project tests pass. Alternative PHP-side comparison design: 95/95.
  Hardening variant: 95/95. Refuse-all: 6 functional failures. Adjacent-API change: 1 project test.
  Partial levers behave as declared (schema 1 security failure; pad 2; SAML-only 4; OIDC-reverted
  6; link-reverted 8).
- Project tests for the affected area pass at the pinned commit and on the reference fix.
- No regression test for the advisory exists at the pinned commit (the only commit between pinned
  and fix adds a `DbCompatTest` method, which is not in the pinned tree).
- Installer builder (read-only inspection and direct SQL probe): `updateDatabase()` creates tables
  from `DatabaseStructureHelper::getDefaultTables()` and never applies the declared `indexes` /
  `foreign_keys`, so the screener's O8 claim that the installer's unique key conflates subjects is
  wrong — there is no unique key at all on installer-created tables.

## What could not be verified

- PostgreSQL behaviour (no server in the verifier; the reference code returns the bare column for
  non-MySQL, as the published fix does).
- The web installer end-to-end (its wizard was not driven; only its schema builder was inspected).
- `present_in_latest` for the installer route was judged from the current upstream tree
  (2026-10-23): the installer definitions still do not set a binary collation on the identity
  columns, while `sql/poweradmin-mysql-db-structure.sql` does carry the fix.

## Pattern B register rows

Appended to `build/audit/uncovered-routes.tsv` (task, repo, advisory, trap_ref, real_upstream,
present_in_latest, public_upstream_report, in_current_scope, built, note, disclosure_status):
two rows for the web-installer schema builder (OIDC and SAML identity tables), built=no, with the
note that the builder creates no unique index and that a charset-independent lookup comparison
closes the lookup path.

## Outside this advisory (not built on)

- Email-based account linking (`findUserByEmail`, `link_by_email`) is a separate trust decision and
  is preserved as-is by the functional suite.
- External group names mapped to local groups are an authorization concern, not identity
  resolution; untouched.

## Gate log

- static: PASS (2026-10-24T05:46Z).
- nop: PASS (2026-10-24T06:08Z) — all 9 security tests fail on the injected vulnerable tree, all
  functional and project tests pass.
- oracle: PASS (2026-10-24T06:12Z) — three reference-fix runs, each reward 1.0 with identical
  results (9 security + 86 functional/project tests).
- patches: PASS (2026-10-24T06:24Z) — every declared check behaved as declared:
  `security-fail-schema` 0.8889 (stability only), `security-fail-pad` 0.7778 (both trailing-space
  tests), `security-fail-saml` 0.5556, `security-fail-oidc` 0.3333, `security-fail-link` 0.1111,
  `functional-fail-refuse-all` 0.0 (7 functional failures), `functional-fail-adjacent-api` 0.0
  (project `DbCompatTest::testConcatSQLite`), `pass-hardening` 1.0, `pass-alternative` 1.0.
  The `blind-fix.patch` entry is listed as required but intentionally not written by the builder.

Note on the run environment: the shared Docker daemon's `/info` and `/containers/json` endpoints
wedged under the concurrent trial load, so the gate stages were run against a task-private dockerd
(`build/poweradmin-ds/priv-docker`, data root and socket local to this task, 10.150/10.151
address pools). No images or caches of the shared daemon were pruned or touched.
