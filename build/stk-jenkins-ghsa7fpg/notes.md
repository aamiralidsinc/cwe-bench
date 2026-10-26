# stk-jenkins-ghsa7fpg — build notes

Start: 2026-10-23T03:02:00Z (the queue restarted this slug cleanly; the previous run's task trees had
been removed by the restart. The surviving gate evidence, check patches and a recovered oracle diff
were re-verified from scratch in this run — nothing from the earlier notes was trusted).

## Scope decision

The design stays inside the advisories' protection (P1): no stored job configuration may cause a job
to start another job unless the user writing the configuration may build that other job. The
configuration-page reconcile loop that rewrites a *neighbouring* project's stored trigger (the
reader's P2/T7) is outside both advisories and is not built on; it is used only as a
must-keep-working value (`FunFormSubmitTest.savesWhileUnconfigurableUpstreamExists`). The reader's
T2 (matrix job kind) is folded into C1 as one more job kind.

## Levers (one line each)

- T1/T3 — C1, how-type / MiMo: the shared submission step must judge the submitted post-build data
  before the stored list is replaced (a read of the current stored list sees the previous entry).
  `core/src/main/java/hudson/model/AbstractProject.java:1746-1798`, ordered against
  `core/src/main/java/hudson/model/Project.java:196-204`. Miss patch `stale_list.patch`.
  Tests: `SecFormSubmitTest` (4); functional `FunFormSubmitTest` (4) + `FunTriggerBuildsTest`.
- T4 — C2, DeepSeek-type uncovered route: a whole-document update of an existing job already checks
  the editor permission but never judges the document; names must be resolved with controller
  authority and then judged as the requesting user, before the document is applied.
  `core/src/main/java/hudson/model/AbstractItem.java:566-597`. Miss patch
  `missing_xml_update_check.patch`. Tests: `SecUpdateXmlTest` (2), `FunUpdateXmlTest`.
- T5 — C3, DeepSeek-type uncovered route: creation from a supplied document checks only the creation
  permission; judge before registering and leave no directory behind on refusal.
  `core/src/main/java/hudson/model/ItemGroupMixIn.java:216-239`. Miss patch
  `missing_create_check.patch`. Tests: `SecCreateFromXmlTest`, `FunCreateFromXmlTest`.
- T6 — C4, DeepSeek-type uncovered route: duplication copies the source's stored definition into a
  new job the copier owns; the copy must be judged before registration.
  `core/src/main/java/hudson/model/ItemGroupMixIn.java:197-214`. Miss patch
  `missing_copy_check.patch`. Tests: `SecCopyTest` (2), `FunCopyTest`.

Concepts: C1 = [T1,T3], C2 = [T4], C3 = [T5], C4 = [T6]. DeepSeek-type: T4/T5/T6. MiMo-type: T3
(T1 both). `score_at_build`: deepseek 0.8006, mimo 0.4338, joint 0.3473.

## History checks

- Pinned `aaf79ed33e60100cb89c122a86b7c66268cf16e9` is the parent of 757bc8a53956 (SECURITY-55);
  36342d71e29e is the same change on another branch and is not an ancestor.
- `upstream_first_fix.patch` = 757bc8a alone, expect security_fail (it fixes only the page route,
  with a user-scoped name lookup).
- `upstream_fix.patch` = 757bc8a plus b6b2a367a797 (SECURITY-109) together, expect security_fail.

## Verified from scratch in this run

- The oracle diff applies cleanly to a pristine pinned worktree.
- All check patches apply cleanly to a pristine pinned worktree.
- The hidden suites drive the real HTTP entry points against a JenkinsRule controller with a
  per-resource permission authority and manual login over loopback:
  - configuration page: `job/<name>/configure` (GET), form Save (POST `configSubmit`);
  - whole document: POST `job/<name>/config.xml`;
  - creation: POST `createItem?name=...` with an XML body;
  - duplication: POST `createItem?name=...&mode=copy&from=...`.
- Full verifier path replayed in a container from the warm image (`/tests/test.sh` as root, BUILD and
  both suites as uid-1000 `agent`, CSRF off in the fixture): pinned -> reward 0.0, 8 passed / 9
  failed, every security test failing with the same statuses the earlier gate recorded (302
  form/copy, 200 xml/create), every functional test passing; oracle -> reward 1.0, 17/17.
- Check patches replayed against the same harness: `stale_list` fails exactly the 4 form security
  tests; `missing_xml_update_check` exactly the 2 whole-document tests; `missing_create_check`
  exactly the creation test; `missing_copy_check` exactly the 2 duplication tests; `crash_as_refusal`
  fails all 9 security tests; `refuse_all` fails 7/8 functional; `wrong_object_self_check` fails 4/8
  functional (it checks the edited job instead of the named one, which refuses every save). Each
  with the other group green.
- The CSRF crumb issuer is switched off in the fixture (`setCrumbIssuer(null)`, the standard
  JenkinsRule idiom); raw POSTs would otherwise be rejected 403 by the crumb filter before the
  product code runs. Login is done manually because the harness's `login()` follows a redirect that
  this controller answers with 404.
- The affected-area project tests (`hudson.tasks.BuildTriggerTest.testBuildTrigger`,
  `testTriggerEvenWhenUnstable`) run at image build time at the pinned commit on JDK 8 / Maven 3.8.8
  from `/opt/m2`, and the image warm-up proves they pass offline.
- No advisory regression test exists at the pinned commit (the fix commits add them).

## Gate

- static (main and control): only the missing `blind` pass patch (written later by the blind-fix
  agent). `stacking/check_stack.py`: conforming (4 concepts, H3a).
