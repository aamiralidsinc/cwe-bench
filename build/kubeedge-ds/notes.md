# kubeedge-ds — build notes

Started: 2026-10-24T04:45Z (pipeline)
Repo: kubeedge/kubeedge @ ba0f2c67146c0c9a34b2a0be2900011f96680a08 (vulnerable)
Fixes: 552af457 (release-1.22), 657b745b, b72db7f8 (same change on other release branches)
Advisory family: OS command injection (CWE-78) — cloud-supplied node-operations job fields
interpolated into `bash -c` on the edge.

## What the published fix does (verified from 552af457~1..552af457)

- `edge/pkg/taskmanager/actions/nodeupgradejob.go`: validate Version/Image in `checkItems`
  and in `upgrade`; replace the `bash -c` string builder with `exec.Command("keadm", args...)`
  plus an opened `/tmp/keadm.log`.
- `edge/pkg/taskmanager/v1alpha1/taskexecutor/node_upgrade.go`: same argv conversion for the
  legacy executor (`nohup keadm ...` with Start/Release to stay detached).
- `cloud/pkg/admissioncontroller/admit_nodeupgradejob.go`: v1alpha1 webhook validates version
  and image with new helpers.
- `pkg/util/validation/validation.go`: `ValidateVersion`, `ValidateImageRepo`.

## Candidate sibling sites / routes (all shell sinks reachable from cloud->edge job data)

1. `edge/pkg/taskmanager/actions/nodeupgradejob.go:250` — v1alpha2 Upgrade, Version/Image. Landing; fix touches it.
2. `edge/pkg/taskmanager/actions/nodeupgradejob.go:134` — v1alpha2 Check. Fix adds validation here (no shell sink itself).
3. `edge/pkg/taskmanager/v1alpha1/taskexecutor/node_upgrade.go:200` — v1alpha1 upgrade, IDs/Version/Image/ConfigFile. Pattern A far site; fix touches it.
4. `edge/pkg/taskmanager/v1alpha1/taskexecutor/node_rollback.go:65` — real, unmodified; shells UpgradeID (API-name constrained) and the current version. Fix never touches it.
5. `edge/pkg/taskmanager/actions/configupdatejob.go:106` — real, unmodified; UpdateFields keys+values joined into `keadm config-update --set` and run through bash. Fix never touches it.
6. `edge/pkg/metamanager/metaserver/handlerfactory/extend_confirm_upgrade.go` + `dao/dbclient/upgrade_v2.go` — producer/reload route into (1): preRun saves the spec, confirm reloads it and starts at BackUp, skipping Check. Real, unmodified; fix never touches them.
7. `pkg/containers/container_runtime.go` copyResourcesCmd — `/bin/sh -c`, but container/host paths are package constants and images go to the CRI, not the shell. Not reachable.
8. `keadm/.../util/common_others.go` execs.NewCommand(fmt.Sprintf(...)) — local operator/CLI input, not a cloud job. Out of scope (noted).
9. `edge/pkg/taskmanager/actions/imageprepulljob.go` — no shell at pin; images go to the CRI.
10. `edge/pkg/taskmanager/v1alpha1/taskexecutor/image_prepull.go` — no shell at pin.
11. `edge/pkg/taskmanager/actions/nodeupgradejob.go:264` (rollback) and `configupdatejob.go:80,121` — fixed command strings, no job value.

## Injected siblings: all candidates considered, and the picks

- (pick) (4) rollback cleanup: inject a pre-rollback `rm -rf` of the failed upgrade directory derived
  from the request Version, in the same bash-fmt style as the file. Reachable via the executor's
  rolling-back state, which the cloud drives after a failed upgrade. Dismissal: legacy
  failure-recovery branch; a directory cleanup reads as path handling, and the file is not in the report.
- (pick) (9) pre-pull presence probe: inject a `crictl inspecti <image>` local-cache probe over the
  submitted image list in the pre-pull Check action. Reachable via the pre-pull runner's Check action.
  Dismissal: a different job kind; image references look like identifiers, and the probe is read-only.
- (rejected) v1alpha1 rollback with only UpgradeID/HistoryID: real code, but upstream those are an
  API-server-validated object name and a UUID; a security test on them would not be fair.
