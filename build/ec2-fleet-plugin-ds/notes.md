# ec2-fleet-plugin-ds — build notes

- Start (pipeline): 2026-10-18T22:12Z
- End: (filled at the end)

Advisory GHSA-2X9C-VP3G-HVV2 / CVE-2026-57295, jenkinsci/ec2-fleet-plugin.
Pinned (vulnerable) `8fedff2a81c3f91c14e7a1f5ea5191063f3d43b3` = parent of the published fix
`a6eedb7bc112de92bbba179c03840d845b845c82` (verified locally: `git rev-parse a6eedb7^` = 8fedff2).
Track: injected. Pattern: A. Language: Java (Maven, Jenkins plugin parent POM 6.2138, Jenkins
2.492.3, JUnit 5 + JenkinsRule + HtmlUnit + Mockito). Fully offline after the image build.

## Prior art / why this is a rebuild
An earlier build of the same advisory (`jenkins-ec2fleet-authz-inj`) passed the gate but was
**rejected in trials: DeepSeek 3/3 and MiMo 3/3 solved it**. Its design is reused as the base; the
advisory's own agent-retirement behaviour (O5) was investigated as an extra lever and kept only as
a coupled preservation test (see below).

## Mechanism (one line)
The plugin exposes Stapler form/web methods that use a stored AWS credential against a
caller-chosen region/endpoint; at the pinned commit they check neither permission nor HTTP
method, and the region/endpoint are not validated before they are turned into a service host.

## Levers (one line each)
1. **A base (obvious)** — main cloud descriptor's form/validate/test web methods (region and fleet
   listing, connection test): missing ADMINISTER; fleet listing and connection test also missing
   @RequirePOST, region/endpoint validation. `EC2FleetCloud.java:978-1072`.
   Dismiss: none — this is where the report lands.
2. **A far** — the label-based cloud descriptor duplicates the same helpers (region listing,
   key-pair listing, connection test). `EC2FleetLabelCloud.java:811-886`.
   Dismiss: a separate, less-used cloud type in another class; "a different feature".
3. **A far** — the lower-level AWS client factory derives an endpoint from an unvalidated region;
   reached by every client build. `aws/EC2Api.java:181-223`.
   Dismiss: indirect helper; handlers look as if they validate first.
4. **A endpoint lookalike** — endpoint allow-check by raw string suffix accepts
   `evilamazonaws.com`, `amazonaws.com.evil.example`, userinfo and AWS-looking paths; must be
   checked by parsed host. Dismiss: "ends with amazonaws.com" reads as a complete allow-list.
5. **injected S1** — node-hardware scaler instance-type preview (nested descriptor `doFill`
   helper) builds an AWS client from request credential/region/endpoint and calls
   describeInstanceTypes. Dismiss: an optional preview on a nested scaler descriptor, easy to miss
   while hardening the top-level cloud forms.
6. **injected S2** — plugin root-action "refresh" forcing `cloud.update()` with stored credentials.
   Dismiss: sits next to the existing read-only stats endpoint and reads as a harmless companion.

## Investigated and dismissed: agent retirement (O5)
`EC2FleetNodeComputer.doDoDelete` already checks the per-agent DELETE right at the pinned commit;
the published fix adds @RequirePOST. **Behavioural test on the pinned copy: a safe GET returns 405
and the agent remains** (the platform already enforces POST on the inherited core action), so this
is not an independently exploitable lever and no security test is scored on it. It is kept in the
oracle (matches upstream) and as the coupled functional preservation rule: a non-admin holding
DELETE for the agent must still be able to retire it through a POST — an ADMINISTER-only guard
fails. Register row updated to `no (dismissed)`.

## Sites, routes, input shapes scored
- Sites: both cloud descriptors; the lower-level client factory; the two injected siblings.
- Routes: real HTTP through JenkinsRule WebClient (GET/POST) on
  `descriptorByName/<cloud>/<method>`, the nested scaler descriptor, and the root action; host
  steering observed through Jenkins' HTTP proxy pointed at a local recording proxy (CONNECT line
  shows the host actually contacted).
- Shapes: blank/region-derived endpoint; China `*.amazonaws.com.cn`; mixed case and surrounding
  whitespace; scheme-less host; gov/iso region names; trailing-dot host; lookalike suffixes and
  userinfo/path tricks; regions with `.` `/` `:` `?` `#` `@`; blank region as null; GET vs POST;
  non-admin POST vs admin GET.

