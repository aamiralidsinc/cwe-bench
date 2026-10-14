//! Security tests. Each drives a real russh peer whose algorithm offer pairs a
//! cipher that REQUIRES a separate integrity MAC (aes*-ctr, aes*-cbc, 3des-cbc)
//! with `mac=none`, against a peer that permissively lists `none`. A session
//! that completes its handshake under such a pairing has NO integrity
//! protection (and is vulnerable to a trivially crafted short packet).
//!
//! The security property: russh must REFUSE to establish such a session. Each
//! test therefore asserts the handshake does NOT connect. On vulnerable code
//! the handshake completes (test FAILS); on fixed code it is refused (PASSES).
#![allow(clippy::unwrap_used)]

use std::borrow::Cow;

use russh::{cipher, mac, Preferred};
use russh_sec_harness::{negotiate, with_fast_kex};

/// A permissive peer: offers strong AEAD and MAC-requiring ciphers, and lists
/// `none` among its MACs (a plausible operator misconfiguration).
fn permissive() -> Preferred {
    with_fast_kex(Preferred {
        cipher: Cow::Borrowed(&[
            cipher::CHACHA20_POLY1305,
            cipher::AES_256_GCM,
            cipher::AES_256_CTR,
            cipher::AES_128_CTR,
            cipher::AES_256_CBC,
            cipher::TRIPLE_DES_CBC,
        ]),
        mac: Cow::Borrowed(&[mac::HMAC_SHA256, mac::NONE]),
        ..Preferred::DEFAULT
    })
}

/// A peer that offers ONLY a MAC-requiring cipher together with `mac=none`.
fn attacker(ciph: cipher::Name) -> Preferred {
    with_fast_kex(Preferred {
        cipher: Cow::Owned(vec![ciph]),
        mac: Cow::Borrowed(&[mac::NONE]),
        ..Preferred::DEFAULT
    })
}

#[tokio::test]
async fn aes256_ctr_with_none_mac_refused_client_side() {
    // Attacker is the connecting client; victim is the server.
    let out = negotiate(attacker(cipher::AES_256_CTR), permissive()).await;
    assert!(
        !out.connected,
        "aes256-ctr paired with mac=none must not establish a session; negotiated {:?}",
        out.names.map(|n| (n.cipher.as_ref().to_string(), n.client_mac.as_ref().to_string(), n.server_mac.as_ref().to_string()))
    );
}

#[tokio::test]
async fn aes128_ctr_with_none_mac_refused() {
    let out = negotiate(attacker(cipher::AES_128_CTR), permissive()).await;
    assert!(
        !out.connected,
        "aes128-ctr paired with mac=none must not establish a session"
    );
}

#[tokio::test]
async fn aes256_cbc_with_none_mac_refused() {
    let out = negotiate(attacker(cipher::AES_256_CBC), permissive()).await;
    assert!(
        !out.connected,
        "aes256-cbc paired with mac=none must not establish a session"
    );
}

#[tokio::test]
async fn tdes_cbc_with_none_mac_refused() {
    let out = negotiate(attacker(cipher::TRIPLE_DES_CBC), permissive()).await;
    assert!(
        !out.connected,
        "3des-cbc paired with mac=none must not establish a session"
    );
}

#[tokio::test]
async fn aes256_ctr_with_none_mac_refused_server_side() {
    // Reverse direction: the attacker is the server; the victim connects as a
    // client. The MAC-requiring-cipher + none pairing must still be refused.
    let out = negotiate(permissive(), attacker(cipher::AES_256_CTR)).await;
    assert!(
        !out.connected,
        "aes256-ctr paired with mac=none must not establish a session (server-offered)"
    );
}
