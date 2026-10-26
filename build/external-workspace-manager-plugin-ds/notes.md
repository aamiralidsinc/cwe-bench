# external-workspace-manager-plugin-ds — build notes

- Started (UTC): 2026-10-24T05:26:23Z
- Ended (UTC): 2026-10-24T09:35:03Z
- Repo: jenkinsci/external-workspace-manager-plugin
- Advisory: GHSA-HRMJ-8FM9-CG8X / CVE-2026-57296
- Pinned: 265ef4f624a8fefc976b1656d83d9c1ab1a493ae
- Published fix: 2fccbbd398cf209f5931b48e006659dbee86ddf2 (contains real hunks; the screener's
  "no hunks" note was wrong)

## What the published fix actually does (verified from the commit diff)

1. `ExwsAllocateExecution.computeCustomPath` — reject `..` segments in the user `path` parameter.
2. `ExwsAllocateExecution.computePathBasedOnTemplate` — re-apply the same check to the path after
   `replaceMacro` expands build parameters (the raw template check ran before substitution).
3. `ExternalWorkspace.doWs` — canonical-path containment check under `masterMountPoint`, explicitly
   for "previously persisted malicious pathOnDisk values" browsed via `/exws/browse/{id}/ws/`.
4. Adds two tests to `CustomWorkspaceTest`.

The fix does **not** guard the agent-side join (`ExwsExecution.start` -> `child(pathOnDisk)`) and
does not re-validate a workspace replayed from an earlier run (`exwsAllocate selectedRun:`); the
commit message says the value "reached the agent-side sink ExwsExecution.child(pathOnDisk)
unguarded" and that only the producers were closed.

## Security property (written once, in the report)

> The plugin must never act on a filesystem location outside a disk's mount point, whatever value a
> build supplies and however that value reaches it, including a workspace value that was recorded
> by an earlier allocation.

Every tested route and injected sibling falls under this literal statement. No route, operation,
channel or object kind is named in the report.

## Levers (each with a different reason to dismiss/skip)

Distances are from the reported landing point (`ExwsAllocateExecution.computeCustomPath`).

| id | pattern | shape | where | reason to dismiss |
|----|---------|-------|-------|-------------------|
| T0 | A (reported) | literal custom path with a nested `..` segment (`sub/../../outside`, `../outside`) reaches `pathOnDisk` | `steps/ExwsAllocateExecution.java:219-230` | none — this is the site the report leads to; still tested as the baseline |
| T1 | B (main, how-type) | a `pathOnDisk` recorded by an earlier allocation is replayed by `exwsAllocate selectedRun:` and joined to the node mount point with no re-validation; shape: stored value with a nested `..` segment | `steps/ExwsAllocateExecution.java:114-132` -> `steps/ExwsExecution.java:103-104` | "the value was produced by an earlier allocation, which the fix already validates" — the check never sees the stored value |
| T2 | A (how-type, shape/ordering) | the `..` only appears after `replaceMacro` expands a build parameter into the disk-pool workspace template; the relative check runs on the raw template | `steps/ExwsAllocateExecution.java:265-284` | "the template is admin-configured global config; only the `path` step parameter is user input" |
| T3 | A (far package) | controller-side browse joins `masterMountPoint` + a persisted `pathOnDisk` and serves a `DirectoryBrowserSupport` without containment | `model/ExternalWorkspace.java:89-96` (package `model`, entry `/exws/browse/{id}/ws/`) | "a read-only UI feature reached by an opaque fingerprint id, not the allocate step" |
| S1 | injected | a controller-side workspace cleanup action deletes the workspace through the documented `getCompleteWorkspacePath()` helper; no containment; a persisted `..` value deletes outside the mount | injected into `model/ExternalWorkspace.java` (same file, adjacent action) | "a maintenance action that reuses the plugin's own recommended path helper" |
| S2 | injected | `exwsAllocate` gains an optional job-supplied sub-folder appended to the default path; only a relative-path check, no `..` check | injected into `steps/ExwsAllocateStep.java` + `steps/ExwsAllocateExecution.java` (default-path branch) | "the default path is derived from trusted disk config and the job name; the optional folder looks benign" |

