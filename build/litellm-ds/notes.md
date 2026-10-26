# litellm-ds — build notes

- Start UTC: 2026-10-18T19:45:16Z
- Track: injected. Pattern A+B.
- Pinned: 76ffefcc1c36f4e78178ca0278d38385cafa6ec6 (direct parent of the published fix
  473f72e6; the other two ids in the candidate record are the same merge PR).
- Published fix: `git diff 76ffefc 473f72e -- litellm/` (source part kept in
  `solution/fix.patch`).

## Plan (written before building)

Problem shape: the proxy decides (1) whether a caller may pick the outbound destination — the
provider `model`/`file_id` identifier, an `api_base`, a provider endpoint field, or an
observability host — and (2) whether admin-configured credentials may follow a caller-chosen
destination.

### Levers (one line each)

| id | pattern | shape | where (pinned file:line) | reason a solver skips it |
|----|---------|-------|--------------------------|--------------------------|
| T1 | A landing | URL-valued `model` in the Azure/engines path overrides the body model *after* the body guard ran (chat/completions, embeddings) | `litellm/proxy/common_request_processing.py:891` | "the guard already ran; the path segment is just the deployment name" |
| T2 | A far site | same path-model override in the image-generation handler (its own model-selection step) | `litellm/proxy/image_endpoints/endpoints.py:99` | second implementation in a separate module; fixing the shared processor "covers the proxy" |
| T3 | A far site | multipart bracket-notation metadata (`litellm_metadata[langfuse_host]`, `metadata[api_base]`) is flat at auth time, so the request-body bouncer never sees the banned key | `litellm/proxy/auth/auth_utils.py:439` + `litellm/proxy/openai_files_endpoints/files_endpoints.py:376` | "metadata is not a destination field, and the dict/JSON-string shapes are already checked" |
| T4 | A far site | `/health/test_connection` merges the stored deployment's credentials under a caller-supplied destination field (and keeps `litellm_credential_name` by reference) | `litellm/proxy/health_endpoints/_health_endpoints.py:1830` | admin "test connection" utility documented to load config and allow overrides |
| T5 | B (uncovered route) | `/queue/chat/completions` never calls the request-data guard; query/body `model` reaches `llm_router.schedule_acompletion` (real, unmodified upstream) | `litellm/proxy/proxy_server.py:13064-13151` | experimental route, `include_in_schema=False`; "not a supported API" |
| T6 | injected | multipart bracket form for the *other* nested config container (`extra_body[api_base]`) is reconstructed by the files handler and never checked (the published fix covers only metadata prefixes) | `litellm/proxy/openai_files_endpoints/files_endpoints.py` (injected producer) + `litellm/proxy/auth/auth_utils.py:435-438` | solver fixes the reported metadata prefix only, not the general nested-container rule |
| T7 | injected | Azure-compatible path model added to the moderations endpoint, assigned after `add_litellm_data_to_request`, same copy-paste shape as the real bug | `litellm/proxy/proxy_server.py` (injected decorator + model line) | "the report was about the shared processor / chat and images; moderations is a different endpoint" |

### Security tests (per lever)

- T1: POST `/openai/deployments/{provider}/{url}/chat/completions` and
  `/openai/deployments/{provider}/{url}/embeddings`, body model ordinary -> any 4xx and the
  provider callable is not invoked (chat also via `/engines/{model:path}/...`).
- T2: POST `/openai/deployments/{url}/images/generations` -> 4xx, `aimage_generation` not called.
- T3: POST `/v1/files` multipart with `litellm_metadata[langfuse_host]` and
  `metadata[api_base]` -> 4xx, `acreate_file` not called.
- T4: POST `/health/test_connection` with a configured model name plus caller `api_base` /
  `aws_bedrock_runtime_endpoint` / `litellm_credential_name` -> the configured secret never
  appears in the params handed to the health check.
- T5: POST `/queue/chat/completions` with URL-valued model -> 4xx, provider not called.
- T6: POST `/v1/files` with `extra_body[api_base]` -> 4xx, `acreate_file` not called.
- T7: POST `/openai/deployments/{url}/moderations` -> 4xx, `amoderation` not called.

Each security test also asserts the positive control lives in functional/: an admin-allowlisted
destination host still works.

### Coupled must-keep-working (functional)

- `litellm.provider_url_destination_allowed_hosts` entry -> URL-valued model still routes on the
  path-model routes and the queue route.
- Ordinary deployment names containing `/` (e.g. `dall-e-3`, `openai/gpt-4o` as a name) still
  route; an `image_edits` path model still works.
- Benign bracket metadata (`litellm_metadata[tags]`, `[spend_logs_metadata][owner]`) reaches the
  call; `allow_client_side_credentials: true` restores banned-key passthrough (metadata and
  extra_body).
- `/health/test_connection`: configured model alone inherits config credentials; add-model flow
  with its own api_base+api_key is tested as sent; `allow_client_side_credentials` restores
  inheritance; stored-credential reference kept when the request sets no connection field.
- The affected-area project tests from the pinned tree (auth_utils, health endpoints, azure image
  routes, provider URL guard) still pass.

### Injected siblings (2)

