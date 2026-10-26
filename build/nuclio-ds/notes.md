# nuclio-ds — build notes

- Start: 2026-10-24T05:18Z
- End: 2026-10-24T09:20Z

## Task
GHSA-M8XG-8XG9-MXHM / CVE-2026-45730 / GO-2026-5499, nuclio/nuclio, CWE-862 (missing
authorization on project write operations). Pattern A+B, track INJECTED. Pinned
a1bbd608 (verified as the parent of fix 1915cd2). The published fix adds the policy
query to the kube platform's project create / update / delete and passes the caller
identity into the dashboard's update / delete options.

## Seam
Go unit tests driving the real platform write API that the dashboard handlers and the
CLI call: `kube.Platform` and `local.Platform` CreateProject / UpdateProject /
DeleteProject, the import create (`AbstractProject.CreateAndWait`), and the two injected
administration operations. The tests build the real platform with a policy stub that
answers per resource and verb, and with a recording/mocked storage client, so "refused"
is observed as a client error AND the absence of the storage call. Offline; no cluster,
no Docker daemon, no policy server. Toolchain golang 1.26.3, `-tags test_unit`.

## Levers (each verified: fails on pinned+inject, passes on oracle)
- kube_project_writes (A, published): create / update / delete never query the policy
  service. The published update / delete query only refuses when the caller's options
  ask for it, so a caller that does not ask proceeds after a denial. Dismiss: none (the
  reported site) — the second half is the shape. sec_miss_effective.
- local_backend_project_writes (B, real): the other backend's three project writes never
  had a decision, although it checks the service for function creation. Dismiss: the
  docker/dev single-user deployment; the advisory is about the kubernetes one.
  sec_miss_local.
- rename_authorises_wrong_project (injected, how-type): the rename operation asks about
  the project it is renaming and then creates the project under the new name; the object
  that is written is never the object that was authorised. Dismiss: a rename only touches
  a project the caller can already update, and the new name is the same project.
  sec_miss_rename.
- status_update_no_decision (injected, how-type): an operational status write reaches the
  storage client with no decision while the ordinary update path is being guarded.
  Dismiss: status-only, not a configuration write. sec_miss_status.

## Injected-sibling candidate list (all candidates found, and why the picks won)
1. kube project rename (new administration operation) — PICKED: how-type (wrong object),
   far from the report, plausible dismissal, testable through the platform API.
2. kube project status update (new administration operation) — PICKED: a project write
   that reads as "not really a write", different dismissal from (1), separate operation.
3. Project import create with no caller identity in its options — real upstream gap, but
   the published platform-level create check already runs on that path; what remains is a
   handler-level identity-propagation issue that cannot be exercised without a real
   dashboard + authenticated session. Fixed in the oracle's hardening patch; not scored.
4. Delete-strategy variants (`check`, `restricted`, `cascading`) — they reach the same
   platform delete method already covered; `check` has no side effect. Dismissed.
5. nuctl create / delete project (no permission options) — same platform methods; only
   repeats the "caller must not be able to waive the refusal" shape already in lever 1.
   Dismissed to avoid a second route of one concept.
6. Leader synchroniser writes through the internal project client — authorised by the
   leader's own decision and required to keep working; it is the coupled must-keep-working
   behaviour, not a lever. Dismissed.
7. Dashboard labels / annotations patch operation — considered; overlaps with (2) and is
   less natural than a status toggle. Rejected.
8. Project owner transfer — considered; overlaps with (1)/(2) and adds no new mechanism.
   Rejected.
9. Auto-create of a missing project during function deployment — considered; plausible
   feature but requires invasive wiring into function creation, and the sibling would be
   far harder to reach in a deterministic test. Rejected.

## Oracle
Every project-writing site queries the policy service for the action being performed on
the project actually written and raises the refusal itself before any storage change:
kube create / update / delete, local create / update / delete, rename (update on the old
name AND create on the new name), status update. The dashboard update / delete handlers
pass the caller identity (as published). The import route also gets the caller identity
in the hardening patch. `fix.patch` = injected -> oracle, source only.

## Verified
- nop (pinned+inject): 10 security FAIL, 9 functional PASS (each hidden suite run in the
  two affected packages).
- oracle: all 19 hidden tests PASS; the project's own suites for both packages PASS.
- alt_fix (shared-helper design, identity derived from the session) and hardening
  (oracle + import identity + empty-name guard): all PASS.
- sec_miss_effective / sec_miss_local / sec_miss_rename / sec_miss_status /
  sec_miss_identity / sec_only_create / sec_check_after_write each fail only their own
  lever's security tests and leave every functional test passing.
- func_overbroad (reject empty caller identity) fails functional tests only.
- Every check patch applies cleanly with `patch -p1` to the injected tree.
- The pinned commit does not contain the advisory's regression tests: the fix commit adds
  them to pkg/dashboard/test/server_test.go and pkg/platform/kube/platform_test.go.
- instruction.md: no advisory id, no commit sha, no file/function/field name, 393 words.

## Gate result (2026-10-24, one stage at a time)
- static: PASSED (only the downstream blind patch and FAIRNESS.md are outstanding).
- nop: PASSED — 10 security tests, all failing on the pinned+injected tree; 165 functional
  tests (9 hidden + 156 from the kube platform's own suite), all passing.
- oracle: PASSED — 3 runs, reward 1.0 each, identical security/functional results.
- patches: PASSED — sec_miss_effective 0.7 / sec_miss_local 0.7 / sec_miss_rename 0.9 /
  sec_miss_status 0.9 / sec_miss_identity 0.9 / sec_only_create 0.3 / sec_check_after_write
  0.7 (each security-only failures, functional all pass); func_overbroad 0.0 (functional
  fails only); hardening 1.0; alt_fix 1.0.
- One iteration was needed: the first sec_miss_identity patch cleared the caller identity in
  every check block in the file, including the function-event checks, which broke the project
  suite; it now clears it only in the project-write blocks.

## Could not verify / notes
- How the real policy service treats an empty caller-identity list; the stub answers per
  resource and verb, and a deployment with no policy service (the product's default) is
  defined to allow.
- The current upstream main has evolved (a shared check helper that is a no-op unless the
  deployment's auth kind is iguazio-v4); `present_in_latest` in the register reflects a
  read-only look at HEAD, not a behavioural re-verification.
- The dashboard's own test suite is not part of the hidden functional group: two of its
  project tests compare the exact options the handler passes (the published fix updates
  them) and the task deliberately changes that protocol. The kube platform's own
  behavioural suite does run; the local platform's own suite is excluded because its setup
  starts a real Docker storage container, which the offline verifier has no daemon for
  (the hidden local behavioural tests build the platform directly and need none).
- The local deployment is not normally run with a non-default policy
  service; the general property covers it and the route is real, unmodified upstream code.
