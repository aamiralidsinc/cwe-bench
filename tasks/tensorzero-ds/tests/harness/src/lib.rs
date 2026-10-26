//! Shared helpers for the hidden object-storage tests.
//!
//! Everything a test needs to drive the product's real interfaces lives here:
//! a temporary configured filesystem object store, a private directory outside
//! it, and the small amount of plumbing each entry point needs.

use std::collections::HashMap;
use std::sync::{Arc, Mutex};

use axum::Router;
use axum::body::Body;
use axum::routing::get;
use base64::Engine;
use http::{Request, StatusCode};
use tensorzero_core::client::{Client, ClientBuilder, ClientBuilderMode};
use tensorzero_core::config::{Config, ConfigFileGlob, RuntimeOverlay};
use tensorzero_core::db::clickhouse::ClickHouseConnectionInfo;
use tensorzero_core::db::datasets::{DatasetQueries, GetDatapointParams, GetDatasetMetadataParams, GetDatapointsParams};
use tensorzero_core::db::delegating_connection::PrimaryDatastore;
use tensorzero_core::db::postgres::PostgresConnectionInfo;
use tensorzero_core::db::stored_datapoint::StoredDatapoint;
use tensorzero_core::db::valkey::ValkeyConnectionInfo;
use tensorzero_core::endpoints::object_storage::get_object_handler;
use tensorzero_core::http::TensorzeroHttpClient;
use tensorzero_core::inference::types::storage::{StorageKind, StoragePath};
use tensorzero_core::inference::types::{FunctionType, ModelInput, ResolvedInput, ResolvedInputMessageContent, ResolvedContentBlock};
use tensorzero_core::stored_inference::{SimpleStoredSampleInfo, StoredSample};
use tensorzero_core::utils::gateway::AppStateData;
use tower::ServiceExt;
use uuid::Uuid;

pub const INSIDE: &str = "INSIDE-OBJECT-CONTENT-0123456789";
pub const OUTSIDE: &str = "TOP-SECRET-OUTSIDE-0123456789";
pub const SAFE_PASSWD: &str = "root:x:safe-in-store-fixture";
pub const HOST_PASSWD_CANARY: &str = "root:x:0:0";

pub struct Fixture {
    pub dir: tempfile::TempDir,
    pub root: std::path::PathBuf,
    pub outside: std::path::PathBuf,
}

impl Fixture {
    pub fn new() -> Self {
        let dir = tempfile::tempdir().expect("temp dir");
        let root = dir.path().join("store");
        let outside = dir.path().join("outside");
        std::fs::create_dir_all(&root).expect("store dir");
        std::fs::create_dir_all(&outside).expect("outside dir");
        std::fs::write(root.join("inside.txt"), INSIDE.as_bytes()).expect("inside file");
        std::fs::write(root.join("inside.pdf"), INSIDE.as_bytes()).expect("inside pdf");
        std::fs::create_dir_all(root.join("etc")).expect("etc dir");
        std::fs::write(root.join("etc").join("passwd"), SAFE_PASSWD.as_bytes()).expect("safe passwd");
        std::fs::write(outside.join("secret.txt"), OUTSIDE.as_bytes()).expect("outside file");
        std::fs::write(outside.join("secret.pdf"), OUTSIDE.as_bytes()).expect("outside pdf");
        Self { dir, root, outside }
    }

    pub fn config_toml(&self) -> String {
        format!(
            r#"
[gateway]
disable_pseudonymous_usage_analytics = true

[object_storage]
type = "filesystem"
path = "{root}"

[functions.f]
type = "chat"

[functions.f.experimentation]
type = "static"
candidate_variants = {{ v = 1.0 }}

[functions.f.variants.v]
type = "chat_completion"
model = "m"

[models.m]
routing = ["d"]

[models.m.providers.d]
type = "dummy"
model_name = "require_pdf"
"#,
            root = self.root.to_string_lossy()
        )
    }

