# FAIRNESS review — hubuum-client-rust-ds

Graded: 24 security, 12 hidden functional, 2 pristine project tests. Solver sees only `instruction.md` + repo.
Labels: **G** = Required invariant (no server content/caller secret in default `Display`/`Debug`/`source` of any returned error or value, for every shape). **A** = same data via public fields/explicit accessors; serde unchanged. **U** = identifiers, names, statuses, kinds, timestamps and counts that are not sensitive stay visible. **E** = failures error, retries retry, successes succeed.

## 1. Test-by-test fairness

| Test (`file::name`) | What it asserts | Fairness basis | Could a correct fix fail it? | Risk |
|---|---|---|---|---|
| `security/sec_hubuum.rs::http_error_details_absent_from_display_and_debug` | 401 JSON `message` marker absent from `Display`, `Debug`, `source` | G | no — redact `HttpWithBody.message` in both renderers, or at construction; accessors untouched | low |
| `security/sec_hubuum.rs::http_error_plain_text_body_absent_from_display_and_debug` | 502 plain-text body marker absent from all default rendering | G | no | low |
| `security/sec_hubuum.rs::decode_error_details_absent_from_default_diagnostics` | typed-decode failure text marker absent | G | no | low |
| `security/sec_hubuum.rs::json_error_details_absent_from_default_diagnostics` | serde_json codec text marker absent (meta call) | G | no — a `#[from]`/`source` link would leak through `source` and is not a correct fix (G names the source chain) | low |
| `security/sec_hubuum.rs::retry_error_details_absent_from_default_diagnostics` | custom-transport detail absent from the exhausted-retry error | G | no — redact at `RetryExhausted` or at the retry site | low |
| `security/sec_hubuum.rs::runner_summary_absent_from_default_diagnostics` | async failed export run must not expose the task summary | G | no | low |
| `security/sec_hubuum.rs::blocking_runner_summary_absent_from_default_diagnostics` | same through the blocking client | G ("any ... the library returns"); blocking is part of the library | no | low |
| `security/sec_hubuum.rs::task_response_debug_omits_server_summary` | returned `TaskResponse` Debug omits `summary` | G | no | low |
| `security/sec_hubuum.rs::task_response_debug_omits_nested_link_and_detail_values` | every link/detail URL marker absent | G ("nested values ... containers ... embedded") | no — redacting whole links, or URL queries, both pass | low |
| `security/sec_hubuum.rs::task_event_debug_omits_message_and_data` | event `message` and `data` absent | G | no | low |
| `security/sec_hubuum.rs::event_delivery_debug_omits_claim_token_and_error` | `claim_token` and `last_error` absent | G; both are sensitive tokens, not "identifiers ... that are not sensitive" | no | low |
| `security/sec_hubuum.rs::event_sink_debug_omits_configuration` | config token and `secret_ref` absent | G | no | low |
| `security/sec_hubuum.rs::event_subscription_debug_omits_routing` | routing token absent | G | no | low |
| `security/sec_hubuum.rs::export_result_debug_omits_rendered_body` | rendered export body absent | G | no | low |
| `security/sec_hubuum.rs::export_json_debug_omits_items_and_warnings` | items and warning messages absent | G | no | low |
| `security/sec_hubuum.rs::import_results_debug_omit_server_error_details` | per-item error and details absent | G | no | low |
| `security/sec_hubuum.rs::import_run_result_debug_omits_nested_result_details` | nested change error/details absent | G | no | low |
| `security/sec_hubuum.rs::audit_event_debug_omits_snapshots` | audit summary/before/after/metadata absent | G | no | low |
| `security/sec_hubuum.rs::restore_stage_debug_omits_server_error` | stage `error` absent | G | no | low |
| `security/sec_hubuum.rs::object_history_debug_omits_object_data` | history object `data` absent | G | no | low |
| `security/sec_hubuum.rs::class_history_debug_omits_schema_payload` | class-history `json_schema` absent | G | no | low |
| `security/sec_hubuum.rs::restore_run_async_error_omits_server_detail` | async restore-run error text absent | G | no | low |
| `security/sec_hubuum.rs::restore_run_blocking_error_omits_server_detail` | same, blocking | G | no | low |
| `security/sec_hubuum.rs::sink_delivery_health_debug_omits_last_error` | nested health `last_error` absent | G | no | low |
| `functional/fun_hubuum.rs::http_error_accessors_and_metadata_unchanged` | accessors return original message/body/url/status; `Display` has `GET`, `Debug` has `401` | A, U; standard expert knowledge: HTTP method and status are non-sensitive metadata, and G forbids only server content/caller secrets | no for targeted redaction; only a strict allowlist that drops method would fail | medium |
| `functional/fun_hubuum.rs::valid_responses_decode_and_retries_still_work` | valid decode works; malformed input still errors | A, E | no | low |
| `functional/fun_hubuum.rs::replay_safe_requests_still_retry` | two attempts then success | E | no | low |
| `functional/fun_hubuum.rs::runner_error_keeps_task_identity_and_status` | failed-run error `Display` **and** `Debug` contain `11` and `failed` | U (identifiers, statuses) | no — keep id/status, drop only summary | low |
| `functional/fun_hubuum.rs::task_and_event_values_remain_readable` | fields/serde intact; Debug keeps task id+status, event id+type | A, U | no | low |
| `functional/fun_hubuum.rs::event_sink_and_delivery_values_remain_readable` | fields/serde intact; Debug keeps sink name/id, delivery id/status | A, U | no | low |
| `functional/fun_hubuum.rs::export_and_import_values_remain_readable` | body/items/error/details accessible, serde intact; Debug keeps id/outcome/count | A, U ("counts") | no | low |
| `functional/fun_hubuum.rs::blocking_client_legitimate_flow` | blocking list and successful run work | E | no | low |
| `functional/fun_hubuum.rs::restore_stage_and_run_flows_work` | stage accessors/Debug id; successful run returns | A, U, E | no | low |
| `functional/fun_hubuum.rs::restore_run_blocking_flow_works` | blocking restore run succeeds | E | no | low |
| `functional/fun_hubuum.rs::audit_and_history_values_remain_readable` | accessors intact; Debug keeps `entity_name`, `action`, object name | A, U ("names ... kinds"); standard expert knowledge: `action` is non-sensitive categorical metadata | no if `action` counts as a "kind"; an allowlist that omits it would fail | medium |
| `functional/fun_hubuum.rs::event_delivery_health_values_remain_readable` | `last_error` accessible; Debug keeps sink name | A, U | no | low |
| `errors::tests::exposes_structured_api_error_response` (lib) | pre-existing structured error accessor test | A (accessors unchanged) | no | low |
| `foundations::response_and_error_debug_output_redacts_sensitive_values` (project) | pre-existing: TransportResponse/HttpWithBody Debug redact values, keep names/lengths; Display no query | G, A; pre-existing project behaviour retained | no | low |

