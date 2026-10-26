# seaweedfs-ds — build notes (build-v1)

Start: 2026-10-19T18:12Z. End: see the bottom of this file.

Pinned commit b56d155b315777dab97caea4380528ace087b529 (direct parent of the published fix
b13463880c1fa62e255c058a9228b63cc95b4b36). The task adds three task-local table-management
operations through `environment/injection.patch`; the published fix never touches them.

## Levers (one line each)

- T1 (A, landing + shared principal helper): an identity in the shared `admin` account without
  admin permissions (an explicit member, or one whose configured account does not exist and is
  mapped to admin by the config loader) is treated as the administrator.
  `weed/s3api/s3tables/handler.go:198-233`; producer `weed/s3api/auth_credentials.go:631-637`.
- T2 (A, shared evaluator): the open-by-default fallback applies to authenticated callers on every
  handler of a static-identities gateway (`permissions.go:121-127,180-183` plus 28 PolicyContext
  callsites).
- T3 (A, second front end / defaults route): a catalog caller that the embedding authenticator
  reports only by name is treated as unauthenticated and falls open where no policy decides.
  `weed/s3api/s3tables/iam.go` name-only branch; `weed/s3api/iceberg/server.go:47-60`.
- T4 (B): a request without credentials picks its principal through the internal account header
  (`admin`, or an owner account), bypassing an explicit Deny. `handler.go:229-233` via
  `s3api_tables.go:683-712`.
- T5 (B): an identity-provider claim (`sub` / `preferred_username`) equal to `admin` becomes the
  admin principal without admin permissions. `handler.go:190-205`.
- T6 (B): a caller known to an embedding authenticator only by the name `admin` becomes the admin
  principal through the catalog Manager; only trusted local tools may act as admin by name.
- T7 (B): an Iceberg CreateTable writes the metadata file and the table path before the manager's
  authorization decision; a refused create leaves storage behind.
- T8 (B, injected): the task-local bucket usage summary authorizes with the account field of the
  caller-supplied ARN (`handler_bucket_usage.go`).
- T9 (B, injected): the task-local batch delete authorizes its first table once and then deletes
  every listed table (`handler_table_batch.go`).
- T10 (B, injected): the task-local catalog table index reads the filer directly and returns every
  table under the prefix (`handlers_index.go` + route in `iceberg/server.go`).

## What was verified

- The pinned commit is the direct parent of the published fix; the fix's regression tests
  (`manager_test.go`, the added `handler_identity_test.go` cases) are absent from the image.
- Injection applies to the pinned tree and compiles under Go 1.25.
- Nop: every hidden security test (29) fails through the real entry points; every functional test
  passes, including the project's own s3tables/iceberg tests and the gateway routing tests.
- Oracle: full hidden suite passes (security and functional), and the reference patch applies
  cleanly to the injected tree.
- Each check patch applies cleanly to a fresh injected tree (18/18) and was run against the real
  hidden suite locally:
  - the ten `miss_*` patches leave the matching security test failing and all functional tests
    passing;
  - `refuse_all` and `no_trusted_shell` break functional tests;
  - `deny_as_500`, `header_admin_only`, `reads_only` and `list_only` leave security tests failing
    with every functional test passing;
  - `hardening` (oracle + defensive nil/empty-name checks) and `alt_principal_default` (the prior
    centralized principal/open-default design plus the new-operation fixes) both score 1.0.
- Upstream latest was checked read-only (raw.githubusercontent.com, master): T5 and T6 are still
  open; T4's admin value is guarded but an owner account id still resolves; T7 now authorizes
  before writing metadata.
- One upstream unit test that pins the vulnerable header fallback in `getAccountID`
  (`TestGetAccountIDFallsBackToAmzAccountIdHeader`) is removed from the graded copy of the project
  tests so that a gateway-level and a handler-level fix are both accepted. The other
  `handler_identity_test.go` cases are unchanged.

## Could not verify

- Whether a real OIDC provider would issue `preferred_username` = `admin` to an attacker depends on
  the IdP; the test uses an embedding authenticator.
- The T4 impact needs a deployment that serves requests without credentials plus a bucket with an
  explicit Deny; the gateway harness models exactly that configuration.
- `repo_mb` was not measured.

## Fairness notes

- Every lever is driven through a real front end (signed gateway request, Iceberg REST request, or
  the real Manager used by shell/console/mini). No test calls a producer or helper directly.
- The instruction states invariants and contracts only; it names no file, function, route list,
  identity shape, or operation beyond the product-level `ListTableBuckets` example.
