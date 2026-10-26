# stk-nova-ghsaxc4g build notes

- Original build (first pass): 2026-10-22T19:15:37Z – 2026-10-22T21:02:00Z.
- Reconstruction and verification of the deliverables: from 2026-10-22T22:13:36Z.
- Track: stacked (H3a). Pattern: A+B. Slug: `stk-nova-ghsaxc4g`. Control: `stk-nova-ghsaxc4g-control`.
- Pinned: `d335457f48d09c3d780c92413fe777030c1335e2` — verified by fetching fixes A and B: it is the
  direct parent of A (`2427d4a99bed35baefd8f17ba422cb7aae8dcca7`). B is
  `ce4b2e27be45a85b310237615c47eb53f37bb5f3`; `b0feaffdb2b1`/`d9577ce9f266` are the stable backports
  (not refs in the main repo).
- Reader record: `stacking/out/reader/h3-ghsa-xc4g-7vw8-924h.json` (verified on the pinned tree).

## Levers (one line each)

- **C1 = T1/T2/T7 — personality path (reported route; how-type, MiMo-type).**
  `nova/virt/disk/api.py:315-318`: the caller's path is joined under the mount root and written as
  root; `..`, a link inside the image, and a prefix-sibling spelling reach the host, and the parent
  directory is created before the write. One edit site (`_inject_file_into_fs`). Must keep working:
  absolute, relative, nested and in-root-link paths.
- **C2 = T3/T4 — fixed-path privileged directory operations (DeepSeek-type).**
  `nova/virt/disk/api.py:336-349` and `:357-362`: `root/.ssh` and `etc/network` are created,
  chowned and chmodded as root through link components before the file write. Reason to dismiss:
  the paths are constants, not user input. One concept because the reference applies the same
  check-before-mkdir to both fixed directories.
- **C3 = T5 — metadata file (DeepSeek-type).** `nova/virt/disk/api.py:322-327`: `meta.js` is a fixed
  name at the image root but can be a link in the image; content comes from user metadata.
- **C4 = T6 — two-way password copy (DeepSeek-type).** `nova/virt/disk/api.py:387-396`: `etc/passwd`
  and `etc/shadow` are copied from and back to the image as root through image links; the route is
  behind the optional `inject_password` feature.
- **C5 = S1 — injected legacy key file (DeepSeek-type, injection_room).**
  `nova/virt/disk/api.py:350-354`: the same key block is written a second time to
  `root/.ssh/authorized_keys2` through its own direct `tee -a`. The published A and A+B fixes never
  touch it, so both recall checks fail.

T9 (absolute paths and in-root links must keep working) is a must-keep-working contract, not a
counted trap. T4/T5 duplicate T3's reason to dismiss but are real published-fix sites, so they are
kept as sites/concepts and covered by the same property.

## Verified

- Pinned tree reproduced: 13/13 security tests fail and 10/10 functional pass on the pinned+injected
  copy (dev image, `--network none`).
- Reference fix: 13/13 security, 10/10 functional (three oracle runs; see gate).
- All 14 executable check patches reproduce the declared outcome in the dev image:
  - `sf-personality-only` 8 security failing, 0 functional;
  - `sf-lexical-only` 10 security failing, 0 functional;
  - `sf-check-after-mkdir` 1 security failing (the directory side effect), 0 functional;
  - `sf-no-personality` 5 security, `sf-no-key-dirs` 3, `sf-no-meta` 1, `sf-no-password` 3,
    `sf-no-sibling` 1; functional 0 failing for each;
  - `upstream_first_fix` (A alone) and `upstream_fix` (A+B) 1 security failing each (the legacy key
    file); 0 functional;
  - `ff-refuse-all` 10 functional failing; `ff-refuse-absolute` 3 functional failing;
  - `pass-alt` (realpath) and `pass-hardening` reward 1.0.
- The exact published fixes were read: A adds `_join_and_check_path_within_fs` with
  `os.path.realpath` and applies it at the file, metadata, key, net and password sites; B changes the
  same helper to `utils.execute('readlink', '-nm', ..., run_as_root=True)`. A/B do not add the
  rootwrap filter; the reference does, as a source change needed for the privileged resolver.
- The pinned tree has no regression test for this area: A adds the first ones to
  `nova/tests/test_virt.py`; at pinned that file has no disk-injection test.
