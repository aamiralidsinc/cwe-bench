# seaweedfs-s3tables-authz — build notes (build-v1)

Start: 2026-10-17T06:20Z. End: see the bottom of this file.

## Levers (one line each)
- T1 (A, landing + shared principal helper): a non-admin identity in the shared admin account (an explicit member, or one whose configured account does not exist and which the config loader maps to admin) is treated as admin. weed/s3api/s3tables/handler.go:208-219; producer auth_credentials.go:631-637.
- T2 (A, shared evaluator): the open-by-default fallback applies to authenticated callers on every handler of a static-identities gateway. permissions.go:121-127,180-183; 28 policy contexts in handler_*.go; s3api_tables.go:75-77.
- T3 (A, far site / defaults route): the Iceberg catalog's S3 Tables manager is forced open whatever its authenticator says, and name-only callers count as unauthenticated. manager.go:22-26; iceberg/server.go:47-55. The shell must keep acting for any account.
- T4 (B): a request without credentials picks its principal through the internal account header (`s3-account-id`, value admin or the owner's account), bypassing an explicit Deny. handler.go:229-233 via s3api_tables.go:685-688.
- T5 (B): an identity-provider claim (sub / preferred_username) equal to `admin` becomes the admin principal without admin permissions. handler.go:190-205.

## Verified
- The pinned commit b56d155 is the direct parent of fix b134638, so no commits lie between them and none of the advisory's regression tests are present (handler_identity_test.go additions and manager_test.go are absent).
- Earlier hardening is already at the pinned commit and kept: account-less identities get their own account (accountForUnscopedIdentity), and STS sessions get a distinct owner (#9963). So the "account-less" shape does not reproduce through the loader. T1 uses the two loader shapes that still map to admin.
- Every security test fails on the pinned code (18/18) through real entry points:
  - S3 Tables API: SigV4-signed requests to the real gateway routes, with identities from LoadS3ApiConfigurationFromBytes.
  - Iceberg REST catalog: wired as in weed/command/s3.go, or with an embedding authenticator.
  - Backing store: an in-memory gRPC filer on loopback.
- Functional tests pass on the pinned code (220/220), including the project's own s3tables and iceberg packages and the gateway's S3 Tables routing tests.
- Oracle (published fix, source only, plus fixes for T4 and T5) scores 1.0.
- T4 fix placement: the oracle strips the client's account header in the gateway auth wrapper. The handler keeps its header fallback, which the project's own TestGetAccountIDFallsBackToAmzAccountIdHeader pins for in-process callers.
- Each lever has a security_fail patch that misses only that lever; all were run locally before the gate.
- Pattern B rows: present_in_latest was checked read-only against origin/master ad24869 (2026-10-16).
  - T5: unchanged in latest.
  - T4: latest guards only the `admin` header value; an owner account id still resolves.

## Could not verify
- Whether a real OIDC provider would issue `preferred_username` = `admin` to an attacker (T5) depends on the IdP. The test uses an embedding authenticator.
- The T4 impact needs a deployment that serves requests without credentials (no identities, or advanced IAM with default-allow), plus a bucket with an explicit Deny.

## Out of scope (not followed)
- Regular S3 handlers also read `s3-account-id` (s3api_acp.go:11, s3api_bucket_handlers.go:562/804). Whether a client value survives on zero-config S3 routes was not checked.
End: 2026-10-17T07:25Z. Gate: static (only the blind patch and FAIRNESS.md missing, left for others), nop PASSED, oracle PASSED (3 identical runs), patches PASSED (19 checks).

## Fairness revision (2026-10-17, after FAIRNESS.md)
- The bare-`NewManager()` functional tests are gone. The admin console is now tested through `NewAdminServer` and its HTTP handlers (weed/admin/dash::TestFuncZZAdminConsole*), and the `weed mini` bootstrap through `ensureMiniTableBuckets` (weed/command::TestFuncZZMiniBootstrapsTableBuckets). A fix that marks those tools as trusted passes.
- T6 (new, pattern B): an embedding authenticator caller reported only by the name `admin` became administrator through the catalog, and the published fix and the old oracle both allowed this. Test: TestSecZZCatalogNameOnlyAdminIsEnforced. The oracle now resolves the admin principal only for trusted handlers or identities with an admin action, and marks the admin console and mini as trusted. miss_name_admin.patch = oracle without that guard.
- Leniency: bob GetTable/DeleteTable/ListTagsForResource/TagResource tests and a `sub`=admin claim test were added. table_reads_open.patch (default-allow left raw on the table, table-policy and tag read paths) must security_fail.
- admin_requires_action.patch is now an alternative (expect pass): the evaluator requires an admin action, with the console and mini trusted. no_trusted_console.patch must functional_fail.
- P2 in instruction.md was reworded so it no longer lists the variants.
