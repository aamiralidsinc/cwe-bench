# stk-yt-dlp-2714 — build notes

Start (UTC): 2026-10-26T02:26:05Z (pipeline start marker)
Build start (UTC): 2026-10-26T02:26:30Z
End (UTC): <filled after the container gate>

Stacked H4 task on yt-dlp/yt-dlp. Pinned `3ba1534fa3f55ddb599a891b544ec96e5a15f3cc`, which
`git rev-parse e578e265^` confirms is the direct parent of the published fix
`e578e265f7c6ca94a74b30e0d8d6196a4d19fb6a` ("Remove url, desktop and webloc from safe
extensions"). The pinned tree contains no regression test for this advisory: the published fix
adds no test, and `test/test_utils.py` only carries the earlier CVE-2024-38519 extension tests.

## Levers (one line each)

- **T1 (advisory route, both models).** `_UnsafeExtensionError.ALLOWED_EXTENSIONS`
  (`yt_dlp/utils/_utils.py:5211-5219`) still lists `desktop`, `url` and `webloc`, and
  `sanitize_extension` (`5224-5240`) accepts the last dot-component against that table; a download's
  own reported file type therefore names the output file. Reason to dismiss: none — this is the
  reported bug.
- **T2 (uncovered upstream, DeepSeek).** `_prepare_filename` (`yt_dlp/YoutubeDL.py:1518-1528`) only
  calls `replace_extension` when the evaluated name already ends with the conversion target, so with
  a requested conversion the download's own file type (`url`/`desktop`/`webloc`) stays as the written
  suffix and the extension policy is never consulted. Reason to dismiss: the target is a trusted
  user option that is about to rewrite the extension, so the raw suffix reads as a temporary name.
  The published fix does not reach it.
- **T4 (uncovered upstream, DeepSeek).** In a merged download the part name comes from
  `correct_ext` (`yt_dlp/YoutubeDL.py:3500-3513`) plus `prepend_extension`
  (`3526`/`3559`); the per-format file type becomes the final suffix and the prepend branch only
  slash-checks the infix (`yt_dlp/utils/_utils.py:2142-2151`), never the per-format extension.
  Reason to dismiss: merge-only, the parts look like temporary merge inputs, and the project's own
  tests document the prepend branch as intentional. The published fix does not reach it.
- **T5 (published-fix far site, MiMo).** Once `url`/`desktop`/`webloc` leave the shared allowlist,
  the shortcut writer (`yt_dlp/YoutubeDL.py:3392-3430`, table at
  `yt_dlp/utils/_utils.py:4618-4622`) raises through the same helper and the whole video aborts.
  The published fix adds a per-call allowlist derived from the shortcut table. Reason to dismiss:
  it is the feature itself, so refusing those suffixes reads as a regression, not a fix.
- **T6 considered and dropped (published-fix defect).** The published fix threads a new
  `_allowed_exts` keyword, which breaks the documented `--compat-options allow-unsafe-ext`
  monkeypatch (`yt_dlp/__init__.py:618-622`). It is a real defect and the reference repairs it, but
  the gate's recall check (`checks/upstream_fix.patch`, `expect: security_fail`) must leave every
  functional test passing, and the published fix cannot pass a functional test for that option.
  Dropping the lever keeps the recall check honest. No test covers the opt-out.

Concepts (one reference-fix edit family each): **C1 = [T1, T5]** (the allowlist data change plus
the shortcut writer's per-call exemption; T5 sits in C1 because the same edit breaks it, and its
miss-check is the `functional_fail` patch `miss_exemption.patch`), **C2 = [T2]** (conversion-target
validation), **C3 = [T4]** (merged-format validation). T2 and T4 each get a validation of their own
so that removing one leaves only that concept's security tests failing (verified locally).

## What was verified

- Every trap is reachable through the library's public `YoutubeDL.process_info` against a loopback
  video: pinned writes `title [id].url`, `.desktop`, `.webloc`, `title [id].en.webloc`, the
  conversion-target name and `merged [id].ff1.url`; the reference refuses each with the library's
  `DownloadError` and writes nothing.
- The published fix alone closes T1 only; T2 and T4 still write launcher files through it.
- The reference keeps the coupled values: ordinary downloads, a conversion target (the `.webm`
  name is kept), a merged download (`ff0.mp4`/`ff1.mp4`), the shortcut writer for all three
  documented kinds and the default option, unlisted prepend infixes (`exe`, `format_id`) and the
  documented extension vocabulary.
- The project's own tests for the affected area pass on the pin and under the reference:
  `python3 -m pytest test/test_utils.py test/test_YoutubeDL.py` → 143 passed. The one
  platform-skipped test (`test_windows_escaping`, `@unittest.skipUnless(os.name == 'nt')`) is
  deselected in the grading runner: the gate treats a skipped test as a non-pass, and it cannot
  run on Linux by design.
- Every check patch was applied to a fresh pinned copy and reproduced its declared outcome with the
  project's runner (counts include the 143 project tests):
  `miss_policy` 5 security fail / 0 functional; `miss_final_ext` 2 / 0; `miss_per_format` 2 / 0;
  `upstream_fix` 4 / 0; `miss_exemption` 0 / 4; `hardening` 1.0; `alternative` 1.0;
  `refuse_all` 26 functional fail; `crash_as_refusal` 4 security fail; `adjacent_api` 3 functional
  fail; `whole_value_extension` 1 security fail.
- `pipelines/stacking/3-build-gate/check_stack.py stk-yt-dlp-2714` → conforming (3 concepts,
  pattern H4); `common/builder/conformance_check.py` → conforming for the task and the control.
- Current upstream (`origin/master` fa9886678, read-only, checked 2026-10-26) still has both
  unprotected naming routes (T2, T4); the allowlist no longer lists the three launcher types.

## What could not be verified

- The two target models' pass rates; no trial was run (build prompt).
- The published fix's advisory body was not available; the summary used is the screener's
  "unsafe file-type/name restriction (CWE-641)" plus the fix diff, which is present in the clone.
- Whether a real extractor can supply a per-format `url`/`desktop`/`webloc` ext with a safe merged
  ext; reachability is proven at the download API, not through a shipped extractor.

## Reader-record discrepancies

- The record was read from `pipelines/stacking/out/reader-ds/h4-2714.json` (the `reader/`
  directory holds only H3 records); `manifest.stacking.reader_record` names the file actually used.
- The record's T2 says the table edit "cannot reach" the default `%(ext)s` substitution. With the
  published fix applied, `existing_video_file` calls `replace_extension` for the main file, so the
  plain route is in fact refused by the published fix. The genuinely uncovered T2 is the
  conversion-target branch used here.
- T6 was dropped for the recall-check reason above. The record's `unverified` note about T2/T3 also
  understated how much `process_info` covers.

## Scope note

Content-level concerns around the shortcut file body and verbatim subtitle bodies are outside this
extension-policy advisory and were not built on.

## Container gate

Run one stage at a time.

- static: PASSED (2026-10-26).
- nop: PASSED (2026-10-26T03:54Z) — 9/9 security tests fail on the pin, 166/166 functional pass
  (23 hidden + 143 project, after deselecting the Windows-only project test).
- oracle: PASSED (2026-10-26T04:24Z) — 3 runs, reward 1.0, identical results.
- patches: PASSED (2026-10-26T04:52Z) — all 11 declared checks matched: miss_policy 5 security
  fail / 0 functional; miss_final_ext 2/0; miss_per_format 2/0; upstream_fix 4/0;
  miss_exemption 0/4; hardening 1.0; alternative 1.0; refuse_all 0/26; crash_as_refusal 4/0;
  adjacent_api 0/3; whole_value_extension 1/0.
- control (static/nop/oracle/patches): static PASSED; nop hit the shared-VM Harbor egress-kernel
  probe flake at load ~250 (`ValueError: network_mode='allowlist' is not supported ...` after the
  300 s probe), so the control chain runs behind a probe-gated retry loop and is still running.
