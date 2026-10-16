"""Security: an SCP client receiving files must not let the remote peer write
outside the local destination directory.

In the SCP protocol the sending side names each file in a copy record. The
receiving client joins that name onto the destination directory to decide where
to write. A malicious or compromised server can put path-traversal segments in
the name; if the client does not reject them, the server can place a file at an
arbitrary location on the client's filesystem (outside the directory the user
asked to download into).

This drives the REAL public client API over loopback: asyncssh's scp() download
against a server whose transfer stream is crafted to name a file with a leading
traversal segment, an absolute path, or an embedded traversal segment. The assertion is that nothing is written outside the chosen
destination directory. On vulnerable code the file escapes the destination
(assertion fails); a correct fix rejects the escaping file name.
"""
import asyncio
import os

import pytest

import asyncssh

MAL_NAME = b"../escaped_evil"
DATA = b"PWNED-SCP"


class _Server(asyncssh.SSHServer):
    def begin_auth(self, username):
        return True

    def password_auth_supported(self):
        return True

    def validate_password(self, username, password):
        return password == "pw"


async def _attempt(tmp_path, mal_name=None, escaped_rel="escaped_evil") -> bool:
    """Download from a malicious SCP source that names its file ``mal_name``
    (default ``MAL_NAME``) and report whether ``<base>/<escaped_rel>`` -- a
    path outside the destination directory -- was written."""
    base = str(tmp_path)
    dst = os.path.join(base, "dst")
    os.makedirs(dst, exist_ok=True)
    # An ordinary subdirectory already present in the destination.
    os.makedirs(os.path.join(dst, "sub"), exist_ok=True)
    escaped = os.path.join(base, escaped_rel)
    if mal_name is None:
        mal_name = MAL_NAME                        # == dst/../escaped_evil
    elif callable(mal_name):
        mal_name = mal_name(base)

    hk = os.path.join(base, "hk")
    asyncssh.generate_private_key("ssh-rsa").write_private_key(hk)

    async def malicious_source(process):
        # Act as an SCP source and emit a copy record whose name escapes the
        # destination directory, following the protocol's OK handshaking.
        stdin, stdout = process.stdin, process.stdout
        try:
            await stdin.readexactly(1)                       # sink ready (OK)
            stdout.write(b"C0644 %d %s\n" % (len(DATA), mal_name))
            await stdin.readexactly(1)                       # OK for the record
            stdout.write(DATA)                               # file data
            stdout.write(b"\x00")                            # end-of-file OK
            await stdin.readexactly(1)                       # final OK
        except Exception:
            pass
        process.exit(0)

    server = await asyncssh.create_server(
        _Server, "127.0.0.1", 0, server_host_keys=[hk],
        process_factory=malicious_source, encoding=None)
    port = server.sockets[0].getsockname()[1]

    try:
        async with asyncssh.connect("127.0.0.1", port, username="u",
                                    password="pw", known_hosts=None) as conn:
            try:
                await asyncssh.scp((conn, "anything"), dst)
            except Exception:
                # A correct fix raises on the bad name; that is fine. What
                # matters is whether a file escaped the destination.
                pass
    finally:
        server.close()
        await server.wait_closed()

    return os.path.exists(escaped)


def test_scp_download_path_traversal(tmp_path):
    escaped = asyncio.run(_attempt(tmp_path))
    assert not escaped, (
        "an SCP download wrote a file outside the destination directory via a "
        "traversing file name supplied by the remote peer")



def test_scp_download_absolute_path(tmp_path):
    # The remote peer names the file with an absolute path outside dst.
    escaped = asyncio.run(_attempt(
        tmp_path,
        lambda base: os.path.join(base, "abs_escaped").encode(),
        "abs_escaped"))
    assert not escaped, (
        "an SCP download wrote a file at an absolute path supplied by the "
        "remote peer, outside the destination directory")


def test_scp_download_embedded_traversal(tmp_path):
    # The traversal is not leading: 'sub/../../x' walks out through an
    # existing subdirectory of the destination.
    escaped = asyncio.run(_attempt(
        tmp_path, b"sub/../../embedded_escaped", "embedded_escaped"))
    assert not escaped, (
        "an SCP download wrote a file outside the destination directory via "
        "a file name with an embedded traversal segment")


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
