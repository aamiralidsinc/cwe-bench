"""Security: a client-supplied user name must not let authentication read an
authorized-keys file from outside the configured per-user key directory.

A server can be configured to locate each user's authorized keys by expanding
the user name into a path template (one directory per user). The user name
arrives from the network at connection time, so if it is expanded into the path
without validation a client can present a name containing path-traversal
segments and steer the lookup at an attacker-controlled directory elsewhere on
disk -- authenticating with a key the real account owner never authorized.

This drives the REAL public server API over loopback: a server configured with
a per-user authorized-keys template, and a client that authenticates with a key
planted OUTSIDE the key directory while presenting a traversing user name. The
assertion is that this authentication is refused. On vulnerable code the
traversal succeeds and the client connects (assertion fails); a correct fix
rejects the unsafe user name so the out-of-directory key is never consulted.
"""
import asyncio
import os

import pytest

import asyncssh


async def _attempt(tmp_path, attack_user="../OUTSIDE") -> dict:
    base = str(tmp_path)
    os.makedirs(os.path.join(base, "keys", "legit"), exist_ok=True)
    os.makedirs(os.path.join(base, "OUTSIDE"), exist_ok=True)

    hk = os.path.join(base, "hk")
    asyncssh.generate_private_key("ssh-rsa").write_private_key(hk)

    # Legit user's key pair, authorized under keys/legit/.
    legit = asyncssh.generate_private_key("ssh-rsa")
    legit.write_private_key(os.path.join(base, "legit_id"))
    with open(os.path.join(base, "keys", "legit", "authorized_keys"), "wb") as f:
        f.write(legit.export_public_key())

    # Attacker's key pair, planted OUTSIDE the keys/ directory.
    attacker = asyncssh.generate_private_key("ssh-rsa")
    attacker.write_private_key(os.path.join(base, "atk_id"))
    with open(os.path.join(base, "OUTSIDE", "authorized_keys"), "wb") as f:
        f.write(attacker.export_public_key())

    cfg = os.path.join(base, "sshd_config")
    with open(cfg, "w") as f:
        f.write("AuthorizedKeysFile %s/keys/%%u/authorized_keys\n" % base)

    server = await asyncssh.create_server(
        asyncssh.SSHServer, "127.0.0.1", 0, server_host_keys=[hk], config=[cfg])
    port = server.sockets[0].getsockname()[1]

    out = {}
    try:
        # Baseline: the real account authenticates with its own key.
        try:
            async with asyncssh.connect(
                    "127.0.0.1", port, username="legit",
                    client_keys=[os.path.join(base, "legit_id")],
                    known_hosts=None):
                out["legit"] = "ok"
        except Exception as e:
            out["legit"] = "FAILED:%s" % type(e).__name__

        # Attack: traversing user name + a key planted outside keys/.
        try:
            async with asyncssh.connect(
                    "127.0.0.1", port, username=attack_user,
                    client_keys=[os.path.join(base, "atk_id")],
                    known_hosts=None):
                out["attack"] = "vulnerable"
        except Exception:
            out["attack"] = "blocked"
    finally:
        server.close()
        await server.wait_closed()
    return out


def test_authorized_keys_username_traversal(tmp_path):
    out = asyncio.run(_attempt(tmp_path))
    # Sanity: the legitimate per-user lookup must work, otherwise the test
    # proves nothing about traversal.
    assert out.get("legit") == "ok", (
        "legitimate per-user key lookup did not authenticate: %r" % out.get("legit"))
    assert out.get("attack") == "blocked", (
        "a traversing user name read an authorized-keys file from outside the "
        "per-user key directory and authenticated an unauthorized key")



def test_authorized_keys_username_embedded_traversal(tmp_path):
    # The traversal is not leading: 'legit/../../OUTSIDE' walks out of the key
    # area through a real user's directory.
    out = asyncio.run(_attempt(tmp_path, "legit/../../OUTSIDE"))
    assert out.get("legit") == "ok", (
        "legitimate per-user key lookup did not authenticate: %r" % out.get("legit"))
    assert out.get("attack") == "blocked", (
        "a user name with an embedded traversal segment read an authorized-keys "
        "file from outside the per-user key directory and authenticated an "
        "unauthorized key")


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
