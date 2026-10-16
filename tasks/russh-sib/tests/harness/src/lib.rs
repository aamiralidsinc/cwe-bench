//! Shared test harness: drive a real russh client against a real russh server
//! over a localhost TCP socket (no network), with caller-chosen algorithm
//! preferences, and report what was negotiated.
//!
//! Two kinds of counterparty are available:
//!   * the library under test (`russh`, the code in /app) on both sides;
//!   * a legacy peer (`russh_peer`): the same library at the commit the task
//!     starts from, i.e. a peer that never refuses anything. A malicious
//!     client or server is not running the fixed library, so the side under
//!     test must refuse on its own.
//!
//! A refusal must be clean: the handshake ends in an error (not a hang until
//! the time limit), and no task panics.
#![allow(clippy::unwrap_used)]

use std::net::SocketAddr;
use std::sync::atomic::{AtomicBool, AtomicUsize, Ordering};
use std::sync::{Arc, Mutex, Once};
use std::time::Duration;

use ssh_key::PrivateKey;

pub use russh_peer;

const CONNECT_LIMIT: Duration = Duration::from_secs(20);

// ---- panic accounting --------------------------------------------------------

static PANICS: AtomicUsize = AtomicUsize::new(0);
static HOOK: Once = Once::new();

/// Count every panic in this test process (tests run one per process under
/// nextest), still printing it as usual.
pub fn watch_panics() {
    HOOK.call_once(|| {
        let prev = std::panic::take_hook();
        std::panic::set_hook(Box::new(move |info| {
            PANICS.fetch_add(1, Ordering::SeqCst);
            prev(info);
        }));
    });
}

pub fn panics() -> usize {
    PANICS.load(Ordering::SeqCst)
}

// ---- per-library endpoints (the same code for the library and the peer) -----

