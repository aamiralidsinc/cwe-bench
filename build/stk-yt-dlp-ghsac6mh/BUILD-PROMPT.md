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

Project root: `/home/mara/cwe-bench`. Task: `stk-yt-dlp-ghsac6mh`. Pattern: `A+B`. Track: `stacked`.

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
- Advisory: GHSA-79w7-vh3h-8g4j; GHSA-c6mh-fpjc-4pr3
- Pinned (vulnerable) commit: 6aaf96a3d6e7d0d426e97e11a2fcf52fda00e733. Published fix: 5ce582448ece, d42a222ed541, e578e265f7c6.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "candidate_id": "h3-ghsa-c6mh-fpjc-4pr3",
 "pattern": "H3b",
 "repo": "yt-dlp/yt-dlp",
 "pinned_commit": "6aaf96a3d6e7d0d426e97e11a2fcf52fda00e733",
 "protections": [
  "Output-template field sanitization: every metadata value substituted into the output template is passed through sanitize_filename, which replaces or strips path separators and reserved characters (yt_dlp/YoutubeDL.py:1295-1301, 1383-1391).",
  "Assembled-path normalization: get_output_path passes the joined path through sanitize_path, which handles Windows reserved characters and trailing spaces/dots and deliberately keeps '.'/'..' components (yt_dlp/YoutubeDL.py:1124-1131; yt_dlp/utils/_utils.py:667-691).",
  "Fixed auxiliary extensions: non-media outputs take constant extensions from OUTTMPL_TYPES such as 'info.json', 'description' and 'annotations.xml', so their extension is not metadata-derived (yt_dlp/utils/_utils.py:2803-2815; yt_dlp/YoutubeDL.py:1417-1420)."
 ],
 "traps": [
  {
   "id": "T1",
   "mechanism": "M2",
   "origin": "uncovered_upstream",
   "locations": [
    "yt_dlp/YoutubeDL.py:4305",
    "yt_dlp/YoutubeDL.py:4306",
    "yt_dlp/YoutubeDL.py:4307",
    "yt_dlp/YoutubeDL.py:4308",
    "yt_dlp/utils/_utils.py:1261",
    "yt_dlp/utils/_utils.py:1262",
    "yt_dlp/YoutubeDL.py:4321",
    "yt_dlp/YoutubeDL.py:4333",
    "yt_dlp/YoutubeDL.py:3250"
   ],
   "reason_to_dismiss": "Subtitle language keys and subtitle formats look like extractor vocabulary, --write-subs/--write-auto-subs are opt-in, and the video filename that is used as the base is already sanitized, so the subtitle suffix is assumed to be safe.",
   "distance": {
    "files": 2,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "hard",
   "tier_mimo": "medium",
   "type": "deepseek",
   "evidence": [
    "yt_dlp/YoutubeDL.py:4305-4308 builds the subtitle path from the raw subtitle dict key and the raw sub_info['ext'] via subtitles_filename",
    "yt_dlp/utils/_utils.py:1261-1262 concatenates sub_lang and sub_format into the extension argument of replace_extension without any sanitizer",
    "yt_dlp/YoutubeDL.py:4321 and 4333 write/dl to that path; yt_dlp/YoutubeDL.py:4309 feeds it to existing_file, which can delete an existing file at that path",
    "yt_dlp/YoutubeDL.py:2770-2778 only sanitizes the subtitle URL and derives ext with determine_ext; the language dict keys are never touched",
    "yt_dlp/options.py:875-893: writesubtitles/writeautomaticsub/allsubtitles/ subtitleslangs are the reachability switches",
    "test/test_YoutubeDL.py:709-717 shows that only template-substituted id values go through the sanitizer"
   ]
  },
  {
   "id": "T2",
   "mechanism": "M2",
   "origin": "uncovered_upstream",
   "locations": [
    "yt_dlp/YoutubeDL.py:4365",
    "yt_dlp/YoutubeDL.py:4366",
    "yt_dlp/YoutubeDL.py:4368",
    "yt_dlp/YoutubeDL.py:4369",
    "yt_dlp/YoutubeDL.py:4382",
    "yt_dlp/YoutubeDL.py:2616",
    "yt_dlp/YoutubeDL.py:2621",
    "yt_dlp/utils/_utils.py:1251",
    "yt_dlp/utils/_utils.py:1252"
   ],
   "reason_to_dismiss": "determine_ext already reduces the URL extension to [A-Za-z0-9]+, so the thumbnail extension looks pre-sanitized, and thumbnail ids are treated as extractor-chosen metadata rather than site input.",
   "distance": {
    "files": 1,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "hard",
   "tier_mimo": "medium",
   "type": "deepseek",
   "evidence": [
    "yt_dlp/YoutubeDL.py:4366 composes thumb_ext from the raw t['id'] (only when --write-all-thumbnails yields multiple thumbnails) plus determine_ext(t['url'])",
    "yt_dlp/YoutubeDL.py:4368-4369 append that string to the sanitized base filename with replace_extension",
    "yt_dlp/YoutubeDL.py:4382 writes the downloaded thumbnail bytes to the resulting path",
    "yt_dlp/YoutubeDL.py:2616-2621 only defaults a missing id to str(i) and sanitizes the URL as a URL; a supplied id is kept verbatim",
    "yt_dlp/utils/_utils.py:1248-1258 accepts any purely alphanumeric URL suffix as the extension, including non-media types",
    "yt_dlp/options.py:1503-1517: --write-thumbnail/--write-all-thumbnails are the reachability switches"
   ]
  },
  {
   "id": "T3",
   "mechanism": "M2",
   "origin": "uncovered_upstream",
   "locations": [
    "yt_dlp/YoutubeDL.py:3377",
    "yt_dlp/YoutubeDL.py:3379",
    "yt_dlp/YoutubeDL.py:3382",
    "yt_dlp/YoutubeDL.py:3386",
    "yt_dlp/YoutubeDL.py:3387",
    "yt_dlp/YoutubeDL.py:3390",
    "yt_dlp/YoutubeDL.py:3391",
    "yt_dlp/YoutubeDL.py:3404",
    "yt_dlp/YoutubeDL.py:3405",
    "yt_dlp/YoutubeDL.py:3406",
    "yt_dlp/YoutubeDL.py:3437",
    "yt_dlp/YoutubeDL.py:3438",
    "yt_dlp/YoutubeDL.py:3439",
    "yt_dlp/YoutubeDL.py:2358",
    "yt_dlp/utils/_utils.py:3042",
    "yt_dlp/utils/_utils.py:3051",
    "yt_dlp/utils/_utils.py:3052",
    "yt_dlp/utils/_utils.py:3056",
    "yt_dlp/utils/_utils.py:2088",
    "yt_dlp/utils/_utils.py:2091"
   ],
   "reason_to_dismiss": "A merged download is normally resolved by get_compatible_ext to a known container (mp4/mkv/webm), so the merged extension is assumed to be fixed, and format_id is only used for an intermediate fragment name.",
   "distance": {
    "files": 2,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "hard",
   "tier_mimo": "hard",
   "type": "both",
   "evidence": [
    "yt_dlp/YoutubeDL.py:3379-3387 defines correct_ext as a manual f-string that appends the raw info_dict['ext'] to the already-sanitized filename, without replace_extension or any sanitizer",
    "yt_dlp/YoutubeDL.py:3390-3391 rewrite full_filename and temp_filename through correct_ext before the download, so the rewritten temp path is the one written to",
    "yt_dlp/YoutubeDL.py:3404-3406 and 3437-3439 pass 'f{format_id}' plus the raw per-format ext into prepend_extension",
    "yt_dlp/YoutubeDL.py:2358 takes the merged ext from get_compatible_ext, whose fallback at yt_dlp/utils/_utils.py:3051-3056 returns a raw vext from the format list",
    "yt_dlp/utils/_utils.py:2088-2098: prepend_extension/replace_extension perform plain string concatenation of the ext argument",
    "yt_dlp/YoutubeDL.py:2830-2835 shows per-format ext is only defaulted from determine_ext when missing; extractor-supplied ext and format_id are only string-coerced (yt_dlp/YoutubeDL.py:2715-2720, 2831)"
   ]
  },
  {
   "id": "T4",
   "mechanism": "M4",
   "origin": "injection_room",
   "locations": [
    "yt_dlp/YoutubeDL.py:1413",
    "yt_dlp/YoutubeDL.py:1414",
    "yt_dlp/YoutubeDL.py:1415",
    "yt_dlp/YoutubeDL.py:1416",
    "yt_dlp/utils/_utils.py:2096",
    "yt_dlp/utils/_utils.py:2098"
   ],
   "reason_to_dismiss": "The branch only fires when the user requests a conversion (final_ext is set from --recode-video/--remux-video/--extract-audio) and hard-codes that target extension in the output template, and the raw ext is about to be superseded by the conversion anyway.",
   "distance": {
    "files": 1,
    "packages": 0
   },
   "protection_state": "absent",
   "tier_deepseek": "xhard",
   "tier_mimo": "hard",
   "type": "deepseek",
   "evidence": [
    "yt_dlp/YoutubeDL.py:1413-1416 runs after template substitution and re-inserts the raw info_dict['ext'] with replace_extension whenever the substituted filename already ends with the final extension",
    "yt_dlp/utils/_utils.py:2096-2098 shows replace_extension inserts the ext argument verbatim",
    "yt_dlp/__init__.py:765-769 shows final_ext is a trusted user option, while ext at yt_dlp/YoutubeDL.py:1414 is metadata"
   ]
  },
  {
   "id": "T5",
   "mechanism": "M8",
   "origin": "uncovered_upstream",
   "locations": [
    "yt_dlp/utils/_utils.py:626",
    "yt_dlp/utils/_utils.py:646",
    "yt_dlp/utils/_utils.py:647",
    "yt_dlp/utils/_utils.py:648",
    "yt_dlp/utils/_utils.py:649",
    "yt_dlp/utils/_utils.py:650",
    "yt_dlp/utils/_utils.py:652",
    "yt_dlp/utils/_utils.py:661",
    "yt_dlp/utils/_utils.py:670",
    "yt_dlp/utils/_utils.py:676",
    "yt_dlp/utils/_utils.py:682",
    "yt_dlp/YoutubeDL.py:1296",
    "yt_dlp/YoutubeDL.py:1131"
   ],
   "reason_to_dismiss": "sanitize_filename is the CVE-2024-38519 fix itself, its tests assert that no '/' survives, and the new rules deliberately preserve leading dots and dashes, so the guard is assumed to be closed.",
   "distance": {
    "files": 2,
    "packages": 0
   },
   "protection_state": "weak",
   "tier_deepseek": "xhard",
   "tier_mimo": "hard",
   "type": "both",
   "evidence": [
    "yt_dlp/utils/_utils.py:646-650: in the default mode the substitute-character strip regex only matches around NUL placeholders, and yt_dlp/utils/_utils.py:652/661 shows the lstrip('.') cleanup is inside the 'if not is_id' block",
    "yt_dlp/YoutubeDL.py:1296 passes is_id=NO_DEFAULT in default operation, and NO_DEFAULT is a truthy class (yt_dlp/utils/_utils.py:62-63), so the leading-dot/underscore cleanup is skipped",
    "yt_dlp/utils/_utils.py:626-628 only rewrites the characters \" * : < > ? | / \\ ; a component that is exactly '..' or '.' is returned unchanged",
    "yt_dlp/utils/_utils.py:670-676: sanitize_path is a no-op on POSIX unless force is set",
    "yt_dlp/utils/_utils.py:682 deliberately keeps '.' and '..' path parts, so a dot-only component survives path normalization",
    "test/test_utils.py:174 and test/test_YoutubeDL.py:709-717 assert that leading dots/dashes are preserved in default mode, while test/test_utils.py:173/176 show the legacy is_id=False mode strips them",
    "test/test_utils.py:253-256 confirms sanitize_path intentionally passes '..' components through"
   ]
  },
  {
   "id": "T6",
   "mechanism": "M11",
   "origin": "advisory_route",
   "locations": [
    "yt_dlp/utils/_utils.py:1248",
    "yt_dlp/utils/_utils.py:1251",
    "yt_dlp/utils/_utils.py:1252",
    "yt_dlp/YoutubeDL.py:2834",
    "yt_dlp/YoutubeDL.py:2835",
    "yt_dlp/YoutubeDL.py:3018",
    "yt_dlp/YoutubeDL.py:1295",
    "yt_dlp/YoutubeDL.py:1296",
    "yt_dlp/YoutubeDL.py:1383",
    "yt_dlp/YoutubeDL.py:1391",
    "yt_dlp/utils/_utils.py:639"
   ],
   "reason_to_dismiss": "The extension is the format identity and must keep working for every legitimate container; sanitize_filename has already made it a legal filename, so preserving a site-chosen extension is treated as intended download behavior rather than a security control.",
   "distance": {
    "files": 2,
    "packages": 0
   },
   "protection_state": "weak",
   "tier_deepseek": "medium",
   "tier_mimo": "hard",
   "type": "mimo",
   "evidence": [
    "yt_dlp/utils/_utils.py:1248-1258 returns any purely alphanumeric URL suffix as the extension (or the caller's default), with no notion of dangerous file types",
    "yt_dlp/YoutubeDL.py:2834-2835 defaults a format's ext from determine_ext(url); yt_dlp/YoutubeDL.py:3017-3018 copies the selected format's ext into the top-level info_dict used by the default template",
    "yt_dlp/utils/_utils.py:2800: the default output template is '%(title)s [%(id)s].%(ext)s'",
    "yt_dlp/YoutubeDL.py:1383-1391 sanitizes every substituted value, but yt_dlp/utils/_utils.py:639 leaves ordinary letters/digits untouched, so an attacker-chosen alphanumeric extension is preserved",
    "yt_dlp/utils/_utils.py:5022-5035 lists the legitimate media extension families that any type restriction would have to keep working"
   ]
  }
 ],
 "independent_groups": [
  [
   "T1",
   "T2",
   "T4"
  ],
  [
   "T3"
  ],
  [
   "T5"
  ],
  [
   "T6"
  ]
 ],
 "history": {
  "a_fix_leaves_b_open": true,
  "b_in_code_a_wrote": false,
  "masking": [
   "T6 becomes the residual route once the character-level sites T1-T5 are sanitized: the extension is still chosen by the metadata source even when every separator is neutralized.",
   "T1 and T2 each concatenate two attacker-influenced components into one extension string (sub_lang + sub_format; t['id'] + URL extension), so sanitizing one component can hide the other in the same fix."
  ],
  "dependency_bump_fix": false,
  "in_repo_fix_possible": true
 },
 "conflicts": [
  {
   "a": "T6",
   "b": "T1",
   "what": "A file-type allowlist/blocklist for T6 must keep legitimate subtitle formats working; 'json' subtitles are explicitly special-cased (yt_dlp/postprocessor/ffmpeg.py:627-629) and 'vtt'/'srt'/'ass'/'lrc' are normal outputs (yt_dlp/utils/_utils.py:5029). Over-hardening the extension policy breaks --write-subs."
  },
  {
   "a": "T6",
   "b": "T2",
   "what": "A type restriction must also keep thumbnail formats working (jpg/png/webp at yt_dlp/utils/_utils.py:5027, with gif sources handled at yt_dlp/postprocessor/ffmpeg.py:1109), while --write-desktop-link/--write-url-link deliberately create .desktop/.url files (yt_dlp/options.py:1523-1539; yt_dlp/utils/_utils.py:4531-4554). A blanket 'no dangerous extension' rule breaks documented features."
  },
  {
   "a": "T5",
   "b": "T3",
   "what": "Stripping '.'/'..'/leading dots (a natural fix for T5) conflicts with the documented new sanitization rules that preserve '.abcd' and '--gasdgf' (test/test_utils.py:171-176; test/test_YoutubeDL.py:709-717) and would mangle legitimate ids and extensions; only dot-only components need special handling."
  }
 ],
 "fairness_risks": [
  "Legitimate subtitle language tags (e.g. 'zh-Hans', 'pt-BR') and subtitle formats ('json', 'vtt', 'srt', 'ass', 'lrc') must keep working; a rule that restricts them to a small character set or allowlist contradicts real extractor output.",
  "Arbitrary or unknown media extensions are legitimate (determine_ext can return 'unknown_video'; storyboards use 'mhtml'; manifests use 'f4m'/'m3u8'/'mpd'; yt_dlp/utils/_utils.py:5022-5035), so a file-type allowlist for T6 would refuse formats that must remain downloadable.",
  "User output templates legitimately contain subdirectories and '..' components (yt_dlp/utils/_utils.py:682 and test/test_utils.py:253-256 deliberately preserve them); a rule rejecting any '..' path component would refuse a legitimate template shape.",
  "Ids and extensions may legitimately start with '.' or '-' (A's tests assert '.abcd' and '--gasdgf' are preserved: test/test_utils.py:171-176, test/test_YoutubeDL.py:709-717); a naive lstrip breaks them.",
  "--write-desktop-link and --write-url-link deliberately create .desktop/.url files (yt_dlp/options.py:1523-1539); a dangerous-extension block used for T6 must not refuse this requested output type."
 ],
 "effort_minutes": 90,
 "usable": true,
 "design": {
  "traps": [
   "T1",
   "T3",
   "T5",
   "T6"
  ],
  "why": "Four independent judgements, each with a different dismissal: T1 is the opt-in subtitle path whose language key and format look like trusted extractor vocabulary; T3 is the default bestvideo+bestaudio merge where get_compatible_ext makes the merged extension look normalized and format_id looks like a temporary name; T5 is the CVE-2024-38519 sanitizer itself mishandling a dot-only component; T6 is the extension vocabulary, where any blocking rule collides with legitimate formats. T2 and T4 are additional surfaces of the same raw-extension insertion as T1 and are counted in its group. Fixing any one leaves the others open, and the set carries deepseek-type absentness-with-dismissal traps (T1, T5) plus a mimo-type coupled-value trap (T6), so it probes both models' known blind spots."
 },
 "unverified": [
  "The B advisory text and fix commit e578e265f7c6 are not present in the pinned worktree and could not be inspected (no network or git execution), so which of T1-T6 the 2026 fix actually covered is unverified; all trap sites are verified in the pinned code.",
  "Attacker control of format ext, subtitle dict keys, sub_info['ext'] and thumbnail ids assumes extractor-supplied metadata is untrusted, as in the CVE-2024-38519 threat model; no extractor in this tree is shown passing site JSON into those fields, so reachability is inferred from their provenance (yt_dlp/YoutubeDL.py:2770-2778, 2830-2835, 2615-2621).",
  "sanitize_filename('..') == '..' is derived from yt_dlp/utils/_utils.py:646-664 (is_id is NO_DEFAULT, so the lstrip('.') at line 661 is skipped); only the neighbouring '.gasdgf' case is covered by a test (test/test_utils.py:174).",
  "The record says szz_status H3u; it is mapped here to H3b (A's guard leaves B open, with B in pre-existing code). If the true B is the leading-dot/'..' weakness in sanitize_filename, the pattern would be H3a (regression in code A wrote) instead.",
  "Grouping T1, T2 and T4 as one group assumes a single sanitizer in replace_extension/prepend_extension would close all three; if the fix is applied per metadata producer instead, they are three independent traps and the candidate becomes even stronger.",
  "Whether the 2026 fix includes a file-type restriction (T6) is unverified; T6 is recorded because the advisory summary names 'dangerous file type creation' and no such restriction exists in the pinned code."
 ]
}
  ```
- Published fix sites:   - yt_dlp/utils/_utils.py:1248 — T6 M11 (reason to dismiss: The extension is the format identity and must keep working for every legitimate container; sanitize_filename has already made it a legal filename, so preserving a site-chosen extension is treated as intended download behavior rather than a security control.)
  - yt_dlp/utils/_utils.py:1251 — T6 M11 (reason to dismiss: The extension is the format identity and must keep working for every legitimate container; sanitize_filename has already made it a legal filename, so preserving a site-chosen extension is treated as intended download behavior rather than a security control.)
  - yt_dlp/utils/_utils.py:1252 — T6 M11 (reason to dismiss: The extension is the format identity and must keep working for every legitimate container; sanitize_filename has already made it a legal filename, so preserving a site-chosen extension is treated as intended download behavior rather than a security control.)
  - yt_dlp/YoutubeDL.py:2834 — T6 M11 (reason to dismiss: The extension is the format identity and must keep working for every legitimate container; sanitize_filename has already made it a legal filename, so preserving a site-chosen extension is treated as intended download behavior rather than a security control.)
  - yt_dlp/YoutubeDL.py:2835 — T6 M11 (reason to dismiss: The extension is the format identity and must keep working for every legitimate container; sanitize_filename has already made it a legal filename, so preserving a site-chosen extension is treated as intended download behavior rather than a security control.)
  - yt_dlp/YoutubeDL.py:3018 — T6 M11 (reason to dismiss: The extension is the format identity and must keep working for every legitimate container; sanitize_filename has already made it a legal filename, so preserving a site-chosen extension is treated as intended download behavior rather than a security control.)
  - yt_dlp/YoutubeDL.py:1295 — T6 M11 (reason to dismiss: The extension is the format identity and must keep working for every legitimate container; sanitize_filename has already made it a legal filename, so preserving a site-chosen extension is treated as intended download behavior rather than a security control.)
  - yt_dlp/YoutubeDL.py:1296 — T6 M11 (reason to dismiss: The extension is the format identity and must keep working for every legitimate container; sanitize_filename has already made it a legal filename, so preserving a site-chosen extension is treated as intended download behavior rather than a security control.)
  - yt_dlp/YoutubeDL.py:1383 — T6 M11 (reason to dismiss: The extension is the format identity and must keep working for every legitimate container; sanitize_filename has already made it a legal filename, so preserving a site-chosen extension is treated as intended download behavior rather than a security control.)
  - yt_dlp/YoutubeDL.py:1391 — T6 M11 (reason to dismiss: The extension is the format identity and must keep working for every legitimate container; sanitize_filename has already made it a legal filename, so preserving a site-chosen extension is treated as intended download behavior rather than a security control.)
  - yt_dlp/utils/_utils.py:639 — T6 M11 (reason to dismiss: The extension is the format identity and must keep working for every legitimate container; sanitize_filename has already made it a legal filename, so preserving a site-chosen extension is treated as intended download behavior rather than a security control.)
- Uncovered routes to confirm (pattern B):   - yt_dlp/YoutubeDL.py:4305 — T1 M2 (reason to dismiss: Subtitle language keys and subtitle formats look like extractor vocabulary, --write-subs/--write-auto-subs are opt-in, and the video filename that is used as the base is already sanitized, so the subtitle suffix is assumed to be safe.)
  - yt_dlp/YoutubeDL.py:4306 — T1 M2 (reason to dismiss: Subtitle language keys and subtitle formats look like extractor vocabulary, --write-subs/--write-auto-subs are opt-in, and the video filename that is used as the base is already sanitized, so the subtitle suffix is assumed to be safe.)
  - yt_dlp/YoutubeDL.py:4307 — T1 M2 (reason to dismiss: Subtitle language keys and subtitle formats look like extractor vocabulary, --write-subs/--write-auto-subs are opt-in, and the video filename that is used as the base is already sanitized, so the subtitle suffix is assumed to be safe.)
  - yt_dlp/YoutubeDL.py:4308 — T1 M2 (reason to dismiss: Subtitle language keys and subtitle formats look like extractor vocabulary, --write-subs/--write-auto-subs are opt-in, and the video filename that is used as the base is already sanitized, so the subtitle suffix is assumed to be safe.)
  - yt_dlp/utils/_utils.py:1261 — T1 M2 (reason to dismiss: Subtitle language keys and subtitle formats look like extractor vocabulary, --write-subs/--write-auto-subs are opt-in, and the video filename that is used as the base is already sanitized, so the subtitle suffix is assumed to be safe.)
  - yt_dlp/utils/_utils.py:1262 — T1 M2 (reason to dismiss: Subtitle language keys and subtitle formats look like extractor vocabulary, --write-subs/--write-auto-subs are opt-in, and the video filename that is used as the base is already sanitized, so the subtitle suffix is assumed to be safe.)
  - yt_dlp/YoutubeDL.py:4321 — T1 M2 (reason to dismiss: Subtitle language keys and subtitle formats look like extractor vocabulary, --write-subs/--write-auto-subs are opt-in, and the video filename that is used as the base is already sanitized, so the subtitle suffix is assumed to be safe.)
  - yt_dlp/YoutubeDL.py:4333 — T1 M2 (reason to dismiss: Subtitle language keys and subtitle formats look like extractor vocabulary, --write-subs/--write-auto-subs are opt-in, and the video filename that is used as the base is already sanitized, so the subtitle suffix is assumed to be safe.)
  - yt_dlp/YoutubeDL.py:3250 — T1 M2 (reason to dismiss: Subtitle language keys and subtitle formats look like extractor vocabulary, --write-subs/--write-auto-subs are opt-in, and the video filename that is used as the base is already sanitized, so the subtitle suffix is assumed to be safe.)
  - yt_dlp/YoutubeDL.py:4365 — T2 M2 (reason to dismiss: determine_ext already reduces the URL extension to [A-Za-z0-9]+, so the thumbnail extension looks pre-sanitized, and thumbnail ids are treated as extractor-chosen metadata rather than site input.)
  - yt_dlp/YoutubeDL.py:4366 — T2 M2 (reason to dismiss: determine_ext already reduces the URL extension to [A-Za-z0-9]+, so the thumbnail extension looks pre-sanitized, and thumbnail ids are treated as extractor-chosen metadata rather than site input.)
  - yt_dlp/YoutubeDL.py:4368 — T2 M2 (reason to dismiss: determine_ext already reduces the URL extension to [A-Za-z0-9]+, so the thumbnail extension looks pre-sanitized, and thumbnail ids are treated as extractor-chosen metadata rather than site input.)
  - yt_dlp/YoutubeDL.py:4369 — T2 M2 (reason to dismiss: determine_ext already reduces the URL extension to [A-Za-z0-9]+, so the thumbnail extension looks pre-sanitized, and thumbnail ids are treated as extractor-chosen metadata rather than site input.)
  - yt_dlp/YoutubeDL.py:4382 — T2 M2 (reason to dismiss: determine_ext already reduces the URL extension to [A-Za-z0-9]+, so the thumbnail extension looks pre-sanitized, and thumbnail ids are treated as extractor-chosen metadata rather than site input.)
  - yt_dlp/YoutubeDL.py:2616 — T2 M2 (reason to dismiss: determine_ext already reduces the URL extension to [A-Za-z0-9]+, so the thumbnail extension looks pre-sanitized, and thumbnail ids are treated as extractor-chosen metadata rather than site input.)
  - yt_dlp/YoutubeDL.py:2621 — T2 M2 (reason to dismiss: determine_ext already reduces the URL extension to [A-Za-z0-9]+, so the thumbnail extension looks pre-sanitized, and thumbnail ids are treated as extractor-chosen metadata rather than site input.)
  - yt_dlp/utils/_utils.py:1251 — T2 M2 (reason to dismiss: determine_ext already reduces the URL extension to [A-Za-z0-9]+, so the thumbnail extension looks pre-sanitized, and thumbnail ids are treated as extractor-chosen metadata rather than site input.)
  - yt_dlp/utils/_utils.py:1252 — T2 M2 (reason to dismiss: determine_ext already reduces the URL extension to [A-Za-z0-9]+, so the thumbnail extension looks pre-sanitized, and thumbnail ids are treated as extractor-chosen metadata rather than site input.)
  - yt_dlp/YoutubeDL.py:3377 — T3 M2 (reason to dismiss: A merged download is normally resolved by get_compatible_ext to a known container (mp4/mkv/webm), so the merged extension is assumed to be fixed, and format_id is only used for an intermediate fragment name.)
  - yt_dlp/YoutubeDL.py:3379 — T3 M2 (reason to dismiss: A merged download is normally resolved by get_compatible_ext to a known container (mp4/mkv/webm), so the merged extension is assumed to be fixed, and format_id is only used for an intermediate fragment name.)
  - yt_dlp/YoutubeDL.py:3382 — T3 M2 (reason to dismiss: A merged download is normally resolved by get_compatible_ext to a known container (mp4/mkv/webm), so the merged extension is assumed to be fixed, and format_id is only used for an intermediate fragment name.)
  - yt_dlp/YoutubeDL.py:3386 — T3 M2 (reason to dismiss: A merged download is normally resolved by get_compatible_ext to a known container (mp4/mkv/webm), so the merged extension is assumed to be fixed, and format_id is only used for an intermediate fragment name.)
  - yt_dlp/YoutubeDL.py:3387 — T3 M2 (reason to dismiss: A merged download is normally resolved by get_compatible_ext to a known container (mp4/mkv/webm), so the merged extension is assumed to be fixed, and format_id is only used for an intermediate fragment name.)
  - yt_dlp/YoutubeDL.py:3390 — T3 M2 (reason to dismiss: A merged download is normally resolved by get_compatible_ext to a known container (mp4/mkv/webm), so the merged extension is assumed to be fixed, and format_id is only used for an intermediate fragment name.)
  - yt_dlp/YoutubeDL.py:3391 — T3 M2 (reason to dismiss: A merged download is normally resolved by get_compatible_ext to a known container (mp4/mkv/webm), so the merged extension is assumed to be fixed, and format_id is only used for an intermediate fragment name.)
  - yt_dlp/YoutubeDL.py:3404 — T3 M2 (reason to dismiss: A merged download is normally resolved by get_compatible_ext to a known container (mp4/mkv/webm), so the merged extension is assumed to be fixed, and format_id is only used for an intermediate fragment name.)
  - yt_dlp/YoutubeDL.py:3405 — T3 M2 (reason to dismiss: A merged download is normally resolved by get_compatible_ext to a known container (mp4/mkv/webm), so the merged extension is assumed to be fixed, and format_id is only used for an intermediate fragment name.)
  - yt_dlp/YoutubeDL.py:3406 — T3 M2 (reason to dismiss: A merged download is normally resolved by get_compatible_ext to a known container (mp4/mkv/webm), so the merged extension is assumed to be fixed, and format_id is only used for an intermediate fragment name.)
  - yt_dlp/YoutubeDL.py:3437 — T3 M2 (reason to dismiss: A merged download is normally resolved by get_compatible_ext to a known container (mp4/mkv/webm), so the merged extension is assumed to be fixed, and format_id is only used for an intermediate fragment name.)
  - yt_dlp/YoutubeDL.py:3438 — T3 M2 (reason to dismiss: A merged download is normally resolved by get_compatible_ext to a known container (mp4/mkv/webm), so the merged extension is assumed to be fixed, and format_id is only used for an intermediate fragment name.)
  - yt_dlp/YoutubeDL.py:3439 — T3 M2 (reason to dismiss: A merged download is normally resolved by get_compatible_ext to a known container (mp4/mkv/webm), so the merged extension is assumed to be fixed, and format_id is only used for an intermediate fragment name.)
  - yt_dlp/YoutubeDL.py:2358 — T3 M2 (reason to dismiss: A merged download is normally resolved by get_compatible_ext to a known container (mp4/mkv/webm), so the merged extension is assumed to be fixed, and format_id is only used for an intermediate fragment name.)
  - yt_dlp/utils/_utils.py:3042 — T3 M2 (reason to dismiss: A merged download is normally resolved by get_compatible_ext to a known container (mp4/mkv/webm), so the merged extension is assumed to be fixed, and format_id is only used for an intermediate fragment name.)
  - yt_dlp/utils/_utils.py:3051 — T3 M2 (reason to dismiss: A merged download is normally resolved by get_compatible_ext to a known container (mp4/mkv/webm), so the merged extension is assumed to be fixed, and format_id is only used for an intermediate fragment name.)
  - yt_dlp/utils/_utils.py:3052 — T3 M2 (reason to dismiss: A merged download is normally resolved by get_compatible_ext to a known container (mp4/mkv/webm), so the merged extension is assumed to be fixed, and format_id is only used for an intermediate fragment name.)
  - yt_dlp/utils/_utils.py:3056 — T3 M2 (reason to dismiss: A merged download is normally resolved by get_compatible_ext to a known container (mp4/mkv/webm), so the merged extension is assumed to be fixed, and format_id is only used for an intermediate fragment name.)
  - yt_dlp/utils/_utils.py:2088 — T3 M2 (reason to dismiss: A merged download is normally resolved by get_compatible_ext to a known container (mp4/mkv/webm), so the merged extension is assumed to be fixed, and format_id is only used for an intermediate fragment name.)
  - yt_dlp/utils/_utils.py:2091 — T3 M2 (reason to dismiss: A merged download is normally resolved by get_compatible_ext to a known container (mp4/mkv/webm), so the merged extension is assumed to be fixed, and format_id is only used for an intermediate fragment name.)
  - yt_dlp/utils/_utils.py:626 — T5 M8 (reason to dismiss: sanitize_filename is the CVE-2024-38519 fix itself, its tests assert that no '/' survives, and the new rules deliberately preserve leading dots and dashes, so the guard is assumed to be closed.)
  - yt_dlp/utils/_utils.py:646 — T5 M8 (reason to dismiss: sanitize_filename is the CVE-2024-38519 fix itself, its tests assert that no '/' survives, and the new rules deliberately preserve leading dots and dashes, so the guard is assumed to be closed.)
  - yt_dlp/utils/_utils.py:647 — T5 M8 (reason to dismiss: sanitize_filename is the CVE-2024-38519 fix itself, its tests assert that no '/' survives, and the new rules deliberately preserve leading dots and dashes, so the guard is assumed to be closed.)
  - yt_dlp/utils/_utils.py:648 — T5 M8 (reason to dismiss: sanitize_filename is the CVE-2024-38519 fix itself, its tests assert that no '/' survives, and the new rules deliberately preserve leading dots and dashes, so the guard is assumed to be closed.)
  - yt_dlp/utils/_utils.py:649 — T5 M8 (reason to dismiss: sanitize_filename is the CVE-2024-38519 fix itself, its tests assert that no '/' survives, and the new rules deliberately preserve leading dots and dashes, so the guard is assumed to be closed.)
  - yt_dlp/utils/_utils.py:650 — T5 M8 (reason to dismiss: sanitize_filename is the CVE-2024-38519 fix itself, its tests assert that no '/' survives, and the new rules deliberately preserve leading dots and dashes, so the guard is assumed to be closed.)
  - yt_dlp/utils/_utils.py:652 — T5 M8 (reason to dismiss: sanitize_filename is the CVE-2024-38519 fix itself, its tests assert that no '/' survives, and the new rules deliberately preserve leading dots and dashes, so the guard is assumed to be closed.)
  - yt_dlp/utils/_utils.py:661 — T5 M8 (reason to dismiss: sanitize_filename is the CVE-2024-38519 fix itself, its tests assert that no '/' survives, and the new rules deliberately preserve leading dots and dashes, so the guard is assumed to be closed.)
  - yt_dlp/utils/_utils.py:670 — T5 M8 (reason to dismiss: sanitize_filename is the CVE-2024-38519 fix itself, its tests assert that no '/' survives, and the new rules deliberately preserve leading dots and dashes, so the guard is assumed to be closed.)
  - yt_dlp/utils/_utils.py:676 — T5 M8 (reason to dismiss: sanitize_filename is the CVE-2024-38519 fix itself, its tests assert that no '/' survives, and the new rules deliberately preserve leading dots and dashes, so the guard is assumed to be closed.)
  - yt_dlp/utils/_utils.py:682 — T5 M8 (reason to dismiss: sanitize_filename is the CVE-2024-38519 fix itself, its tests assert that no '/' survives, and the new rules deliberately preserve leading dots and dashes, so the guard is assumed to be closed.)
  - yt_dlp/YoutubeDL.py:1296 — T5 M8 (reason to dismiss: sanitize_filename is the CVE-2024-38519 fix itself, its tests assert that no '/' survives, and the new rules deliberately preserve leading dots and dashes, so the guard is assumed to be closed.)
  - yt_dlp/YoutubeDL.py:1131 — T5 M8 (reason to dismiss: sanitize_filename is the CVE-2024-38519 fix itself, its tests assert that no '/' survives, and the new rules deliberately preserve leading dots and dashes, so the guard is assumed to be closed.)
- Design plan from the lead: TRACK = STACKED (H3b). Build the stacked design the reader chose: traps T1, T3, T5, T6. Why: Four independent judgements, each with a different dismissal: T1 is the opt-in subtitle path whose language key and format look like trusted extractor vocabulary; T3 is the default bestvideo+bestaudio merge where get_compatible_ext makes the merged extension look normalized and format_id looks like a temporary name; T5 is the CVE-2024-38519 sanitizer itself mishandling a dot-only component; T6 is the extension vocabulary, where any blocking rule collides with legitimate formats. T2 and T4 are additional surfaces of the same raw-extension insertion as T1 and are counted in its group. Fixing any one leaves the others open, and the set carries deepseek-type absentness-with-dismissal traps (T1, T5) plus a mimo-type coupled-value trap (T6), so it probes both models' known blind spots. Follow the stacked-task rules appended at the end of this prompt; they add to the rules above.
- Host notes: Reader fairness risks (resolve each in the report's contracts or the tests): Legitimate subtitle language tags (e.g. 'zh-Hans', 'pt-BR') and subtitle formats ('json', 'vtt', 'srt', 'ass', 'lrc') must keep working; a rule that restricts them to a small character set or allowlist contradicts real extractor output. | Arbitrary or unknown media extensions are legitimate (determine_ext can return 'unknown_video'; storyboards use 'mhtml'; manifests use 'f4m'/'m3u8'/'mpd'; yt_dlp/utils/_utils.py:5022-5035), so a file-type allowlist for T6 would refuse formats that must remain downloadable. | User output templates legitimately contain subdirectories and '..' components (yt_dlp/utils/_utils.py:682 and test/test_utils.py:253-256 deliberately preserve them); a rule rejecting any '..' path component would refuse a legitimate template shape. | Ids and extensions may legitimately start with '.' or '-' (A's tests assert '.abcd' and '--gasdgf' are preserved: test/test_utils.py:171-176, test/test_YoutubeDL.py:709-717); a naive lstrip breaks them. | --write-desktop-link and --write-url-link deliberately create .desktop/.url files (yt_dlp/options.py:1523-1539); a dangerous-extension block used for T6 must not refuse this requested output type.. Conflicts the reader found: A file-type allowlist/blocklist for T6 must keep legitimate subtitle formats working; 'json' subtitles are explicitly special-cased (yt_dlp/postprocessor/ffmpeg.py:627-629) and 'vtt'/'srt'/'ass'/'lrc' are normal outputs (yt_dlp/utils/_utils.py:5029). Over-hardening the extension policy breaks --write-subs. | A type restriction must also keep thumbnail formats working (jpg/png/webp at yt_dlp/utils/_utils.py:5027, with gif sources handled at yt_dlp/postprocessor/ffmpeg.py:1109), while --write-desktop-link/--write-url-link deliberately create .desktop/.url files (yt_dlp/options.py:1523-1539; yt_dlp/utils/_utils.py:4531-4554). A blanket 'no dangerous extension' rule breaks documented features. | Stripping '.'/'..'/leading dots (a natural fix for T5) conflicts with the documented new sanitization rules that preserve '.abcd' and '--gasdgf' (test/test_utils.py:171-176; test/test_YoutubeDL.py:709-717) and would mangle legitimate ids and extensions; only dot-only components need special handling.

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

## Environment (`tasks/stk-yt-dlp-ghsac6mh/environment/Dockerfile`)
- **Base and code.** A small official base image. The repo goes into `/app` at the pinned commit,
  and `/app/.git` is then deleted.
- **Offline.** Install every dependency, tool and service the project and tests need; nothing may
  be downloaded at test time. Services start from `test.sh`.
- **Packages:** `patch`, `curl`, `ca-certificates`, `bash`, `git`.
- **Agent layer.** Append `common/trial/claude-code.Dockerfile.snippet` unchanged at the end.
- **No test code in the image.** The agent shares the container. Pre-build against stubs; `test.sh`
  copies the real tests in at grading time.
- **Project tests.** The project's own tests for the affected area must pass in the image at the
  pinned commit.
- **No leaked regression tests.** The pinned commit must not already contain the advisory's
  regression tests (check `git log` between the pinned and fix commits).

## Report to the solver (`tasks/stk-yt-dlp-ghsac6mh/instruction.md`)
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

## Tests (`tasks/stk-yt-dlp-ghsac6mh/tests/`)
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
- **Wrong-fix patches** go in `build/stk-yt-dlp-ghsac6mh/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/stk-yt-dlp-ghsac6mh/`:**
- `instruction.md`;
- `task.toml`, from `common/builder/templates/`, with `[metadata]` (incl. the delivery fields) filled in and
  `network_mode = "no-network"` (no allowlist);
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/stk-yt-dlp-ghsac6mh/manifest.json`:**
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

**Also in `build/stk-yt-dlp-ghsac6mh/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `common/builder/templates/` and `common/trial/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I common/gate/gate.py stk-yt-dlp-ghsac6mh --only static
python3 -I common/gate/gate.py stk-yt-dlp-ghsac6mh --only nop
python3 -I common/gate/gate.py stk-yt-dlp-ghsac6mh --only oracle
python3 -I common/gate/gate.py stk-yt-dlp-ghsac6mh --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/stk-yt-dlp-ghsac6mh/`;
  - edit only `tasks/stk-yt-dlp-ghsac6mh/`, `build/stk-yt-dlp-ghsac6mh/` and, for pattern B, the register;
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
is missing. The reader's record lists them, with evidence: `/home/mara/cwe-bench/pipelines/stacking/out/reader/h3-ghsa-c6mh-fpjc-4pr3.json`. Verify each trap on the
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
5. **A coupled must-keep-working value next to every hidden route**, tested functionally. The
   report covers it ONLY through the general keep-working sentence ("everything that works today
   keeps working"); it never names or describes the value. If a security rule, read literally, would
   forbid that value, reword the security rule over its protected outcome instead of adding an
   exception that names the value.
6. **Effort budget.** A careful engineer who knows where to look fixes everything in about 45-60
   minutes. If the stack needs more, drop the weakest concept.

**The report**
7. **One general property per distinct protection, and nothing per trap.** Never one per route, and
   never a count. Describe no surface, as the build template already requires. If the stack spans two
   protections, state two properties, each over its protected data or outcome.
   - **The one-bug test:** for every sentence of the report, ask "would this sentence be here if the
     task had only the advisory's own route?" If not, delete it. That covers forms ("in every form it
     can be named"), timing ("and again when the call connects"), sources ("whichever response
     supplies it"), encodings, aliases, example values in keep-working lines, and lists of resources.
   - Only the advisory's own route may be shown, in the impact example.
   - General contracts that hold for every route stay: the refusal form (for example "a client
     error, with no effect"), an operator opt-in, "keep every legitimate use working".
   - Keep the report short: the goal in a few lines, the property, the general contracts.
   - After the build, `pipelines/stacking/4-listing/run_listing_check.sh` classifies every hidden trap against the
     report. One NAMED hidden trap, or more than one DESCRIBED hidden trap, is a FAIL. Once the
     reviewer is calibrated (`pipelines/stacking/4-listing/LISTING_ENFORCE`), a FAIL means the task is not marked sound.

**History rules** (by the record's `pattern`)
8. **H3a / H3b (fix of a fix):**
   - pin the parent of the earlier fix A's first commit;
   - the reference fix is the complete fix (A plus the later fix B, or an equivalent);
   - add `checks/upstream_first_fix.patch`, which is A's fix applied alone, with `expect: fail`, so
     upstream's first fix is proven to be a wrong fix.
9. **H3c (masking):** the masked bug's security test must fail on the pinned code through its own
   route, without relying on the masking bug, so the gate's nop stage holds.
10. **Conflicting fixes (F8):** when the record names a pair where the natural fix for one trap breaks
    a value another needs, test that value functionally. The report covers it only through the
    general keep-working sentence, as in rule 5; never by naming the value.
11. **Dependency-bump fixes (F5):** when upstream fixed a bug by upgrading a dependency, the task must
    be fixable inside the repository. The reference proves it. The report never asks for an upgrade,
    and the solver works offline.
12. **Recall check (every pattern):** add `checks/upstream_fix.patch` (every published fix commit for
    the stacked advisories, applied together) with `expect: fail`. If it passes, the stack adds
    nothing beyond what upstream shipped. Rework the design.

**The control task**
13. Also build `<slug>-control`: the same pinned code, the same report, but only the advisory's own
    route (the trap the report leads to) in the security tests and the reference. It isolates the
    effect of stacking from the effect of the host. The two `instruction.md` files stay byte-identical
    for the task's whole life: any later change to the stacked report (fairfix, upgrade) is copied to
    the control. `check_stack.py` checks it.

**Manifest:** add a `stacking` block containing:
- `pattern`;
- `reader_record`;
- `concepts` (groups of trap ids);
- `history`: advisories A and B with their fix commits, `pinned_commit` and its rule;
- `score_at_build`: copy the `score` of your job's row in `pipelines/stacking/out/stack_scores_ds.tsv` (do NOT run
  `score_stack.py`: it rewrites the shared selection file);
- `control_slug`.

**Exact manifest fields the static conformance check reads (step 5, `pipelines/stacking/3-build-gate/check_stack.py`). Emit these literally — the field NAMES and VALUES below must match, or the build is rejected before the container gate:**

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
  `{ "patch": "checks/miss_<concept>.patch", "kind": "security_fail", "expect": "security_fail", "misses": [<exactly this concept's trap ids>] }`.
  `misses` must be non-empty and be a subset of that concept's trap id group; one such check is required for every group in `stacking.concepts`.
- **Recall (always):** `{ "patch": "checks/upstream_fix.patch", "expect": "security_fail" }` — all published fix commits for the stacked advisories applied together.
- **Recall (H3a and every H3b variant):** also `{ "patch": "checks/upstream_first_fix.patch", "expect": "security_fail" }` — the earlier fix A applied alone.

Every `checks/*.patch` named above must be a real file in the task's `checks/` directory (the container gate then runs each with its `expect`ed outcome). A concept with no `security_fail` miss-check, a trap with no `type`, or a missing recall check/file each fails the conformance check.

**Report back:** also give the concept count, the DeepSeek-type and MiMo-type trap ids, the result of
each history check patch, and the control task's gate result.

Stacked task slug: `stk-yt-dlp-ghsac6mh`. Control task slug: `stk-yt-dlp-ghsac6mh-control`. Manifest `stacking.reader_record`: `pipelines/stacking/out/reader/h3-ghsa-c6mh-fpjc-4pr3.json`.
