# airflow-info-exposure-inj — build notes

- Start UTC: 2026-10-18T16:20:07Z (original build); hardened + Frontier 1.4 conversion 2026-10-21.
- End UTC: see end of file

## Levers (one line each)
- T1 A landing: single-option API route hides only literal registered (section,key) — routes/public/config.py:160.
- T2 A far: full/section listing masks by iterating the registry, missing `[team=section]` sections — shared parser.py:1793.
- T3 A far/producer: team env vars split by the loader into section `<team>`, key `_<section>__<key>` — parser.py:791.
- T4 A far: `config list --hide-sensitive` render path uses the literal lookup — parser.py:2035.
- T5 shape: team `_cmd`/`_secret` entries are never resolved and the cmd/secret exemption keeps them visible.
- T6 B: core start-up secret masking registers only base-section values — configuration.py:438 (real upstream, still in main).
- T7 B: per-key backend kwarg masking keyed on literal section names — services/public/config.py:40 (real upstream, still in main).
- T8 injected: GET /config team view copies team overrides over the masked listing, guarded only by "base already hidden".
- T9 injected: `config get-value --hide-sensitive` uses the literal lookup.
- T10 B (hardening v2): the task SDK's duplicated worker-side `mask_secrets` loop is not team aware. A re-executed
  worker process (`_AIRFLOW__REEXECUTED_PROCESS=1`) skips core start-up masking, so the worker's logging
  configuration is the only place secrets are registered there. Injection: `configure_logging` now calls the
  existing `conf.mask_secrets()` (a natural wiring of otherwise dead code).
- T11 B (hardening v2): team-scoped per-key secrets-backend kwargs
  (`AIRFLOW__<TEAM>___SECRETS__BACKEND_KWARG__*`) are never matched by core's per-key kwarg masking loop,
  which scans `AIRFLOW__SECRETS__BACKEND_KWARG__` only. They therefore stay in logs. (Recommended by the
  fairness review's "Quality to tighten" list.)

## Verified (v2, local dev image)
- The two new security levers reproduce at pinned+injection: 23/23 security tests fail, 25/25 hidden
  functional pass. Oracle: 23/23 + 25/25. Project tests (API config 39 + CLI config 197 + parser 59) pass
  on the oracle and on an independent blind fix.
- New check patches: `sf-no-sdk-log-redaction.patch` -> 2 security fail, functional all pass;
  `sf-no-team-kwarg-log.patch` -> 1 security fail, functional all pass.
- `pass-hardening.patch` / `pass-alt-env-parse.patch` regenerated (old fix + the v2 delta) -> 48/48.
- `pass-blind.patch` (kind=blind) is the independent fix written from instruction.md + repo only by the
  earlier hardening attempt; it passes 48/48 hidden + 236 + 59 project tests (not derived from the oracle).
- Frontier 1.4: /workspace everywhere, separate offline verifier, uid-1000 grading, artifacts restore,
  fresh canary GUID, dual scoring. `conformance_check.py` prints "conforming"; static gate passes.

## Not verified / dropped
- task-sdk `mask_secrets` as a standalone producer: importing any `airflow.*` module initialises core, whose
  (fixed) masking also populates the SDK masker. The worker test therefore runs with the project's own
  re-executed-worker marker so core start-up skips secret registration and the SDK path is the real one.
- Whether team values reach real task logs beyond start-up/worker logging was not traced.
