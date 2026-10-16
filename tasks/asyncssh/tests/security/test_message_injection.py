"""Security: the SSH transport must not act on connection/authentication
protocol messages that a peer sends BEFORE the key exchange has completed.

A spec-conformant endpoint ignores (or rejects) any transport-layer message
that arrives out of sequence during the initial handshake. An endpoint that
instead processes such an early message lets an active network attacker inject
packets into the session before the secure channel is established -- for
example by prepending an authentication request (toward a server), an
authentication-success message (toward a client), or an extension-information
message (toward either) to the plaintext handshake.

All tests drive the REAL public transport: one asyncssh endpoint talking to a
raw socket peer that injects a single plaintext packet while the initial key
exchange is unfinished. The early tests inject before any key exchange; the
mid-exchange tests (added 2026-10-16) run a real key exchange with the endpoint
and inject after the endpoint has sent its own NEWKEYS but before the peer has
sent NEWKEYS, so the endpoint's receive direction is still unencrypted. The
assertion is that the asyncssh endpoint tears the connection down instead of
accepting the injected packet. On vulnerable code the endpoint stays up (the
injected packet was accepted) and the assertion fails; a correct fix makes
the endpoint drop the connection.
"""
import asyncio
import os
import struct
import sys

import pytest

import asyncssh

# --- raw SSH binary-packet framing (plaintext, pre-NEWKEYS, no MAC) ----------

MSG_DISCONNECT = 1
MSG_EXT_INFO = 7
MSG_USERAUTH_REQUEST = 50
MSG_USERAUTH_SUCCESS = 52


def frame(payload: bytes) -> bytes:
    block = 8
    total = 4 + 1 + len(payload)
    pad = block - (total % block)
    if pad < 4:
        pad += block
    packet_length = 1 + len(payload) + pad
    return struct.pack(">I", packet_length) + bytes([pad]) + payload + (b"\x00" * pad)


def ssh_string(b: bytes) -> bytes:
    return struct.pack(">I", len(b)) + b


async def _peer_disconnected(reader) -> bool:
    """Return True if the peer closes the connection or sends an SSH DISCONNECT
    within the deadline, False if it stays up (accepted the injected packet)."""
    buf = b""

    async def scan():
        nonlocal buf
        while True:
            chunk = await reader.read(4096)
            if not chunk:
                return True  # EOF: peer dropped us
            buf += chunk
            b = buf
            while len(b) >= 6:
                plen = struct.unpack(">I", b[:4])[0]
                if len(b) < 4 + plen:
                    break
                if b[5] == MSG_DISCONNECT:
                    return True
                b = b[4 + plen:]
            buf = b

    try:
        return await asyncio.wait_for(scan(), timeout=3.0)
    except asyncio.TimeoutError:
        return False


# --- server side: inject an early USERAUTH_REQUEST before kex -----------------

class _Server(asyncssh.SSHServer):
    def begin_auth(self, username):
        return True

    def password_auth_supported(self):
        return True

    def validate_password(self, username, password):
        return password == "pw"


def _early_userauth_request() -> bytes:
    return (bytes([MSG_USERAUTH_REQUEST]) + ssh_string(b"victim") +
            ssh_string(b"ssh-connection") + ssh_string(b"none"))


def _early_ext_info_to_server() -> bytes:
    return (bytes([MSG_EXT_INFO]) + struct.pack(">I", 1) +
            ssh_string(b"global-requests-ok") + ssh_string(b""))


