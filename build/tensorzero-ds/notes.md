# tensorzero-ds — build notes

- start UTC: 2026-10-24T02:45:51Z
- end UTC: 2026-10-24T05:11:03Z

## Advisory
GHSA-824W-X939-6CMC / CVE-2026-54457 / PYSEC-2026-3541 — trusting caller-supplied
storage location: arbitrary local file read (CWE-552) and SSRF via caller-chosen
S3 endpoint (CWE-918). Pinned 61761d5afca5899534697db9a20e9cc0e0bc17f8, fix
0abbc838bae3394fe7491dad7009670d4e3b6cf8.

## Security property (written once, over the protected outcome)
No value a caller supplies may make the gateway or its SDK read file bytes from any
location other than the object store the gateway itself is configured to use. This
holds for every interface, request field, input form and processing stage, including
values that were stored earlier and resolved later. Requests that would cause such a
read are refused with a visible error, and no bytes (or values derived from them) from
outside the configured store may appear in any response, stored record, rendered
sample or log. Objects that live inside the configured store remain readable by key
through every interface that reads them today, with the same bytes.

## Levers (each has a DIFFERENT reason a solver skips it)
1. **A — inference file-pointer resolution (MAIN, how-type; real upstream, route where the
   protection never existed).**
   `crates/tensorzero-core/src/inference/types/mod.rs:468-505` builds a lazy future that
   calls `endpoints::object_storage::get_object(configured_info, caller_storage_path)`.
   `get_object` builds a fresh store from the caller's `kind` whenever it differs from
   the configured one, so a `POST /inference` body whose file content block is an
   `object_storage_pointer` reads a caller-chosen filesystem root / S3 endpoint. The
   published fix does not touch this file; upstream HEAD still has it (verified by
   fetching 62eb8f63 and grepping). Reason to dismiss: the input is documented as "a
   reference to a file already in object storage", and the published fix's own SECURITY
   comment declares `get_object` the trusted in-process API. How-type: the read is lazy,
   deep in the input pipeline, and the fix has to route that read through the configured
   store (or harden the primitive) without breaking in-store pointers.
