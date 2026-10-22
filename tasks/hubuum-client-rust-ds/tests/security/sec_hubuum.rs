//! Hidden behavioural security tests: default diagnostics must not carry
//! server-provided or caller-secret content. Every test drives a public entry
//! point of the library and only asserts that the marker is absent.

use std::sync::Arc;
use std::time::Duration;

use hubuum_client::{
    ApiError, Authenticated, BackupDocument, BaseUrl, Client, ExportRequest, ExportScope,
    ExportScopeKind, MockTransport, RequestPlan, RetryPolicy, Token, TransportResponse,
};
use reqwest::StatusCode;
use serde_json::{Value, json};

fn async_client(transport: MockTransport) -> Client<Authenticated> {
    Client::builder(BaseUrl::new("https://example.invalid").unwrap())
        .with_transport(Arc::new(transport))
        .retry_policy(RetryPolicy::disabled())
        .build()
        .unwrap()
        .authenticate(Token::new("consumer-secret"))
}

fn blocking_client(transport: MockTransport) -> hubuum_client::blocking::Client<Authenticated> {
    hubuum_client::blocking::Client::builder(BaseUrl::new("https://example.invalid").unwrap())
        .with_transport(Arc::new(transport))
        .retry_policy(RetryPolicy::disabled())
        .build()
        .unwrap()
        .authenticate(Token::new("consumer-secret"))
}

fn json_response(status: StatusCode, body: &Value) -> TransportResponse {
    TransportResponse::json(status, body).unwrap()
}

fn text_response(status: StatusCode, content_type: &str, body: &str) -> TransportResponse {
    let mut headers = reqwest::header::HeaderMap::new();
    headers.insert(
        reqwest::header::CONTENT_TYPE,
        reqwest::header::HeaderValue::from_str(content_type).unwrap(),
    );
    TransportResponse {
        status,
        headers,
        body: body.as_bytes().to_vec(),
    }
}

fn assert_absent(error: &ApiError, secret: &str) {
    let display = error.to_string();
    assert!(!display.contains(secret), "Display leaked {secret}: {display}");
    let debug = format!("{error:?}");
    assert!(!debug.contains(secret), "Debug leaked {secret}: {debug}");
    let mut source = std::error::Error::source(error);
    while let Some(inner) = source {
        let text = inner.to_string();
        assert!(!text.contains(secret), "source leaked {secret}: {text}");
        source = std::error::Error::source(inner);
    }
}

fn task_json(id: i64, status: &str, summary: Option<&str>) -> Value {
    json!({
        "id": id,
        "kind": "export",
        "status": status,
        "submitted_by": 1,
        "created_at": "2026-07-23T08:00:00Z",
        "started_at": null,
        "finished_at": null,
        "progress": {
            "total_items": 1,
            "processed_items": 1,
            "success_items": 0,
            "failed_items": 1
        },
        "summary": summary,
        "request_redacted_at": null,
        "links": {
            "task": format!("/api/v1/tasks/{id}"),
            "events": format!("/api/v1/tasks/{id}/events")
        },
        "details": null
    })
}

fn export_request() -> ExportRequest {
    ExportRequest {
        limits: None,
        missing_data_policy: None,
        query: None,
        scope: ExportScope {
            class_id: None,
            kind: ExportScopeKind::Collections,
            object_id: None,
        },
        include: None,
        relation_context: None,
    }
}

fn backup_document() -> BackupDocument {
    serde_json::from_value(json!({
        "backup_version": 3,
        "created_at": "2026-07-23T08:00:00",
        "source_version": "0.0.3",
        "state": {"sections": {}},
        "history": null,
        "manifest": {"item_counts": {}, "exclusions": []}
    }))
    .expect("backup document fixture should deserialize")
}

fn restore_stage_json(status: &str, error: Option<&str>, capability: Option<&str>) -> Value {
    json!({
        "id": 5,
        "status": status,
        "requested_by": 1,
        "requested_by_identity_scope": "local",
        "requested_by_name": "alice",
        "sha256": "abc123",
        "byte_size": 10,
        "expires_at": "2026-07-23T09:00:00Z",
        "error": error,
        "confirmed_at": null,
        "started_at": null,
        "finished_at": null,
        "created_at": "2026-07-23T08:00:00Z",
        "updated_at": "2026-07-23T08:00:00Z",
        "validation": {
            "backup_version": 3,
            "source_version": "0.0.3",
            "includes_history": true,
            "total_items": 1
        },
        "restore_capability": capability
    })
}