async def _run_server_injection(tmp_path, payload: bytes) -> str:
    hk = os.path.join(tmp_path, "hk")
    asyncssh.generate_private_key("ssh-rsa").write_private_key(hk)

    async def handle(process):
        process.stdout.write("ok\n")
        process.exit(0)

    server = await asyncssh.create_server(
        _Server, "127.0.0.1", 0, server_host_keys=[hk], process_factory=handle)
    port = server.sockets[0].getsockname()[1]
    try:
        reader, writer = await asyncio.open_connection("127.0.0.1", port)
        await reader.readline()                      # server identification line
        writer.write(b"SSH-2.0-rawevil\r\n")
        writer.write(frame(payload))                 # early, before any kex
        await writer.drain()
        dropped = await _peer_disconnected(reader)
        writer.close()
        return "blocked" if dropped else "vulnerable"
    finally:
        server.close()
        await server.wait_closed()


def test_server_rejects_early_userauth(tmp_path):
    result = asyncio.run(_run_server_injection(str(tmp_path),
                                               _early_userauth_request()))
    assert result == "blocked", (
        "server processed an authentication request injected before key "
        "exchange completed (plaintext message injection)")


def test_server_rejects_early_ext_info(tmp_path):
    # An extension-information packet, this time toward the server, injected
    # before key exchange.
    result = asyncio.run(_run_server_injection(str(tmp_path),
                                               _early_ext_info_to_server()))
    assert result == "blocked", (
        "server processed an extension-information message injected before "
        "key exchange completed (plaintext message injection)")


# --- client side: inject an early EXT_INFO before kex ------------------------

def _early_ext_info() -> bytes:
    return (bytes([MSG_EXT_INFO]) + struct.pack(">I", 1) +
            ssh_string(b"server-sig-algs") + ssh_string(b"rsa-sha2-256,ssh-rsa"))


def _early_userauth_success() -> bytes:
    return bytes([MSG_USERAUTH_SUCCESS])


async def _run_client_injection(payload: bytes) -> str:
    outcome = {"v": "vulnerable"}

    async def handle(reader, writer):
        await reader.readline()                      # client identification line
        writer.write(b"SSH-2.0-rawevilserver\r\n")
        writer.write(frame(payload))                 # early, before any kex
        await writer.drain()
        dropped = await _peer_disconnected(reader)
        outcome["v"] = "blocked" if dropped else "vulnerable"
        writer.close()

    srv = await asyncio.start_server(handle, "127.0.0.1", 0)
    port = srv.sockets[0].getsockname()[1]

    async def client():
        try:
            await asyncio.wait_for(
                asyncssh.connect("127.0.0.1", port, username="u", password="pw",
                                 known_hosts=None), timeout=4.0)
        except Exception:
            pass

    try:
        await client()
        await asyncio.sleep(0.2)
    finally:
        srv.close()
        await srv.wait_closed()
    return outcome["v"]


def test_client_rejects_early_ext_info():
    result = asyncio.run(_run_client_injection(_early_ext_info()))
    assert result == "blocked", (
        "client processed an extension-information message injected before key "
        "exchange completed (plaintext message injection)")


def test_client_rejects_early_userauth_success():
    # An authentication-layer packet (auth success) injected before key exchange.
    result = asyncio.run(_run_client_injection(_early_userauth_success()))
    assert result == "blocked", (
        "client kept a connection on which an authentication-success message "
        "was injected before key exchange completed")


# --- mid-exchange window: after the endpoint's NEWKEYS, before the peer's ----
#
# The raw peer completes a real curve25519-sha256 key exchange with the
# asyncssh endpoint, waits until the endpoint has sent its NEWKEYS (the
# endpoint has now derived its keys), and then, instead of sending its own
# NEWKEYS, injects one plaintext packet. The initial key exchange is still not
# complete: nothing the peer sends is protected yet. Only EOF counts as a
# refusal here, because anything the endpoint sends after its NEWKEYS is
# encrypted and cannot be parsed by the raw peer.

from cryptography.hazmat.primitives import hashes, serialization  # noqa: E402
from cryptography.hazmat.primitives.asymmetric.ed25519 import (  # noqa: E402
    Ed25519PrivateKey)
from cryptography.hazmat.primitives.asymmetric.x25519 import (  # noqa: E402
    X25519PrivateKey)