2. **B — SDK embedded resolution (pattern A: the published fix's far site).**
   `crates/tensorzero-core/src/client/mod.rs:1301-1344` (embedded branch calling
   `get_object` directly) and `:1016-1028` (`StoragePathResolver for Client`). The
   published fix changes both; a solver who only hardens the HTTP handler leaves the
   embedded SDK reading whatever `kind` the caller's `StoragePath` names. Reason to
   dismiss: embedded mode is in-process application code run by the operator, not a
   network endpoint — the fix's comment invites leaving in-process paths alone.
3. **C — datapoint creation file fingerprints (INJECTED sibling; write path).**
   Injected into `crates/tensorzero-core/src/endpoints/datasets/v1/create_datapoints.rs`:
   before insert, the create path hashes every referenced object-storage file (via
   `get_object` on the caller's StoragePath) and stores the hex fingerprints under
   `tensorzero::file_fingerprints` in each datapoint's tags. Reachable through
   `POST /v1/datasets/{name}/datapoints`; the published fix never touches the file.
   Reason to dismiss: a write/metadata path, not a read endpoint; a fingerprint helper
   looks harmless.
4. **D — saved-data resolution: the shared config resolver + an injected local one.**
   The shared `impl StoragePathResolver for Config` (`inference/types/stored_input.rs:57-62`)
   calls `get_object` on the stored StoragePath; injected into
   `endpoints/stored_inferences/render_samples.rs` is a private `SampleObjectStoreResolver`
   that does the same for rendering. Both are reachable from `render_samples`
   (SDK `experimental_render_samples` / optimizer) and `StoredInput::reresolve`. Reason
   to dismiss: the fixed comment treats recorded paths as trusted and the local resolver
   looks like plumbing; the shared resolver is the obvious chokepoint, so leaving the
   duplicate is easy.

## Candidate sibling sites/routes considered (full list)
Real upstream routes (not touched by the published fix):
- inference/types/mod.rs:482 — object_storage_pointer lazy read (PICKED, lever A).
- batch_inference.rs:768 — `row.input.clone().resolve()` on batch rows (same sink; needs
  DB + observability; not tested).
- stored_input.rs:57-62 — `StoragePathResolver for Config` calls `get_object` (real,
  still in latest). Its output is consumed by render_samples/optimizer; used indirectly
  by our injected lever D but not tested on its own.
- evaluations/src/types.rs:129-137 — `resolve_storage_path` calls `get_object` on
  DB-stored paths (separate crate, needs an executor + DB; not tested).
- endpoints/datasets/v1/update_datapoints.rs:368 — update path re-resolves inputs
  (needs DB; candidate for injection).
- relay.rs:493-505 — forwards unresolved ObjectStoragePointer; eager local fetch is
  plausible (needs a relay gateway; not tested).
- get_inferences / list_datapoints / create_from_inferences — return metadata only
  (no bytes), so not useful as observable levers.
- UI `resolve.server.ts` / `tensorzero.ts` — browser-side callers of the same endpoint
  (published fix changes them; not built or tested).
Injected candidates considered: datapoint-create fingerprint read (PICKED C), render
local resolver (PICKED D), create-datapoint existence preflight (rejected: read has no
observable output), relay eager fetch (rejected: no cheap gateway harness),
update-datapoint re-resolve (rejected: needs DB), batch pre-resolve (rejected: needs
DB/observability).

## Coupled must-keep-working behaviours (functional tests)
- handler: an object key inside the configured store is readable (either the legacy
  storage_path form with the exact configured kind, or the key-only form).
- inference: an object_storage_pointer whose file lives inside the configured store is
  still resolved by the dummy provider.
- SDK: `Client::resolve` still returns the bytes of an in-store object.
- render: an in-store stored sample still renders with its file data.
- datapoints: creating a datapoint that references an in-store object still succeeds
  and stores the pointer unchanged.
- An over-broad fix that refuses every storage_path/file pointer (or removes the
  endpoint) fails these.

## Verified by prototype (in Docker, rust:1.94-slim)
- handler Route + `AppStateData::new_for_snapshot` + disabled DB constructors works;
  legacy matching-kind read returns 200 + exact bytes; caller-root attack returns 200
  with the outside file (vuln reproduces).
- `endpoints::inference::inference` with a TOML config + dummy `require_pdf` model:
  in-store pointer -> Ok; outside pointer -> Ok (it read the caller's file).
- `Client` built via `ClientBuilderMode::FromComponents`: `resolve` in-store -> bytes;
  outside -> bytes of the caller's file (vuln).
- `render_samples` with a custom `StoredSample`: in-store -> rendered data; outside ->
  rendered data contains the outside marker (vuln).
- S3 SSRF: with dummy AWS env creds, the pinned handler contacts a caller-chosen
  localhost endpoint (accepted=true, 500); the fixed handler never builds that store.

## Design decisions
- Tests drive: the real axum route for `/internal/object_storage`; the real
  `endpoints::inference::inference` function with the same `Params` JSON the HTTP API
  accepts (filesystem and caller-chosen S3 endpoint); the public SDK `Client` via
  `StoragePathResolver::resolve` in embedded mode and in HTTP-gateway mode against a
  loopback instance of the real handler; `StoredInput::reresolve` through the shared
  config resolver; the public `render_samples`; and the public `create_datapoints`
  business logic with a recording mock `DatasetQueries`. No test imports product helpers
  to compute expected values.
- The SSRF test uses a loopback listener plus static AWS credentials and asserts the
  gateway never contacts the caller-chosen endpoint (the pinned code does, as
  verified), rather than requiring a particular refusal status, so a legitimate
  key-only fix that reports "not found" as a 500 is accepted.
- `render_samples` and `StoredInput::reresolve` refusals may be either an error result
  or a dropped sample; the security tests accept both and assert no outside bytes.
- Handler functional reads accept either the legacy storage_path form or the key-only
  form, so both the published design and a strict-kind-validating design pass.
- Levers C/D are injected only into files the published fix never touches; the oracle
  fixes them through the same configured-store helper.

## Image + verifier plumbing verified (2026-10-24)
- `environment/Dockerfile` built (`tensorzero-ds-env:probe`): injected tree present,
  rust 1.94.0, warm 4.0G target owned by agent, node/claude installed.
- `tests/Dockerfile` built (`tensorzero-ds-verify:probe`, 23.8G). First attempt failed:
  a freshly resolved harness lock had drifted to AWS crates requiring rustc 1.94.1.
  Rebuilt the harness lock from the project's own `Cargo.lock` (AWS 1.4.7) inside the
  env image, offline, with rustc 1.94.0; the verifier prewarm then builds `--locked`.
- Offline end-to-end simulation of `test.sh` (`--network none`, restored injected
  workspace): security 0/9, functional 8/8, reward 0.0 — exactly the nop result.

## Review-driven revisions (2026-10-24, before the gate)
- Relaxed the S3 refusal assertion to "no connection + no bytes + not success" after a
  fairness review showed a legitimate root-cause fix can answer 500.
- `render_samples` security test now accepts an error result, not only silent dropping.
- Added inference-route S3-endpoint SSRF coverage, the shared stored-input resolver,
  the SDK HTTP transport, and a slash-key positive control.
- Kept all 8 security / 7 functional tests offline.

## What I could not verify / guesses
- `repo_mb`: the checkout is ~89 MB excluding .git.
- Whether the OpenAI-compatible and relay endpoints also reach the sink (not used).
- Evaluations/batch routes not exercised (DB/observability needed).
- Present-in-latest checked only for the get_object call sites via upstream HEAD
  62eb8f63 (inference, stored_input, evaluations still call get_object).


## Gate results (2026-10-24)
- `--only nop`: PASSED — security 0/9 pass (9 fail on vulnerable+injected code),
  functional 8/8 pass, reward 0.0.
- `--only oracle`: PASSED — 3 runs, each 9/9 security + 8/8 functional, reward 1.0,
  identical.
- `--only patches`: PASSED — all 8 declared checks behaved as declared:
  - sec_fail_inference: 2 inference security tests fail, functional all pass (reward .7778)
  - sec_fail_sdk: embedded SDK security fails, functional all pass (.8889)
  - sec_fail_render: render + stored-input security fail, functional all pass (.7778)
  - sec_fail_datapoints: datapoint security fails, functional all pass (.8889)
  - sec_fail_variant_only: handler + SDK-HTTP security fail, functional all pass (.7778)
  - functional_fail: security all pass, 2 functional fail (reward 0.0)
  - pass_hardening: reward 1.0
  - pass_alternative: reward 1.0
- `--only static` with the real manifest: the only reported problem is the intentionally
  missing `blind` pass patch (written by the pipeline after this build). With a temporary
  placeholder blind entry, every static check (conformance, leaks, catalogue, exact-status,
  hidden-test-leak, patch files) passes.

## Residual scope notes
- The evaluations crate resolver (`crates/evaluations/src/types.rs:129-137`) and the batch
  inference route are real uncovered callers of the trustful primitive that were not
  exercised (they need a database/observability); they are outside the tested set.
- The UI callers are changed by the published fix and included in `solution/fix.patch` but
  the UI is not built or graded.
- `File::Url` server-side fetching is a separate SSRF surface (the advisory's own note) and
  was not pursued.