## Coupled must-keep-working behaviour
Admins keep every real provider input listed above (functional); a non-admin with the delete right
for an agent keeps being able to retire that agent (functional). An over-broad fix (blank endpoint
rejected, only `ec2.<region>.amazonaws.com` allowed, ADMINISTER required for retirement) fails the
functional group.

## Producer off the check's path
Not used: the stored-config producer is admin-saved, POST+crumb-protected and was dismissed by
the screener (O8) as not a CSRF route; the check must sit at the request sink, not at the loader.

## What I verified
- Pinned commit: `a6eedb7^ == 8fedff2`; the published regression tests (`EC2FleetLabelCloudTest`,
  `AwsRegionValidatorTest`, ...) appear only in the fix commit, not at the pinned commit.
- `environment/inject-siblings.patch` and `solution/fix.patch` apply cleanly to the pinned tree;
  every `checks/*.patch` applies cleanly to the pinned+injected tree (dry-run).
- Local dev-image runs (before trimming the non-reproducing lever): on the vulnerable base every
  security class reached failed (e.g. EndpointLookalike 3/3, LabelCloudHelpers 4/4) and every
  functional class passed; on the oracle the same security classes passed. The retirement probe
  showed a GET returning 405 at the pinned commit with the agent intact.
- Gate `nop` (pinned+injected): 0/25 security pass, 14/14 functional pass, reward 0.0 — PASSED.

## What I could not verify / caveats
- No trial of either target model was run (out of scope). The predecessor design of this same
  advisory was solved 3/3 by both models; the six levers here are the same except that the
  agent-retirement lever was dropped after it failed to reproduce.
- Agent retirement: the security facet does not reproduce (see above); only the coupled
  preservation rule is tested.
- The higher-level `AutoScalingGroupFleet.getEndpoint` / `aws/CloudFormationApi.getEndpoint`
  routes were dismissed by the earlier build after behavioural checks (handlers validate first /
  reached only from admin-saved config); no pattern-B route is built.

## Gate run log
- static: only the downstream `blind` patch and `FAIRNESS.md` are missing (as expected; not written here).
- nop: PASSED — 0/25 security pass, 14/14 functional pass, reward 0.0.
- oracle/patches: the first attempts failed on the known Harbor allowlist/egress-probe infrastructure
  flake under load (`network_mode='allowlist' is not supported ...` / docker-compose start failure);
  retried under the run rules (never weakening task.toml). Final results: see below.
- oracle: PASSED — 3/3 trials identical, 25/25 security + 14/14 functional, reward 1.0.
- patches: run per check (the stage-level attempt restarts the whole stage on a flake; the
  per-check runner retries only the flaked check). Check results are copied to build/ec2-fleet-plugin-ds/reports/.

## Upgrade 2026-10-20 (BETTER-PATTERNS §2–§8)
- instruction.md rewritten: the security property is stated once over the protected outcome
  (stored credential use requires administration + a genuine state-changing submission; no
  caller value may steer it outside the provider's domains). Removed the route/sibling
  descriptions (helper endpoints, credential+region GET, region/endpoint provenance, input-shape
  lists tied to specific operations) and generalised the coupled retirement contract.
- No repo change, so the image is reused unchanged.
- Coverage gap closed: the published fix added ADMINISTER but no POST requirement to each
  cloud's region listing. The main cloud's admin-GET facet was already tested; the label cloud's
  was not. Added `security/SecurityLabelCloudRegionPostTest.java::adminGetToLabelCloudRegionListingIsRefused`
  and `checks/sec_label_region_safe_method.patch` (oracle minus the label region `@RequirePOST`),
  wired as `security_fail`. The oracle already closes it (`@RequirePOST` is in fix.patch), so
  `solution/fix.patch` is unchanged.
- Levers unchanged (how-type: endpoint lookalike M8, region-to-host shape M8, coupled retirement
  value M11; plus where-type siblings). Hidden suite is now 26 security + 14 functional.
- Static leak scan: no leaked term in instruction.md. Only the pre-existing missing
  downstream `blind` patch and `FAIRNESS.md` are reported.
