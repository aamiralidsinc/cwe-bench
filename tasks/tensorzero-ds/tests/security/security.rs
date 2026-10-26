//! Hidden security tests: a caller-supplied storage location must never make the
//! product read outside the configured object store.

use std::time::Duration;

use base64::Engine;
use tz_hidden::*;

/// Point the S3 SDK at a local listener and report whether it was contacted.
async fn watch_for_s3_contact() -> (
    String,
    std::sync::Arc<std::sync::atomic::AtomicBool>,
    tokio::task::JoinHandle<()>,
) {
    std::env::set_var("AWS_ACCESS_KEY_ID", "test-key");
    std::env::set_var("AWS_SECRET_ACCESS_KEY", "test-secret");
    std::env::set_var("AWS_EC2_METADATA_DISABLED", "true");
    std::env::set_var("AWS_REGION", "us-east-1");

    let listener = tokio::net::TcpListener::bind("127.0.0.1:0")
        .await
        .expect("listener");
    let address = listener.local_addr().expect("address");
    let contacted = std::sync::Arc::new(std::sync::atomic::AtomicBool::new(false));
    let contacted_in_task = contacted.clone();
    let handle = tokio::spawn(async move {
        if let Ok(Ok(_)) = tokio::time::timeout(Duration::from_secs(20), listener.accept()).await {
            contacted_in_task.store(true, std::sync::atomic::Ordering::SeqCst);
        }
    });
    (format!("http://{address}"), contacted, handle)
}

fn caller_s3_location(endpoint: &str) -> tensorzero_core::inference::types::storage::StoragePath {
    tensorzero_core::inference::types::storage::StoragePath {
        kind: tensorzero_core::inference::types::storage::StorageKind::S3Compatible {
            bucket_name: Some("bucket".to_string()),
            region: Some("us-east-1".to_string()),
            endpoint: Some(endpoint.to_string()),
            allow_http: Some(true),
            prefix: String::new(),
        },
        path: object_store::path::Path::parse("secret.txt").expect("path"),
    }
}

#[tokio::test]
async fn handler_blocks_caller_chosen_store() {
    let fixture = Fixture::new();
    let router = fixture.handler_router(fixture.app_state().await);

    // 1. The reported caller-chosen filesystem root must not be served.
    let uri = legacy_storage_uri(&fixture.object_location(&fixture.outside, "secret.txt"));
    let (status, body) = get_uri(&router, &uri).await;
    assert!(
        !status.is_success(),
        "caller-chosen storage root was served with {status}"
    );
    assert!(
        !body_contains_marker(&body, OUTSIDE),
        "response carried bytes from outside the configured store: {}",
        String::from_utf8_lossy(&body)
    );

    // 2. Key-only forms must stay inside the configured root whenever they are accepted.
    let (_, body) = get_uri(&router, "/internal/object_storage?path=../outside/secret.txt").await;
    assert!(
        !body_contains_marker(&body, OUTSIDE),
        "key with parent segments escaped the configured store"
    );

    // 3. An absolute-looking key must resolve under the configured prefix, never on
    //    the host filesystem.
    let (status, body) = get_uri(&router, "/internal/object_storage?path=/etc/passwd").await;
    assert!(
        !String::from_utf8_lossy(&body).contains(HOST_PASSWD_CANARY),
        "absolute-looking key reached the host filesystem: {}",
        String::from_utf8_lossy(&body)
    );
    if status.is_success() {
        let value: serde_json::Value = serde_json::from_slice(&body).expect("json response");
        let decoded = decode_base64(value.get("data").and_then(|d| d.as_str()).unwrap_or_default());
        assert_eq!(
            String::from_utf8_lossy(&decoded),
            SAFE_PASSWD,
            "absolute-looking key was not confined to the configured store"
        );
    }
}

#[tokio::test]
async fn handler_blocks_caller_chosen_s3_endpoint() {
    let fixture = Fixture::new();
    let router = fixture.handler_router(fixture.app_state().await);
    let (endpoint, contacted, watcher) = watch_for_s3_contact().await;

    let uri = legacy_storage_uri(&caller_s3_location(&endpoint));
    let (status, body) = get_uri(&router, &uri).await;
    tokio::time::sleep(Duration::from_millis(300)).await;

    assert!(
        !contacted.load(std::sync::atomic::Ordering::SeqCst),
        "the gateway contacted a caller-chosen S3 endpoint"
    );
    assert!(
        !status.is_success(),
        "caller-chosen S3 endpoint was served successfully"
    );
    assert!(
        !body_contains_marker(&body, OUTSIDE),
        "response carried bytes obtained through a caller-chosen endpoint"
    );
    watcher.abort();
}

#[tokio::test]
async fn inference_blocks_caller_chosen_store() {
    let fixture = Fixture::new();
    let state = fixture.app_state().await;

    let result = tensorzero_core::endpoints::inference::inference(
        state.config.clone(),
        &state.http_client,
        state.clickhouse_connection_info.clone(),
        state.postgres_connection_info.clone(),
        state.cache_manager.clone(),
        state.deferred_tasks.clone(),
        state.rate_limiting_manager.clone(),
        state.primary_datastore,
        fixture.inference_params(&fixture.outside, "secret.pdf"),
        None,
    )
    .await;

    assert!(
        result.is_err(),
        "an inference request naming a location outside the configured store succeeded"
    );
}

