"""Functional: ordinary session data transfer must keep working.

A command round-trip exercises normal channel data at the default packet size;
the large-output case forces data to be split across many channel-data packets.
Together they protect against a packet-size fix that is too aggressive (e.g. one
that rejects or mangles normal, positive packet sizes) and against a handshake
fix that breaks legitimate post-key-exchange traffic.
"""
import asyncio
import os

import pytest

import asyncssh


class _Server(asyncssh.SSHServer):
    def begin_auth(self, username):
        return True

    def password_auth_supported(self):
        return True

    def validate_password(self, username, password):
        return password == "pw"


async def _serve_and_run(tmp_path, command, output):
    hk = os.path.join(tmp_path, "hk")
    asyncssh.generate_private_key("ssh-rsa").write_private_key(hk)

    async def handle(process):
        process.stdout.write(output)
        process.exit(0)

    server = await asyncssh.create_server(
        _Server, "127.0.0.1", 0, server_host_keys=[hk], process_factory=handle)
    port = server.sockets[0].getsockname()[1]
    try:
        async with asyncssh.connect("127.0.0.1", port, username="u",
                                    password="pw", known_hosts=None) as conn:
            result = await conn.run(command)
            return result.exit_status, result.stdout
    finally:
        server.close()
        await server.wait_closed()


def test_command_roundtrip(tmp_path):
    status, stdout = asyncio.run(
        _serve_and_run(str(tmp_path), "echo", "the quick brown fox\n"))
    assert status == 0
    assert stdout == "the quick brown fox\n"


def test_large_output_multiple_packets(tmp_path):
    # ~256 KiB forces the output across many channel-data packets (default max
    # packet size is 32 KiB), exercising normal packet-size chunking.
    payload = ("abcdefghij" * 100 + "\n") * 256
    status, stdout = asyncio.run(
        _serve_and_run(str(tmp_path), "cat", payload))
    assert status == 0
    assert stdout == payload
    assert len(stdout) > 200000


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