fn event_sink_json() -> Value {
    json!({
        "id": 1,
        "name": "sink-one",
        "kind": "webhook",
        "config": {
            "url": "https://example.invalid/hook",
            "token": "sink-config-secret"
        },
        "enabled": true,
        "secret_ref": "sink-secret-ref",
        "created_at": "2026-07-23T08:00:00Z",
        "updated_at": "2026-07-23T08:00:00Z"
    })
}

fn delivery_json() -> Value {
    json!({
        "id": 41,
        "event_id": 42,
        "subscription_id": 43,
        "status": "failed",
        "attempts": 2,
        "next_attempt_at": "2026-07-23T08:00:01Z",
        "claim_token": "delivery-claim-secret",
        "last_error": "sink rejected bearer delivery-error-secret",
        "locked_until": "2026-07-23T08:01:00Z",
        "created_at": "2026-07-23T07:59:00Z",
        "updated_at": "2026-07-23T08:00:00Z"
    })
}

// ---------------------------------------------------------------------------
// T1: HTTP error envelope
// ---------------------------------------------------------------------------

#[tokio::test]
async fn http_error_details_absent_from_display_and_debug() {
    let transport = MockTransport::default();
    transport.push_response(json_response(
        StatusCode::UNAUTHORIZED,
        &json!({"error": "Unauthorized", "message": "http-error-message-secret"}),
    ));
    let client = async_client(transport);
    let error = client.classes().list().await.unwrap_err();
    assert_absent(&error, "http-error-message-secret");
}

#[tokio::test]
async fn http_error_plain_text_body_absent_from_display_and_debug() {
    let transport = MockTransport::default();
    transport.push_response(text_response(
        StatusCode::BAD_GATEWAY,
        "text/plain",
        "upstream failed with plain-body-secret",
    ));
    let client = async_client(transport);
    let error = client.classes().list().await.unwrap_err();
    assert_absent(&error, "plain-body-secret");
}

// ---------------------------------------------------------------------------
// T2: decode and retry diagnostics
// ---------------------------------------------------------------------------

#[tokio::test]
async fn decode_error_details_absent_from_default_diagnostics() {
    let transport = MockTransport::default();
    transport.push_response(json_response(
        StatusCode::OK,
        &json!([{
            "id": "decode-marker-secret",
            "name": "class",
            "description": "class",
            "collection": {
                "id": 7,
                "name": "collection",
                "description": "collection",
                "created_at": "2026-07-23T08:00:00Z",
                "updated_at": "2026-07-23T08:00:00Z"
            },
            "json_schema": null,
            "validate_schema": null,
            "created_at": "2026-07-23T08:00:00Z",
            "updated_at": "2026-07-23T08:00:00Z"
        }]),
    ));
    let client = async_client(transport);
    let error = client.classes().list().await.unwrap_err();
    assert_absent(&error, "decode-marker-secret");
}

#[tokio::test]
async fn json_error_details_absent_from_default_diagnostics() {
    let transport = MockTransport::default();
    transport.push_response(json_response(
        StatusCode::OK,
        &json!({
            "config": {
                "enabled": true,
                "backend": "memory",
                "max_attempts": 5,
                "max_attempts_per_ip": 20,
                "max_attempts_per_subnet": 100,
                "window_seconds": 300,
                "backoff_base_seconds": 300,
                "backoff_max_seconds": 86400,
                "subnet_prefix_v4": 24,
                "subnet_prefix_v6": 64
            },
            "tracked_entries": "json-codec-secret",
            "locked_entries": 0,
            "returned_entries": 0,
            "entries": []
        }),
    ));
    let client = async_client(transport);
    let error = client.meta_login_rate_limit().send().await.unwrap_err();
    assert_absent(&error, "json-codec-secret");
}

#[derive(Debug)]
struct FailingTransport {
    detail: String,
}

impl hubuum_client::AsyncTransport for FailingTransport {
    fn execute<'a>(
        &'a self,
        _request: RequestPlan,
    ) -> std::pin::Pin<
        Box<dyn std::future::Future<Output = Result<TransportResponse, ApiError>> + Send + 'a>,
    > {
        Box::pin(async move { Err(ApiError::Transport(self.detail.clone())) })
    }
}

