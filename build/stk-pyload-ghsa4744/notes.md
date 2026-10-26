# stk-pyload-ghsa4744 — build notes

## Fairness fix 2026-10-24 (AUDIT-FIX-20261024.md)

One test was a test-fault: `security/test_startup_location.py::
test_startup_does_not_adopt_saved_temporary_download_folder` read the folder back from the saved
`settings/pyload.cfg`. A correct fix that drops a saved temporary-area value when the
configuration is loaded (in memory) leaves that file untouched under `--dry-run`, so it failed
although the service never uses the value. The reference passed only because its reset calls
`config.set`, which saves the file immediately.

- `tests/support/harness.py`: added `reported_storage_folder(proc)`, which reads the folder the
  started service reports it uses (the product's own `Storage directory:` log line; ANSI escapes
  stripped). `saved_storage_folder` is kept for the functional tests that legitimately assert a
  saved value.
- `tests/security/test_startup_location.py`: `_assert_not_inside_temp` now asserts the reported
  effective folder is outside the temporary area; the "nothing was created inside it" assertions
  are unchanged.
- `instruction.md` and `solution/fix.patch` are unchanged (as the audit requires).
- Verified locally with the pinned tree (19 security failures, 12 functional passes), the
  reference (31 passes), and an in-memory-drop variant that leaves the saved file at the bad
  value (5/5 start-up security tests pass). The check-patch matrix matches the manifest exactly:
  miss_core 7, miss_plugin 2, miss_storage 10, upstream_first 14, upstream_fix 7,
  wrong_option_names 2, reads_only 19, check_after_set 5, api_only_location 5,
  refuse_all 6 functional, overbroad_temp 5 functional; hardening and alternative_fix 31/31.

- Start (pipeline): 2026-10-23T08:07:18Z (this build session; a previous attempt at 01:19Z left
  notes and check patches that were not reused — its patches were `diff -ruN` output with bytecode
  noise and could not be applied with `patch -p1`)
- Build work started: 2026-10-23T08:07Z
- End: 2026-10-23T09:21Z

## Levers (one line each)

1. **T1 — core authority (pattern A, the advisory route, type both).** A non-admin account holding
   only the settings permission writes the reconnection program through the settings API and the
   download engine executes it later (`src/pyload/core/api/__init__.py:207-210`,
   `src/pyload/core/managers/thread_manager.py:157-199`). Reason to dismiss: settings users are meant
   to change settings, and a configured program has to exist on disk.
