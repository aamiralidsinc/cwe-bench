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
raw socket peer that injects a single early packet before any key exchange.
The assertion is that the asyncssh endpoint tears the connection down instead
of accepting the injected packet. On vulnerable code the endpoint stays up
(the injected packet was accepted) and the assertion fails; a correct fix makes
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


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
