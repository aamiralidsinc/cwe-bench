# sulu-ds build notes

- start UTC: 2026-10-24T05:24:25Z
- end UTC: 2026-10-24T09:26:06Z
- candidate: GHSA-65CV-W493-7VHQ / CVE-2026-82394, sulu/sulu, pinned 2b959de, fix 44d8844
- pattern B, track injected, builder build-v1, strict_gate true

## One-line levers

- T0 (base, published-fix far site): the admin preview-link route and the product's preview-link
  application service mint and revoke public links without VIEW on the resource's security context
  (manager/generate+revoke; the controller is the report's landing point).
- T1 (real uncovered route, protection never existed): the read route returns the stored link,
  including its public token, to any logged-in admin without VIEW (controller read action, real
  unmodified upstream code; the fix never touched it).
- T2 (injected, wrong object): a share endpoint that already checks VIEW, but on the caller-supplied
  webspace option instead of the security context of the content being linked; it writes through the
  repository directly (second implementation, bypasses the manager).
- T3 (injected, lifecycle): a token-rotation endpoint that assumes that an existing link means the
  caller is allowed and re-mints through the repository without any check.

## Property (written before routes)

A preview link is a public bearer capability for one piece of content. A caller may mint, rotate,
read or destroy a link for a piece of content only if the caller holds VIEW permission on the
security context of that content. The rule is over the outcome (no link or token for content the
caller may not view), not over a surface: it holds for every way the product issues, refreshes or
reports a link, including the product's own preview-link service used by other code. Refusal is a
client error with no side effect. Content without a security context stays linkable. Installations
without the security component keep working.

## Every candidate site/route found before choosing

Real upstream (pinned tree):
- R1 GET /admin/api/preview-links/{resourceId} returns the link with token, no check (real, still in latest).
- R2 POST /admin/api/preview-links/{resourceId}?action=generate (base; published-fix site).
- R3 POST ...?action=revoke (base; published-fix site).
- R4 POST /admin/preview/{start,render,update,update-context} renders any resource without VIEW
  (real, still in latest). Not same protected outcome: renders content but mints no public token;
  the advisory is about the public token, so it is outside this task's protection (noted, not built).
- R5 per-page object ACL not checked (PageController checks SecurityCondition with objectType/id;
  preview checks only the webspace context). Neighbouring feature, outside the advisory (screener
  dismissed it); also the published fix does not do it, so requiring it would contradict the oracle.
- R6 public render routes (/admin/p/{token}, /admin/p/{token}/render): token possession is the authorisation; no
  mint. Left unauthenticated by design (functional test keeps them unauthenticated).
- R7 repository create()/findByResource(): lower-level primitive with no real external reach.

Injected candidates considered:
- I1 share endpoint whose existing check uses the request's webspace option (wrong object) and mints
  through the repository. Chosen (T2): real maintainer mistake; the admin sends webspaceKey from
  the page context, so it normally matches; the endpoint already "has a check", so it reads as done.
- I2 rotation endpoint that re-mints for a resource with an existing link (lifecycle). Chosen (T3):
  different dismissal ("a link exists, so the resource was authorised"); writes through the
  repository, so a manager-only fix misses it.
- I3 console command calling the manager. Rejected: with no authenticated token the real
  SecurityChecker fails open (it swallows AuthenticationCredentialsNotFoundException), so a CLI
  surface cannot carry the property without inventing an impersonation mechanism.
- I4 second preview object provider deriving its context from a request option. Rejected: a realistic
  provider needs the document manager/PHPCR, which the offline harness cannot boot; a fake data
  source would be planted-looking and the injected code would not be plausible product code.
- I5 bulk listing of links for a webspace. Rejected: same concept as R1 (a read surface); the design
  forbids more routes of one concept, and I1/I2 add different mechanisms rather than another read.
- I6 activity-log disclosure of the generated URL. Rejected: fixing it lives in ActivityBundle/Doctrine
  and would require the full ORM/kernel; too far outside the advisory's own code path and untestable
  offline in this task.
- I7 SecuredControllerInterface on the link controller. Rejected as a sibling: the central listener
  would check a fixed context and EDIT/ADD, i.e. a wrong fix, not a missing surface.

## Sites/routes/input shapes the security tests cover

- POST generate: attacker (no VIEW), viewer of another webspace; side effect = no link stored.
- POST revoke: link exists; attacker; side effect = link still stored.
- GET link: attacker and viewer of another webspace; response carries no token.
- product preview-link service generate/revoke called from code with an authenticated attacker.
- share endpoint: caller with VIEW on the option webspace, resource in another webspace; no link.
- rotation endpoint: attacker rotates an existing link; old link unchanged.
All through the real entry point: the product routes (HTTP) and the product's application service.

## Coupled must-keep-working behaviour (functional tests)

- VIEW without EDIT is enough to generate, read, revoke, share (matching webspace) and rotate.
- a provider that returns no security context keeps minting.
- the manager built without a security checker (installations without the security component) keeps
  generating.
- the public token routes stay unauthenticated and keep rendering.
- unknown action still 400, unknown link still 404.

## Harness

Minimal Symfony kernel (FrameworkBundle only) that loads the product's real PreviewBundle
services.php, so the DI wiring the published fix needs is exercised; test doubles for the repository
(in-memory), the activity collector, the view handler, the renderer, Twig and the permission
authority (answers per context and verb, like the real checker). Real SecurityChecker class. Real
routing files. No DB, no network, no PHPCR.

## Verified locally (minimal-kernel harness, before the gate)

On the injected tree with no fix: 9/9 security tests fail (each attack succeeds), 9/9 functional
tests pass.
With solution/fix.patch: 18/18 pass (twice).
Each checks/ patch on the injected tree:
- sf-miss-t0: 5 security fail / 0 functional fail; sf-miss-t1: 2/0; sf-miss-t2: 1/0; sf-miss-t3: 1/0
- wrongfix-crash: 3/0; wrongfix-generate-only: 2/0; wrongfix-reads-only: 7/0;
  wrongfix-after-side-effect: 3/0
- functional-fail-refuse-all: 0 security fail, 3 functional fail (1 error)
- functional-fail-public: 0 security fail, 1 functional fail
- pass-hardening: 18/18 pass; pass-alternative: 18/18 pass

## Gate

- static: PASS (on the shared daemon, before it wedged).
- nop: PASS (9 security tests all fail on the injected vulnerable tree; 9 functional tests pass).
- oracle: PASS, 3 runs, reward 1.0 each, identical results.
- patches: PASS, 12/12 checks behaved as declared (8 security_fail with every functional test still
  passing, 2 functional_fail, hardening 1.0, alternative 1.0).
The shared Docker daemon wedged during this build; nop and oracle first passed on a task-private
dockerd (build/sulu-ds/priv-docker, DOCKER_HOST). After the operator repaired and restarted the
system daemon, static, nop, oracle (3x) and patches were re-run on it and all passed; the patches
stage hit the documented 30s egress-probe flake once (allowlist ValueError) and passed on retry.

## What I could not verify

- The project's own affected unit test (Tests/Unit/Application/Manager/PreviewLinkManagerTest.php)
  and the project's functional test need the require-dev toolchain and MySQL + PHPCR; they are not
  run in this offline image. The functional group carries the equivalent four-argument construction
  test for the affected service.
- The live-preview admin routes (PreviewController) are a real, still-upstream gap of a neighbouring
  feature (they render content without VIEW) but they do not mint a public token; they are outside
  this advisory's protection and are not part of the task (noted, not built).
- The two injected controllers are reachable through the real routing files and the real application
  services, but they are not called by the bundled administration JavaScript (they model an
  integration/older share shortcut).
