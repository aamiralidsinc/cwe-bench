# FAIRNESS review: seaweedfs-s3tables-authz

Reviewer inputs: instruction.md, every file under tests/ (security, functional, harness, project copies, test.sh, score.py), solution/fix.patch, manifest.json, notes.md, checks/*.patch (read in full: miss_header, drop_header_fallback, alt_principal_default, admin_requires_action, gateway_closed_when_auth, no_trusted_shell, miss_idp_claims; others judged from the manifest and their names). Nothing was run. The repository source is not available here, so claims about upstream call sites (for example, which code the admin console calls) come from the manifest, notes and tests, and I could not check them against the source.

Abbreviations: P1–P4 = the four bullets under "Security properties". C-x = bullets under "Contracts". KW = the "keep working exactly as today" list.

## 1. Per-test table

### Security group (`weed/s3api`, 18 tests)

| Test | Asserts | Fairness basis | Could a correct fix fail it? | Risk |
|---|---|---|---|---|
| TestSecZZAdminAccountMemberCannotReadOthersBucket | carol (account `admin`, actions Read/List) gets a 4xx on GetTableBucket alice-tb | P2 "not its account"; C-1 4xx | no | low |
| TestSecZZAdminAccountMemberCannotDeleteOthersBucket | carol's Delete alice-empty returns 4xx, and the bucket still exists | P2, C-1 | no | low |
| TestSecZZAdminAccountMemberSubjectToBucketPolicy | carol's Get on the deny-all bucket returns 4xx | P2, P1 | no | low |
| TestSecZZUnknownAccountIdentityCannotDeleteOthersBucket | dave (account id not configured, so the loader maps him to admin) gets 4xx on Delete, and the bucket survives | P2 "not its account" | maybe. A fix that makes the config loader reject an unknown account id makes `zzNewGateway` t.Fatalf. Every security test then fails, and the change also breaks plain-S3 startup, so it is a poor fix anyway | low |
| TestSecZZUnknownAccountIdentityCannotListOthersBuckets | dave's listing omits alice-tb, or he gets a 4xx | P1, C-1 "Listings leave out…" | no | low |
| TestSecZZOtherUserCannotGetBucket | bob (other account, no table permissions) gets 4xx on Get | P1, P3 | no | low |
| TestSecZZOtherUserListDoesNotShowBucket | bob's listing omits alice-tb | P1, C-1 | no | low |
| TestSecZZOtherUserCannotDeleteBucket | bob gets 4xx on Delete; the bucket survives | P1, P3 | no | low |
| TestSecZZOtherUserCannotCreateNamespace | bob gets 4xx on CreateNamespace; no namespace is created | P1, P3 | no | low |
| TestSecZZOtherUserCannotPutBucketPolicy | bob gets 4xx on PutTableBucketPolicy; the stored policy is unchanged | P1, P3 | no | low |
| TestSecZZOtherUserCannotCreateTable | bob gets 4xx on CreateTable; no table is created | P1, P3 | no | low |
| TestSecZZCatalogOtherUserCannotListNamespaces | Iceberg: bob gets a non-2xx with no "sales" in the body | P1 "every front end"; C-1 Iceberg clause | no | low |
| TestSecZZCatalogOtherUserCannotCreateNamespace | Iceberg: bob gets a non-2xx; no namespace is created | P1, C-1 | no | low |
| TestSecZZCatalogAdminAccountMemberCannotCreateNamespace | Iceberg: carol gets a non-2xx; no namespace is created | P2, P1 | no | low |
| TestSecZZCatalogNameOnlyCallerIsEnforced | an embedding authenticator reports only the name "bob" with defaultAllow=false; List and Create namespaces are refused | C-2 "embedded with its own authenticator… whatever caller that authenticator reports" | no | low |
| TestSecZZCatalogProviderUsernameDoesNotMakeAdmin | an IdP identity with `preferred_username=admin` and actions [Read] cannot CreateNamespace in a deny-all bucket | P2 "anything its identity provider asserts" | no | low |
| TestSecZZUnauthenticatedRequestCannotClaimAdmin | on a server with no identities, an unsigned Delete carrying `S3-Account-Id: admin` on a deny-all bucket gets 4xx; the bucket survives | P4 | no | low |
| TestSecZZUnauthenticatedRequestCannotClaimOwner | the same request with the header set to the owner's account gets 4xx | P4 "never acts as an owner" | no | low |

### Functional group: hidden tests

| Test | Asserts | Fairness basis | Could a correct fix fail it? | Risk |
|---|---|---|---|---|
| weed/s3api::TestFuncZZOwnerListsOwnBuckets | alice and bob each list their own buckets, though neither holds a ListTableBuckets permission | KW owners | maybe: a fix that adds a stricter account-level ListTableBuckets gate. "owners keep working" covers this | low |
| ::TestFuncZZOwnerGetsAndDeletesOwnBucket | the owner can Get and Delete her own bucket | KW owners | no | low |
| ::TestFuncZZOwnerCreatesBucketNamespaceAndTable | alice (holding s3tables:CreateTableBucket) creates a bucket owned by acct-alice, then a namespace and a table | KW owners and explicit permissions | no | low |
| ::TestFuncZZOwnerManagesBucketPolicy | the owner can Put and Get her bucket policy | KW owners | no | low |
| ::TestFuncZZAdminsManageAnyBucket | Admin, `*`, `s3:*` and `s3tables:*` identities can Get, List-all, CreateNamespace and Delete another account's bucket | KW "administrative or wildcard permissions" | maybe: a fix that stops treating `s3:*` as table-admin. "wildcard permissions… exactly as today" covers this | low |
| ::TestFuncZZAdminsBypassBucketPolicy | the admin and the owner can both Get a deny-all bucket | KW "exactly as today" (owners and admins are exempt from bucket Deny today) | maybe: an engineer who applies AWS semantics (explicit Deny binds the owner) fails. Only KW "exactly as today" makes this fair; the instruction never says owners bypass Deny | low |
| ::TestFuncZZExplicitTablePermissionGrantsAccess | frank (s3tables:GetTableBucket and ListTableBuckets) can Get alice-tb and sees it in his listing | KW explicit permissions; P1 | no. Frank holds both permissions, so filtering the listing on either one passes | low |
| ::TestFuncZZBucketPolicyGrantsAccess | a policy Allow for acct-bob grants bob Get and CreateNamespace | KW bucket policies | no | low |
| ::TestFuncZZAnonymousKeepsOpenDefault | the configured anonymous identity still gets the open default on Get and List, and a Deny still applies | P3 "served by a configured anonymous identity"; KW | no | low |
| ::TestFuncZZNoIdentitiesServerIsOpen | with no identities, unsigned Create, List, CreateNamespace, Get and Delete work | P3, KW | no | low |
| ::TestFuncZZNoIdentitiesServerHonoursDeny | with no identities, an unsigned Delete on a deny-all bucket is refused | P4 | no | low |
| ::TestFuncZZCatalogOwnerWorks | Iceberg: the owner can list, create and get namespaces | KW owners | no | low |
| ::TestFuncZZCatalogAdminWorks | Iceberg: the Admin identity can list and create in other accounts' buckets | KW admins | no | low |
| ::TestFuncZZCatalogExplicitPermission | Iceberg: frank with s3tables:ListNamespaces can list | KW explicit permissions | no | low |
| ::TestFuncZZCatalogNoIdentitiesServerIsOpen | Iceberg with no identities is open for unsigned requests | P3, KW | no | low |
| ::TestFuncZZCatalogEmbeddedAuthenticatorOwner | an embedding authenticator with defaultAllow=false: the name-only owner "nina" can list and create; an unsigned request is refused | C-2, KW owners | maybe: a fix that treats every name-only caller as an untrusted non-principal fails. C-2 covers this | low |
| ::TestFuncZZCatalogEmbeddedAuthenticatorOpenDefault | an embedding authenticator with defaultAllow=true: an unsigned request still lists | P3, KW "requests with no credentials" | no | low |
| weed/s3api/s3tables::TestFuncZZManagerAdminConsoleIdentity | a bare `NewManager()` (not marked trusted) with identity name "admin" and **no permissions** can Get, CreateNamespace and Delete another account's bucket | KW "admin console… act for any account they name" | **yes.** P2 says a name never makes an identity an administrator. A fix that follows P2 in the evaluator or the principal derivation fails this test, even when the engineer also marks the real admin-console call site as trusted, because the test calls `NewManager()` directly and not the console code. checks/admin_requires_action.patch is exactly that fix (published fix + T4/T5 + "admin principal needs an admin action") and is expected to `functional_fail` on this test | **high** |
| weed/s3api/s3tables::TestFuncZZManagerDefaultAccountBootstrap | a bare `NewManager()` with DefaultAccountID creates a bucket; a second create returns BucketAlreadyExists | KW `weed mini` | maybe: a fix that makes untrusted `NewManager()` require an explicit CreateTableBucket permission. It passes today and under the oracle only because principal == owner | low |
| weed/shell::TestFuncZZShellCreatesBucketForAccount | `s3tables.bucket -create/-list/-get -account bob` works | KW shell "act for any account they name" | no | low |
| weed/shell::TestFuncZZShellManagesAnyAccountsBucket | the shell, acting as account "ops", can Get and Delete acct-alice's bucket | KW shell | no | low |

### Functional group: the project's own tests (restored from pristine)

| Test(s) | Asserts | Fairness basis | Could a correct fix fail it? | Risk |
|---|---|---|---|---|
| s3tables::TestGetAccountIDFallsBackToAmzAccountIdHeader | `getAccountID` still reads the account header when no identity is present | "Do not modify tests"; the test is visible in the repo | maybe: the most natural T4 fix removes the header read in the handler (checks/drop_header_fallback.patch, `functional_fail`). The test is visible and fails when the package's tests run, so a competent engineer finds it and strips the header at the gateway instead | low–medium |
| s3tables::TestCheckPermissionWithDefaultAllow | `CheckPermissionWithContext` with DefaultAllow=true allows a non-owner principal | visible test | maybe: a T2 fix inside the evaluator ("ignore DefaultAllow for named principals") fails it. The test is visible, so the engineer moves the fix to the call sites | low |
| s3tables::TestGetAccountIDPrefersClaimsOverAccountID / UsesSub… / IgnoresEmptyClaimValues | with Account.Id = admin, a `sub` or `preferred_username` claim still becomes the principal | visible | no. The claims are non-admin values | low |
| remaining s3tables, iceberg and gateway routing/validation tests | existing behaviour | visible | no | low |

## 2. Leniency

| Property / trap | Most plausible wrong fix | Caught? |
|---|---|---|
| P1/T2 open-default for authenticated callers | fix only the ListTableBuckets filter (the screener's tempting fix) | yes: OtherUserCannotGet/Delete/CreateNamespace/… (checks/list_only.patch) |
| P1/T2 | fix read paths only | yes: OtherUserCannotDelete/PutBucketPolicy/CreateTable (checks/reads_only.patch) |
| P1/T2 | patch the `DefaultAllow:` call sites one at a time and miss handler_policy tag operations or the table operations (Get/Delete/UpdateTable, ListTables, Delete/GetNamespace, TagResource/UntagResource/ListTagsForResource, Get/DeleteTablePolicy) | **no**. The tested S3 Tables operations are GetTableBucket, ListTableBuckets, DeleteTableBucket, CreateNamespace, PutTableBucketPolicy and CreateTable. No test covers tags, table-level read/delete/update, namespace get/delete, or table policies |
| P1 refusal shape | refuse with 500 | yes on S3 Tables (4xx required; checks/deny_as_500.patch) |
| P1 listing | filter the listing on the wrong owner field | yes (checks/list_wrong_owner.patch) |
| T1 admin account | guard only explicit `account: admin`, not the loader's unknown-account mapping | yes: UnknownAccountIdentity* (checks/miss_admin_account.patch covers the whole lever) |
| T2 gateway default | turn off default-allow whenever identities exist | caught as functional_fail: AnonymousKeepsOpenDefault (checks/gateway_closed_when_auth.patch) |
| T3 catalog | fix only the S3 Tables port | yes: Catalog* tests (checks/miss_catalog.patch) |
| T3 name-only | treat name-only callers as unauthenticated, then open | yes: CatalogNameOnlyCallerIsEnforced |
| T3 / P2 name-only "admin" | leave the oracle as it is: an embedding authenticator that reports only the name `admin` becomes administrator through the catalog (the `NewManager()` path resolves principal "admin", and the evaluator lets admin win outright) | **no**, and the **oracle itself** has this behaviour, which contradicts P2 ("not … its name") and C-2 ("properties hold for whatever caller that authenticator reports") |
| T4 header | strip or ignore only the value `admin` | yes: CannotClaimOwner (checks/header_admin_only.patch) |
| T4 | strip the header only when no identities are configured, not on the advanced-IAM default-allow path that lets failed signatures through | **no**. Only the no-identities server is tested |
| T5 IdP claims | guard `preferred_username` but not `sub` = admin | **no**. Only `preferred_username` is tested |
| T5 | fix T1 at the Account.Id step only | yes: CatalogProviderUsernameDoesNotMakeAdmin (checks/miss_idp_claims.patch) |
| Catalog breadth | protect namespaces but not catalog table operations (load/create/drop table, commit) | **no** catalog table-operation security test. Risk is reduced because the catalog shares the manager/handler path |
| Adjacent API | break the shell | caught as functional_fail (checks/no_trusted_shell.patch) |

Wrong fixes that no test catches:
1. Per-call-site T2 fixes that miss the tag, table-policy, table or namespace get/delete handlers.
2. A name-only `admin` caller from an embedding authenticator stays admin (the oracle does this too).
3. The T4 header survives on the advanced-IAM default-allow path.
4. A `sub` claim equal to `admin`.
5. Catalog table-level operations.

## 3. Hints in instruction.md

- P2: "Only an identity granted administrative permissions is an administrator. Nothing else about an identity makes it one: not its account, its name, or anything its identity provider asserts." This is a list of the trap variants: account = T1, IdP assertions = T5. "its name" also contradicts TestFuncZZManagerAdminConsoleIdentity (see §1). Proposed wording: "Only an identity granted administrative permissions is an administrator; no other attribute of an identity makes it one." This still covers T1 and T5 without listing them.
- P4: "A request without valid credentials never acts as an owner or an administrator, whatever else it carries". This paraphrases the T4 mechanism (a client-carried value). It is a property-level statement and is needed so that CannotClaimOwner is fair. Acceptable; optionally drop "whatever else it carries".
- C-2: "The catalog server may be embedded with its own authenticator." This names the T3 / embedding route. It is needed for the fairness of three tests (NameOnly, EmbeddedOwner, EmbeddedOpenDefault). Acceptable.
- P3: "servers with no identities configured, and requests served by a configured anonymous identity". This states the exact boundary of the fix, but it is required for functional fairness. Acceptable.
- No file, function, or leak_terms entry appears in the instruction, and the instruction does not state a flaw count. "`s3tables.*` commands" names shell commands, which is acceptable as a functional contract.

## 4. Realism

- T1: the published fix site. The loader mapping an unknown (for example, mistyped) account id to `admin` is real loader behaviour per the manifest. Realistic.
- T2: published. 28 raw `DefaultAllow: h.defaultAllow` sites. Realistic.
- T3: published (manager, server, shell). Realistic.
- T4: unmodified upstream code; the notes say it is still present on master for owner values. Realistic. Reachable only on open or default-allow deployments, as stated.
- T5: unmodified upstream code. Whether an attacker can obtain `preferred_username=admin` depends on the IdP (notes: could not verify). The test uses a synthetic embedding authenticator (`zzTokenAuth` / `zzIdpIdentity`) through the real `S3Authenticator` interface. This is plausible but somewhat contrived as an exploit path. Acceptable because the instruction states the property.
- The harness wires the real `registerS3TablesRoutes`, the loader, SigV4, `iceberg.NewServer`, and the shell command `Do`. Nothing looks planted in the product code.
- TestFuncZZManagerAdminConsoleIdentity and TestFuncZZManagerDefaultAccountBootstrap claim to stand in for the admin console and `weed mini`, but they call `NewManager()` directly. I could not check whether those tools really call a bare `NewManager()` with the name "admin" (no repo here). Either way, the tests pin library defaults and do not exercise the tools.

## 5. Verdict: NOT READY

Required changes:

1. **TestFuncZZManagerAdminConsoleIdentity (high).** It requires that an untrusted `NewManager()` caller named "admin" with no permissions be an administrator. That contradicts P2. Rewrite it to drive the real admin-console entry point, so that a fix which marks the console as a trusted tool passes. Do the same for the `weed mini` bootstrap test. Then re-run checks/admin_requires_action.patch combined with a trusted admin-console call site: it should pass, and should be listed as an `alternative`. If the console cannot be driven in-process, the only alternative is to drop "its name" from P2 and add a contract that in-process manager callers act as the account they name. That is weaker and leakier.
2. **The oracle and the instruction disagree on a name-only `admin` from an embedding authenticator.** After (1), add a security test where `zzTokenAuth` reports only the name `admin`, defaultAllow=false, and calls CreateNamespace in a deny-all bucket. It must be refused. Then extend fix.patch so that only trusted managers honour a bare "admin" name. Alternatively, narrow C-2/P2; do not leave the contradiction in place.
3. **Leniency (medium).** Add bob security tests for at least TagResource (or ListTagsForResource) and DeleteTable/GetTable on alice-tb. Add a checks patch that leaves `h.defaultAllow` in handler_policy.go and handler_table.go read paths, and it must `security_fail`. Optionally add a `sub`=admin variant to the T5 test.
4. Reword P2 as proposed in §3.
