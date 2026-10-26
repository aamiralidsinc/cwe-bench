# stk-avideo-ghsawc3f — build notes

Started: 2026-10-22T22:19:19Z (first build job start). Re-assembled and re-gated from
2026-10-23T03:03Z; finished 2026-10-23T05:48Z.

## What the task is

AVideo (WWBN/AVideo), pinned at `75ce8a579a58c9d4c7aafe453fbced002cb8f373`, the parent of the
earlier published fix commit (`25c8ab90269e`, GHSA-pmj8-r2j7-xg6c); the later
`c1cfa2bea8a3` (GHSA-wc3f-xc32-435f) extends the same sanitizer. Some installations run a separate
media host that starts FFmpeg jobs on instructions the main site sends as encrypted payloads.

## Levers (one line each)

- **T1 — command separator (advisory route, both; concept 1).** The command-text blacklist leaves a
  single `&`, and the command is embedded in a double-quoted `sh -c` string.
  `plugin/API/standAlone/functions.php:65,70` -> `objects/functionsExec.php:658`.
- **T2 — expansion shape (MiMo, injection room; concept 1).** The blacklist removes
  single-character separators but not `$`, `(`, `)` or newline; the wrapped `sh -c` still expands
  them. `plugin/API/standAlone/functions.php:70`, `objects/functionsExec.php:639,658`.
- **T3 — completion-notification values (DeepSeek, uncovered upstream; concept 2).** Two payload
  values are concatenated raw beside the job command while their neighbours are escaped.
  `plugin/API/standAlone/ffmpeg.json.php:411`.
- **T4 — process-lookup value (DeepSeek, uncovered upstream; concept 3).** The list and
  running-state modes pass a raw client value into a single-quoted `grep` argument.
  `ffmpeg.json.php:221,341` -> `functions.php:109,112`.
- **T5 — restream user identifier (DeepSeek, uncovered upstream; concept 4).** The identifier is
  substituted into the log path, which is appended unquoted to the executed command.
  `plugin/Live/standAloneFiles/restreamer.json.php:318,720,723`.
- **T6 — coupled legitimate values (MiMo, published fix's far sites).** Legitimate commands end
  with their own redirect and carry quoted paths; a blanket ban or quote stripping refuses or
  mangles them. `restreamer.json.php:604,660,720`, `objects/functionsFFMPEG.php:498`.

Concepts (reference edit sites): C1 = T1+T2 (sanitizer + execution sink), C2 = T3, C3 = T4, C4 = T5.
DeepSeek-type: T3, T4, T5. MiMo-type: T2, T6.

## Verified

- `static`: PASSED for the task and the control (the `blind` pass patch is declared but its file is
  produced later by run_blindfix, as the build prompt allows).
- `stacking/check_stack.py`: conforming, 4 concepts, pattern H3a.
- Per-check patch apply: every `checks/*.patch` applies cleanly to the pinned tree.
- The pinned commit is the first parent of fix A (`git rev-parse 25c8ab90269e^ == 75ce8a579...`);
  the two fix commits touch only `plugin/API/standAlone/functions.php`, so the pinned tree carries
  no advisory regression tests.
- Route reproduction on the pinned tree: all five marker shapes (T1, T2 substitution, T2 newline,
  T3 both fields, T4 both modes, T5) are reproduced by the gate's nop stage.

## Gate results (this rebuild)

- `static` PASSED for `stk-avideo-ghsawc3f` and `stk-avideo-ghsawc3f-control`.
- `nop` PASSED: 8/8 security tests fail on the pinned tree; 57/57 functional tests pass
  (3 media + 2 lookup + 2 restream + 50 project).
- `oracle` PASSED: three runs, each reward 1.0 and identical test outcomes.
- `patches` PASSED, per check:
  - `miss_command_shell` 0.625 (3 security failing), `miss_notify` 0.75 (2),
    `miss_keyword` 0.75 (2), `miss_restream` 0.875 (1), `miss_callback_only` 0.875 (1)
    — all `security_fail` with every functional test passing;
  - `upstream_fix` 0.375 (5 security failing, 0 functional failing) and
    `upstream_first_fix` 0.25 (6 security failing) — both recall checks `security_fail`;
  - `hardening` 1.0 and `alt_fix` 1.0 — pass;
  - `func_overbroad` 0.0 with 1 functional failure; `refuse_all` 0.0 with 3 functional failures
    — the two `functional_fail` checks.
  The recall chunk hit Harbor's known `network_mode='no-network'` startup probe flake on its first
  attempt; the per-chunk retry passed on the second attempt (evidence:
  `evidence/rerun-gate-patches-*.log`).
- Control task `stk-avideo-ghsawc3f-control`: `static` PASSED; `nop` PASSED (4/4 security tests
  fail, 54/54 functional pass); `oracle` PASSED after one infra retry (reward 1.0); `patches`
  PASSED — `miss_sanitizer` 0.0 with 4 security failures, `func_overbroad` 0.0 with 2 functional
  failures, `refuse_all` 0.0 with 4 functional failures, `hardening` 1.0.

## Rebuild decision

The earlier run left every lever, test, patch and gate artifact on disk but the task directory
itself was missing. Tests were recovered byte-identically from the verifier image
(`avideo-tests:latest`, `/tests`), the environment/config from the control task, and the reference
fix from the recovered `patches/fix.patch`.

One change was required for the recall checks: the published fixes A+B strip `&` inside quoted
values, so the upstream-fix recall also broke the media-path quoted-URL functional test. The
stacking conformance check requires every recall patch to be `security_fail` (a security failure
with all functional tests passing), so the duplicate media-path quoted-URL functional test was
removed. The must-keep-working quoted-URL contract is still tested functionally on the restream
route (`RestreamFunctionalTest`), which is unaffected by the published sanitizer and which an
over-broad fix still breaks. The existing separate `func_overbroad` check was changed from
"strip every separator" to "strip quoting characters", so it still fails a functional test
(quoted paths with spaces) without making the recall check fail functionally.

## What I could not verify

- Whether a low-privilege streamer can obtain a token in a stock deployment: the restream route is
  exercised with a token the harness's platform stand-in accepts, which is the product's normal
  main-site contract.
- The reader's note about a destination URL host containing `&` was not exercised; the T5 test uses
  the user identifier only, and the restream functional test covers the quoted stream URL.

## Notes

- Pattern B register rows for T3, T4, T5 are present in `build/audit/uncovered-routes.tsv`
  (appended by the earlier run; T5 is still present on current upstream master, T3/T4 were fixed
  later by unrelated edits).
- Read-only look at upstream master (2026-10-22): T3 and T4 have since been fixed by unrelated
  later edits; T5 is still present.
