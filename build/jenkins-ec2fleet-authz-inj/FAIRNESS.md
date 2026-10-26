# FAIRNESS — jenkins-ec2fleet-authz-inj

Reviewer: pre-trial fairness/leniency review (BUILDER.md 3h). Nothing was run. I read:
instruction.md, all 15 test methods (12 files) in tests/, test.sh, score.py, solution/fix.patch,
environment/inject-siblings.patch, manifest.json, notes.md, every checks/*.patch, and
gate_report.partial.json. The pinned plugin source is not in the workspace (the Dockerfile clones
it), so I could not check claims about `RegionHelper`, the jelly views or the scaler's fields.

**Process note.** This is meant to be a *pre-trial* review, but trials have already run:
trial_mimo.out shows 2 runs and trial_deepseek.out shows 3, all with reward 0.0. The build dir has
no per-test results for those runs. The 0.0 rewards fit the contradictions in §1: a fix that
follows the instruction fails a functional test, and any functional failure zeroes the reward.

## 1. Per-test fairness

| Test (file::name) | Asserts | Instruction basis | Could a correct fix fail it? | Risk |
|---|---|---|---|---|
| security/SecurityCloudRegionPermissionTest::nonAdminCannotInvokeRegionListing | READ-only user, GET `EC2FleetCloud/fillRegionItems` → 4xx | Property 1 ("unless the requester is entitled"); Refusal form | no. A permission check (403) or POST-only (405) both pass. | low |
| security/SecurityCloudFleetPostTest::getRequestToFleetListingIsRefused | admin, GET `fillFleetItems` → 4xx | Property 1 ("and the request is a genuine state-changing submission") | no | low |
| security/SecurityLabelCloudRegionPermissionTest::nonAdminCannotInvokeLabelCloudRegionListing | READ user, GET label-cloud `fillRegionItems` → 4xx | Property 1 ("no matter which cloud type exposes it") | no. **But see §2, gate anomaly A.** | low (test) / high (gate evidence) |
| security/SecurityEndpointRegionValidationTest::malformedRegionDoesNotProduceOffAwsEndpoint | direct Java call `new EC2Api().getEndpoint(bad, null)` must throw, return null, or return an AWS host, for `evil.com/`, `evil.example/path`, `a/b`, `foo:9000/` | Property 2 ("No value of the caller-supplied region … may cause a credential-bearing call to be directed at" a non-AWS host) | **yes**. Validating region and endpoint in every HTTP handler, or inside `connect()` only, fully meets Property 2: no request can reach an off-AWS host. That fix still fails, because the test calls a credential-free public helper directly. `sec_published_only.patch` is exactly this handler-level fix, and the gate scores it as a *security* failure. The oracle is also inconsistent: `getEndpoint` returns an explicit endpoint unvalidated, so the helper only guards half of Property 2. | **high** |
| security/SecurityNodeHardwarePreviewTest::nonAdminGetToInstanceTypePreviewIsRefused | READ user, GET scaler `fillInstanceTypeItems` → 4xx | Property 1 ("previews") | no. **But see §2, gate anomaly B.** | low (test) / high (gate evidence) |
| security/SecurityStatsRefreshTest::nonAdminCannotTriggerRefresh | READ user, GET `ec2-fleet/refresh` → 4xx | Property 1 ("nor to refresh a cloud") | no | low |
| functional/FunctionalAdminRegionListingTest::adminCanListRegions | admin, **GET** `fillRegionItems` → 200, and the body contains `us-east-1` | Preservation ("Administrators must still use these operations") | **yes**. Property 1 says a credential-using listing needs "a genuine state-changing submission", and "Observed impact" calls the bare GET the attack. Adding `@POST`/`@RequirePOST` plus ADMINISTER to `doFillRegionItems` is the standard Jenkins hardening for credential-using fill methods (the real form sends fill requests as POST). That fix returns 405 here. **The repo's own blind patch (`checks/blind.patch`, expected `pass`) does exactly this (`@POST` on `doFillRegionItems` in both clouds), so it fails this test.** | **high** |
| functional/FunctionalAdminFleetPostTest::adminCanListFleetsViaPost | admin, POST (crumb issuer disabled) `fillFleetItems` → 200 | Preservation | no. The handler swallows the offline AWS failure. A fix that returns 400 on a blank `awsCredentialsId` would fail, but that is unlikely. | low |
| functional/FunctionalTestConnectionEndpointsTest::blankEndpointIsAccepted | direct Java call `new DescriptorImpl().doTestConnection("credentials","us-east-1","",null)` → OK (AwsPermissionChecker mocked) | Preservation ("a blank endpoint") | maybe. There is no Stapler request. A fix that checks the method by hand (`Stapler.getCurrentRequest2().getMethod()`) gets an NPE. A fix that rejects an unknown credential id fails too, because "credentials" does not exist. The instruction never says the method must work outside an HTTP request. | medium |
| functional/FunctionalTestConnectionEndpointsTest::mixedCaseChinaEndpointIsAccepted | same, region null, `HTTPS://EC2.CN-NORTH-1.AMAZONAWS.COM.CN` → OK | Preservation ("alternate (e.g. China) domains … mixed case") | maybe (same direct-call caveat) | medium |
| functional/FunctionalTestConnectionEndpointsTest::schemelessAwsHostIsAccepted | same, `us-west-2` + `ec2.us-west-2.amazonaws.com` → OK | Preservation ("a host given without a URL scheme") | maybe (same direct-call caveat) | medium |
| functional/FunctionalEndpointDerivationTest::derivesStandardAndChinaEndpoints | `getEndpoint` gives exact strings for us-east-1, cn-north-1 and us-gov-west-1 | Preservation ("Deriving a provider endpoint from an ordinary region name must behave exactly as today") | no | low |
| functional/FunctionalEndpointDerivationTest::blankRegionYieldsNoEndpoint | `getEndpoint(null,null)` and `getEndpoint("",null)` → null | standard expert knowledge: keep the existing null-in/null-out contract | maybe. A fix that throws on blank input is not clearly forbidden. | low |
| functional/FunctionalEndpointDerivationTest::explicitEndpointIsReturnedAsIs | an explicit valid endpoint is returned byte-for-byte | Preservation | maybe. A fix that canonicalises a valid endpoint fails (blind.patch's `normalizeEndpoint` does this, but only at the handler, so it passes). | low |
| functional/FunctionalStatsRefreshAdminTest::adminCanTriggerRefresh | admin, **GET** `ec2-fleet/refresh` → 200 | Preservation | **yes**. Property 1 names refresh and requires "a genuine state-changing submission rather than a safe, side-effect-free one". `@RequirePOST` on `doRefresh` is the fix the instruction asks for, and it fails this test. The oracle breaks the instruction here: it adds only ADMINISTER, so a lured admin GET still forces every cloud to `update()` with its stored credential. That is the CSRF case in "Observed impact". | **high** |

## 2. Leniency (wrong fixes vs. tests)

### Gate anomalies (must be explained before anything else)

- **A.** `sec_published_only.patch` adds `checkPermission(ADMINISTER)` to the label cloud's
  `doFillRegionItems`, the same line the oracle adds. gate_report.partial.json still lists
  `SecurityLabelCloudRegionPermissionTest` as failing for that patch.
- **B.** `sec_miss_siblings.patch` adds `checkPermission(ADMINISTER)` to
  `NodeHardwareScaler.DescriptorImpl.doFillInstanceTypeItems`. A READ-only GET must then get 403.
  The gate still lists `SecurityNodeHardwarePreviewTest` as failing for that patch.

So either the gate did not apply these patches as written, or the two tests fail for some reason
other than a missing guard. The second case would also endanger correct solver fixes. Either way,
these two `security_fail` results do not show that the label-cloud or node-hardware trap is caught.

### Mapping traps to wrong fixes

| Property / trap | Most plausible wrong fix | Caught? |
|---|---|---|
| base_authz_and_post | ADMINISTER everywhere, no POST | caught: SecurityCloudFleetPostTest (`sec_perm_only_no_post.patch`, gate shows that single failure) |
| Property 1, "entitled" half | `@RequirePOST` only (no permission) on fleet listing, preview, `testConnection` and label `fillEc2KeyPairNameItems`; ADMINISTER only on region listing and refresh, where the admin-GET functional tests forbid POST | **not caught**. No test sends a *non-admin POST*. A READ user can get a crumb and still drive the stored credential. Every security test is a GET, so 405 satisfies it. |
| base_authz_and_post | `testConnection` left fully open (both clouds) | **not caught**. No security test covers `testConnection`. |
| label_cloud_second_implementation | guard label `fillRegionItems` only, and leave `fillEc2KeyPairNameItems` / `testConnection` open (both take the request's region and endpoint and use the credential) | **not caught**. The manifest's `security_fail_patch` for this trap (`sec_published_only.patch`) *includes* the label guard, so it shows nothing (see anomaly A). No patch removes only the label guards. |
| ec2api_region_lower_level | blocklist only `/` and `:` in the region | **not caught**. `evil.com?x`, `evil.com#`, `x@evil.com` and `evil.com\\` give off-AWS or ambiguous hosts and are not in `badRegions`. |
| node_hardware_preview_injected | permission only, or POST only | each passes alone, because the test is a non-admin GET. The manifest's `sec_miss_siblings.patch` already has the permission check, so under the test as written it should *pass* (see anomaly B). |
| stats_refresh_injected | permission only (no POST) | not caught. The functional test *requires* this. Caught by sec_miss_siblings only for "no guard at all". |
| Property 2, endpoint half | validate region only and pass `endpoint=https://attacker.example` through | **not caught**. notes.md admits there is no endpoint-lookalike security test. `func_overbroad_endpoint.patch` fails only because it rejects blank and China endpoints, not because it accepts lookalikes. |
| retire agent (`doDoDelete` POST) | leave as is | **not caught**. It is untested, but the instruction lists it as a required property. |

Wrong fixes no test catches: POST-only (no permission) on fleet listing, preview, testConnection
and key-pair listing; open `testConnection` on both clouds; open label key-pair listing; no endpoint
validation at all; a partial region blocklist; refresh without POST; retire without POST.

`wrong_fix_catalogue.reads_only` says "there is no read-only subset a fix could guard". In fact a
fix can guard every helper with *either* POST *or* permission, never both, and pass. The
`one_role_or_direction` class is covered for only one handler, fleet listing.

## 3. Hints

- "to list the regions available to a credential, to list the fleets, to preview instance hardware,
  to "test" a connection, and so on" and "operations that refresh a cloud's live state from the
  provider and that retire an individual provisioned agent". Together these list every scored site,
  including both injected siblings. Proposed: "The plugin exposes a number of background helper
  endpoints and operations that use a stored credential to contact the provider or that affect
  provisioned agents."
- "no matter which cloud type exposes it, no matter whether the helper lists, tests, previews,
  refreshes or retires, and no matter whether it returns data, a status, or nothing". This points
  at the label-cloud trap and repeats the variant list. Proposed: "This holds for every such
  operation the plugin exposes, whatever it returns."
- "Deriving a provider endpoint from an ordinary region name must behave exactly as today." This
  points at `EC2Api.getEndpoint`. It is acceptable as a preservation contract once §5 item 2 is
  settled.
- "Retiring an agent must still work for a user who is allowed to retire that agent … even if they
  are not a server administrator." This points at the untested `doDoDelete` site and steers toward
  POST-only rather than ADMINISTER there. Keep it only if that site gets a test. Otherwise drop
  retirement from the instruction.

## 4. Realism

- S2 `EC2FleetStatsApi.doRefresh`: plausible. It sits next to the existing unguarded `doStats` in
  the same style, and it is reachable by GET through the real root action.
- S1 `NodeHardwareScaler.DescriptorImpl.doFillInstanceTypeItems`: the code pattern is plausible.
  But inject-siblings.patch adds no `instanceType` field, `@DataBoundSetter` or jelly view. If the
  scaler has no such field, the result is a `doFill` web method that no form ever calls, which
  looks planted. It is reachable only by a hand-built `descriptorByName/...$NodeHardwareScaler` URL.
  Builder to confirm a matching field and view exist, or add them.
- The `EC2Api.getEndpoint` facet is scored through a direct Java call, not the real HTTP entry
  point.
- blind.patch's file headers have no injected-sibling hunks and show no trace of the injected code.
  It looks like it was produced on, or diffed against, a tree *without* inject-siblings.patch. If
  so, the blind check does not reflect the solver's environment.

## 5. Verdict: **NOT READY**

Required changes:

1. **Fix the POST contradiction.** Change FunctionalAdminRegionListingTest and
   FunctionalStatsRefreshAdminTest to POST (crumb issuer disabled, as the other POST tests do). Add
   `@RequirePOST` to `doFillRegionItems` (both clouds) and to `doRefresh` in the oracle. Re-run
   alt_fix/hardening afterwards. Without this, the reference blind fix and any instruction-faithful
   fix score 0.
2. **SecurityEndpointRegionValidationTest.** Either drive it through HTTP (admin POST to
   `fillFleetItems`/`fillInstanceTypeItems` with `region=evil.com/`, asserting via a mocked
   `EC2Api`/client builder that no off-AWS endpoint is used), or reclassify it as functional/defence
   in depth. The instruction alone does not justify scoring it as security.
3. **Explain gate anomalies A and B** (patch application vs. test behaviour). Then add check patches
   that remove *only* the label-cloud guards and *only* the preview guard, and confirm each produces
   exactly one security failure. Correct the trap→patch mapping in manifest.json.
4. **Add security tests** for: a non-admin *POST* (crumb disabled) to `fillFleetItems` and to
   `fillInstanceTypeItems`; `testConnection` (non-admin POST, and GET) on at least one cloud; label
   `fillEc2KeyPairNameItems`; an endpoint lookalike (`https://evil.example`,
   `https://evilamazonaws.com`, `https://amazonaws.com.evil.example`); and region strings with
   `?`, `#` and `@`. Either test `doDoDelete` GET → 4xx, or remove retirement from the instruction.
5. **FunctionalTestConnectionEndpointsTest.** Call it through an admin HTTP POST, or add to the
   instruction that these helpers must also work when invoked programmatically with an unknown
   credential id.
6. Apply the §3 rewording. Confirm the S1 field/view exists.
7. Regenerate and re-gate blind.patch on the *injected* tree. As written it would fail
   FunctionalAdminRegionListingTest, SecurityNodeHardwarePreviewTest and SecurityStatsRefreshTest.
   Record it in the gate report; it is currently missing from it. Discard the 5 trial runs and
   re-run after the fixes.