- (rejected) v1alpha2 rollback with the job name: same API-name constraint.
- (rejected) a normaliser/rewrite after the check: the only natural homes are the functions the
  published fix rewrites, and the reference argv fix would auto-cover it, so it adds no scope difficulty.
- (rejected) keadm-side shell step with ToVersion: needs a real keadm + container runtime and
  privileged upgrade flow; not reachable deterministically offline.
- (rejected) v1alpha2 admission webhook: no shell execution; a cloud-side denial is not required by
  a property about what the node executes, so an edge-only correct fix would fail unfairly.

Picks beat the rejected ones because they are real handlers on the same cloud->edge channel, in files
the published fix never touches, and their values are genuinely submitter-controlled (Version, Images),
unlike the rejected identity fields.

## Levers (each has a different reason a solver skips it)

- L1 (main, HOW — producer off the check's path): the confirmation/reload route. `preRun` stores the
  spec before Check runs; the confirm endpoint reloads the stored spec and starts the flow at BackUp,
  so Upgrade runs without Check. `checkItems` never calls the store. A fix that validates only the
  visible check step leaves this open. Coupled functional: a legitimate confirmed spec still upgrades
  with the right argv.
- L2 (Pattern B, real): `configupdatejob.go` UpdateFields keys and values reach the same shell sink;
  the fix never touches it. Dismissal: a different CRD/feature (config update, not upgrade) and values
  look like plain config text.
- L3 (Pattern A far site): the v1alpha1 executor builds `nohup keadm ... <request fields>` through
  bash. Dismissal: deprecated legacy API; the advisory says v1alpha2; its fields are constrained
  upstream (semver webhook, object name, UUID).
- L4 (injected, L4 = pre-pull probe): a submitted image list reaches `crictl inspecti` through a shell.
  Dismissal: pre-pull is another feature; image references look like identifiers; the probe is read-only.
- L5 (injected, rollback cleanup): the request Version becomes part of an `rm -rf` shell line during
  failure recovery. Dismissal: recovery branch of the legacy API; a path cleanup.
- Coupled must-keep-working (HOW): legitimate image references with registry:port, tag or digest, an
  empty image, prerelease versions, multi-pair config updates, a detached logged v1alpha1 upgrade, and
  the probe/cleanup behaviour itself. An over-broad check (reject ':'/'@', require an image, drop the
  probe) fails functional tests.

## Security property (stated once, general)

No value a job submitter supplies may be interpreted by a shell on the edge; every such value must
reach the tool as literal data, however it arrives (including values the node stored earlier), and
must never start a second command, substitution, redirection or pipeline. Everything that works today
keeps working.

## Tests

Security (through the real action handlers/executor/runner; marker = file in a per-test temp dir;
assert marker absent, never a status):
- S1 v1alpha2 Upgrade Version `;`
- S2 v1alpha2 Upgrade Image `$( )`
- S3 stored+reloaded spec -> Upgrade action, Version backticks (L1)
- S4/S5 config update value `;` and key `$( )` (L2)
- S6 v1alpha1 executor Version `;`, S7 Image `$( )` (L3)
- S8 pre-pull image `` ` `` (L4)
- S9 rollback Version `;` (L5)

Functional:
- F1 v1alpha2 Upgrade legit argv (version+image)
- F2 empty image + prerelease version
- F3 digest image
- F4 confirmed stored legitimate spec -> correct argv (L1 coupled)
- F5 config update several pairs -> single --set value (L2 coupled)
- F6 v1alpha1 upgrade detached + output in /tmp/keadm.log (L3 coupled)
- F7 pre-pull probe still runs for legitimate images (L4 coupled)
- F8 rollback cleanup still removes the legitimate failed-upgrade dir (L5 coupled)
- Plus the project's own tests for pkg/util/validation and pkg/nodetask/actionflow (pristine copies).

## Notes / unverified at plan time

- /tmp is the shared host; tests use per-test temp dirs and unique tokens, and packages run with -p 1.
- CGO is required for the sqlite DAO used by the runner/save-reload test; gcc is in the Go base image.
- The repo's vendor tree needs GOWORK=off (go.work + vendor mismatch under modern Go); the image and
  the verifier set it.
- The pinned project tests in edge/pkg/taskmanager/actions assert the vulnerable bash command and are
  updated by the upstream fix; they are excluded from grading (verified passing at pin at image build)
  and the two hidden-test packages are staged with only the hidden files.

## Build log (running)

- 05:13Z first nop run: `EnvironmentStartTimeoutError` at 1800 s. The environment image's
  build-time project-test step ran the gomonkey suite with `-gcflags=all=-l`, which recompiles
  the dependency tree; under the shared VM load (load average >100) it did not finish. Fix:
  the environment image now only proves the toolchain on the tiny validation/actionflow
  packages; the verifier image warms exactly the packages the graded suites compile (no
  `-gcflags`, no cloud admission tree, no project-test compile). Raised the Harbor build
  timeouts to 3600 s ([environment] and [verifier.environment]) and the verifier phase to
  3600 s; test.sh builds with BUILD_TIMEOUT=900, TEST_TIMEOUT=600, SUITE_TIMEOUT=1500.
- Full project tests for the affected area were verified at the pinned+injected commit in a
  scratch checkout with `go test -count=1 -gcflags=all=-l ...` (validation, actionflow,
  admissioncontroller, actions) — all pass; the actions suite is build-time proof only because
  the upstream fix rewrites the tests that assert the vulnerable command line.
- 08:13Z nop PASS: on the pinned+injected tree, 9/9 security tests fail (every route executes the
  marker) and 24/24 functional tests pass (9 hidden functional cases + the pristine project suites
  for pkg/util/validation and pkg/nodetask/actionflow).
- The nine wrong-fix patches were re-verified locally against the shipped test files, each exactly
  as declared: sec_miss_confirm 3 security failures / 0 functional; sec_miss_config 2/0;
  sec_miss_legacy 2/0; sec_miss_prepull 1/0; sec_miss_rollback 1/0; func_overbroad 0/3;
  refuse_all 0/9; hardening 0/0; alt_fix 0/0.
- 08:49Z oracle PASS: 3/3 runs reward 1.0, 33/33 tests passing in each (9 security + 24
  functional), identical results across the runs. The patches stage is running next.
- 09:11Z patches PASS: all nine declared check patches matched in the separate verifier —
  sec_miss_confirm 3 security failures / 0 functional; sec_miss_config 2/0; sec_miss_legacy 2/0;
  sec_miss_prepull 1/0; sec_miss_rollback 1/0; func_overbroad 0/3 (the three legitimate image/version
  shape cases); refuse_all 0/9; hardening 1.0; alt_fix 1.0.

## Final state (end 2026-10-24T09:11Z)

Gate: static PASS; nop PASS (9 security fail / 24 functional pass on the vulnerable tree); oracle
PASS (3/3 at 1.0, 33/33 each, identical); patches PASS (all 9 declared checks behave as declared).
Status in build/kubeedge-ds/manifest.json is "built".

Not verified / guesses:
- No target-model trials were run by me (the brief forbids it); the bar (DeepSeek and MiMo failing
  all three) is a later judgement.
- The config-update route is real upstream code the published fix never touches; current upstream
  master builds an argv command for it, so the route is no longer vulnerable there. I inferred it
  was fixed after this advisory rather than tracing the fixing commit.
- The two injected siblings are synthetic maintainer-style code (registered in
  build/audit/uncovered-routes.tsv); "present in latest" is n/a for both.
- Harbor behaviour under extreme host load was the only instability seen; the first nop runs hit
  image-build timeouts and were rerun after the host Docker fix, with no change to the task's
  correctness settings (only build scope/timeouts).
- The latent reportActionStatus nil dereference means a fix that validates in the runner's pre-run
  hook or the serializer panics instead of refusing; the instruction requires an error refusal, so
  that is treated as a judgement failure, not a harness fault.

Outside scope, one line: keadm's own installer utilities build `bash -c` strings from local
operator/CLI input (keadm/cmd/keadm/app/cmd/util/common_others.go:161-195), and the legacy rollback
command's UpgradeID is the API-server-validated object name; neither is built on.