#[tokio::test]
async fn inference_blocks_caller_chosen_s3_endpoint() {
    let fixture = Fixture::new();
    let state = fixture.app_state().await;
    let (endpoint, contacted, watcher) = watch_for_s3_contact().await;

    let params = {
        let value = serde_json::json!({
            "function_name": "f",
            "dryrun": true,
            "input": {"messages": [{"role": "user", "content": [{
                "type": "file",
                "file_type": "object_storage_pointer",
                "mime_type": "application/pdf",
                "storage_path": {
                    "kind": {
                        "type": "s3_compatible",
                        "bucket_name": "bucket",
                        "region": "us-east-1",
                        "endpoint": endpoint,
                        "allow_http": true,
                    },
                    "path": "secret.txt",
                }
            }]}]}
        });
        serde_json::from_value(value).expect("inference params")
    };

    let result = tensorzero_core::endpoints::inference::inference(
        state.config.clone(),
        &state.http_client,
        state.clickhouse_connection_info.clone(),
        state.postgres_connection_info.clone(),
        state.cache_manager.clone(),
        state.deferred_tasks.clone(),
        state.rate_limiting_manager.clone(),
        state.primary_datastore,
        params,
        None,
    )
    .await;
    tokio::time::sleep(Duration::from_millis(300)).await;

    assert!(
        !contacted.load(std::sync::atomic::Ordering::SeqCst),
        "inference contacted a caller-chosen S3 endpoint"
    );
    assert!(
        result.is_err(),
        "an inference request naming a caller-chosen endpoint succeeded"
    );
    watcher.abort();
}

#[tokio::test]
async fn sdk_blocks_caller_chosen_store() {
    use tensorzero_core::inference::types::stored_input::StoragePathResolver;

    let fixture = Fixture::new();
    let client = fixture.embedded_client().await;
    let storage_path = fixture.object_location(&fixture.outside, "secret.txt");

    match client.resolve(storage_path).await {
        Err(_) => {}
        Ok(data) => {
            let decoded = String::from_utf8_lossy(&decode_base64(&data)).into_owned();
            assert!(
                !decoded.contains(OUTSIDE),
                "the SDK returned bytes from outside the configured store"
            );
            panic!("the SDK resolved a storage location outside the configured store");
        }
    }
}

#[tokio::test]
async fn sdk_http_blocks_caller_chosen_store() {
    use tensorzero_core::inference::types::stored_input::StoragePathResolver;

    let fixture = Fixture::new();
    let router = fixture.handler_router(fixture.app_state().await);
    let (url, server) = serve_gateway(router).await;
    let client = tensorzero_core::client::ClientBuilder::new(
        tensorzero_core::client::ClientBuilderMode::HTTPGateway {
            url: url::Url::parse(&url).expect("url"),
        },
    )
    .build()
    .await
    .expect("http client");

    let result = client
        .resolve(fixture.object_location(&fixture.outside, "secret.txt"))
        .await;
    server.abort();

    match result {
        Err(_) => {}
        Ok(data) => {
            let decoded = String::from_utf8_lossy(&decode_base64(&data)).into_owned();
            assert!(
                !decoded.contains(OUTSIDE),
                "the HTTP SDK returned bytes from outside the configured store"
            );
            panic!("the HTTP SDK resolved a storage location outside the configured store");
        }
    }
}

#[tokio::test]
async fn stored_input_blocks_caller_chosen_store() {
    use tensorzero_core::inference::types::stored_input::StoragePathResolver;

    let fixture = Fixture::new();
    let (config, _overlay) = fixture.load_config().await;
    let saved = fixture.saved_input(&fixture.outside, "secret.pdf");

    match saved.reresolve(&*config).await {
        Err(_) => {}
        Ok(resolved) => {
            assert!(
                !resolved_contains(&resolved, OUTSIDE),
                "a saved input resolved bytes from outside the configured store"
            );
            panic!("a saved input resolved a location outside the configured store");
        }
    }
}

#[tokio::test]
async fn render_blocks_caller_chosen_store() {
    let fixture = Fixture::new();
    let (config, _overlay) = fixture.load_config().await;
    let mut variants = std::collections::HashMap::new();
    variants.insert("f".to_string(), "v".to_string());

    let sample = Sample {
        input: Some(fixture.saved_input(&fixture.outside, "secret.pdf")),
    };
    match tensorzero_core::endpoints::stored_inferences::render_samples(
        config,
        vec![sample],
        variants,
        None,
    )
    .await
    {
        Err(_) => {}
        Ok(rendered) => {
            for sample in &rendered {
                assert!(
                    !model_input_contains(&sample.input, OUTSIDE),
                    "a rendered sample carried bytes from outside the configured store"
                );
            }
        }
    }
}

#[tokio::test]
async fn datapoint_create_does_not_read_caller_chosen_store() {
    let fixture = Fixture::new();
    let (config, _overlay) = fixture.load_config().await;
    let database = RecordingDatasetDb::default();
    let request = fixture.create_request(&fixture.outside, "secret.txt");

    let result = tensorzero_core::endpoints::datasets::v1::create_datapoints(
        &config,
        &make_http_client(),
        &database,
        "dataset",
        request,
    )
    .await;

    // The create path fingerprints referenced files. A fingerprint of the outside
    // file proves the object was read.
    let outside_payload = base64::engine::general_purpose::STANDARD.encode(OUTSIDE.as_bytes());
    let outside_fingerprint = fingerprint_of_base64(&outside_payload);
    let leaked = result.is_ok()
        && database
            .inserted_tags()
            .iter()
            .any(|tags| tags.values().any(|value| value.contains(&outside_fingerprint)));
    assert!(
        !leaked,
        "creating a datapoint read an object outside the configured store"
    );
}
