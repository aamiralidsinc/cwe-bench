# Build notes — stk-blender-mcp-787

## Times
- Start: 2026-10-26T02:19:39Z
- Stacked gate finished green: 2026-10-26T04:47Z
- End: 2026-10-26T05:04Z (stacked complete; control stages stopped by the session limit)

## Lever one-liners
- **T1 / concept 1 (Poly Haven attached files, advisory route)** — the model metadata's
  attached-file path is joined to the download folder and its parent is created before the
  write; relative traversal, absolute paths and the directory side effect must all be refused.
- **T2 / concept 1 (coupled value)** — legitimate attached-file keys carry subdirectories that
  the same loop creates for the glTF importer, so flattening to a basename or rejecting every
  key with a separator breaks a valid import.
- **T8 / concept 2 (Sketchfab archive name)** — the archive is written at a name built from the
  caller-supplied model identifier, before the handler's own zip-slip member guard.
- **T6 / concept 3 (Hyper3D temporary prefix)** — both generated-asset transports pass the
  caller-supplied `task_uuid`/`request_id` as the temporary file's prefix; `tempfile` treats a
  separator as a directory component. Random suffix means create-not-overwrite, which is the
  reason to dismiss it.

## Gate results (stacked task)
- static: PASS (2026-10-26T02:34Z).
- nop: PASS — 9 security tests fail on the pinned tree, 12 functional tests pass
  (6 hidden + 6 project), 2026-10-26T02:54Z.
- oracle: PASS — 3 runs of the reference fix, reward 1.0 each, 21/21 tests, identical results
  (2026-10-26T04:14Z). The stage's first attempt was cut by a `/tmp` inode spike on the shared
  VM (infra, verdict "infra"); the re-run used `TMPDIR` on the large disk.
- patches: PASS — all 11 check patches produced the declared outcome in the verifier:
  `abs-unchecked` 2 security fails; `check-after-makedirs` 2; `miss_concept_polyhaven` 4;
  `miss_concept_sketchfab` 2; `miss_concept_hyper3d` 3; `upstream_fix` 5 (recall: the published
  fix alone leaves T8 and T6 open); `functional-overbroad`, `global-abs` and `refuse-all` fail
  functional tests; `alt_correct_fix` and `hardening` score 1.0.

## Control task
- `stk-blender-mcp-787-control` has the same pinned code and a byte-identical `instruction.md`, a
  reference fix limited to the advisory route, and a security suite limited to the four
  advisory-route tests. Its static gate stage passes. Its nop/oracle/patches stages were started
  only after the stacked gate went green and could not finish before the shared-VM session limit:
  the Docker daemon was saturated (~200 concurrent containers from other build sessions) and the
  control's env compose build stalled for over 11 minutes. The control's reference, wrong-fix and
  nop outcomes were verified locally before the gate (10 hidden + 6 project tests; every check
  patch produced its declared outcome).

## Verified
- Pinned tree at `584e892695deb28d8f09b258db981006bbb1b229` fetched and read.
- `git fetch --depth 2` of the published fix shows its parent is the pinned commit exactly.
- The published fix `30a3308446cd8f81a9446e5a2ed657c0d8d86072` changes only the Poly Haven
  attached-file block (T1). The Sketchfab and Hyper3D sinks are untouched by it.
- Both non-advisory sinks reproduce through the add-on's real socket command protocol on Linux
  with `bpy`/`mathutils` stubbed and remote services answered in-process:
  the attack-named directory/file is created outside the operation's temporary area.
- Reference fix (published fix + fixed Sketchfab archive name + fixed Hyper3D prefixes) makes
  every security test pass and keeps every functional test passing (15 hidden + 6 project).
- Every check patch was applied to a fresh pinned tree and run both locally and in the verifier;
  the observed outcome matches the manifest declaration (`validate2.log`, `validate/summary.json`,
  and the gate job results under `~/.tb-graders/cwe/gate-jobs/stk-blender-mcp-787-chk-*`).
- Project test `test_set_texture_version_guard.py` passes on the pinned tree, the reference,
  the alternative and the hardening variant.
- `check_stack.py` reports conforming (3 concepts, H4); the control's instruction.md is
  byte-identical; both tasks pass the static gate.
- The current upstream HEAD still contains the Sketchfab archive-name sink and both Hyper3D
  prefix sinks (the Poly Haven attached-file block is fixed there).

## Could not verify / left out
- **T3** (the URL-derived Poly Haven main file name) is only escapable on Windows; on POSIX the
  last URL segment cannot contain a separator. Dropped as a tested lever.
- **T4** (Hunyuan `extractall`) and **T5** (Sketchfab member prefix comparison) do not show an
  outside write on Linux: CPython's `extractall` strips absolute and `..` member names, so the
  observable outcome is a sanitised extraction, not an escape. Dropped as tested levers.
- **T7** (`get_viewport_screenshot` filepath) is by-design socket code and the MCP server
  supplies the absolute path; kept only as a keep-working sibling (the adjacent-API wrong-fix
  check), never as a security route.
- No Blender binary is installed; the tests use an in-process `bpy`/`mathutils` stand-in. The
  add-on's panel/registration code is not exercised.
- The remote-service schemas are the shapes the handler reads, reconstructed from the pinned
  code; no live service was contacted.

## Scope note
Nothing outside advisory 787's protection (asset-download path confinement in this repository at
the pinned commit) was built on; the two extra sinks are the same protection in the same file.