No test demands a particular redaction string, error class, status, or refusal form; assertions are marker-absence plus the visible accessor/usefulness contracts.

## 2. Leniency (QUALITY)

| Lever | Most plausible wrong fix | Caught? |
|---|---|---|
| T1 http envelope | redact body, keep `message` in Display/Debug | yes — `http_error_details_...`; `checks/sf-http-envelope.patch` (2 fails) |
| T2 decode/retry | fix HTTP only, leave `Json`/`Deserialization`/`RetryExhausted` (or keep `#[from]` source) | yes — `json_error_...`, `decode_error_...`, `retry_error_...`; `checks/sf-decode-retry.patch` (3 fails) |
| T3 runners | redact error enum but leave the runner `format!` sites, or fix async only | yes — `runner_summary_...`, `blocking_runner_summary_...`; `checks/sf-runners.patch` (2 fails) |
| T4 result models | treat structs as "plain data", fix only errors/HTTP | yes — 10 result-model tests; `checks/sf-result-models.patch` (8+ fails) |
| B1 audit | dismiss audit records as "meant to be read" | yes — `audit_event_debug_...`; `checks/sf-audit-event.patch` (1) |
| B2 restore stage | skip the neighbouring backup type | yes — `restore_stage_debug_...`; `checks/sf-restore-stage.patch` (1) |
| B3 history | skip history rows as "data you asked for" | yes — `object_history_...`, `class_history_...`; `checks/sf-history-payloads.patch` (2) |
| S1 injected restore run | fix pre-existing run ops, miss the convenience op in either client | yes — both restore-run tests; `checks/sf-restore-run.patch` (2) |
| S3 injected sink health | fix `EventDelivery`, miss the nested health row | yes — `sink_delivery_health_debug_...`; `checks/sf-sink-health.patch` (1) |
| Over-broad (all) | blank ids/names/statuses | yes — functional group; `checks/ff-overbroad.patch` (functional fails) |

