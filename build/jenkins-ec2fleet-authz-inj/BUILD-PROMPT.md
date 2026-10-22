# Build one security-fix benchmark task (build-v1)

## What this is
We build a security-fix benchmark from published, already-fixed advisories in open-source projects.
You build ONE task, from the advisory below.

The task pins the project at the commit just before the published fix and gives a solver agent that
code plus a short problem report (`instruction.md`). Hidden behavioural tests then score the
solver's fix. The tests check that the flaw is closed, using harmless inputs and markers, and that
legitimate use still works.

Everything stays on this machine. Describe each mechanism in one line in notes and reports; the
tests hold the detail, so never write exploitation steps out in prose. Stay inside this advisory's
own protection, in this repository, at the pinned commit. Note anything outside that scope in one
line in your report, and do not build on it.

Project root: `/home/mara/cwe-bench`. Task: `jenkins-ec2fleet-authz-inj`. Pattern: `A+B`. Track: `injected`.

## Goal and acceptance
- **The bar.** Two target models (DeepSeek V4.1 Flash, MiMo-V2.6-Pro) must each fail all 3
  finished attempts because of their own judgement.
- **Fairness.** Everything the tests require must be findable from `instruction.md` plus the code,
  or be standard expert knowledge. A careful engineer who knows where to look fixes it in about
  45 minutes.
- **What never counts as a failure:** timeouts, and runs cut by API or network errors.
- **Proof.** A task is built only when the gate passes. A task that misses the bar is reported as
  such, never shipped weaker.

