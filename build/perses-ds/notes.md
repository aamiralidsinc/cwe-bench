# perses-ds build notes

* Start (UTC): 2026-10-24T05:18:25Z (pipeline start recorded in `build/perses-ds/start_utc.txt`)
* End (UTC): 2026-10-24T10:02:00Z (gate patches stage finished; Docker stages resumed after the host daemon fix at 07:48Z).

## Advisory and pinned tree
GHSA-4227-9989-JRHX / CVE-2026-63199 / GO-2026-6514, perses/perses, CWE-862. Pinned
`51b7c0bba66fd2a725de9dc885808c68fbd79091`, published fix `2368c9ef4eb0a70fbca5df69aa20e595821ab625`.
The published fix gates secret references at datasource save time (project and global datasource
services) and at proxy time for the three unsaved proxy routes; it deliberately leaves saved proxy
routes without a credential check, so that viewers keep querying already-authorized configuration.

## Levers (one line each)
* T1 — Pattern A (report site): the three unsaved proxy routes resolve a secret named in the body
  with only Datasource/GlobalDatasource create permission (`internal/api/impl/proxy/projectdatasource.go:52`,
  `globaldatasource.go:53`, `localdatasource.go:53`). Reason to dismiss: a one-shot body persists
  nothing, so the check looks like it belongs where datasources are saved.
* T2 — Pattern A (far site, different package): saving or updating a project/global datasource that
  names a credential is authorised only by Datasource create/update
  (`internal/api/impl/v1/datasource/service.go:44,64`, `globaldatasource/service.go:44,64`).
  Reason to dismiss: the CRUD services already pass a resource RBAC check, so saving looks
  authorised.
* T3 — Pattern B (real unmodified upstream, protection never existed): a dashboard's local
  datasource specs are saved with only Dashboard RBAC and later resolved by the saved dashboard
  proxy route (`internal/api/impl/v1/dashboard/service.go:57,79`; sink
  `internal/api/impl/proxy/localdatasource.go:62`). Reason to dismiss: dashboards are a separate
  resource with their own RBAC and the report is about datasources.
* T4 — Injected sibling S1: a saved proxy route for ephemeral dashboards' local datasources
  (`internal/api/impl/proxy/proxy.go:178`, handler `ephemeraldatasource.go:41`) whose producer,
  the ephemeral dashboard service, never checks Secret read
  (`internal/api/impl/v1/ephemeraldashboard/service.go:50,72`). Reason to dismiss: ephemeral
  dashboards are transient previews.
* T5 — Injected sibling S2 (shape trap): a header value may reference a stored credential
  (`{{secret:NAME}}`), resolved by `resolveHeaderSecrets` (`internal/api/impl/proxy/proxy.go:281`)
  through the same retrieve callback. A check that only inspects the proxy's `secret` field sees
  nothing. Reason to dismiss: header values look like plain forwarding configuration.
* Coupled must-keep-working (part of T2/T3/T4): a caller that may read the datasource but not the
  credential keeps querying saved project, global, dashboard and ephemeral-dashboard datasources;
  the functional suite drives all four.

## Verified locally (before the gate)
* Full product server via `core.New` + real HTTP routes, native RBAC, file persistence, real plugin
  schemas (Prometheus + Markdown archives), and a local upstream service that records what it
  receives. The plugin archive is only in the verifier image (`/opt/perses-plugins`).
* Pinned+injected tree: 14/14 security tests fail (the credential reaches the upstream, or the
  authoring request is accepted), 12/12 hidden functional tests pass, the project's own
  `internal/api/impl/proxy` tests pass.
* Reference fix: every hidden security and functional test passes, as do the project's tests.
* The published fix alone (without the dashboard/ephemeral/header coverage) was run against the
  same suites: it blocks T1/T2 and leaves T3/T4/T5 failing, which is what the task adds.
* Gate `oracle` (Docker verifier, 3 runs): PASS - reward 1.0 each, identical per-test results.
* Gate `patches` (Docker verifier, 13 checks): PASS - every check matched its declaration (9 security_fail, 2 functional_fail, hardening and alt_fix reward 1.0).
* Gate `nop` (Docker verifier): PASS - 14/14 security tests fail on the pinned+injected tree, 83/83 functional pass.
* Each wrong-fix patch was applied locally and its declared outcome checked (see the results below
  and `build/perses-ds/checks/`).

## Check patch results (local)
Applied each `checks/*.patch` to a fresh pinned+injected tree and ran both hidden groups plus the
project's proxy package tests:

| patch | security failures | functional failures | project tests |
|---|---|---|---|
| hardening.patch | 0 | 0 | ok |
| alt_fix.patch | 0 | 0 | ok |
| miss_proxy_unsaved.patch | 4 | 0 | ok |
| miss_authoring.patch | 5 | 0 | ok |
| miss_dashboard.patch | 5 | 0 | ok |
| miss_ephemeral.patch | 2 | 0 | ok |
| miss_header_shape.patch | 2 | 0 | ok |
| check_after_adjustment.patch | 4 | 0 | ok |
| wrong_resource.patch | 14 | 0 | ok |
| project_only.patch | 3 | 0 | ok |
| crash_as_refusal.patch | 14 | 0 | ok |
| refuse_all.patch | 0 | 9 | ok |
| overbroad_proxy.patch | 0 | 4 | ok |

## Not verified / guesses
* The advisory text itself was not available; the screener summary and the published diff were the
  source. The dashboard/ephemeral-dashboard gaps were confirmed behaviourally on the pinned tree,
  not from an upstream report.
* `present_in_latest` for the dashboard route is `unknown` (no network read of current upstream).
* The SQLProxy branch of `newProxy` resolves secrets too, but no shipped default plugin schema
  accepts a SQLProxy config (all built-in datasources pin HTTPProxy), so no real entry point
  reaches it from a default installation; it is covered by the reference fix but not by a test.
* Plugin archives are downloaded at image-build time (Prometheus and Markdown only). The whole
  default plugin set (96 MB) was not shipped.
* `/tmp` inode exhaustion on the shared VM was worked around by pointing the server's own
  temporary directories at the workspace (`PERSES_TEST_WORKDIR`, `TMPDIR`).

## Out of scope (not built on)
* The reverse proxy forwards the caller's own Perses JWT in the outbound `Authorization` header
  unless a secret overrides it; that is a separate credential-forwarding concern, not this
  advisory's reference-authorization property, and is not tested.
