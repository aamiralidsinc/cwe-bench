# stk-comfyui-manager-2366 — build notes

- Start (UTC): 2026-10-22T22:13:08Z (rebuild after the 22:12 workspace reset; the original
  19:16–21:19 build's task tree and manifests were reconstructed from its retained scratch
  artifacts and transcript, then re-verified end to end).
- End (UTC): 2026-10-23T01:00:00Z

## What the task is

ComfyUI-Manager keeps its own trusted state (the security level that gates remote operations,
preferences, saved environments, work scheduled for a later start) under `<user>/default/ComfyUI-Manager`,
a folder ComfyUI's user-file endpoints can write. A client that can reach those endpoints plants
state there; Manager then trusts it. The pinned tree is the direct parent of the published fix
`e44c5cef58fb4973670b86433b9d24d077b44a26`.

## Levers (one line each)

- T1 (landing, base, not counted): `glob/manager_core.py:217/:229/:1696/:1739` — state is stored in
  and read from the public folder; `glob/manager_server.py:89` gates routes on the planted level.
- T2 (Pattern A far site, base): `prestartup_script.py:88/:519/:796` — the startup hook computes the
  same path a second time and replays whatever queue it finds; reason to dismiss: "it only replays a
  queue Manager itself wrote".
- T3 (concept 1, DeepSeek-type): `glob/manager_core.py:1739/:1766` — on a host without the protected
  capability the level is taken from the public folder (or defaults to `normal`); reason to dismiss:
  "once the folder has moved, old hosts are out of scope".
- T4 (concept 1 coupled value, MiMo-type): `glob/manager_core.py:1696`, `glob/manager_server.py:1377`
  — forcing the strongest level must not be persisted over the operator's saved value and must not
  block ComfyUI self-update.
- T5 (concept 2, DeepSeek-type, Pattern B): `prestartup_script.py:91/:574/:604`, `cm-cli.py:1076` —
  a scheduled restore planted in the public folder is consumed at start; the HTTP route that
  schedules it is already gated, which is the reason to dismiss. Still unguarded on upstream master.
- T6 (concept 3, DeepSeek-type, Pattern B): `prestartup_script.py:99/:126/:131/:505/:520`,
  `glob/manager_util.py:494` — the startup hook's own config loader and package-install lists change
  TLS verification, remapping, the blacklist and the package index used at start; reason to dismiss:
  "tuning knobs read before Manager core loads". Still ungated on upstream master.

