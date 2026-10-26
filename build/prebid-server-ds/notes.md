# prebid-server-ds — build notes

start_utc: 2026-10-24T05:05:24Z
end_utc: 2026-10-24T06:31:13Z

## Candidate

prebid/prebid-server @ f0a03396bd5189af815ed4f5b26f08076f64f475 (parent of the published fix
494ac271cd4b5024df9123ef25ca3cff96390be3, "Validate host & subdomain bidder params").
Family: SSRF / URL-authority injection through bidder parameters interpolated into outbound
endpoint templates (CWE-918). Pattern A, injected track.

## Security property (one sentence, general)

Whatever values a bid request carries for a bidder, the server must never build an outbound bidder
request whose destination differs from the host the bidder's own endpoint configuration names; such
a request is refused with a client error before any outbound request exists. The guarantee belongs
to the request-construction path itself, for every bidder and every caller.

## Levers (one line each)

- T0 (published fix, reported mechanism): the host-named builders the fix protects (acuityads,
  bidmachine, smartyads, trafficgate, zeroclickfraud), with the path/query/fragment/userinfo shapes
  that actually move the authority and the coupled legitimate values (ports, mixed case, loopback).
- T1 (second implementation, how): rediads never resolves the endpoint templates; it splits the
  configured host and rewrites label 0 with the request's `endpoint`, so a template-level fix
  misses it.
- T2 (far sites, how): adhese `account`, kayzen `zone` and tradplus optional `zoneId` feed the
  authority under names that are not host-like; tradplus must stay empty-safe.
- T3 (producer off the check's path, how): between and clydo are real, unmodified upstream builders
  that interpolate a request value into the authority with presence checks only; their sole guard
  is a parameter-schema enum the builder never calls.
- T4 (injected sibling): silvermob's allowlist gained a "fully-qualified shard" suffix branch that
  a value with a path separator passes.
- T5 (injected sibling): rtbstack accepts a region from the route query when hostname extraction
  fails, with no check on that branch.
- Coupled must-keep-working (T0/T2): values the server normalises before use (scheme, own domain),
  optional empty values, explicit ports, mixed case, single-label and numeric names.

## Sites (file:line at pinned)

Published fix sites tested: adapters/acuityads/acuityads.go:109, adapters/adhese/adhese.go:70,
adapters/bidmachine/bidmachine.go:186, adapters/kayzen/kayzen.go:94,
adapters/rediads/rediads.go:101-107, adapters/relevantdigital/relevantdigital.go:181-187,
adapters/smartyads/smartyads.go:127, adapters/tradplus/tradplus.go:88,
adapters/trafficgate/trafficgate.go:153, adapters/zeroclickfraud/zeroclickfraud.go:152.
tappx is defence-in-depth only at pinned (the endpoint regex already restricts it; the Host
parameter is deprecated and unused) and gets a functional test but no security test.
Real Pattern B sites: adapters/between/between.go:101, adapters/clydo/clydo.go:146-155.
Injected: adapters/silvermob/silvermob.go:22-23, adapters/rtbstack/rtbstack.go:181-209.

## Verified locally (before the gate)

- Every attack was reproduced behaviourally on the pinned+injected tree through the adapter's
  Builder + MakeRequests: all 14 security tests fail there, all functional tests pass there.
- The oracle (published source fix reduced to source + checks for the two real schema-only
  builders + the two injected siblings) makes every security and functional test pass, and the
  project's own behavioural tests for the 16 affected packages pass too.
- The two schema acceptance tests (TestValidParams/TestInvalidParams) are skipped in the verifier:
  the pinned rediads list treats a full-URL endpoint as valid, which this task deliberately
  changes. Everything else in those packages runs.
- Check patches were each applied to a fresh pinned+injected tree and run against both hidden
  suites and the project tests: the six per-trap and the partial-delimiter misses fail only
  security; overbroad, before-normalization and macro-global fail functional; the alternative
  (central endpoint-parameter check at the macro layer + a rediads check, with tappx building its
  path outside the authority) and the hardening fix score 1.0.
- Pattern B register rows appended for between and clydo (T3); the current upstream tree still has
  no builder check in either, so `present_in_latest=yes`.

## Gate (2026-10-24)

- static: PASSED (only the declared-but-not-yet-written blind pass patch is absent).
- nop: PASSED — 43 security testcases, every one failing on the pinned+injected tree; 386
  functional testcases, all passing.
- oracle: PASSED — 3/3 runs at reward 1.0 with identical security/functional results.
- patches: PASSED — 12/12 declared outcomes: miss_published_hosts (21 security failures, 0
  functional), miss_rediads (3/0), miss_nonhost_fields (9/0), miss_schema_only (6/0),
  miss_silvermob (2/0), miss_rtbstack (2/0), partial_delimiter (23/0), overbroad (9 functional
  failures), before_normalization (3), macro_global (49), alt_correct_fix 1.0, hardening 1.0.
  The blind pass patch is declared and written later by run_blindfix.

The patch stage first ran against the shared `/var/run/docker.sock`; that daemon wedged under the
shared VM load (`docker version` and `docker ps` timing out) mid-stage. Per the documented
workaround a task-private dockerd was started (pool 10.238.0.0/16, bridge 10.237.0.1/16) and the
stage was re-run against it unchanged; no task file was weakened.

## What I could not verify

- Whether a later upstream release changes between/clydo; only current master was read.
