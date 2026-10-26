# atlantis-ds — build notes

- Start: 2026-10-24T02:43:04Z
- End: 2026-10-24T03:55:00Z (approx.; final gate stages completed at 03:52Z)
- Advisory: GHSA-26W5-6G95-GJ28 / CVE-2026-64679 / GO-2026-6273 (runatlantis/atlantis)
- Pinned: 06b90ef7850c2075f2d1009c593f90c7ebcd8b9c; published fix: ea4e4ceebf8b387d015fff7ed8a7fcca33279afe
- Track: injected; pattern: A. The advisory's own CWE-22/CWE-73 protection (external control of a
  file path into directory delete/create under DATA_DIR) is the scope; the two injected siblings are
  the same class of value reaching the same protected outcome.

## Security property (one)

No repository identity, workspace name, project name or project directory supplied by a client — in
a request, in repository configuration, or in state saved by an earlier operation — may make the
server create, modify or delete anything outside the directory allocated at that level (managed
data area / pull request directory / workspace checkout), however the value is spelled and at every
point while a request is handled. Legitimate multi-component owners, the checkout root as the
default project directory, nested project directories and ordinary workspaces keep working.

## Levers (one line each)

- T1 (report target, where-type): repository identity and workspace in the working-directory path
  builders (`server/events/working_dir.go:794-835`) — Delete and DeleteForWorkspace `RemoveAll` an
  unchecked path; GetPullDir/GetWorkingDir expose it. Reason to keep going: the existing
  `validateCloneDir` bounds only to DATA_DIR/repos and only Clone/MergeAgain use it, so a fix that
  reuses it still leaves the per-pull and per-workspace bound open.
- T2 (how-type, main): `ctx.RepoRelDir` in the six command runners
  (`server/events/project_command_runner.go:459,704,752,811,837,883`) — a value the API accepts
  unvalidated, spelled with a leading or embedded `..`; the config cleaner `filepath.Clean("./"+dir)`
  preserves it, so "project configuration is normalised" is the reason to dismiss it.
- T3 (how-type): plan-file deletion fed by state saved earlier
  (`server/events/working_dir.go:849` from `delete_lock_command.go:39,63`) — the check's data comes
  from the lock store, so a request-field fix never sees it.
- S1 (injected, how-type, different package): plan-output artefact directory named from the project
  name (`server/core/runtime/plan_step_runner.go`, `writePlanOutputSnapshot`); the config schema's
  URL-safety check replaces `/` before comparing, so a path fragment passes. Reason to dismiss:
  "the project name is already validated as URL-safe".
- S2 (injected, how-type, ordering): stale-plan removal while the plan command's context is built
  (`server/events/project_artifacts.go`, called from `project_command_context_builder.go`); it runs
  before the runner check that validates the same directory. Reason to dismiss: "the runner rejects
  a traversing project directory now".

## Injected sibling candidates searched (full list) and why the two picks won

1. `pending_plan_finder.go` workspace fast path / weakening `workspaceRepoDir` — rejected: the
   finder's workspace comes from `os.ReadDir` (no separators), and no real caller supplies an
   unvalidated workspace, so the route is not reachable through a product path.
2. `plan_step_runner.go` `env/<workspace>.tfvars` write/delete — rejected: the workspace is already
   confined by the working-directory lookup before any step runner runs, so it cannot escape.
3. `policy/conftest_client.go` policy-result write — rejected: `workdir` is the checked project
   path and the filename embeds a confined workspace and a `/`-sanitised project name.
4. `project_command_context_builder.go` / `project_artifacts.go` stale-plan removal — CHOSEN (S2):
   runs before the runner's check (ordering), a different file, the published fix never touches it.
5. `plan_step_runner.go` project-name artefact directory — CHOSEN (S1): a project name that passes
   the URL-safety validator but is a path fragment; different package from the report, executes
   inside a real plan step.
6. `delete_lock_command.go` inline workspace-directory cleanup (needs a DataDir field) — rejected:
   duplicates T3's persisted-state concept, and would need configuration wiring.
