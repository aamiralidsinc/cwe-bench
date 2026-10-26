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

Project root: `/home/mara/cwe-bench`. Task: `hubuum-client-rust-mm`. Pattern: `A+B`. Track: `injected`.

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
- Advisory: ["GHSA-2625-RW7M-5Q5X"]; hubuum/hubuum-client-rust; CWE-532 sensitive information in default diagnostics (Display/Debug/error source chain redaction)
- Pinned (vulnerable) commit: parent of 5a5c275ffa45f342459b7d3e977926da643bde50 (parent_commit not given in candidate). Published fix: 5a5c275ffa45f342459b7d3e977926da643bde50.
- The screener's record (a lead to verify, not a fact):
  ```json
  {
 "screener_version": "screener-v2",
 "lessons_version": "lessons-v1",
 "model": "claude-opus-5-5",
 "entry_id": "20282",
 "advisory_ids": [
  "GHSA-2625-RW7M-5Q5X"
 ],
 "repo": "hubuum/hubuum-client-rust",
 "pinned_commit": "parent of 5a5c275ffa45f342459b7d3e977926da643bde50 (parent_commit not given in candidate)",
 "fix_commits": [
  "5a5c275ffa45f342459b7d3e977926da643bde50"
 ],
 "trust_decision": {
  "summary": "Which server-provided or caller-secret values (HTTP error messages, reqwest URLs with query values, JSON/decode/retry details, task summaries, event sink config/routing, delivery claim tokens, import/export payloads, password bodies) may appear in the library's default Display/Debug diagnostics; decided per-type in hand-written or derived Debug impls and in the thiserror #[error] formats of ApiError.",
  "evidence": [
   "src/errors.rs:58",
   "src/errors.rs:116-213",
   "src/types/task.rs:110",
   "src/types/event.rs:50",
   "src/client/async.rs:3272",
   "src/client/shared.rs:498-499"
  ]
 },
 "landing_point": {
  "where": "src/errors.rs:58",
  "why": "The summary says 'default diagnostics'; ApiError's Display/Debug in src/errors.rs is the obvious first place, and it already contains partial redaction (HttpWithBody body, PaginationCycle cursor) at src/errors.rs:140-154 and src/errors.rs:198-202."
 },
 "fix_sites": [
  {
   "where": "src/errors.rs:58",
   "entry_point": "Display of any ApiError::HttpWithBody returned by every typed/raw API call (e.g. client.classes().list())",
   "module_kind": "error type (core)"
  },
  {
   "where": "src/errors.rs:16-20",
   "entry_point": "ApiError::from(reqwest::Error)/serde_json::Error via ? in every call; Display/Debug/source chain",
   "module_kind": "error type (core)"
  },
  {
   "where": "src/errors.rs:67",
   "entry_point": "DeserializationError Display from parse_response / TypedObject::try_from / SSE parsing",
   "module_kind": "error type (core)"
  },
  {
   "where": "src/errors.rs:88",
   "entry_point": "RetryExhausted Display from send_with_retry on any call",
   "module_kind": "error type (core)"
  },
  {
   "where": "src/errors.rs:151",
   "entry_point": "Debug of HttpWithBody message",
   "module_kind": "error type (core)"
  },
  {
   "where": "src/errors.rs:155-158",
   "entry_point": "Debug of DeserializationError",
   "module_kind": "error type (core)"
  },
  {
   "where": "src/errors.rs:183",
   "entry_point": "Debug of RetryExhausted last_error",
   "module_kind": "error type (core)"
  },
  {
   "where": "src/client/async.rs:454-457",
   "entry_point": "async send_with_retry on any request (reqwest error URL with query values)",
   "module_kind": "async client implementation"
  },
  {
   "where": "src/client/sync.rs:419-422",
   "entry_point": "blocking send_with_retry on any request",
   "module_kind": "blocking client (second implementation)"
  },
  {
   "where": "src/client/async.rs:3272",
   "entry_point": "async backups().run()...send() on failed task (summary copied into ApiError::Api)",
   "module_kind": "high-level runner (async)"
  },
  {
   "where": "src/client/async.rs:3536",
   "entry_point": "async exports().run() on failed task",
   "module_kind": "high-level runner (async)"
  },
  {
   "where": "src/client/async.rs:3661",
   "entry_point": "async export template run on failed task",
   "module_kind": "high-level runner (async)"
  },
  {
   "where": "src/client/async.rs:3804",
   "entry_point": "async imports().run() (refactor only, already summary-free)",
   "module_kind": "high-level runner (async)"
  },
  {
   "where": "src/client/sync.rs:3079",
   "entry_point": "blocking backups run on failed task",
   "module_kind": "high-level runner (blocking)"
  },
  {
   "where": "src/client/sync.rs:3322",
   "entry_point": "blocking exports run on failed task",
   "module_kind": "high-level runner (blocking)"
  },
  {
   "where": "src/client/sync.rs:3443",
   "entry_point": "blocking export template run on failed task",
   "module_kind": "high-level runner (blocking)"
  },
  {
   "where": "src/client/shared.rs:498-499",
   "entry_point": "Debug of internal RawResponse (body, next_cursor) used by raw()/paging",
   "module_kind": "shared internal response type"
  },
  {
   "where": "src/resources/user.rs:241-242",
   "entry_point": "Debug of SetPasswordBody behind user set_password API",
   "module_kind": "resource request body"
  },
  {
   "where": "src/types/event.rs:50",
   "entry_point": "Debug of EventSink returned by event sink list/get APIs (config, secret_ref)",
   "module_kind": "public model type"
  },
  {
   "where": "src/types/event.rs:64",
   "entry_point": "Debug of NewEventSink passed to sink create",
   "module_kind": "public model type (request)"
  },
  {
   "where": "src/types/event.rs:76",
   "entry_point": "Debug of UpdateEventSink passed to sink update",
   "module_kind": "public model type (request)"
  },
  {
   "where": "src/types/event.rs:118",
   "entry_point": "Debug of EventSubscription (routing)",
   "module_kind": "public model type"
  },
  {
   "where": "src/types/event.rs:136",
   "entry_point": "Debug of NewEventSubscription",
   "module_kind": "public model type (request)"
  },
  {
   "where": "src/types/event.rs:152",
   "entry_point": "Debug of UpdateEventSubscription",
   "module_kind": "public model type (request)"
  },
  {
   "where": "src/types/event.rs:185",
   "entry_point": "Debug of EventDelivery (claim_token, last_error)",
   "module_kind": "public model type"
  },
  {
   "where": "src/types/export.rs:150",
   "entry_point": "Debug of ExportJsonResponse from exports output",
   "module_kind": "public model type"
  },
  {
   "where": "src/types/export.rs:175",
   "entry_point": "Debug of ExportResult (rendered body)",
   "module_kind": "public model type"
  },
  {
   "where": "src/types/import.rs:117",
   "entry_point": "Debug of ImportClassInput (json_schema)",
   "module_kind": "public model type (request)"
  },
  {
   "where": "src/types/import.rs:129",
   "entry_point": "Debug of ImportObjectInput (data)",
   "module_kind": "public model type (request)"
  },
  {
   "where": "src/types/import.rs:171",
   "entry_point": "Debug of ImportGraph",
   "module_kind": "public model type (request)"
  },
  {
   "where": "src/types/import.rs:187",
   "entry_point": "Debug of ImportRequest passed to imports().run()",
   "module_kind": "public model type (request)"
  },
  {
   "where": "src/types/import.rs:225",
   "entry_point": "Debug of ImportRunResult returned by imports().run()",
   "module_kind": "public model type"
  },
  {
   "where": "src/types/remote.rs:419",
   "entry_point": "Debug of RemoteCallResult error (hand-written Debug that already redacts other fields)",
   "module_kind": "public model type"
  },
  {
   "where": "src/types/task.rs:62",
   "entry_point": "Debug of TaskLinks inside TaskResponse",
   "module_kind": "public model type"
  },
  {
   "where": "src/types/task.rs:75",
   "entry_point": "Debug of ImportTaskDetails",
   "module_kind": "public model type"
  },
  {
   "where": "src/types/task.rs:80",
   "entry_point": "Debug of ExportTaskDetails",
   "module_kind": "public model type"
  },
  {
   "where": "src/types/task.rs:92",
   "entry_point": "Debug of BackupTaskDetails",
   "module_kind": "public model type"
  },
  {
   "where": "src/types/task.rs:110",
   "entry_point": "Debug of TaskResponse (summary) from tasks get/poll",
   "module_kind": "public model type"
  },
  {
   "where": "src/types/task.rs:127",
   "entry_point": "Debug of TaskEventResponse (message, data)",
   "module_kind": "public model type"
  },
  {
   "where": "src/types/task.rs:138",
   "entry_point": "Debug of ImportTaskResultResponse (item_ref, identifier, error, details)",
   "module_kind": "public model type"
  }
 ],
 "O1_entry_points": 12,
 "O2_out_of_scope_site": {
  "kind": "second_implementation",
  "where": "src/client/sync.rs:419-422 and src/client/sync.rs:3079 (blocking client duplicates the async retry and runner leaks); also the shared internal type src/client/shared.rs:498-499"
 },
 "O3_reason_to_dismiss": "Model structs like TaskEventResponse/ImportObjectInput are plain data the caller already holds, so redacting their derived Debug looks like over-reach beyond 'error diagnostics'; and the blocking client is a separate feature a solver who reproduced with async may never open.",
 "O4_distance": {
  "files": 11,
  "packages": 1,
  "repo_mb": null
 },
 "O5_coupled_behaviour": {
  "what": "Explicit accessors must keep returning the original server details (api_message, response_body, request_url, new json_error/deserialization_message/last_retry_error) and fields must stay readable/serializable (task.summary, delivery.claim_token, create_sink.config); an over-broad fix that scrubs the stored strings or Serialize output breaks callers and the existing accessor test.",
  "where": "src/errors.rs:246-269; src/errors.rs:293 (existing test asserts api_message 'Authentication failure'); fix.diff:1866-1873"
 },
 "O6_input_shapes": [
  "Display vs Debug vs std::error::Error::source chain of ApiError",
  "reqwest::Error carrying a URL with query values (direct From vs RetryExhausted string)",
  "Option<String>/Option<Value> fields (redacted only when present) vs required String/Value fields",
  "nested containers (ImportGraph -> Vec<ImportObjectInput>, ExportResult::Json -> ExportJsonResponse, TaskResponse -> TaskLinks/TaskDetails)",
  "async and blocking client variants",
  "request (New*/Update*) and response model variants of the same resource"
 ],
 "O7_producer": {
  "kind": "serializer",
  "where": "derived Debug formatters (e.g. src/types/task.rs:110, src/types/event.rs:50) and the ApiResource derive macro hubuum_client_derive/src/lib.rs:332 which emits #[derive(Debug)] on every generated resource struct",
  "check_calls_producer": false
 },
 "O8_uncovered_routes": [
  {
   "route": "Restore staging response Debug prints the server-provided error string unredacted, while the fix redacts the analogous RemoteCallResult/EventDelivery/ImportTaskResult error fields",
   "where": "src/types/backup.rs:233",
   "reason_to_dismiss": "Backup/restore is a neighbouring feature not named in the changelog and the type already has a hand-written Debug, so it looks already reviewed",
   "distance": "src/types/backup.rs, separate module from errors.rs and task.rs",
   "present_in_latest": "yes",
   "latest_where": "latest/src/types/backup.rs:221"
  },
  {
   "route": "Audit EventResponse derives Debug and prints before/after object snapshots, metadata and summary, in the same file where the fix redacted sink/subscription/delivery types",
   "where": "src/types/event.rs:7-35",
   "reason_to_dismiss": "It's an audit-log record whose content is meant to be read; the changelog lists only sink configuration, routing and delivery",
   "distance": "same file as fixed sites (src/types/event.rs)",
   "present_in_latest": "yes",
   "latest_where": "latest/src/types/event.rs:11-13"
  },
  {
   "route": "Generated resource structs (Object.data, Class.json_schema) derive Debug through the ApiResource macro, though the fix redacts the same object data and json_schema on the import input types",
   "where": "hubuum_client_derive/src/lib.rs:332; src/resources/object.rs:32-33",
   "reason_to_dismiss": "Object data is the caller's own primary resource, the derive macro is another crate, and redacting it would hamper ordinary debugging",
   "distance": "separate workspace crate hubuum_client_derive plus src/resources/",
   "present_in_latest": "yes",
   "latest_where": "latest/src/resources/generated/object.rs:59-67"
  },
  {
   "route": "ObjectHistory.data and ClassHistory.json_schema keep derived Debug",
   "where": "src/types/history.rs:33-54",
   "reason_to_dismiss": "History is a legacy/neighbouring read API, not mentioned in the advisory",
   "distance": "src/types/history.rs",
   "present_in_latest": "yes",
   "latest_where": "latest/src/types/history.rs:79-100"
  },
  {
   "route": "ObjectWithPath.data (related-object graph) keeps derived Debug",
   "where": "src/resources/object.rs:54-61",
   "reason_to_dismiss": "Graph traversal type, not a diagnostic",
   "distance": "src/resources/object.rs",
   "present_in_latest": "unknown",
   "latest_where": ""
  }
 ],
 "O8b_injection_room": [
  {
   "where": "src/types/backup.rs:219-233",
   "sibling": "A restore/backup result type whose hand-written Debug forwards a server error string",
   "why_realistic": "The file already hand-writes Debug field-by-field; forgetting one field is the exact mistake the fix corrected in src/types/remote.rs:419"
  },
  {
   "where": "src/client/sync.rs:3079",
   "sibling": "Another blocking-only runner that formats task.summary into ApiError::Api",
   "why_realistic": "Async and blocking runners are copy-pasted; a maintainer adding a new runner to one client copies the old pattern"
  },
  {
   "where": "src/errors.rs:25-29",
   "sibling": "ApiError::Api/Transport variants whose Display embeds a server- or transport-provided string",
   "why_realistic": "Display formats with {0} are the thiserror default and Api(String) is still used for server messages via api_message()"
  }
 ],
 "O9_family": "CWE-532 sensitive information in default diagnostics (Display/Debug/error source chain redaction)",
 "O9_dos": false,
 "O10_build": {
  "language": "Rust (edition 2024, rust-version 1.88)",
  "toolchain": "cargo workspace (hubuum_client + hubuum_client_derive proc-macro), reqwest 0.13, thiserror, tokio, httpmock for tests",
  "services": [],
  "offline_after_build": true,
  "project_tests": "Unit tests in src/errors.rs:272-303, src/client/tests.rs (export run failure tests at src/client/tests.rs:440-456 and 530-547), tests/foundations.rs (response_and_error_debug_output_redacts_sensitive_values), tests/client_behavior.rs; integration-tests feature needs a Hubuum server image and is not needed for this area"
 },
 "O11_fix_minutes": 90,
 "O12_red_flags": [],
 "O13_recall_risk": "low",
 "pattern_fit": "A+B",
 "j": {
  "j_multi_site": 1,
  "j_sites_touched": "src/errors.rs, src/client/async.rs, src/client/sync.rs, src/client/shared.rs, src/client/mod.rs, src/resources/user.rs, src/types/event.rs, src/types/export.rs, src/types/import.rs, src/types/remote.rs, src/types/task.rs",
  "j_sibling_sites": "yes",
  "j_cause_other_layer": 1,
  "j_defence_ineffective": 1,
  "j_overbroad_breaks_legit": 1,
  "j_tempting_wrong_fix": "Drop {message} from the HttpWithBody #[error] format and redact message in ApiError's Debug, leaving reqwest URLs, JSON/decode/retry strings, runner task summaries and all model-type derived Debug impls untouched."
 },
 "out_of_scope_notes": [
  "The same fix commit also routes login/probes/streaming through the configured custom transport and disables redirects in the built-in reqwest clients (fix.diff:236-251, 264-481); these are separate transport-boundary concerns, not CWE-532.",
  "Pinned Cargo.toml version 0.6.0 vs fix 0.6.1; CHANGELOG/COMPATIBILITY/README edits ignored.",
  "Latest upstream has a new hubuum_reconcile crate that generates resource structs (latest/hubuum_reconcile/src/generate.rs:520) instead of the derive macro."
 ],
 "unverified": [
  "repo_mb not measured (no shell); the source is a single client library and likely under 5 MB, which would make tiny_repo apply, but this was not confirmed so the flag is left out.",
  "O1 count of 12 groups entry points by surface (ApiError Display, ApiError Debug, source chain, async retry, blocking retry, async runners, blocking runners, RawResponse, SetPasswordBody, event types, task/import/export types, remote result); finer counting gives ~40 sites (candidate metadata says 62 sites in 10 files).",
  "Pinned commit hash is not given; tree assumed to be the parent of the fix commit.",
  "Whether ObjectWithPath still exists in latest was not checked.",
  "Advisory text itself was not available; the trust decision is taken from the CHANGELOG security entry at fix.diff:11-34.",
  "Whether the 'default diagnostics' protection is documented project-wide was not checked beyond the CHANGELOG and docs/advanced.md hunks."
 ]
}
  ```
