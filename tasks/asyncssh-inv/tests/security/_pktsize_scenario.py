"""Helper process for the channel max-packet-size denial-of-service tests.

Not a test module (no ``test_`` prefix, so pytest does not collect it). It is
launched as a subprocess by ``test_pktsize_dos.py`` under a wall-clock timeout.

Usage: ``_pktsize_scenario.py <tmpdir> [mode]``

Modes (the peer always advertises a maximum packet size of zero):

* ``open`` (default) -- the client opens a session channel advertising zero;
  the server is the target and has channel data to send back.
* ``open-dropbear`` -- as ``open``, but the client presents a dropbear
  software version and compression is negotiated (the library's default
  algorithm list). The advertised size is still zero.
* ``confirm`` -- the server accepts the client's session channel and its
  open confirmation advertises zero; the client is the target and has
  channel data (stdin) to send.

A correct endpoint rejects the zero size with a protocol-level error, so this
script catches the error and exits 0 ("blocked") promptly. A vulnerable
endpoint accepts the zero size and spins forever trying to chunk its output
into empty packets, wedging the event loop in a synchronous loop; this script
then never returns and the parent's timeout fires.
"""
import asyncio
import os
import sys

import asyncssh


class _Server(asyncssh.SSHServer):
    def begin_auth(self, username):
        return True

    def password_auth_supported(self):
        return True

    def validate_password(self, username, password):
        return password == "pw"


async def main() -> int:
    base = sys.argv[1]
    mode = sys.argv[2] if len(sys.argv) > 2 else "open"
    hk = os.path.join(base, "hk")
    asyncssh.generate_private_key("ssh-rsa").write_private_key(hk)

    async def handle(process):
        if mode == "confirm":
            try:
                await process.stdin.read()          # drain what the client sends
            except Exception:
                pass
        process.stdout.write("hello world\n")       # peer must send channel data
        process.exit(0)

    server_kw = {}
    client_kw = {}
    run_kw = {}
    if mode == "confirm":
        server_kw["max_pktsize"] = 0                # server advertises zero
        run_kw["input"] = "hello server\n" * 4      # client must send data
    else:
        run_kw["max_pktsize"] = 0                   # client advertises zero
    if mode == "open-dropbear":
        client_kw["client_version"] = "dropbear_2022.83"

    server = await asyncssh.create_server(
        _Server, "127.0.0.1", 0, server_host_keys=[hk], process_factory=handle,
        **server_kw)
    port = server.sockets[0].getsockname()[1]

    try:
        async with asyncssh.connect("127.0.0.1", port, username="u",
                                    password="pw", known_hosts=None,
                                    **client_kw) as conn:
            try:
                await conn.run("x", **run_kw)
            except asyncssh.Error:
                print("blocked")        # the zero packet size was rejected
                return 0
            # Served data without rejecting a zero packet size: not the fixed
            # behaviour. (A vulnerable endpoint never reaches here; it hangs.)
            print("unexpected-complete")
            return 2
    finally:
        server.close()
        await server.wait_closed()


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
