//! Shared test harness: drive a real russh client against a real russh server
//! over a localhost TCP socket (no network), with caller-chosen algorithm
//! preferences, and report what was negotiated.
#![allow(clippy::unwrap_used)]

use std::borrow::Cow;
use std::sync::{Arc, Mutex};
use std::time::Duration;

use russh::keys::{PrivateKeyWithHashAlg, PublicKeyOrCertificate};
use russh::*;
use ssh_key::PrivateKey;

#[derive(Clone)]
pub struct TestServer;

impl server::Handler for TestServer {
    type Error = russh::Error;

    async fn auth_publickey(
        &mut self,
        _user: &str,
        _public_key: &ssh_key::PublicKey,
    ) -> Result<server::Auth, Self::Error> {
        Ok(server::Auth::Accept)
    }

    async fn channel_open_session(
        &mut self,
        _channel: Channel<server::Msg>,
        reply: server::ChannelOpenHandle,
        _session: &mut server::Session,
    ) -> Result<(), Self::Error> {
        reply.accept().await;
        Ok(())
    }

    async fn data(
        &mut self,
        channel: ChannelId,
        data: &[u8],
        session: &mut server::Session,
    ) -> Result<(), Self::Error> {
        session.data(channel, data.to_vec())?;
        Ok(())
    }
}

pub struct TestClient {
    pub names: Arc<Mutex<Option<Names>>>,
}

impl client::Handler for TestClient {
    type Error = russh::Error;

    async fn check_server_key(
        &mut self,
        _server_public_key: &PublicKeyOrCertificate,
    ) -> Result<bool, Self::Error> {
        Ok(true)
    }

    async fn kex_done(
        &mut self,
        _shared_secret: Option<&[u8]>,
        names: &Names,
        _session: &mut client::Session,
    ) -> Result<(), Self::Error> {
        *self.names.lock().unwrap() = Some(names.clone());
        Ok(())
    }
}

fn mk_server_config(pref: Preferred) -> Arc<server::Config> {
    let mut c = server::Config::default();
    c.inactivity_timeout = None;
    c.auth_rejection_time = Duration::from_millis(100);
    c.keys
        .push(PrivateKey::random(&mut rand::rng(), ssh_key::Algorithm::Ed25519).unwrap());
    c.preferred = pref;
    Arc::new(c)
}

fn mk_client_config(pref: Preferred) -> Arc<client::Config> {
    let mut c = client::Config::default();
    c.inactivity_timeout = None;
    c.preferred = pref;
    Arc::new(c)
}

/// Pin KEX to a single fast algorithm so the handshake is quick and
/// deterministic; leave everything else at the caller's choice.
pub fn with_fast_kex(mut p: Preferred) -> Preferred {
    p.kex = Cow::Borrowed(&[kex::CURVE25519]);
    p
}

/// Outcome of attempting to bring up a session.
pub struct Outcome {
    /// Did the client handshake (through NEWKEYS) succeed?
    pub connected: bool,
    /// Algorithms the client observed as negotiated (only if connected).
    pub names: Option<Names>,
}

/// Attempt only the transport handshake: client connects, we capture the
/// negotiated algorithms, then disconnect. Returns whether it connected.
pub async fn negotiate(client_pref: Preferred, server_pref: Preferred) -> Outcome {
    let server_config = mk_server_config(server_pref);
    let client_config = mk_client_config(client_pref);

    let listener = tokio::net::TcpListener::bind("127.0.0.1:0").await.unwrap();
    let addr = listener.local_addr().unwrap();

    tokio::spawn(async move {
        if let Ok((socket, _)) = listener.accept().await {
            let _ = server::run_stream(server_config, socket, TestServer).await;
        }
    });

    let names = Arc::new(Mutex::new(None));
    let handler = TestClient {
        names: names.clone(),
    };

    let connect = tokio::time::timeout(
        Duration::from_secs(20),
        client::connect(client_config, addr, handler),
    )
    .await;

    match connect {
        Ok(Ok(mut session)) => {
            let captured = names.lock().unwrap().clone();
            let _ = session
                .disconnect(Disconnect::ByApplication, "", "")
                .await;
            Outcome {
                connected: true,
                names: captured,
            }
        }
        _ => Outcome {
            connected: false,
            names: None,
        },
    }
}

/// Full legitimate session: handshake, authenticate with a public key, open a
/// session channel, echo data, and confirm the byte round-trip. Returns the
/// echoed bytes on success.
pub async fn echo_round_trip(
    client_pref: Preferred,
    server_pref: Preferred,
    payload: &[u8],
) -> anyhow::Result<Vec<u8>> {
    let server_config = mk_server_config(server_pref);
    let client_config = mk_client_config(client_pref);

    let listener = tokio::net::TcpListener::bind("127.0.0.1:0").await?;
    let addr = listener.local_addr()?;

    tokio::spawn(async move {
        if let Ok((socket, _)) = listener.accept().await {
            let _ = server::run_stream(server_config, socket, TestServer).await;
        }
    });

    let names = Arc::new(Mutex::new(None));
    let handler = TestClient {
        names: names.clone(),
    };

    let client_key = PrivateKey::random(&mut rand::rng(), ssh_key::Algorithm::Ed25519)?;

    let mut session = tokio::time::timeout(
        Duration::from_secs(20),
        client::connect(client_config, addr, handler),
    )
    .await
    .map_err(|_| anyhow::anyhow!("connect timed out"))?
    .map_err(|e| anyhow::anyhow!("connect failed: {e:?}"))?;

    let authed = session
        .authenticate_publickey(
            "user",
            PrivateKeyWithHashAlg::new(Arc::new(client_key), None),
        )
        .await
        .map_err(|e| anyhow::anyhow!("auth error: {e:?}"))?
        .success();
    if !authed {
        anyhow::bail!("authentication failed");
    }

    let mut channel = session.channel_open_session().await?;
    channel.data(payload).await?;

    let collected = Arc::new(Mutex::new(Vec::new()));
    let want = payload.len();
    let got = tokio::time::timeout(Duration::from_secs(20), async {
        loop {
            match channel.wait().await {
                Some(ChannelMsg::Data { ref data }) => {
                    let mut g = collected.lock().unwrap();
                    g.extend_from_slice(&data[..]);
                    if g.len() >= want {
                        return g.clone();
                    }
                }
                Some(_) => continue,
                None => return collected.lock().unwrap().clone(),
            }
        }
    })
    .await
    .map_err(|_| anyhow::anyhow!("echo timed out"))?;

    let _ = session
        .disconnect(Disconnect::ByApplication, "", "")
        .await;
    Ok(got)
}
