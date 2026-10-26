# Build one security-fix benchmark task (build-v1)

## What this is
We build a security-fix benchmark from published, already-fixed advisories in open-source projects.
You build ONE task, from the advisory below.

The task pins the project at the commit just before the published fix and gives a solver agent that
code plus a short problem report (`instruction.md`). Hidden behavioural tests then score the
solver's fix. The tests check that the flaw is closed, using harmless inputs and markers, and that
legitimate use still works.

Everything stays on this machine. Describe each mechanism in one line in notes and reports; the
tests hold the detail, so never write exploitation steps out in prose. Stay inside this advisory's
own protection, in this repository, at the pinned commit. Note anything outside that scope in one
line in your report, and do not build on it.

Project root: `/home/mara/cwe-bench`. Task: `stk-comfyui-manager-2366`. Pattern: `A+B`. Track: `stacked`.

## Goal and acceptance
- **The bar.** Two target models (DeepSeek V4.1 Flash, MiMo-V2.6-Pro) must each fail all 3
  finished attempts because of their own judgement.
- **Fairness.** Everything the tests require must be findable from `instruction.md` plus the code,
  or be standard expert knowledge. A careful engineer who knows where to look fixes it in about
  45 minutes.
- **What never counts as a failure:** timeouts, and runs cut by API or network errors.
- **Proof.** A task is built only when the gate passes. A task that misses the bar is reported as
  such, never shipped weaker.

