//! Helpers shared by the hidden suites.
//!
//! Every fixture is built here from first principles (a 128-byte NNEF tensor header, an ONNX
//! protobuf) so that no expected value is computed with the code under test.
#![allow(dead_code)]

use std::path::{Path, PathBuf};

use tract_nnef::prelude::*;

pub const TRACT_VENDOR: u16 = ((b'T' as u16) << 8) | b'R' as u16;

/// Build an NNEF tensor file: 128-byte header (magic, version, byte count, rank, dims,
/// bits per item, item type, vendor) followed by `payload`.
pub fn dat(
    dims: &[u32],
    data_size_bytes: u32,
    bits_per_item: u32,
    item_type: u16,
    vendor: u16,
    payload: &[u8],
) -> Vec<u8> {
    assert!(dims.len() <= 8);
    let mut h = vec![0u8; 128];
    h[0] = 0x4e;
    h[1] = 0xef;
    h[2] = 1;
    h[3] = 0;
    h[4..8].copy_from_slice(&data_size_bytes.to_le_bytes());
    h[8..12].copy_from_slice(&(dims.len() as u32).to_le_bytes());
    for (i, d) in dims.iter().enumerate() {
        h[12 + 4 * i..16 + 4 * i].copy_from_slice(&d.to_le_bytes());
    }
    h[44..48].copy_from_slice(&bits_per_item.to_le_bytes());
    h[48..50].copy_from_slice(&item_type.to_le_bytes());
    h[50..52].copy_from_slice(&vendor.to_le_bytes());
    h.extend_from_slice(payload);
    h
}

/// A fresh directory for one test, keyed by name and process so parallel tests never collide.
pub fn temp_dir(name: &str) -> PathBuf {
    let mut p = std::env::temp_dir();
    p.push(format!("tract-fixture-{}-{}", name, std::process::id()));
    let _ = std::fs::remove_dir_all(&p);
    std::fs::create_dir_all(&p).expect("creating the fixture directory");
    p
}

/// Write an NNEF model directory: `graph.nnef` plus one file per tensor.
pub fn nnef_model(name: &str, graph: &str, files: &[(&str, Vec<u8>)]) -> PathBuf {
    let dir = temp_dir(name);
    std::fs::write(dir.join("graph.nnef"), graph).expect("writing graph.nnef");
    for (f, content) in files {
        std::fs::write(dir.join(f), content).expect("writing a tensor file");
    }
    dir
}

/// Load an NNEF model. Outer `Err(())` means the loader panicked: a crash is not a refusal.
pub fn load_nnef(dir: &Path) -> Result<TractResult<TypedModel>, ()> {
    std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| {
        tract_nnef::nnef().model_for_path(dir)
    }))
    .map_err(|_| ())
}

/// Load an ONNX model. Outer `Err(())` means the loader panicked.
pub fn load_onnx(path: &Path) -> Result<TractResult<tract_onnx::tract_hir::prelude::InferenceModel>, ()> {
    std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| {
        tract_onnx::onnx().model_for_path(path)
    }))
    .map_err(|_| ())
}

/// Encode an ONNX model holding a single initializer named `w`, exposed as the graph output.
/// `dims` and `raw` are the initializer's declared shape and stored payload; `external` names a
/// side file (created empty when present) instead of inline data.
pub fn onnx_single_initializer(
    dims: &[i64],
    data_type: i32,
    raw: &[u8],
    external: Option<&str>,
) -> Vec<u8> {
    use prost::Message;
    use tract_onnx::pb;

    let tensor = pb::TensorProto {
        dims: dims.to_vec(),
        data_type,
        raw_data: raw.to_vec(),
        name: "w".into(),
        data_location: external
            .map(|_| pb::tensor_proto::DataLocation::External as i32),
        external_data: external
            .map(|f| vec![pb::StringStringEntryProto { key: "location".into(), value: f.into() }])
            .unwrap_or_default(),
        ..Default::default()
    };
    let graph = pb::GraphProto {
        name: "g".into(),
        initializer: vec![tensor],
        output: vec![pb::ValueInfoProto { name: "w".into(), ..Default::default() }],
        ..Default::default()
    };
    let model = pb::ModelProto {
        ir_version: 8,
        graph: Some(graph),
        opset_import: vec![pb::OperatorSetIdProto { domain: "".into(), version: 13 }],
        ..Default::default()
    };
    model.encode_to_vec()
}