    pub async fn load_config(&self) -> (Arc<Config>, Arc<RuntimeOverlay>) {
        let path = self.dir.path().join("tensorzero.toml");
        std::fs::write(&path, self.config_toml()).expect("write config");
        let glob = ConfigFileGlob::new_from_path(&path).expect("glob");
        let unwritten = Config::load_from_path_optional_verify_credentials(&glob, false)
            .await
            .expect("load config");
        let overlay = Arc::new(unwritten.runtime_overlay().clone());
        (
            Arc::new(unwritten.dangerous_into_config_without_writing()),
            overlay,
        )
    }

    pub async fn app_state(&self) -> AppStateData {
        let (config, overlay) = self.load_config().await;
        self.app_state_with(config, overlay)
    }

    pub fn app_state_with(&self, config: Arc<Config>, overlay: Arc<RuntimeOverlay>) -> AppStateData {
        AppStateData::new_for_snapshot(
            config,
            overlay,
            make_http_client(),
            ClickHouseConnectionInfo::new_disabled(),
            PostgresConnectionInfo::new_disabled(),
            ValkeyConnectionInfo::new_disabled(),
            ValkeyConnectionInfo::new_disabled(),
            tokio_util::task::TaskTracker::new(),
            tokio_util::sync::CancellationToken::new(),
            PrimaryDatastore::Disabled,
        )
        .expect("app state")
    }

    pub fn handler_router(&self, state: AppStateData) -> Router {
        Router::new()
            .route("/internal/object_storage", get(get_object_handler))
            .with_state(state)
    }

    pub fn file_pointer(&self, kind_root: &std::path::Path, key: &str, mime: &str) -> serde_json::Value {
        serde_json::json!({
            "type": "file",
            "file_type": "object_storage_pointer",
            "mime_type": mime,
            "storage_path": {
                "kind": {"type": "filesystem", "path": kind_root.to_string_lossy()},
                "path": key,
            }
        })
    }

    pub fn inference_params(&self, kind_root: &std::path::Path, key: &str) -> tensorzero_core::endpoints::inference::Params {
        let value = serde_json::json!({
            "function_name": "f",
            "dryrun": true,
            "input": {"messages": [{"role": "user", "content": [
                self.file_pointer(kind_root, key, "application/pdf"),
            ]}]}
        });
        serde_json::from_value(value).expect("inference params")
    }

    pub fn saved_input(&self, kind_root: &std::path::Path, key: &str) -> tensorzero_core::inference::types::StoredInput {
        let value = serde_json::json!({
            "messages": [{"role": "user", "content": [{
                "type": "file",
                "mime_type": "application/pdf",
                "storage_path": {
                    "kind": {"type": "filesystem", "path": kind_root.to_string_lossy()},
                    "path": key,
                }
            }]}]
        });
        serde_json::from_value(value).expect("stored input")
    }

    pub fn create_request(&self, kind_root: &std::path::Path, key: &str) -> tensorzero_core::endpoints::datasets::v1::types::CreateDatapointsRequest {
        let value = serde_json::json!({
            "datapoints": [{
                "type": "chat",
                "function_name": "f",
                "input": {"messages": [{"role": "user", "content": [
                    self.file_pointer(kind_root, key, "application/pdf"),
                ]}]}
            }]
        });
        serde_json::from_value(value).expect("create request")
    }

    pub async fn embedded_client(&self) -> Client {
        let (config, overlay) = self.load_config().await;
        ClientBuilder::new(ClientBuilderMode::FromComponents {
            config,
            runtime_overlay: overlay,
            clickhouse_connection_info: ClickHouseConnectionInfo::new_disabled(),
            postgres_connection_info: PostgresConnectionInfo::new_disabled(),
            valkey_connection_info: ValkeyConnectionInfo::new_disabled(),
            valkey_cache_connection_info: ValkeyConnectionInfo::new_disabled(),
            http_client: make_http_client(),
            timeout: None,
        })
        .build()
        .await
        .expect("embedded client")
    }

