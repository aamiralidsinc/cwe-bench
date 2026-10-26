# stk-payara-29001 build notes

Start (UTC): 2026-10-26T02:12:59Z (pipeline start; this build session)
End (UTC): 2026-10-26T04:25Z (builder; the pipeline postbuild gate/listing/blind continue after the builder exits)

## What the task is

Payara Server's administration console at `a67eae17e621925b072fbc5880f6bd70a4dad5b6`, the direct
parent of the published fix merge `be83ab093692bafb09125323f3fdefaeab9cc398` (PR payara/Payara#8229).
The advisory is GHSA-X939-7FQ5-V9V6 / CVE-2026-12986: a download request whose `restUrl` names another
administration base makes the console attach the session's admin REST token to that host.

## Levers (one line each)

- **T5 — advisory route, endpoint integrity (published fix).** The three download content sources take
  the outbound admin base from the request (`restUrl`) and `RestUtil` attaches the session REST token
  to it; the fix takes the base from the session. `type=both`, `origin=advisory_route`.
- **T6 — uncovered upstream, representation control.** `DownloadServlet.Context.getAttribute` falls
  back to `request.getParameter(name)`, so `ContentType` in the query becomes the response
  `Content-type`. The published fix does not touch it; still present on upstream main today.
  `type=both`, `origin=uncovered_upstream`.
- **T7 — uncovered upstream, path/location shape.** `target` (log files) and `appName` (client stubs)
  are concatenated into a staging file name and an admin REST path segment with no shape validation.
  The published fix does not touch it; still present on upstream main today. `type=both`,
  `origin=uncovered_upstream`.

Concept groups: `[T5]`, `[T6]`, `[T7]` (three independent edit sites; the published fix closes T5 and
leaves T6/T7 reachable, proved by `checks/upstream_fix.patch`).

## Scope note (one line)

T6 and T7 are sibling protections in the same `DownloadServlet`/content-source surface the advisory
names, but they are outside the advisory's CSRF/credential-leak family; the reader's H4 design lists
them as independent concepts, and the report covers them only through the general property.

## Deviation from the reader's trap list

The reader record's T1/T2/T3/T4 group (anti-forgery/proof of intent on `/download/*`) was not built as a
separate concept. A mechanism-neutral hidden test cannot accept both an origin/Referer fix and a
session-token fix: a token fix changes the legitimate request in a way the harness cannot learn without
running the JSF pages, so the test would fail a valid design. T5 is the advisory's own route and the
published fix's subject, so it carries the advisory-route anchor. The stack still has three independent
concepts and both model types (`type=both` on all three; T6/T7 are routes where the protection never
existed).

## What was verified

- Pinned code, real servlet entry point (`doGet`/`doPost` with a servlet-container-shaped request and a
  loopback admin REST endpoint): 8 security tests fail, 6 functional tests pass.
- Reference fix (published T5 diff + T6 fallback removal + T7 name validation): 14/14 pass.
- Concept misses: `miss_endpoint` 3 security fail, `miss_representation` 2, `miss_location` 3; all
  functional pass in each. `upstream_fix.patch` (the published fix alone): 5 security fail, functional
  pass.
- Pass designs: `pass-hardening` 14/14; `pass-alt` (reject the routing hint + page update, keep the
  document fallback only for non-representation attributes, percent-encode names) 14/14.
- Wrong fixes behave: refuse-all 5 functional fail; crash-as-refusal 3 security fail; wrong resource 2;
  one direction 1; reads-only 1; check-after-adjustment 1; malformed identity 3.
- The module's own test `org.glassfish.admingui.common.test.RestResponseTest` runs in the functional
  group through a pristine copy and passes on the pinned code and under every pass design.
- The offline compile path (`console-build.sh` in the agent image; the verifier's BUILD command) was
  exercised against the pinned and fixed trees in the maven base image.
- Environment image builds from the sparse checkout; verifier image builds from `tests/`.
- Control task `stk-payara-29001-control` (same report, only the advisory route in the security tests
  and reference): pinned 4 security fail / 6 functional pass, published-fix oracle 10/10, all check
  patches behave.

## What could not be verified

- The full Payara Maven reactor is not built: the console module's internal artifacts are not in the
  sparse checkout. The tests compile the affected sources against pinned third-party jars plus a small
  compatibility layer for the rest of the runtime (the same layer stubs `GuiUtil`, `MiscUtil`, the
  admin auth constant, the security/SSL services and Faces). A change the solver makes outside the
  compiled file set is not observed; the report's properties live in the compiled files.
- The reader record in this checkout is `pipelines/stacking/out/reader-ds/h4-29001.json`; the manifest
  keeps the path the build prompt names (`pipelines/stacking/out/reader/h4-29001.json`), which does not
  exist in the checkout.
- The published fix is a merge; the first-parent diff used is `a67eae..be83ab`. The PR branch tip
  `b95e118` additionally changes the admin-password page, which the merge drops; that unrelated change
  is not part of the task.
- `present_in_latest=yes` for T6/T7 was read from the raw files on upstream `main` at build time.

## Gate

- `static`: PASSED for the stacked task (and for the control), and
  `check_stack.py stk-payara-29001` reports conforming (3 concepts, H4).
- The verifier was exercised end to end with the real `tests/test.sh` and the real
  `stk-payara-29001-ver` image (the same BASE/BUILD/run_group/score.py the gate uses), against a
  restored copy of the pinned tree and of the reference-fixed tree:
  - pinned: reward 0.0, security 0/8, functional 6/6;
  - reference: reward 1.0, security 8/8, functional 6/6.
- `nop`/`oracle`/`patches` through Harbor were attempted; at build time the shared Docker daemon was
  at ~130-150 running containers and load >300. The Harbor egress-control kernel probe (a container
  start with a 300 s timeout) did not get a container on either attempt, and the retried compose
  build stayed queued behind other sessions' builds, so the manual attempts were stopped rather than
  left competing. The pipeline's postbuild gate (which sources `common/gate/docker-tuning.env`, holds
  `build/SLUG/.gate.lock` and retries each stage up to four times) is the authoritative run. Every
  check patch was also applied to the pinned tree and run through the same compiled sources and
  hidden suites in the maven base image, with the outcomes recorded above.
