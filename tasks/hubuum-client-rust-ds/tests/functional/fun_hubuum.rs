//! Hidden functional tests: legitimate use keeps working. These must pass on
//! the vulnerable code and on a correct fix, and they fail an over-broad fix
//! that removes useful diagnostics or changes stored values.

use std::sync::{Arc, Mutex};
use std::time::Duration;

use hubuum_client::{
    ApiError, Authenticated, BackupDocument, BaseUrl, Client, ExportRequest, ExportResult,
    ExportScope, ExportScopeKind, MockTransport, RequestPlan, RetryPolicy, Token,
    TransportResponse,
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

fn class_json(name: &str) -> Value {
    json!({
        "id": 42,
        "name": name,
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
    })
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
            "success_items": 1,
            "failed_items": 0
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

#[tokio::test]
async fn http_error_accessors_and_metadata_unchanged() {
    let transport = MockTransport::default();
    let body = r#"{"error":"Unauthorized","message":"accessor-message"}"#;
    transport.push_response(text_response(StatusCode::UNAUTHORIZED, "application/json", body));
    let client = async_client(transport);
    let error = client.classes().list().await.unwrap_err();

    assert_eq!(error.status(), Some(StatusCode::UNAUTHORIZED));
    assert_eq!(error.api_message(), Some("accessor-message"));
    assert_eq!(error.response_body(), Some(body));
    assert!(error.is_status(StatusCode::UNAUTHORIZED));
    assert!(
        error
            .request_url()
            .expect("request url accessor")
            .ends_with("/api/v1/classes")
    );
    let parsed = error.api_response().expect("structured error payload");
    assert_eq!(parsed.error, "Unauthorized");
    assert_eq!(parsed.message, "accessor-message");

    let display = error.to_string();
    assert!(display.contains("GET"), "{display}");
    assert!(display.contains("401"), "{display}");
    let debug = format!("{error:?}");
    assert!(debug.contains("401"), "{debug}");
}

#[tokio::test]
async fn valid_responses_decode_and_retries_still_work() {
    let transport = MockTransport::default();
    transport.push_response(json_response(StatusCode::OK, &json!([class_json("alpha")])));
    let client = async_client(transport);
    let classes = client.classes().list().await.unwrap();
    assert_eq!(classes.len(), 1);
    assert_eq!(classes[0].name, "alpha");

    let transport = MockTransport::default();
    transport.push_response(json_response(
        StatusCode::OK,
        &json!([{
            "id": "not-a-number",
            "name": "broken"
        }]),
    ));
    let client = async_client(transport);
    assert!(client.classes().list().await.is_err());
}

#[derive(Debug)]
struct FlakyTransport {
    calls: Arc<Mutex<usize>>,
    success: Value,
}

impl hubuum_client::AsyncTransport for FlakyTransport {
    fn execute<'a>(
        &'a self,
        _request: RequestPlan,
    ) -> std::pin::Pin<
        Box<dyn std::future::Future<Output = Result<TransportResponse, ApiError>> + Send + 'a>,
    > {
        Box::pin(async move {
            let mut calls = self.calls.lock().unwrap();
            *calls += 1;
            if *calls == 1 {
                Err(ApiError::Transport("temporary failure".to_string()))
            } else {
                TransportResponse::json(StatusCode::OK, &self.success)
            }
        })
    }
}

#[tokio::test]
async fn replay_safe_requests_still_retry() {
    let calls = Arc::new(Mutex::new(0));
    let client = Client::builder(BaseUrl::new("https://example.invalid").unwrap())
        .with_transport(Arc::new(FlakyTransport {
            calls: calls.clone(),
            success: json!([class_json("retried")]),
        }))
        .retry_policy(RetryPolicy {
            max_attempts: 2,
            initial_delay: Duration::ZERO,
            max_delay: Duration::ZERO,
        })
        .build()
        .unwrap()
        .authenticate(Token::new("consumer-secret"));
    let classes = client.classes().list().await.unwrap();
    assert_eq!(classes[0].name, "retried");
    assert_eq!(*calls.lock().unwrap(), 2);
}

#[tokio::test]
async fn runner_error_keeps_task_identity_and_status() {
    let transport = MockTransport::default();
    transport.push_response(json_response(
        StatusCode::ACCEPTED,
        &task_json(11, "queued", None),
    ));
    transport.push_response(json_response(
        StatusCode::OK,
        &task_json(11, "failed", Some("runner-coupled-secret")),
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

    for text in [error.to_string(), format!("{error:?}")] {
        assert!(text.contains("11"), "task identity missing: {text}");
        assert!(
            text.to_lowercase().contains("failed"),
            "task status missing: {text}"
        );
    }
}

#[tokio::test]
async fn task_and_event_values_remain_readable() {
    let transport = MockTransport::default();
    transport.push_response(json_response(
        StatusCode::OK,
        &task_json(11, "succeeded", Some("kept-summary")),
    ));
    let client = async_client(transport);
    let task = client.tasks().get(11).await.unwrap();
    assert_eq!(task.summary.as_deref(), Some("kept-summary"));
    assert_eq!(task.progress.total_items, 1);
    let value = serde_json::to_value(&task).unwrap();
    assert_eq!(value["summary"], "kept-summary");
    assert_eq!(value["status"], "succeeded");
    let debug = format!("{task:?}");
    assert!(debug.contains("11"), "{debug}");
    assert!(debug.to_lowercase().contains("succeeded"), "{debug}");

    let transport = MockTransport::default();
    transport.push_response(json_response(
        StatusCode::OK,
        &json!([{
            "id": 7,
            "task_id": 11,
            "event_type": "failed",
            "message": "kept-message",
            "data": {"token": "kept-data"},
            "created_at": "2026-07-23T08:00:00Z"
        }]),
    ));
    let client = async_client(transport);
    let events = client.tasks().events(11).list().await.unwrap();
    assert_eq!(events.len(), 1);
    assert_eq!(events[0].message, "kept-message");
    assert_eq!(events[0].data.as_ref().unwrap()["token"], "kept-data");
    let debug = format!("{events:?}");
    assert!(debug.contains("7"), "{debug}");
    assert!(debug.contains("failed"), "{debug}");
}

#[tokio::test]
async fn event_sink_and_delivery_values_remain_readable() {
    let transport = MockTransport::default();
    transport.push_response(json_response(
        StatusCode::OK,
        &json!({
            "id": 1,
            "name": "sink-one",
            "kind": "webhook",
            "config": {"url": "https://example.invalid/hook", "token": "kept-config"},
            "enabled": true,
            "secret_ref": "kept-ref",
            "created_at": "2026-07-23T08:00:00Z",
            "updated_at": "2026-07-23T08:00:00Z"
        }),
    ));
    let client = async_client(transport);
    let sink = client.event_sinks().get(1).await.unwrap().into_inner();
    assert_eq!(sink.config["token"], "kept-config");
    assert_eq!(sink.secret_ref.as_deref(), Some("kept-ref"));
    assert_eq!(sink.name, "sink-one");
    let debug = format!("{sink:?}");
    assert!(debug.contains("sink-one"), "{debug}");
    assert!(debug.contains('1'), "{debug}");

    let transport = MockTransport::default();
    transport.push_response(json_response(
        StatusCode::OK,
        &json!({
            "id": 41,
            "event_id": 42,
            "subscription_id": 43,
            "status": "failed",
            "attempts": 2,
            "next_attempt_at": "2026-07-23T08:00:01Z",
            "claim_token": "kept-claim",
            "last_error": "kept-delivery-error",
            "locked_until": "2026-07-23T08:01:00Z",
            "created_at": "2026-07-23T07:59:00Z",
            "updated_at": "2026-07-23T08:00:00Z"
        }),
    ));
    let client = async_client(transport);
    let delivery = client.event_deliveries().get(41).await.unwrap();
    assert_eq!(delivery.claim_token.as_deref(), Some("kept-claim"));
    assert_eq!(delivery.last_error.as_deref(), Some("kept-delivery-error"));
    let value = serde_json::to_value(&delivery).unwrap();
    assert_eq!(value["claim_token"], "kept-claim");
    let debug = format!("{delivery:?}");
    assert!(debug.contains("41"), "{debug}");
    assert!(debug.to_lowercase().contains("failed"), "{debug}");
}

#[tokio::test]
async fn export_and_import_values_remain_readable() {
    let transport = MockTransport::default();
    transport.push_response(text_response(StatusCode::OK, "text/csv", "kept-export-body"));
    let client = async_client(transport);
    match client.exports().output(11).await.unwrap() {
        ExportResult::Rendered { content_type, body } => {
            assert_eq!(content_type.to_string(), "text/csv");
            assert_eq!(body, "kept-export-body");
        }
        other => panic!("expected rendered export, got {other:?}"),
    }

    let transport = MockTransport::default();
    transport.push_response(json_response(
        StatusCode::OK,
        &json!({
            "items": [{"secret": "kept-item"}],
            "meta": {
                "content_type": "application/json",
                "count": 1,
                "scope": {"class_id": null, "kind": "collections", "object_id": null},
                "truncated": false
            },
            "warnings": [{"code": "w", "message": "kept-warning", "path": null}]
        }),
    ));
    let client = async_client(transport);
    match client.exports().output(11).await.unwrap() {
        ExportResult::Json(response) => {
            assert_eq!(response.items[0]["secret"], "kept-item");
            assert_eq!(response.warnings[0].message, "kept-warning");
            let debug = format!("{response:?}");
            assert!(debug.contains('1'), "{debug}");
            let value = serde_json::to_value(&response).unwrap();
            assert_eq!(value["items"][0]["secret"], "kept-item");
        }
        other => panic!("expected JSON export, got {other:?}"),
    }

    let transport = MockTransport::default();
    transport.push_response(json_response(
        StatusCode::OK,
        &json!([{
            "id": 9,
            "task_id": 11,
            "item_ref": "kept-ref",
            "entity_kind": "object",
            "action": "create",
            "identifier": "kept-identifier",
            "outcome": "failed",
            "error": "kept-import-error",
            "details": {"token": "kept-import-details"},
            "created_at": "2026-07-23T08:00:00Z"
        }]),
    ));
    let client = async_client(transport);
    let results = client.imports().results(11).list().await.unwrap();
    assert_eq!(results[0].error.as_deref(), Some("kept-import-error"));
    assert_eq!(
        results[0].details.as_ref().unwrap()["token"],
        "kept-import-details"
    );
    let debug = format!("{results:?}");
    assert!(debug.contains('9'), "{debug}");
    assert!(debug.contains("failed"), "{debug}");
}

#[test]
fn blocking_client_legitimate_flow() {
    let transport = MockTransport::default();
    transport.push_response(json_response(StatusCode::OK, &json!([class_json("blocking")])));
    let client = blocking_client(transport);
    let classes = client.classes().list().unwrap();
    assert_eq!(classes[0].name, "blocking");

    let transport = MockTransport::default();
    transport.push_response(json_response(
        StatusCode::ACCEPTED,
        &task_json(11, "queued", None),
    ));
    transport.push_response(json_response(
        StatusCode::OK,
        &task_json(11, "succeeded", Some("done")),
    ));
    transport.push_response(text_response(StatusCode::OK, "text/csv", "blocking-export"));
    let client = blocking_client(transport);
    match client
        .exports()
        .run(export_request())
        .poll_interval(Duration::from_millis(1))
        .timeout(Some(Duration::from_secs(5)))
        .send()
        .unwrap()
    {
        ExportResult::Rendered { body, .. } => assert_eq!(body, "blocking-export"),
        other => panic!("expected rendered export, got {other:?}"),
    }
}

#[tokio::test]
async fn restore_stage_and_run_flows_work() {
    let transport = MockTransport::default();
    transport.push_response(json_response(
        StatusCode::OK,
        &restore_stage_json("validated", None, Some("capability-value")),
    ));
    let client = async_client(transport);
    let staged = client.restores().stage(&backup_document()).await.unwrap();
    assert!(staged.error.is_none());
    assert_eq!(
        staged
            .restore_capability
            .as_ref()
            .map(|capability| capability.as_str()),
        Some("capability-value")
    );
    let debug = format!("{staged:?}");
    assert!(debug.contains('5'), "{debug}");

    let transport = MockTransport::default();
    transport.push_response(json_response(
        StatusCode::OK,
        &restore_stage_json("validated", None, Some("capability-value")),
    ));
    transport.push_response(json_response(
        StatusCode::OK,
        &restore_stage_json("succeeded", None, None),
    ));
    let client = async_client(transport);
    let finished = client
        .restores()
        .run(&backup_document())
        .poll_interval(Duration::from_millis(1))
        .timeout(Some(Duration::from_secs(5)))
        .send()
        .await
        .unwrap();
    assert!(finished.status.is_terminal());
    assert!(finished.error.is_none());
}

#[test]
fn restore_run_blocking_flow_works() {
    let transport = MockTransport::default();
    transport.push_response(json_response(
        StatusCode::OK,
        &restore_stage_json("validated", None, Some("capability-value")),
    ));
    transport.push_response(json_response(
        StatusCode::OK,
        &restore_stage_json("succeeded", None, None),
    ));
    let client = blocking_client(transport);
    let finished = client
        .restores()
        .run(&backup_document())
        .poll_interval(Duration::from_millis(1))
        .timeout(Some(Duration::from_secs(5)))
        .send()
        .unwrap();
    assert!(finished.status.is_terminal());
}

#[tokio::test]
async fn audit_and_history_values_remain_readable() {
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
            "summary": "kept-audit-summary",
            "before": {"token": "kept-before"},
            "after": {"token": "kept-after"},
            "metadata": {"token": "kept-metadata"},
            "schema_version": 1
        }]),
    ));
    let client = async_client(transport);
    let events = client.events().list().await.unwrap();
    assert_eq!(events[0].summary, "kept-audit-summary");
    assert_eq!(events[0].after.as_ref().unwrap()["token"], "kept-after");
    assert_eq!(events[0].metadata["token"], "kept-metadata");
    let debug = format!("{events:?}");
    assert!(debug.contains("history-object"), "{debug}");
    assert!(debug.contains("updated"), "{debug}");

    let transport = MockTransport::default();
    transport.push_response(json_response(
        StatusCode::OK,
        &json!([{
            "id": 9,
            "name": "history-object",
            "collection_id": 7,
            "hubuum_class_id": 42,
            "data": {"token": "kept-history-data"},
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
    assert_eq!(history[0].data["token"], "kept-history-data");
    let debug = format!("{history:?}");
    assert!(debug.contains("history-object"), "{debug}");
}

#[tokio::test]
async fn event_delivery_health_values_remain_readable() {
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
    let transport = MockTransport::default();
    transport.push_response(json_response(
        StatusCode::OK,
        &json!({
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
                "last_error": "kept-health-error"
            }],
            "subscriptions": []
        }),
    ));
    let client = async_client(transport);
    let health = client.event_deliveries().health().await.unwrap();
    assert_eq!(health.sinks[0].sink_name, "sink-one");
    assert_eq!(health.sinks[0].last_error.as_deref(), Some("kept-health-error"));
    let debug = format!("{health:?}");
    assert!(debug.contains("sink-one"), "{debug}");
}