    pub fn object_location(&self, kind_root: &std::path::Path, key: &str) -> StoragePath {
        StoragePath {
            kind: StorageKind::Filesystem {
                path: kind_root.to_string_lossy().into_owned(),
            },
            path: object_store::path::Path::parse(key).expect("path"),
        }
    }
}

pub fn make_http_client() -> TensorzeroHttpClient {
    TensorzeroHttpClient::new(tensorzero_core::http::DEFAULT_HTTP_CLIENT_TIMEOUT, None)
        .expect("http client")
}

/// Serve a product router on an ephemeral loopback port and return its base URL.
pub async fn serve_gateway(router: Router) -> (String, tokio::task::JoinHandle<()>) {
    let listener = tokio::net::TcpListener::bind("127.0.0.1:0")
        .await
        .expect("bind gateway");
    let address = listener.local_addr().expect("gateway address");
    let handle = tokio::spawn(async move {
        let _ = axum::serve(listener, router).await;
    });
    (format!("http://{address}/"), handle)
}

pub fn urlencode(value: &str) -> String {
    let mut out = String::new();
    for b in value.bytes() {
        match b {
            b'A'..=b'Z' | b'a'..=b'z' | b'0'..=b'9' | b'-' | b'_' | b'.' | b'~' => out.push(b as char),
            _ => out.push_str(&format!("%{:02X}", b)),
        }
    }
    out
}

pub async fn get_uri(router: &Router, uri: &str) -> (StatusCode, Vec<u8>) {
    let response = router
        .clone()
        .oneshot(Request::builder().uri(uri).body(Body::empty()).expect("request"))
        .await
        .expect("response");
    let status = response.status();
    let body = axum::body::to_bytes(response.into_body(), 8 * 1024 * 1024)
        .await
        .expect("body");
    (status, body.to_vec())
}

/// Build the legacy caller-supplied storage-location query used by the API.
pub fn legacy_storage_uri(storage_path: &StoragePath) -> String {
    format!(
        "/internal/object_storage?storage_path={}",
        urlencode(&serde_json::to_string(storage_path).expect("serialize path"))
    )
}

pub fn decode_base64(value: &str) -> Vec<u8> {
    base64::engine::general_purpose::STANDARD
        .decode(value)
        .unwrap_or_default()
}

/// True if any base64 file payload in a resolved input carries the marker.
pub fn resolved_contains(input: &ResolvedInput, marker: &str) -> bool {
    input.messages.iter().flat_map(|m| m.content.iter()).any(|content| match content {
        ResolvedInputMessageContent::File(file) => {
            String::from_utf8_lossy(&decode_base64(&file.data)).contains(marker)
        }
        _ => false,
    })
}

pub fn model_input_contains(input: &ModelInput, marker: &str) -> bool {
    input.messages.iter().flat_map(|m| m.content.iter()).any(|content| match content {
        ResolvedContentBlock::File(file) => {
            String::from_utf8_lossy(&decode_base64(&file.data)).contains(marker)
        }
        _ => false,
    })
}

pub fn body_contains_marker(body: &[u8], marker: &str) -> bool {
    let text = String::from_utf8_lossy(body);
    if text.contains(marker) {
        return true;
    }
    // Object bytes travel base64-encoded; try decoding every long string field.
    if let Ok(value) = serde_json::from_slice::<serde_json::Value>(body) {
        if let Some(data) = value.get("data").and_then(|d| d.as_str()) {
            return String::from_utf8_lossy(&decode_base64(data)).contains(marker);
        }
    }
    false
}

pub fn fingerprint_of_base64(data: &str) -> String {
    hex_encode(blake3::hash(data.as_bytes()).as_bytes())
}

fn hex_encode(bytes: &[u8]) -> String {
    let mut out = String::with_capacity(bytes.len() * 2);
    for b in bytes {
        out.push_str(&format!("{b:02x}"));
    }
    out
}