## Inputs
- Advisory: 2366; authorization bypass via unprotected alternate channel (trusted config
- Pinned (vulnerable) commit: c8dce94c031ed87a8673d354482a39dedc15407b. Published fix: e44c5cef58fb4973670b86433b9d24d077b44a26.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "candidate_id": "h4-2366",
 "pattern": "H4",
 "repo": "comfy-org/comfyui-manager",
 "pinned_commit": "c8dce94c031ed87a8673d354482a39dedc15407b",
 "protections": [
  "P1: Manager's own trusted state (config.ini security_level, startup-scripts queue, snapshots, pip override/blacklist/auto-fix lists, DB cache, channels) must not be stored in or loaded from a folder that ComfyUI's userdata web API can write; it is currently stored at <user>/default/ComfyUI-Manager (glob/manager_core.py:217, prestartup_script.py:88, prestartup_script.py:519).",
  "P2: When no protected location exists (host ComfyUI lacks a system-user directory), state loaded from the web-writable legacy folder must not be trusted: security_level is treated as strong and startup-time actions read from that folder are refused (no such fallback exists in the pinned code: glob/manager_core.py:1739, glob/manager_core.py:1766, prestartup_script.py:574, prestartup_script.py:796)."
 ],
 "traps": [
  {
   "id": "T1",
   "mechanism": "M5",
   "origin": "advisory_route",
   "locations": [
    "glob/manager_core.py:217",
    "glob/manager_core.py:229",
    "glob/manager_core.py:1739",
    "glob/manager_server.py:89"
   ],
   "reason_to_dismiss": "",
   "distance": {
    "files": 0,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "easy",
   "tier_mimo": "easy",
   "type": "neither",
   "evidence": [
    "glob/manager_core.py:217 manager_files_path = <user>/default/ComfyUI-Manager",
    "glob/manager_core.py:229 config.ini is placed in that folder",
    "glob/manager_core.py:1713 read_config reads config.ini from there",
    "glob/manager_core.py:1739 security_level taken straight from the stored config",
    "glob/manager_server.py:89-98 is_allowed_security_level gates every risky route on get_config()['security_level']",
    "glob/manager_core.py:230-234 channels.list, pip_overrides, pip_blacklist, components and DB cache share the same folder (same fix closes them)",
    "glob/share_3rdparty.py:68-121 share credentials also live in manager_files_path (same fix)",
    "cm-cli.py:146 cm-cli reaches the same path through Ctx.set_user_directory -> core.update_user_directory"
   ]
  },
  {
   "id": "T2",
   "mechanism": "M2",
   "origin": "published_fix_far_site",
   "locations": [
    "prestartup_script.py:88",
    "prestartup_script.py:519",
    "prestartup_script.py:742",
    "prestartup_script.py:776",
    "prestartup_script.py:796"
   ],
   "reason_to_dismiss": "prestartup_script.py is a separate startup hook rather than the web/core module, and it only replays a queue that Manager itself wrote (glob/manager_core.py:1842), so fixing manager_core's path looks sufficient.",
   "distance": {
    "files": 1,
    "packages": 1
   },
   "protection_state": "absent",
   "tier_deepseek": "medium",
   "tier_mimo": "medium",
   "type": "deepseek",
   "evidence": [
    "prestartup_script.py:88 independently recomputes <user>/default/ComfyUI-Manager",
    "prestartup_script.py:519 hardcodes the install-scripts.txt path again without using manager_files_path",
    "prestartup_script.py:750 each queued line is parsed with ast.literal_eval",
    "prestartup_script.py:763-776 a non-'#' entry is executed as a process with process_wrap(script[1:], script[0])",
    "prestartup_script.py:796-797 execution happens whenever the file exists, with no trust check",
    "glob/manager_core.py:1842 and glob/manager_core.py:955 are the legitimate writers of the queue"
   ]
  },
  {
   "id": "T3",
   "mechanism": "M4",
   "origin": "published_fix_far_site",
   "locations": [
    "glob/manager_core.py:1739",
    "glob/manager_core.py:1766",
    "glob/manager_core.py:241"
   ],
   "reason_to_dismiss": "Once the folder moves to a protected location the issue looks closed; old ComfyUI hosts without a protected system-user directory look out of scope, and nothing in this repository shows that the host may lack one.",
   "distance": {
    "files": 0,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "hard",
   "tier_mimo": "medium",
   "type": "deepseek",
   "evidence": [
    "glob/manager_core.py:241 path is derived only from folder_paths.get_user_directory(); there is no capability check of the host",
    "glob/manager_core.py:1739 main branch returns the stored security_level unmodified",
    "glob/manager_core.py:1766 fallback branch returns 'normal' (not strong) when config.ini is missing or unparsable",
    "glob/manager_server.py:98 'normal' already passes 'middle'-level gates"
   ]
  },
  {
   "id": "T4",
   "mechanism": "M11",
   "origin": "published_fix_far_site",
   "locations": [
    "glob/manager_server.py:1377",
    "glob/manager_core.py:1739",
    "glob/manager_core.py:1696"
   ],
   "reason_to_dismiss": "",
   "distance": {
    "files": 1,
    "packages": 0
   },
   "protection_state": "weak",
   "tier_deepseek": "medium",
   "tier_mimo": "hard",
   "type": "mimo",
   "evidence": [
    "glob/manager_server.py:1377-1381 update_comfyui is not gated by is_allowed_security_level, so ComfyUI self-update must keep working under a forced 'strong' level (the way a user upgrades to a host with the protected directory)",
    "glob/manager_core.py:1696 write_config persists get_config()['security_level']; a forced override that is written back would permanently overwrite the user's own setting",
    "glob/manager_server.py:94-98 only weak/normal-/normal levels change gate results; a legitimate 'strong' or 'normal' level in a user's existing config must be kept, not reset"
   ]
  },
  {
   "id": "T5",
   "mechanism": "M4",
   "origin": "uncovered_upstream",
   "locations": [
    "prestartup_script.py:91",
    "prestartup_script.py:574",
    "prestartup_script.py:604",
    "cm-cli.py:1076"
   ],
   "reason_to_dismiss": "Snapshot restore is a neighbouring feature: the HTTP restore route is already gated (glob/manager_server.py:984), so once the level is forced to strong, restore seems blocked.",
   "distance": {
    "files": 1,
    "packages": 1
   },
   "protection_state": "absent",
   "tier_deepseek": "xhard",
   "tier_mimo": "hard",
   "type": "deepseek",
   "evidence": [
    "prestartup_script.py:91 restore-snapshot.json path is under the same web-writable folder",
    "prestartup_script.py:574 runs whenever the file exists",
    "prestartup_script.py:604-605 spawns cm-cli restore-snapshot on it",
    "cm-cli.py:1076-1133 restore-snapshot command calls core.restore_snapshot with no security_level check",
    "glob/manager_server.py:984-997 the gated HTTP route only copies the snapshot into this file; the startup consumer bypasses the gate"
   ]
  },
  {
   "id": "T6",
   "mechanism": "M6",
   "origin": "uncovered_upstream",
   "locations": [
    "prestartup_script.py:99",
    "prestartup_script.py:126",
    "prestartup_script.py:131",
    "prestartup_script.py:505",
    "prestartup_script.py:520",
    "glob/manager_util.py:494"
   ],
   "reason_to_dismiss": "These look like tuning knobs (uv mode, logging, package remaps) rather than the security level, and they are read before Manager core loads, so the forced-strong override in read_config looks like the only place that matters.",
   "distance": {
    "files": 2,
    "packages": 1
   },
   "protection_state": "absent",
   "tier_deepseek": "hard",
   "tier_mimo": "hard",
   "type": "deepseek",
   "evidence": [
    "prestartup_script.py:99-107 a separate config.ini loader that never goes through manager_core.read_config",
    "prestartup_script.py:505-510 bypass_ssl from that loader disables TLS verification process-wide",
    "prestartup_script.py:126-136 pip_overrides.json and pip_blacklist.list loaded from the legacy folder",
    "prestartup_script.py:140 overrides remap requirement names at startup install (prestartup_script.py:630)",
    "prestartup_script.py:520 and prestartup_script.py:800 PIPFixer built with the legacy manager_files_path and run at every start",
    "glob/manager_util.py:494-530 pip_auto_fix.list from that folder drives pip install, including an index_url"
   ]
  },
  {
   "id": "T7",
   "mechanism": "M2",
   "origin": "injection_room",
   "locations": [
    "cm-cli.py:81"
   ],
   "reason_to_dismiss": "cm-cli is a local CLI tool, not a web route, so a direct config read there seems to need no trust override.",
   "distance": {
    "files": 1,
    "packages": 1
   },
   "protection_state": "absent",
   "tier_deepseek": "medium",
   "tier_mimo": "medium",
   "type": "deepseek",
   "evidence": [
    "cm-cli.py:81-94 cm-cli already parses config.ini by itself outside read_config",
    "cm-cli.py:85 it currently reads core.manager_config.path (an attribute that does not exist; the real one is manager_config_path at glob/manager_core.py:229), so the read raises and is swallowed at cm-cli.py:93; a planted sibling must fix the attribute so the path is live"
   ]
  },
  {
   "id": "T8",
   "mechanism": "M1",
   "origin": "injection_room",
   "locations": [
    "glob/manager_core.py:1838",
    "prestartup_script.py:796"
   ],
   "reason_to_dismiss": "The startup guard covers the one known queue file, and another queue file looks like a Manager-internal implementation detail.",
   "distance": {
    "files": 1,
    "packages": 1
   },
   "protection_state": "absent",
   "tier_deepseek": "hard",
   "tier_mimo": "medium",
   "type": "deepseek",
   "evidence": [
    "glob/manager_core.py:1838-1845 and glob/manager_core.py:954-958 write startup-queue entries into manager_startup_script_path",
    "prestartup_script.py:796 the consumer checks only existence of one filename; a second queue file consumed the same way would need its own guard"
   ]
  }
 ],
 "independent_groups": [
  [
   "T1"
  ],
  [
   "T2"
  ],
  [
   "T3"
  ],
  [
   "T4"
  ],
  [
   "T5"
  ],
  [
   "T6"
  ],
  [
   "T7"
  ],
  [
   "T8"
  ]
 ],
 "history": {
  "a_fix_leaves_b_open": null,
  "b_in_code_a_wrote": null,
  "masking": [
   "T5 and T6 are closed on new hosts by the T2 path move (prestartup_script.py:88-92 derive all their paths from manager_files_path), so they are only reachable on the old-host shape that T3 introduces; a solver who does not model the old-host shape never sees them."
  ],
  "dependency_bump_fix": false,
  "in_repo_fix_possible": true
 },
 "conflicts": [
  {
   "a": "T3",
   "b": "T4",
   "what": "Forcing security_level to strong on old hosts must not block the ungated ComfyUI self-update (glob/manager_server.py:1377), and the forced value must not be written back over the user's config by write_config (glob/manager_core.py:1696). A blanket 'block all' or 'persist strong' breaks the upgrade path."
  },
  {
   "a": "T1",
   "b": "T4",
   "what": "Moving the folder without migrating it discards a legitimate user's config.ini, snapshots and pip lists; migrating blindly imports a possibly tampered security_level, so only weak/normal- should be raised and strong/normal kept."
  },
  {
   "a": "T5",
   "b": "T4",
   "what": "Refusing restore-snapshot.json at startup on old hosts also refuses a restore the owner scheduled legitimately; this is acceptable only because the HTTP scheduling route is already blocked under strong (glob/manager_server.py:984)."
  },
  {
   "a": "T6",
   "b": "T4",
   "what": "Ignoring legacy pip_overrides/pip_blacklist/use_uv on old hosts changes legitimate install behaviour (prestartup_script.py:110-111, prestartup_script.py:139-145)."
  }
 ],
 "fairness_risks": [
  "Tests must stub folder_paths.get_system_user_directory (absent from this repo), and the protected folder name (__manager) is a host convention that the code here cannot discover; hidden tests should accept any location returned by that API instead of a hardcoded name.",
  "Old-host behaviour (forced strong, startup scripts blocked) contradicts a user who intentionally set security_level=weak on an old host; tests must state that the downgrade is expected.",
  "update_comfyui (glob/manager_server.py:1377) must stay reachable under forced strong; a test that asserts 'all /manager routes 403 on old hosts' would be unfair.",
  "T6 has no published reference: upstream also left it open (per screener), so expected behaviour (ignore vs. load-but-ignore-security-relevant keys such as bypass_ssl and pip_auto_fix index_url) must be specified, or the trap graded only on the security-relevant keys."
 ],
 "effort_minutes": 70,
 "usable": true,
 "design": {
  "traps": [
   "T2",
   "T3",
   "T4",
   "T5",
   "T6"
  ],
  "why": "T1 is the landing point the report leads to and acts as the base fix rather than a scored trap. On top of it, T2 (second path implementation plus executor in the startup hook; reason: 'just a copy / Manager wrote it'), T3 (old-host fallback that never existed; reason: 'out of scope once moved'), T5 (startup restore-snapshot consumer reaching an ungated cm-cli; reason: 'HTTP route already gated') and T6 (separate prestartup config/pip loader off the read_config path; reason: 'tuning knobs') each need a separate fix site and a different reason to dismiss. T2, T3, T5 and T6 are deepseek-type and T4 is the mimo-type coupled value (keep update_comfyui, do not persist the forced level, keep legitimate strong/normal). Planted siblings T7/T8 are weaker, because T7's existing code is dead (cm-cli.py:85) and T8 is a near-surface variant. Keep T6 as an optional fifth trap if the spec cannot pin down its expected behaviour."
 },
 "unverified": [
  "Whether the worktree HEAD c8dce94c is exactly the parent of fix commit e44c5cef (git history was not inspected; line numbers match the screener's references to the pinned code).",
  "Contents of the fix diff (fix.diff line references in the screener) and upstream advisory text; the published-fix coverage of T2/T3/T4 and non-coverage of T5/T6 is taken from the screener record, not read.",
  "That ComfyUI's userdata API can write <user>/default/ComfyUI-Manager and protects '__'-prefixed folders (lives in ComfyUI core, not in this repo).",
  "Whether T5/T6 are still present in the latest upstream (screener claims latest/prestartup_script.py:602 and :107-135).",
  "Whether the cached DB under manager_util.cache_dir (glob/manager_core.py:234) or channels.list (glob/manager_core.py:1635) can redirect installs independently of the security level; treated as part of T1's group.",
  "Repository size in MB.",
  "Resolved from screener unverified list: glob/security_check.py:11-12 derives paths from __file__ and does not read legacy Manager state; pip_fixer.fix_broken does read pip_auto_fix.list from the legacy path (glob/manager_util.py:494), now part of T6."
 ]
}
  ```
- Published fix sites:   - glob/manager_core.py:217 — T1 M5 (reason to dismiss: none)
  - glob/manager_core.py:229 — T1 M5 (reason to dismiss: none)
  - glob/manager_core.py:1739 — T1 M5 (reason to dismiss: none)
  - glob/manager_server.py:89 — T1 M5 (reason to dismiss: none)
  - prestartup_script.py:88 — T2 M2 (reason to dismiss: prestartup_script.py is a separate startup hook rather than the web/core module, and it only replays a queue that Manager itself wrote (glob/manager_core.py:1842), so fixing manager_core's path looks sufficient.)
  - prestartup_script.py:519 — T2 M2 (reason to dismiss: prestartup_script.py is a separate startup hook rather than the web/core module, and it only replays a queue that Manager itself wrote (glob/manager_core.py:1842), so fixing manager_core's path looks sufficient.)
  - prestartup_script.py:742 — T2 M2 (reason to dismiss: prestartup_script.py is a separate startup hook rather than the web/core module, and it only replays a queue that Manager itself wrote (glob/manager_core.py:1842), so fixing manager_core's path looks sufficient.)
  - prestartup_script.py:776 — T2 M2 (reason to dismiss: prestartup_script.py is a separate startup hook rather than the web/core module, and it only replays a queue that Manager itself wrote (glob/manager_core.py:1842), so fixing manager_core's path looks sufficient.)
  - prestartup_script.py:796 — T2 M2 (reason to dismiss: prestartup_script.py is a separate startup hook rather than the web/core module, and it only replays a queue that Manager itself wrote (glob/manager_core.py:1842), so fixing manager_core's path looks sufficient.)
  - glob/manager_core.py:1739 — T3 M4 (reason to dismiss: Once the folder moves to a protected location the issue looks closed; old ComfyUI hosts without a protected system-user directory look out of scope, and nothing in this repository shows that the host may lack one.)
  - glob/manager_core.py:1766 — T3 M4 (reason to dismiss: Once the folder moves to a protected location the issue looks closed; old ComfyUI hosts without a protected system-user directory look out of scope, and nothing in this repository shows that the host may lack one.)
  - glob/manager_core.py:241 — T3 M4 (reason to dismiss: Once the folder moves to a protected location the issue looks closed; old ComfyUI hosts without a protected system-user directory look out of scope, and nothing in this repository shows that the host may lack one.)
  - glob/manager_server.py:1377 — T4 M11 (reason to dismiss: none)
  - glob/manager_core.py:1739 — T4 M11 (reason to dismiss: none)
  - glob/manager_core.py:1696 — T4 M11 (reason to dismiss: none)
- Uncovered routes to confirm (pattern B):   - prestartup_script.py:91 — T5 M4 (reason to dismiss: Snapshot restore is a neighbouring feature: the HTTP restore route is already gated (glob/manager_server.py:984), so once the level is forced to strong, restore seems blocked.)
  - prestartup_script.py:574 — T5 M4 (reason to dismiss: Snapshot restore is a neighbouring feature: the HTTP restore route is already gated (glob/manager_server.py:984), so once the level is forced to strong, restore seems blocked.)
  - prestartup_script.py:604 — T5 M4 (reason to dismiss: Snapshot restore is a neighbouring feature: the HTTP restore route is already gated (glob/manager_server.py:984), so once the level is forced to strong, restore seems blocked.)
  - cm-cli.py:1076 — T5 M4 (reason to dismiss: Snapshot restore is a neighbouring feature: the HTTP restore route is already gated (glob/manager_server.py:984), so once the level is forced to strong, restore seems blocked.)
  - prestartup_script.py:99 — T6 M6 (reason to dismiss: These look like tuning knobs (uv mode, logging, package remaps) rather than the security level, and they are read before Manager core loads, so the forced-strong override in read_config looks like the only place that matters.)
  - prestartup_script.py:126 — T6 M6 (reason to dismiss: These look like tuning knobs (uv mode, logging, package remaps) rather than the security level, and they are read before Manager core loads, so the forced-strong override in read_config looks like the only place that matters.)
  - prestartup_script.py:131 — T6 M6 (reason to dismiss: These look like tuning knobs (uv mode, logging, package remaps) rather than the security level, and they are read before Manager core loads, so the forced-strong override in read_config looks like the only place that matters.)
  - prestartup_script.py:505 — T6 M6 (reason to dismiss: These look like tuning knobs (uv mode, logging, package remaps) rather than the security level, and they are read before Manager core loads, so the forced-strong override in read_config looks like the only place that matters.)
  - prestartup_script.py:520 — T6 M6 (reason to dismiss: These look like tuning knobs (uv mode, logging, package remaps) rather than the security level, and they are read before Manager core loads, so the forced-strong override in read_config looks like the only place that matters.)
  - glob/manager_util.py:494 — T6 M6 (reason to dismiss: These look like tuning knobs (uv mode, logging, package remaps) rather than the security level, and they are read before Manager core loads, so the forced-strong override in read_config looks like the only place that matters.)
- Design plan from the lead: TRACK = STACKED (H4). Build the stacked design the reader chose: traps T2, T3, T4, T5, T6. Why: T1 is the landing point the report leads to and acts as the base fix rather than a scored trap. On top of it, T2 (second path implementation plus executor in the startup hook; reason: 'just a copy / Manager wrote it'), T3 (old-host fallback that never existed; reason: 'out of scope once moved'), T5 (startup restore-snapshot consumer reaching an ungated cm-cli; reason: 'HTTP route already gated') and T6 (separate prestartup config/pip loader off the read_config path; reason: 'tuning knobs') each need a separate fix site and a different reason to dismiss. T2, T3, T5 and T6 are deepseek-type and T4 is the mimo-type coupled value (keep update_comfyui, do not persist the forced level, keep legitimate strong/normal). Planted siblings T7/T8 are weaker, because T7's existing code is dead (cm-cli.py:85) and T8 is a near-surface variant. Keep T6 as an optional fifth trap if the spec cannot pin down its expected behaviour. Follow the stacked-task rules appended at the end of this prompt; they add to the rules above.
- Host notes: Reader fairness risks (resolve each in the report's contracts or the tests): Tests must stub folder_paths.get_system_user_directory (absent from this repo), and the protected folder name (__manager) is a host convention that the code here cannot discover; hidden tests should accept any location returned by that API instead of a hardcoded name. | Old-host behaviour (forced strong, startup scripts blocked) contradicts a user who intentionally set security_level=weak on an old host; tests must state that the downgrade is expected. | update_comfyui (glob/manager_server.py:1377) must stay reachable under forced strong; a test that asserts 'all /manager routes 403 on old hosts' would be unfair. | T6 has no published reference: upstream also left it open (per screener), so expected behaviour (ignore vs. load-but-ignore-security-relevant keys such as bypass_ssl and pip_auto_fix index_url) must be specified, or the trap graded only on the security-relevant keys.. Conflicts the reader found: Forcing security_level to strong on old hosts must not block the ungated ComfyUI self-update (glob/manager_server.py:1377), and the forced value must not be written back over the user's config by write_config (glob/manager_core.py:1696). A blanket 'block all' or 'persist strong' breaks the upgrade path. | Moving the folder without migrating it discards a legitimate user's config.ini, snapshots and pip lists; migrating blindly imports a possibly tampered security_level, so only weak/normal- should be raised and strong/normal kept. | Refusing restore-snapshot.json at startup on old hosts also refuses a restore the owner scheduled legitimately; this is acceptable only because the HTTP scheduling route is already blocked under strong (glob/manager_server.py:984). | Ignoring legacy pip_overrides/pip_blacklist/use_uv on old hosts changes legitimate install behaviour (prestartup_script.py:110-111, prestartup_script.py:139-145).

## Design: where difficulty comes from
Models find the code the report leads to and diagnose it correctly. They fail on scope. Build these
in, in order of evidence:
1. **Pattern A: the published fix's far sites.**
   - The report leads to one site. The tests cover every entry point the published fix protects,
     including one in a module that looks out of scope: a second implementation, a lower-level
     public API, a wrapper, a save/reload path, or a defaults or merge route.
   - Give it a plausible **reason to dismiss**, and **distance**: another file or package from the
     landing point.
   - **A second implementation is the strongest form of this**: separate code doing the same
     guarded operation (a fallback backend, another package, another transport, a legacy version),
     so fixing the reported copy changes nothing in the other. Models fix the copy the example hits,
     re-run the example and stop. Prefer a real one (Pattern A or B) over a planted one. Find
     candidates by searching for the low-level primitive across packages (redirect following,
     header copying, file writes, message construction). It only counts if the report never
     describes it.
2. **Pattern B: uncovered routes.**
   - Routes into the same protected sink where the advisory's own protection is missing at the
     pinned commit, and which the published fix did not touch.
   - They are unmodified upstream code. A solver may argue they were never covered, but the task's
     general property covers them, so leaving one open is a model failure, not out of scope. The
     same holds for a route where the protection never existed: the property requires it.
   - Make sure the property, read literally, really covers each route (no word that excludes it),
     and that its test fails only when the protection is really missing (it must pass a correct
     fix placed at any valid layer).
   - The strongest lever found so far: DeepSeek 6 of 6 on one; both models 0 of 3 on three combined.
3. **Shape traps: an input form that a plausible check mishandles.** Examples: a value given as an
   array where the check only handles a string; a name split on the first separator when it can
   contain the separator; a resolved path against a lexical check; a rename or rewrite that happens
   after the check; a nested expression the check never inspects. Two conditions: the general
   property must cover the form literally, and the form must not fall inside anything a
   must-keep-working clause or a test fixture calls legitimate. A pure spelling, encoding, verb,
   protocol or role variant of a stated input is NOT a shape trap: both models always catch those
   (see "Never add").
4. **A coupled must-keep-working behaviour** next to the sink, tested functionally, so an
   over-broad fix fails. MiMo tends to over-harden.
5. **Producer off the check's path.** The check depends on data produced elsewhere (a schema,
   serializer, cache, mapper, table builder or config loader) and does not call it; the data
   reaches the check on a separate path (saved and reloaded, rebuilt from config). The fix needs
   both the check and the producer. Models trace into what the check calls, never back to where
   its data comes from. Rules:
   - it counts only if the producer is infrastructure, not a request handler;
   - verify that the check does **not** call the producer; if it does, the model follows the call
     and fixes it;
   - the report describes impact only through the check's path and states the property abstractly
     ("including data saved earlier"); it never points at the producer or the reload path;
   - avoid fixes where the check cannot compile without the producer change (that forces the find);
   - hidden tests must not need a field or function name the solver would have to guess;
   - prefer a producer deep in internal machinery (a table or schema builder). One behind a path
     that is easy to follow falls as soon as anything points at it.
6. **Injected siblings**, only where the plan asks for them. Each must be:
   - code a maintainer could have written, with no deceptive names or comments;
   - reachable through the real entry point;
   - covered by the task's general property, never by a sentence of its own;
   - placed where the upstream fix never touches.
7. **Wrong object.** The authorization check exists but decides on a different object than the one
   the request actually touches: a neighbouring or proxy resource (a parent or container instead of
   the item written), or an identity field the caller supplies (an account inside a caller-provided
   resource name; a parent read from one part of the request while the write uses another). Models
   copy the nearby precedent. Rules:
   - the instruction names the protected object class in product terms ("the objects that hold the
     limits"), never the check or its location;
   - the security test denies exactly the object touched while the proxy object stays allowed;
   - a functional test keeps a legitimate request on that same object working.
8. **Ordering.** The check is right but runs at the wrong moment: after an adjustment turns the
   attacker's value into a different bad value (an offset, a clamp, a unit conversion, a
   normalisation), or after a side effect has already happened (a directory created, a file cleared,
   copied or re-permissioned, a request sent) before the refusal. Rules:
   - the instruction states the property over the attacker's input or the outcome ("nothing outside
     the folder is created or changed, even when the request is refused"), never the order of steps;
   - the security test checks the side effect itself, not only the response;
   - any fix that keeps the property passes, wherever it places the check.
9. **Route where the protection never existed.** Real code reaches the protected sink but never had
   the check at all, so its absence reads as design (DeepSeek missed one 6 of 6 times). Rules:
   - it needs a plausible reason to dismiss: an unsupported combination, a legacy path, a
     neighbouring feature. If the project documents the protection as applying everywhere with no
     exceptions, there is no reason to dismiss and the route adds nothing;
   - the general property must cover it literally; never describe it in the instruction;
   - confirm it with a behavioural test on the pinned copy, like any Pattern B route.
10. **Merged or defaults route.** The restricted value reaches the sink through defaults, a merge,
    inheritance, a patch, or stored configuration rather than the request field the report shows.
    Models treat the report's example fields as the whole set. Rules:
    - state the property over the sink ("anything a submitter supplies that ends up in X, however
      it gets there"), not over the entry or field;
    - the security test drives the merged or stored route through the real entry point;
    - a functional test keeps legitimate defaults and merges working.

Aim for at least two levers with **different** reasons to dismiss.

**At least one lever must be how-type**: its fix needs the mechanism understood, not only found.
How-type levers are a producer off the check's path (5), a coupled must-keep-working value (4), a
shape that a plausible check mishandles (3: a separator split, a rename after the check), and a
route where the protection never existed. Where-type levers (another entry point into the same code,
a second copy, injected siblings) only cost a search. They held only when the report stayed general,
so count them as extras, never as the task's main difficulty.

Never add:
- encoding, verb, protocol or role/direction variants;
- more routes of one concept;
- resource-exhaustion traps.

Every lever must be findable by a blind engineer from the report and the code. A lever that a blind
fix cannot find is unfair: remove it.

**Pattern B rules:**
- Confirm each route with a behavioural test on the pinned copy before relying on it. The
  screener's claim is only a lead.
- Append one row per route to `/home/mara/cwe-bench/build/audit/uncovered-routes.tsv`, using its existing
  header. Columns:
  - `task`, `repo`, `advisory`;
  - `trap_ref` (the manifest trap id only; no mechanism text, since the manifest holds the detail);
  - `real_upstream`;
  - `present_in_latest` (`yes`, `no` or `unknown`, from a read-only look at current upstream code if
    you can reach it);
  - `public_upstream_report`, `in_current_scope`, `built`, `note`;
  - `disclosure_status` (`pending client decision`).

## Environment (`tasks/stk-comfyui-manager-2366/environment/Dockerfile`)
- **Base and code.** A small official base image. The repo goes into `/app` at the pinned commit,
  and `/app/.git` is then deleted.
- **Offline.** Install every dependency, tool and service the project and tests need; nothing may
  be downloaded at test time. Services start from `test.sh`.
- **Packages:** `patch`, `curl`, `ca-certificates`, `bash`, `git`.
- **Agent layer.** Append `harness/claude-code.Dockerfile.snippet` unchanged at the end.
- **No test code in the image.** The agent shares the container. Pre-build against stubs; `test.sh`
  copies the real tests in at grading time.
- **Project tests.** The project's own tests for the affected area must pass in the image at the
  pinned commit.
- **No leaked regression tests.** The pinned commit must not already contain the advisory's
  regression tests (check `git log` between the pinned and fix commits).

## Report to the solver (`tasks/stk-comfyui-manager-2366/instruction.md`)
**Write:**
- what the system is, at product level;
- one observed impact, with ONE concrete trigger at user level (HTTP request, CLI call or public API
  use);
- the security property as an **invariant**, stated once in general terms: who may do what to which
  data, or what attacker input must never achieve ("no value of X may …, however it arrives"). It is
  fair when, read literally, it covers every tested route and shape; it must not point at any of
  them. Write a second property only for a genuinely different protection, never one per route,
  and never a count;
- every **contract** the tests need, each stated once for the whole product, never per route:
  - the refusal form ("a client error with no side effect");
  - any interface or field name a test uses, stated so it applies everywhere. If a sibling's test
    would need a contract that only that sibling uses, change the test so it does not, or drop the
    sibling;
  - preservation clauses ("everything that works today keeps working exactly as today"). Name a
    coupled legitimate value in property terms ("visible values keep binding even next to a hidden
    one"), not by the feature or route it sits on;
  - a legitimate magnitude next to any attack magnitude;
- that examples are examples, not the full set;
- the standard constraints block: fix the problem and its close variants; keep legitimate use
  working; do not look up the upstream fix; do not special-case the
  example.

**Never write:**
- file, package, function, class, field or parameter names a user would not see;
- line numbers, the root cause, the fix approach, or a CVE or GHSA id;
- a list of routes, spellings or roles;
- restricting adverbs ("directly", "only via");
- anything that names or paraphrases a far site, an uncovered route or an injected sibling;
- any clause that describes where a far site, uncovered route or injected sibling lives, even in
  product terms: no route, operation, command, channel, object kind, stage or format that points
  at one of them. State each property once, over the protected data or outcome, so it covers every
  route without pointing at any;
- a word that is general but is also the name of one stage or entry point ("loading" when the
  product has a load call). Pick wording that cannot be read as one surface.

Check before you finish: for each sentence of the report, ask whether it exists to cover one
specific route or trap. If it does, delete it or widen it into the general property.

Put every identifier that must not appear in `manifest.leak_terms`.

## Tests (`tasks/stk-comfyui-manager-2366/tests/`)
- **`security/`:** one test per site, route, input shape and form. Each one:
  - goes through the real entry point;
  - fails on the pinned code and passes on a correct fix;
  - asserts the attack is blocked: any client error plus no side effect, never one exact status.
- **`functional/`:**
  - legitimate use, including the coupled behaviour of every lever;
  - where they exist, the project's own tests for the area.
- **No product code in a test's bookkeeping.** Compute expected values and clean-ups in the test
  itself, because a hardened helper must not crash a test.
- **Stubs** of permission or authority answer per resource and verb, like the real thing.
- **Scope.** A test may vary only what the instruction names, and drive only the entry point it
  names.
- **No network**, and nothing that depends on the fix commit being present.
- **Templates.** JUnit XML into the two directories the template names. Copy `score.py` unchanged.
  Edit only the marked command lines of `test.sh`, and keep its agent-kill block.

## Proof
- **The oracle.** `solution/fix.patch` is the published fix reduced to source changes, plus fixes
  for every uncovered route and injected sibling in the task. `solution/solve.sh` applies it to
  `/app`.
- **Wrong-fix patches** go in `build/stk-comfyui-manager-2366/checks/`, listed in `manifest.patch_checks`:
  - one `security_fail` per lever (the fix that misses only that lever);
  - a `functional_fail` (an over-broad or feature-removing fix);
  - a `pass` of kind `hardening` (the oracle plus defensive hardening of the product code the
    security tests import);
  - a `pass` alternative fix where a second valid design is plausible.
- **`manifest.wrong_fix_catalogue`:** for each class, a `checks/` patch, or `n/a: <why>`:
  `refuse_all`, `crash_as_refusal`, `wrong_resource`, `one_role_or_direction`, `reads_only`,
  `check_after_adjustment`, `unlisted_route`, `malformed_identity`, `missing_authority`,
  `adjacent_api`.

## Deliverables
**`tasks/stk-comfyui-manager-2366/`:**
- `instruction.md`;
- `task.toml`, from `builder/templates/`, with `[metadata]` (incl. the delivery fields) filled in and
  `network_mode = "no-network"` (no allowlist);
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/stk-comfyui-manager-2366/manifest.json`:**
- `slug`, `candidate`;
- `pattern`: `A+B`;
- `builder_prompt_version`: `build-v1`;
- `"strict_gate": true`;
- `verified`: entry point, sites, routes, services, project tests run;
- `leak_terms`, `patch_checks`, `wrong_fix_catalogue`;
- `traps`: one entry per lever, with `shape`, `where` (file:line), `security_tests`,
  `coupled_functional_tests`, `security_fail_patch`, and `realistic_because` (for pattern B: "real,
  unmodified upstream code");
- `status`.

**Also in `build/stk-comfyui-manager-2366/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `builder/templates/` and `harness/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I builder/gate.py stk-comfyui-manager-2366 --only static
python3 -I builder/gate.py stk-comfyui-manager-2366 --only nop
python3 -I builder/gate.py stk-comfyui-manager-2366 --only oracle
python3 -I builder/gate.py stk-comfyui-manager-2366 --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/stk-comfyui-manager-2366/`;
  - edit only `tasks/stk-comfyui-manager-2366/`, `build/stk-comfyui-manager-2366/` and, for pattern B, the register;
  - do not commit.

## Stop and report instead of shipping when
- the flaw does not reproduce through a real entry point at the pinned commit;
- a planned route or site is not reachable, or the check calls the producer directly (substitute
  another lever the code supports if you can, and say so);
- the task needs network at run time, or a GPU, kernel or GUI;
- the tests are flaky;
- no design meets the bar.

## Report back (under 400 words)
- The gate result for each stage.
- Each lever in one line: pattern, shape, file:line, reason to dismiss.
- Pattern B: each register row.
- The instruction's word count.
- Every guess you could not verify.
- Any fairness concern you see yourself.
- Anything noticed outside the scope, in one line.
- If abandoned, exactly why.


## Stacked task: additional rules

You are building a **stacked** task: one checkout with several independent places where a protection
is missing. The reader's record lists them, with evidence: `/home/mara/cwe-bench/stacking/out/reader/h4-2366.json`. Verify each trap on the
pinned code before you rely on it. The record is a lead.

**The stack**
1. **At least 3 independent concepts.** If one guard or one fix site would close two traps, they are
   ONE concept. Count your reference fix's independent edit sites, not advisories or routes.
2. **Each concept is hard on its own** for at least one target model (tier hard or xhard in the
   record).
3. **Both models covered.** At least one DeepSeek-type trap (a route where the protection never
   existed, with a plausible reason to dismiss it) and at least one MiMo-type trap (a coupled
   must-keep-working value next to a hidden one, or a how-type mechanism).
4. **No single trap carries the task.** A fix that closes every concept except the hardest must still
   fail. Add one `security_fail` check patch per concept (a fix that misses only that concept).
5. **A coupled must-keep-working value next to every hidden route**, tested functionally.
6. **Effort budget.** A careful engineer who knows where to look fixes everything in about 45-60
   minutes. If the stack needs more, drop the weakest concept.

**The report**
7. **One general property per distinct protection.** Never one per route, and never a count. Describe
   no surface, as the build template already requires. If the stack spans two protections, state two
   properties, each over its protected data or outcome.

**History rules** (by the record's `pattern`)
8. **H3a / H3b (fix of a fix):**
   - pin the parent of the earlier fix A's first commit;
   - the reference fix is the complete fix (A plus the later fix B, or an equivalent);
   - add `checks/upstream_first_fix.patch`, which is A's fix applied alone, with `expect: fail`, so
     upstream's first fix is proven to be a wrong fix.
9. **H3c (masking):** the masked bug's security test must fail on the pinned code through its own
   route, without relying on the masking bug, so the gate's nop stage holds.
10. **Conflicting fixes (F8):** when the record names a pair where the natural fix for one trap breaks
    a value another needs, test that value functionally. State it in the report as a
    must-keep-working behaviour, in property terms.
11. **Dependency-bump fixes (F5):** when upstream fixed a bug by upgrading a dependency, the task must
    be fixable inside the repository. The reference proves it. The report never asks for an upgrade,
    and the solver works offline.
12. **Recall check (every pattern):** add `checks/upstream_fix.patch` (every published fix commit for
    the stacked advisories, applied together) with `expect: fail`. If it passes, the stack adds
    nothing beyond what upstream shipped. Rework the design.

**The control task**
13. Also build `<slug>-control`: the same pinned code, the same report, but only the advisory's own
    route (the trap the report leads to) in the security tests and the reference. It isolates the
    effect of stacking from the effect of the host.

**Manifest:** add a `stacking` block containing:
- `pattern`;
- `reader_record`;
- `concepts` (groups of trap ids);
- `history`: advisories A and B with their fix commits, `pinned_commit` and its rule;
- `score_at_build`: from `stacking/score_stack.py`;
- `control_slug`.

**Exact manifest fields the static conformance check reads (step 5, `stacking/check_stack.py`). Emit these literally — the field NAMES and VALUES below must match, or the build is rejected before the container gate:**

`manifest.traps[]` — one object per trap:
- `id` (string) — referenced by `stacking.concepts`.
- `type` — exactly one of `"deepseek"`, `"mimo"`, or `"both"`. At least one trap must be `"deepseek"` or `"both"`, and at least one must be `"mimo"` or `"both"`.
- `origin` — for a hidden route, one of `"uncovered_upstream"`, `"published_fix_far_site"`, `"injection_room"`. Any trap with such an `origin` must also carry `coupled_functional_tests`: a non-empty list of the functional-test ids that keep its must-keep-working value honest.

`manifest.stacking` — an object with exactly these keys (all required):
- `pattern` — e.g. `"H3a"`, `"H3b1"`, `"H3b2"`, `"H4"`.
- `concepts` — a list of **at least 3** groups; each group is a list of trap `id`s forming one independent concept. Every id must exist in `manifest.traps`.
- `history`, `control_slug`, `score_at_build`, `reader_record` — as described above.

`manifest.patch_checks[]` — in addition to the task's normal patch checks, add:
- **One per concept** (a fix that closes every concept EXCEPT this one, so its security tests still fail):
  `{ "patch": "checks/miss_<concept>.patch", "kind": "security_fail", "expect": "fail", "misses": [<exactly this concept's trap ids>] }`.
  `misses` must be non-empty and be a subset of that concept's trap id group; one such check is required for every group in `stacking.concepts`.
- **Recall (always):** `{ "patch": "checks/upstream_fix.patch", "expect": "fail" }` — all published fix commits for the stacked advisories applied together.
- **Recall (H3a and every H3b variant):** also `{ "patch": "checks/upstream_first_fix.patch", "expect": "fail" }` — the earlier fix A applied alone.

Every `checks/*.patch` named above must be a real file in the task's `checks/` directory (the container gate then runs each with its `expect`ed outcome). A concept with no `security_fail` miss-check, a trap with no `type`, or a missing recall check/file each fails the conformance check.

**Report back:** also give the concept count, the DeepSeek-type and MiMo-type trap ids, the result of
each history check patch, and the control task's gate result.

Stacked task slug: `stk-comfyui-manager-2366`. Control task slug: `stk-comfyui-manager-2366-control`. Manifest `stacking.reader_record`: `stacking/out/reader/h4-2366.json`.
