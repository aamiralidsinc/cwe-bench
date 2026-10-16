//! Security tests. Each drives a real russh client against a real russh server
//! over a loopback TCP socket, with one peer offering an algorithm set that, if
//! accepted, yields a session with NO cryptographic protection — no
//! confidentiality, no integrity, and/or no server authentication. Three
//! independent negotiation decisions can each produce such a session:
//!
//!   * the key-exchange stage accepting the null exchange (`none`), which does
//!     no key agreement and signs no host key (initially or in a re-key);
//!   * the cipher stage accepting the null cipher (`none`/`clear`) paired with
//!     no MAC, giving plaintext with no integrity;
//!   * the MAC stage accepting `mac=none` for a cipher that provides no
//!     integrity of its own (a CTR/CBC/3des block cipher).
//!
//! The security property: russh must REFUSE to complete such a handshake,
//! cleanly (an error, not a hang or a panic), whichever side makes the offer.
//! The first group runs the library under test on both sides. The `legacy_*`
//! group puts the library under test on ONE side only; the attacker is a peer
//! that never refuses (the library as the task found it), so the side under
//! test must refuse by itself.
#![allow(clippy::unwrap_used)]

use std::borrow::Cow;

use russh::{cipher, kex, mac, Preferred};
use russh_sec_harness::russh_peer;
use russh_sec_harness::{
    negotiate, victim_client_rekey_with_legacy_server, victim_client_vs_legacy_server,
    victim_server_vs_legacy_client, with_fast_kex,
};

/// Pin a specific key-exchange list, leaving everything else at defaults.
fn kex_only(kexes: Vec<kex::Name>) -> Preferred {
    Preferred {
        kex: Cow::Owned(kexes),
        ..Preferred::DEFAULT
    }
}

/// A peer that offers exactly one cipher together with `mac=none` (a real
/// key exchange is pinned so only the cipher/MAC choice is under test).
fn cipher_attacker(ciph: cipher::Name) -> Preferred {
    with_fast_kex(Preferred {
        cipher: Cow::Owned(vec![ciph]),
        mac: Cow::Borrowed(&[mac::NONE]),
        ..Preferred::DEFAULT
    })
}

/// A permissive endpoint: offers strong AEAD plus MAC-requiring and null
/// ciphers, and lists `none` among its MACs (a plausible operator
/// misconfiguration).
fn cipher_permissive() -> Preferred {
    with_fast_kex(Preferred {
        cipher: Cow::Borrowed(&[
            cipher::CHACHA20_POLY1305,
            cipher::AES_256_GCM,
            cipher::AES_128_GCM,
            cipher::AES_256_CTR,
            cipher::AES_192_CTR,
            cipher::AES_128_CTR,
            cipher::AES_256_CBC,
            cipher::AES_192_CBC,
            cipher::AES_128_CBC,
            cipher::TRIPLE_DES_CBC,
            cipher::NONE,
            cipher::CLEAR,
        ]),
        mac: Cow::Borrowed(&[mac::HMAC_SHA256, mac::HMAC_SHA512, mac::NONE]),
        ..Preferred::DEFAULT
    })
}

/// A permissive endpoint whose key-exchange list keeps `none` as a last
/// resort behind a real exchange.
fn kex_permissive() -> Preferred {
    kex_only(vec![kex::CURVE25519, kex::NONE])
}

// Offers of the legacy (attacker) peer.
mod legacy {
    use super::Cow;
    use super::russh_peer::{cipher, kex, mac, Preferred};

    pub fn kex_only(kexes: Vec<kex::Name>) -> Preferred {
        Preferred {
            kex: Cow::Owned(kexes),
            ..Preferred::DEFAULT
        }
    }

    pub fn cipher_attacker(ciph: cipher::Name) -> Preferred {
        Preferred {
            kex: Cow::Borrowed(&[kex::CURVE25519]),
            cipher: Cow::Owned(vec![ciph]),
            mac: Cow::Borrowed(&[mac::NONE]),
            ..Preferred::DEFAULT
        }
    }

    /// Ordinary offer for the initial exchange of the re-key tests.
    pub fn ordinary() -> Preferred {
        Preferred {
            kex: Cow::Borrowed(&[kex::CURVE25519]),
            ..Preferred::DEFAULT
        }
    }

    pub use kex::NONE as NULL_KEX;
}

// ---- key-exchange stage: the null exchange ---------------------------------

#[tokio::test]
async fn null_kex_refused_client_offered() {
    // Attacker connects as the client offering only the null key exchange; the
    // victim server permissively lists it alongside a real one.
    let out = negotiate(kex_only(vec![kex::NONE]), kex_only(vec![kex::NONE, kex::CURVE25519])).await;
    out.assert_refused("null key exchange (client-offered)");
}

#[tokio::test]
async fn null_kex_refused_server_offered() {
    // Reverse direction: the attacker is the server offering only the null
    // exchange; the victim connects as a client.
    let out = negotiate(kex_only(vec![kex::NONE, kex::CURVE25519]), kex_only(vec![kex::NONE])).await;
    out.assert_refused("null key exchange (server-offered)");
}