#[tokio::test]
async fn retry_error_details_absent_from_default_diagnostics() {
    let client = Client::builder(BaseUrl::new("https://example.invalid").unwrap())
        .with_transport(Arc::new(FailingTransport {
            detail: "retry-detail-secret".to_string(),
        }))
        .retry_policy(RetryPolicy::disabled())
        .build()
        .unwrap()
        .authenticate(Token::new("consumer-secret"));
    let error = client.classes().list().await.unwrap_err();
    assert_absent(&error, "retry-detail-secret");
}

// ---------------------------------------------------------------------------
// T3: high-level run operations
// ---------------------------------------------------------------------------

#[tokio::test]
async fn runner_summary_absent_from_default_diagnostics() {
    let transport = MockTransport::default();
    transport.push_response(json_response(
        StatusCode::ACCEPTED,
        &task_json(11, "queued", None),
    ));
    transport.push_response(json_response(
        StatusCode::OK,
        &task_json(11, "failed", Some("async-runner-summary-secret")),
    ));
    let client = async_client(transport);
    let error = client
        .exports()
        .run(export_request())
        .poll_interval(Duration::from_millis(1))
        .timeout(Some(Duration::from_secs(5)))
        .send()
        .await
        .unwrap_err();
    assert_absent(&error, "async-runner-summary-secret");
}

#[test]
fn blocking_runner_summary_absent_from_default_diagnostics() {
    let transport = MockTransport::default();
    transport.push_response(json_response(
        StatusCode::ACCEPTED,
        &task_json(11, "queued", None),
    ));
    transport.push_response(json_response(
        StatusCode::OK,
        &task_json(11, "failed", Some("blocking-runner-summary-secret")),
    ));
    let client = blocking_client(transport);
    let error = client
        .exports()
        .run(export_request())
        .poll_interval(Duration::from_millis(1))
        .timeout(Some(Duration::from_secs(5)))
        .send()
        .unwrap_err();
    assert_absent(&error, "blocking-runner-summary-secret");
}

// ---------------------------------------------------------------------------
// T4: result model types
// ---------------------------------------------------------------------------

#[tokio::test]
async fn task_response_debug_omits_server_summary() {
    let transport = MockTransport::default();
    transport.push_response(json_response(
        StatusCode::OK,
        &task_json(11, "failed", Some("task-summary-secret")),
    ));
    let client = async_client(transport);
    let task = client.tasks().get(11).await.unwrap();
    let debug = format!("{task:?}");
    assert!(!debug.contains("task-summary-secret"), "{debug}");
}

#[tokio::test]
async fn task_response_debug_omits_nested_link_and_detail_values() {
    let transport = MockTransport::default();
    transport.push_response(json_response(
        StatusCode::OK,
        &json!({
            "id": 11,
            "kind": "import",
            "status": "failed",
            "submitted_by": 1,
            "created_at": "2026-07-23T08:00:00Z",
            "started_at": null,
            "finished_at": null,
            "progress": {
                "total_items": 1,
                "processed_items": 1,
                "success_items": 0,
                "failed_items": 1
            },
            "summary": null,
            "request_redacted_at": null,
            "links": {
                "task": "/api/v1/tasks/11?capability=link-task-secret",
                "events": "/api/v1/tasks/11/events?token=link-events-secret",
                "import": "/api/v1/imports/11?token=link-import-secret",
                "import_results": "/api/v1/imports/11/results?token=link-results-secret",
                "export": "/api/v1/exports/11?token=link-export-secret",
                "export_output": "/api/v1/exports/11/output?token=link-output-secret",
                "backup": "/api/v1/backups/11?token=link-backup-secret",
                "backup_output": "/api/v1/backups/11/output?token=link-backup-output-secret"
            },
            "details": {
                "import": {
                    "results_url": "/api/v1/imports/11/results?token=detail-import-secret"
                },
                "export": {
                    "output_url": "/api/v1/exports/11/output?token=detail-export-secret",
                    "output_available": true,
                    "output_expired": false
                },
                "backup": {
                    "output_url": "/api/v1/backups/11/output?token=detail-backup-secret",
                    "output_available": true,
                    "output_expired": false
                }
            }
        }),
    ));
    let client = async_client(transport);
    let task = client.tasks().get(11).await.unwrap();
    let debug = format!("{task:?}");
    for secret in [
        "link-task-secret",
        "link-events-secret",
        "link-import-secret",
        "link-results-secret",
        "link-export-secret",
        "link-output-secret",
        "link-backup-secret",
        "link-backup-output-secret",
        "detail-import-secret",
        "detail-export-secret",
        "detail-backup-secret",
    ] {
        assert!(!debug.contains(secret), "{secret} leaked: {debug}");
    }
}

