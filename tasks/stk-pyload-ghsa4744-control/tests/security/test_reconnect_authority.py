"""The reported route: an account that holds only the settings permission must not be able to
change the program the service runs when it reconnects.  Every case drives the product's own HTTP
settings API with the account's credentials."""
import os

from support import harness

SCRIPT = "/bin/true"
OTHER_SCRIPT = "/bin/sh"
THIRD_SCRIPT = "/bin/false"


def _legacy_set(env, value):
    return env.client.post(
        "/api/setConfigValue",
        data={"category": "reconnect", "option": "script", "value": value, "section": "core"},
        headers=harness.Env._auth(harness.USER, harness.PASSWORD),
    )


def test_non_admin_cannot_set_reconnect_script(env):
    before = env.value("reconnect", "script")
    env.set_value("reconnect", "script", SCRIPT)
    after = env.value("reconnect", "script")
    assert after == before, f"reconnect program changed from {before!r} to {after!r}"


def test_non_admin_cannot_set_reconnect_script_through_legacy_name(env):
    before = env.value("reconnect", "script")
    _legacy_set(env, THIRD_SCRIPT)
    after = env.value("reconnect", "script")
    assert after == before, f"reconnect program changed from {before!r} to {after!r}"


def test_non_admin_cannot_point_reconnect_at_a_program_they_placed(env):
    holder = env.scratch("program")
    program = os.path.join(holder, "reconnect.sh")
    with open(program, "w", encoding="utf-8") as fp:
        fp.write("#!/bin/sh\nexit 0\n")
    os.chmod(program, 0o755)
    before = env.value("reconnect", "script")
    env.set_value("reconnect", "script", program)
    after = env.value("reconnect", "script")
    assert after == before, f"reconnect program changed from {before!r} to {after!r}"


def test_non_admin_cannot_replace_an_already_configured_script(env):
    env.set_value("reconnect", "script", SCRIPT, admin=True)
    configured = env.value("reconnect", "script")
    env.set_value("reconnect", "script", OTHER_SCRIPT)
    after = env.value("reconnect", "script")
    assert after == configured, f"reconnect program changed from {configured!r} to {after!r}"