- Published fix sites:   - src/errors.rs:58 — entry point: Display of any ApiError::HttpWithBody returned by every typed/raw API call (e.g. client.classes().list()) [error type (core)]
  - src/errors.rs:16-20 — entry point: ApiError::from(reqwest::Error)/serde_json::Error via ? in every call; Display/Debug/source chain [error type (core)]
  - src/errors.rs:67 — entry point: DeserializationError Display from parse_response / TypedObject::try_from / SSE parsing [error type (core)]
  - src/errors.rs:88 — entry point: RetryExhausted Display from send_with_retry on any call [error type (core)]
  - src/errors.rs:151 — entry point: Debug of HttpWithBody message [error type (core)]
  - src/errors.rs:155-158 — entry point: Debug of DeserializationError [error type (core)]
  - src/errors.rs:183 — entry point: Debug of RetryExhausted last_error [error type (core)]
  - src/client/async.rs:454-457 — entry point: async send_with_retry on any request (reqwest error URL with query values) [async client implementation]
  - src/client/sync.rs:419-422 — entry point: blocking send_with_retry on any request [blocking client (second implementation)]
  - src/client/async.rs:3272 — entry point: async backups().run()...send() on failed task (summary copied into ApiError::Api) [high-level runner (async)]
  - src/client/async.rs:3536 — entry point: async exports().run() on failed task [high-level runner (async)]
  - src/client/async.rs:3661 — entry point: async export template run on failed task [high-level runner (async)]
  - src/client/async.rs:3804 — entry point: async imports().run() (refactor only, already summary-free) [high-level runner (async)]
  - src/client/sync.rs:3079 — entry point: blocking backups run on failed task [high-level runner (blocking)]
  - src/client/sync.rs:3322 — entry point: blocking exports run on failed task [high-level runner (blocking)]
  - src/client/sync.rs:3443 — entry point: blocking export template run on failed task [high-level runner (blocking)]
  - src/client/shared.rs:498-499 — entry point: Debug of internal RawResponse (body, next_cursor) used by raw()/paging [shared internal response type]
  - src/resources/user.rs:241-242 — entry point: Debug of SetPasswordBody behind user set_password API [resource request body]
  - src/types/event.rs:50 — entry point: Debug of EventSink returned by event sink list/get APIs (config, secret_ref) [public model type]
  - src/types/event.rs:64 — entry point: Debug of NewEventSink passed to sink create [public model type (request)]
  - src/types/event.rs:76 — entry point: Debug of UpdateEventSink passed to sink update [public model type (request)]
  - src/types/event.rs:118 — entry point: Debug of EventSubscription (routing) [public model type]
  - src/types/event.rs:136 — entry point: Debug of NewEventSubscription [public model type (request)]
  - src/types/event.rs:152 — entry point: Debug of UpdateEventSubscription [public model type (request)]
  - src/types/event.rs:185 — entry point: Debug of EventDelivery (claim_token, last_error) [public model type]
  - src/types/export.rs:150 — entry point: Debug of ExportJsonResponse from exports output [public model type]
  - src/types/export.rs:175 — entry point: Debug of ExportResult (rendered body) [public model type]
  - src/types/import.rs:117 — entry point: Debug of ImportClassInput (json_schema) [public model type (request)]
  - src/types/import.rs:129 — entry point: Debug of ImportObjectInput (data) [public model type (request)]
  - src/types/import.rs:171 — entry point: Debug of ImportGraph [public model type (request)]
  - src/types/import.rs:187 — entry point: Debug of ImportRequest passed to imports().run() [public model type (request)]
  - src/types/import.rs:225 — entry point: Debug of ImportRunResult returned by imports().run() [public model type]
  - src/types/remote.rs:419 — entry point: Debug of RemoteCallResult error (hand-written Debug that already redacts other fields) [public model type]
  - src/types/task.rs:62 — entry point: Debug of TaskLinks inside TaskResponse [public model type]
  - src/types/task.rs:75 — entry point: Debug of ImportTaskDetails [public model type]
  - src/types/task.rs:80 — entry point: Debug of ExportTaskDetails [public model type]
  - src/types/task.rs:92 — entry point: Debug of BackupTaskDetails [public model type]
  - src/types/task.rs:110 — entry point: Debug of TaskResponse (summary) from tasks get/poll [public model type]
  - src/types/task.rs:127 — entry point: Debug of TaskEventResponse (message, data) [public model type]
  - src/types/task.rs:138 — entry point: Debug of ImportTaskResultResponse (item_ref, identifier, error, details) [public model type]
