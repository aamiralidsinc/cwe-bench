# docling-file-disclosure: build notes

Start (UTC): 2026-10-17T06:25:05Z
End (UTC): 2026-10-17T07:20:41Z

## Levers
- T1 (B) docling/datamodel/document.py:572-576 ConversionAssets.load: a shared conversion archive's document.json names local images; dismiss: "your own saved output", not converter input.
- T2 (B) docling/service_client/client.py:428 (+1784, 1797-1799 in the oracle): a service-returned document names local images; dismiss: "your own docling-serve", and the bundle path already has a containment guard.
- S1 (shape) relative picture path, resolved against the CWD; dismiss: the report's example is absolute.
- S2 (shape) file: URI picture (disclosed by save_as_json EMBEDDED although pil_image refuses file:); dismiss: a URI, not a path.
- S3 (shape) page image (not an item) copied into a REFERENCED save; dismiss: the report shows a picture.
- Coupled: data: images and http(s) links kept on every route; text/tables unchanged; archive save/load round-trip; bundle relative artifacts still embedded (project test).

## Verified
- Pinned e4780063 is the sole parent of fix d4bb7768; the fix's 4 new tests are absent at the pinned commit.
- All 6 security tests fail on pinned by the disclosure assertion; all pass on the oracle. 7 functional + 252 project tests pass on both.
- Each check patch behaves as declared in a local run (scratch venv, same versions as the image).
- T1 and T2 still unfiltered in upstream HEAD 0e54294 (2026-10-16): document.py:578, client.py:428/1784/1797.
- Table/code/form item images reach no export sink in docling-core 2.98.0 (only ML enrichment), so untested.

## Not verified
- Whether a public upstream report exists for T1/T2.
- Presigned json artifact and bundle sub-routes of T2 are closed by the oracle but untested (one route per concept; the loopback SSRF guard blocks the fake's presigned URLs).
- Enrichment-model routes (picture description sending local images to a VLM API) need ML models; not exercised.

## Out of scope (one line each)
- DCLX archive backend yields local Path refs to its own extracted artifacts (legitimate); docling-core's load_from_doclang_archive not reviewed.
- CLI default --image-export-mode embedded turns a kept local ref into embedded output; the CLI needs torch so it is not driven.

## Gate
static: only blind patch + FAIRNESS.md missing (expected). nop PASSED (6 security fail, 259 functional pass). oracle PASSED (3 runs). patches PASSED (13/13 as declared).
