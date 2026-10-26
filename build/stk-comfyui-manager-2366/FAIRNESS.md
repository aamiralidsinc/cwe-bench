# Fairness review — stk-comfyui-manager-2366 (revision 2026-10-24)

Source of the required changes: `build/stk-comfyui-manager-2366/AUDIT-FIX-20261024.md`
(the post-trial Opus audit, attribution test-fault). Instruction-only repair; no test,
oracle, manifest, trap or check patch changed.

## Tests and their covering instruction

| test | asserts | covering sentence | correct fix could fail? | risk |
|---|---|---|---|---|
| security/test_trusted_storage.py::test_state_is_not_stored_in_the_public_folder | written state is not under `<user>/default` and no config lands there | "Manager must store its state there" (where endpoints cannot write) | no | low |
| security/test_trusted_storage.py::test_planted_action_is_not_carried_out_on_current_host | planted queue is not replayed at start | "…or cause work to be carried out" | no | low |
| security/test_trusted_storage.py::test_planted_level_cannot_open_remote_install | planted `weak` level does not open install; 4xx, no marker | state trusted only where endpoints cannot write; "may not lower the effective security level" | no | low |
| security/test_trusted_storage.py::test_planted_lowered_level_cannot_open_remote_install | same for `normal-` | same | no | low |
| security/test_trusted_storage.py::test_replanted_level_after_first_run_cannot_open_remote_install | re-planted level after first run still ignored | same | no | low |
| security/test_untrusted_host.py::test_old_host_forces_the_strongest_level | no-protected-location host refuses install at planted `weak` | "Where nothing can be kept out of their reach, the strongest security level is the effective one" | no | low |
| security/test_untrusted_host.py::test_old_host_defaulted_level_is_not_enough | defaulted config does not permit restore; nothing queued | same + "cause work to be carried out" | no | low |
| security/test_untrusted_host.py::test_old_host_cannot_launch_planted_restore | planted scheduled restore is not run at start | same + "cause work to be carried out" | no | low |
| security/test_untrusted_host.py::test_old_host_ignores_planted_startup_environment | planted TLS/remap/blacklist settings do not load | "change what Manager installs or trusts" | no | low |
| security/test_untrusted_host.py::test_old_host_does_not_use_planted_package_index | planted index is never contacted | same | no | low |
| functional/test_trusted_behaviour.py::test_saved_level_and_preference_survive_first_run | saved `normal` level and unrelated preference survive the move | new clause a: carry-over once, at/above default and unrelated preferences keep values | no | low |
| functional/test_trusted_behaviour.py::test_queue_written_by_manager_runs_on_current_host | Manager's own queue runs at start | "Everything that works today keeps working" | no | low |
| functional/test_trusted_behaviour.py::test_scheduled_restore_runs_on_current_host | operator-scheduled restore runs | keep-working + "Keep legitimate use working" | no | low |
| functional/test_trusted_behaviour.py::test_trusted_install_preferences_still_apply | trusted settings in the live protected state still apply | keep-working | no | low |
| functional/test_trusted_behaviour.py::test_self_update_stays_reachable_on_old_host | self-update stays reachable under forced strongest level | keep-working; no security rule forbids an operation drawing on no public-folder state | no | low |
| functional/test_trusted_behaviour.py::test_saved_level_not_overwritten_on_old_host | saved level survives an unrelated settings save on the old host | new clause b: saved value not replaced by the enforced one | no | low |

## Leniency (QUALITY)

| wrong fix | caught by |
|---|---|
| refuse-all | `ff-refuse-all.patch` → 3 functional fails |
| crash as refusal | `sf-crash.patch` → 2 security fails |
| reads-only / still writes public | `sf-reads-only.patch` → `test_state_is_not_stored_in_the_public_folder` |
| no protected storage | `sf-no-protected-storage.patch` → 5 security fails |
| no old-host enforcement | `sf-no-oldhost-trust.patch` → 2 security fails |
| capability fail-open | `sf-capability-fail-open.patch` → 2 security fails |
| no restore guard | `sf-no-restore-guard.patch` → 1 security fail |
| no startup-config guard | `sf-no-startup-config-guard.patch` → 2 security fails |
| persist forced level | `ff-persist-forced.patch` → `test_saved_level_not_overwritten_on_old_host` |

Wrong-fix catalogue entries marked n/a (wrong object, role/direction, arithmetic normalisation,
identity parsing, shared helper) have no in-scope analogue here. No test catches a fix that
moves state but keeps a *second* writable trust source; the re-plant test covers the main form.

## Hints (QUALITY)

No file, function, field, route, or literal example value appears. "public folder" is the
advisory's own surface (T1 exempt). The two restored contracts are host-state outcomes, not
mechanism, and contain no identifier.

**Required: generalize** — none. The audit explicitly holds that both restored sentences concern
the advisory's own route and pass build rule 7's one-bug test.