- T6: form bracket parsing extended to `extra_body[` in the files handler; realistic extension of
  the same producer the file route already runs. Fix: apply the auth-time nested-container check
  to every nested config/metadata container's bracket form, not just metadata.
- T7: Azure-compatible moderations route with the model-selection block copied from the other
  handlers. Fix: apply the destination check wherever the path model is selected.

Both are reachable through the real HTTP entry point, are covered by the instruction invariant
("no value of the model identifier or destination parameter ... however it is supplied"), and sit
outside every file the published fix changes.

## Verified (this session, pinned tree + venv)

- Bracket metadata on `/v1/files`: pinned 200 + `acreate_file` called with
  `litellm_metadata.langfuse_host = https://attacker.invalid`; published fix -> 401, no call.
- Path model: chat/completions (200 + `litellm.acompletion` called with URL), embeddings (200 +
  provider called), image generation (200 + `aimage_generation` called); published fix -> all 400,
  no call. Completions route enters real provider network in the local venv if
  `litellm.atext_completion` is not mocked (must mock it in tests).
- `/health/test_connection`: pinned passes `api_key=sk-configured-secret` with caller
  `api_base=https://attacker.invalid/v1`; published fix drops it.
- `/queue/chat/completions`: pinned and published fix both reach the provider with
  `model=huggingface/https://attacker.invalid` (real B route).
- Injected siblings on pinned: `extra_body[api_base]` -> `acreate_file(extra_body={"api_base":
  ...})`; moderations path model -> router `amoderation` called with the URL (must patch
  `proxy_server.llm_router.amoderation` because the Router binds its callables at init).
- Project tests at pinned in venv: provider-guard + azure routes 20/20; auth_utils + health
  endpoints 267 passed, 1 failed (`test_health_liveliness_endpoint`, a <100 ms latency assertion
  on a cold process - environmental; will deselect it in the project-test run).
- No regression tests for this advisory exist at the pinned commit (fix commit adds them only).

## Build / gate progress

- Image built (python:3.12-slim + `.[proxy]` + prisma + pytest toolchain + respx). Offline runs
  (`docker run --network none`, tests mounted read-only at /tests): nop security 0/21,
  functional 298/298; oracle 21/21, 298/298, reward 1.0.
- All 16 checks patches verified (local venv and, for the three `pass`/`functional_fail`/two
  representative `security_fail` patches, in the offline container): each behaves as declared.
- The three wall-clock liveness/liveness/readiness project tests are excluded in test.sh
  (cold TestClient request exceeds their 100 ms bound here); pytest's `--deselect` prefix also
  excludes the five `test_health_readiness*` siblings.
- Gate static: only the two expected outstanding items (blind patch, FAIRNESS.md).
- Gate nop: PASSED.
- Gate oracle: two runs reached reward 1.0 (21/21, 298/298, identical); the third run of each
  attempt was cut by `docker compose ... network ... not found`, a Docker-network race on this
  shared VM where 14 other gate stages were running concurrently. Retried until three
  consecutive runs pass.

## Pre-trial fairness revision (2026-10-19)

Applied `build/litellm-ds/FAIRNESS.md`:

- Every security test now parametrises the attack destination over
  `https://example.invalid/v1`, `https://attacker.example/v1` and
  `http://evil.example/v1` (path, image, queue, moderation, form, health), so a
  route-level hardcode of the example host or of the `https://` scheme is caught.
- Form cases cross the containers and fields (`metadata`, `litellm_metadata`,
  `extra_body` x `api_base`, `langfuse_host`, `aws_bedrock_runtime_endpoint`).
- The non-queue `/v1/chat/completions` query-string `model` shape is now a security test.
  Verified on the pinned tree that it reaches `acompletion`; the oracle refuses it.
- An allowlist-embedding attack (`evilexample.test`, `example.test.attacker.example`)
  catches substring/endswith route-level allowlist matching.
- Health security tests assert the outcome is 2xx or 4xx (never 5xx) in addition to the
  credential/reference absence.
- A second allowlisted host (`trusted.example`) is exercised by the functional path and
  queue allowlist tests.
- `/openai/deployments/{model:path}/images/edits`: verified NOT reachable. The handler
  sets `data["model"]` from the path before entering the shared request processing, so
  the pinned body check already refuses the attack with 400 and no provider call. No
  test or oracle change is needed.
- New checks patches: `sf-example-host-only` (hardcodes `example.invalid` at the route
  checks), `sf-https-only` (route checks accept only `https://`), and
  `sf-health-crash-as-refusal` (health route 500s when a destination is supplied without
  a key). All three fail security while keeping every functional test green.
- Instruction rewritten: removed the "Names the tests use" field/container list, the
  system-level route/encoding enumeration, the flaw-count/variant sentences; replaced the
  deployment-name and connectivity examples with neutral contracts; the refusal contract
  now states 4xx and the management route's 2xx-continues-without-credentials outcome.

## Open / not verified

- The published fix's `_config_base_for_health_check` behaviour with a real credential store was
  not traced; tests assert on the params handed to `litellm.ahealth_check`.
- Whether `langfuse_host` inside `litellm_metadata` reaches an observability client end to end
  was not traced; the security test asserts the destination-selecting value reaching the
  provider call path, which is the boundary the request-body check enforces.