- `stacking/check_stack.py stk-nova-ghsaxc4g`: conforming (5 concepts, pattern H3a).
- Gate: static fails only on the expected missing blind pass patch (written after this build).
  nop PASSED (security 0/13, functional 10/10). oracle PASSED (3 runs, reward 1.0, identical
  results). patches: all 14 executable checks behave as declared, run in three invocations
  because a Harbor `no-network` capability probe flaked twice under the shared-VM load (an
  infra classification, not a task result): the stage is resumed from the failed check. The
  gate cannot parse the shipped manifest's check_stack `expect:"fail"` entries (see below), so
  the patches stage is run on the executable subset (the same entries without the `fail` form).
  Results are in `build/stk-nova-ghsaxc4g/gate_report*.json` and the `chk-*` job dirs.
- Control (`stk-nova-ghsaxc4g-control`): static fails only on the missing blind patch;
  nop PASS (security 0/5, functional 10/10); oracle PASS (3 runs, 1.0); patches PASS (7/7:
  sf-no-personality 5 security fail, sf-check-after-mkdir 1, sf-lexical-only 2, ff-refuse-all
  10 functional fail, ff-refuse-absolute 3 functional fail, pass-alt 1.0, pass-hardening 1.0).

## Injected sibling

The published A+B fix closes every real route in this file, so the stacked recall rule
(`upstream_fix` must fail) could not be met with real code alone. I kept the maintainer-style
compatibility write to `authorized_keys2` (the legacy protocol-2 key file) in the same key-injection
path. It has no deceptive naming, is reachable only through the real key-injection entry point, is
covered only by the task's general property, and is not touched by the published fix. It is the only
change from the pinned checkout.

## Fairness notes

- Absolute personality paths are a normal API use (rebased by `lstrip('/')`); the report says so and
  the functional suite keeps them working.
- Images legitimately contain in-root links; the functional suite keeps a relative in-root link
  working, and `pass-alt` (unprivileged `os.path.realpath`) is accepted as a correct fix.
- The root-only-directory part of B is not observable under the verifier's uid-1000 test process:
  the sandbox and its links are owned by the test user, so both `realpath` and `readlink -nm`
  resolve them. The tests grade the behaviour (links resolved / not resolved), not the implementation
  choice, as the reader's fairness note requires.
- The rootwrap filter added by the reference is not exercised because `utils.execute` is stubbed.

## Could not verify / tooling mismatches

- The upstream stable backports `b0feaffdb2b1` and `d9577ce9f266` could not be fetched from the
  main repo (stable-branch refs), so their exact content was not read.
- `builder/gate.py` (2026-10-21) accepts only `expect` values `security_fail`, `functional_fail` and
  `pass`; `stacking/check_stack.py` (2026-10-22) requires recall/miss entries with `expect: "fail"`.
  The manifest carries both forms: the executable `security_fail`/`functional_fail`/`pass` entries
  first, then the `kind: security_fail, expect: fail, misses: [...]` and recall entries that
  check_stack reads. The gate's `patches` stage therefore stops at the first `expect: "fail"` entry
  with "unknown expect 'fail'"; every executable entry before it was run by the gate. This is a
  tooling schema mismatch, not a task failure.
- `run_blindfix.sh` extracts the project from `/app`, while the Frontier delivery format puts it in
  `/workspace`. The environment Dockerfile therefore keeps a pristine copy at `/app` (same content,
  added after the fresh one-commit git baseline) so the blind-fix step can run; the agent still
  works in `/workspace` and the verifier restores only `/workspace`.
- No project test for the affected area exists at the pinned commit, so none is run.

## Container-gate patch outcomes (main task, executable set)

