mod common;

use common::*;

/// Hostname that the harness maps to the loopback interface before the suite runs.
const LOOPBACK_HOST: &str = "media-preview.internal";

#[tokio::test]
async fn sec_image_loopback_endpoint_is_refused() {
    let srv = LoopbackHttp::start("127.0.0.1:0", b64(PNG_B64), "image/png").await;
    let result = parse_chat(chat_body(image_part(&srv.url("127.0.0.1", "one.png")))).await;
    assert!(
        result.is_err(),
        "the server accepted an image source that points at its own loopback interface"
    );
    assert_eq!(srv.hits(), 0, "the server connected to the loopback endpoint");
}

#[tokio::test]
async fn sec_image_loopback_hostname_is_refused() {
    let srv = LoopbackHttp::start("127.0.0.1:0", b64(PNG_B64), "image/png").await;
    let result = parse_chat(chat_body(image_part(&srv.url(LOOPBACK_HOST, "one.png")))).await;
    assert!(
        result.is_err(),
        "the server accepted a host name that resolves to its own loopback interface"
    );
    assert_eq!(srv.hits(), 0, "the server connected to the loopback endpoint");
}

#[tokio::test]
async fn sec_image_server_local_path_is_refused() {
    let path = fixture("secret.png", &b64(PNG_B64));
    let result = parse_chat(chat_body(image_part(path.to_str().unwrap()))).await;
    assert!(
        result.is_err(),
        "the server accepted a bare server-local path as an image source"
    );
}

#[tokio::test]
async fn sec_image_server_local_file_url_is_refused() {
    let path = fixture("secret-url.png", &b64(PNG_B64));
    let url = format!("file://{}", path.display());
    let result = parse_chat(chat_body(image_part(&url))).await;
    assert!(
        result.is_err(),
        "the server accepted a file URL as an image source"
    );
}
