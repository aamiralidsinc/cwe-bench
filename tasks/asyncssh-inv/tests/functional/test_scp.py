"""Functional: a legitimate SCP download must keep working.

The file name here is ordinary (no traversal) and includes a dot, like most
real file names. This protects against a fix that blocks the traversal by
over-restricting legitimate file names (for example rejecting any name
containing '.'), which would break normal downloads.
"""
import asyncio
import os

import pytest

import asyncssh

CONTENT = "quarterly report contents\n"


class _Server(asyncssh.SSHServer):
    def begin_auth(self, username):
        return True

    def password_auth_supported(self):
        return True

    def validate_password(self, username, password):
        return password == "pw"


async def _download(tmp_path) -> str:
    base = str(tmp_path)
    srv_root = os.path.join(base, "srv")
    os.makedirs(srv_root, exist_ok=True)
    with open(os.path.join(srv_root, "report.txt"), "w") as f:
        f.write(CONTENT)
    dst = os.path.join(base, "dl")
    os.makedirs(dst, exist_ok=True)

    hk = os.path.join(base, "hk")
    asyncssh.generate_private_key("ssh-rsa").write_private_key(hk)

    server = await asyncssh.create_server(
        _Server, "127.0.0.1", 0, server_host_keys=[hk],
        sftp_factory=lambda chan: asyncssh.SFTPServer(chan, chroot=srv_root),
        allow_scp=True)
    port = server.sockets[0].getsockname()[1]
    try:
        async with asyncssh.connect("127.0.0.1", port, username="u",
                                    password="pw", known_hosts=None) as conn:
            await asyncssh.scp((conn, "/report.txt"), dst)
    finally:
        server.close()
        await server.wait_closed()

    with open(os.path.join(dst, "report.txt")) as f:
        return f.read()


def test_legit_scp_download(tmp_path):
    assert asyncio.run(_download(str(tmp_path))) == CONTENT


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
