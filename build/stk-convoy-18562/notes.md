# stk-convoy-18562 build notes

Start (UTC): 2026-10-26T02:05:19Z
End (UTC): 2026-10-26T04:30Z (gate blocked by shared Docker daemon; see gate-status.md)

## Levers

- **T1 (advisory route, type both)** — the project-scoped source read by identifier ignores the
  project argument (`internal/sources/impl.go:436`, `internal/sources/queries.sql:145`); the report
  leads here and the unused argument makes the intended scope visible.
- **T3 (uncovered write, type deepseek)** — the source update is keyed on the identifier alone
  (`internal/sources/impl.go:375`, `internal/sources/queries.sql:99-108`); the dismissal is that the
  scoped read hides it from HTTP and the sibling delete is already project-scoped. Its own route is
  the service API, exercised directly.
- **T4 (uncovered how-type, type mimo)** — the subscription update validates the source only inside
  the `endpoint_id` block (`services/update_subscription.go:74-90,116-118` plus the subscription
  UPDATE); the guard is visible at line 85, so the path reads as handled.
- **T5 (uncovered route, type deepseek)** — the subscription create validates source ownership only
  for incoming projects while copying `source_id` for every project type
  (`services/create_subscription.go:65-74,88-102`); the field reads as incoming-only.
- **T6 (uncovered read far site, type deepseek)** — both subscription-to-source joins are
  unconstrained by project (`internal/subscriptions/queries.sql:204,444`); the subscription row is
  project-scoped, so the response looks scoped and the source looks like display metadata. Covers
  rows already stored.
- **T7 (coupled must-keep-working value, type mimo)** — the public capability lookup by mask
  identifier has no project and must stay project-agnostic (`internal/sources/impl.go:467`,
  `queries.sql:211`, `api/ingest.go:41,448`); an over-broad fix that scopes every lookup breaks it.

## Concepts

`[T1, T3]`, `[T4, T5]`, `[T6]` (3 independent concepts). T7 is a coupled value, not a security
concept; it is guarded functionally.

## Verified

- Pinned commit: all 9 hidden security tests fail; all 9 hidden functional tests pass; the
  `internal/sources` and `internal/subscriptions` project suites and the affected `services` unit
  tests pass.
- Reference fix: 9/9 security, 9/9 hidden functional, and the project suites pass.
- Alternative design (subscription source ownership enforced in the repository instead of the
  handler): same result.
- Hardening (reference plus repository-layer defence in depth and an empty-mask guard): same result.
- Patch matrix run locally against the real database:
  `miss_source_scope` 7 security failures, `miss_subscription_writes` 2, `miss_subscription_join` 2,
  `upstream_fix` 5, `sf_get_only` 8, `sf_self_compare` 7, `sf_check_after_write` 2,
  `sf_wrong_object` 2 — all with the functional suite green; `ff_refuse_all` and
  `ff_reject_outgoing_source` fail functional.
- Migrations run on PostgreSQL 15 and 17 (the verifier image pins Debian's PostgreSQL 15 and builds
  a migrated template database offline; each test clones it).
- The pinned commit is the direct parent of the published fix commit (verified with
  `git rev-parse 1cc67cd16fb1f8890cc83a3998d3f92dceb7fd06^`).

## Could not verify

- The published fix commit also carries a JWT blacklist canonicalization for a different advisory;
  it is deliberately excluded from this task.
- The upstream Twitter CRC handler dereferences a nil provider configuration at the pinned commit,
  so the mask-id capability is exercised through its lookup rather than the CRC route.
- The project's own `internal/sources` and `internal/subscriptions` suites launch Docker-backed
  PostgreSQL in the pinned tree; the verifier restores pristine copies of those test files and runs
  them with a local-PostgreSQL clone helper (same assertions, same code under test) because the
  verifier has no Docker daemon.

## Gate log

- `static`: PASS (stacked and control); `check_stack.py`: conforming, 3 concepts, H4.
- `nop`: PASS on 2026-10-26T04:08Z — 9/9 hidden security tests fail on the pinned tree, 232
  functional tests pass (9 hidden + the pristine internal/sources, internal/subscriptions and
  affected services suites).
- Two earlier nop attempts were infrastructure-only: the first lost Harbor's temporary compose
  file after a 34-minute image build; the second exposed a task-side artifact bug (the generic
  `build` exclude dropped the repo's embedded `api/ui/build`). The task.toml artifact excludes
  were narrowed to `.git`, `node_modules`, `__pycache__`, `.cache`, and the Dockerfiles were
  trimmed (`go mod download` instead of `all`, no second 4.8 GB `/go` chown layer).
- `oracle` and `patches`: BLOCKED by the shared Docker daemon. From ~04:14Z the daemon answers
  `_ping`, `/version` and `docker info` in <1s but **cannot create containers**: Harbor's
  egress-kernel probe (`docker container run --rm alpine:3.23.4 ...`) hangs for minutes, and
  `docker create alpine` does not return; `docker events` shows no container-create event from
  any session. Two oracle attempts produced no trial; the stage is stuck in the probe and cannot
  reach the verifier. This is infrastructure, not a task result: no oracle or patch verdict was
  produced. The private-dockerd workaround was deliberately not used (the operator requires the
  system Docker only), and the shared daemon was not restarted (other sessions' containers).
  The oracle, alternative, hardening and every wrong-fix patch were verified locally against a
  real PostgreSQL before the wedge; those results are in `verified.local` in the manifest.

## Wrong-fix evidence kept in checks/ but not gate-run (VM time budget)

`sf_get_only.patch`, `sf_self_compare.patch`, `sf_check_after_write.patch`,
`sf_wrong_object.patch`, `ff_reject_outgoing_source.patch` were each verified locally against the
real database: the first four leave security red with functional green, the last breaks the
outgoing own-source functional case. The catalogue marks their classes `n/a` with those reasons;
the gate runs the per-concept misses, the published-fix recall, one refuse-all functional failure,
the alternative fix and the hardening pass.