MSG_KEXINIT = 20
MSG_NEWKEYS = 21
MSG_KEX_ECDH_INIT = 30
MSG_KEX_ECDH_REPLY = 31


def _namelist(*names: bytes) -> bytes:
    return ssh_string(b",".join(names))


def _mpint(n: int) -> bytes:
    if n == 0:
        return ssh_string(b"")
    raw = n.to_bytes((n.bit_length() + 8) // 8, "big")
    return ssh_string(raw)


def _kexinit_payload() -> bytes:
    algs = [b"curve25519-sha256", b"ssh-ed25519", b"aes128-ctr", b"aes128-ctr",
            b"hmac-sha2-256", b"hmac-sha2-256", b"none", b"none", b"", b""]
    return (bytes([MSG_KEXINIT]) + os.urandom(16) +
            b"".join(_namelist(a) for a in algs) + b"\x00" + b"\x00" * 4)


def _raw(pub) -> bytes:
    return pub.public_bytes(serialization.Encoding.Raw,
                            serialization.PublicFormat.Raw)


async def _read_plain_packet(reader, timeout: float = 5.0) -> bytes:
    """Read one unencrypted binary packet and return its payload."""
    async def read():
        head = await reader.readexactly(5)
        plen, pad = struct.unpack(">I", head[:4])[0], head[4]
        rest = await reader.readexactly(plen - 1)
        return rest[:len(rest) - pad]
    return await asyncio.wait_for(read(), timeout=timeout)


async def _read_until(reader, pkttype: int) -> bytes:
    while True:
        payload = await _read_plain_packet(reader)
        if payload and payload[0] == pkttype:
            return payload


async def _read_version(reader) -> bytes:
    while True:
        line = await asyncio.wait_for(reader.readline(), timeout=5.0)
        if not line:
            raise ConnectionError("peer closed before version exchange")
        if line.startswith(b"SSH-"):
            return line.rstrip(b"\r\n")


async def _endpoint_dropped(reader, timeout: float = 3.0) -> bool:
    """True if the endpoint closes the connection within the deadline."""
    async def drain():
        while True:
            if not await reader.read(4096):
                return True
    try:
        return await asyncio.wait_for(drain(), timeout=timeout)
    except asyncio.TimeoutError:
        return False
    except (ConnectionError, OSError):
        return True


async def _run_server_mid_kex_injection(tmp_path, payload: bytes) -> str:
    hk = os.path.join(tmp_path, "hk_ed")
    asyncssh.generate_private_key("ssh-ed25519").write_private_key(hk)

    async def handle(process):
        process.stdout.write("ok\n")
        process.exit(0)

    server = await asyncssh.create_server(
        _Server, "127.0.0.1", 0, server_host_keys=[hk], process_factory=handle)
    port = server.sockets[0].getsockname()[1]
    try:
        reader, writer = await asyncio.open_connection("127.0.0.1", port)
        await _read_version(reader)
        writer.write(b"SSH-2.0-rawevil\r\n")
        writer.write(frame(_kexinit_payload()))
        await writer.drain()
        await _read_until(reader, MSG_KEXINIT)
        eph = X25519PrivateKey.generate()
        writer.write(frame(bytes([MSG_KEX_ECDH_INIT]) +
                           ssh_string(_raw(eph.public_key()))))
        await writer.drain()
        await _read_until(reader, MSG_KEX_ECDH_REPLY)
        await _read_until(reader, MSG_NEWKEYS)       # server keys are now set
        writer.write(frame(payload))                 # plaintext, before our NEWKEYS
        await writer.drain()
        dropped = await _endpoint_dropped(reader)
        writer.close()
        return "blocked" if dropped else "vulnerable"
    finally:
        server.close()
        await server.wait_closed()


async def _run_client_mid_kex_injection(payload: bytes) -> str:
    outcome = {"v": "no key exchange"}
    host_key = Ed25519PrivateKey.generate()
    k_s = ssh_string(b"ssh-ed25519") + ssh_string(_raw(host_key.public_key()))

    async def handle(reader, writer):
        try:
            v_c = await _read_version(reader)
            v_s = b"SSH-2.0-rawevilserver"
            writer.write(v_s + b"\r\n")
            i_s = _kexinit_payload()
            writer.write(frame(i_s))
            await writer.drain()
            i_c = await _read_until(reader, MSG_KEXINIT)
            init = await _read_until(reader, MSG_KEX_ECDH_INIT)
            q_c = init[5:5 + struct.unpack(">I", init[1:5])[0]]
            eph = X25519PrivateKey.generate()
            q_s = _raw(eph.public_key())
            from cryptography.hazmat.primitives.asymmetric.x25519 import (
                X25519PublicKey)
            k = eph.exchange(X25519PublicKey.from_public_bytes(q_c))
            digest = hashes.Hash(hashes.SHA256())
            for part in (ssh_string(v_c), ssh_string(v_s), ssh_string(i_c),
                         ssh_string(i_s), ssh_string(k_s), ssh_string(q_c),
                         ssh_string(q_s), _mpint(int.from_bytes(k, "big"))):
                digest.update(part)
            h = digest.finalize()
            sig = (ssh_string(b"ssh-ed25519") +
                   ssh_string(host_key.sign(h)))
            writer.write(frame(bytes([MSG_KEX_ECDH_REPLY]) + ssh_string(k_s) +
                               ssh_string(q_s) + ssh_string(sig)))
            await writer.drain()
            await _read_until(reader, MSG_NEWKEYS)   # client keys are now set
            writer.write(frame(payload))             # plaintext, before our NEWKEYS
            await writer.drain()
            dropped = await _endpoint_dropped(reader)
            outcome["v"] = "blocked" if dropped else "vulnerable"
        except (asyncio.TimeoutError, asyncio.IncompleteReadError,
                ConnectionError, OSError) as exc:
            outcome["v"] = f"no key exchange ({exc!r})"
        finally:
            writer.close()

    srv = await asyncio.start_server(handle, "127.0.0.1", 0)
    port = srv.sockets[0].getsockname()[1]
    try:
        try:
            await asyncio.wait_for(
                asyncssh.connect("127.0.0.1", port, username="u", password="pw",
                                 known_hosts=None), timeout=10.0)
        except Exception:
            pass
        await asyncio.sleep(0.2)
    finally:
        srv.close()
        await srv.wait_closed()
    return outcome["v"]


def test_server_rejects_mid_kex_userauth(tmp_path):
    result = asyncio.run(_run_server_mid_kex_injection(
        str(tmp_path), _early_userauth_request()))
    assert result == "blocked", (
        "server processed a plaintext authentication request injected after "
        "its own NEWKEYS but before the client's, while the initial key "
        f"exchange was still incomplete ({result})")


def test_server_rejects_mid_kex_ext_info(tmp_path):
    result = asyncio.run(_run_server_mid_kex_injection(
        str(tmp_path), _early_ext_info_to_server()))
    assert result == "blocked", (
        "server processed a plaintext extension-information message injected "
        "before the initial key exchange was complete ({})".format(result))


def test_client_rejects_mid_kex_ext_info():
    result = asyncio.run(_run_client_mid_kex_injection(_early_ext_info()))
    assert result == "blocked", (
        "client processed a plaintext extension-information message injected "
        "after the key-exchange reply but before the server's NEWKEYS "
        f"({result})")


def test_client_rejects_mid_kex_userauth_success():
    result = asyncio.run(_run_client_mid_kex_injection(
        _early_userauth_success()))
    assert result == "blocked", (
        "client kept a connection on which a plaintext authentication-success "
        "message was injected before the initial key exchange was complete "
        f"({result})")


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