2. **T4 — the same list, the real option names (pattern A, uncovered upstream, type deepseek).** The
   published list names `webui.ssl_cert`/`webui.ssl_key`; the product declares
   `ssl_certfile`/`ssl_keyfile` (`default.cfg:39-40`), so the certificate options stay writable. The
   property ("settings that select a program, the served endpoint, certificate material or
   credentials") covers them; a guard that copies the plausible names guards nothing. Reason to
   dismiss: certificate paths and proxy credentials do not execute code. **How-type**: a shape a
   plausible check mishandles.
3. **T2 — download folder at the settings write (pattern B, the second advisory's route, type mimo).**
   The existing dangerous-location list covers the package and user directories only; the server's
   own temporary working area (session store, bytecode cache) is missing
   (`src/pyload/core/api/__init__.py:223-232`, `src/pyload/core/__init__.py:55,116-122`,
   `src/pyload/webui/app/__init__.py:90-101,113-119`). Must resolve the value, not compare text.
   Coupled must-keep-working: an ordinary folder beside the area or sharing a name prefix stays
   accepted. Reason to dismiss: a blocklist already exists and the temporary area looks like scratch
   space. **How-type**: coupled value + over-hardening.
4. **T3 — the second copy at start-up (pattern B, uncovered upstream, type deepseek).** The same
   incomplete list is implemented again at `src/pyload/core/__init__.py:141-152`, so a folder supplied
   on the command line or restored from saved configuration is adopted. Neither published fix touches
   the file; current upstream (4a6106a7) still has the incomplete list there. Reason to dismiss: only
   reached from the command line or the stored configuration, both operator-controlled. **How-type**:
   a second implementation / route where the protection never existed.
5. **T5 — the plugin branch (pattern A far site, published-fix far site, type deepseek).** The plugin
   branch of the same write applies no authority check
   (`src/pyload/core/api/__init__.py:243-244`) and the scanner options reach `subprocess.Popen`
   (`AntiVirus.py:33-34,46-47,75`). Reason to dismiss: add-on options belong to the add-on, the
   scanner is opt-in, and the advisories are phrased around core settings.

Concepts: `[T1,T4] [T2,T3] [T5]` (three independent guards: the core option list, the folder rule,
the plugin option list). DeepSeek-type: T3, T4, T5. MiMo-type: T2.

## Stacking

- Pattern H3a. Pin = first parent of fix A: `git rev-parse f5e284fcdfea^` =
  `52f29bc5f088c03940dcb03cf3c95a6bc831f771`; fix B (`c4cf995a2803`) is 42 commits later with A as
  an ancestor. The reference is the complete fix (A + B) plus the folder rule at both sites, with
  the certificate option names corrected.
- `score_at_build` from `stacking/score_stack.py`: **0.075** (P_fail3 DeepSeek 0.66, MiMo 0.114;
  score without the hardest concept 0.003, flagged `single-trap-carries`). The reader's model
  predicts DeepSeek failing 3/3 and MiMo often solving; the added T4 shape and the
  operator-side start-up lever are not in that model.

## What was verified (local, before the container gate)

- The flaw reproduces through the real entry points at the pin: POST `/api/set_config_value` with the
  product's own Basic-auth path as a non-admin settings account changes the reconnection program,
  the certificate/key options, the proxy credentials, the scanner program and arguments, and the
  download folder; `python -m pyload --dry-run --storagedir <tempdir>/...` and a configuration file
  saved earlier both adopt a folder inside the runtime area.
- Local matrix (fresh pinned tree per row, both suites): reference 19/19 security + 12/12 functional;
  `alternative_fix` and `hardening` 19/19 + 12/12; `miss_core_settings` 7 security failures,
  `miss_plugin_settings` 2, `miss_storage_location` 10, all with functional passing;
  `api_only_location` 5, `check_after_set` 5, `wrong_option_names` 2, `reads_only` 19 — all with
  functional passing; `refuse_all` and `overbroad_temp` break functional only; `upstream_first_fix`
  14 security failures (functional pass); `upstream_fix` 7 security failures (functional pass).
- Control task (`stk-pyload-ghsa4744-control`): reference = corrected fix A; 4 security tests, all
  failing on the pin and passing under the reference; 12 functional pass in both. Its own matrix:
  `partial` 4 security failures, `reads_only` 4, `refuse_all` functional only, `hardening` and
  `alternative` 1.0.
- The project's own runnable tests at the pin: `tests/test_skeleton.py` and
  `tests/test_mega_nz_folder.py` pass and are included in the functional group; `tests/test_parse.py`
  is stale at the pin and is not included.

## Container gate (this build)

- `static` PASS (only the blind patch, which run_blindfix writes later, is absent).
- `nop` PASS: 19 security tests fail on the untouched pin, 12 functional tests pass.
- `oracle` PASS: three runs, reward 1.0 each, identical security/functional results.
- `patches` PASS: every listed check behaved as declared — `miss_core_settings` 7 security failures,
  `miss_plugin_settings` 2, `miss_storage_location` 10, `upstream_first_fix` 14, `upstream_fix` 7,
  `wrong_option_names` 2, `reads_only` 19, `check_after_set` 5, `api_only_location` 5 (all with
  functional passing); `refuse_all` 6 functional failures, `overbroad_temp` 5 functional failures;
  `hardening` and `alternative_fix` 1.0. The blind check is deferred to run_blindfix.
- Control task (`stk-pyload-ghsa4744-control`, reference = corrected fix A): `static` PASS, `nop` PASS
  (4 security fail, 12 functional pass), `oracle` PASS (3 runs, reward 1.0, identical), `patches`
  PASS (`partial` 4 security failures, `reads_only` 4, `refuse_all` 6 functional failures,
  `hardening` and `alternative` 1.0; blind deferred).

## What could not be verified / corrections to the reader record

- Fix A references `flask` without importing it; the import arrives in an intermediate commit before
  fix B. Both recall patches carry the import, otherwise the code cannot run and every functional
  test fails. This is noted in `manifest.stacking.history`.
- The advisory's code-execution chain relies on the session backend deserialising a planted file.
  That dependency behaviour was not reproduced and is not needed: the tests observe that the download
  folder never lands in the runtime area, not deserialisation. No test depends on the session
  backend's format.
- T5 is recorded as `published_fix_far_site`, not `uncovered_upstream`: the later published fix B
  does guard the scanner options, so only fix A leaves it open.
- The reader's T4 share of the T1 fix site is real (one option list), so T1 and T4 are one concept;
  the reader's T2 and T3 are one guard (one shared folder rule, two call sites), so they are one
  concept. The manifest therefore has three concepts, each carried by a hard-or-xhard trap for
  DeepSeek.
- Windows case-folding in the blocklist is kept in the reference but not exercised (Linux verifier).

## Out of scope, noticed only

- `get_config_dict` carries no permission decorator at the pin, and `upload_container` joins a
  caller-supplied file name into the folder. Neither is tested or built on here.
