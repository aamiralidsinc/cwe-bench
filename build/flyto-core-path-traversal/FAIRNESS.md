# FAIRNESS — flyto-core-path-traversal

Reviewer: pre-trial fairness/leniency review (BUILDER.md 3h). Static review only; nothing was run.
Inputs read: instruction.md, tests/ (conftest, score.py, test.sh, security/, functional/, functional/project/),
solution/fix.patch, manifest.json, notes.md, checks/*.patch. The sf-*/ff-*/pass-* patches are oracle variants with one change each; I checked their shape and did not re-run them.

## 1. Per-test fairness

Abbreviations: S = tests/security/test_output_confinement.py, F = tests/functional/test_inside_sandbox.py,
P = project tests run by test.sh. "Refused" = conftest.refused (status ≥400, or `ok` not true, or inner `ok` false)
**and** the outside snapshot is unchanged.

### Security (S)

| test | asserts | instruction basis | correct fix could fail? | risk |
|---|---|---|---|---|
| S::test_image_download_explicit_path_outside | refused; outside unchanged (no `fresh/` dir) | Observed impact example; "No caller-supplied parameter… created" | maybe: a fix that *redirects* the path into the sandbox (returns ok) fails. See note R1 | low |
| S::test_image_download_default_name_into_outside_dir | default name in outside `output_dir` refused, no `dl/` | "includes locations the module derives… from a given output directory" | maybe (R1) | low |
| S::test_image_download_refusal_creates_no_directory | output_path outside while output_dir inside is refused, and no `made/` dir | "nothing outside the sandbox changes. That includes directories…" | maybe (R1) | low |
| S::test_image_compress_absolute_outside | absolute outside refused | "absolute" spelling | maybe (R1) | low |
| S::test_image_convert_into_new_outside_directory | refused and `newdir/` not created | "That includes directories the run would otherwise have created" | maybe (R1) | low |
| S::test_image_crop_dot_dot_segments | `inside/../../outside/...` refused | "with `..` segments" | maybe (R1) | low |
| S::test_image_resize_default_output_next_to_outside_input | default `_resized` beside an outside input refused | "a name built from an input file" | maybe (R1). Reads stay unchanged and only the derived *write* is refused, so this is consistent | low |
| S::test_image_rotate_through_symlink_in_sandbox | sandbox symlink to outside refused | "through a symbolic link inside the sandbox that points outside it" | maybe (R1) | low |
| S::test_image_watermark_absolute_outside | absolute outside refused | "absolute" | maybe (R1) | low |
| S::test_qrcode_svg_outside | svg variant refused | "every file a module writes" | maybe (R1) | low |
| S::test_qrcode_png_outside | png refused | same | maybe (R1) | low |
| S::test_excel_write_outside | refused | "No caller-supplied parameter of any module" | maybe (R1) | low |
| S::test_pdf_fill_form_outside | refused | same | maybe (R1) | low |
| S::test_pdf_to_word_outside | refused | same | maybe (R1) | low |
| S::test_word_to_pdf_default_output_next_to_outside_input | derived `.pdf` beside an outside input refused | "a name built from an input file" | maybe (R1) | low |
| S::test_pdf_generate_outside | refused | "any module" | maybe (R1) | low |
| S::test_word_parse_images_outside | `images_output_dir` outside refused | "every file a module writes, for any purpose" | maybe (R1) | low |
| S::test_csv_write_absolute_outside | absolute outside refused | "absolute" | maybe (R1) | low |
| S::test_json_to_csv_absolute_outside | refused, no `sub/` | "absolute"; "directories… created" | maybe (R1) | low |
| S::test_file_copy_destination_outside | refused | "any module… created" | maybe (R1) | low |
| S::test_file_move_destination_outside | refused; source still present | "any module"; a refused run "changes nothing" | maybe (R1) | low |
| S::test_pagination_state_outside | interrupted run with outside checkpoint refused, nothing written | "every file a module writes, for any purpose" | maybe (R1) | low |
| S::test_pagination_completed_run_leaves_outside_file | pre-existing outside file not overwritten or removed; refused | "overwritten… or removed" | maybe (R1) | low |

**R1, refuse vs redirect.** Every security test requires the run to be *reported as failed*. The instruction says "A refused run fails cleanly…" but never says that an outside location **must** be refused. Another fix also satisfies the first bullet: clamping or rebasing the path into the sandbox (e.g. `sandbox/basename(path)`) and returning ok. A competent engineer would usually refuse, so this is a medium risk, not high. It costs one sentence to close (see Verdict).

### Functional (F)

