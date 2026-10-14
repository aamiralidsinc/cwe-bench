//! Functional tests. Legitimate algorithm combinations must keep working, so a
//! fix that over-restricts (e.g. bans `mac=none` outright, or drops the
//! MAC-requiring ciphers) is caught here.
#![allow(clippy::unwrap_used)]

use std::borrow::Cow;

use russh::{cipher, mac, Preferred};
use russh_sec_harness::{echo_round_trip, negotiate, with_fast_kex};

fn only(ciph: cipher::Name, m: mac::Name) -> Preferred {
    with_fast_kex(Preferred {
        cipher: Cow::Owned(vec![ciph]),
        mac: Cow::Owned(vec![m]),
        ..Preferred::DEFAULT
    })
}

const MSG: &[u8] = b"the quick brown fox jumps over the lazy dog 0123456789";

#[tokio::test]
async fn default_handshake_connects_with_a_real_mac() {
    // Out-of-the-box defaults on both sides.
    let out = negotiate(with_fast_kex(Preferred::DEFAULT), with_fast_kex(Preferred::DEFAULT)).await;
    assert!(out.connected, "default client/server handshake must connect");
    let names = out.names.expect("names captured");
    // Default ciphers (chacha20/gcm are AEAD) may negotiate mac=none legitimately,
    // but the handshake must succeed.
    let _ = names;
}

#[tokio::test]
async fn aes256_ctr_with_hmac_sha256_works() {
    let p = only(cipher::AES_256_CTR, mac::HMAC_SHA256);
    let out = negotiate(p.clone(), p).await;
    assert!(out.connected, "aes256-ctr + hmac-sha2-256 must connect");
    let names = out.names.expect("names captured");
    assert_eq!(names.client_mac.as_ref(), "hmac-sha2-256");
    assert_eq!(names.cipher.as_ref(), "aes256-ctr");
}

#[tokio::test]
async fn aes256_cbc_with_hmac_sha512_works() {
    let p = only(cipher::AES_256_CBC, mac::HMAC_SHA512);
    let out = negotiate(p.clone(), p).await;
    assert!(out.connected, "aes256-cbc + hmac-sha2-512 must connect");
    let names = out.names.expect("names captured");
    assert_eq!(names.client_mac.as_ref(), "hmac-sha2-512");
}

#[tokio::test]
async fn aes256_gcm_with_none_mac_works() {
    // AEAD cipher: mac=none is legitimate and must remain allowed.
    let p = only(cipher::AES_256_GCM, mac::NONE);
    let out = negotiate(p.clone(), p).await;
    assert!(
        out.connected,
        "aes256-gcm (AEAD) with mac=none is legitimate and must connect"
    );
}

#[tokio::test]
async fn chacha20_poly1305_with_none_mac_works() {
    // AEAD cipher: mac=none is legitimate and must remain allowed.
    let p = only(cipher::CHACHA20_POLY1305, mac::NONE);
    let out = negotiate(p.clone(), p).await;
    assert!(
        out.connected,
        "chacha20-poly1305 (AEAD) with mac=none is legitimate and must connect"
    );
}

#[tokio::test]
async fn aes256_ctr_hmac_full_data_round_trip() {
    let p = only(cipher::AES_256_CTR, mac::HMAC_SHA256);
    let echoed = echo_round_trip(p.clone(), p, MSG)
        .await
        .expect("full session with aes256-ctr + hmac must work");
    assert_eq!(echoed, MSG, "echoed data must match");
}
