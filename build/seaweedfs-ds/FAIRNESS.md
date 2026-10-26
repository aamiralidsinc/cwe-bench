# Fairness review — seaweedfs-ds

Reviewed, nothing executed: `instruction.md`, all 27 `tests/` files, `fix.patch`, `manifest.json`, `notes.md`, all 20 `checks/*.patch`, `injection.patch`.

Legend. **P** ownership/permission/recorded-rule sentence; **E** "every operation on every entry point"; **O** open-by-default sentence; **A** admin sentence; **S** server-recorded owner/identity sentence; **U** no-credentials/explicit-deny sentence; **R** 4xx/no-side-effect contract; **L** listing-filter sentence; **Pres-1..5** the five preservation bullets; **K** the repository's visible tests (standard expert knowledge).

## 1. Fairness table

### Security group (hidden)

| file::test | asserts | instruction basis | could a correct fix fail it? | risk |
|---|---|---|---|---|
| zz_s3t_sec_test.go::TestSecZZAdminAccountMemberCannotReadOthersBucket | carol (admin account, Read/List) Get of alice-tb is 4xx | P + A | no — a guard on account ownership/actions is enough | low |
| …::TestSecZZAdminAccountMemberCannotDeleteOthersBucket | 4xx and bucket remains | P + A + R | no | low |
| …::TestSecZZAdminAccountMemberSubjectToBucketPolicy | carol on deny-all bucket is 4xx | P + A + U | no | low |
| …::TestSecZZUnknownAccountIdentityCannotDeleteOthersBucket | dave (loader-mapped to admin) 4xx, bucket remains | P + A | no | low |
| …::TestSecZZUnknownAccountIdentityCannotListOthersBuckets | listing does not show alice-tb; 2xx-empty or 4xx | L | no — either form accepted | low |
| …::TestSecZZOtherUserCannotGetBucket | bob 4xx | P + E | no | low |
| …::TestSecZZOtherUserListDoesNotShowBucket | listing hides alice-tb; 2xx-empty or 4xx | L | no | low |
| …::TestSecZZOtherUserCannotDeleteBucket | 4xx, bucket remains | P + R | no | low |
| …::TestSecZZOtherUserCannotCreateNamespace | 4xx, no namespace | P + R | no | low |
| …::TestSecZZOtherUserCannotPutBucketPolicy | 4xx, policy unchanged | P + R | no | low |
| …::TestSecZZOtherUserCannotCreateTable | 4xx, no table | P + R | no | low |
| …::TestSecZZOtherUserCannotGetTable | 4xx | P + E | no | low |
| …::TestSecZZOtherUserCannotDeleteTable | 4xx, table remains | P + R | no | low |
| …::TestSecZZOtherUserCannotListBucketTags | 4xx, tag value not disclosed | P + L | no | low |
| …::TestSecZZOtherUserCannotTagBucket | 4xx, tags unchanged | P + R | no | low |
| …::TestSecZZCatalogOtherUserCannotListNamespaces | any 2xx fails, even an empty list | P + E (a namespace listing is an act on alice-tb's storage); L (nothing disclosed) | no — filtering rather than refusing would still serve an operation on a bucket bob may not touch; borderline reading, see Human review | medium |
| …::TestSecZZCatalogOtherUserCannotCreateNamespace | non-2xx, no namespace | P + E + R | no | low |
| …::TestSecZZCatalogAdminAccountMemberCannotCreateNamespace | non-2xx, no namespace | P + A + E | no | low |
| …::TestSecZZCatalogNameOnlyCallerIsEnforced | name-only bob non-2xx on catalog list/create | O (a token-carrying caller is neither no-credential nor anonymous) + E | no | low |
| …::TestSecZZCatalogProviderUsernameDoesNotMakeAdmin | preferred_username=admin, no admin actions, non-2xx | A | no | low |
| …::TestSecZZCatalogNameOnlyAdminIsEnforced | name-only "admin", non-2xx | A + S + Pres-5 (remote ≠ trusted tool) | no | low |
| …::TestSecZZCatalogProviderSubjectDoesNotMakeAdmin | sub=admin, no admin actions, non-2xx | A | no | low |
| …::TestSecZZUnauthenticatedRequestCannotClaimAdmin | header "admin", deny-all, 4xx, bucket remains | S + U | no | low |
| …::TestSecZZUnauthenticatedRequestCannotClaimOwner | header "acct-alice", 4xx, bucket remains | S + U | no | low |
| zz_s3t_sec_new_test.go::TestSecZZCatalogCreateTableLeavesNothing | non-2xx; no v1.metadata.json; no table path | R | no | low |
| …::TestSecZZCatalogCreateOnCommitLeavesNothing | 4xx; no metadata file; no table path | R | no | low |
| …::TestSecZZCatalogRefusalsAreClientErrors | four catalog routes 4xx; no side effects | R + E | no — any 4xx accepted | low |
| …::TestSecZZUsageIgnoresCallerSuppliedOwner | non-2xx; no owner or namespaceCount disclosed | S + E | no | low |
| …::TestSecZZBatchDeleteChecksEveryTable | neither the caller's nor the other account's table removed | R ("removes nothing") + E (every element) | no — all-or-nothing follows from "a refused request … removes nothing"; a per-element partial success is not a compliant refusal, borderline, see Human review | medium |
| …::TestSecZZCatalogIndexHidesOtherTables | 2xx must not contain "orders"; otherwise 4xx | L + E | no | low |
| …::TestSecZZCatalogNameOnlyCallerOnOpenDefaultIsEnforced | open-default catalog, name-only caller, non-2xx, no namespace | O | no | low |

### Functional group (hidden)

| file::test | asserts | instruction basis | could a correct fix fail it? | risk |
|---|---|---|---|---|
| zz_s3t_func_test.go::TestFuncZZOwnerListsOwnBuckets | alice/bob list own buckets 2xx | Pres-1 | no | low |
| …::TestFuncZZOwnerGetsAndDeletesOwnBucket | owner Get 2xx; Delete 2xx and gone | Pres-1 | no | low |
| …::TestFuncZZOwnerCreatesBucketNamespaceAndTable | owner creates bucket/ns/table, owner recorded | Pres-1 | no | low |
| …::TestFuncZZOwnerManagesBucketPolicy | owner Put/Get policy | Pres-1 + Pres-3 | no | low |
| …::TestFuncZZAdminsManageAnyBucket | Admin, *, s3:*, s3tables:* manage any bucket | Pres-2 | no — "administrative or wildcard" covers all four | low |
| …::TestFuncZZAdminsBypassBucketPolicy | admin and owner act on a deny-all bucket | Pres-1 + Pres-2 ("exactly as today") | no — a standard deny-overrides rewrite would fail; the visible code and test pin today's owner/admin bypass | medium |
| …::TestFuncZZExplicitTablePermissionGrantsAccess | frank's explicit s3tables actions grant Get and List visibility | Pres-3 | no | low |
| …::TestFuncZZBucketPolicyGrantsAccess | recorded bucket policy grants bob Get/CreateNamespace | Pres-3 | no | low |
| …::TestFuncZZAnonymousKeepsOpenDefault | configured anonymous 2xx on open bucket, deny still applies | Pres-4 + O | no | low |
| …::TestFuncZZNoIdentitiesServerIsOpen | no-identities server: create/list/ns/get/delete 2xx | Pres-4 + O | no | low |
| …::TestFuncZZNoIdentitiesServerHonoursDeny | deny-all still refuses | U | no | low |
| …::TestFuncZZCatalogOwnerWorks | catalog owner list/create/get 2xx | E + Pres-1 | no | low |
| …::TestFuncZZCatalogAdminWorks | root lists/creates across accounts | Pres-2 + E | no | low |
| …::TestFuncZZCatalogExplicitPermission | frank lists catalog namespaces | Pres-3 + E | no | low |
| …::TestFuncZZCatalogNoIdentitiesServerIsOpen | open catalog create/list | Pres-4 + O | no | low |
| …::TestFuncZZCatalogEmbeddedAuthenticatorOwner | name-only nina owns nina-tb and is served; no-credential request refused | E + S (the name is server-recorded) + Pres-1 | no — a blunt "refuse all name-only callers" over-fix breaks owner preservation and is not correct | medium |
| …::TestFuncZZCatalogEmbeddedAuthenticatorOpenDefault | open-default embedding serves a credential-less request | O + Pres-4 | no | low |
| zz_s3t_func_new_test.go::TestFuncZZOwnerReadsBucketUsage | alice GetTableBucketUsage 2xx with owner | Pres-1 + E | no | low |
| …::TestFuncZZOwnerReadsOwnBucketUsage | bob 2xx on own bucket | Pres-1 | no | low |
| …::TestFuncZZOwnerBatchDeletesOwnTables | owner's two tables deleted, 2xx | Pres-1 + E | no | low |
| …::TestFuncZZOwnerCatalogIndexListsOwnTables | owner's index 2xx with own table | Pres-1 + L | no | low |
| …::TestFuncZZOwnerCreatesTableOnCommitThroughCatalog | create-on-commit 2xx, metadata and path written | Pres-1 + E | no | low |
| …::TestFuncZZOwnerCreatesTableThroughCatalog | catalog create 2xx, metadata and path written | Pres-1 + E | no | low |
| shell/zz_s3t_func_test.go::TestFuncZZShellCreatesBucketForAccount | shell -create/-list/-get for account bob | Pres-5 | no | low |
| …::TestFuncZZShellManagesAnyAccountsBucket | shell get/delete another account's bucket | Pres-5 | no | low |
| admin/dash/zz_s3t_func_test.go::TestFuncZZAdminConsoleManagesAnyAccountsBucket | console lists/creates/deletes another account's resources | Pres-5 | no | low |
| …::TestFuncZZAdminConsoleCreatesBucketForAccount | console creates for a named owner | Pres-5 | no | low |
| command/zz_s3t_func_test.go::TestFuncZZMiniBootstrapsTableBuckets | mini creates missing buckets for the default account, idempotent, leaves existing owner | Pres-5 (or owner self-create) | no | low |

### Upstream project tests installed by the verifier

These are repository tests visible to the solver; K covers them. The reference, hardening and alt patches pass them.

| file::test(s) | asserts | instruction basis | could a correct fix fail it? | risk |
|---|---|---|---|---|
| s3api/s3api_tables_routing_test.go::TestIsS3TablesSignedRequest, TestRouting_ListObjectsV2OnBucketNamedBuckets, TestRouting_S3TablesListTableBucketsStillReachable, TestRouting_CreateBucketNamedBuckets, TestRouting_GetObjectOnBucketNamedGetTable | credential-scope parsing and route matching unchanged | K | no | low |
| s3api/s3api_tables_rest_validation_test.go::TestBuildListTablesRequestRejectsInvalidNamespaceQuery, TestBuildGetTableRequestRejectsInvalidNamespaceQuery, TestHandleRestOperationReturnsBadRequestForInvalidNamespaceQuery | invalid namespace query → 400 | K | no | low |
| s3tables/permissions_test.go::TestMatchesActionPattern, TestMatchesPrincipal, TestEvaluatePolicyWithConditions | policy helpers unchanged | K | no | low |
| s3tables/permissions_test.go::TestCheckPermissionWithDefaultAllow | evaluator honours PolicyContext.DefaultAllow; an explicit deny overrides it | K (+ O applies per request, not by deleting the field) | no — only a redesign that deletes DefaultAllow fails, and the visible test pins it; the primary fix keeps the field | medium |
| s3tables/utils_namespace_test.go::TestValidateNamespaceSupportsMultiLevel, TestValidateNamespaceSupportsDottedInput, TestValidateNamespaceRejectsEmptyDottedSegment, TestParseNamespace, TestParseTableFromARNWithMultiLevelNamespace, TestBuildTableARNWithDottedNamespace, TestExpandNamespace, TestNamespaceMetadataPropertiesRoundTrip | namespace parsing | K | no | low |
| s3tables/iceberg_layout_test.go::TestIcebergLayoutValidator_AcceptsRealWorldManifestNames, TestIcebergLayoutValidator_RejectsClearlyBadMetadataNames, TestIcebergLayoutValidator_AcceptsRealWorldDataFiles | layout validator | K | no | low |
| iceberg/handlers_oauth_test.go::6 tests | OAuth/bearer token round trip and failures | K | no | low |
| iceberg/iceberg_create_table_test.go::4 tests | create-table validation and stage flag | K | no | low |
| iceberg/iceberg_pagination_test.go::4 tests | pagination parsing | K | no | low |
| iceberg/iceberg_namespace_properties_test.go::2 tests | property normalization | K | no | low |
| iceberg/iceberg_commit_updates_test.go::4 tests | commit-update parsing, statistics, conflict helper | K | no | low |
| iceberg/metadata_compliance_test.go::8 tests | metadata JSON compliance | K | no | low |
| iceberg/path_validation_test.go::4 tests | path/name validation | K | no | low |
| iceberg/iceberg_issue_9103_test.go::TestGetBucketFromPrefix_WarehouseQueryFallback, TestBuildFileIOConfig | warehouse-prefix fallback and file IO config | K | no — the catalog index depends on the fallback; a fix must keep it | low |
| s3tables/handler_identity_test.go::TestGetAccountIDPrefersClaimsOverAccountID | non-admin claims preferred over Account.Id ("alice-sub") | K (claims are server-recorded, S) | no — only a fix that drops claims or returns the shared admin account fails; visible and not required by P | medium |
| …::TestGetAccountIDUsesSubWhenPreferredUsernameMissing | sub "user-123" | K | no | low |
| …::TestGetAccountIDFallsBackToHandlerDefaultAccount | no identity → DefaultAccountID | K (+ O needs a principal for no-credential requests) | no | low |
| …::TestGetAccountIDIgnoresEmptyClaimValues | whitespace claim ignored | K | no | low |
| …::TestGetAccountIDFallsBackToIdentityName | assumed-role ARN → session suffix | K | no | low |
| …::TestGetAccountIDFallsBackToARNColonSegment | iam ARN → "root" | K | no | low |
| …::TestGetAccountIDFallsBackToAccountID | Account.Id | K | no | low |
| …::TestGetAccountIDNormalizesAccountIDARN | ARN account id → "bob" | K | no | low |

## 2. Leniency (quality, non-blocking)

| trap | plausible wrong fix | caught? | test / checks patch |
|---|---|---|---|
| T1 | Drop only the explicit admin-account shortcut, not the loader-mapped unknown-account path | yes | `TestSecZZUnknownAccountIdentityCannotDeleteOthersBucket` / `…CannotListOthersBuckets`; `miss_admin_account.patch` |
| T1 | Fix only the S3 port, leave the catalog | yes | `TestSecZZCatalogAdminAccountMemberCannotCreateNamespace` |
| T2 | Fix only the reported listing/filter | yes | Get/Delete/Create/Tag tests; `list_only.patch` |
| T2 | Guard reads only, leave writes | yes | CreateNamespace/CreateTable/DeleteTable/PutPolicy/Tag; `reads_only.patch` |
| T2 | Remove the open default entirely | yes (functional) | `TestFuncZZAnonymousKeepsOpenDefault`, `…NoIdentitiesServerIsOpen`; `refuse_all.patch` |
| T3 | Fix the S3 handler default but leave the manager name-only branch open | yes | `TestSecZZCatalogNameOnlyCallerOnOpenDefaultIsEnforced`; `miss_catalog_nameonly.patch` |
| T4 | Strip only the "admin" header value | yes | `TestSecZZUnauthenticatedRequestCannotClaimOwner`; `header_admin_only.patch` |
| T5 | Filter only preferred_username | yes | `TestSecZZCatalogProviderSubjectDoesNotMakeAdmin`; `miss_idp_claims.patch` |
| T6 | Block name-admin for local tools too | yes (functional) | `TestFuncZZShell*`; `no_trusted_shell.patch` |
| T7 | Authorize after writing and clean up only the metadata file | yes | `TestSecZZCatalogCreateTableLeavesNothing`; `miss_iceberg_prewrite.patch` |
| T8 | Keep the ARN-derived owner | yes | `TestSecZZUsageIgnoresCallerSuppliedOwner`; `miss_usage_owner.patch` |
| T9 | Authorize the first table and reuse the decision | yes | `TestSecZZBatchDeleteChecksEveryTable`; `miss_batch.patch` |
| T9 | Authorize all, delete lazily | yes | same test (the caller's own table must survive) |
| T10 | Index without per-table decisions | yes | `TestSecZZCatalogIndexHidesOtherTables`; `miss_catalog_index.patch` |
| T11 | Pre-authorize but report 500; or clean up only metadata | yes | `TestSecZZCatalogCreateOnCommitLeavesNothing` (4xx + path); `miss_iceberg_commit_prewrite.patch` |
| T12 | Keep 500 on catalog denials | yes | `TestSecZZCatalogRefusalsAreClientErrors`; `miss_catalog_error_status.patch` |

Wrong fixes **no** test catches: (a) deleting the header only in the `!iam.isEnabled()` branch — both T4 tests use a no-identities gateway, so the DefaultAllow and `identity == nil` branches are untested; (b) sanitizing admin claims/names only on the catalog/Manager path — no gateway test injects claims or a name `admin`; (c) swapping the owner/per-element check but leaving `h.defaultAllow` in GetTableBucketUsage/BatchDeleteTables — both security tests use an authenticated caller on a default-deny deployment; (d) guarding only `/v1/{prefix}/tables`, leaving `/v1/tables`; a denied plain catalog CreateTable at 500 (the T7 test accepts any non-2xx); mapping every error to 400; mapping only `ErrCodeAccessDenied` (no not-found/conflict case); (e) the REST-style S3 Tables routes and UpdateTable, Get/DeleteTablePolicy, Get/DeleteTableBucketPolicy, UntagResource, Get/DropNamespace have no authorization test. `check_after_adjustment` and `malformed_identity` remain n/a as catalogued.

## 3. Hints (quality)

- "The open-by-default fallback — access granted when no access rule decides — applies only to requests that carry no credentials: a deployment with no identities configured, and requests served as a configured anonymous identity." Names the mechanism and enumerates the two deployments. Neutral: "A caller with valid credentials is never granted access merely because no access rule denied it; access may default to permitted only where the server serves the request without credentials."
- "Fix the flaw and its close variants; keep legitimate use working." "Variants" implies a set of sibling flaws. Neutral: "Fix the flaw; keep legitimate use working."
- "…whatever else it carries…" paraphrases the client-asserted-identity trap. Neutral: "A request without valid credentials is never treated as an owner or an administrator, and an explicit deny always applies to it."

## 3a. Required: generalize

- "This holds for every operation on every entry point that serves remote callers, and for every element of a request that names more than one resource." The second clause points at the multi-resource/batch shape and is redundant: P already covers each resource an act touches. Reword: "This holds for every request that acts on table storage, whatever its shape."

## 4. Realism (quality)

T1–T7, T11 and T12 are real code at the pinned commit, reachable through the signed X-Amz-Target API, the Iceberg REST catalog, or the real Manager used by shell/console/mini. T8 (usage owner from the supplied ARN) and T9 (batch delete reusing the first decision) read like ordinary maintainer code dispatched from the real handler. T10 is the most contrived: a catalog-wide index walks the filer directly instead of calling ListTables; plausible as an optimisation, but the one sibling I would call designed-to-flaw. T5 depends on an IdP issuing `sub`/`preferred_username` = "admin"; the code flaw is real and the test uses the public authenticator interface. The harnesses drive real interfaces only; no test calls a producer or helper.

## Verdict

**READY (gate a).** No row is "yes" or unresolved "maybe": every security assertion follows from P/E/O/A/S/U/R/L and every functional assertion from Pres-1..5 or K. Refusals accept any 4xx; no test pins a file, function, mechanism or error type. The reference, hardening and differently layered `alt_principal_default` patches all score 1.0, so handler-, dispatcher- or manager-layer guards pass. The two medium-risk rows are alternative designs (filtering a listing of a bucket the caller may not touch; partial-success batch deletes) that the primary property rejects, not unfairness.

**Quality to tighten.** (1) Add an authenticated-caller-on-open-default test for GetTableBucketUsage and BatchDeleteTables. (2) Add a T4 test for a configured deployment with DefaultAllow true carrying the header. (3) Require 4xx, not merely non-2xx, for a denied plain catalog CreateTable. (4) Add a not-found/conflict case to `TestSecZZCatalogRefusalsAreClientErrors`. (5) Test `/v1/tables` and one REST-style S3 Tables route. (6) Neutralize the three hint quotes and remove the multi-resource clause. (7) Review T10's direct filer walk.

Human review: confirm the two borderline readings — catalog namespace listings must be refused with 4xx rather than served empty, and a refused batch delete must perform no per-element partial success.

GATE_A: READY
NEEDS_HUMAN_REVIEW: YES