| test | asserts | instruction basis | correct fix could fail? | risk |
|---|---|---|---|---|
| F::test_image_module_absolute_path_inside[×7] | absolute in-sandbox writes, incl. new sub-dirs, succeed | "absolute paths… sub-directories that do not exist yet" | no | low |
| F::test_qrcode_svg_inside | svg written as `.svg` | "work exactly as today" | no | low |
| F::test_image_download_explicit_path_inside | new `fresh/` dir inside works | "sub-directories… created as today" | no | low |
| F::test_image_download_default_name_into_dir | default name into new inside dir | "default output locations that fall inside" | no | low |
| F::test_image_resize_default_output_name | `_resized` default inside | same | no | low |
| F::test_image_crop_dot_segments_staying_inside | `sub/../sub/./c.png` accepted | "spellings with `.` or `..` that still end up inside" | no. Explicitly allowed, so a `..`-substring reject is correctly caught | low |
| F::test_relative_paths_inside | relative paths (cwd = sandbox) for rotate and csv | "relative paths (resolved as today)" | no. cwd == sandbox, so cwd- and sandbox-relative resolution both pass | low |
| F::test_excel_write_inside | new sub-dir works | as above | no | low |
| F::test_pdf_fill_form_inside | works | "work exactly as today" | no | low |
| F::test_pdf_to_word_inside | new sub-dir | as above | no | low |
| F::test_pdf_to_word_default_output | derived `.docx` inside | "default output locations that fall inside" | no | low |
| F::test_word_to_pdf_default_output | derived `.pdf` inside | same | no | low |
| F::test_word_to_pdf_inside | new sub-dir | same | no | low |
| F::test_pdf_generate_inside | works | same | no | low |
| F::test_word_parse_images_inside | exactly `["image_1.png"]` | "exactly as today" | no (existing naming) | low |
| F::test_word_parse_without_images | parse with no extraction | reads unchanged | no | low |
| F::test_csv_write_inside | content exact | "as today" | no | low |
| F::test_json_to_csv_inside | new sub-dir | as above | no | low |
| F::test_file_copy_inside / test_file_move_inside / test_file_write_inside | inside works; move removes the inside source | "Keep all legitimate use" | no | low |
| F::test_pagination_checkpoint_inside_and_resume | inside checkpoint + `.jsonl` written, resume works, state cleared | "Locations inside the sandbox work exactly as today" | no | low |
| F::test_pagination_without_checkpoint | no checkpoint path still works | as today | no. A guard that crashes on `None` would fail, but that is a real regression | low |

### Project (P), run by test.sh from pristine copies

| test | asserts | instruction basis | correct fix could fail? | risk |
|---|---|---|---|---|
| P tests/modules/test_new_modules.py::TestImageModules (5) | direct module calls write under `tmp_path` | "Keep all legitimate use" | no: `--basetemp` puts `tmp_path` inside the sandbox | low |
| P tests/browser/test_checkpoint.py::TestCheckpoint (10) | `PaginationCheckpoint` save/load/clear round-trips | "Keep all legitimate use" | **yes.** The fixture uses `tempfile.NamedTemporaryFile`, which writes to `/tmp/…json`. That is **outside** `FLYTO_SANDBOX_DIR=/tmp/flyto-grading/sandbox`, and `--basetemp` does not affect `tempfile`. Consider a fix that puts the confinement in `PaginationCheckpoint.save()/clear()`, or in `__init__`, where the file writes actually happen. That is a natural sink-level choice for "every file a module writes", and it fails ≈7 of these tests (save_creates_file, roundtrip, incompatible×2, clear, incremental, stopped_reason). The oracle passes only because it guards at the module. test.sh's comment ("pytest's temp dir sits inside the sandbox, where these tests write") is wrong for this file | **high** |

## 2. Leniency

