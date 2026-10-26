# hubuum-client-rust-ds — build notes

Start UTC: 2026-10-18T23:35:44Z
End UTC: 2026-10-19T02:12:00Z

Task: hubuum/hubuum-client-rust, advisory GHSA-2625-RW7M-5Q5X (CWE-532), pinned at
9c123207eb141ef1cfc8f53af538a06eeb458461 = direct parent of fix 5a5c275ffa45f342459b7d3e977926da643bde50.
Pattern A+B, track injected, strict gate.

## Design summary (chosen before building)

Protected sink: the default `Display` / `Debug` / `std::error::Error::source` rendering of errors and
public result types the library returns. Explicit fields and accessors stay unchanged; serialization
stays unchanged. Tests assert markers are absent from default diagnostics and present in the fields.

Levers (one line each):

- T1 (A, landing) `src/errors.rs` `ApiError` HTTP-with-body arm: server message/body in `Display`
  and `Debug`. Reason to dismiss: none; it is the reported symptom. Coupled functional: the
  documented accessors still return the original message/body/url/status.
- T2 (A, far, same error enum) `src/errors.rs` JSON/decode/retry arms: server/transport detail in
  `Display`, `Debug`, and the `source` chain. Reason to dismiss: "these are technical codec/retry
  details, not HTTP error text". Coupled functional: failures still surface, retries still happen.
- T3 (A, far, high-level runners) `src/client/async.rs` and `src/client/sync.rs` backup/export/
  export-template run operations copy the server task summary into `ApiError::Api`. Reason to
  dismiss: "the summary is a status line, not a secret". Coupled functional: successful runs still
  return their output and failed runs still return an error.
- T4 (A, far, result model types) derived/hand-written `Debug` on `TaskResponse`,
  `TaskEventResponse`, `ImportTaskResultResponse`, `ImportRunResult`, `EventSink`, `EventDelivery`,
  `ExportJsonResponse`/`ExportResult`, `RemoteCallResult`, internal raw response. Reason to dismiss:
  "plain data the caller already holds; not error diagnostics". Shapes: required `Value`, optional
  strings, nested containers. Coupled functional: fields readable, serde unchanged, Debug keeps
  ids/names/statuses/counts.
- B1 (uncovered route, real upstream) `src/types/event.rs` audit event response derives `Debug` and
  prints summary/before/after/metadata. Reason to dismiss: "an audit-log record is meant to be
  read; the report is about errors". Coupled functional: id/entity/action remain visible.
- B2 (uncovered route, real upstream) `src/types/backup.rs` restore-stage response has a
  hand-written `Debug` that forwards the server error string. Reason to dismiss: "backup/restore is
  a neighbouring feature and the hand-written Debug looks reviewed". Coupled functional: error and
  status fields remain readable.
- B3 (uncovered route, real upstream) `src/types/history.rs` object/class history derive `Debug`
  and print the object data / class schema. Reason to dismiss: "history is a neighbouring read API
  and history rows are data you asked for". Coupled functional: data/schema fields readable.
- S1 (injected sibling, async+blocking) a convenience restore run operation (added to both clients)
  stages, polls, and on failure formats the server restore error into `ApiError::Api`. Reason to
  dismiss: "a new convenience in the backup/restore subsystem; the string is not a task summary".
  Coupled functional: successful restore runs return the response, failures still error.
- S3 (injected sibling) `EventSinkDeliveryHealth` (nested in the event-delivery health response)
  gains a server `last_error` field with derived `Debug`. Reason to dismiss: "an operational health
  view is diagnostics by definition; the field is nested". Coupled functional: sink name/counts
  remain visible, `last_error` field readable.

Why this meets the bar: two independent reasons to dismiss (T2/T4 "not diagnostics/plain data") plus
three real unmodified upstream routes that the published fix never touched (B1-B3) plus two injected
siblings in code the fix never touches (S1, S3). The instruction states the invariant generally, so a
careful engineer can find every lever from the code without being told a route list.

## Routes / input shapes covered by security tests

- Error diagnostics: HTTP-with-body JSON message and plain-text body; typed decode failure; direct
  JSON codec failure; custom-transport retry exhaustion; async and blocking clients.
- Runner summaries: async and blocking export run on a failed task.
- Result values returned by real API calls: tasks get, task events, event delivery get, event sink
  get, export output (rendered and JSON), import results, import run, audit event list, restore
  stage, object history, event-delivery health.
- Shapes: required `serde_json::Value`, `Option<String>`, required `String`, nested containers
  (`ImportRunResult` -> task + changes; export JSON response -> items/warnings).

## Coupled must-keep-working behaviour (functional tests)

Accessors return originals; public fields readable and serializable; failures still fail; retries
still retry; successful flows still succeed; Debug still shows non-sensitive identifiers, names,
statuses and counts (over-broad redaction fails).

## Injected siblings

`environment/injection.patch` adds, in code the published fix never touches:
1. async `Restores::run` + `RestoreRunOp` (server restore error into `ApiError::Api`);
2. blocking `Restores::run` + `RestoreRunOp` (same);
3. `EventSinkDeliveryHealth.last_error` with derived `Debug`.
No deceptive names or comments; all reachable through public entry points; all covered by the
instruction's invariant.

## Test/run mechanics

- Hidden Rust integration tests (`tests/security/sec_hubuum.rs`, `tests/functional/fun_hubuum.rs`)
  are copied into `/app/tests/` at grading time and run with
  `cargo test --offline --locked --features blocking --test ... -- --test-threads=1`.
- A small converter under `tests/` turns libtest output into JUnit XML in
  `/logs/verifier/{security,functional}/`.
- Project tests included in functional: pristine pinned `errors::tests` and the existing
  foundations redaction test (both behaviour-stable across the fix).