**Listing check (build rule 7), re-run after the change:** FAIL `named=0 described=2`. T3 was
already DESCRIBED in the pre-change PASS (pre-existing strongest-level clause). T4 becomes
DESCRIBED because restored clause b necessarily states the coupled saved-value outcome the audit
requires. The listing failure is a direct, unavoidable consequence of Required 1b: a sentence that
gives T4 its fair contract cannot avoid describing that value. Reported for the record; the
contract was not dropped.

## Realism (QUALITY)

All traps are real upstream code at the pinned parent. T5/T6 are unmodified upstream routes the
published fix never touched and remain open on master; realistic by definition. T1–T4 are the
published fix sites. No contrived code.

## Stacking checks

Concepts: **C1 = [T3, T4]**, **C2 = [T5]**, **C3 = [T6]** (H4; T1/T2 are the non-counted base).

### S1 — Coupled traps

| functional test | concept | covering clause | security rule that could forbid it |
|---|---|---|---|
| `test_saved_level_and_preference_survive_first_run` | C1 | clause a + "Everything that works today keeps working" | none: at/above-default level and unrelated preference are explicitly preserved |
| `test_saved_level_not_overwritten_on_old_host` | C1 | clause b | none: enforcement may change the effective level but not replace the saved value |
| `test_self_update_stays_reachable_on_old_host` | C1 | "Everything that works today keeps working" / "Keep legitimate use working" | none: no planted state is involved, so the public-folder rule does not apply |
| `test_queue_written_by_manager_runs_on_current_host` | base/C2 | keep-working | none: queue sits in the protected location |
| `test_scheduled_restore_runs_on_current_host` | C2 | keep-working | none: issued through the real route on a protected-location host |
| `test_trusted_install_preferences_still_apply` | C3 | keep-working | none: settings are configured in the live protected state |

Result: no contradiction; a correct fix can satisfy both the security rules and each coupled
value.

### S2 — Shape traps

| concept | refused shape | outside the legitimate set because |
|---|---|---|
| C1 | planted `weak` / `normal-` / absent level in the public folder; copy in an unreachable-looking folder on a no-API host | the only legitimate source is state the operator saved at the protected location; the public folder is never one, and the strongest level is stated for a host with no protected location |
| C1 | `target=legit` restore on a no-protected-location host | the same operation is legitimate on a protected-location host (functional test); the old host is governed by the stated strongest level |
| C2 | planted restore queue in the public folder on a no-protected-location host | restore queues the operator schedules are legitimate on a protected host; here the source is writable state |
| C3 | planted `bypass_ssl`/remap/blacklist/index values in the public folder | the same values are legitimate when configured in the live protected state (functional test); the public-folder copy is not |

Result: no refused shape falls inside a legitimate set the instruction describes.

### S3 — Fixtures and harness

States are the two legitimate operator states (pre-existing saved settings; live protected
settings the operator configured) plus planted writable copies the instruction calls untrusted.
The harness reaches every concept through the real entry point: the aiohttp route table
registered by the product, the startup-hook import, and the product's own state API; it never
computes a security decision. A guard at dispatcher, handler or core layer is therefore
observable. Pass.

### S4 — Concept independence

| concept | security test on pinned code | own route | correct fix alone passes |
|---|---|---|---|
| C1 | `test_old_host_forces_the_strongest_level`, `test_old_host_defaulted_level_is_not_enough` | install and restore routes on a no-capability host | yes (`sf-no-oldhost-trust` flips only these) |
| C2 | `test_old_host_cannot_launch_planted_restore` | startup consumer | yes (`sf-no-restore-guard` flips only this) |
| C3 | `test_old_host_ignores_planted_startup_environment`, `test_old_host_does_not_use_planted_package_index` | startup configuration/package loader | yes (`sf-no-startup-config-guard` flips only these) |

Masking (H3c) does not apply to pattern H4. Pass.

### S5 — History

Pattern is H4, so the H3a/H3b `upstream_first_fix` rule does not apply. Recall evidence:
`checks/upstream_fix.patch` still violates the literal property — a planted restore is carried
out and planted startup settings change what Manager installs or trusts (3 security tests fail);
the unmodified published form also replaces the operator's saved level (clause b). It differs
from the reference in exactly the covered outcomes, not merely in code. Pass.

### S6 — Contracts

Tests read only pre-existing product names (`manager_config_path`, `manager_files_path`,
`manager_snapshot_path`, `manager_startup_script_path`, `get_config`, `write_config`,
`reserve_script`, the startup module's existing attributes); nothing new must be guessed. No
wrong-object trap. The fail-open fallback is stated in product terms: the host either offers a
protected location or nothing can be kept out of the endpoints' reach, with the required outcome
for each. Pass.

### S7 — Decisive tests

`build/stk-comfyui-manager-2366/trial_summary.md` does not exist for this revision; nothing to
re-check. Not fired.

## Verdict

GATE_A: READY
NEEDS_HUMAN_REVIEW: NO