7. `pull_closed_executor.go` per-project artefact cleanup — rejected: needs a data-dir field and
   duplicates the delete path.
8. `project_finder.go` auto-discovery joins — rejected: read-only, not a delete/create sink.
9. Terraform/conftest version caches (`key.Original()`) — rejected: go-version rejects path
   fragments, so the value cannot reach the path.
10. tfclient rc-file / binary-dir writes — rejected: no externally supplied path fragment.

Picks 4 and 5 are the only candidates that are (a) reachable through a normal product flow,
(b) produce a real create/delete outside the managed directory on the pinned tree, and (c) sit in
code the published fix never touches.

## Verified

- Pinned + injection: 15/15 security tests fail (foreign directory removed, foreign plan removed,
  a step executed outside the workspace, an outside artefact created) and 10/10 functional tests
  pass. Run locally in a clean worktree and through the gate's `nop` stage.
- Published fix minus tests + the S1/S2 containment: 15/15 security and 10/10 functional pass.
- Project tests (pristine copies): `server/events/models`, `server/core/config/raw`, events
  `TestPendingPlanFinder` pass on pinned and on the oracle.
- Every checks/ patch was run locally against both suites; each sf-* leaves at least one security
  failure with all functional passing; both ff-* fail functional; both pass-* pass everything.
- The config schema accepts a project name of the S1 shape (validated directly).
- Entry points confirmed offline: FileWorkspace methods, the six `DefaultProjectCommandRunner`
  methods, `DefaultDeleteLockCommand`, `DefaultProjectCommandContextBuilder` and the real
  `runtime.NewPlanStepRunner` (fake terraform executor). No server, network or git is needed at
  test time.

## Could not verify

- The two target-model trials (not run here; the gate is the only proof available to the builder).
- `present_in_latest` for the two injected siblings: they are our code, not upstream.
- The API route is gated by `ATLANTIS_API_SECRET`; the tests therefore drive the builder/runner the
  API controller calls rather than an HTTP request (the API's repo allowlist and clone would need
  network). The screener's own dismissal reason for the API route ("callers count as trusted
  operators") is what T2's tests are designed to defeat.
- The advisory's other value shapes (`/etc`, backslash, embedded `/` in a workspace) are rejected
  by the config/comment validators in the published fix, but they are not escapes on Linux at the
  sink; the tests therefore cover escaping `..` shapes only, so a valid sink-level fix is not
  penalised for accepting a single-component oddity.

## Outside the scope, noted (not built on)

- `server/events/project_command_context_builder.go` reads `.tf` files for version detection before
  the runner check (read-only, different impact); `server/events/comment_parser.go` rejects a
  leading `~` in workspaces for shell-safety reasons — a different protection.

## Gate results (run one stage at a time)

- static: PASS (after moving the S2 helper into a new file so the injection patch shares no import
  lines with the tests).
- nop: PASS — 15/15 security tests fail on the pinned+injected tree, 478/478 functional pass.
- oracle: PASS — 3 runs, reward 1.0 each, identical per-test results.
- patches: PASS — all 11 declared checks behave as declared (sf-miss-working-dir 0.7333,
  sf-miss-runner 0.5333, sf-miss-deleteplan 0.8667, sf-miss-plan-artifact 0.9333,
  sf-miss-context-cleanup 0.9333, sf-leading-dotdot-only 0.8, sf-reads-only 0.1333,
  ff-refuse-all 0.0, ff-overbroad 0.0, pass-hardening 1.0, pass-alt 1.0).
- One patches-stage attempt aborted with an infrastructure failure (`/tmp/containerd-mount...:
  no space left on device`, tmpfs exhausted by concurrent builds); the retry passed unchanged. No
  task file was modified in response.

## Register

Two rows appended to `build/audit/uncovered-routes.tsv` for the injected siblings (real_upstream=no,
in_current_scope=yes (injected), disclosure_status=pending client decision).