Wrong fixes **no test catches**:

- `RemoteCallResult` Debug (`src/types/remote.rs`) left leaking its `error`; the oracle fixes it, but no test drives a remote call (and `sf-result-models.patch` omits `remote.rs`).
- Caller-input `NewEventSink`/`UpdateEventSink`/`NewEventSubscription`/`UpdateEventSubscription` (`config`, `routing`, `secret_ref`) are fixed by the oracle but never formatted by a test (also arguably outside "the library returns").
- Bare `ApiError::Transport(String)` Display: the retried path is wrapped into `RetryExhausted`, so `Transport` text is never the returned error in a test.
- `ApiError::Http(reqwest::Error)` source/URL query is untested (only `HttpWithBody` is covered by the project foundations test).
- Redacting only keys named `token`/`secret` inside nested `config`/`routing`/`details` passes: every marker sits in such a key while other container content is still printed.
- Partial link redaction: link markers sit only in query values, so a fix printing URL paths/other content passes.
- Untested types: `RawResponse` (crate-private), `ExportTemplateHistory`, `TaskQueueStateResponse`, and any other `ApiError::Api(format!(...))` site outside the two fixed families.

## 3. Hints (QUALITY)

- "retries still retry" paraphrases one affected mechanism; neutral: "Existing call outcomes are unchanged."
- No file, type, route, operation, stage, format, variant list or flaw count is named; the `Display`/`Debug`/`source` sentence names the protected sink, not a fix approach.

## 3a. Required: generalize

none. The property is stated once over server-supplied content and caller secrets in default diagnostics of returned values; no sentence locates a sibling, far site or uncovered route, and no general word doubles as a product/entry-point name.

## 4. Realism (QUALITY)

- T1–T4 are published fix sites; B1–B3 are real, unmodified upstream routes and are not flagged.
- S1 (`Restores::run` beside the existing run operations) and S3 (a per-sink `last_error`) are plausible, publicly reachable additions with neutral names; nothing contrived.

## 5. Verdict

**READY.** Every security test drives a public entry point and asserts only marker absence; every functional/project test encodes a visible contract (A, U, E). G read literally covers every exercised route, including the real-upstream B routes, the injected siblings and the blocking client. No test bypasses a valid layer, demands one error class/status, or contradicts the instruction; the oracle and both passing variants confirm the natural fix passes.

**Quality to tighten:**
1. Test `RemoteCallResult` and bare `ApiError::Transport`; both are currently uncaught.
2. Put markers in non-token parts of `config`/`routing`/`details` and in link URL paths, so key-only redaction fails.
3. Decide whether caller-input event types are in scope; test them, or stop redacting them in the oracle.
4. Reword "retries still retry" (§3).

**Human review:** confirm "diagnostics stay useful" lets a correct fix keep non-sensitive audit `action` and the HTTP method in `Debug`/`Display`, so the two functional assertions are satisfiable.

GATE_A: READY
NEEDS_HUMAN_REVIEW: YES