#[tokio::test]
async fn task_event_debug_omits_message_and_data() {
    let transport = MockTransport::default();
    transport.push_response(json_response(
        StatusCode::OK,
        &json!([{
            "id": 7,
            "task_id": 11,
            "event_type": "failed",
            "message": "event-message-secret",
            "data": {"token": "event-data-secret"},
            "created_at": "2026-07-23T08:00:00Z"
        }]),
    ));
    let client = async_client(transport);
    let events = client.tasks().events(11).list().await.unwrap();
    let debug = format!("{events:?}");
    assert!(!debug.contains("event-message-secret"), "{debug}");
    assert!(!debug.contains("event-data-secret"), "{debug}");
}

#[tokio::test]
async fn event_delivery_debug_omits_claim_token_and_error() {
    let transport = MockTransport::default();
    transport.push_response(json_response(StatusCode::OK, &delivery_json()));
    let client = async_client(transport);
    let delivery = client.event_deliveries().get(41).await.unwrap();
    let debug = format!("{delivery:?}");
    assert!(!debug.contains("delivery-claim-secret"), "{debug}");
    assert!(!debug.contains("delivery-error-secret"), "{debug}");
}

#[tokio::test]
async fn event_sink_debug_omits_configuration() {
    let transport = MockTransport::default();
    transport.push_response(json_response(StatusCode::OK, &event_sink_json()));
    let client = async_client(transport);
    let sink = client.event_sinks().get(1).await.unwrap().into_inner();
    let debug = format!("{sink:?}");
    assert!(!debug.contains("sink-config-secret"), "{debug}");
    assert!(!debug.contains("sink-secret-ref"), "{debug}");
}

#[tokio::test]
async fn event_subscription_debug_omits_routing() {
    let transport = MockTransport::default();
    transport.push_response(json_response(
        StatusCode::OK,
        &json!({
            "id": 2,
            "collection_id": 7,
            "sink_id": 1,
            "name": "subscription-one",
            "description": "subscription",
            "entity_types": ["object"],
            "actions": ["updated"],
            "routing": {
                "url": "https://example.invalid/hook",
                "token": "subscription-routing-secret"
            },
            "enabled": true,
            "filter": null,
            "created_at": "2026-07-23T08:00:00Z",
            "updated_at": "2026-07-23T08:00:00Z"
        }),
    ));
    let client = async_client(transport);
    let subscription = client.event_subscriptions(7).get(2).await.unwrap();
    let debug = format!("{subscription:?}");
    assert!(!debug.contains("subscription-routing-secret"), "{debug}");
}

#[tokio::test]
async fn export_result_debug_omits_rendered_body() {
    let transport = MockTransport::default();
    transport.push_response(text_response(
        StatusCode::OK,
        "text/csv",
        "rendered-export-secret",
    ));
    let client = async_client(transport);
    let result = client.exports().output(11).await.unwrap();
    let debug = format!("{result:?}");
    assert!(!debug.contains("rendered-export-secret"), "{debug}");
}

#[tokio::test]
async fn export_json_debug_omits_items_and_warnings() {
    let transport = MockTransport::default();
    transport.push_response(json_response(
        StatusCode::OK,
        &json!({
            "items": [{"secret": "json-export-secret"}],
            "meta": {
                "content_type": "application/json",
                "count": 1,
                "scope": {"class_id": null, "kind": "collections", "object_id": null},
                "truncated": false
            },
            "warnings": [{"code": "w", "message": "warning-export-secret", "path": null}]
        }),
    ));
    let client = async_client(transport);
    let result = client.exports().output(11).await.unwrap();
    let debug = format!("{result:?}");
    assert!(!debug.contains("json-export-secret"), "{debug}");
    assert!(!debug.contains("warning-export-secret"), "{debug}");
}

