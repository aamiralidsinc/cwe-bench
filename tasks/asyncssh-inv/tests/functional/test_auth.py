"""Functional: ordinary authentication must keep working.

These protect the affected features against an over-broad fix: password login
must still succeed, and the per-user authorized-keys lookup (the same mechanism
the traversal test abuses) must still authenticate a legitimate user whose name
maps to their own key directory.
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


async def _password_login(tmp_path) -> str:
    hk = os.path.join(tmp_path, "hk")
    asyncssh.generate_private_key("ssh-rsa").write_private_key(hk)

    async def handle(process):
        process.stdout.write("hello\n")
        process.exit(0)

    server = await asyncssh.create_server(
        _Server, "127.0.0.1", 0, server_host_keys=[hk], process_factory=handle)
    port = server.sockets[0].getsockname()[1]
    try:
        async with asyncssh.connect("127.0.0.1", port, username="alice",
                                    password="pw", known_hosts=None) as conn:
            result = await conn.run("whoami")
            return result.stdout.strip()
    finally:
        server.close()
        await server.wait_closed()


def test_password_login(tmp_path):
    assert asyncio.run(_password_login(str(tmp_path))) == "hello"


async def _pubkey_login(tmp_path) -> bool:
    base = str(tmp_path)
    os.makedirs(os.path.join(base, "keys", "alice"), exist_ok=True)

    hk = os.path.join(base, "hk")
    asyncssh.generate_private_key("ssh-rsa").write_private_key(hk)

    user_key = asyncssh.generate_private_key("ssh-rsa")
    user_key.write_private_key(os.path.join(base, "alice_id"))
    with open(os.path.join(base, "keys", "alice", "authorized_keys"), "wb") as f:
        f.write(user_key.export_public_key())

    cfg = os.path.join(base, "sshd_config")
    with open(cfg, "w") as f:
        f.write("AuthorizedKeysFile %s/keys/%%u/authorized_keys\n" % base)

    server = await asyncssh.create_server(
        asyncssh.SSHServer, "127.0.0.1", 0, server_host_keys=[hk], config=[cfg])
    port = server.sockets[0].getsockname()[1]
    try:
        async with asyncssh.connect(
                "127.0.0.1", port, username="alice",
                client_keys=[os.path.join(base, "alice_id")],
                known_hosts=None):
            return True
    finally:
        server.close()
        await server.wait_closed()


def test_per_user_pubkey_login(tmp_path):
    assert asyncio.run(_pubkey_login(str(tmp_path))) is True


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
