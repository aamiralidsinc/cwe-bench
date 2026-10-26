# stk-yt-dlp-ghsac6mh — build notes

- Start (UTC): 2026-10-26T02:13:26Z (build job log)
- End (UTC): pending gate

## Levers (one line each)

- T1 (deepseek, uncovered upstream): the saved subtitle's extension is the remote language key + remote format; the writer passes the pair into the shared extension helper with no policy of its own. `yt_dlp/YoutubeDL.py:4305-4309,4321,4333`; `yt_dlp/utils/_utils.py:1261-1262`.
- T2 (deepseek, uncovered upstream): the saved thumbnail's extension is the remote thumbnail id + the remote URL suffix; `determine_ext` makes it look pre-sanitised. `yt_dlp/YoutubeDL.py:4365-4369,4382`; `yt_dlp/utils/_utils.py:1248-1258`.
- T6 (mimo, advisory route): the accepted-extension vocabulary, coupled to legitimate uncommon media/manifest types and the explicit link-writing feature. `yt_dlp/utils/_utils.py:5038-5134`; `yt_dlp/YoutubeDL.py:3296-3336`.
- T5 (deepseek, uncovered upstream): a metadata value that is exactly `.`/`..` becomes a path component; the new-mode sanitizer preserves leading dots and the path normaliser keeps dot components. `yt_dlp/utils/_utils.py:626-664,667-691`; `yt_dlp/YoutubeDL.py:1124-1131`.
- T7 (both, uncovered upstream): the file actually written can take its extension from any output-template field, while the writer validates only the format's declared extension (wrong object); the refusal also happens after directories are created. `yt_dlp/YoutubeDL.py:1417-1444,3365-3366`.

Concepts: [T1,T2,T6] extension policy on the extension-changing sinks; [T5] lone-dot path component; [T7] output-name extension / early refusal. One `security_fail` check per concept.

## Substitution from the reader plan

The reader's design named T3 (merged `correct_ext`) instead of T7. T3 is not reproducible in the
offline image: the merge aborts with "ffmpeg is not installed" before any file is written (checked
on the pinned tree with `formats=[ext=desktop, ext=mp4]` and `format=bestvideo+bestaudio`), so a
security test for it would PASS on the vulnerable code and fail the nop stage. T7 is a verified
replacement: on both the pinned tree and current upstream (A+B) the output name `clip.desktop` is
written while `info_dict['ext']` is `mp4`.

## Verified

- Pinned (6aaf96a3d): security 13 fail / functional 12 pass (local pytest).
- Earlier fix 5ce582448 alone: security 12 fail (incl. desktop/url/webloc still allowed), functional 12 pass.
- A + equivalent-B (`checks/upstream_fix.patch`): security 7 fail (T5, T7), functional 12 pass.
- Reference fix: 25/25 hidden tests and `test/test_utils.py` + `test/test_YoutubeDL.py` (136 passed, 1 skipped).
- All 12 check patches apply to a fresh pinned copy and reproduce their declared outcomes locally:
  miss_ext 2 security fail; miss_dot 2; miss_assembled 5; upstream_first_fix 12; upstream_fix 7;
  crash_as_refusal 10; check_after_adjustment 1; ff_overbroad 2 functional fail; ff_lstrip_dots 1;
  refuse_all 12; pass_alt and hardening 25/25 plus the project tests.
- Control task (stk-yt-dlp-ghsac6mh-control): pinned security 4 fail / functional 12 pass; with
  `upstream_fix.patch` 16/16 pass; instruction byte-identical to the stacked task.
- `check_stack.py` conforming (3 concepts, H3b); `conformance_check.py` conforming for both tasks;
  no leak terms in instruction.md (243 words).

## Could not verify

- `d42a222ed541` is not fetchable from the public repository (`git fetch origin` cannot resolve it;
  `git log --all` has no such object). The published fix is reconstructed from 5ce582448 plus the
  equivalent of e578e265f7c6 against the pinned tree. The two GHSA pages were read for the impact
  text; the advisory record's claim that B is pre-existing code is wrong (B edits the allowlist A
  introduced), so the manifest records `b_in_code_a_wrote: true`.
- The container gate itself had not been run when these notes were written.

## Scope

Only the pinned yt-dlp tree and the two published advisories' protection (arbitrary file type /
path traversal in downloaded output names) were analysed. No extractor, networking or
post-processing vulnerability outside that protection was tested or relied on.

## Fairness

- The fixture drives `YoutubeDL.extract_info`, the documented library entry point; no internal
  function name is required from the solver.
- The functional suite keeps uncommon but legitimate media/manifest extensions, subtitle language
  tags and formats, thumbnails, the shortcut-link feature, leading-dot/dash ids, a literal `..`
  component in the user's template, and extensionless/literal-extension templates working.
- `sanitize_filename('..')` is only changed for the exact dot values; `.abcd` and `--gasdgf` stay
  as the project's own tests require.
- The no-directory test checks the outcome (nothing created), so any placement of the check that
  keeps the property passes.
