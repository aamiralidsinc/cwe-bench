# FAIRNESS review: docling-file-disclosure

Reviewer did not write the tests. Files read: instruction.md, tests/ (security, functional, test.sh,
score.py, and the relevant project tests), solution/fix.patch, manifest.json, notes.md, checks/*.patch.
Nothing was run.

## 1. Per-test fairness

Security tests pass if docling refuses (exception or non-success status gives `doc=None`), or if none of
these four outputs contain the marker pixels: JSON EMBEDDED, JSON REFERENCED (copied files), Markdown
EMBEDDED, HTML EMBEDDED.

| Test | Asserts | Instruction basis | Correct fix could fail? | Risk |
|---|---|---|---|---|
| security/test_sec_json_input.py::test_json_picture_absolute_path | Converting a JSON file whose picture names an absolute local path does not leak the file | "Observed impact" example; Required behaviour bullet 1 | no | low |
| security/test_sec_json_input.py::test_json_picture_relative_path | Same, with the path relative to the CWD | "in any form" (bullet 1); "close variants" | no. A fix that allows relative paths "inside CWD" fails, and that is correct | low |
| security/test_sec_json_input.py::test_json_picture_file_uri | Same, with a `file:` URI | "in any form"; standard expert knowledge: `file:` URIs are local filesystem references | no | low |
| security/test_sec_json_input.py::test_json_page_image_path | A page image (not a picture) names a local file and is copied in REFERENCED save | "anywhere in the document" | no | low |
| security/test_sec_saved_archive.py::test_archive_document_images | `ConversionAssets.load(zip)` with local picture and page refs does not leak them | "wherever docling reads such serialized document data from"; "often comes from other people, pipelines or machines" | no, if the engineer follows "wherever". It is "maybe" only for someone who treats the archive as trusted own output, which the instruction rules out | medium (discoverability, not correctness) |
| security/test_sec_service_result.py::test_service_document_images | An in-body service result (in-process docling-serve fake) with local refs does not leak them | same "wherever" sentence; standard expert knowledge: a service response is remote input. The repo's own `test_convert_presigned_bundle_rejects_image_outside_bundle` already treats service output as hostile | no | medium (discoverability) |
| functional/test_func_json_input.py::test_embedded_picture_is_kept | A `data:` picture keeps its exact URI and embeds | "Embedded images (data: URIs) load and export exactly as today" | no | low |
| functional/test_func_json_input.py::test_remote_picture_link_is_kept | An https picture link keeps its URI | "Remote image links ... stay in the document unchanged" | no | low |
| functional/test_func_json_input.py::test_embedded_page_image_is_kept | A `data:` page image is kept and decodes to the same pixels | data: bullet | no | low |
| functional/test_func_json_input.py::test_document_content_survives_alongside_images | Text, table and three pictures survive; both data: images embed | "Text, tables and every other part ..." | no | low |
| functional/test_func_json_input.py::test_stream_input_round_trips | A stream input's `export_to_dict()` equals the input exactly (data: plus http) | "exactly as today"; "unchanged" | no for a filter-only fix. It fails a fix that rewrites or normalises safe refs, and that is intended | low |
| functional/test_func_saved_archive.py::test_archive_round_trip_keeps_images | Save then load of an archive keeps data:/https refs, table, page image | "wherever docling reads ..." in Must-keep bullet 3; data:/remote bullets | no | low |
| functional/test_func_service_result.py::test_service_document_keeps_images | A service result keeps data:/https refs, table, page image | same | no | low |
| project tests (6 files, 252 tests), notably test_service_client_sdk_unit.py::test_convert_presigned_bundle_materializes_embedded_images and ::test_convert_presigned_bundle_rejects_image_outside_bundle | The bundle's own relative artifacts are still embedded; an out-of-bundle ref still fails with "outside the bundle" | "The project's existing test suite" (the tests are visible to the solver in /app/tests) | maybe: a fix that filters the bundle document before `_embed_referenced_images` fails both tests. The engineer can see this by running the project's own suite | medium |

## 2. Leniency

| Property / trap | Most plausible wrong fix | Caught? |
|---|---|---|
| S1 relative path | Drop only absolute `Path` refs | yes: test_json_picture_relative_path (abs_picture_only.patch) |
| S2 `file:` URI | Drop `Path` refs only | yes: test_json_picture_file_uri (paths_only.patch) |
| S3 page image | Walk `doc.pictures` only | yes: test_json_page_image_path (pictures_only.patch) |
| T1 archive load | Fix only the JSON backend (the published fix) | yes: test_archive_document_images (no_archive.patch, published_fix_only.patch) |
| T2 service result | Filter only the artifact/bundle paths | yes: test_service_document_images (service_artifacts_only.patch, no_service.patch) |
| over-fix | Drop all refs, drop http(s), crash on any image, filter bundle before embedding | yes: functional tests and project tests (refuse_all, drop_remote, crash_on_images, adjacent_bundle patches) |

**Wrong fixes no test catches:**

1. **T2, filter in-body only (MEDIUM).** Filtering only `_build_conversion_result` (client.py:428) passes every test. It leaves two routes open:
   - the presigned JSON artifact (`_document_from_artifact`, client.py:1784);
   - the resource bundle after embedding (`file:`/absolute refs that the containment guard skips).

   `DoclingServiceClient.convert()` tries the presigned route first (project test `test_convert_falls_back_to_inbody...`), so the high-level API's default path has no security coverage. notes.md already lists this as "Not verified".
2. Async client (`AsyncDoclingServiceClient`): it is not checked whether it has its own materialisation path. Unverified.
3. Table/code/form item images and non-file schemes (ftp:, s3:): no export sink opens them at this docling-core version, so this is n/a for disclosure. Accepted.
4. Opt-in: no test checks that an opt-in exists or works. That is fine, because the instruction makes it optional.

## 3. Hints

- "in any form and anywhere in the document": a soft paraphrase of the S1–S3 variant list (forms = path/relative/`file:`; anywhere = page images). It names nothing concrete, and without it S3 would be less fair. **Keep.**
- "This holds wherever docling reads such serialized document data from, not only for the example above.": signals more than one route (T1, T2) without naming any. This sentence is what makes T1 and T2 fair. **Keep.**
- "documents are routinely passed between systems in this form and converted again, for example to re-export them": a mild nod toward archives and services. Neutral enough. Optional neutral wording: "documents are routinely exchanged in this form."
- "The example above is one example, not the full set." This duplicates Constraint 1 and hints that there is more than one flaw, but gives no count. Acceptable.
- "Embedded images (`data:` URIs)" contains the leak term "uri". It is needed to define the functional contract. **Keep.**
- "either leaves that image out ... or refuses the document": this describes the accepted outcomes, not one mechanism, and both are accepted by the tests (alt_refuse.patch). **Keep.**

No file, function, class, route name or flaw count appears.

## 4. Realism

- T1 (`ConversionAssets.load`) and T2 (`client.py:428`) are unmodified upstream code, still present in upstream HEAD according to notes.md, and reached through public APIs. Not planted.
- In the T2 test, the server-side document comes from monkeypatching the repo's own fake (`_fake_document`). This stands in for any service returning such JSON, and the client code path is real. Acceptable. The threat model (a malicious or compromised service, or attacker JSON relayed through a service) is supported by the repo's existing out-of-bundle test.
- S1–S3 are input shapes at the published fix site. Realistic.
- Nothing looks contrived.

## 5. Verdict

**READY, with one recommended tightening (not blocking)**

The instruction makes every test fair, no test penalises a correct fix, and both designs (drop and refuse) are accepted.

Recommended before trial (leniency gap 1): add a security test, `test_sec_service_result::test_service_presigned_json_images`:
- Call `DoclingServiceClient.convert(source)` on the presigned JSON-artifact route, with a document carrying absolute and `file:` local refs.
- Drive it the way the project's own tests do (`MethodType` on `_submit_convert_task`, `_wait_for_terminal_status`, `_fetch_presigned_result`, `_download_artifact_bytes`). Or relax the loopback guard for the fake, if a public option exists.

Without this test, an in-body-only service fix earns full reward. If the client accepts "one route per concept", the task can be trialled as is, with gap 1 disclosed.