- nop: PASSED. 9/9 security tests fail on the pinned code, 8/8 functional pass (trial
  `stk-jenkins-ghsa7fpg-nop-1792727846`).
- oracle: PASSED. 3 strict runs, reward 1.0 each, identical security/functional maps.
- patches: every check was observed with its declared outcome (gate runs unless marked local):
  hardening 1.0 (pass), alternative 1.0 (pass), stale_list 0.5556 (the 4 form security tests fail,
  functional green), missing_xml_update_check 0.7778 (its 2), missing_create_check 0.8889 (its 1),
  missing_copy_check 0.7778 (its 2), crash_as_refusal 0.0 (all 9 security fail, functional green),
  check_after_submit 0.5556 (the 4 form tests), upstream_first_fix 0.4444 and upstream_fix 0.4444
  (the same 5 non-form tests fail: both xml, create, both copy), wrong_object_self_check
  functional_fail (4/8 functional fail, gate), refuse_all functional_fail 7/8 (local replay).
  wrong_configure_permission was not observed by a gate run in this session; it is declared
  functional_fail and the pipeline's full patches rerun covers it.
  Two Harbor environment-provider flakes (`network_mode='no-network' is not supported by
  EnvironmentType.DOCKER`, classified infra, at different checks) forced the stage to be completed
  in split runs with a trimmed manifest, restored immediately afterwards; the last split run
  PASSED. No check ever mismatched its declaration.

## Could not verify / guesses

- Whether upstream ever added save-time checks to the three uncovered writers; current master shows
  none (runtime enforcement relies on the build's authentication), so the register says
  `present_in_latest = no`, a read-only look at master rather than a historical audit.
- The two target models were not run (the build prompt forbids it).

## Scope note

Outside the advisories' protection (not built on): the configuration-page reconcile loop rewrites a
neighbouring project's stored trigger without a configure check on that project. It is exercised
only as a must-keep-working value.

## Tooling

`stacking/check_stack.py` wants the recall entries to say `expect: security_fail` (the addendum's
prose says `fail`); `builder/gate.py` is the executor of record and joins `patch` names onto
`build/<slug>/checks/`. The manifest uses bare file names and `security_fail` for both recall
patches.

## Audit fix 2026-10-25 (AUDIT-FIX-20261024 v3, post-trial test-fault)

The post-trial audit found a harness defect, not a task defect: `enableAcl()` installed
`j.createDummySecurityRealm()` (an anonymous `JenkinsRule` subclass holding the rule instance) and
a `BtAuthz` that keyed its grants by live `Job` objects in an `IdentityHashMap`. Any code path that
calls `Jenkins.save()` with ACLs on therefore failed inside XStream. A correct fix that refuses an
unauthorised copy by rolling the half-created item back (`Item.delete()` -> `Jenkins.onDeleted` ->
`Jenkins.save()`) surfaced as HTTP 500, failing `SecCopyTest` for the right fix.

- `tests/harness/BtTest.java`: `enableAcl()` now installs a named
  `HudsonPrivateSecurityRealm(false, false, null)` with the same two accounts (`attacker`, `admin`,
  password = name, the same credentials the harness logs in with) and the same root grants
  (`admin`: administer; `attacker`: read + job create). Same users, same permissions, same refusal
  semantics; the realm is the product's own and persists.
- `tests/harness/BtAuthz.java`: per-job grants are keyed by `Job.getFullName()` instead of the live
  `Job` object, so the authority serialises with no live item reachable from it. Same ACL decisions.
- `tests/functional/FunFixtureSaveTest.java` (new): after `enableAcl()` and per-job grants, calls
  `j.jenkins.save()` and asserts the configured job is still there. It passes on the pinned code and
  on every reference/alternative/rollback fix; on the old fixture it fails with "Failed to serialize
  jenkins.model.Jenkins#securityRealm", so it pins the fixture property the audit asked for.
- Control: the same two harness files were copied to
  `tasks/stk-jenkins-ghsa7fpg-control/tests/harness/`. No other control file changed.
- Nothing else changed: instruction.md, solution/fix.patch, the security tests' assertions and the
  manifest traps are untouched.

Local replay before the gate (prebuilt pinned / oracle / control workspaces, verifier-image
classpath, hidden suites compiled and run exactly as `run_group.sh` does):
- pinned: 9/9 security fail (same 302/302/200 statuses as the earlier gate), 9/9 functional pass
  including the new self-check;
- oracle: 18/18 pass (9 security, 9 functional);
- a deliberately constructed correct fix that refuses the copy *after* creation and rolls back
  through `Item.delete()`: with the old fixture the two copy tests fail with 500 (the audit's exact
  symptom) and the self-check fails with the serialisation error; with the new fixture all 18 pass;
- control: oracle 4/4 security + 5/5 functional, pinned 0/4 + 5/5.

## Fairfix 2026-10-24 (AUDIT-FIX-20261024 Required 1, instruction scope)

- `instruction.md`: the property is now scoped to the job the write is about — "a configuration write
  must not leave the written job configured to start another job that the user making the write is
  not allowed to build." The earlier wording ("must not result in a job configured to start...")
  read literally also forbade `FunFormSubmitTest.savesWhileUnconfigurableUpstreamExists`, where a
  pre-existing upstream job already triggers the saved job. No identifier, route or value added;
  leak terms clean; listing check re-run by the launcher.
- `manifest.json`: declared the pipeline's `blind.patch` (`kind: blind`, `expect: pass`) so the
  static stage is green; the file is produced separately by the blind-fix run.
- `FAIRNESS.md`: added the stacked-task "Stacking checks" section (S1-S7 per concept).
- Gate after the change: static PASSED, nop PASSED, oracle PASSED (3 runs, 1.0), patches PASSED.