macro_rules! endpoints {
    ($m:ident, $r:ident) => {
        pub mod $m {
            use super::*;
            use $r::keys::{PrivateKeyWithHashAlg, PublicKeyOrCertificate};
            use $r::{client, server, Channel, ChannelId, ChannelMsg, Disconnect, Names, Preferred};

            #[derive(Clone)]
            pub struct TestServer;

            impl server::Handler for TestServer {
                type Error = $r::Error;

                async fn auth_publickey(
                    &mut self,
                    _user: &str,
                    _public_key: &ssh_key::PublicKey,
                ) -> Result<server::Auth, Self::Error> {
                    Ok(server::Auth::Accept)
                }

                async fn auth_password(&mut self, _user: &str, _password: &str) -> Result<server::Auth, Self::Error> {
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

            /// Records every completed key exchange (initial and re-keys) as
            /// the names of (kex, cipher, client MAC).
            pub struct TestClient {
                pub kexes: Arc<Mutex<Vec<(String, String, String)>>>,
                pub names: Arc<Mutex<Option<Names>>>,
            }

            impl client::Handler for TestClient {
                type Error = $r::Error;

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
                    self.kexes.lock().unwrap().push((
                        names.kex.as_ref().to_string(),
                        names.cipher.as_ref().to_string(),
                        names.client_mac.as_ref().to_string(),
                    ));
                    *self.names.lock().unwrap() = Some(names.clone());
                    Ok(())
                }
            }

            pub fn server_config(pref: Preferred) -> Arc<server::Config> {
                let mut c = server::Config::default();
                c.inactivity_timeout = None;
                c.auth_rejection_time = Duration::from_millis(100);
                c.keys
                    .push(PrivateKey::random(&mut rand::rng(), ssh_key::Algorithm::Ed25519).unwrap());
                c.preferred = pref;
                Arc::new(c)
            }

            pub fn client_config(pref: Preferred) -> Arc<client::Config> {
                let mut c = client::Config::default();
                c.inactivity_timeout = None;
                c.preferred = pref;
                Arc::new(c)
            }

            /// Accept one connection and run a server session on it. The
            /// returned task ends when that session ends.
            pub async fn serve(pref: Preferred) -> (SocketAddr, tokio::task::JoinHandle<()>) {
                let config = server_config(pref);
                let listener = tokio::net::TcpListener::bind("127.0.0.1:0").await.unwrap();
                let addr = listener.local_addr().unwrap();
                let task = tokio::spawn(async move {
                    if let Ok((socket, _)) = listener.accept().await {
                        if let Ok(running) = server::run_stream(config, socket, TestServer).await {
                            let _ = running.await;
                        }
                    }
                });
                (addr, task)
            }

            pub struct Connected {
                pub handle: client::Handle<TestClient>,
                pub kexes: Arc<Mutex<Vec<(String, String, String)>>>,
            }

            /// Result of a client connection attempt: connected, refused
            /// with an error, or neither within the time limit.
            pub enum Attempt {
                Connected(Connected, Option<Names>),
                Refused(String),
                TimedOut,
            }

            pub async fn connect(addr: SocketAddr, pref: Preferred) -> Attempt {
                let kexes = Arc::new(Mutex::new(Vec::new()));
                let names = Arc::new(Mutex::new(None));
                let handler = TestClient { kexes: kexes.clone(), names: names.clone() };
                match tokio::time::timeout(CONNECT_LIMIT, client::connect(client_config(pref), addr, handler)).await {
                    Ok(Ok(handle)) => {
                        let n = names.lock().unwrap().clone();
                        Attempt::Connected(Connected { handle, kexes }, n)
                    }
                    Ok(Err(e)) => Attempt::Refused(format!("{e:?}")),
                    Err(_) => Attempt::TimedOut,
                }
            }

            impl Connected {
                /// Authenticate with a password (works whatever the key
                /// exchange produced) and open a session channel.
                pub async fn open_with_password(&mut self) -> anyhow::Result<Channel<client::Msg>> {
                    let authed = self
                        .handle
                        .authenticate_password("user", "password")
                        .await
                        .map_err(|e| anyhow::anyhow!("auth error: {e:?}"))?
                        .success();
                    if !authed {
                        anyhow::bail!("authentication failed");
                    }
                    Ok(self.handle.channel_open_session().await?)
                }

                /// Authenticate and open a session channel.
                pub async fn open(&mut self) -> anyhow::Result<Channel<client::Msg>> {
                    let key = PrivateKey::random(&mut rand::rng(), ssh_key::Algorithm::Ed25519)?;
                    let authed = self
                        .handle
                        .authenticate_publickey("user", PrivateKeyWithHashAlg::new(Arc::new(key), None))
                        .await
                        .map_err(|e| anyhow::anyhow!("auth error: {e:?}"))?
                        .success();
                    if !authed {
                        anyhow::bail!("authentication failed");
                    }
                    Ok(self.handle.channel_open_session().await?)
                }

                pub async fn close(self) {
                    let _ = self.handle.disconnect(Disconnect::ByApplication, "", "").await;
                }
            }

            /// Send `payload` and wait for all of it to come back.
            pub async fn echo(channel: &mut Channel<client::Msg>, payload: &[u8]) -> anyhow::Result<Vec<u8>> {
                channel.data(payload).await?;
                let mut got = Vec::new();
                tokio::time::timeout(CONNECT_LIMIT, async {
                    while got.len() < payload.len() {
                        match channel.wait().await {
                            Some(ChannelMsg::Data { ref data }) => got.extend_from_slice(&data[..]),
                            Some(_) => continue,
                            None => break,
                        }
                    }
                })
                .await
                .map_err(|_| anyhow::anyhow!("echo timed out"))?;
                Ok(got)
            }

            /// Wait until the channel reports that the session is gone.
            pub async fn wait_closed(channel: &mut Channel<client::Msg>, limit: Duration) -> bool {
                tokio::time::timeout(limit, async {
                    loop {
                        if channel.wait().await.is_none() {
                            return;
                        }
                    }
                })
                .await
                .is_ok()
            }
        }
    };
}

endpoints!(lib_side, russh);
endpoints!(peer_side, russh_peer);

// ---- outcomes ----------------------------------------------------------------

/// Algorithm names a client observed as negotiated.
#[derive(Debug, Clone)]
pub struct Negotiated {
    pub kex: String,
    pub cipher: String,
    pub client_mac: String,
    pub server_mac: String,
}

/// Outcome of attempting to bring up a session.
pub struct Outcome {
    /// Did the client handshake (through NEWKEYS) succeed?
    pub connected: bool,
    /// The attempt ended in an error (the client saw the handshake fail).
    pub refused_with_error: bool,
    /// Neither connected nor failed within the time limit.
    pub timed_out: bool,
    /// Panics in this process during the attempt (either side).
    pub panics: usize,
    /// Algorithms the client observed as negotiated (only if connected).
    pub names: Option<Negotiated>,
    pub error: Option<String>,
}

impl Outcome {
    /// The security property for one attack: no session, and a clean refusal.
    pub fn assert_refused(&self, what: &str) {
        assert!(
            !self.connected,
            "{what}: the handshake completed and a session was established; negotiated {:?}",
            self.names
        );
        assert!(
            !self.timed_out,
            "{what}: the handshake neither completed nor failed within {CONNECT_LIMIT:?} (a hang is not a clean refusal)"
        );
        assert!(self.refused_with_error, "{what}: the handshake did not end in an error");
        assert_eq!(self.panics, 0, "{what}: a panic occurred while the handshake was refused (not a clean refusal)");
    }
}

async fn settle(server: tokio::task::JoinHandle<()>) {
    // Let the server side finish (it ends once the connection is gone) so a
    // panic there is counted too.
    let _ = tokio::time::timeout(Duration::from_secs(5), server).await;
}

macro_rules! outcome_from {
    ($side:ident, $attempt:expr, $server:expr, $before:expr) => {{
        let out = match $attempt {
            $side::Attempt::Connected(c, names) => {
                let names = names.map(|n| Negotiated {
                    kex: n.kex.as_ref().to_string(),
                    cipher: n.cipher.as_ref().to_string(),
                    client_mac: n.client_mac.as_ref().to_string(),
                    server_mac: n.server_mac.as_ref().to_string(),
                });
                c.close().await;
                (true, false, false, names, None)
            }
            $side::Attempt::Refused(e) => (false, true, false, None, Some(e)),
            $side::Attempt::TimedOut => (false, false, true, None, None),
        };
        settle($server).await;
        Outcome {
            connected: out.0,
            refused_with_error: out.1,
            timed_out: out.2,
            panics: panics() - $before,
            names: out.3,
            error: out.4,
        }
    }};
}

/// Both sides run the library under test.
pub async fn negotiate(client_pref: russh::Preferred, server_pref: russh::Preferred) -> Outcome {
    watch_panics();
    let before = panics();
    let (addr, server) = lib_side::serve(server_pref).await;
    let attempt = lib_side::connect(addr, client_pref).await;
    outcome_from!(lib_side, attempt, server, before)
}

/// Relay one connection to `upstream` and watch the server-to-client bytes
/// until encryption starts. Up to and including the server's NEWKEYS of the
/// first key exchange, SSH packets are plaintext (RFC 4253: identification
/// line, then uint32 packet_length, byte padding_length, payload...). The
/// flag is set when the server sends NEWKEYS, i.e. it completed its side of
/// the key exchange and switched the session onto the negotiated algorithms.
async fn newkeys_watch_proxy(upstream: SocketAddr) -> (SocketAddr, Arc<AtomicBool>) {
    use tokio::io::{AsyncReadExt, AsyncWriteExt};
    let listener = tokio::net::TcpListener::bind("127.0.0.1:0").await.unwrap();
    let addr = listener.local_addr().unwrap();
    let seen = Arc::new(AtomicBool::new(false));
    let flag = seen.clone();
    tokio::spawn(async move {
        let Ok((client, _)) = listener.accept().await else { return };
        let Ok(server) = tokio::net::TcpStream::connect(upstream).await else { return };
        let (mut cr, mut cw) = client.into_split();
        let (mut sr, mut sw) = server.into_split();
        tokio::spawn(async move {
            let _ = tokio::io::copy(&mut cr, &mut sw).await;
            let _ = sw.shutdown().await;
        });
        let mut pending: Vec<u8> = Vec::new();
        let mut banner_done = false;
        let mut watching = true;
        let mut chunk = vec![0u8; 16384];
        loop {
            let n = match sr.read(&mut chunk).await {
                Ok(0) | Err(_) => break,
                Ok(n) => n,
            };
            if watching {
                pending.extend_from_slice(&chunk[..n]);
                loop {
                    if !banner_done {
                        // Lines before (and including) the "SSH-" identification line.
                        let Some(eol) = pending.iter().position(|&b| b == b'\n') else { break };
                        let line: Vec<u8> = pending.drain(..=eol).collect();
                        banner_done = line.starts_with(b"SSH-");
                        continue;
                    }
                    if pending.len() < 4 {
                        break;
                    }
                    let len = u32::from_be_bytes([pending[0], pending[1], pending[2], pending[3]]) as usize;
                    if !(2..=262144).contains(&len) {
                        watching = false; // not plaintext framing any more
                        break;
                    }
                    if pending.len() < 4 + len {
                        break;
                    }
                    let msg_type = pending[5];
                    pending.drain(..4 + len);
                    if msg_type == 21 {
                        flag.store(true, Ordering::SeqCst);
                        watching = false;
                        break;
                    }
                }
                if !watching {
                    pending.clear();
                }
            }
            if cw.write_all(&chunk[..n]).await.is_err() {
                break;
            }
        }
        let _ = cw.shutdown().await;
    });
    (addr, seen)
}

/// The library under test is the SERVER; a legacy (non-refusing) peer
/// connects as the client with the given offer. The peer's own view of the
/// handshake is not evidence that the server accepted it (with the null key
/// exchange it considers itself done before the server answers), so the
/// server counts as having established the session when it sent NEWKEYS
/// (completed the key exchange). A refusal must also reach the peer as an
/// error: its connection attempt, or its first use of the session, fails.
pub async fn victim_server_vs_legacy_client(
    server_pref: russh::Preferred,
    attacker: russh_peer::Preferred,
) -> Outcome {
    watch_panics();
    let before = panics();
    let (upstream, server) = lib_side::serve(server_pref).await;
    let (addr, server_sent_newkeys) = newkeys_watch_proxy(upstream).await;
    let attempt = match peer_side::connect(addr, attacker).await {
        peer_side::Attempt::Connected(mut c, names) => {
            let used = tokio::time::timeout(CONNECT_LIMIT, async {
                let mut channel = c.open_with_password().await?;
                let got = peer_side::echo(&mut channel, b"is this session usable?").await?;
                anyhow::ensure!(got.as_slice() == b"is this session usable?", "echo mismatch");
                Ok(())
            })
            .await;
            match used {
                Ok(Ok(())) => peer_side::Attempt::Connected(c, names),
                Ok(Err(e)) => {
                    c.close().await;
                    peer_side::Attempt::Refused(format!("{e:?}"))
                }
                Err(_) => {
                    c.close().await;
                    peer_side::Attempt::TimedOut
                }
            }
        }
        other => other,
    };
    let mut out = outcome_from!(peer_side, attempt, server, before);
    if server_sent_newkeys.load(Ordering::SeqCst) {
        out.connected = true;
        out.refused_with_error = false;
    }
    out
}

/// The library under test is the CLIENT; a legacy (non-refusing) peer serves
/// with the given offer.
pub async fn victim_client_vs_legacy_server(
    client_pref: russh::Preferred,
    attacker: russh_peer::Preferred,
) -> Outcome {
    watch_panics();
    let before = panics();
    let (addr, server) = peer_side::serve(attacker).await;
    let attempt = lib_side::connect(addr, client_pref).await;
    outcome_from!(lib_side, attempt, server, before)
}

/// Pin KEX to a single fast algorithm so the handshake is quick and
/// deterministic; leave everything else at the caller's choice.
pub fn with_fast_kex(mut p: russh::Preferred) -> russh::Preferred {
    p.kex = std::borrow::Cow::Borrowed(&[russh::kex::CURVE25519]);
    p
}

/// Full legitimate session: handshake, authenticate with a public key, open a
/// session channel, echo data, and confirm the byte round-trip. Returns the
/// echoed bytes on success.
pub async fn echo_round_trip(
    client_pref: russh::Preferred,
    server_pref: russh::Preferred,
    payload: &[u8],
) -> anyhow::Result<Vec<u8>> {
    let (addr, _server) = lib_side::serve(server_pref).await;
    let mut c = match lib_side::connect(addr, client_pref).await {
        lib_side::Attempt::Connected(c, _) => c,
        lib_side::Attempt::Refused(e) => anyhow::bail!("connect failed: {e}"),
        lib_side::Attempt::TimedOut => anyhow::bail!("connect timed out"),
    };
    let mut channel = c.open().await?;
    let got = lib_side::echo(&mut channel, payload).await?;
    c.close().await;
    Ok(got)
}

// ---- re-key ------------------------------------------------------------------

/// Outcome of a re-key on an established, working session.
pub struct RekeyOutcome {
    /// Every key exchange the client completed: (kex, cipher, client MAC).
    pub kexes: Vec<(String, String, String)>,
    /// A second key exchange completed.
    pub rekey_completed: bool,
    /// Data still round-trips after the re-key completed.
    pub echo_after: bool,
    /// The session ended (the re-key was refused).
    pub session_closed: bool,
    /// Panics in this process during the re-key (either side).
    pub panics: usize,
}

impl RekeyOutcome {
    pub fn assert_refused(&self, what: &str) {
        assert!(
            !self.rekey_completed,
            "{what}: the re-key completed and the session continued; key exchanges {:?}",
            self.kexes
        );
        assert!(
            self.session_closed,
            "{what}: the re-key neither completed nor ended the session within {CONNECT_LIMIT:?}"
        );
        assert_eq!(self.panics, 0, "{what}: a panic occurred while the re-key was refused");
    }
}

const PAYLOAD: &[u8] = b"rekey probe 0123456789 abcdefghijklmnopqrstuvwxyz";

macro_rules! rekey_flow {
    ($side:ident, $c:ident, $rekey:block, $done:expr) => {{
        let mut channel = $c.open().await.expect("setup: authenticate and open a channel");
        let first = $side::echo(&mut channel, PAYLOAD).await.expect("setup: echo before the re-key");
        assert_eq!(first, PAYLOAD, "setup: echo before the re-key");
        assert_eq!($c.kexes.lock().unwrap().len(), 1, "setup: exactly one key exchange so far");
        $rekey
        let done = $done;
        let (completed, closed) = tokio::time::timeout(CONNECT_LIMIT, async {
            loop {
                if done() {
                    return (true, false);
                }
                tokio::select! {
                    msg = channel.wait() => {
                        if msg.is_none() {
                            return (done(), true);
                        }
                    }
                    _ = tokio::time::sleep(Duration::from_millis(50)) => {}
                }
            }
        })
        .await
        .unwrap_or((false, false));
        let echo_after = completed
            && matches!($side::echo(&mut channel, PAYLOAD).await, Ok(ref v) if v.as_slice() == PAYLOAD);
        let kexes = $c.kexes.lock().unwrap().clone();
        $c.close().await;
        (kexes, completed, echo_after, closed)
    }};
}

/// The library under test is the SERVER. A legacy peer connects as a client
/// with `attacker` (a real key exchange first), uses the session, then
/// re-keys offering only `rekey_kexes`. Used for legitimate re-keys only:
/// the peer's record of a completed key exchange is reliable for real
/// exchanges, not for the null one (see `victim_server_vs_legacy_client`).
pub async fn victim_server_rekey_by_legacy_client(
    server_pref: russh::Preferred,
    attacker: russh_peer::Preferred,
    rekey_kexes: Vec<russh_peer::kex::Name>,
) -> RekeyOutcome {
    watch_panics();
    let (addr, server) = lib_side::serve(server_pref).await;
    let mut c = match peer_side::connect(addr, attacker).await {
        peer_side::Attempt::Connected(c, _) => c,
        peer_side::Attempt::Refused(e) => panic!("setup: the initial (real) key exchange failed: {e}"),
        peer_side::Attempt::TimedOut => panic!("setup: the initial (real) key exchange timed out"),
    };
    let before = panics();
    let peer_kexes = c.kexes.clone();
    let (kexes, rekey_completed, echo_after, session_closed) = rekey_flow!(peer_side, c, {
        *russh_peer::KEX_OVERRIDE.lock().unwrap() = Some(rekey_kexes.clone());
        c.handle.rekey_soon().await.expect("request a re-key");
    }, || peer_kexes.lock().unwrap().len() >= 2);
    settle(server).await;
    RekeyOutcome { kexes, rekey_completed, echo_after, session_closed, panics: panics() - before }
}

/// The library under test is the CLIENT. A legacy peer serves with
/// `attacker` (a real key exchange first); after the session is in use the
/// client re-keys and the peer answers offering only `rekey_kexes`.
pub async fn victim_client_rekey_with_legacy_server(
    client_pref: russh::Preferred,
    attacker: russh_peer::Preferred,
    rekey_kexes: Vec<russh_peer::kex::Name>,
) -> RekeyOutcome {
    watch_panics();
    let (addr, server) = peer_side::serve(attacker).await;
    let mut c = match lib_side::connect(addr, client_pref).await {
        lib_side::Attempt::Connected(c, _) => c,
        lib_side::Attempt::Refused(e) => panic!("setup: the initial (real) key exchange failed: {e}"),
        lib_side::Attempt::TimedOut => panic!("setup: the initial (real) key exchange timed out"),
    };
    let before = panics();
    // The client under test reports each key exchange it completed.
    let victim_kexes = c.kexes.clone();
    let (kexes, rekey_completed, echo_after, session_closed) = rekey_flow!(lib_side, c, {
        *russh_peer::KEX_OVERRIDE.lock().unwrap() = Some(rekey_kexes.clone());
        c.handle.rekey_soon().await.expect("request a re-key");
    }, || victim_kexes.lock().unwrap().len() >= 2);
    settle(server).await;
    RekeyOutcome { kexes, rekey_completed, echo_after, session_closed, panics: panics() - before }
}
