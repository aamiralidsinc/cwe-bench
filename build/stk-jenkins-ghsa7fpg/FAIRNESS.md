# stk-jenkins-ghsa7fpg — fairness record

The review of record for this revision is `build/stk-jenkins-ghsa7fpg/AUDIT-FIX-20261024.md` v3
(post-trial audit, DeepSeek r2: test-fault). It found that the shared fixture could not be
serialised, so a correct fix that rolls a refused copy back (`Jenkins.onDeleted` -> `Jenkins.save()`)
was reported as HTTP 500. `tests/harness/BtTest.java` now installs the product's own
`HudsonPrivateSecurityRealm` with the same two accounts and root grants, `tests/harness/BtAuthz.java`
keys per-job grants by full name (no live item reachable from it), and the new
`FunFixtureSaveTest.savesControllerStateWithAclAndGrants` pins the property by calling
`j.jenkins.save()` after the grants. Same users, same permissions, same refusal semantics; the
control's harness received the same two files. Instruction, reference and security assertions are
unchanged. Local replay: pinned 9/9 security fail + 9/9 functional pass; oracle 18/18; a correct fix
that refuses the copy after creation and rolls back through `Item.delete()` 18/18 with the new
fixture (it reproduced the 500 with the old one).

## Stacking checks

Concepts from `manifest.stacking`: **C1** = [T1, T3] (configuration-page submission, incl. the
ordering shape), **C2** = [T4] (whole-document update of an existing job), **C3** = [T5] (creation
from a supplied document), **C4** = [T6] (duplication). `checks/upstream_first_fix.patch` is the
first fix of the earlier advisory (SECURITY-55, 757bc8a53956). No `trial_summary.md` exists; the
post-trial audit is the artifact reviewed here.

