# devguard-ds build notes

Start: 2026-10-24T04:58:07Z
End: (filled at the end)

Repo: l3montree-dev/devguard, pinned 2a71eebe8e88a1a7188eb2677047d726a74824f2.
Advisory: GHSA-6P54-FW2F-Q7GF / CVE-2026-48089 / GO-2026-5183. Track: injected, pattern A+B.

## The flaw (verified at the pinned commit)

`MultiOrganizationMiddlewareRBAC`, `OrganizationAccessControlMiddleware`,
`ProjectAccessControlFactory` and `AssetAccessControlFactory` set the same request flag
(`publicRequest`) when a caller is refused only because the organization, project or asset is
public, and then continue. Every write route under such a resource must therefore add its own
refusal (or write-action RBAC). At the pinned commit, 21 write registrations do not, because they
only require the token scope `manage` (a scope any signed-in user can mint for their own token).

## Levers (one line each)

- T1 (main, how-type, pattern B): the organization's GitHub installation callback is a GET that
  writes the installation-organization binding behind only organization read RBAC
  (`router/org_router.go:81`). Reason to dismiss: it is a GET and an installation callback, and
  the published fix and its own regression test skip every GET. Real, unmodified upstream code.
- T2 (how-type, coupled must-keep-working): read-only members must keep recording assessment
  decisions on the findings they can see (`router/dependency_vuln_router.go:39-42`,
  `router/first_party_vuln_router.go:38-39`, `router/license_risk_router.go:35-38`,
  `router/vex_rule_router.go:40-43`). Reason to dismiss: "every write needs write permission"
  closes the public hole but locks read-only members out of triage.
- T3 (how-type shape): the same public flag is granted at project or asset level
  (`middlewares/access_control_middlewares.go:133,185`), so a fix keyed on the organization's own
  public flag misses an org member who is not a member of the public project/asset. Reason to
  dismiss: the report example is a public organization.
- T4 (injected, untouched file): a project-scoped policy write registered on the project's read
  group with a read-action RBAC check that a public request passes
  (`router/project_router.go:70`). Reason to dismiss: it already carries an explicit project RBAC
  check, and project routes are outside the reported asset area.
- T5 (injected, untouched file): an organization-scoped policy write registered on the
  organization's read group with only a scope check (`router/org_router.go:85`). Reason to
  dismiss: maintenance actions sitting among the organization's read routes read as reads.

## Sibling candidates (full list, and why the picks won)

1. `router/org_router.go:81` GET `integrations/finish-installation/` - real GET that writes the
   installation binding. PICKED (T1): real upstream code, far from the report, different verb,
   plausible dismissal.
2. `router/org_router.go:71` GET `trigger-sync/` - real, but only external-entity organizations do
   anything, the same refresh already runs from a background middleware for any request, and the
   external-entity RBAC changes who counts as a visitor. Dropped as a weak, ambiguous sink.
3. `router/project_router.go:59-68` a project-level write on the read group. PICKED as T4 with the
   read-action-RBAC form, because that variant looks protected (an explicit check is attached) and
   needs the mechanism understood; an unguarded route would only cost a search.
4. `router/org_router.go` a second organization-level write. PICKED as T5 (unguarded policy
   reapply) to give the two injected siblings different dismissal reasons ("looks protected" vs
   "sits among reads").
5. `router/asset_version_router.go:66` bulk `events/` route without `EventMiddleware`. Dropped: the
   published fix touches this file, and the task's injected siblings must live where the published
   fix never goes.
6. `router/crowdsourced_vexing_router.go:33` POST `apply/`. Dropped: needs a new controller method
   and service write for no extra difficulty.
7. `router/session_router.go` fast-access routes - already carry write-action RBAC; no gap.
8. `router/asset_router.go` asset-level writes - file touched by the published fix (cosmetic line).
9. `dependency_proxy`, `webhook`, `scan-unauthenticated` - unauthenticated by design, outside the
   org-scoped RBAC chain.