| property / trap | most plausible wrong fix | caught? |
|---|---|---|
| Landing (image.download no-op check) | Fix only download's commonpath base (check against sandbox, keep mkdir before) | yes: S::test_image_download_refusal_creates_no_directory; checks/sf-mkdir-before-check.patch, sf-download-wrong-base.patch |
| T1 pagination state file | Leave the checkpoint alone ("internal state") | yes: S::test_pagination_state_outside, …_completed_run_leaves_outside_file; sf-no-pagination.patch |
| T2 document package | Fix image package only | yes: S excel/pdf_fill_form/pdf_to_word/word_to_pdf; sf-no-document-published.patch |
| T3 csv '..' check | Trust existing '..' check | yes: S csv/json_to_csv absolute; sf-no-data-writers.patch |
| T4 file.copy/move | Skip generic file ops | yes (destination): S file_copy/file_move; sf-no-file-ops.patch |
| T5 word.parse images | Treat as reader | yes: S::test_word_parse_images_outside; sf-no-word-parse.patch |
| T6 pdf.generate | Skip generator | yes: S::test_pdf_generate_outside; sf-no-pdf-generate.patch |
| T7 symlink | normpath/abspath prefix check | yes, **only on image.rotate**: S::test_image_rotate_through_symlink_in_sandbox; sf-normpath-no-symlinks.patch |
| T8 absolute vs '..'-only | Reject '..' only | yes: S compress/watermark/qrcode/csv; sf-dotdot-only.patch. An over-broad '..' reject is caught by F crop_dot_segments (ff-overbroad-dotdot-and-defaults.patch) |
| T9 derived defaults | Validate only explicit params | yes: S resize/download default/word_to_pdf default; sf-explicit-only.patch |
| T10 mkdir before check | Check after mkdir | yes **only on download, convert and json_to_csv** (S tests with a new outside sub-dir); sf-mkdir-before-check.patch |
| refuse-all / no-absolute | Over-restrict | yes: F; ff-refuse-all.patch, ff-no-absolute.patch |

**Wrong fixes no test catches:**
- **file.move with an outside `source`** (the outside file is *removed* by moving it into the sandbox). The instruction names "removed" explicitly, and the oracle validates source. No test covers it, so a destination-only guard passes. Medium.
- Lexical (non-realpath) check on every module except image.rotate: only rotate has a symlink test. Low, because a real engineer uses one helper.
- mkdir-before-check in excel_write, pdf_to_word `_ensure_output_dir`, pdf_generate and qrcode: their S tests write straight into the existing `outside/` dir, so no new directory is attempted. Low–medium.
- Unbuilt writers: browser.download, browser.screenshot, cookies export (documented in notes as not reproducible or not built). Accepted; pass-hardening.patch covers some of them.
- A fix that skips confinement when `FLYTO_SANDBOX_DIR` is unset (the cwd default). Tests always set it. Low.

## 3. Hints in instruction.md

| quote | concern | proposed neutral wording |
|---|---|---|
| "(for example, a name built from an input file or from a given output directory)" | Paraphrases T9 and names its two shapes (resize/word_to_pdf from input; download from output_dir) | "It includes output locations a module derives itself from other inputs when the caller gives none." (drop the parenthetical) |
| "That includes directories the run would otherwise have created." | Points at T10 | Acceptable for fairness. Optionally fold it in: "nothing outside the sandbox is created, changed or removed, directories included." |
| "absolute, relative, with `..` segments, or through a symbolic link inside the sandbox that points outside it" | Lists the T7/T8 variants | Standard expert knowledge, so it is defensible. Optionally: "This holds however the location is spelled or resolved." Low priority: removing it makes the symlink test lean on expert knowledge only |
| "This covers every file a module writes, for any purpose." | Generic pointer to T1/T5 | Keep: it anchors the fairness of T1 and does not name anything |
| "Some modules already refuse locations outside it; others do not." | Mild pointer to the existing guard (file.write / utils) | Keep: realistic report text |

No file, function or module names beyond the example's `image.download`. No flaw count.

## 4. Realism

All trap sites are unmodified upstream code at the pinned commit (manifest: no injected siblings). T1–T2 are published fix sites. T3–T6 are real upstream code that later upstream security commits also confined (notes: main 795d07e). Every one is reached through `POST /v1/execute`. Pagination is driven through a stub browser session, but the product code makes every file write, so I consider it legitimate. Nothing looks planted.

## 5. Verdict: **NOT READY**

Required changes:
1. **(high) test.sh, project run:** make `tempfile` land inside the sandbox so a sink-level guard in `PaginationCheckpoint` is not punished. For example, run the project pytest with
   `mkdir -p /tmp/flyto-grading/sandbox/tmp && TMPDIR=/tmp/flyto-grading/sandbox/tmp FLYTO_SANDBOX_DIR=… python3 -m pytest …`.
   The alternative is to drop tests/browser/test_checkpoint.py. Fix the misleading comment either way, then re-verify that the oracle, pass-* and checks still behave as declared, and add a pass-* patch that guards inside `core/browser/checkpoint.py`.
2. **(medium) instruction.md:** state that refusal is required. Add to the "refused run" bullet: "A run that would write outside the sandbox must be refused, not redirected to another location."
3. **(medium, leniency) tests:** add S::test_file_move_source_outside: move an outside file into the sandbox, expect refusal, and check the outside file is still present. The oracle already passes it.
4. Recommended: replace the T9 parenthetical with the neutral wording above. Optionally add one mkdir-before-check case for a document writer (e.g. excel.write into `outside/new/h.xlsx`).