T1 and T2 are the two how-type levers: T1 needs the persistence/replay mechanism understood, T2
needs the check-before-substitution ordering understood. T0, T3, S1, S2 are additional sites, each
with its own test.

## Full candidate list for injected siblings (searched, before picking)

1. `ExternalWorkspace.getCompleteWorkspacePath()` (model:78-80) used by a planted cleanup/delete
   action — **picked as S1** (delete outcome, persisted value, documented helper).
2. `ExwsAllocateExecution` default path + a job-supplied sub-folder parameter
   (screener O8b #2) — **picked as S2** (a route with no check at all, allocate-time).
3. A `WorkspaceBrowserRootAction.getFile(workspaceId, relativeName)` raw-file download helper using
   `getCompleteWorkspacePath()` — rejected: a second read-outside route on the same browse surface,
   same concept as T3; adds no new reason to skip.
4. An `ExwsExecution` `subDirectory` argument applied to the workspace — rejected: shares T1's sink
   and the same containment lesson; would be a second route of one concept.
5. A node-level disk-usage helper walking `new File(nodeMountPoint, pathOnDisk)` — rejected: a
   read-only status surface, same concept as T3 and not reachable through a pipeline/HTTP entry
   point in a way a user drives.
6. `computeDefaultPathOnDisk` expanding macros in `physicalPathOnDisk` — rejected: same
   post-expansion concept as T2, and `physicalPathOnDisk` is admin config.
7. `FormValidationUtil.validateWorkspaceTemplate` (utils:46) — rejected: UI hint only, not an
   enforcement point (screener agrees).

S1/S2 beat the rest because they are how-type (persisted/derived value, no check at the sink) and
are far from the report's landing point (different package/method family); each has a distinct
dismissal ("recommended helper" vs "trusted default path").

## Sites/routes and input shapes covered by security tests

- T0: custom `path` = `../outside`, `sub/../../outside`; assert build failure + no file outside.
- T1: persisted allocation (created by XML round-trip, simulating a record from an earlier version)
  replayed by `selectRun` + `exwsAllocate selectedRun:` + `exws { writeFile }`; assert failure + no
  file outside.
- T2: template `test/${BRANCH}` with `withEnv(['BRANCH=../../outside'])` and
  `BRANCH=sub/../../outside`; assert failure + no file outside.
- T3: persisted workspace with `pathOnDisk=../outside`, fingerprint+facet registered exactly as the
  product does; GET `/exws/browse/{id}/ws/`; assert status < 500 and the outside marker's content
  is not in the page.
- S1: same persisted workspace; POST `/exws/browse/{id}/cleanup`; assert the outside marker file
  still exists and status < 500.
- S2: `exwsAllocate(diskPoolId: ..., subPath: '../../outside')` + `exws { writeFile }`; assert
  failure + no file outside.

## Coupled must-keep-working behaviour (functional tests)

- T0: nested relative paths (`team/a/1`) and names that merely contain dots (`a..b`, `.cache`).
- T1: a legitimate allocation replayed by a downstream job still reads the upstream file.
- T2: `${JOB_NAME}/${BUILD_NUMBER}` and `team/${BRANCH}` with `BRANCH=feature/x` still work.
- T3: a legitimate persisted workspace is still browsable.
- S1: legitimate cleanup deletes the workspace under the mount and leaves a sibling outside intact.
- S2: a legitimate `subPath` (`nested/dir`) nests under the default path and works.

An over-broad `contains("..")` fix breaks `a..b` and is the `ff-overbroad.patch` functional-fail
check.

## Wrong-fix catalogue mapping

- refuse_all -> `ff-overbroad.patch` (rejects any value containing `..`; the dot-name functional
  test is the positive control)
- crash_as_refusal -> n/a: every security test asserts "blocked", the HTTP ones require status
  < 500, and a crash on legitimate in-bounds use is caught by the functional suite
- wrong_resource -> `wf-wrong-root.patch`
- one_role_or_direction -> `sf-miss-replay.patch`
- reads_only -> `sf-miss-cleanup.patch`
- check_after_adjustment -> `sf-miss-template.patch`
- unlisted_route -> `sf-miss-subpath.patch`
- malformed_identity -> `wf-prefix-only.patch` (only leading `../` rejected; nested traversal missed)
- missing_authority -> n/a: no external authority/role decision in this feature
- adjacent_api -> n/a: the fix adds refusals at entry points; no shared helper's stated behaviour
  changes, and the functional suite pins the public path helpers' behaviour

## Verification log

Local prototype (image `ewm-warm:proto`, same base + warmed Maven repository, offline):

- `injection.patch` applies to the pinned tree; the environment build compiles it.
- `fix.patch` applies on top of the injection and compiles.
- nop (pinned+injected): 8/8 security tests fail for the intended reasons (custom path, template,
  replay, browse, cleanup, sub-path), 8/8 functional tests pass.
- oracle: 16/16 pass.
- Project tests on the pinned+injected tree: CustomWorkspaceTest 9/9, FormValidationUtilTest 10/10
  (with the Java 17 `--add-opens` flags the plugin's own `argLine` omits). ExwsAllocateStepTest
  and ExwsStepTest assert which disk the allocation strategy picks from the host filesystem's free
  space and are unstable in the container, so they are not used as a build gate.
- Check patches (each applied to the injected tree, built offline, both groups run):
  nop and oracle as above; results for each check in the table below.

| check | intended | local result |
|-------|----------|--------------|
| sf-miss-custom | security_fail | security custom-path tests fail, all functional pass |
| sf-miss-template | security_fail | security template tests fail, all functional pass (re-run after the shape fix) |
| sf-miss-replay | security_fail | security replay test fails, all functional pass |
| sf-miss-browse | security_fail | security browse test fails, all functional pass |
| sf-miss-cleanup | security_fail | security cleanup test fails, all functional pass |
| sf-miss-subpath | security_fail | security sub-path test fails, all functional pass |
| wf-prefix-only | security_fail | only the nested custom-path security test fails |
| ff-overbroad | functional_fail | only the dotted-name functional test fails |
| wf-wrong-root | security_fail | the browse and cleanup security tests fail |
| wf-crash | security_fail | the browse and cleanup security tests fail (500 is not a refusal) |
| pass-alt | pass | failed one template test on the first shape (see below); re-run after the fix |
| pass-hardening | pass | 16/16 pass |

The first local run of the whole matrix found a genuine shape bug in my own test: the template
nested case used `test/${BRANCH}` with `sub/../../outside`, whose two `..` segments still land
inside the mount (the `test/` segment absorbs one level), so the build legitimately succeeded on a
containment-only correct fix. The shape was changed to `sub/../../../outside`, which does leave the
mount point; `pass-alt` (containment at the join) then passes it, while the nop and
`sf-miss-template` variants still fail it.

Gate stages (final run on the restored system Docker daemon; an earlier identical run used a
task-private dockerd while the host daemon was wedged by an unrelated bug):

- static: PASSED.
- nop: PASSED -- 8 security tests (all fail on the pinned+injected code) and 8 functional tests
  (all pass), verified on the real environment/verifier images.
- oracle: PASSED -- three identical runs, reward 1.0.
- patches: PASSED -- 12/12 checks as declared: each of the six per-lever `security_fail` patches
  fails only its own security tests with every functional test passing; `wf-prefix-only` fails the
  nested custom-path test only; `wf-wrong-root` and `wf-crash` fail the browse and cleanup
  security tests; `ff-overbroad` fails the dotted-name functional test; `pass-alt` and
  `pass-hardening` both score 1.0. The `blind` patch is produced downstream.

## What I could not verify

- The published fix diff was read directly from the upstream repository (it does have hunks; the
  screener's "no hunks" note was wrong).
- Current upstream master still joins a replayed `pathOnDisk` with no re-check and still has the
  unguarded `ExwsExecution.child`; the browse containment from the fix is present. The two
  injected siblings do not exist upstream by construction.
- The ExwsAllocateStepTest/ExwsStepTest environment sensitivity (disk selection by host free
  space) was observed, not fixed.

