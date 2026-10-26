# FAIRNESS.md — litellm-ds

Pre-trial fairness and leniency review. I read `tasks/litellm-ds/instruction.md`, every file under
`tasks/litellm-ds/tests/`, `solution/fix.patch`, `environment/injection.patch`,
`build/litellm-ds/manifest.json`, `notes.md` and all nineteen `checks/*.patch`. I ran no tests,
Docker or gates, and did not consult any upstream advisory.

**State note.** The live `tests/` tree is the *pre-revision* suite. The revised
(parametrised/status-asserting) suite that `notes.md` describes and that the three new checks
(`sf-example-host-only`, `sf-https-only`, `sf-health-crash-as-refusal`) were built against exists
only in `build/litellm-ds/.fairfixed-snapshot/tests/`. Likewise the live `instruction.md` still
contains the "Names the tests use" paragraph and the variant/flaw-count sentences that `notes.md`
says were removed. This review covers the live files. The drift is a quality/leniency finding
(§2.3, §5b), not a correct-fix-fails finding.

## 1. Test fairness table

Scoring: `tests/score.py` gives 1.0 only when every security and every functional test passes; any
functional failure forces 0.0. The four `tests/functional/project/` files are pristine copies of
the project's own tests for the affected area and are run after being restored over `/app`; they
are grouped by file below (280 individual cases cannot usefully be repeated row-by-row, but every
assertion category is covered).

