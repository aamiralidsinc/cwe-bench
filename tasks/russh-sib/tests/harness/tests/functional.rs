//! Functional tests. Legitimate algorithm combinations must keep working, so a
//! fix that over-restricts (bans `mac=none` even for AEAD ciphers, drops the
//! MAC-requiring ciphers, or refuses a real key exchange) is caught here.
#![allow(clippy::unwrap_used)]

use std::borrow::Cow;

use russh::{cipher, kex, mac, Preferred};
use russh_sec_harness::russh_peer;
use russh_sec_harness::{
    echo_round_trip, negotiate, victim_client_rekey_with_legacy_server, victim_client_vs_legacy_server,
    victim_server_rekey_by_legacy_client, victim_server_vs_legacy_client, with_fast_kex,
};

fn only(ciph: cipher::Name, m: mac::Name) -> Preferred {
    with_fast_kex(Preferred {
        cipher: Cow::Owned(vec![ciph]),
        mac: Cow::Owned(vec![m]),
        ..Preferred::DEFAULT
    })
}

fn kex_cipher_mac(k: kex::Name, ciph: cipher::Name, m: mac::Name) -> Preferred {
    Preferred {
        kex: Cow::Owned(vec![k]),
        cipher: Cow::Owned(vec![ciph]),
        mac: Cow::Owned(vec![m]),
        ..Preferred::DEFAULT
    }
}

const MSG: &[u8] = b"the quick brown fox jumps over the lazy dog 0123456789";

#[tokio::test]
async fn default_handshake_connects() {
    // Out-of-the-box defaults on both sides: a real kex, an AEAD cipher and a
    // real MAC list, with compression `none` (the default).
    let out = negotiate(with_fast_kex(Preferred::DEFAULT), with_fast_kex(Preferred::DEFAULT)).await;
    assert!(out.connected, "default client/server handshake must connect");
    let _ = out.names.expect("names captured");
}

#[tokio::test]
async fn aes256_ctr_with_hmac_sha256_works() {
    let p = only(cipher::AES_256_CTR, mac::HMAC_SHA256);
    let out = negotiate(p.clone(), p).await;
    assert!(out.connected, "aes256-ctr + hmac-sha2-256 must connect");
    let names = out.names.expect("names captured");
    assert_eq!(names.client_mac, "hmac-sha2-256");
    assert_eq!(names.cipher, "aes256-ctr");
}

#[tokio::test]
async fn aes256_cbc_with_hmac_sha512_works() {
    let p = only(cipher::AES_256_CBC, mac::HMAC_SHA512);
    let out = negotiate(p.clone(), p).await;
    assert!(out.connected, "aes256-cbc + hmac-sha2-512 must connect");
    let names = out.names.expect("names captured");
    assert_eq!(names.client_mac, "hmac-sha2-512");
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
async fn real_kex_curve25519_full_round_trip() {
    // A real key exchange with a real cipher and MAC must carry a full session.
    let p = kex_cipher_mac(kex::CURVE25519, cipher::AES_256_CTR, mac::HMAC_SHA256);
    let echoed = echo_round_trip(p.clone(), p, MSG)
        .await
        .expect("full session over curve25519 + aes256-ctr + hmac must work");
    assert_eq!(echoed, MSG, "echoed data must match");
}

#[tokio::test]
async fn real_kex_mlkem_connects() {
    // A different real key exchange must also still connect (a fix must not ban
    // key exchange wholesale while removing the null one).
    let p = kex_cipher_mac(kex::MLKEM768X25519_SHA256, cipher::AES_256_GCM, mac::NONE);
    let out = negotiate(p.clone(), p).await;
    assert!(out.connected, "mlkem768x25519-sha256 handshake must connect");
    let names = out.names.expect("names captured");
    assert_eq!(names.kex, "mlkem768x25519-sha256");
}

// ---- interoperability with a peer running the library as the task found it --

fn legacy_default() -> russh_peer::Preferred {
    russh_peer::Preferred {
        kex: Cow::Borrowed(&[russh_peer::kex::CURVE25519]),
        ..russh_peer::Preferred::DEFAULT
    }
}

#[tokio::test]
async fn legacy_client_default_interoperates() {
    let out = victim_server_vs_legacy_client(with_fast_kex(Preferred::DEFAULT), legacy_default()).await;
    assert!(out.connected, "a default client of the original library must still connect: {:?}", out.error);
}

#[tokio::test]
async fn legacy_server_default_interoperates() {
    let out = victim_client_vs_legacy_server(with_fast_kex(Preferred::DEFAULT), legacy_default()).await;
    assert!(out.connected, "a default server of the original library must still be reachable: {:?}", out.error);
}

// ---- re-keying with a real key exchange keeps the session working -----------

#[tokio::test]
async fn rekey_with_real_kex_keeps_session_server_side() {
    let out = victim_server_rekey_by_legacy_client(
        with_fast_kex(Preferred::DEFAULT),
        legacy_default(),
        vec![russh_peer::kex::CURVE25519],
    )
    .await;
    assert!(out.rekey_completed, "a re-key with a real key exchange must complete; got {:?}", out.kexes);
    assert!(out.echo_after, "the session must keep carrying data after a real re-key");
}

#[tokio::test]
async fn rekey_with_real_kex_keeps_session_client_side() {
    let out = victim_client_rekey_with_legacy_server(
        with_fast_kex(Preferred::DEFAULT),
        legacy_default(),
        vec![russh_peer::kex::CURVE25519],
    )
    .await;
    assert!(out.rekey_completed, "a re-key with a real key exchange must complete; got {:?}", out.kexes);
    assert!(out.echo_after, "the session must keep carrying data after a real re-key");
}
