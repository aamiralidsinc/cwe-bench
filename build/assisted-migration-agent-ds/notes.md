# Build notes: assisted-migration-agent-ds

- Start (UTC): 2026-10-24T04:43:32Z
- End (UTC): see end_utc.txt

## Advisory / commits
GHSA-8G5P-JXP9-457C / CVE-2026-53475 / GO-2026-6232 - kubev2v/assisted-migration-agent,
CWE-295 (hardcoded TLS skip-verify on outbound vCenter connections). Pinned
`e350e7b68e6d3f320cf3ef1d0030e280999533f0`, verified direct parent of the published fix
`b940fec9f5032a0801e994054d30e81d64b2942a`. Pattern A, injected track.

## Mechanism (one line)
Every outbound vCenter TLS session is opened with verification hardcoded off, and the API has
no way to supply an authority bundle or to ask for validation; the task makes the requested
validation reach every connection the agent builds.

## Levers
- T1 (reported site, A): `pkg/vmware/client.go:27` NewVsphereClient passes `true`; POST /inspector
  (nested details) and POST /forecaster's second connection. Dismiss: none - it is the report.
- T2 (second implementation, A): `internal/services/forecaster.go:194` builds its own
  `soap.NewClient(u, true)` for the forecaster preflight; PUT /forecaster/credentials and
  POST /forecaster. Dismiss: a duplicate preflight inside the service, not the shared helper.
- T3 (route where protection never existed + documented risk acceptance, how-type):
  `internal/services/rightsizing.go:258` + `pkg/rightsizing/vsphere.go:74`; POST /rightsizing
  (asynchronous). Dismiss: the comment frames skip-verify as a reasoned risk acceptance, and it
  is a separate package with its own connection code.
- T4 (validation preflight, A): `pkg/vmware/auth.go:78`; POST /inspector/credentials and the
  collector pipeline's credential check. Dismiss: a login/logout check looks like credential
  validation rather than an operational connection.
- T5 (shape trap, how-type): the tri-state `skipTls` in the API mapper (`api/v1/extension.go`
  over `internal/models/vcenter.go`). `skipTls:false` with no bundle must validate against the
  system trust store; a mapper that collapses absent and false onto "skip" passes every bundle
  test but ignores an explicit request to validate. The mirror error (verification as the
  default) is caught by the omitted-options functional test.
- S1 (injected sibling, extra): a maintainer-written fail-fast TLS reachability dial
  (`pkg/vmware/endpoint.go:15`, called from `internal/services/collector_work.go:135`); POST
  /collector (background). Dismiss: plumbing, in files the published fix never touches.
- S2 (injected sibling, extra, second transport): a best-effort vCenter REST metadata client
  (`internal/services/inspector_meta.go:15`, called from `internal/services/inspector.go:98`);
  POST /inspector. Dismiss: plain HTTPS client, not SOAP; errors ignored so it reads harmless.

## Sibling candidate list (and why the picks won)
Every place that can reach an outbound vCenter TLS session, plus the plausible maintainer gaps:
1. `pkg/crypto/crypto.go:167,185` Encrypt/Decrypt rebuild Credentials field by field. REJECTED:
   the CredentialsService has no HTTP route at the pinned commit, so it is not reachable through a
   real entry point.
2. `internal/services/forecaster.go:253` savedCreds cache. REJECTED after a behavioural check:
   `resolveCredentials` normalises an empty URL to "/sdk" first, so the saved-credentials branch is
   dead at the pinned commit; POST /forecaster without credentials returns
   `unsupported protocol scheme ""`. Not reachable.
3. `internal/services/rightsizing.go:466-481` collector-triggered auto-rightsizing rebuild.
   REJECTED: it runs only after the collector pipeline reaches forklift parity; that pipeline blocks
   for minutes (and 5 s in VSphereCollector.Close) even against a live simulator, so no reliable
   isolation is possible.
4. `pkg/collector/vsphere.go:108-121` forklift Secret (`insecureSkipVerify` string). KEPT in the
   oracle and not used as a lever: the collector's credential check gates it with the same
   credentials, and the forklift connection cannot be observed independently before the parity
   loop. (Out-of-scope note: the vendored forklift module is not in the tree.)
5. `internal/services/inspector.go:105` vmdetect Detector gets no TLS options. REJECTED: the
   detector's Credentials type is in an external module with no CA/skip fields, so it cannot be
   fixed in this repository. Out of scope.