Concepts counted by the stacking rules: [T3,T4], [T5], [T6]. T1+T2 are the landing/base protection
(T2's record tier is medium, so it is not counted as an independent hard concept).

## Verified locally (no target model was run)

- Pinned: 10 security tests fail and 6 functional tests pass.
- Oracle (`solution/fix.patch`, the published fix plus the T3/T4/T5/T6 work): all 16 pass.
- Control (`stk-comfyui-manager-2366-control`): pinned 4 security fail + 6 functional pass;
  its reference (the published storage fix with the old-host enforcement removed) 10/10 pass.
- Check patches, run locally against a clean pinned worktree (all match the manifest):
  - sf-no-protected-storage: 5 security fail, functional pass
  - sf-no-oldhost-trust: 2 security fail, functional pass
  - sf-no-restore-guard: 1 security fail, functional pass
  - sf-no-startup-config-guard: 2 security fail, functional pass
  - sf-reads-only: 1 security fail, functional pass
  - sf-crash: 2 security fail, functional pass
  - sf-capability-fail-open: 2 security fail, functional pass
  - ff-refuse-all: 3 functional fail
  - ff-persist-forced: 1 functional fail
  - pass-hardening: 16/16
  - pass-alt: 16/16 (different design: `__comfy_mgr` directory, inline migration, no migration module)
  - upstream_fix (recall): 3 security fail, functional pass. The unmodified published patch (kept as
    `checks/upstream_fix_published.patch`) fails the same three security tests **and** overwrites the
    operator's saved security level (one functional fail). Because the pipeline's `expect` vocabulary
    only admits a pure security miss for a recall check, `checks/upstream_fix.patch` is the published
    patch plus the minimal saved-level preservation; either form proves the stack leaves T5/T6 open.
  The same five control checks behave as declared (4 security fail / 1 security fail / 3 functional
  fail / 10-of-10 / 10-of-10).
- Every route was confirmed behaviourally on the pinned tree before the tests relied on it: HTTP
  install via a loopback dumb-HTTP git repository (marker from `install.py`), startup queue replay,
  scheduled restore clone, startup config loader (TLS bypass + package remap), and pip_auto_fix
  (loopback index hit counter).
- `present_in_latest`: checked `Comfy-Org/ComfyUI-Manager` master on 2026-10-22: the startup restore
  consumer and the separate startup config loader are still unguarded (T5, T6).
- Container gate (this run): static reports only the expected missing blind patch; nop PASSED;
  oracle PASSED (three runs). The patches stage PASSED all twelve checks on its third attempt (the
  first two died in the known Harbor egress-control kernel-probe flake that reports
  `network_mode='no-network' is not supported` under load; nothing about the task changed and the
  retries went green). That run used the unmodified published recall patch, which fails 3 security
  tests and 1 functional test. After the recall patch was given its minimal saved-level preservation
  (so the pipeline's `security_fail` vocabulary fits), the stage was re-run on the final manifest: it
  re-verified 8 of 12 checks before another egress-probe flake, and was then stopped to verify the
  changed check alone; `check`-targeted `gate.py --only patches` on the final recall patch PASSED
  (only three security tests fail, all functional pass). The other eleven check files are unchanged
  from the fully green run. The control task's gate results are recorded in its own notes.

## Harness note

`stacking/check_stack.py` was updated during this run (23:52Z) to read `security_fail` as the
failure vocabulary and a post-build normalizer now forces that value on recall checks. The manifest
matches it: `python3 -I stacking/check_stack.py stk-comfyui-manager-2366` reports
`conforming (3 concepts, pattern H4)`. The one consequence for this advisory is the recall patch:
the unmodified published fix also breaks a coupled functional value (it writes its forced level over
the operator's saved one), so `checks/upstream_fix.patch` carries the minimal saved-level
preservation on top of the published commits; the unmodified patch is preserved as
`checks/upstream_fix_published.patch` and is recorded in `recall_checks`.

Two test-harness details fixed during the rebuild: the host double must expose the legacy
`folder_paths.user_directory` attribute the startup module reads, and the hidden suites are staged
under `/home/agent/htests` (outside the agent's restored `/workspace`).

## Could not verify

- Whether the hidden tests' behaviour matches the real ComfyUI userdata endpoints end to end: the
  endpoint itself lives in ComfyUI core, outside this repository; the tests plant the state the
  endpoint could write and drive the real Manager entry points.
- The record's line numbers for a few traps differ by a few lines from the pinned checkout; the
  file-level sites were re-checked directly.
- Repository size in MB (not measured).

## Scope

Everything built here is within advisory 2366's own protection (state in the web-writable folder)
and the pinned commit. Nothing outside that scope was used.

## Reconstruction and re-gate (2026-10-23)

- Start (UTC): 2026-10-23T02:59Z. The build pipeline restarted this task after a workspace reset
  that removed `tasks/stk-comfyui-manager-2366*` and the build manifests. The tree was restored
  from the retained scratch worktrees (pinned `src`, fixed `oracle`, `variant`), the final hidden
  suites extracted from the verifier image built during the previous gate run, the recovered build
  transcript for `instruction.md`/`task.toml`/`environment/`, and the existing `build/checks/`.
- End (UTC): 2026-10-23T04:45Z.

`solution/fix.patch` was regenerated from the oracle worktree with the same command used before and
verified to reproduce the oracle files exactly; the control reference was regenerated with
`make_control_fix.py`. Both test suites and both manifests are byte-identical to the ones the
previous gate used.

Re-verified locally after the restore: pinned 10 security fail / 6 functional pass; reference
16/16; control pinned 4 security fail / 6 functional pass; control reference 10/10; all twelve
check patches and the control's five applied to a clean pinned worktree reproduce their declared
outcomes (see `check-local.log` / `control-check-local.log`). `python3 -I stacking/check_stack.py
stk-comfyui-manager-2366` reports `conforming (3 concepts, pattern H4)`.

Container gate after the restore: `static` reports only the expected missing `blind` patch (written
by the pipeline after this stage, not by the builder); `nop` PASSED; `oracle` PASSED (three runs);
`patches` PASSED: all twelve checks matched their declared outcome (seven security_fail, two
functional_fail, two pass at reward 1.0, one recall security_fail). Two infrastructure-only retries
(Harbor produced no trial under the shared VM load) restarted the stage; nothing about the task
changed and the third attempt went green.
