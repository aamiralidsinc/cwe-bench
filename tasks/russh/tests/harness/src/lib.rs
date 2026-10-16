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
    /// The client gave no answer at all within the time limit (hang).
    pub timed_out: bool,
    /// The client's error, if the handshake failed with one.
    pub client_error: Option<String>,
    /// The client's or the server's connection task panicked.
    pub panicked: bool,
}

fn is_panic(e: &russh::Error) -> bool {
    matches!(e, russh::Error::Join(_))
}

/// Attempt only the transport handshake: client connects, we capture the
/// negotiated algorithms, then disconnect. Returns whether it connected.
pub async fn negotiate(client_pref: Preferred, server_pref: Preferred) -> Outcome {
    let server_config = mk_server_config(server_pref);
    let client_config = mk_client_config(client_pref);

    let listener = tokio::net::TcpListener::bind("127.0.0.1:0").await.unwrap();
    let addr = listener.local_addr().unwrap();

    // The server task reports whether its connection task panicked.
    let server_task = tokio::spawn(async move {
        if let Ok((socket, _)) = listener.accept().await {
            match server::run_stream(server_config, socket, TestServer).await {
                Ok(running) => matches!(running.await, Err(ref e) if is_panic(e)),
                Err(ref e) => is_panic(e),
            }
        } else {
            false
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

    let mut out = Outcome {
        connected: false,
        names: None,
        timed_out: false,
        client_error: None,
        panicked: false,
    };
    match connect {
        Ok(Ok(mut session)) => {
            out.connected = true;
            out.names = names.lock().unwrap().clone();
            let _ = session
                .disconnect(Disconnect::ByApplication, "", "")
                .await;
        }
        Ok(Err(e)) => {
            out.panicked |= is_panic(&e);
            out.client_error = Some(format!("{e:?}"));
        }
        Err(_) => out.timed_out = true,
    }
    if !out.connected {
        // A refused handshake ends the server's connection too; collect it.
        match tokio::time::timeout(Duration::from_secs(5), server_task).await {
            Ok(Ok(server_panicked)) => out.panicked |= server_panicked,
            Ok(Err(join)) => out.panicked |= join.is_panic(),
            Err(_) => {}
        }
    }
    out
}

/// Security assertion for a handshake that must be refused: it must fail
/// promptly with an error (no session, no hang until the time limit, no
/// panicking connection task on either side).
pub fn assert_refused(out: &Outcome, what: &str) {
    assert!(
        !out.connected,
        "{what} must not establish a session; negotiated {:?}",
        out.names.as_ref().map(|n| (
            n.cipher.as_ref().to_string(),
            n.client_mac.as_ref().to_string(),
            n.server_mac.as_ref().to_string()
        ))
    );
    assert!(
        !out.timed_out,
        "{what}: the handshake must be refused with an error, but it hung until the time limit"
    );
    assert!(
        !out.panicked,
        "{what}: a connection task panicked instead of refusing cleanly ({:?})",
        out.client_error
    );
    assert!(
        out.client_error.is_some(),
        "{what}: the handshake must end with an error"
    );
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

/// A raw SSH peer that speaks the transport protocol directly (it does not run
/// this library's negotiation). It sends a KEXINIT with exactly the algorithm
/// lists the test chooses and then completes a genuine curve25519-sha256 key
/// exchange, so the library under test is the only side that can refuse.
pub mod raw {
    use std::io;

    use russh::keys::signature::Signer;
    use russh::keys::ssh_encoding::Encode;
    use russh::keys::HashAlg;
    use tokio::io::{AsyncReadExt, AsyncWriteExt};
    use tokio::net::TcpStream;

    use super::*;

    const MSG_DISCONNECT: u8 = 1;
    const MSG_KEXINIT: u8 = 20;
    const MSG_NEWKEYS: u8 = 21;
    const MSG_KEX_ECDH_INIT: u8 = 30;
    const MSG_KEX_ECDH_REPLY: u8 = 31;
    const RAW_ID: &[u8] = b"SSH-2.0-RawPeer_1.0";

    /// Algorithms the raw peer offers (one name per list).
    #[derive(Clone, Copy, Debug)]
    pub struct Offer {
        pub cipher: &'static str,
        pub mac_client_to_server: &'static str,
        pub mac_server_to_client: &'static str,
    }

    impl Offer {
        pub fn new(cipher: &'static str, mac: &'static str) -> Self {
            Offer {
                cipher,
                mac_client_to_server: mac,
                mac_server_to_client: mac,
            }
        }
    }

    /// What the library under test (the victim) did with the raw peer's offer.
    #[derive(Debug, PartialEq, Eq)]
    pub enum Verdict {
        /// The key exchange completed and the session is up.
        Established,
        /// The victim aborted the handshake with an error of its own.
        Refused(String),
        /// The victim's connection task panicked.
        Panicked(String),
        /// The victim ended the connection without reporting any error.
        EndedWithoutError,
        /// The victim neither completed nor refused within the time limit.
        Stalled,
    }

    // ---- wire helpers ------------------------------------------------------

    fn put_string(buf: &mut Vec<u8>, s: &[u8]) {
        buf.extend_from_slice(&(s.len() as u32).to_be_bytes());
        buf.extend_from_slice(s);
    }

    fn put_name_list(buf: &mut Vec<u8>, names: &[&str]) {
        put_string(buf, names.join(",").as_bytes());
    }

    fn put_mpint(buf: &mut Vec<u8>, s: &[u8]) {
        let mut i = 0;
        while i < s.len() && s[i] == 0 {
            i += 1;
        }
        let digits = &s[i..];
        if digits.first().is_some_and(|b| b & 0x80 != 0) {
            buf.extend_from_slice(&((digits.len() + 1) as u32).to_be_bytes());
            buf.push(0);
        } else {
            buf.extend_from_slice(&(digits.len() as u32).to_be_bytes());
        }
        buf.extend_from_slice(digits);
    }

    fn get_string(p: &[u8]) -> Option<&[u8]> {
        let len = u32::from_be_bytes(p.get(..4)?.try_into().ok()?) as usize;
        p.get(4..4 + len)
    }

    fn kexinit(offer: &Offer) -> Vec<u8> {
        let mut p = vec![MSG_KEXINIT];
        p.extend_from_slice(&[0x5a; 16]); // cookie
        put_name_list(&mut p, &["curve25519-sha256"]);
        put_name_list(&mut p, &["ssh-ed25519"]);
        put_name_list(&mut p, &[offer.cipher]);
        put_name_list(&mut p, &[offer.cipher]);
        put_name_list(&mut p, &[offer.mac_client_to_server]);
        put_name_list(&mut p, &[offer.mac_server_to_client]);
        put_name_list(&mut p, &["none"]);
        put_name_list(&mut p, &["none"]);
        put_name_list(&mut p, &[]);
        put_name_list(&mut p, &[]);
        p.push(0); // first_kex_packet_follows
        p.extend_from_slice(&0u32.to_be_bytes());
        p
    }

    async fn send_packet(s: &mut TcpStream, payload: &[u8]) -> io::Result<()> {
        let mut padding = 8 - ((5 + payload.len()) % 8);
        if padding < 4 {
            padding += 8;
        }
        let mut pkt = Vec::with_capacity(5 + payload.len() + padding);
        pkt.extend_from_slice(&((1 + payload.len() + padding) as u32).to_be_bytes());
        pkt.push(padding as u8);
        pkt.extend_from_slice(payload);
        pkt.resize(pkt.len() + padding, 0);
        s.write_all(&pkt).await?;
        s.flush().await
    }

    /// Read one unencrypted binary packet and return its payload.
    async fn read_packet(s: &mut TcpStream) -> io::Result<Vec<u8>> {
        let mut len = [0u8; 4];
        s.read_exact(&mut len).await?;
        let len = u32::from_be_bytes(len) as usize;
        if !(5..=256 * 1024).contains(&len) {
            return Err(io::Error::other("bad packet length"));
        }
        let mut pkt = vec![0u8; len];
        s.read_exact(&mut pkt).await?;
        let padding = pkt[0] as usize;
        if padding + 1 > len {
            return Err(io::Error::other("bad padding"));
        }
        Ok(pkt[1..len - padding].to_vec())
    }

    /// Read the peer's identification line (without CR LF).
    async fn read_id(s: &mut TcpStream) -> io::Result<Vec<u8>> {
        loop {
            let mut line = Vec::new();
            loop {
                let mut b = [0u8];
                s.read_exact(&mut b).await?;
                if b[0] == b'\n' {
                    break;
                }
                line.push(b[0]);
                if line.len() > 512 {
                    return Err(io::Error::other("id line too long"));
                }
            }
            if line.last() == Some(&b'\r') {
                line.pop();
            }
            if line.starts_with(b"SSH-") {
                return Ok(line);
            }
        }
    }

    /// Next packet of one of the wanted types; None if the peer disconnected.
    async fn expect(s: &mut TcpStream, want: u8) -> io::Result<Option<Vec<u8>>> {
        loop {
            let p = read_packet(s).await?;
            match p.first() {
                Some(&t) if t == want => return Ok(Some(p)),
                Some(&MSG_DISCONNECT) => return Ok(None),
                _ => continue, // IGNORE, DEBUG, EXT_INFO, ...
            }
        }
    }

    // ---- X25519 (RFC 7748), field arithmetic in 16 limbs of 16 bits -------

    type Gf = [i64; 16];

    fn carry(o: &mut Gf) {
        for i in 0..16 {
            o[i] += 1 << 16;
            let c = o[i] >> 16;
            if i < 15 {
                o[i + 1] += c - 1;
            } else {
                o[0] += 38 * (c - 1);
            }
            o[i] -= c << 16;
        }
    }

    fn select(p: &mut Gf, q: &mut Gf, b: i64) {
        let c = !(b - 1);
        for i in 0..16 {
            let t = c & (p[i] ^ q[i]);
            p[i] ^= t;
            q[i] ^= t;
        }
    }

    fn pack(n: &Gf) -> [u8; 32] {
        let mut t = *n;
        carry(&mut t);
        carry(&mut t);
        carry(&mut t);
        for _ in 0..2 {
            let mut m: Gf = [0; 16];
            m[0] = t[0] - 0xffed;
            for i in 1..15 {
                m[i] = t[i] - 0xffff - ((m[i - 1] >> 16) & 1);
                m[i - 1] &= 0xffff;
            }
            m[15] = t[15] - 0x7fff - ((m[14] >> 16) & 1);
            let b = (m[15] >> 16) & 1;
            m[14] &= 0xffff;
            select(&mut t, &mut m, 1 - b);
        }
        let mut o = [0u8; 32];
        for i in 0..16 {
            o[2 * i] = (t[i] & 0xff) as u8;
            o[2 * i + 1] = (t[i] >> 8) as u8;
        }
        o
    }

    fn unpack(n: &[u8; 32]) -> Gf {
        let mut o: Gf = [0; 16];
        for i in 0..16 {
            o[i] = n[2 * i] as i64 + ((n[2 * i + 1] as i64) << 8);
        }
        o[15] &= 0x7fff;
        o
    }

    fn add(a: &Gf, b: &Gf) -> Gf {
        let mut o = [0; 16];
        for i in 0..16 {
            o[i] = a[i] + b[i];
        }
        o
    }

    fn sub(a: &Gf, b: &Gf) -> Gf {
        let mut o = [0; 16];
        for i in 0..16 {
            o[i] = a[i] - b[i];
        }
        o
    }

    fn mul(a: &Gf, b: &Gf) -> Gf {
        let mut t = [0i64; 31];
        for i in 0..16 {
            for j in 0..16 {
                t[i + j] += a[i] * b[j];
            }
        }
        for i in 0..15 {
            t[i] += 38 * t[i + 16];
        }
        let mut o: Gf = [0; 16];
        o.copy_from_slice(&t[..16]);
        carry(&mut o);
        carry(&mut o);
        o
    }

    fn inv(i: &Gf) -> Gf {
        let mut c = *i;
        for a in (0..=253).rev() {
            c = mul(&c, &c);
            if a != 2 && a != 4 {
                c = mul(&c, i);
            }
        }
        c
    }

    /// X25519(scalar, u-coordinate).
    pub fn x25519(scalar: &[u8; 32], point: &[u8; 32]) -> [u8; 32] {
        let mut z = *scalar;
        z[31] = (z[31] & 127) | 64;
        z[0] &= 248;
        let x = unpack(point);
        let k121665: Gf = [0xdb41, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0];
        let mut a: Gf = [0; 16];
        let mut b = x;
        let mut c: Gf = [0; 16];
        let mut d: Gf = [0; 16];
        a[0] = 1;
        d[0] = 1;
        for i in (0..=254).rev() {
            let r = ((z[i >> 3] >> (i & 7)) & 1) as i64;
            select(&mut a, &mut b, r);
            select(&mut c, &mut d, r);
            let mut e = add(&a, &c);
            a = sub(&a, &c);
            c = add(&b, &d);
            b = sub(&b, &d);
            d = mul(&e, &e);
            let f = mul(&a, &a);
            a = mul(&c, &a);
            c = mul(&b, &e);
            e = add(&a, &c);
            a = sub(&a, &c);
            b = mul(&a, &a);
            c = sub(&d, &f);
            a = mul(&c, &k121665);
            a = add(&a, &d);
            c = mul(&c, &a);
            a = mul(&d, &f);
            d = mul(&b, &x);
            b = mul(&e, &e);
            select(&mut a, &mut b, r);
            select(&mut c, &mut d, r);
        }
        pack(&mul(&a, &inv(&c)))
    }

    const BASE: [u8; 32] = {
        let mut b = [0u8; 32];
        b[0] = 9;
        b
    };

    // ---- raw client against the library's server ---------------------------

    /// Returns Ok(true) once the full key exchange completed (both NEWKEYS),
    /// Ok(false) if the server sent DISCONNECT, Err on a closed socket.
    async fn drive_raw_client(s: &mut TcpStream, offer: &Offer) -> io::Result<bool> {
        let secret = [0x77u8; 32];
        let mut id = RAW_ID.to_vec();
        id.extend_from_slice(b"\r\n");
        s.write_all(&id).await?;
        read_id(s).await?;
        if expect(s, MSG_KEXINIT).await?.is_none() {
            return Ok(false);
        }
        send_packet(s, &kexinit(offer)).await?;
        let mut init = vec![MSG_KEX_ECDH_INIT];
        put_string(&mut init, &x25519(&secret, &BASE));
        send_packet(s, &init).await?;
        if expect(s, MSG_KEX_ECDH_REPLY).await?.is_none() {
            return Ok(false);
        }
        if expect(s, MSG_NEWKEYS).await?.is_none() {
            return Ok(false);
        }
        send_packet(s, &[MSG_NEWKEYS]).await?;
        Ok(true)
    }

    /// A raw client offers `offer` to a server built on the library and runs
    /// the key exchange to completion. The raw client never hangs up by
    /// itself, so the server either keeps serving (Established) or ends the
    /// connection on its own.
    pub async fn client_offer_to_server(server_pref: Preferred, offer: Offer) -> Verdict {
        let server_config = mk_server_config(server_pref);
        let listener = tokio::net::TcpListener::bind("127.0.0.1:0").await.unwrap();
        let addr = listener.local_addr().unwrap();
        let mut server_task = tokio::spawn(async move {
            let (socket, _) = listener.accept().await.unwrap();
            let running = server::run_stream(server_config, socket, TestServer).await?;
            running.await
        });

        let mut s = TcpStream::connect(addr).await.unwrap();
        let completed = matches!(
            tokio::time::timeout(Duration::from_secs(10), drive_raw_client(&mut s, &offer)).await,
            Ok(Ok(true))
        );
        // Keep the socket open while waiting: the server must end it itself.
        let res = tokio::time::timeout(Duration::from_secs(4), &mut server_task).await;
        drop(s);
        match res {
            Err(_) => {
                server_task.abort();
                if completed {
                    Verdict::Established
                } else {
                    Verdict::Stalled
                }
            }
            Ok(Err(join)) => Verdict::Panicked(format!("{join:?}")),
            Ok(Ok(Err(e))) if is_panic(&e) => Verdict::Panicked(format!("{e:?}")),
            Ok(Ok(Err(e))) => Verdict::Refused(format!("{e:?}")),
            Ok(Ok(Ok(()))) => Verdict::EndedWithoutError,
        }
    }

    // ---- raw server against the library's client ---------------------------

    async fn drive_raw_server(
        s: &mut TcpStream,
        offer: &Offer,
        host_key: &PrivateKey,
    ) -> io::Result<()> {
        let secret = [0x5du8; 32];
        let mut id = RAW_ID.to_vec();
        id.extend_from_slice(b"\r\n");
        s.write_all(&id).await?;
        let v_c = read_id(s).await?;
        let Some(i_c) = expect(s, MSG_KEXINIT).await? else {
            return Ok(());
        };
        let i_s = kexinit(offer);
        send_packet(s, &i_s).await?;
        let Some(init) = expect(s, MSG_KEX_ECDH_INIT).await? else {
            return Ok(());
        };
        let q_c: [u8; 32] = get_string(&init[1..])
            .and_then(|q| q.try_into().ok())
            .ok_or_else(|| io::Error::other("bad KEX_ECDH_INIT"))?;
        let q_s = x25519(&secret, &BASE);
        let k = x25519(&secret, &q_c);
        let k_s = host_key.public_key().to_bytes().map_err(io::Error::other)?;

        let mut h = Vec::new();
        put_string(&mut h, &v_c);
        put_string(&mut h, RAW_ID);
        put_string(&mut h, &i_c);
        put_string(&mut h, &i_s);
        put_string(&mut h, &k_s);
        put_string(&mut h, &q_c);
        put_string(&mut h, &q_s);
        put_mpint(&mut h, &k);
        let hash = HashAlg::Sha256.digest(&h);
        let sig: ssh_key::Signature = host_key.try_sign(&hash).map_err(io::Error::other)?;
        let sig_blob = sig.encode_vec().map_err(io::Error::other)?;

        let mut reply = vec![MSG_KEX_ECDH_REPLY];
        put_string(&mut reply, &k_s);
        put_string(&mut reply, &q_s);
        put_string(&mut reply, &sig_blob);
        send_packet(s, &reply).await?;
        send_packet(s, &[MSG_NEWKEYS]).await?;
        Ok(())
    }

    /// A raw server offers `offer` to a client built on the library and runs
    /// the key exchange to completion. The verdict is the client's: whether
    /// `client::connect` comes back with a session or with an error.
    pub async fn server_offer_to_client(client_pref: Preferred, offer: Offer) -> Verdict {
        let listener = tokio::net::TcpListener::bind("127.0.0.1:0").await.unwrap();
        let addr = listener.local_addr().unwrap();
        let host_key = PrivateKey::random(&mut rand::rng(), ssh_key::Algorithm::Ed25519).unwrap();
        let raw_server = tokio::spawn(async move {
            let (mut s, _) = listener.accept().await.unwrap();
            let _ = drive_raw_server(&mut s, &offer, &host_key).await;
            // Never hang up first: hold the connection until the client does.
            let mut buf = [0u8; 4096];
            while let Ok(n) = s.read(&mut buf).await {
                if n == 0 {
                    break;
                }
            }
        });

        let names = Arc::new(Mutex::new(None));
        let handler = TestClient { names };
        let res = tokio::time::timeout(
            Duration::from_secs(20),
            client::connect(mk_client_config(client_pref), addr, handler),
        )
        .await;
        let verdict = match res {
            Err(_) => Verdict::Stalled,
            Ok(Ok(mut session)) => {
                let _ = session
                    .disconnect(Disconnect::ByApplication, "", "")
                    .await;
                Verdict::Established
            }
            Ok(Err(e)) if is_panic(&e) => Verdict::Panicked(format!("{e:?}")),
            Ok(Err(e)) => Verdict::Refused(format!("{e:?}")),
        };
        raw_server.abort();
        verdict
    }
}