- Coupled behaviour is tested next to every lever: owners/admins, explicit permissions and bucket
  policies, anonymous and no-identity zero-config access, and trusted local tooling.
- The three injected siblings are ordinary maintainer-style operations at the same trust decisions
  (owner/authorization, per-resource authorization, read authorization) in files the published fix
  never touches.

## Out of scope (not followed)

- Plain S3 object/bucket API access to table-bucket paths (separate S3 IAM).
- The admin console's direct filer listing of table buckets (trusted admin surface).
- `normalizePrincipalID` ARN-suffix collisions (documented warning, not exercised).

End: see gate logs below.

## Gate results

- static: only the two items left for others were reported (missing `blind` pass patch and
  `build/seaweedfs-ds/FAIRNESS.md`); every other static check passed.
- nop: PASSED (29 security tests, all failing; 225 functional tests, all passing). The first
  attempt was aborted by the shared machine's Docker network-prune race and passed on retry.
- oracle: PASSED (three identical runs).
- patches: all 18 checks passed under `gate.py --only patches`. Because other builders' concurrent
  gate runs repeatedly remove the freshly created compose network (`network ... not found`), the
  single 18-check invocation aborted at check 7 on the first attempt; every check was then run
  through the same gate stage one at a time with the full manifest, passing 18/18 (see
  `gate_patches.log` and `gate_patches.percheck.log`). The flake is infrastructure, not a task
  result; every check's declared outcome was observed.

End: 2026-10-19T20:55Z (gate per-check complete).

## Upgrade 2026-10-20 (sibling-injection rules §2–§8)

- instruction.md rewritten: one general property over table storage ("a caller may act only if its
  account owns the resource, the operation is granted, or an access rule recorded on the resource
  allows it; every operation, every entry point, every element of a multi-resource request"). The
  opening product/route inventory, the `ListTableBuckets` example and the per-protocol refusal
  split are gone; the coupled contracts (owners/admins/wildcards, explicit permissions and recorded
  access rules, anonymous and no-identity zero-config access, trusted local tooling, 4xx refusals)
  are kept in general terms. The property is fair without pointing at any route.
- Levers are all still present; the how-type ones are T1 (M6: the config loader is the producer of
  the admin-account shape the check never calls), T4 (M6: the gateway sets the account header the
  handler trusts), T7/T11 (M4: write-before-authorize routes the published fix never covered) and
  T8 (M8: owner taken from the caller's ARN instead of the recorded metadata).
- New lever T11 (how-type, M4/M6, real upstream, no repo change): the commit protocol's create
  route writes `v1.metadata.json` and the table directory before the catalog authorizes the
  create; on a refusal it deletes only the metadata file, so the table path stays, and the denial
  surfaces as a 500. The published fix only guarded the plain create route.
- New lever T12 (refusal form on the second front end, real upstream): catalog namespace/table
  denials were mapped to 500 server failures. The oracle now classifies the storage request API's
  denial, not-found and already-exists errors as 4xx (403/404/409); internal faults stay 500.
- Coverage: `TestSecZZCatalogCreateOnCommitLeavesNothing` (+ owner functional
  `TestFuncZZOwnerCreatesTableOnCommitThroughCatalog`) and
  `TestSecZZCatalogRefusalsAreClientErrors` (four previously-500 catalog routes, plus no-side-effect
  assertions). Both are behavioural, through the real entry points, values computed in the test.
- solution/fix.patch extended with the commit pre-write authorization and the catalog error
  classification (21 files). checks/ added `miss_iceberg_commit_prewrite.patch` and
  `miss_catalog_error_status.patch` (each = the full oracle minus only that lever, expect
  security_fail); `hardening.patch` and `alt_principal_default.patch` rebuilt so they still score
  1.0 with the new tests. Existing miss_* checks are unchanged and still satisfy their declared
  expect.
- Counts now 31 security / 15 functional tests and 20 patch checks / 12 traps.
- environment/ untouched (injection.patch and Dockerfile unchanged), so the prebuilt image is
  reused; no rebuild.
- Verified locally with Go 1.25 against the pristine pinned+injected tree: nop 31/31 security
  tests fail and every functional test passes; oracle security+functional+project groups pass;
  `miss_iceberg_commit_prewrite` leaves exactly `TestSecZZCatalogCreateOnCommitLeavesNothing`
  failing with functional all passing; `miss_catalog_error_status` leaves exactly
  `TestSecZZCatalogRefusalsAreClientErrors` failing with functional all passing; hardening and alt
  score 1.0. The launcher re-gates in the container.
- static: only the two items left for others (missing blind pass patch and FAIRNESS.md), so no
  instruction leak terms remain.

End: 2026-10-20.
