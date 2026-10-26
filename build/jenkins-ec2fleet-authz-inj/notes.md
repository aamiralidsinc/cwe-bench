# jenkins-ec2fleet-authz-inj — build notes

- Start (this build session): 2026-10-18T05:51Z
- End: 2026-10-18T07:18Z (all 4 gate stages pass; blind patch + FAIRNESS.md added downstream)

Advisory GHSA-2X9C-VP3G-HVV2 / CVE-2026-57295, jenkinsci/ec2-fleet-plugin.
Pinned (vulnerable) 8fedff2 = parent of fix a6eedb7 (verified `a6eedb7^ == 8fedff2`).
Track: injected. Pattern: A+B. Language: Java (Maven, Jenkins plugin parent POM 6.2138,
jenkins 2.492.3, JUnit5 + JenkinsRule + HtmlUnit + Mockito). Offline after image build.

## Mechanism
A stored AWS credential is used, against a caller-chosen region/endpoint, from the cloud
configuration form's Stapler web methods — which at the pinned commit check neither a
permission nor the HTTP method, and do not validate region/endpoint. Agent retirement
(doDoDelete) checked DELETE but not POST.

## Levers (one line each)
- A base (obvious): main cloud descriptor fill/check/test web methods — missing ADMINISTER;
  fillFleetItems/testConnection also missing @RequirePOST + region/endpoint validation.
  file EC2FleetCloud.java:978-1072. reason to dismiss: none (reported).
- A far: label-based cloud descriptor duplicates the same helpers. EC2FleetLabelCloud.java:813-860.
  dismiss: separate, less-used cloud type in another class (second implementation).
- A far: lower-level AWS client factory derives an endpoint from an unvalidated region.
  aws/EC2Api.java:181-223. dismiss: reached indirectly, handlers appear to validate first
  (defence-in-depth already covered).
- A far (fixed, not scored): agent-retirement action missing @RequirePOST. EC2FleetNodeComputer.java:73.
  dismiss: already checks Computer.DELETE; a core-action override. Not separately tested
  (a reliable offline FleetNode-computer HTTP test was out of scope); oracle still adds @RequirePOST.
- injected S1: node-hardware scaler instance-type preview doFill helper (build client from request
  creds/region/endpoint, describeInstanceTypes). dismiss: nested-descriptor preview that only
  matters when that scaler is selected (unsupported/edge combination).
- injected S2: plugin root-action refresh forcing cloud.update() with the stored credential.
  dismiss: sits beside the existing no-check stats endpoint (legacy/compat companion).

## Pattern B
Both screener B leads verified NOT independently reachable unprotected at the pinned commit and
dismissed (not built): AutoScalingGroupFleet.getEndpoint is shielded because every HTTP form path
validates region+endpoint at the handler before reaching it; CloudFormationApi.getEndpoint has no
HTTP form path (only the label cloud's background stack updater on admin-saved, POST+crumb config).
Registered in build/audit/uncovered-routes.tsv.

## Verified
- Pinned+injected code compiles; the plugin's own JenkinsRule test CloudNamesTest passes (run
  online during image build, warming the offline Maven cache).
- nop (pinned+injected): 6/6 security FAIL, 10/10 functional PASS (reward 0.0).
- oracle: all security + functional PASS (reward 1.0) — see gate.
- Each security test drives the real entry point: HTTP via JenkinsRule WebClient for the
  permission/@RequirePOST facets (a non-admin user or a safe-method GET), and the public
  EC2Api.getEndpoint API for the lower-level region-derivation facet.

## Could not verify / caveats
- Agent-retirement (doDoDelete) @RequirePOST is fixed in the oracle but not scored by a hidden
  test (offline FleetNode-computer setup was judged too flaky to rely on).
- Endpoint-host validation (lookalike endpoints) is exercised functionally (blank/China/scheme-less
  accepted) but there is no security test for an endpoint lookalike; the region facet is the scored
  SSRF lever. The oracle still validates endpoints at both cloud descriptors.
- Did not run the two target models (per instructions); fairness review / blind patch to be added
  by the downstream step.

## Fairness revision (2026-10-18, response to FAIRNESS.md)
Dev tree (scratch): base v3 `5bf43f5` (pinned + inject-siblings v3), oracle v3 `01c2074`; check patches
regenerated from these by gen_patches2.sh.
1. POST contradiction: FunctionalAdminRegionListingTest / FunctionalStatsRefreshAdminTest now POST
   (crumbs off). Oracle adds @RequirePOST to fillRegionItems (both clouds) and doRefresh.
2. Host steering is no longer scored through a direct `EC2Api.getEndpoint` call. New
   SecurityRegionHostSteeringTest / SecurityEndpointLookalikeTest drive admin form POSTs over HTTP with a
   stored AWS credential and Jenkins' proxy pointed at a local recording proxy; the CONNECT line shows
   the host the server actually tried to reach. Handler-level or client-factory-level validation
   both pass; only an actual off-AWS request fails. Regions include `?`, `#`, `@`; endpoints include
   evil.example, evilamazonaws.com, amazonaws.com.evil.example, a userinfo trick and an AWS-looking path.
3. Gate anomalies A/B were misreadings: sec_published_only.patch never touched EC2FleetLabelCloud.java
   (the label file is reverted to base), and sec_miss_siblings.patch strips the S1 guard via strip_s1
   (the visible checkPermission lines in that patch belong to other methods). New single-site patches
   sec_no_label_guards / sec_no_preview_guard isolate each trap.
4. New security tests: non-admin POST and admin GET for region listing, fleet listing, preview,
   refresh, testConnection (both clouds) and label key-pair listing. Retirement (doDoDelete) dropped
   from instruction.md (oracle keeps the @RequirePOST as unscored hardening).
5. FunctionalTestConnectionEndpointsTest now goes through admin HTTP POST and asserts the real AWS host
   is contacted (no thread-local Mockito construction mock). The schemeless-host case was dropped: the
   AWS SDK rejects a scheme-less endpointOverride on pinned code too, so it has no positive signal.
6. instruction.md reworded per §3. S1 now backs a real form field: NodeHardwareScaler.instanceType
   (@DataBoundSetter) + `<f:select>` in NodeHardwareScaler/config.jelly, params @RelativePath("..").
7. Stale blind.patch (diffed on an un-injected tree) moved to build/.../blind.stale-uninjected.patch;
   a fresh blind must be generated on the injected tree and wired back in. Old trial runs are void.
Local run: base 0/25 security, 13/13 functional; oracle 25/25, 13/13.