#[tokio::test]
async fn import_results_debug_omit_server_error_details() {
    let transport = MockTransport::default();
    transport.push_response(json_response(
        StatusCode::OK,
        &json!([{
            "id": 9,
            "task_id": 11,
            "item_ref": "item-ref",
            "entity_kind": "object",
            "action": "create",
            "identifier": "identifier",
            "outcome": "failed",
            "error": "import-error-secret",
            "details": {"token": "import-details-secret"},
            "created_at": "2026-07-23T08:00:00Z"
        }]),
    ));
    let client = async_client(transport);
    let results = client.imports().results(11).list().await.unwrap();
    let debug = format!("{results:?}");
    assert!(!debug.contains("import-error-secret"), "{debug}");
    assert!(!debug.contains("import-details-secret"), "{debug}");
}

#[tokio::test]
async fn import_run_result_debug_omits_nested_result_details() {
    let transport = MockTransport::default();
    transport.push_response(json_response(
        StatusCode::ACCEPTED,
        &task_json(11, "queued", None),
    ));
    transport.push_response(json_response(
        StatusCode::OK,
        &task_json(11, "succeeded", Some("ok")),
    ));
    transport.push_response(json_response(
        StatusCode::OK,
        &json!([{
            "id": 9,
            "task_id": 11,
            "item_ref": "item-ref",
            "entity_kind": "object",
            "action": "create",
            "identifier": "identifier",
            "outcome": "failed",
            "error": "import-run-error-secret",
            "details": {"token": "import-run-details-secret"},
            "created_at": "2026-07-23T08:00:00Z"
        }]),
    ));
    let client = async_client(transport);
    let result = client
        .imports()
        .run(hubuum_client::ImportRequest::new(
            hubuum_client::ImportGraph::default(),
        ))
        .poll_interval(Duration::from_millis(1))
        .timeout(Some(Duration::from_secs(5)))
        .send()
        .await
        .unwrap();
    let debug = format!("{result:?}");
    assert!(!debug.contains("import-run-error-secret"), "{debug}");
    assert!(!debug.contains("import-run-details-secret"), "{debug}");
}

// ---------------------------------------------------------------------------
// B1: audit event records
// ---------------------------------------------------------------------------

#[tokio::test]
async fn audit_event_debug_omits_snapshots() {
    let transport = MockTransport::default();
    transport.push_response(json_response(
        StatusCode::OK,
        &json!([{
            "id": 1,
            "event_id": "evt-1",
            "occurred_at": "2026-07-23T08:00:00Z",
            "entity_type": "object",
            "entity_id": 9,
            "entity_name": "history-object",
            "collection_id": 7,
            "action": "updated",
            "actor_kind": "user",
            "actor_user_id": 1,
            "correlation_id": null,
            "request_id": null,
            "summary": "audit-summary-secret",
            "before": {"token": "audit-before-secret"},
            "after": {"token": "audit-after-secret"},
            "metadata": {"token": "audit-metadata-secret"},
            "schema_version": 1
        }]),
    ));
    let client = async_client(transport);
    let events = client.events().list().await.unwrap();
    let debug = format!("{events:?}");
    for secret in [
        "audit-summary-secret",
        "audit-before-secret",
        "audit-after-secret",
        "audit-metadata-secret",
    ] {
        assert!(!debug.contains(secret), "{secret} leaked: {debug}");
    }
}

// ---------------------------------------------------------------------------
// B2: restore stage response
// ---------------------------------------------------------------------------

#[tokio::test]
async fn restore_stage_debug_omits_server_error() {
    let transport = MockTransport::default();
    transport.push_response(json_response(
        StatusCode::OK,
        &restore_stage_json("failed", Some("restore-stage-error-secret"), Some("cap")),
    ));
    let client = async_client(transport);
    let staged = client.restores().stage(&backup_document()).await.unwrap();
    let debug = format!("{staged:?}");
    assert!(!debug.contains("restore-stage-error-secret"), "{debug}");
}

// ---------------------------------------------------------------------------
// B3: history payloads
// ---------------------------------------------------------------------------

#[tokio::test]
async fn object_history_debug_omits_object_data() {
    let transport = MockTransport::default();
    transport.push_response(json_response(
        StatusCode::OK,
        &json!([{
            "id": 9,
            "name": "history-object",
            "collection_id": 7,
            "hubuum_class_id": 42,
            "data": {"token": "history-data-secret"},
            "description": "object",
            "created_at": "2026-07-23T08:00:00Z",
            "updated_at": "2026-07-23T08:00:00Z",
            "op": "update",
            "valid_from": "2026-07-23T08:00:00Z",
            "valid_to": null,
            "history_id": 1,
            "actor_id": 1,
            "actor_username": "alice"
        }]),
    ));
    let client = async_client(transport);
    let history = client.object_history(42, 9).list().await.unwrap();
    let debug = format!("{history:?}");
    assert!(!debug.contains("history-data-secret"), "{debug}");
}