// ---- cipher stage: the null cipher with no MAC -----------------------------

#[tokio::test]
async fn null_cipher_none_mac_refused_client_offered() {
    let out = negotiate(cipher_attacker(cipher::NONE), cipher_permissive()).await;
    out.assert_refused("null cipher with mac=none (client-offered)");
}

#[tokio::test]
async fn null_cipher_none_mac_refused_server_offered() {
    let out = negotiate(cipher_permissive(), cipher_attacker(cipher::NONE)).await;
    out.assert_refused("null cipher with mac=none (server-offered)");
}

#[tokio::test]
async fn clear_cipher_none_mac_refused() {
    // `clear` is the other name for the same no-encryption cipher.
    let out = negotiate(cipher_attacker(cipher::CLEAR), cipher_permissive()).await;
    out.assert_refused("clear cipher with mac=none");
}

// ---- MAC stage: a block cipher with no MAC ---------------------------------

#[tokio::test]
async fn block_cipher_ctr_none_mac_refused() {
    let out = negotiate(cipher_attacker(cipher::AES_256_CTR), cipher_permissive()).await;
    out.assert_refused("aes256-ctr with mac=none");
}

#[tokio::test]
async fn block_cipher_cbc_none_mac_refused() {
    let out = negotiate(cipher_attacker(cipher::AES_256_CBC), cipher_permissive()).await;
    out.assert_refused("aes256-cbc with mac=none");
}

#[tokio::test]
async fn triple_des_none_mac_refused_server_offered() {
    let out = negotiate(cipher_permissive(), cipher_attacker(cipher::TRIPLE_DES_CBC)).await;
    out.assert_refused("3des-cbc with mac=none (server-offered)");
}

// ---- one side only: the attacker is a peer that never refuses --------------

#[tokio::test]
async fn legacy_client_null_kex_refused_by_server() {
    let out = victim_server_vs_legacy_client(kex_permissive(), legacy::kex_only(vec![legacy::NULL_KEX])).await;
    out.assert_refused("server under test, client offers only the null key exchange");
}

#[tokio::test]
async fn legacy_server_null_kex_refused_by_client() {
    let out = victim_client_vs_legacy_server(kex_permissive(), legacy::kex_only(vec![legacy::NULL_KEX])).await;
    out.assert_refused("client under test, server offers only the null key exchange");
}

#[tokio::test]
async fn legacy_client_null_cipher_refused_by_server() {
    let out =
        victim_server_vs_legacy_client(cipher_permissive(), legacy::cipher_attacker(russh_peer::cipher::NONE)).await;
    out.assert_refused("server under test, client offers only the null cipher with mac=none");
}

#[tokio::test]
async fn legacy_server_clear_cipher_refused_by_client() {
    let out =
        victim_client_vs_legacy_server(cipher_permissive(), legacy::cipher_attacker(russh_peer::cipher::CLEAR)).await;
    out.assert_refused("client under test, server offers only the clear cipher with mac=none");
}

#[tokio::test]
async fn legacy_client_aes128_ctr_none_mac_refused_by_server() {
    let out = victim_server_vs_legacy_client(
        cipher_permissive(),
        legacy::cipher_attacker(russh_peer::cipher::AES_128_CTR),
    )
    .await;
    out.assert_refused("server under test, client offers aes128-ctr with mac=none");
}

#[tokio::test]
async fn legacy_server_aes128_cbc_none_mac_refused_by_client() {
    let out = victim_client_vs_legacy_server(
        cipher_permissive(),
        legacy::cipher_attacker(russh_peer::cipher::AES_128_CBC),
    )
    .await;
    out.assert_refused("client under test, server offers aes128-cbc with mac=none");
}

#[tokio::test]
async fn legacy_client_3des_none_mac_refused_by_server() {
    let out = victim_server_vs_legacy_client(
        cipher_permissive(),
        legacy::cipher_attacker(russh_peer::cipher::TRIPLE_DES_CBC),
    )
    .await;
    out.assert_refused("server under test, client offers 3des-cbc with mac=none");
}

#[tokio::test]
async fn legacy_server_aes192_ctr_none_mac_refused_by_client() {
    let out = victim_client_vs_legacy_server(
        cipher_permissive(),
        legacy::cipher_attacker(russh_peer::cipher::AES_192_CTR),
    )
    .await;
    out.assert_refused("client under test, server offers aes192-ctr with mac=none");
}

// ---- re-key: the null exchange answered on an established session ----------

#[tokio::test]
async fn legacy_server_rekey_to_null_kex_refused_by_client() {
    // A real exchange first; the client re-keys and the peer answers offering
    // only `none`.
    let out = victim_client_rekey_with_legacy_server(
        kex_permissive(),
        legacy::ordinary(),
        vec![legacy::NULL_KEX],
    )
    .await;
    out.assert_refused("client under test, server answers a re-key with only the null key exchange");
}
