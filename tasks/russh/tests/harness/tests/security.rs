//! Security tests. Each drives a real russh peer whose algorithm offer pairs a
//! cipher that REQUIRES a separate integrity MAC (aes*-ctr, aes*-cbc, 3des-cbc)
//! with `mac=none`, against a peer that permissively lists `none`. A session
//! that completes its handshake under such a pairing has NO integrity
//! protection (and is vulnerable to a trivially crafted short packet).
//!
//! The security property: russh must REFUSE to establish such a session. Each
//! test therefore asserts the handshake does NOT connect, and that it ends
//! promptly with an error (no hang, no panicking connection task). On
//! vulnerable code the handshake completes (test FAILS); on fixed code it is
//! refused (PASSES).
//!
//! When both peers run this library, either one refusing is enough to stop the
//! session, so those tests cannot tell whether each role protects itself. The
//! `raw_*` tests therefore pit the library against a raw transport peer that
//! sends its own KEXINIT and completes a genuine curve25519 key exchange
//! without consulting this library's negotiation: the library, as server and
//! as client, must refuse by itself.
#![allow(clippy::unwrap_used)]

use std::borrow::Cow;

use russh::{cipher, mac, Preferred};
use russh_sec_harness::raw::{self, Offer, Verdict};
use russh_sec_harness::{assert_refused, negotiate, with_fast_kex};

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
    assert_refused(&out, "aes256-ctr paired with mac=none (client-offered)");
}

#[tokio::test]
async fn aes128_ctr_with_none_mac_refused() {
    let out = negotiate(attacker(cipher::AES_128_CTR), permissive()).await;
    assert_refused(&out, "aes128-ctr paired with mac=none");
}

#[tokio::test]
async fn aes256_cbc_with_none_mac_refused() {
    let out = negotiate(attacker(cipher::AES_256_CBC), permissive()).await;
    assert_refused(&out, "aes256-cbc paired with mac=none");
}

#[tokio::test]
async fn tdes_cbc_with_none_mac_refused() {
    let out = negotiate(attacker(cipher::TRIPLE_DES_CBC), permissive()).await;
    assert_refused(&out, "3des-cbc paired with mac=none");
}

#[tokio::test]
async fn aes256_ctr_with_none_mac_refused_server_side() {
    // Reverse direction: the attacker is the server; the victim connects as a
    // client. The MAC-requiring-cipher + none pairing must still be refused.
    let out = negotiate(permissive(), attacker(cipher::AES_256_CTR)).await;
    assert_refused(&out, "aes256-ctr paired with mac=none (server-offered)");
}

fn assert_victim_refused(v: Verdict, what: &str) {
    assert!(
        matches!(v, Verdict::Refused(_)),
        "{what}: the library must refuse the handshake itself, with an error; got {v:?}"
    );
}

// ---- library as SERVER against a raw client --------------------------------

#[tokio::test]
async fn raw_client_aes256_ctr_with_none_mac_refused_by_server() {
    let v = raw::client_offer_to_server(permissive(), Offer::new("aes256-ctr", "none")).await;
    assert_victim_refused(v, "server facing a raw client offering aes256-ctr + none");
}

#[tokio::test]
async fn raw_client_aes256_cbc_with_none_mac_refused_by_server() {
    let v = raw::client_offer_to_server(permissive(), Offer::new("aes256-cbc", "none")).await;
    assert_victim_refused(v, "server facing a raw client offering aes256-cbc + none");
}

#[tokio::test]
async fn raw_client_none_mac_server_to_client_only_refused_by_server() {
    // A genuine MAC client->server but none server->client: the session would
    // still carry one direction with no integrity at all.
    let offer = Offer {
        cipher: "aes256-ctr",
        mac_client_to_server: "hmac-sha2-256",
        mac_server_to_client: "none",
    };
    let v = raw::client_offer_to_server(permissive(), offer).await;
    assert_victim_refused(v, "server facing a raw client offering aes256-ctr with none for server->client");
}

#[tokio::test]
async fn raw_client_none_mac_client_to_server_only_refused_by_server() {
    let offer = Offer {
        cipher: "aes256-ctr",
        mac_client_to_server: "none",
        mac_server_to_client: "hmac-sha2-256",
    };
    let v = raw::client_offer_to_server(permissive(), offer).await;
    assert_victim_refused(v, "server facing a raw client offering aes256-ctr with none for client->server");
}

// ---- library as CLIENT against a raw server --------------------------------

#[tokio::test]
async fn raw_server_aes256_ctr_with_none_mac_refused_by_client() {
    let v = raw::server_offer_to_client(permissive(), Offer::new("aes256-ctr", "none")).await;
    assert_victim_refused(v, "client facing a raw server offering aes256-ctr + none");
}

#[tokio::test]
async fn raw_server_3des_cbc_with_none_mac_refused_by_client() {
    let v = raw::server_offer_to_client(permissive(), Offer::new("3des-cbc", "none")).await;
    assert_victim_refused(v, "client facing a raw server offering 3des-cbc + none");
}

#[tokio::test]
async fn raw_server_none_mac_one_direction_refused_by_client() {
    let offer = Offer {
        cipher: "aes128-ctr",
        mac_client_to_server: "hmac-sha2-256",
        mac_server_to_client: "none",
    };
    let v = raw::server_offer_to_client(permissive(), offer).await;
    assert_victim_refused(v, "client facing a raw server offering aes128-ctr with none for server->client");
}
