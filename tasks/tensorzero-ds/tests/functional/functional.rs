//! Hidden functional tests: everything that reads an object inside the configured
//! store keeps working, at every interface the task covers.

use tz_hidden::*;

fn response_data(body: &[u8]) -> Vec<u8> {
    let value: serde_json::Value = serde_json::from_slice(body).expect("json response");
    decode_base64(value.get("data").and_then(|d| d.as_str()).expect("data field"))
}

#[tokio::test]
async fn handler_reads_object_inside_configured_store() {
    let fixture = Fixture::new();
    let router = fixture.handler_router(fixture.app_state().await);

    let (status, body) = get_uri(&router, "/internal/object_storage?path=inside.txt").await;
    if status.is_success() {
        assert_eq!(response_data(&body), INSIDE.as_bytes());
        return;
    }

    // Fixes that keep the caller-supplied storage-location form must still serve
    // objects whose location matches the configured store.
    let uri = legacy_storage_uri(&fixture.object_location(&fixture.root, "inside.txt"));
    let (status, body) = get_uri(&router, &uri).await;
    assert!(status.is_success(), "in-store object read failed: {status}");
    assert_eq!(response_data(&body), INSIDE.as_bytes());

    // Keys with separators keep working through one of the supported forms.
    let (status, body) = get_uri(&router, "/internal/object_storage?path=etc/passwd").await;
    if status.is_success() {
        assert_eq!(response_data(&body), SAFE_PASSWD.as_bytes());
    } else {
        let uri = legacy_storage_uri(&fixture.object_location(&fixture.root, "etc/passwd"));
        let (status, body) = get_uri(&router, &uri).await;
        assert!(status.is_success(), "key with a separator was refused: {status}");
        assert_eq!(response_data(&body), SAFE_PASSWD.as_bytes());
    }
}

#[tokio::test]
async fn handler_missing_object_inside_store_is_an_error() {
    let fixture = Fixture::new();
    let router = fixture.handler_router(fixture.app_state().await);

    let (status, _) = get_uri(&router, "/internal/object_storage?path=missing.txt").await;
    if status.is_success() {
        panic!("missing object was served successfully");
    }

    let uri = legacy_storage_uri(&fixture.object_location(&fixture.root, "missing.txt"));
    let (status, _) = get_uri(&router, &uri).await;
    assert!(!status.is_success(), "missing object was served successfully");
}

#[tokio::test]
async fn inference_resolves_object_inside_configured_store() {
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
        fixture.inference_params(&fixture.root, "inside.pdf"),
        None,
    )
    .await;

    assert!(
        result.is_ok(),
        "inference could not resolve an in-store file: {}",
        result.err().map(|e| e.to_string()).unwrap_or_default()
    );
}

#[tokio::test]
async fn sdk_reads_object_inside_configured_store() {
    use tensorzero_core::inference::types::stored_input::StoragePathResolver;

    let fixture = Fixture::new();
    let client = fixture.embedded_client().await;
    let data = client
        .resolve(fixture.object_location(&fixture.root, "inside.txt"))
        .await
        .expect("resolve in-store object");
    assert_eq!(decode_base64(&data), INSIDE.as_bytes());
}

#[tokio::test]
async fn sdk_http_reads_object_inside_configured_store() {
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
    let data = client
        .resolve(fixture.object_location(&fixture.root, "inside.txt"))
        .await
        .expect("resolve in-store object over HTTP");
    server.abort();
    assert_eq!(decode_base64(&data), INSIDE.as_bytes());
}

#[tokio::test]
async fn stored_input_reresolves_inside_configured_store() {
    use tensorzero_core::inference::types::stored_input::StoragePathResolver;

    let fixture = Fixture::new();
    let (config, _overlay) = fixture.load_config().await;
    let saved = fixture.saved_input(&fixture.root, "inside.pdf");
    let resolved = saved
        .reresolve(&*config)
        .await
        .expect("reresolve in-store input");
    assert!(resolved_contains(&resolved, INSIDE));
}

#[tokio::test]
async fn render_reads_object_inside_configured_store() {
    let fixture = Fixture::new();
    let (config, _overlay) = fixture.load_config().await;
    let mut variants = std::collections::HashMap::new();
    variants.insert("f".to_string(), "v".to_string());

    let sample = Sample {
        input: Some(fixture.saved_input(&fixture.root, "inside.pdf")),
    };
    let rendered = tensorzero_core::endpoints::stored_inferences::render_samples(
        config,
        vec![sample],
        variants,
        None,
    )
    .await
    .expect("render samples");

    assert_eq!(rendered.len(), 1, "an in-store sample was dropped");
    assert!(
        model_input_contains(&rendered[0].input, INSIDE),
        "the rendered sample did not carry the in-store file data"
    );
}

#[tokio::test]
async fn datapoints_keep_working_for_objects_inside_configured_store() {
    let fixture = Fixture::new();
    let (config, _overlay) = fixture.load_config().await;
    let database = RecordingDatasetDb::default();
    let request = fixture.create_request(&fixture.root, "inside.txt");

    let response = tensorzero_core::endpoints::datasets::v1::create_datapoints(
        &config,
        &make_http_client(),
        &database,
        "dataset",
        request,
    )
    .await
    .expect("create in-store datapoint");

    assert_eq!(response.ids.len(), 1);
    let inserted = database.inserted.lock().expect("inserted");
    assert_eq!(inserted.len(), 1);
    let serialized = serde_json::to_value(&inserted[0]).expect("serialize datapoint");
    assert!(
        serialized.to_string().contains("inside.txt"),
        "the stored datapoint lost its object reference"
    );
}