## Inputs
- Advisory: GHSA-2X9C-VP3G-HVV2 / CVE-2026-57295 - jenkinsci/ec2-fleet-plugin - CSRF / missing permission check on Stapler form and web methods (CWE-352 with CWE-862), bundled with endpoint/region input validation (SSRF-style credential exfiltration). Whether a request may make Jenkins call AWS with a stored credential against a caller-chosen region/endpoint, or schedule an agent's EC2 instance for 
- Pinned (vulnerable) commit: 8fedff2a81c3f91c14e7a1f5ea5191063f3d43b3. Published fix: a6eedb7bc112de92bbba179c03840d845b845c82.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "screener_version": "screener-v2",
 "lessons_version": "lessons-v1",
 "model": "claude-opus-5-5",
 "entry_id": "22565",
 "advisory_ids": [
  "GHSA-2X9C-VP3G-HVV2",
  "CVE-2026-57295"
 ],
 "repo": "jenkinsci/ec2-fleet-plugin",
 "pinned_commit": "parent of a6eedb7bc112de92bbba179c03840d845b845c82 (parent_commit not given in candidate)",
 "fix_commits": [
  "a6eedb7bc112de92bbba179c03840d845b845c82"
 ],
 "trust_decision": {
  "summary": "Whether a request may make Jenkins call AWS with a stored credential against a caller-chosen region/endpoint, or schedule an agent's EC2 instance for termination, is decided in the cloud descriptors' Stapler web methods (needs POST + Jenkins.ADMINISTER) and in EC2FleetNodeComputer.doDoDelete (needs POST + Computer.DELETE); at the pinned commit the descriptor methods check neither and doDoDelete checks only DELETE, without POST.",
  "evidence": [
   "src/main/java/com/amazon/jenkins/ec2fleet/EC2FleetCloud.java:1016-1034",
   "src/main/java/com/amazon/jenkins/ec2fleet/EC2FleetCloud.java:1050-1057",
   "src/main/java/com/amazon/jenkins/ec2fleet/EC2FleetLabelCloud.java:819-826",
   "src/main/java/com/amazon/jenkins/ec2fleet/EC2FleetLabelCloud.java:839-846",
   "src/main/java/com/amazon/jenkins/ec2fleet/EC2FleetNodeComputer.java:72-74",
   "fix.diff:747-754",
   "fix.diff:799-807",
   "fix.diff:1579-1582"
  ]
 },
 "landing_point": {
  "where": "src/main/java/com/amazon/jenkins/ec2fleet/EC2FleetCloud.java:1050",
  "why": "EC2FleetCloud.DescriptorImpl.doTestConnection is the obvious 'Test Connection' form endpoint in the main cloud class: it builds an AWS client from the request's credential id, region and endpoint, with no POST or permission check."
 },
 "fix_sites": [
  {
   "where": "src/main/java/com/amazon/jenkins/ec2fleet/EC2FleetCloud.java:1016",
   "entry_point": "HTTP descriptorByName/...EC2FleetCloud/fillFleetItems (gets @RequirePOST, ADMINISTER, region+endpoint validation)",
   "module_kind": "primary implementation, Stapler descriptor web method"
  },
  {
   "where": "src/main/java/com/amazon/jenkins/ec2fleet/EC2FleetCloud.java:1050",
   "entry_point": "HTTP descriptorByName/...EC2FleetCloud/testConnection (gets @RequirePOST, ADMINISTER, region+endpoint validation)",
   "module_kind": "primary implementation, Stapler descriptor web method"
  },
  {
   "where": "src/main/java/com/amazon/jenkins/ec2fleet/EC2FleetCloud.java:978",
   "entry_point": "HTTP .../EC2FleetCloud/fillAwsCredentialsIdItems (gets ADMINISTER only)",
   "module_kind": "primary implementation, Stapler descriptor web method"
  },
  {
   "where": "src/main/java/com/amazon/jenkins/ec2fleet/EC2FleetCloud.java:982",
   "entry_point": "HTTP .../EC2FleetCloud/fillRegionItems (gets ADMINISTER only; calls AWS DescribeRegions with stored credential)",
   "module_kind": "primary implementation, Stapler descriptor web method"
  },
  {
   "where": "src/main/java/com/amazon/jenkins/ec2fleet/EC2FleetCloud.java:986",
   "entry_point": "HTTP .../EC2FleetCloud/checkMaxTotalUses (gets ADMINISTER)",
   "module_kind": "primary implementation, form validation"
  },
  {
   "where": "src/main/java/com/amazon/jenkins/ec2fleet/EC2FleetCloud.java:996",
   "entry_point": "HTTP .../EC2FleetCloud/checkName (gets ADMINISTER; lists cloud names)",
   "module_kind": "primary implementation, form validation"
  },
  {
   "where": "src/main/java/com/amazon/jenkins/ec2fleet/EC2FleetCloud.java:1040",
   "entry_point": "descriptor method isExistingCloudNameDuplicated (gets ADMINISTER)",
   "module_kind": "primary implementation, descriptor helper"
  },
  {
   "where": "src/main/java/com/amazon/jenkins/ec2fleet/EC2FleetCloud.java:1042",
   "entry_point": "HTTP .../EC2FleetCloud/checkFleet (gets ADMINISTER)",
   "module_kind": "primary implementation, form validation"
  },
  {
   "where": "src/main/java/com/amazon/jenkins/ec2fleet/EC2FleetLabelCloud.java:819",
   "entry_point": "HTTP .../EC2FleetLabelCloud/fillEc2KeyPairNameItems (gets @RequirePOST, ADMINISTER, region+endpoint validation)",
   "module_kind": "second implementation (label-based cloud), Stapler descriptor web method"
  },
  {
   "where": "src/main/java/com/amazon/jenkins/ec2fleet/EC2FleetLabelCloud.java:839",
   "entry_point": "HTTP .../EC2FleetLabelCloud/testConnection (gets @RequirePOST, ADMINISTER, region+endpoint validation)",
   "module_kind": "second implementation, Stapler descriptor web method"
  },
  {
   "where": "src/main/java/com/amazon/jenkins/ec2fleet/EC2FleetLabelCloud.java:811",
   "entry_point": "HTTP .../EC2FleetLabelCloud/fillAwsCredentialsIdItems (gets ADMINISTER)",
   "module_kind": "second implementation, Stapler descriptor web method"
  },
  {
   "where": "src/main/java/com/amazon/jenkins/ec2fleet/EC2FleetLabelCloud.java:815",
   "entry_point": "HTTP .../EC2FleetLabelCloud/fillRegionItems (gets ADMINISTER)",
   "module_kind": "second implementation, Stapler descriptor web method"
  },
  {
   "where": "src/main/java/com/amazon/jenkins/ec2fleet/EC2FleetLabelCloud.java:859",
   "entry_point": "HTTP .../EC2FleetLabelCloud/checkName (gets ADMINISTER)",
   "module_kind": "second implementation, form validation"
  },
  {
   "where": "src/main/java/com/amazon/jenkins/ec2fleet/EC2FleetLabelCloud.java:883",
   "entry_point": "descriptor method isExistingCloudNameDuplicated (gets ADMINISTER)",
   "module_kind": "second implementation, descriptor helper"
  },
  {
   "where": "src/main/java/com/amazon/jenkins/ec2fleet/EC2FleetNodeComputer.java:73",
   "entry_point": "HTTP computer/<agent>/doDelete (gets @RequirePOST; DELETE check already present)",
   "module_kind": "agent Computer subclass overriding a core action (looks out of scope from the cloud config forms)"
  },
  {
   "where": "src/main/java/com/amazon/jenkins/ec2fleet/aws/EC2Api.java:181-223",
   "entry_point": "public API EC2Api.connect/getEndpoint, reached by every EC2 client build (form methods, RegionHelper, periodic update)",
   "module_kind": "lower-level AWS client factory (region validation added as defence in depth)"
  }
 ],
 "O1_entry_points": 5,
 "O2_out_of_scope_site": {
  "kind": "second_implementation",
  "where": "src/main/java/com/amazon/jenkins/ec2fleet/EC2FleetLabelCloud.java:819-846 (label cloud descriptor duplicating EC2FleetCloud's methods); also a lower-level API at src/main/java/com/amazon/jenkins/ec2fleet/aws/EC2Api.java:192-219 and an agent action at src/main/java/com/amazon/jenkins/ec2fleet/EC2FleetNodeComputer.java:73"
 },
 "O3_reason_to_dismiss": "EC2FleetLabelCloud is a separate, less-used 'label-based' cloud type, and doDoDelete already calls checkPermission(DELETE) and overrides a core action, so a solver who hardens EC2FleetCloud's Test Connection/fill methods can argue both are other features already covered by Jenkins core.",
 "O4_distance": {
  "files": 4,
  "packages": 2,
  "repo_mb": null
 },
 "O5_coupled_behaviour": {
  "what": "Admins must still be able to test and fill with real AWS endpoints: blank endpoint (region-derived), China *.amazonaws.com.cn, mixed-case or space-padded URLs, scheme-less hosts, and gov/iso region names. Agent deletion must keep working for users with Computer.DELETE who are not admins. An over-broad fix (allow-listing only ec2.<region>.amazonaws.com, rejecting a blank endpoint, or requiring ADMINISTER on doDoDelete) breaks these.",
  "where": "fix.diff:6558-6598; fix.diff:6731-6741; src/main/java/com/amazon/jenkins/ec2fleet/EC2FleetNodeComputer.java:73-74; src/main/java/com/amazon/jenkins/ec2fleet/aws/EC2Api.java:214-219"
 },
 "O6_input_shapes": [
  "endpoint with scheme (https://host)",
  "endpoint without scheme (host only, https:// prepended)",
  "endpoint with surrounding whitespace / mixed case",
  "IDN host normalised via IDN.toASCII",
  "host with trailing dot(s)",
  "lookalike suffix (evilamazonaws.com) rejected; exact amazonaws.com / amazonaws.com.cn and subdomains accepted",
  "blank/null endpoint allowed (falls back to region-derived)",
  "region with whitespace / uppercase normalised",
  "region containing '.', '/', ':' rejected",
  "blank region treated as null",
  "GET vs POST on the five state-using web methods"
 ],
 "O7_producer": {
  "kind": "config_loader",
  "where": "src/main/java/com/amazon/jenkins/ec2fleet/EC2FleetCloud.java:164 (DataBoundConstructor storing region/endpoint unvalidated, reloaded from config.xml) and src/main/java/com/amazon/jenkins/ec2fleet/EC2FleetLabelCloud.java:886 (configure/bindJSON)",
  "check_calls_producer": false
 },
 "O8_uncovered_routes": [
  {
   "route": "AutoScalingGroupFleet.createClient/getEndpoint builds the autoscaling endpoint from an unvalidated region; reached from fillFleetItems, testConnection (AwsPermissionChecker ASG path) and the periodic update with saved config. The fix added region validation only to EC2Api.",
   "where": "src/main/java/com/amazon/jenkins/ec2fleet/fleet/AutoScalingGroupFleet.java:123-156",
   "reason_to_dismiss": "The fixed handlers already validate region before reaching it, and the remaining route is admin-saved config, which core protects with POST and a crumb, so it is not CSRF.",
   "distance": "other package (fleet/) from landing point EC2FleetCloud.java; reached via src/main/java/com/amazon/jenkins/ec2fleet/aws/AwsPermissionChecker.java:88",
   "present_in_latest": "yes",
   "latest_where": "latest/src/main/java/com/amazon/jenkins/ec2fleet/fleet/AutoScalingGroupFleet.java:239"
  },
  {
   "route": "CloudFormationApi.connect/getEndpoint builds the cloudformation endpoint from an unvalidated region; reached from EC2FleetLabelCloud.updateStacks using saved config.",
   "where": "src/main/java/com/amazon/jenkins/ec2fleet/aws/CloudFormationApi.java:41-56",
   "reason_to_dismiss": "No HTTP form method reaches it. It runs only from the label cloud's background stack updater on admin-saved config.",
   "distance": "aws/ package, reached via src/main/java/com/amazon/jenkins/ec2fleet/EC2FleetLabelCloud.java:698",
   "present_in_latest": "yes",
   "latest_where": "latest/src/main/java/com/amazon/jenkins/ec2fleet/aws/CloudFormationApi.java:55"
  }
 ],
 "O8b_injection_room": [
  {
   "where": "src/main/java/com/amazon/jenkins/ec2fleet/EC2FleetCloud.java:1140-1190",
   "sibling": "A doFillXxx / doCheckXxx on NodeHardwareScaler.DescriptorImpl that takes awsCredentialsId/region/endpoint and calls describeInstanceTypes to preview executor counts",
   "why_realistic": "NodeHardwareScaler already calls describeInstanceTypes, and a 'preview' dropdown is a natural UI addition on a nested descriptor that a maintainer hardening only the cloud descriptors would miss."
  },
  {
   "where": "src/main/java/com/amazon/jenkins/ec2fleet/EC2FleetStatsApi.java:33",
   "sibling": "A doRefresh action on the ec2-fleet RootAction that triggers cloud.update() (AWS calls with stored credentials) without POST/permission",
   "why_realistic": "The RootAction already exposes doStats with no permission check, and a 'refresh stats' endpoint is an obvious companion."
  },
  {
   "where": "src/main/java/com/amazon/jenkins/ec2fleet/EC2FleetLabelCloud.java:819",
   "sibling": "A doFillFleetItems-style lister on the label cloud descriptor (e.g. existing stacks) calling CloudFormationApi.connect with request region/endpoint",
   "why_realistic": "The label cloud already mirrors EC2FleetCloud's form methods and uses CloudFormationApi, whose getEndpoint lacks region validation."
  }
 ],
 "O9_family": "CSRF / missing permission check on Stapler form and web methods (CWE-352 with CWE-862), bundled with endpoint/region input validation (SSRF-style credential exfiltration)",
 "O9_dos": false,
 "O10_build": {
  "language": "Java",
  "toolchain": "Maven, Jenkins plugin parent POM 6.2138.v03274d462c13 (pom.xml:5-8), JUnit 5 + JenkinsRule + Mockito",
  "services": [],
  "offline_after_build": true,
  "project_tests": "src/test/java/com/amazon/jenkins/ec2fleet/EC2FleetCloudTest.java (descriptor doTestConnection/doFillFleetItems with mocked AWS), src/test/java/com/amazon/jenkins/ec2fleet/aws/EC2ApiTest.java, src/test/java/com/amazon/jenkins/ec2fleet/EC2FleetStatsApiTest.java; the fix adds EC2FleetLabelCloudTest and AwsRegionValidatorTest"
 },
 "O11_fix_minutes": 60,
 "O12_red_flags": [],
 "O13_recall_risk": "medium",
 "pattern_fit": "A",
 "j": {
  "j_multi_site": 1,
  "j_sites_touched": "src/main/java/com/amazon/jenkins/ec2fleet/EC2FleetCloud.java, src/main/java/com/amazon/jenkins/ec2fleet/EC2FleetLabelCloud.java, src/main/java/com/amazon/jenkins/ec2fleet/EC2FleetNodeComputer.java, src/main/java/com/amazon/jenkins/ec2fleet/aws/EC2Api.java, new src/main/java/com/amazon/jenkins/ec2fleet/AwsEndpointValidator.java, new src/main/java/com/amazon/jenkins/ec2fleet/aws/AwsRegionValidator.java (+2 config.jelly)",
  "j_sibling_sites": "yes",
  "j_cause_other_layer": 1,
  "j_defence_ineffective": 0,
  "j_overbroad_breaks_legit": 1,
  "j_tempting_wrong_fix": "Add @RequirePOST + checkPermission(ADMINISTER) to EC2FleetCloud.doTestConnection and doFillFleetItems only, leaving the label cloud descriptor, doDoDelete, and region/endpoint validation untouched."
 },
 "out_of_scope_notes": [
  "EC2FleetStatsApi.doStats (src/main/java/com/amazon/jenkins/ec2fleet/EC2FleetStatsApi.java:33) has no permission check at the pinned commit or in latest. The fix only changes its test to expect 403 for anonymous users, which core's Overall/Read enforces."
 ],
 "unverified": [
  "pinned_commit SHA not provided (parent_commit null); the repo directory is assumed to be the fix's parent.",
  "Repo size not measured (no shell); tiny_repo not asserted. About 33 main Java files suggests a small plugin, and the source alone is likely under 5 MB.",
  "The advisory text itself was not available. The summary says CSRF, but the fix also bundles endpoint/region validation (likely a sibling SSRF/permission advisory). The exact list of affected methods in the advisory text is unknown.",
  "Did not confirm that Jenkins core's fill/validate JS issues POST, so that @RequirePOST on fillFleetItems/fillEc2KeyPairNameItems keeps the UI working.",
  "Pattern B is weak: the O8 routes miss only the lower-level region validation and are shielded by handler-level checks on the CSRF entry points."
 ]
}
  ```
- Published fix sites:   - src/main/java/com/amazon/jenkins/ec2fleet/EC2FleetCloud.java:1016 — entry point: HTTP descriptorByName/...EC2FleetCloud/fillFleetItems (gets @RequirePOST, ADMINISTER, region+endpoint validation) [primary implementation, Stapler descriptor web method]
  - src/main/java/com/amazon/jenkins/ec2fleet/EC2FleetCloud.java:1050 — entry point: HTTP descriptorByName/...EC2FleetCloud/testConnection (gets @RequirePOST, ADMINISTER, region+endpoint validation) [primary implementation, Stapler descriptor web method]
  - src/main/java/com/amazon/jenkins/ec2fleet/EC2FleetCloud.java:978 — entry point: HTTP .../EC2FleetCloud/fillAwsCredentialsIdItems (gets ADMINISTER only) [primary implementation, Stapler descriptor web method]
  - src/main/java/com/amazon/jenkins/ec2fleet/EC2FleetCloud.java:982 — entry point: HTTP .../EC2FleetCloud/fillRegionItems (gets ADMINISTER only; calls AWS DescribeRegions with stored credential) [primary implementation, Stapler descriptor web method]
  - src/main/java/com/amazon/jenkins/ec2fleet/EC2FleetCloud.java:986 — entry point: HTTP .../EC2FleetCloud/checkMaxTotalUses (gets ADMINISTER) [primary implementation, form validation]
  - src/main/java/com/amazon/jenkins/ec2fleet/EC2FleetCloud.java:996 — entry point: HTTP .../EC2FleetCloud/checkName (gets ADMINISTER; lists cloud names) [primary implementation, form validation]
  - src/main/java/com/amazon/jenkins/ec2fleet/EC2FleetCloud.java:1040 — entry point: descriptor method isExistingCloudNameDuplicated (gets ADMINISTER) [primary implementation, descriptor helper]
  - src/main/java/com/amazon/jenkins/ec2fleet/EC2FleetCloud.java:1042 — entry point: HTTP .../EC2FleetCloud/checkFleet (gets ADMINISTER) [primary implementation, form validation]
  - src/main/java/com/amazon/jenkins/ec2fleet/EC2FleetLabelCloud.java:819 — entry point: HTTP .../EC2FleetLabelCloud/fillEc2KeyPairNameItems (gets @RequirePOST, ADMINISTER, region+endpoint validation) [second implementation (label-based cloud), Stapler descriptor web method]
  - src/main/java/com/amazon/jenkins/ec2fleet/EC2FleetLabelCloud.java:839 — entry point: HTTP .../EC2FleetLabelCloud/testConnection (gets @RequirePOST, ADMINISTER, region+endpoint validation) [second implementation, Stapler descriptor web method]
  - src/main/java/com/amazon/jenkins/ec2fleet/EC2FleetLabelCloud.java:811 — entry point: HTTP .../EC2FleetLabelCloud/fillAwsCredentialsIdItems (gets ADMINISTER) [second implementation, Stapler descriptor web method]
  - src/main/java/com/amazon/jenkins/ec2fleet/EC2FleetLabelCloud.java:815 — entry point: HTTP .../EC2FleetLabelCloud/fillRegionItems (gets ADMINISTER) [second implementation, Stapler descriptor web method]
  - src/main/java/com/amazon/jenkins/ec2fleet/EC2FleetLabelCloud.java:859 — entry point: HTTP .../EC2FleetLabelCloud/checkName (gets ADMINISTER) [second implementation, form validation]
  - src/main/java/com/amazon/jenkins/ec2fleet/EC2FleetLabelCloud.java:883 — entry point: descriptor method isExistingCloudNameDuplicated (gets ADMINISTER) [second implementation, descriptor helper]
  - src/main/java/com/amazon/jenkins/ec2fleet/EC2FleetNodeComputer.java:73 — entry point: HTTP computer/<agent>/doDelete (gets @RequirePOST; DELETE check already present) [agent Computer subclass overriding a core action (looks out of scope from the cloud config forms)]
  - src/main/java/com/amazon/jenkins/ec2fleet/aws/EC2Api.java:181-223 — entry point: public API EC2Api.connect/getEndpoint, reached by every EC2 client build (form methods, RegionHelper, periodic update) [lower-level AWS client factory (region validation added as defence in depth)]
- Uncovered routes to confirm (pattern B):   - src/main/java/com/amazon/jenkins/ec2fleet/fleet/AutoScalingGroupFleet.java:123-156 — AutoScalingGroupFleet.createClient/getEndpoint builds the autoscaling endpoint from an unvalidated region; reached from fillFleetItems, testConnection (AwsPermissionChecker ASG path) and the periodic update with saved config. The fix added region validation only to EC2Api. (reason to dismiss: The fixed handlers already validate region before reaching it, and the remaining route is admin-saved config, which core protects with POST and a crumb, so it is not CSRF.; still in latest: yes)
  - src/main/java/com/amazon/jenkins/ec2fleet/aws/CloudFormationApi.java:41-56 — CloudFormationApi.connect/getEndpoint builds the cloudformation endpoint from an unvalidated region; reached from EC2FleetLabelCloud.updateStacks using saved config. (reason to dismiss: No HTTP form method reaches it. It runs only from the label cloud's background stack updater on admin-saved config.; still in latest: yes)
- Design plan from the lead: TRACK = INJECTED (breaker recipe: only injected-sibling tasks at a recurring trust decision have beaten both models).

RECURRING DECISION / PROTECTED SINK: Whether a request may make Jenkins call AWS with a stored credential against a caller-chosen region/endpoint, or schedule an agent's EC2 instance for termination, is decided in the cloud descriptors' Stapler web methods (needs POST + Jenkins.ADMINISTER) and in

STEP 1 - confirm the published fix's sites and these uncovered-route leads with tests on the pinned copy: src/main/java/com/amazon/jenkins/ec2fleet/fleet/AutoScalingGroupFleet.java:123-156 (AutoScalingGroupFleet.createClient/getEndpoint builds t; dismiss: The fixed handlers already validate region be); src/main/java/com/amazon/jenkins/ec2fleet/aws/CloudFormationApi.java:41-56 (CloudFormationApi.connect/getEndpoint builds the cloudf; dismiss: No HTTP form method reaches it. It runs only ).
STEP 2 - INJECT 2 to 4 sibling vulnerabilities of the SAME mechanism into our pinned copy at these recurring sites (verify each by reading the code): src/main/java/com/amazon/jenkins/ec2fleet/EC2FleetCloud.java:1140-1190 -> A doFillXxx / doCheckXxx on NodeHardwareScaler.DescriptorImpl that tak (realistic: NodeHardwareScaler already calls describeInstanceTypes, and ); src/main/java/com/amazon/jenkins/ec2fleet/EC2FleetStatsApi.java:33 -> A doRefresh action on the ec2-fleet RootAction that triggers cloud.upd (realistic: The RootAction already exposes doStats with no permission ch); src/main/java/com/amazon/jenkins/ec2fleet/EC2FleetLabelCloud.java:819 -> A doFillFleetItems-style lister on the label cloud descriptor (e.g. ex (realistic: The label cloud already mirrors EC2FleetCloud's form methods). Each sibling MUST be code a maintainer could plausibly have written (no tell-tale names/comments/shortcuts; match surrounding style), reachable through the real public entry point, covered by a stated invariant, placed where the published upstream fix never touches, and carry a DIFFERENT plausible reason-to-dismiss from the others (legacy/compat path, internal/trusted caller, unsupported combination, neighbouring feature). Distinct reasons-to-dismiss are the lever.
STEP 3 - hidden security tests require closing the base flaw, every uncovered route AND every injected sibling through the real entry point. The oracle closes all; a fix that closes only the obvious sites must score < 1.0 (add a security_fail check patch for exactly that partial fix).
STEP 4 - COUPLED MUST-KEEP-WORKING (one functional test per trap): Admins must still be able to test and fill with real AWS endpoints: blank endpoint (region-derived), China *.amazonaws.com.cn, mixed-case or space-padded URLs, scheme-less hosts, and gov/iso region na (near fix.diff:6558-6598; fix.diff:6731-6741; src/main/j); keep every legitimate use of the mechanism working.

Aim for >=3 levers with DIFFERENT reasons to dismiss. Every sibling must be findable by a blind engineer from instruction.md + code; if not, drop it. instruction.md stays product-level: system, one impact with one user trigger, invariants covering EVERY route/sibling (a natural list, no count); never name files/functions/fields/CVEs (all in manifest.leak_terms). Register each sibling and route in build/audit/uncovered-routes.tsv.
- Host notes: Language: Java. Offline after build, no external services. INJECTED: siblings go in OUR copy only, register them. Recurring trust decision (5 entry points) + screener injection room. Build+test via real entry points; project's own area tests pass at the pinned commit. Pin at the vulnerable commit; keep unrelated earlier fixes.

## Design: where difficulty comes from
Models find the code the report leads to and diagnose it correctly. They fail on scope. Build these
in, in order of evidence:
1. **Pattern A: the published fix's far sites.**
   - The report leads to one site. The tests cover every entry point the published fix protects,
     including one in a module that looks out of scope: a second implementation, a lower-level
     public API, a wrapper, a save/reload path, or a defaults or merge route.
   - Give it a plausible **reason to dismiss**, and **distance**: another file or package from the
     landing point.
2. **Pattern B: uncovered routes.**
   - Routes into the same protected sink where the advisory's own protection is missing at the
     pinned commit, and which the published fix did not touch.
   - They are unmodified upstream code, so a solver can argue they were never covered.
   - The strongest lever found so far: DeepSeek 6 of 6 on one; both models 0 of 3 on three combined.
3. **Input-shape variants** that the general rule covers but a one-case fix misses (a plain string
   and an array).
4. **A coupled must-keep-working behaviour** next to the sink, tested functionally, so an
   over-broad fix fails. MiMo tends to over-harden.
5. **Producer off the check's path.** The check depends on data produced elsewhere (a schema,
   serializer, cache, mapper or config loader) and does not call it. It counts only if the producer
   is infrastructure, not a request handler.
6. **Injected siblings**, only where the plan asks for them. Each must be:
   - code a maintainer could have written, with no deceptive names or comments;
   - reachable through the real entry point;
   - covered by a stated invariant;
   - placed where the upstream fix never touches.

Aim for at least two levers with **different** reasons to dismiss.

Never add:
- encoding, verb, protocol or role/direction variants;
- more routes of one concept;
- resource-exhaustion traps.

Every lever must be findable by a blind engineer from the report and the code. A lever that a blind
fix cannot find is unfair: remove it.

**Pattern B rules:**
- Confirm each route with a behavioural test on the pinned copy before relying on it. The
  screener's claim is only a lead.
- Append one row per route to `/home/mara/cwe-bench/build/audit/uncovered-routes.tsv`, using its existing
  header. Columns:
  - `task`, `repo`, `advisory`;
  - `trap_ref` (the manifest trap id only; no mechanism text, since the manifest holds the detail);
  - `real_upstream`;
  - `present_in_latest` (`yes`, `no` or `unknown`, from a read-only look at current upstream code if
    you can reach it);
  - `public_upstream_report`, `in_current_scope`, `built`, `note`;
  - `disclosure_status` (`pending client decision`).

## Environment (`tasks/jenkins-ec2fleet-authz-inj/environment/Dockerfile`)
- **Base and code.** A small official base image. The repo goes into `/app` at the pinned commit,
  and `/app/.git` is then deleted.
- **Offline.** Install every dependency, tool and service the project and tests need; nothing may
  be downloaded at test time. Services start from `test.sh`.
- **Packages:** `patch`, `curl`, `ca-certificates`, `bash`, `git`.
- **Agent layer.** Append `harness/claude-code.Dockerfile.snippet` unchanged at the end.
- **No test code in the image.** The agent shares the container. Pre-build against stubs; `test.sh`
  copies the real tests in at grading time.
- **Project tests.** The project's own tests for the affected area must pass in the image at the
  pinned commit.
- **No leaked regression tests.** The pinned commit must not already contain the advisory's
  regression tests (check `git log` between the pinned and fix commits).

## Report to the solver (`tasks/jenkins-ec2fleet-authz-inj/instruction.md`)
**Write:**
- what the system is, at product level;
- one observed impact, with ONE concrete trigger at user level (HTTP request, CLI call or public API
  use);
- the security properties as **invariants**: who may do what to which data, or what attacker input
  must never achieve. Word each so it covers every tested route and shape ("no value of X may …").
  If there are several, give one natural list, never a count;
- every **contract** the tests need:
  - the refusal form ("a client error with no side effect");
  - any interface or field name a test uses;
  - preservation clauses ("works exactly as today");
  - a legitimate magnitude next to any attack magnitude;
- that examples are examples, not the full set;
- the standard constraints block: fix the problem and its close variants; keep legitimate use
  working; do not modify or add tests; do not look up the upstream fix; do not special-case the
  example.

**Never write:**
- file, package, function, class, field or parameter names a user would not see;
- line numbers, the root cause, the fix approach, or a CVE or GHSA id;
- a list of routes, spellings or roles;
- restricting adverbs ("directly", "only via");
- anything that names or paraphrases a far site, an uncovered route or an injected sibling.

Put every identifier that must not appear in `manifest.leak_terms`.

## Tests (`tasks/jenkins-ec2fleet-authz-inj/tests/`)
- **`security/`:** one test per site, route, input shape and form. Each one:
  - goes through the real entry point;
  - fails on the pinned code and passes on a correct fix;
  - asserts the attack is blocked: any client error plus no side effect, never one exact status.
- **`functional/`:**
  - legitimate use, including the coupled behaviour of every lever;
  - where they exist, the project's own tests for the area.
- **No product code in a test's bookkeeping.** Compute expected values and clean-ups in the test
  itself, because a hardened helper must not crash a test.
- **Stubs** of permission or authority answer per resource and verb, like the real thing.
- **Scope.** A test may vary only what the instruction names, and drive only the entry point it
  names.
- **No network**, and nothing that depends on the fix commit being present.
- **Templates.** JUnit XML into the two directories the template names. Copy `score.py` unchanged.
  Edit only the marked command lines of `test.sh`, and keep its agent-kill block.

## Proof
- **The oracle.** `solution/fix.patch` is the published fix reduced to source changes, plus fixes
  for every uncovered route and injected sibling in the task. `solution/solve.sh` applies it to
  `/app`.
- **Wrong-fix patches** go in `build/jenkins-ec2fleet-authz-inj/checks/`, listed in `manifest.patch_checks`:
  - one `security_fail` per lever (the fix that misses only that lever);
  - a `functional_fail` (an over-broad or feature-removing fix);
  - a `pass` of kind `hardening` (the oracle plus defensive hardening of the product code the
    security tests import);
  - a `pass` alternative fix where a second valid design is plausible.
- **`manifest.wrong_fix_catalogue`:** for each class, a `checks/` patch, or `n/a: <why>`:
  `refuse_all`, `crash_as_refusal`, `wrong_resource`, `one_role_or_direction`, `reads_only`,
  `check_after_adjustment`, `unlisted_route`, `malformed_identity`, `missing_authority`,
  `adjacent_api`.

## Deliverables
**`tasks/jenkins-ec2fleet-authz-inj/`:**
- `instruction.md`;
- `task.toml`, from `builder/templates/`, with `[metadata]` filled in and the network allowlist
  kept;
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/jenkins-ec2fleet-authz-inj/manifest.json`:**
- `slug`, `candidate`;
- `pattern`: `A+B`;
- `builder_prompt_version`: `build-v1`;
- `"strict_gate": true`;
- `verified`: entry point, sites, routes, services, project tests run;
- `leak_terms`, `patch_checks`, `wrong_fix_catalogue`;
- `traps`: one entry per lever, with `shape`, `where` (file:line), `security_tests`,
  `coupled_functional_tests`, `security_fail_patch`, and `realistic_because` (for pattern B: "real,
  unmodified upstream code");
- `status`.

**Also in `build/jenkins-ec2fleet-authz-inj/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `builder/templates/` and `harness/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I builder/gate.py jenkins-ec2fleet-authz-inj --only static
python3 -I builder/gate.py jenkins-ec2fleet-authz-inj --only nop
python3 -I builder/gate.py jenkins-ec2fleet-authz-inj --only oracle
python3 -I builder/gate.py jenkins-ec2fleet-authz-inj --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/jenkins-ec2fleet-authz-inj/`;
  - edit only `tasks/jenkins-ec2fleet-authz-inj/`, `build/jenkins-ec2fleet-authz-inj/` and, for pattern B, the register;
  - do not commit.

## Stop and report instead of shipping when
- the flaw does not reproduce through a real entry point at the pinned commit;
- a planned route or site is not reachable, or the check calls the producer directly (substitute
  another lever the code supports if you can, and say so);
- the task needs network at run time, or a GPU, kernel or GUI;
- the tests are flaky;
- no design meets the bar.

## Report back (under 400 words)
- The gate result for each stage.
- Each lever in one line: pattern, shape, file:line, reason to dismiss.
- Pattern B: each register row.
- The instruction's word count.
- Every guess you could not verify.
- Any fairness concern you see yourself.
- Anything noticed outside the scope, in one line.
- If abandoned, exactly why.