6. `pkg/vmware/diskmanager.go` operations reuse the caller's client. No new transport.
7. `pkg/vmware/endpoint.go` / `collector_work.go` reachability probe. PICKED (S1): reachable,
   behaves differently under the property, and sits exactly where a maintainer would add a
   fail-fast check.
8. `internal/services/inspector_meta.go` / `inspector.go` REST metadata query. PICKED (S2): a
   genuinely different transport, reachable through the same request, and invisible to a
   SOAP-client search.
Picks beat the others on reachability and on being how-type (S2 is a second transport; S1 is a
second TLS client introduced by ordinary maintenance).

## Verified
- The flaw reproduces at the pinned+injected tree through all six HTTP entry points: a local TLS
  endpoint that records completed sessions sees a completed handshake for every "validate"
  request, including the nested shapes and the asynchronous routes. 11/11 security tests fail on
  that tree.
- The oracle (published fix reduced to source, plus fixes for S1/S2 and for the forklift Secret)
  makes 11/11 security and 9/9 functional tests pass; the project's own tests for
  `internal/handlers/v1` and `pkg/vmware` pass on the pinned+injected tree and on the oracle.
- Every `checks/*.patch` was applied to the pinned+injected tree and run: each security_fail patch
  leaves at least one security test failing with every functional test green; the functional_fail
  patch leaves security green and fails the omitted-options test; both pass patches score a full
  pass (the alternative uses a pointer-typed tri-state and centralises the decision in
  `Credentials.Insecure`, proving the tests accept a different internal design).
- No network is needed at test time. The vCenter needed for the end-to-end positive tests is
  govmomi's in-process simulator (`simulator.VPX`), driven through a reverse proxy behind the same
  TLS endpoint that counts handshakes; the hidden suites never open a listening socket outside
  127.0.0.1 and never dial the internet.

## Could not verify
- Whether the vendored forklift collector honours the `ca.crt` Secret key the published fix adds
  (module not in the tree); the oracle carries the fix, but no test depends on it.
- Whether `vm-migration-detective` opens its own TLS connection and how it verifies certificates
  (external module without TLS fields in its config type); the inspector's detector route is
  therefore out of scope and untested.
- Exact upstream state of the injected siblings (`present_in_latest` is not applicable: they are
  our-copy-only).

## Out of scope (one line)
`test/e2e/*` clients use InsecureSkipVerify against the agent's own HTTPS server (test-only), the
detector module above cannot be changed from this repository, and `api/v2` declares a collector
request type with no v2 handler at the pinned commit.

## Fairness
The instruction states one invariant over outbound TLS (chain to the supplied bundle or system
roots, valid for the host, no session when validation is asked for), the tri-state contract, the
client-error refusal form for contradictory/unusable options, and the preservation clauses
(omitted options keep today's behaviour; explicit skips and valid bundles keep working). It names
no file, package, function or route, and gives no count of sites. Every lever is findable by a
blind engineer from the report plus the code: grep the three TLS client primitives and the
`InsecureSkipVerify` spelling finds all seven sites.

## Gate (run one stage at a time, per the brief)
- static: PASSED (2026-10-24).
- nop (pinned+injected, untouched): PASSED. 11/11 security tests fail on the vulnerable
  tree; 26/26 functional tests pass (9 hidden functional + 17 project test cases from the
  pristine handler and pkg/vmware copies).
- oracle (reference fix applied by solve.sh): PASSED. 3/3 runs at reward 1.0 with identical
  security (11/11) and functional (26/26) results.
- patches: PASSED. All 11 declared checks behaved as declared: each of the eight
  `security_fail` patches left at least one security test failing with every functional
  test green; `overbroad-verify-default.patch` failed the omitted-options functional test
  with security green; `hardening-defensive.patch` and `alt-pointer-tls-decision.patch`
  scored 1.0. The `blind` patch is absent (written later by the blind-fix step).
- Reproduce: source pipeline/docker-tuning.env, export TMPDIR to a work directory, then
  `python3 -I builder/gate.py assisted-migration-agent-ds --only <stage>`.

## Host notes
The shared system Docker daemon deadlocked under load (`/version`, `/info` and
`/containers/json` all hung) during the first nop attempt. The stages above were completed
against a task-private dockerd (documented workaround), and the operator restarted the
system daemon afterwards; the task itself is unaffected.