| Test (file::name) | What it asserts | Instruction sentence that makes it fair | Could a CORRECT fix fail it? | Risk |
|---|---|---|---|---|
| `security/test_path_model_destination.py::test_url_valued_path_model_is_refused` | URL-valued path `model` on `/openai/deployments/{…}/chat/completions` and `/engines/…` (three path shapes, body model ordinary) → 4xx and no provider call | "No value of a caller-supplied model … may become a URL-valued outbound destination, however the request delivers it: … URL path"; "Every route that accepts a model identifier" | No. Checking the effective path model (or the dispatched model) passes | low |
| `security/test_path_model_destination.py::test_url_valued_path_model_on_embeddings_is_refused` | Same on `/openai/deployments/…/embeddings` and `/engines/…` | Same | No | low |
| `security/test_image_path_model_destination.py::test_url_valued_path_model_on_image_generation_is_refused` | URL-valued path `model` on `/images/generations` → 4xx, no `aimage_generation` | "Every route that accepts a model identifier obeys these rules" | No; a fix that applies the rule only in the shared processor is not compliant with "every route", not a correct fix | medium (route discoverability) |
| `security/test_moderation_path_destination.py::test_url_valued_path_model_on_moderation_is_refused` | URL-valued path `model` on the Azure-compatible `/moderations` → 4xx, no `amoderation` | Same | No; the route is visible in the repository (injected decorator) and "every route" covers it | medium (discoverability) |
| `security/test_queue_destination.py::test_url_valued_model_on_queue_route_is_refused` | URL-valued `model` in body and in query on `/queue/chat/completions` → 4xx, no `acompletion` | "… it may arrive in the request body, in a query parameter …"; "Every route" | No. The route is real upstream code and visible | medium (experimental route) |
| `security/test_form_metadata_destination.py::test_bracket_notation_destination_is_refused` | Five multipart bracket fields (`litellm_metadata[langfuse_host]`, `litellm_metadata[api_base]`, `metadata[api_base]`, `extra_body[api_base]`, `extra_body[aws_bedrock_runtime_endpoint]`) → 4xx, no `acreate_file` | "… or as a bracket-notation form field"; the contract names `metadata`, `litellm_metadata`, `extra_body` and JSON-vs-bracket delivery | No. Generalising over the existing nested-container/banned-param sets passes; special-casing one container is not compliant | low |
| `security/test_health_connection_credentials.py::test_configured_credentials_do_not_follow_a_caller_destination` | Caller `api_base` / `aws_bedrock_runtime_endpoint` with a configured model → configured secret absent from the params handed to `ahealth_check` (3 cases) | "Credentials configured for a deployment must never be sent to a destination the request chose"; "including management routes that test a deployment's connectivity" | No. Refusing (4xx, no call) or continuing without credentials both pass | low |
| `security/test_health_connection_credentials.py::test_stored_credential_reference_does_not_follow_a_caller_destination` | Caller `api_base` → `litellm_credential_name` absent from the downstream params | "… and any reference to a stored credential, must not accompany it" | No | low |
| `functional/test_legit_routing.py::test_ordinary_chat_deployment_path_routes` | Ordinary path model `gpt-4o` → 200, provider called | "A deployment name that is an ordinary string … still routes"; "Keep every legitimate use working" | No | low |
| `functional/test_legit_routing.py::test_deployment_name_containing_a_provider_prefix_routes` | Path model `openai/gpt-4o` → 200, provider called | "A deployment name that is an ordinary string — including one containing a provider prefix and a slash — still routes" | No. Guards against a naive "reject any slash" fix | low |
| `functional/test_legit_routing.py::test_plain_body_model_routes` | Body model `gpt-4o` on `/v1/chat/completions` → 200 | Preservation | No | low |
| `functional/test_legit_routing.py::test_ordinary_image_deployment_path_routes` | Path model `dall-e-3` (not in the test config) → 200, `aimage_generation` called | Preservation; ordinary deployment names route | No, unless a fix invents deployment-existence validation, which the instruction never asks for | low |
| `functional/test_legit_routing.py::test_allowlisted_destination_still_routes_on_a_path_model` | `provider_url_destination_allowed_hosts = ["example.test"]`; URL-valued path model on that host → 200 | "The operator may explicitly allowlist destination hosts; allowlisted hosts keep working"; "Destinations on the operator's allowlist still route … in the path" | No. The allowlist mechanism is already in the repository | low |
| `functional/test_legit_routing.py::test_allowlisted_destination_still_routes_on_the_queue_route` | Same allowlist, URL-valued queue body model → 200 | Same | No | low |
| `functional/test_legit_routing.py::test_ordinary_queue_model_routes` | Ordinary queue body model → 200, provider called | Preservation | No | low |
| `functional/test_legit_routing.py::test_ordinary_moderation_deployment_path_routes` | Ordinary moderation path model → 200, `amoderation` called | Preservation | No | low |
| `functional/test_legit_routing.py::test_non_string_model_value_is_left_to_normal_validation` | A dict-valued `model` is not answered 400 with a "URL-valued" message | Standard expert knowledge: type validation is the request validator's job; the rule is about URL-valued strings | No. The assertion is deliberately weak | low |
| `functional/test_legit_health.py::test_configured_model_inherits_configuration_credentials` | Model alone → 200, config `api_key`/`api_base` inherited | "A configured model named without any connection field still inherits the configuration's endpoint and credentials" | No; always-strip is non-compliant | low |
| `functional/test_legit_health.py::test_complete_request_is_tested_as_sent` | Request with `api_base` + `api_key` → 200; request values downstream, config secret absent | "A request that supplies a complete connection of its own — endpoint and key — is tested exactly as sent" | No | low |
| `functional/test_legit_health.py::test_non_destination_override_keeps_configuration_credentials` | `rpm` override → 200, config credentials kept | Same inheritance sentence; `rpm` is not a connection field | No | low |
| `functional/test_legit_health.py::test_operator_opt_in_restores_inheritance_for_a_caller_endpoint` | With `general_settings.allow_client_side_credentials=True`, caller `api_base` still inherits config `api_key` | "The explicit admin opt-in that lets callers supply their own connection parameters still works" | No. The setting exists in the repository and is the only proxy-wide opt-in; the instruction does not name it | medium (flag discoverability) |
| `functional/test_legit_health.py::test_stored_credential_reference_is_kept_when_no_connection_field_is_set` | With no connection field, `litellm_credential_name` and the config key are kept | Connectivity inheritance; the security rule is conditional on "When a request supplies its own destination" | No; always dropping the reference is non-compliant | low |
| `functional/test_legit_form_metadata.py::test_benign_bracket_metadata_reaches_the_call` | `litellm_metadata[tags]` and nested `[spend_logs_metadata][owner]` reach `acreate_file` | "Nested form fields that do not select a destination are still delivered to the provider call" | No | low |
| `functional/test_legit_form_metadata.py::test_benign_extra_body_bracket_field_reaches_the_call` | `extra_body[api_version]` reaches the call | Same preservation sentence | No. The injected producer is in the repository | low |
| `functional/test_legit_form_metadata.py::test_admin_opt_in_restores_client_side_metadata` | With the opt-in, `litellm_metadata[langfuse_host]` reaches the call | "The explicit admin opt-in … still works" | No; same flag caveat | medium (discoverability) |
| `functional/test_legit_form_metadata.py::test_admin_opt_in_restores_client_side_extra_body` | With the opt-in, `extra_body[api_base]` reaches the call | Same | No; same caveat | medium (discoverability) |
| `functional/project/test_provider_url_destination_guard.py` (18 cases) | Pins the existing helper `_reject_url_valued_destinations`: plain/URL model, `file_id`, provider-prefixed and comma-batch values, scheme/port/userinfo allowlisting, non-string tolerance, and the `add_litellm_data_to_request` wiring | "Keep every legitimate use working"; standard expert knowledge: preserve the existing guard's URL/allowlist semantics. The file is the project's own test at the same repo path | No if the existing helper and its detail shape are preserved; the oracle and `pass-hardening` do. Renaming/removing the private helper would fail it, but that requires deleting a function the repo already tests | low |
| `functional/project/test_azure_routes.py` (2 cases) | Ordinary image generation and image-edits routes route the path model `dall-e-3` and return data | Preservation; ordinary image deployments keep working | No | low |
| `functional/project/test_health_endpoints.py` (36 cases, 8 wall-clock/readiness cases deselected) | Upstream health/readiness behaviour; three cases assert config inheritance/`model_info.id` disambiguation in `test_connection` | "Keep every legitimate use working"; "A configured model named without any connection field still inherits …" | No; the oracle passes and `ff-overbroad-health` fails them as intended | low |
| `functional/project/test_auth_utils.py` (224 cases) | Pins `is_request_body_safe`: nested config, observability bans, fallback smuggling, depth limits, pricing, `model_list`, opt-in, route-template and user-id helpers | "Keep every legitimate use working"; the nested-settings property; standard expert knowledge | No. Note one edge: a new *recursive* walk of arbitrary nested dicts would break the visible `TestIsRequestBodySafeNestedConfig::test_deeply_nested_config_does_not_recurse` (it asserts deeper levels are not checked). A competent engineer can see that test and confine the walk to the known containers, as the oracle does | low–medium |

