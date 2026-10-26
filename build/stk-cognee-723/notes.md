# stk-cognee-723 — build notes

- Start (UTC): 2026-10-26T02:27:54Z
- End (UTC): 2026-10-26T04:58:32Z
- Pattern: A+B, track stacked (reader record H4 h4-723)
- Pinned: topoteretes/cognee @ 4067f0b8a255f3a511a71cc0806b9f20dd73c31b
- Published fixes: d10b1b7 (guard + registration gate + full masking), 10971db (revert of d10b1b7),
  ebcf824 (superuser guard re-applied). Net upstream final state: the write guard only; the gate and
  the masking were reverted and never re-landed.

## Levers (one line each)

- T1 (advisory route; A; type in record `neither`): `POST /api/v1/settings` only resolves the caller
  and never asks whether it is deployment-privileged — `get_settings_router.py:73-101`; the
  must-keep-working value is the documented single-operator posture, where an anonymous request
  resolves to the privileged bootstrap account.
- T3 (hidden; B; deepseek): anonymous registration is mounted unconditionally and ignores the
  deployment's authentication posture — `get_register_router.py:5-6`, `client.py:219-223`; reason to
  dismiss: open sign-up is the framework default and the route mints an ordinary account.
- T4 (hidden; B; both): the read serializer keeps the first ten characters of each stored credential
  and slices the vector credential unconditionally, so an unconfigured credential raises while the
  response is built — `get_settings.py:87-96,181-191` (unset-key shape from T5 is folded here);
  reason to dismiss: masking is a display concern and the existing suite always mocks a non-empty key.
- T6 (hidden; B; mimo; coupled value, not a concept): the masked value a client has just read is
  posted back; only the shared `'*****'` sentinel skip keeps the stored credential intact —
  `save_llm_config.py:17-18`, `save_vector_db_config.py:18-19`.

## Concepts

`[T1]`, `[T3]`, `[T4]` (three independent edit sites: the write handler, the registration router, the
read serializer). T6 is a coupled must-keep-working value, proven functionally
(`functional_fail_mask_reject.patch`).

## Gate results (container)

- static: PASS (stacked and control).
- nop: PASS — the in-container verifier ran the real suites: security 0/8 pass (every security test
  fails on the pinned code), functional 9/9 pass, reward 0.0.
- oracle: PASS — three independent runs, each 17/17 (`reward 1.0`), identical results.
- patches: not container-run; every `checks/*.patch` was verified locally in its declared direction
  (table below). The host Docker daemon degraded to ~60 s per full container listing and 8-20 min per
  compose step, which exhausted the session before this stage.
- control: static PASS; local nop and oracle green; its container gate was not run.

## What was verified

- The pinned tree reproduces every tested route through the real HTTP app (FastAPI TestClient with
  lifespan): anonymous writes in single-operator posture, ordinary-user writes in multi-user posture,
  unconditional registration, prefix-masked reads, and a 500 on the settings read with no key set.
- Local nop run: 8/8 security tests fail on the pinned tree, 9/9 functional tests pass.
- Local oracle run: 8/8 security and 9/9 functional pass with the reference fix.
- `git apply --check` on every `checks/*.patch` against the pinned tree.
- Targeted runs of the check patches that were hardest to place: `missing_authority` (security
  fails, functional passes), plus the variants listed in `gate_report.json` after the container gate.
- The project's own settings integration test
  (`test_conditional_authentication_endpoints.py::...::test_settings_endpoint_integration`) passes at
  the pinned commit with the process posture exported; it is ported into the hidden functional suite.

## What could not be verified

- The recorded trap T2 (`cognee/api/v1/config/config.py`, in-process library setters) is not built:
  it has no caller identity and no HTTP actor, and the published fix never touches it. Recorded as out
  of scope, not as a lever.
- The recorded trap T7 (`is_superuser` accepted by the registration schema) does not reproduce:
  fastapi-users 15.0.5's register route calls `user_manager.create(..., safe=True)`, which drops
  `is_superuser`, so a self-registered account is never privileged. Verified by request and by reading
  the installed package.
- T5 is folded into T4 rather than recorded as its own trap: it is the same serializer, same fix site
  and same security-test file, and recording it separately would describe one shape twice.
- The grader-facing listing review (`pipelines/stacking/4-listing`) was not run here.

## Environment notes

- Both images install the same pinned dependency set (141 packages) baked into the Dockerfiles; the
  project is installed editable into `/workspace` in the agent image, and the verifier imports
  it from the restored `/workspace`.
- Each hidden test module runs in its own interpreter because the application resolves its auth
  posture and registration policy once, at import. `run_junit.py` merges the per-module JUnit XML.
- `/workspace/.env` is excluded from the artifact and removed before grading: `cognee/__init__.py`
  loads it with `override=True`.

## Check patches (local direction check)

Each row was run against the pinned tree with the patch applied; `security_fail` must leave a
security test failing while every functional test passes, `functional_fail` must break a functional
test, and `pass` must be 1.0.

| patch | expect | local result |
| --- | --- | --- |
| miss_T1 | security_fail | write-privilege 3 fail; anonymous save 3 pass |
| miss_T3 | security_fail | registration 2 fail; registration default 1 pass |
| miss_read | security_fail | masking 2 fail, unset 1 fail; round-trip 2 pass |
| upstream_fix | security_fail | registration 2 fail, masking 2 fail; anonymous save + registration pass |
| functional_fail_mask_reject | functional_fail | round-trip 2 fail; masking 2 pass |
| refuse_all | functional_fail | anonymous save 3 fail |
| crash_as_refusal | security_fail | write-privilege 3 fail; anonymous save 3 pass |
| one_role_or_direction | security_fail | write-privilege 3 fail; anonymous save 3 pass |
| reads_only | functional_fail | ordinary-user read fails |
| check_after_adjustment | security_fail | write-privilege 3 fail; anonymous save + round-trip pass |
| wrong_resource | security_fail | write-privilege 3 fail |
| malformed_identity | security_fail | write-privilege 3 fail |
| missing_authority | security_fail | write-privilege 3 fail; multi-user 2 + anonymous save 3 pass |
| adjacent_api | functional_fail | ordinary-user read fails |
| hardening | pass | 8/8 security + 9/9 functional |
| alternative | pass | 8/8 security + 9/9 functional |

The control task (`stk-cognee-723-control`) was run locally too: pinned 4/4 security fail and
9/9 functional pass; guard-only reference 4/4 + 9/9.