| Check | Concept | Finding | Gate effect |
|---|---|---|---|
| S1 | C1 | Coupled values: `savesWithoutTrigger` (empty), `addsBuildableTarget`, `matrixAddsBuildableTarget` (a job the editor may build), `savesWhileUnconfigurableUpstreamExists` (an upstream job already triggers the written job), `storedTriggerBuildsDownstream` (build-time trigger). Instruction clause: "Everything that works today keeps working." The security rule now reads "a configuration write must not leave the written job configured to start another job that the user making the write is not allowed to build": in each of these the written job names nothing or a job the writer may build. No contradiction. | pass |
| S1 | C2 | Coupled value: `xmlUpdateToBuildableTarget` — the written job is left naming a job the writer may build. Covered by "Everything that works today keeps working."; the rule permits it. | pass |
| S1 | C3 | Coupled value: `createWithBuildableTarget` — the written (new) job names a job the writer may build. Covered by the keep-working sentence; the rule permits it. | pass |
| S1 | C4 | Coupled value: `copyWithBuildableTrigger` — the copied (written) job names a job the copier may build. Covered by the keep-working sentence; the rule permits it. | pass |
| S2 | C1 | Refused shapes: a named job with read but not build (visible, unbuildable), a named job the writer cannot see, a list mixing a buildable and an unbuildable name, and the same shape on a matrix job. The instruction's legitimate set is a target the writing user is allowed to build; every refused shape lies outside it. | pass |
| S2 | C2 | Refused shapes: a whole-document write naming a job the writer cannot see, and one naming a visible-but-unbuildable job. Outside the stated legitimate set (targets the writer may build). | pass |
| S2 | C3 | Refused shape: a supplied document naming a job the writer cannot see. Outside the stated legitimate set. | pass |
| S2 | C4 | Refused shapes: a duplicated source whose stored target is invisible, and one whose target is visible but unbuildable. Outside the stated legitimate set. | pass |
| S3 | C1 | Fixture states are legitimate: configured jobs, an editor holding read+configure on the written job, a real controller permission matrix, and a target that exists and is readable or hidden. The harness drives the real configuration page (GET) and its Save (POST) over loopback with the product's own form field and stored trigger. | pass |
| S3 | C2 | Fixture states are legitimate (editor holds configure on the written job). The harness POSTs a configuration document to the real route; a guard placed at the route, at the document load, or at the trigger check all satisfy it. | pass |
| S3 | C3 | Fixture states are legitimate (the creator holds the create permission; the document is the product's own serialization of a real job). The harness POSTs the real creation request with an XML body. | pass |
| S3 | C4 | Fixture states are legitimate (the copier holds read on the source and the create permission). The harness POSTs the real duplication request. | pass |
| S3 | all (C1–C4) | The shared fixture is itself persistable, so a refusal implemented as a rollback of a half-created item is not reported as a server error. `enableAcl()` installs the product's own `HudsonPrivateSecurityRealm` with the same two accounts and the same root grants; `BtAuthz` keys per-job grants by full name; `FunFixtureSaveTest.savesControllerStateWithAclAndGrants` calls `j.jenkins.save()` after those grants. It asserts no product rule (so no concept can mask it) and passes on pinned and on the reference, alternative and rollback fixes. | pass |
| S4 | C1 | On the pinned code the four form security tests fail through the form route (302, config unchanged); `stale_list.patch` leaves exactly those four failing with functional green. A correct guard on the submitted publisher data passes regardless of the other concepts. | pass |
| S4 | C2 | On the pinned code both whole-document tests fail through their own route (200, config unchanged); `missing_xml_update_check.patch` leaves exactly those two failing. Independent of C1, C3, C4. | pass |
| S4 | C3 | On the pinned code the creation test fails through its own route; `missing_create_check.patch` leaves exactly it failing. Independent of the other concepts. | pass |
| S4 | C4 | On the pinned code both duplication tests fail through their own route; `missing_copy_check.patch` leaves exactly those two failing. Independent of the other concepts. | pass |
| S5 | C1..C4 | H3a: `upstream_first_fix.patch` adds the judgement only to the configuration-page submission. Read literally, the property still requires refusing a whole-document update, a creation and a duplication that leave the written job configured to start a job the writer may not build — all three remain open, so the first fix violates the property as written. Recorded outcome: `security_fail` at 0.4444 (the five non-form security tests fail). | pass |
| S6 | C1 | No field, function or setting name must be guessed: assertions read the job's own stored trigger through the product, and the protected object is named in product terms ("job", "the written job"). The refusal contract is stated ("A refusal is a client error and has no effect"). | pass |
| S6 | C2 | Same contract: the request is a configuration write of the written job; the test only requires the stated client-error refusal and an unchanged stored configuration. | pass |
| S6 | C3 | Same contract: the written job is the job the configuration write produces; only the stated refusal and the absence of a registered job are required. | pass |
| S6 | C4 | Same contract: the written job is the duplicated job; only the stated refusal and the absence of a registered job are required. | pass |
| S7 | C1 | No `trial_summary.md` exists. The post-trial audit reports a DeepSeek r2 run whose only failures were `SecCopyTest.copySourceTriggeringInvisibleTarget` and `copySourceTriggeringVisibleUnbuildableTarget` (HTTP 500 on a correct fix that rolled the refused copy back). Re-checked S1–S6: the fixture now persists (S3 row above), the tests drive the real duplication request, accept any client-error refusal, and assert only an unchanged outcome; the failure was the harness fault the audit names, now fixed and replayed locally. | pass |
| S7 | C2 | No `trial_summary.md`; the audit names no C2 test. Nothing to re-check. | n/a |
| S7 | C3 | No `trial_summary.md`; the audit names no C3 test. Nothing to re-check. | n/a |
| S7 | C4 | The audit's two named tests are C4's `SecCopyTest` cases (see the C1 row: the audit groups its finding as a harness fault, not a concept fault). Re-checked under C4: the state is legitimate (the copier may read the source and create a job), the refusal form is any client error, and every reference/alternative fix passes with the new fixture. | pass |

## Verdict

Gate a: **READY**. Every security test is covered by the instruction's one general property read
literally — "a configuration write must not leave the written job configured to start another job
that the user making the write is not allowed to build" — and every coupled functional value by
"Everything that works today keeps working". The only correct-fix-fails mechanism the post-trial
audit found was the unpersistable fixture, now removed: `HudsonPrivateSecurityRealm` and a
full-name-keyed `BtAuthz`, plus a functional self-check that saves the controller after the grants.
Replayed locally: pinned 9/9 security fail, 9/9 functional pass; reference 18/18; a rollback-style
correct fix 18/18 (500 on the old fixture); control reference 4+5, control pinned 0+5.

**Required: generalize** — none; `instruction.md` is unchanged in this revision.

**Quality to tighten** — none new. The audit's four required items are applied, and the new
functional self-check keeps the fixture property from regressing.

GATE_A: READY
NEEDS_HUMAN_REVIEW: NO