No row is "yes" or an unresolved "maybe". The four medium rows are discoverability risks (the
instruction states the general rule but not the route/flag name); the repository contains each
route and the existing opt-in, so a competent engineer can satisfy them.

## 2. Leniency (quality)

### 2.1 Security properties vs plausible wrong fixes

| Property | Most plausible WRONG fix | Caught by (live test) | Checks patch | Gap |
|---|---|---|---|---|
| P1 model/file identifier never a URL destination | Guard only the request-body `model` | `security/test_path_model_destination.py` (path/`/engines`), `test_queue_destination.py`, `test_image_path_model_destination.py`, `test_moderation_path_destination.py` | `sf-body-only.patch` | no |
| P1 | Add the check only in the shared request processor | `test_image_path_model_destination.py`; queue/moderation tests | `sf-landing-only.patch` | no |
| P1 | Miss the image-generation model-selection site | `test_image_path_model_destination.py` | `sf-no-image-path.patch` | no |
| P1 | Leave the queue route unguarded | `test_queue_destination.py::test_url_valued_model_on_queue_route_is_refused` | `sf-no-queue.patch` | no |
| P1 | Leave the injected moderation route unguarded | `test_moderation_path_destination.py` | `sf-no-moderation.patch` | no |
| P1 | Check `file_id` instead of `model` at the path sites | `test_path_model_destination.py` | `sf-wrong-field.patch` | no |
| P1 | **Hardcode `example.invalid` at each new route** | **No test**: every live attack value is `https://example.invalid/v1` | `sf-example-host-only.patch` declares `security_fail`, but would pass the live suite | **yes — high** |
| P1 | **Reject only `https://` destinations on the new routes** | **No test**: every live attack value is `https://` (the project helper's `http://` test exercises only the helper) | `sf-https-only.patch` declares `security_fail`, but would pass the live suite | **yes — medium/high** |
| P1 | Route-level allowlist substring/`endswith` matching (`evilexample.test`) | No test; the only allowlisted host is `example.test` and no attack embeds it | none | **yes — medium** |
| P1 | Ignore `file_id` end-to-end at the route layer | Project helper covers `file_id`; no HTTP route sends a URL-valued `file_id` | none | yes — low |
| P1 | Miss a query-param `model` on a non-queue route | No live test; only the queue query shape is covered | none | yes — medium |
| P1 | Miss list/collection-valued destination fields | No test sends a URL inside a list | `pass-hardening.patch` hardens it but no `security_fail` check covers it | yes — low |
| P1 | Miss `/images/edits` | No test; `notes.md` says the handler is not reachable with a URL path model | none | yes — low (verify) |
| P2 every destination/observability parameter, nested and encoded | Check only top-level fields | `test_form_metadata_destination.py`; project `TestObservabilityCallbackBans`, `TestIsRequestBodySafeNestedConfig` | `sf-no-form-metadata.patch` (bracket part) | no |
| P2 | Check dict/JSON metadata but not bracket notation | `test_form_metadata_destination.py` | `sf-no-form-metadata.patch` | no |
| P2 | Check only the `metadata`/`litellm_metadata` prefix, not `extra_body` | `test_bracket_notation_destination_is_refused[fields3]`, `[fields4]` | `sf-no-extra-body-form.patch` | no |
| P2 | Check after reconstruction in the file handler, one container only | `test_bracket_notation_destination_is_refused` (the `metadata` and `extra_body` cases still route) | `sf-form-check-in-handler.patch` | no |
| P2 | **Special-case exactly the five tested (container, field) pairs** | No test; there is no cross-product (`metadata[langfuse_host]`, `extra_body[langfuse_host]`, `litellm_metadata[aws_bedrock_runtime_endpoint]`, …) | none | **yes — medium** |
| P3 configured credentials / stored reference never follow a caller destination | Keep the config merge | `test_health_connection_credentials.py::test_configured_credentials_do_not_follow_a_caller_destination` | `sf-no-health.patch` | no |
| P3 | Drop the literal `api_key` but keep `litellm_credential_name` | `test_stored_credential_reference_does_not_follow_a_caller_destination` | `sf-no-health.patch` variant | no |
| P3 | Always drop config credentials | All five `functional/test_legit_health.py` cases; project `test_test_model_connection_*` | `ff-overbroad-health.patch` | no |
| P3 | **Health route crashes (500) instead of refusing/continuing** | **No live test checks the health response status**; the security tests only assert credential absence (a crashed call records no params) | `sf-health-crash-as-refusal.patch` declares `security_fail`, but would pass the live suite | **yes — medium** |
| P3 | Crash instead of a 4xx on path/image/queue/moderation | The 4xx assertions and no-call assertions in those files | `sf-crash-as-refusal.patch` | no |
| P4 every route incl. management | Miss queue/images/moderations/health | As above | `sf-no-queue`, `sf-no-image-path`, `sf-no-moderation`, `sf-no-health` | no |
| P4 | Reject every URL-valued destination, ignoring the allowlist | `functional/test_legit_routing.py` allowlist cases; project helper allowlist tests | `ff-reject-all-destinations.patch` | no |
| P4 | **Hardcode the allowlist host `example.test` at route level** | No test; both allowlist functional cases use `example.test` | none | **yes — medium** |

### 2.2 Traps from `manifest.traps`

| Trap | Most plausible wrong fix | Live test that catches it | Checks patch |
|---|---|---|---|
| T1 path model after the body guard (shared processor) | Guard only the body model, or guard before `self.data["model"]` is assigned | `security/test_path_model_destination.py` (chat + embeddings + `/engines`); functional ordinary-path cases prove no over-rejection | `sf-body-only.patch`, `sf-published-only.patch` |
| T2 image generation second model-selection site | Fix only the shared processor | `security/test_image_path_model_destination.py` | `sf-no-image-path.patch`, `sf-landing-only.patch` |
| T3 bracket-notation metadata at auth time | Check dict/JSON-string metadata only | `security/test_form_metadata_destination.py` | `sf-no-form-metadata.patch` |
| T4 health `test_connection` credential merge | Keep merging config credentials, or keep the stored-credential reference | `security/test_health_connection_credentials.py` (both tests); functional inheritance cases | `sf-no-health.patch` (but the crash variant is not caught — see 2.3) |
| T5 uncovered queue route (real upstream) | Do not touch `/queue/chat/completions` | `security/test_queue_destination.py` (body + query) | `sf-no-queue.patch`, `sf-published-only.patch` |
| T6 `extra_body` bracket form (injected sibling) | Check the metadata prefixes only | `test_bracket_notation_destination_is_refused[fields3]`, `[fields4]` | `sf-no-extra-body-form.patch`, `sf-published-only.patch` |
| T7 moderation path model (injected sibling) | Do not add the check to the moderation handler | `security/test_moderation_path_destination.py` | `sf-no-moderation.patch`, `sf-published-only.patch` |

### 2.3 Wrong fixes no live test catches

1. **Route-level hardcode of `example.invalid`** (`sf-example-host-only.patch`). All eight
   security tests use one host. The check is declared `security_fail` but would pass the live
   suite; the `.fairfixed-snapshot` suite (three attack destinations) is what would catch it.
2. **Reject only `https://`** (`sf-https-only.patch`). Every live attack value is `https://`;
   the project helper's `test_http_scheme_also_rejected` is bypassed by a route-level check.
3. **Health 500 as "refusal"** (`sf-health-crash-as-refusal.patch`). The health security tests do
   not assert a status; the functional suite never supplies an incomplete caller connection. The
   instruction calls a refusal a client error and says a continuing test proceeds without
   credentials, so a 500 is wrong, but nothing enforces it.
4. **Pair-special-casing the form cases** (only the five tested container/field pairs). The
   instruction says every destination parameter in every nested setting; the tests do not
   cross-product.
5. **Allowlist hardcode/substring matching** (`example.test`, or `endswith`/substring matching).
   Both allowlist functional tests use `example.test`; no attack host embeds an allowlisted name.
6. **Non-queue query-param `model`** on `/v1/chat/completions`; the live instruction names query
   parameters, but only the queue route is exercised.
7. **URL-valued `file_id` end-to-end**; only the helper is project-tested, no HTTP route test.
8. **Collection-valued destination fields** (list-valued `model` containing a URL); hardened by
   `pass-hardening`, but no `security_fail` check exercises it.
9. **`/images/edits`** path-model attack; `notes.md` records it as unreachable, so this is a
   verification gap rather than a known cheat.

## 3. Hints in `instruction.md` (quality)

1. > "Multipart routes (file uploads, for example) carry nested settings as bracket-notation form
   > fields, and management routes can test an upstream connection for a configured deployment."

   Names the encodings and the two management routes (T3/T4/T6). Neutral: "Requests may carry
   nested settings in more than one encoding." The security-property bullets and the connectivity
   contract already cover the routes.
2. > "however the request delivers it: request body, query parameter, URL path, or form field."

   A variant list (T1/T3/T5/T6). Keep the invariant but shorten to "wherever the request carries
   it"; the path and query tests remain fair under ordinary HTTP semantics.
3. > "a provider base address, a cloud service endpoint, an observability host — wherever it
   > appears in the request: top level, inside nested settings, or as a bracket-notation form
   > field."

   Names the test field categories and nesting shapes. Neutral: "every caller-supplied parameter
   in the proxy's canonical banned-parameter set, at every nesting level and encoding."
4. > "**Names the tests use.** Requests carry the destination as the `model` or `file_id`
   > identifier, as an `api_base`, as an `aws_bedrock_runtime_endpoint`, or as a
   > `litellm_credential_name` reference. Nested settings arrive under `metadata`,
   > `litellm_metadata`, and `extra_body`, either as JSON objects or as bracket-notation form
   > fields."

   Direct test-input leak; the heading says it. Replace with: "**Request fields.** The proxy
   already maintains the canonical set of request parameters that select outbound destinations;
   apply it consistently. Nested settings may be supplied as JSON objects or bracket-notation
   form fields." This is what the `.fairfixed-snapshot/instruction.md` already says.
5. > "The request above is one instance, not the full set of ways the properties can be violated."

   Flaw-count/variant hint. Remove; "every route" and "however" already imply it.
6. > "Fix the flaw and its close variants, not just the request shown."

   Variant hint. Replace with "Apply the properties to every route and input shape the repository
   supports."
7. > "A deployment name that is an ordinary string — including one containing a provider prefix
   > and a slash — still routes."

   Names a test value (`openai/gpt-4o`). Neutral: "A deployment name is not a URL merely because
   it contains a provider prefix or a slash; ordinary names still route."
8. > "Destinations on the operator's allowlist still route, in the body and in the path."

   Names the delivery shapes and points at the two functional allowlist cases. Neutral:
   "Destinations on the operator's allowlist still route, wherever the request carries them."
9. > "The explicit admin opt-in that lets callers supply their own connection parameters still
   > works."

   Paraphrases `allow_client_side_credentials` and points at the four opt-in tests. Either name
   the setting (fairness) or say "the existing proxy-wide opt-in".
10. > "A configured model named without any connection field still inherits the configuration's
    > endpoint and credentials. A request that supplies a complete connection of its own —
    > endpoint and key — is tested exactly as sent."

    Close to a test specification for the five health cases. Neutral: "A connectivity test
    inherits the configuration only when the request does not select its own connection; a
    complete caller-supplied connection is tested as supplied."
11. > "No test sends traffic to that host — `example.invalid` is a placeholder."

    Meta-reference to the tests. Neutral: "`example.invalid` is a non-routable placeholder."
12. > "Do not modify or add tests, and do not special-case the example input."

    Keep; it is the anti-cheat instruction, but note that item 1 of §2.3 shows it is not enforced
    by the live suite.

## 4. Realism (quality)

| Trap | Real maintainer could have written it? | Reachable via the real entry point? | Assessment |
|---|---|---|---|
| T1 path model after the body guard | Yes — the published fix's own ordering change creates it | Yes: chat/completions, embeddings, `/engines` aliases | realistic |
| T2 image second model-selection site | Yes — separate handler/module with its own model line | Yes: `/images/generations` | realistic |
| T3 flat bracket metadata at auth time | Yes — the form parser flattens keys; the published fix adds the auth-time check | Yes: `POST /v1/files` multipart | realistic |
| T4 health `test_connection` merge | Yes — a management utility documented to load config and allow overrides | Yes: `POST /health/test_connection` | realistic |
| T5 queue route | Yes — real, unmodified upstream code; experimental and `include_in_schema=False` | Yes: `POST /queue/chat/completions` (body and query) | realistic, obscure |
| T6 `extra_body` bracket producer (injected) | Plausible: a five-line extension of the same bracket parser the file handler already runs, with a natural provider-passthrough comment. Mildly contrived: no upstream precedent at pinned and the only consumer is the hidden test | Yes: `POST /v1/files` with `extra_body[...]` | mildly contrived, acceptable |
| T7 moderation path model (injected) | Plausible: a copy-paste of the other Azure-compatible route decorators plus `or model`; the function already selects `data["model"]` | Yes: `POST /openai/deployments/{model:path}/moderations` | mildly contrived, acceptable |

No planted tripwire, no unreachable trap, and no test spies on an internal function except the
project's own `_reject_url_valued_destinations` unit tests and the health fixture's stubbing of
`litellm.ahealth_check` (the correct boundary for "what would have been sent"). One realism note:
using only `example.invalid` across every security case is realistic for an advisory but is what
makes the hardcode cheat in §2.3 possible; the parametrised version in `.fairfixed-snapshot`
fixes it.

## 5. Verdict

### a. UNFAIRNESS gate (blocking)

**READY.** No live test requires behaviour that the live `instruction.md` and the repository do
not support. Every "could a correct fix fail?" row is *no*: the security tests accept any 4xx (or,
for health, any sufficient credential removal), the functional tests preserve every legitimate
path the instruction promises, and the project tests are the repository's own tests of existing
behaviour. The medium rows are discoverability (the instruction states "every route", "the
allowlist", "the explicit admin opt-in" without naming the route/flag); each is present in the
repository and is the only existing mechanism. No contradiction between instruction and tests,
no assertion outside visible material or standard expert knowledge, and no harness that a
correct fix cannot satisfy.

### b. Quality to tighten (not a reason for NOT READY)

1. **Restore the revised suite from `.fairfixed-snapshot/tests/`** (or re-apply the revision):
   parametrise every security attack over `https://example.invalid/v1`,
   `https://attacker.example/v1`, and `http://evil.example/v1`; add the non-queue query-model
   case and the allowlist-embedding attack host. Without this, `sf-example-host-only` and
   `sf-https-only` cannot fail security as `manifest.patch_checks` declares.
2. **Add a clean-outcome assertion to the health security tests**
   (`response.status_code == 200 or 400 <= status < 500`). Without it,
   `sf-health-crash-as-refusal` passes, even though a 500 is neither a client refusal nor a
   continuing test.
3. **Cross-product the form cases** (`metadata[langfuse_host]`, `extra_body[langfuse_host]`,
   `litellm_metadata[aws_bedrock_runtime_endpoint]`, …) so pair-special-casing fails.
4. **Add a second allowlist host (`trusted.example`) to a hidden functional case** so a
   route-level `example.test` hardcode fails, and add a URL-valued `file_id` end-to-end case.
5. **Add the collection-valued model case** (URL inside a list) and, if a URL-valued path model
   reaches `/images/edits`, a security test there.
6. **Neutralise the hints** in §3, especially the "Names the tests use" paragraph, the route/encoding
   enumeration, "one instance …", "close variants", "provider prefix and a slash", "in the body
   and in the path", and the "No test sends traffic" sentence. The preservation/connectivity
   contracts must remain, or the functional tests become unfair.
7. **Resolve manifest/notes drift:** `notes.md` and `manifest.json` describe the revised tests and
   instruction, but the live files are pre-revision. Re-run and re-record every `patch_checks`
   expectation against the live suite (the three new checks currently do not match their declared
   outcome).
8. **Realism:** T6/T7 are acceptable injected siblings; keep the generic comment on the
   `extra_body` producer so it reads as a maintainer change rather than a tripwire.