- Only custom in-process transport (`MockTransport` / an error transport) is used; no external
  network.

## Verified

- Pinned tree (injected, no fix): all 21 security tests fail; all 11 hidden functional tests pass;
  the pinned project tests run in the image (`errors::tests::exposes_structured_api_error_response`
  and `foundations::response_and_error_debug_output_redacts_sensitive_values`) pass.
- Oracle tree: all 21 security tests pass; all 11 hidden functional tests pass; both project tests
  pass.
- Local variant sweep (in-process MockTransport, same image):
  - sf-http-envelope 19/21 security, sf-decode-retry 18/21, sf-runners 19/21, sf-result-models 13/21,
    sf-audit-event 20/21, sf-restore-stage 20/21, sf-history-payloads 20/21, sf-restore-run 19/21,
    sf-sink-health 20/21; every one keeps all 11 hidden functional tests passing.
  - ff-overbroad: all security tests pass but 4 of 11 functional tests fail (over-broad redaction).
  - pass-hardening and pass-alt: 21/21 security and 11/11 functional.
  - Every check patch applies cleanly to the injected pinned tree with `patch -p1`.

## Could not verify / out of scope

- The published commit also reroutes login/probes/streaming through a custom transport and disables
  redirects; those are separate transport-boundary concerns, not CWE-532, and are not built on.
- Advisory prose itself was not available; the trust decision follows the fix's source changes.

## Gate results

- static: only the expected two gaps remain (`blind` pass patch and FAIRNESS.md, both written by
  others after the builder), everything else in the static check passes.
- nop: PASSED — 21 security tests all failed, 13 functional tests passed (11 hidden + 2 project).
- oracle: PASSED — 3 independent trials, reward 1.0 each, identical results.
- patches: PASSED — 12/12 checks behaved as declared: sf-http-envelope 2 security failures,
  sf-decode-retry 3, sf-runners 2, sf-result-models 8, sf-audit-event 1, sf-restore-stage 1,
  sf-history-payloads 1, sf-restore-run 2, sf-sink-health 1 (all with zero functional failures);
  ff-overbroad failed 5 functional tests; pass-hardening and pass-alt both scored 1.0.
  The first attempts hit the shared-machine Docker network-prune race (`network ... not found`),
  an infrastructure error; a bounded retry produced a clean pass. task.toml was not weakened.

## What I could not verify

- The advisory prose itself (not available); the trust decision follows the published fix's source
  changes and the CHANGELOG security entry.
- The exact upstream report/public disclosure status; `public_upstream_report` is left `unknown` in
  the register.
- One screener lead was not used: `SetPasswordBody` loses `Debug` in the published fix but the
  private type is not observable through the public API, so it is not a scored lever.

## Fairness assessment

- Every scored route is reachable through a documented public method and was confirmed on the
  pinned copy before the task was written.
- The instruction gives the invariant (no server/caller secrets in default `Display`/`Debug`/source,
  including nested values and both clients) and the coupled contracts (accessors keep originals,
  diagnostics keep identifiers/names/statuses/counts). It does not name a route or a far site.
- The remaining risk is breadth: a solver must enumerate result types and both clients. That is
  findable from the code (`derive(Debug)` / hand-written impls) and is the intended scope lever.
- No test asserts a single exact refusal status and no test imports product helpers to compute
  expected values.

## Upgrade 2026-10-20 (sibling-injection / BETTER-PATTERNS rules)

- instruction.md rewritten to one general property over server-supplied content and
  caller-supplied secrets in default diagnostics. Removed the async/blocking surface list
  (`resources, jobs, eventing, import/export, remote calls, administrative views`), the
  concrete typed-list trigger naming `client.classes().list()`, the "ordinary structs /
  payload fields" description, and the "one example" sentence. Coupled contracts stay in
  property terms.
- Lever types recorded in the manifest: T3 is how-type M11 (the failed-run diagnostic must
  keep the task identifier and status while dropping the server detail); B1/B2/B3 and the
  injected S1/S3 are how-type M4 (routes where the protection never existed). T1/T2/T4 are
  where-type extras.
- Coverage added (tests only; repo, environment, solution and checks unchanged):
  - `security/sec_hubuum.rs::class_history_debug_omits_schema_payload` — the class-history
    sibling of the B3 lever; it was real upstream code with no protection and no test.
    `sf-history-payloads.patch` misses it too (now 2 security failures).
  - `security/sec_hubuum.rs::event_subscription_debug_omits_routing` — an event result model
    reached through the collection subscription route; `sf-result-models.patch` misses it.
  - `security/sec_hubuum.rs::task_response_debug_omits_nested_link_and_detail_values` — the
    link/detail containers nested in a returned task, previously not asserted.
  - `event_sink_debug_omits_configuration` now also asserts the sink `secret_ref` marker.
  - `functional/fun_hubuum.rs::runner_error_keeps_task_identity_and_status` — makes the M11
    coupled contract explicit without asserting the secret (it must pass on the pinned tree).
- Verified locally in the prebuilt `hubuum-ds-dev:base` image (same `cargo test --offline`
  commands as the verifier):
  - pinned: security 0/24, functional 12/12; both project tests pass.
  - oracle (`solution/fix.patch`): security 24/24, functional 12/12; both project tests pass.
  - pass-hardening and pass-alt: 24/24 + 12/12; ff-overbroad: 24/24 security, 4/12
    functional failures (unchanged expectation).
  - sf-result-models: 14/24 security (still security_fail), 12/12 functional.
  - sf-history-payloads: 22/24 security (object + class history, still security_fail),
    12/12 functional.
- No image rebuild: no file under `environment/`, `solution/` or the repository changed.
