# flyto-core-path-traversal — build notes (build-v1)

- Start (UTC): 2026-10-17T05:20:41Z (this run; an earlier run 04:27–04:35 left scratch trees and probes, re-verified here)
- End (UTC): see end of file

## Levers (one line each)
- T1 (A, far site, save/reload): paginator state file path is written each page and removed on completion — browser/pagination.py:323 → browser/checkpoint.py:109,142. Dismiss: "internal resume state, not an output file".
- T2 (A, far sites, other package): document writers/converters incl. derived default output — document/{excel_write,pdf_fill_form,pdf_to_word,word_to_pdf}.py. Dismiss: "the example is an image module".
- T3 (B): CSV writers with a '..' substring check, absolute paths open — data/csv_write.py:95, data/json_to_csv.py:161. Dismiss: "already has a traversal check".
- T4 (B): file copy/move destination — file/copy.py:98, file/move.py:93. Dismiss: "generic file ops next to the already-guarded file write".
- T5 (B): Word image extraction dir, same no-op check as the landing point — document/word_parse.py:178. Dismiss: "a reader; names are generated".
- T6 (B): PDF generation output — document/pdf_generate.py:102. Dismiss: "generates content, not in the report".
- T7 (shape): symlink in sandbox resolving outside (lexical check fails). T8 (shape): absolute outside vs '..'-only rejection. T9 (shape): derived default outputs. T10 (shape): directory created before the check.
- Coupled must-keep-working: absolute and relative in-sandbox paths, in-sandbox '..' spellings, new sub-dirs, derived defaults inside, paginator checkpoint+resume inside, file.write.

## Verified
- Pinned 9103529 is the sole parent of fix d5f89d7; no regression tests leaked.
- Every route reproduced through POST /v1/execute (FastAPI TestClient) on the pinned code: 23/23 security tests fail on pinned, pass on oracle; 29/29 own functional tests and 15 project tests pass on both (local venv, Python 3.12, same library versions as the image).
- Each checks/ patch run locally against both groups and behaves as declared (see manifest.patch_checks).
- Latest upstream (main 795d07e, 2026-10-12) confines all six built routes (present_in_latest = no), via later security commits (85a4f6b, bbb6f1c).
- image.download is tested against a local 127.0.0.1 HTTP server allowed by FLYTO_ALLOW_PRIVATE_NETWORK + FLYTO_HTTP_ALLOWED_PORTS; no external network.

## Not verified / not built
- Browser download/screenshot routes: the write is made by the Playwright driver; not reproduced (no browsers). Cookies export: reachable with a stub but same concept as T1; not built. Knowledge export: no module entry point found.
- '~' home-expansion shape: none of the tested writers expand '~' themselves (the write would land in a literal "~" dir under cwd), so no fair test; not built.
- Producer-off-path lever: the checkpoint serializer derives its .jsonl beside the validated path, so a check at the module covers it; not a real lever here.
- The paginator is driven with a stub browser session registered in the server's session table (no real browser); the product code does every file write.
- Advisory text itself was not available; scope taken from the fix diff.
- End (UTC): 2026-10-17T06:16:05Z
- Gate: static (only blind patch + FAIRNESS.md missing, by design), nop PASS, oracle PASS, patches PASS (16/16).

## Fairness revision (2026-10-17)
- test.sh: project tests run with TMPDIR inside the sandbox (test_checkpoint.py writes via tempfile); added checks/pass-checkpoint-sink.patch (guard in PaginationCheckpoint.__init__, no module-level pagination guard), expect pass.
- instruction.md: refusal (not redirect) required; T9 parenthetical removed.
- New security tests: test_file_move_source_outside (outside source must not be removed), test_excel_write_into_new_outside_directory (mkdir-before-check on a document writer). 25 security tests.
- Gate after revision: static, nop, oracle, patches all PASS (patches needed a re-run after one Docker compose infra error).