- Uncovered routes to confirm (pattern B):   - src/types/backup.rs:233 — Restore staging response Debug prints the server-provided error string unredacted, while the fix redacts the analogous RemoteCallResult/EventDelivery/ImportTaskResult error fields (reason to dismiss: Backup/restore is a neighbouring feature not named in the changelog and the type already has a hand-written Debug, so it looks already reviewed; still in latest: yes)
  - src/types/event.rs:7-35 — Audit EventResponse derives Debug and prints before/after object snapshots, metadata and summary, in the same file where the fix redacted sink/subscription/delivery types (reason to dismiss: It's an audit-log record whose content is meant to be read; the changelog lists only sink configuration, routing and delivery; still in latest: yes)
  - hubuum_client_derive/src/lib.rs:332; src/resources/object.rs:32-33 — Generated resource structs (Object.data, Class.json_schema) derive Debug through the ApiResource macro, though the fix redacts the same object data and json_schema on the import input types (reason to dismiss: Object data is the caller's own primary resource, the derive macro is another crate, and redacting it would hamper ordinary debugging; still in latest: yes)
  - src/types/history.rs:33-54 — ObjectHistory.data and ClassHistory.json_schema keep derived Debug (reason to dismiss: History is a legacy/neighbouring read API, not mentioned in the advisory; still in latest: yes)
  - src/resources/object.rs:54-61 — ObjectWithPath.data (related-object graph) keeps derived Debug (reason to dismiss: Graph traversal type, not a diagnostic; still in latest: unknown)
- Design plan from the lead: No lead plan is provided for this task — you are the lead as well as the builder. Using the Design section above and the screener record, design the task yourself and WRITE YOUR PLAN in `notes.md` BEFORE you build:
  - choose the main lever and at least one more, each with a DIFFERENT reason a solver would dismiss or skip it;
  - decide the sites, routes and input shapes the security tests will cover;
  - identify the coupled must-keep-working behaviour next to each lever, for the functional tests;
  - for the injected track: decide the realistic sibling gap(s) to add — each must be code a maintainer could plausibly have left, reachable through the real entry point, covered by a stated invariant, and placed where the published fix never touches. Add 2–4 siblings at a recurring trust decision, each with its own reason a solver would skip it;
  - if this candidate cannot support a fair task that meets the bar (flaw does not reproduce at the pinned commit through a real entry point, needs network/GPU/GUI at run time, or no design meets the bar), STOP and report why. Do not ship a weak task.
Follow every rule in the Design, Report, Tests and Proof sections exactly. You choose the design; the rules are fixed.
- Host notes: none

## Design: where difficulty comes from
Models find the code the report leads to and diagnose it correctly. They fail on scope. Build these
in, in order of evidence:
1. **Pattern A: the published fix's far sites.**
   - The report leads to one site. The tests cover every entry point the published fix protects,
     including one in a module that looks out of scope: a second implementation, a lower-level
     public API, a wrapper, a save/reload path, or a defaults or merge route.
   - Give it a plausible **reason to dismiss**, and **distance**: another file or package from the
     landing point.
2. **Pattern B: uncovered routes.**
   - Routes into the same protected sink where the advisory's own protection is missing at the
     pinned commit, and which the published fix did not touch.
   - They are unmodified upstream code, so a solver can argue they were never covered.
   - The strongest lever found so far: DeepSeek 6 of 6 on one; both models 0 of 3 on three combined.
3. **Input-shape variants** that the general rule covers but a one-case fix misses (a plain string
   and an array).
4. **A coupled must-keep-working behaviour** next to the sink, tested functionally, so an
   over-broad fix fails. MiMo tends to over-harden.
5. **Producer off the check's path.** The check depends on data produced elsewhere (a schema,
   serializer, cache, mapper or config loader) and does not call it. It counts only if the producer
   is infrastructure, not a request handler.
6. **Injected siblings**, only where the plan asks for them. Each must be:
   - code a maintainer could have written, with no deceptive names or comments;
   - reachable through the real entry point;
   - covered by a stated invariant;
   - placed where the upstream fix never touches.

Aim for at least two levers with **different** reasons to dismiss.

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

## Environment (`tasks/hubuum-client-rust-mm/environment/Dockerfile`)
- **Base and code.** A small official base image. The repo goes into `/app` at the pinned commit,
  and `/app/.git` is then deleted.
- **Offline.** Install every dependency, tool and service the project and tests need; nothing may
  be downloaded at test time. Services start from `test.sh`.
- **Packages:** `patch`, `curl`, `ca-certificates`, `bash`, `git`.
- **Agent layer.** Append `harness/claude-code.Dockerfile.snippet` unchanged at the end.
- **No test code in the image.** The agent shares the container. Pre-build against stubs; `test.sh`
  copies the real tests in at grading time.
- **Project tests.** The project's own tests for the affected area must pass in the image at the
  pinned commit.
- **No leaked regression tests.** The pinned commit must not already contain the advisory's
  regression tests (check `git log` between the pinned and fix commits).

## Report to the solver (`tasks/hubuum-client-rust-mm/instruction.md`)
**Write:**
- what the system is, at product level;
- one observed impact, with ONE concrete trigger at user level (HTTP request, CLI call or public API
  use);
- the security properties as **invariants**: who may do what to which data, or what attacker input
  must never achieve. Word each so it covers every tested route and shape ("no value of X may …").
  If there are several, give one natural list, never a count;
- every **contract** the tests need:
  - the refusal form ("a client error with no side effect");
  - any interface or field name a test uses;
  - preservation clauses ("works exactly as today");
  - a legitimate magnitude next to any attack magnitude;
- that examples are examples, not the full set;
- the standard constraints block: fix the problem and its close variants; keep legitimate use
  working; do not modify or add tests; do not look up the upstream fix; do not special-case the
  example.

**Never write:**
- file, package, function, class, field or parameter names a user would not see;
- line numbers, the root cause, the fix approach, or a CVE or GHSA id;
- a list of routes, spellings or roles;
- restricting adverbs ("directly", "only via");
- anything that names or paraphrases a far site, an uncovered route or an injected sibling.

Put every identifier that must not appear in `manifest.leak_terms`.

## Tests (`tasks/hubuum-client-rust-mm/tests/`)
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
- **Wrong-fix patches** go in `build/hubuum-client-rust-mm/checks/`, listed in `manifest.patch_checks`:
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
**`tasks/hubuum-client-rust-mm/`:**
- `instruction.md`;
- `task.toml`, from `builder/templates/`, with `[metadata]` filled in and the network allowlist
  kept;
- `environment/Dockerfile`;
- `solution/solve.sh` and `solution/fix.patch`;
- `tests/test.sh`, `tests/score.py`, `tests/security/` and `tests/functional/`.

**`build/hubuum-client-rust-mm/manifest.json`:**
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

**Also in `build/hubuum-client-rust-mm/`:**
- `checks/*.patch`;
- `notes.md`: start and end UTC, each lever in one line, what you verified, what you could not.

Pattern B: the register rows (see Design).

Use `builder/templates/` and `harness/smoke-task/` for the layout.

## Run the gate
Run the stages in order, one at a time:
```
python3 -I builder/gate.py hubuum-client-rust-mm --only static
python3 -I builder/gate.py hubuum-client-rust-mm --only nop
python3 -I builder/gate.py hubuum-client-rust-mm --only oracle
python3 -I builder/gate.py hubuum-client-rust-mm --only patches
```
In static, only the missing `blind` patch and the missing `FAIRNESS.md` may remain; others write
those after you. Do NOT write them yourself, and do NOT run trials or any target model.

## Machine and files
- **The machine:** one shared 8-CPU / 12 GB Docker VM that is running trials.
  - At most one Docker build or gate stage of yours at a time.
  - Never prune Docker images or the build cache.
  - Never stop containers you did not start.
- **Files:**
  - scratch work goes in `~/.tb-graders/cwe/work/hubuum-client-rust-mm/`;
  - edit only `tasks/hubuum-client-rust-mm/`, `build/hubuum-client-rust-mm/` and, for pattern B, the register;
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