#[tokio::test]
async fn class_history_debug_omits_schema_payload() {
    let transport = MockTransport::default();
    transport.push_response(json_response(
        StatusCode::OK,
        &json!([{
            "id": 42,
            "name": "history-class",
            "collection_id": 7,
            "validate_schema": true,
            "description": "class",
            "json_schema": {"default": "class-schema-secret"},
            "created_at": "2026-07-23T08:00:00Z",
            "updated_at": "2026-07-23T08:00:00Z",
            "op": "update",
            "valid_from": "2026-07-23T08:00:00Z",
            "valid_to": null,
            "history_id": 1,
            "actor_id": 1,
            "actor_username": "alice"
        }]),
    ));
    let client = async_client(transport);
    let history = client.class_history(42).list().await.unwrap();
    let debug = format!("{history:?}");
    assert!(!debug.contains("class-schema-secret"), "{debug}");
}

// ---------------------------------------------------------------------------
// S1: injected restore run convenience (async + blocking)
// ---------------------------------------------------------------------------

#[tokio::test]
async fn restore_run_async_error_omits_server_detail() {
    let transport = MockTransport::default();
    transport.push_response(json_response(
        StatusCode::OK,
        &restore_stage_json("validated", None, Some("cap")),
    ));
    transport.push_response(json_response(
        StatusCode::OK,
        &restore_stage_json("failed", Some("restore-run-error-secret"), None),
    ));
    let client = async_client(transport);
    let error = client
        .restores()
        .run(&backup_document())
        .poll_interval(Duration::from_millis(1))
        .timeout(Some(Duration::from_secs(5)))
        .send()
        .await
        .unwrap_err();
    assert_absent(&error, "restore-run-error-secret");
}

#[test]
fn restore_run_blocking_error_omits_server_detail() {
    let transport = MockTransport::default();
    transport.push_response(json_response(
        StatusCode::OK,
        &restore_stage_json("validated", None, Some("cap")),
    ));
    transport.push_response(json_response(
        StatusCode::OK,
        &restore_stage_json("failed", Some("restore-run-error-secret"), None),
    ));
    let client = blocking_client(transport);
    let error = client
        .restores()
        .run(&backup_document())
        .poll_interval(Duration::from_millis(1))
        .timeout(Some(Duration::from_secs(5)))
        .send()
        .unwrap_err();
    assert_absent(&error, "restore-run-error-secret");
}

// ---------------------------------------------------------------------------
// S3: injected event-delivery health detail
// ---------------------------------------------------------------------------

fn delivery_health_json() -> Value {
    let counts = json!({
        "total": 0,
        "pending": 0,
        "in_flight": 0,
        "succeeded": 0,
        "failed": 0,
        "dead": 0,
        "retryable": 0
    });
    let worker = json!({
        "workers_configured": 1,
        "batch_size": 10,
        "poll_interval_ms": 100,
        "lock_timeout_ms": 1000,
        "wakeups": {
            "notifications_sent": 0,
            "notification_wakeups": 0,
            "poll_wakeups": 0
        }
    });
    json!({
        "fanout": {
            "pending_events": 0,
            "in_flight_events": 0,
            "stale_claims": 0,
            "oldest_pending_age_seconds": null,
            "worker": worker
        },
        "delivery": {
            "counts": counts,
            "stale_claims": 0,
            "oldest_due_age_seconds": null,
            "worker": worker
        },
        "sinks": [{
            "sink_id": 1,
            "sink_name": "sink-one",
            "sink_kind": "webhook",
            "sink_enabled": true,
            "subscription_count": 1,
            "counts": counts,
            "stale_claims": 0,
            "oldest_due_age_seconds": null,
            "last_error": "health-last-error-secret"
        }],
        "subscriptions": []
    })
}

#[tokio::test]
async fn sink_delivery_health_debug_omits_last_error() {
    let transport = MockTransport::default();
    transport.push_response(json_response(StatusCode::OK, &delivery_health_json()));
    let client = async_client(transport);
    let health = client.event_deliveries().health().await.unwrap();
    let debug = format!("{health:?}");
    assert!(!debug.contains("health-last-error-secret"), "{debug}");
}