10. `project_router.go` GET `components/` with ActionCreate - a read route, not a write; denies
   public visitors already (action is not read).

## Property

"Access that comes from a resource being publicly readable - rather than from membership in that
same resource - may never be used to change data belonging to it, whatever operation carries the
change, and no matter which level of the hierarchy granted the visibility." Read literally this
covers every published route, the GET callback, the project/asset-level visibility shape and both
injected siblings, without naming any of them.

## Verified

- The flaw reproduces through the real router tree built from the product's own constructors with
  stub repositories: every in-scope route reaches its handler for a public-visibility visitor at
  the pinned commit (status 500 from the stub, or 200 and an installation `Save` for the callback).
- On the oracle tree all security and functional tests pass; on the pinned tree every security test
  fails and every functional test passes.
- All 11 check patches were built and run locally against the hidden suites with the declared
  outcome (see `checks/`).
- The project's own tests for the affected area (`go test ./middlewares ./router`) pass on the
  pinned tree.
- The environment and verifier images share golang:1.27-bookworm and warm the module/build caches
  so the suites run offline.

## Could not verify

- Whether an attacker can obtain a valid, unbound GitHub App installation in a real deployment;
  the test models an unbound installation row, which is the relevant precondition.
- `trigger-sync` reachability for external-entity organizations (dropped, not used).
- Whether triage controllers check that `:dependencyVulnID`/`:ruleId` belong to the routed asset
  version (IDOR); out of scope for this advisory.

## Out-of-scope notes

- `dependency_proxy` npm/go/pypi routes and `/webhook/`, `/scan-unauthenticated/` are
  unauthenticated by design.
- External-entity RBAC and the organization `trigger-sync` route were not built on.

## Check-patch validation (local, before the gate)

Each check patch was applied to the injected pinned tree and the hidden suites were run with the
project's Go toolchain:

| patch | security | functional | expected |
|---|---|---|---|
| (pinned, no patch) | all fail | all pass | nop |
| oracle fix.patch | pass | pass | oracle |
| sf-miss-callback | fail | pass | security_fail |
| sf-miss-project-sibling | fail | pass | security_fail |
| sf-miss-org-sibling | fail | pass | security_fail |
| sf-miss-lower-visibility | fail | pass | security_fail |
| sf-post-only | fail | pass | security_fail |
| sf-published-only | fail | pass | security_fail |
| sf-crash | fail | pass | security_fail |
| ff-blanket-update | pass | fail | functional_fail |
| ff-refuse-all | fail | fail | functional_fail |
| pass-alt | pass | pass | pass |
| pass-hardening | pass | pass | pass |

## Host pause and resume

The build was paused 2026-10-24T06:40Z..07:39Z while the shared host Docker daemon (deadlocking
under load) was fixed and restarted; private dockers started during the pause were shut down.
The gate was then re-run on the system Docker. The image Dockerfiles create the uid-1000 user
*before* warming the Go caches, so the cache layers are agent-owned and no recursive re-ownership
layer (which duplicated the whole cache) is emitted.

## Gate results (final, system Docker)

| stage | result |
|---|---|
| static | pass |
| nop | pass (all 34 security cases fail on the pinned tree; all 22 functional cases pass) |
| oracle | pass, 3 runs identical, reward 1.0 |
| patches | pass: 7 security_fail, 2 functional_fail, 2 pass (hardening, alternative) |

Patch-stage detail: sf-miss-callback (1 security failure), sf-miss-project-sibling (4),
sf-miss-org-sibling (2), sf-miss-lower-visibility (7), sf-post-only (10), sf-published-only (6),
sf-crash (26); ff-blanket-update (18 functional failures), ff-refuse-all (1 functional failure,
also security); pass-hardening and pass-alt both reward 1.0. blind.patch is written after this
build, as the brief requires.

End: 2026-10-24T09:47:00Z
