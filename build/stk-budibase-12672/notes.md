# stk-budibase-12672 — build notes

Start (UTC): 2026-10-26T02:09:42Z (recorded by the launcher)
End (UTC): 2026-10-26T03:00Z (gate runs recorded separately)

## Task

- Project: budibase/budibase, pinned at `5e19b935536d6d1be1f47100e43c6fb30917826e`
  (first parent of the published fix `8b1bca71501b11c68310351ef4f2c3028b2d5f08`;
  verified with `git cat-file -p 8b1bca71`).
- Advisory: GHSA-MQHR-6J6H-74P5 / CVE-2026-73407 (CWE-200): stored REST datasource
  credentials are attached before the destination is confirmed, so a query path that becomes an
  absolute URL — including through a parameter of a published PUBLIC query — sends them to an
  arbitrary server.
- Stacked pattern H4, three concepts.

## Levers (one line each)

- T1 (both; advisory route + how-type producer): the REST integration merges stored headers/auth
  before resolving the destination, and the only evidence of the authored destination is the saved
  path before run-time expansion, which lives in the query runner.
  `packages/server/src/integrations/rest.ts:669-687,722`; `packages/server/src/threads/query.ts:193-197`.
- T2 (deepseek; published far site): a same-origin request redirected to another origin keeps
  arbitrary datasource header names because the shared helper strips only four well-known names.
  `packages/backend-core/src/utils/outboundFetch.ts:139,181,244`; `rest.ts:802`.
- T3 (deepseek; uncovered route where the protection never existed): the stored OAuth2 client
  credential is re-sent to a redirect target in the token request body; every published fix commit
  leaves this call site alone. `packages/server/src/sdk/workspace/oauth2/utils.ts:68-70`.

Dropped from the reader's record: T6 (an OAuth2 connection id naming another workspace connection)
is the product's design — the query editor lists every workspace OAuth2 connection for every
datasource (`packages/builder/src/components/integration/rest/AuthPicker.svelte:30-36`), so a
security rule demanding per-datasource ownership would contradict legitimate use. Its fix commits
also never touched it.

## Verified

- The published fix diff and its own added suites (fetched read-only from the fix commit).
- Every lever's security test fails on the pinned tree and passes on the reference (see gate logs).
- The coupled functional values (same-origin relative/absolute, no-base-address bare host with
  credentials, parameterised same-origin, template base rewrite, same-origin redirect, other
  outbound callers following cross-origin redirects, 307/308 method/body, normal OAuth2 token
  acquisition) pass on the pinned tree and on the reference.
- Project suites for the touched modules: `packages/server/src/threads/query.spec.ts`,
  `packages/server/src/sdk/workspace/queries/queries.spec.ts`,
  `packages/backend-core/src/utils/tests/outboundFetch.spec.ts`.

## Could not verify / fairness notes

- The route-level and integration suites need Docker testcontainers (CouchDB/MinIO) and are not run;
  the same modules are driven directly. Recorded in the manifest.
- A datasource whose stored base address is itself a handlebars template is not required to keep
  working: the published fix compares the raw stored base, so such a datasource is refused rather
  than leaked. Not tested either way.
- Upstream current master (checked 2026-10-26) still leaves the token-request call site unprotected.

## Outside scope (one line)

- The advisory also names the earlier GHSA-3gp5 work; only the current advisory's protection is built.

## Local validation (probe image, jest, offline, no testcontainers)

| variant | security | functional | expected |
|---|---|---|---|
| pinned | 0/18 | 63/63 | nop contract |
| reference | 18/18 | 63/63 | oracle |
| alt_correct_fix (strip stored credentials instead of refusing) | 18/18 | 63/63 | pass |
| hardening | 18/18 | 63/63 | pass |
| miss_concept_initial | 6/18 | 63/63 | security_fail |
| miss_concept_rest_redirect | 14/18 | 63/63 | security_fail |
| miss_concept_oauth2_redirect | 16/18 | 63/63 | security_fail |
| reads_only | 17/18 | 63/63 | security_fail |
| check_before_expansion | 6/18 | 63/63 | security_fail |
| refuse_all | 18/18 | 55/63 | functional_fail |
| functional_overbroad (global redirect refusal) | 18/18 | 54/63 | functional_fail |
| upstream_fix (published fix only) | 16/18 | 63/63 | security_fail (recall) |
| control pinned | 0/12 | 63/63 | nop contract |
| control reference (published fix) | 12/12 | 63/63 | oracle |
| control_malformed_identity | 0/12 | 63/63 | security_fail |
| control_overbroad | 12/12 | 55/63 | functional_fail |

The security group is 11 direct-integration, 5 thread-runner and 2 stored-OAuth2 tests; the
functional group is 5 direct-integration, 2 shared-helper, 3 thread-runner, 3 OAuth2 and the three
project suites (6 + 13 + 34 cases).