| patch | expected | gate result |
|---|---|---|
| sf-personality-only | security_fail | 5/13 security pass (8 fail), 10/10 functional |
| sf-lexical-only | security_fail | 3/13 security pass (10 fail), 10/10 functional |
| sf-check-after-mkdir | security_fail | 1 fail: test_personality_directory_side_effect_is_refused |
| sf-no-personality | security_fail | 5 fail: the personality tests (T1/T2/T7) |
| sf-no-key-dirs | security_fail | 3 fail: 2 `root/.ssh` + 1 `etc/network` (T3/T4) |
| sf-no-meta | security_fail | 1 fail: test_metadata_symlinked_file_is_refused |
| sf-no-password | security_fail | 3 fail: the password-copy tests |
| sf-no-sibling | security_fail | 1 fail: test_ssh_key_second_key_file_is_refused |
| upstream_first_fix | security_fail | 1 fail: test_ssh_key_second_key_file_is_refused |
| upstream_fix | security_fail | 1 fail: test_ssh_key_second_key_file_is_refused |
| ff-refuse-all | functional_fail | 10/10 functional fail |
| ff-refuse-absolute | functional_fail | 3 functional fail (absolute, nested, in-image link) |
| pass-alt | pass | reward 1.0 |
| pass-hardening | pass | reward 1.0 |

Two Harbor runs were cut by the shared-VM `no-network` capability-probe flake
(`ValueError: network_mode='no-network' is not supported`, an infra classification); the stage was
resumed from the failed check each time, so every check above ran to a real result.

## Reconstruction (2026-10-23)

The `tasks/` trees and the build manifest were rebuilt from the verified scratch snapshot under
`~/.tb-graders/cwe/work/stk-nova-ghsaxc4g/` (`app` = pinned+injection, `app_oracle` = reference,
`htests` = the hidden suites, `gen_checks.py` = the check generator).

- `solution/fix.patch` was regenerated from `app` -> `app_oracle`: the archived copy held the
  first-pass, personality-only fix and did not close the far sites. The new patch reproduces the
  oracle tree byte-for-byte.
- All 14 check patches were regenerated with `gen_checks.py`; every one reproduced byte-identically
  to the archived set.
- `manifest.patch_checks` is now one entry per concept carrying `expect: "security_fail"` +
  `kind: "security_fail"` + `misses`, and the two recall checks carry `expect: "security_fail"`.
  That is the single schema both `stacking/check_stack.py` and `builder/gate.py` accept; the
  archived manifest's trailing `expect: "fail"` duplicates (which `gate.py` cannot parse) are gone.
- `environment/Dockerfile` re-adds the `/app` copy of the workspace that `run_blindfix.sh` extracts.
- The control `stk-nova-ghsaxc4g-control` was rebuilt from the same pin and the same report, with
  only the reported personality route in its security suite (5 tests), the same 10 functional tests,
  and `sf-personality-only.patch` as its reference.

## Gate results (reconstructed tree, 2026-10-23 UTC)

- `static` (main and control): fails only on `manifest.patch_checks has no expect=pass patch with
  kind='blind'` — the blind pass patch is produced later by `run_blindfix.sh`, as the build prompt
  allows. No other problem.
- `nop` main: PASS, security 0/13 (every security test fails on the pinned+injection tree),
  functional 10/10.
- `oracle` main: PASS, 3 runs, reward 1.0 each, identical.
- `patches` main: PASS, 14/14 declared outcomes:
  sf-personality-only 8 security fail; sf-lexical-only 10; sf-check-after-mkdir 1
  (`test_personality_directory_side_effect_is_refused`); sf-no-personality 5; sf-no-key-dirs 3;
  sf-no-meta 1; sf-no-password 3; sf-no-sibling 1; upstream_first_fix 1; upstream_fix 1 (all with
  0 functional fail); ff-refuse-all 10 functional fail; ff-refuse-absolute 3 functional fail;
  pass-alt 1.0; pass-hardening 1.0.
- `nop` control: PASS, security 0/5, functional 10/10. `oracle` control: PASS, reward 1.0.
  `patches` control: PASS, 7/7 (sf-no-personality 5 security fail, sf-check-after-mkdir 1,
  sf-lexical-only 2, ff-refuse-all 10 functional fail, ff-refuse-absolute 3, pass-alt 1.0,
  pass-hardening 1.0).
- Infra: the shared-VM Harbor `no-network` capability probe (`ValueError: network_mode='no-network'
  is not supported by EnvironmentType.DOCKER`) aborted stages several times while the host load
  average was above 100. Each stage was resumed: a completed check is identified by its Harbor job's
  `verifier/results.json`, and the pending-only manifest was swapped in and the shipped manifest
  restored after each attempt. No task file was weakened; the final shipped manifest is the one
  `check_stack` verifies. The same probe flake hit the first-pass build on 2026-10-22.
