# stk-glance-ghsavwr9 build notes

- Start (UTC): 2026-10-26T02:14:26Z
- End (UTC): filled in after the gate run.
- Product: openstack/glance, pinned 6b2300fb0c01820b7e45ba2806c1f2468394bd50 (direct parent of
  the first published fix commit 6ab0992e5472), Python 2.7, `python:2.7-slim` (Debian buster
  archive mirror) with the 2012-era dependency pins.
- Pattern: stacked H3b. Advisories A = GHSA-6rrm-xxvh-7r87 / CVE-2012-4573 (v1 arbitrary deletion),
  B = GHSA-vwr9-9f8v-vp5m / CVE-2012-5482 (v2 arbitrary deletion, incomplete fix of A).

## Levers (3 concepts; one line each)

1. **T1 (advisory route, DeepSeek-type)** — `glance/api/v1/images.py:816-845`: the v1 delete handler
   removes (or schedules removal of) the stored data before the registry delete that performs the
   ownership check; a non-owner who can see a public image destroys its data and gets a refusal.
   Reason to dismiss: the registry/DB layer already enforces ownership and the handler checks the
   protected flag, so the handler looks guarded.
2. **T2 (published-fix far site, both-type)** — `glance/api/v2/images.py:256-276`: the second API
   implementation performs the same removal before its database authorization. Reason to dismiss:
   the controller calls `db_api.image_update`/`image_destroy`, which both run the mutation check,
   and `_get_image` already 404s deleted images.
3. **T3 (uncovered route, MiMo-type)** — `glance/db/sqlalchemy/api.py:208-215` reached through
   `glance/registry/api/v1/images.py:305`: the shared destroy checks ownership but not the protected
   flag, so the registry service's own delete destroys a protected image's metadata. Reason to
   dismiss: the registry is an internal service and both API handlers already refuse protected
   deletes. Coupled must-keep-working: unprotect-then-delete and protected metadata updates.

## What was verified

- The flaw reproduces through the real WSGI services at the pinned commit: v1/v2 non-owner delete
  removes the store file and returns 403/404; v1 delayed delete queues the removal; registry delete
  of a protected image succeeds; the project's 399 affected tests pass on the pinned tree.
- The reference fix (A + B + the shared protected check) makes the 6 security tests pass, the 9
  hidden functional tests pass and all 399 project tests pass.
- Every check patch was applied to a pristine tree and run locally against the three suites
  (security, hidden functional, the 399 project tests). Local outcomes:
  reference / alt_correct_fix / hardening -> 6/6, 9/9, 399/399;
  miss_concept_v1 -> 2 security fail, functional and project pass;
  miss_concept_v2 -> 1 security fail; miss_concept_protected -> 3 security fail;
  upstream_first_fix -> 4 security fail; upstream_fix -> 3 security fail;
  functional_overbroad -> 7 hidden functional + 16 project fail; one_role -> the two admin
  functional tests fail; protected_immutable -> the two protected-value functional tests fail.
- The whole verifier flow was run end-to-end (separate image, `/tests/test.sh`, uid 1000):
  reference reward 1.0 with 414/414 tests; pinned reward 0.0 with the 6 security tests failing and
  all 408 functional tests passing.
- `check_stack.py` reports conforming (3 concepts, H3b).
- The instruction's general property was checked against each hidden trap with the one-bug test.

## What could not be verified / was dropped

- **The alternate in-memory data backend (`glance/db/simple/api.py`) was dropped as a lever.** Adding
  authorization there makes the project's own v2 controller tests fail: those tests build ownerless
  images with the permissive test double (`self.db.image_create(request.context, ...)`) and delete
  them as a non-admin, while the property (and the SQLAlchemy backend) make ownerless images
  admin-only. Keeping the lever would either ship a weakening (ownerless images deletable by anyone)
  or break a must-keep-working project test, so it is reported, not shipped.
- **Shared-member deletion is not exercised.** At this commit `image_member_find` returns member
  dicts without a `deleted` key, so `is_image_visible` raises KeyError for a shared private image
  before any delete logic. The property covers it; the behaviour is not reachable through a real
  entry point.
- **v2 delayed deletion is not exercised.** The pinned handler passes an undefined name (`id`) to
  `schedule_delayed_delete_from_backend`; with a stored location it raises NameError. That is a
  separate defect, not part of the advisory's protection.
- The upstream fix commits' exact texts were confirmed from the fetched git history; the two
  published A commits and the two B commits are the same changes merged on two branches.
- Advisories' own texts were read from the GitHub advisory API (summaries above).

## Listing review

The first automatic review (on the instruction as first written) returned FAIL: T2 and T3 were
labelled DESCRIBED from one scope-widening clause ("not a list of routes, services or cases") and
the reviewer also read the intro's "until someone deliberately removes that marking" as describing
the unprotect-then-delete value. Both phrases were removed from the instruction; a fresh review of
the final text returns PASS (0 NAMED, 0 DESCRIBED; both hidden traps GENERAL).

## Container gate

The shared Docker daemon stopped progressing Harbor compose builds during the gate (at times a
plain `docker run` also timed out while other builders held ~160 containers); the three parallel
stages were killed rather than leave hung builds, and the gate was restarted after clearing my own
queue. The nop trial that completed before the wedge was green (0/6 security, 408/408 functional,
reward 0.0). The gate-equivalent outcomes were verified end-to-end with the same verifier image and
test.sh: reference 1.0 (414/414), pinned 0.0, and every patch check with its declared outcome. The
final gate state is recorded in `gate_verdict.json` / `recover.log`.

## Control task

`stk-glance-ghsavwr9-control` has the same pinned code and the byte-identical report, with only the
advisory's own route (the two v1 deletion tests) in its security group and the published first fix
as its reference. Its end-to-end verifier runs: pinned code -> reward 0.0 (0/2 security, 408/408
functional); first fix -> reward 1.0 (2/2 security, 408/408 functional). Its patch matrix:
miss_advisory_route -> 2 security fail, functional pass; functional_overbroad -> functional fail;
alt_correct_fix and upstream_first_fix -> pass. The control's `hardening` and `functional_overbroad`
patch copies were refreshed from the stacked task after the alternate-backend lever was removed
(the older copies still contained that dropped change and failed two project tests).

## Scope

Only the two advisories' deletion/authorization protection is in scope. Nothing outside that was
built on.