/// A minimal `StoredSample` used to drive sample rendering.
pub struct Sample {
    pub input: Option<tensorzero_core::inference::types::StoredInput>,
}

impl StoredSample for Sample {
    fn function_name(&self) -> &str {
        "f"
    }
    fn into_input(self) -> Option<tensorzero_core::inference::types::StoredInput> {
        self.input
    }
    fn input(&self) -> Option<&tensorzero_core::inference::types::StoredInput> {
        self.input.as_ref()
    }
    fn input_mut(&mut self) -> Option<&mut tensorzero_core::inference::types::StoredInput> {
        self.input.as_mut()
    }
    fn owned_simple_info(self) -> SimpleStoredSampleInfo {
        SimpleStoredSampleInfo {
            function_name: "f".to_string(),
            function_type: FunctionType::Chat,
            input: self.input,
            episode_id: Some(Uuid::nil()),
            inference_id: Some(Uuid::nil()),
            output: Some(vec![]),
            stored_output: None,
            dispreferred_outputs: vec![],
            tool_params: None,
            output_schema: None,
            tags: HashMap::new(),
        }
    }
}

/// Recording stand-in for the dataset tables. Only insertion is used.
#[derive(Default)]
pub struct RecordingDatasetDb {
    pub inserted: Mutex<Vec<StoredDatapoint>>,
}

impl RecordingDatasetDb {
    pub fn inserted_tags(&self) -> Vec<HashMap<String, String>> {
        let inserted = self.inserted.lock().expect("inserted");
        inserted
            .iter()
            .map(|datapoint| match datapoint {
                StoredDatapoint::Chat(datapoint) => datapoint.tags.clone().unwrap_or_default(),
                StoredDatapoint::Json(datapoint) => datapoint.tags.clone().unwrap_or_default(),
            })
            .collect()
    }
}

#[async_trait::async_trait]
impl DatasetQueries for RecordingDatasetDb {
    async fn get_dataset_metadata(
        &self,
        _params: &GetDatasetMetadataParams,
    ) -> Result<Vec<tensorzero_core::db::datasets::DatasetMetadata>, tensorzero_core::error::Error> {
        Ok(vec![])
    }

    async fn insert_datapoints(
        &self,
        datapoints: &[StoredDatapoint],
    ) -> Result<u64, tensorzero_core::error::Error> {
        self.inserted.lock().expect("inserted").extend_from_slice(datapoints);
        Ok(datapoints.len() as u64)
    }

    async fn count_datapoints_for_dataset(
        &self,
        _dataset_name: &str,
        _function_name: Option<&str>,
    ) -> Result<u64, tensorzero_core::error::Error> {
        Ok(0)
    }

    async fn get_datapoint(
        &self,
        _params: &GetDatapointParams,
    ) -> Result<StoredDatapoint, tensorzero_core::error::Error> {
        Err(tensorzero_core::error::Error::new(
            tensorzero_core::error::ErrorDetails::DatapointNotFound {
                dataset_name: String::new(),
                datapoint_id: Uuid::nil(),
            },
        ))
    }

    async fn get_datapoints(
        &self,
        _params: &GetDatapointsParams,
    ) -> Result<Vec<StoredDatapoint>, tensorzero_core::error::Error> {
        Ok(vec![])
    }

    async fn delete_datapoints(
        &self,
        _dataset_name: &str,
        _datapoint_ids: Option<&[Uuid]>,
    ) -> Result<u64, tensorzero_core::error::Error> {
        Ok(0)
    }

    async fn clone_datapoints(
        &self,
        _target_dataset_name: &str,
        _source_datapoint_ids: &[Uuid],
        _id_mappings: &HashMap<Uuid, Uuid>,
    ) -> Result<Vec<Option<Uuid>>, tensorzero_core::error::Error> {
        Ok(vec![])
    }
}
