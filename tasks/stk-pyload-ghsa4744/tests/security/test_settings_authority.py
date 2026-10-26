"""A change to a setting that decides what the service executes, how it is exposed, or which
credentials and certificate material it presents must not take effect for an account that is not
an administrator.  Every case goes through the product's HTTP API with the account's own
credentials."""
import pytest

#: settings that select a program, the served endpoint/transport, certificate material or
#: credentials towards another service
PROTECTED_CORE = [
    ("reconnect", "script", "/bin/true"),
    ("webui", "ssl_certfile", "/etc/hostname.crt"),
    ("webui", "ssl_keyfile", "/etc/hostname.key"),
    ("webui", "use_ssl", "true"),
    ("webui", "host", "0.0.0.0"),
    ("proxy", "username", "attacker"),
    ("proxy", "password", "attacker-secret"),
]

PROTECTED_PLUGIN = [
    ("AntiVirus", "avfile", "/bin/sh"),
    ("AntiVirus", "avargs", "-c id"),
]


@pytest.mark.parametrize("category,option,value", PROTECTED_CORE)
def test_non_admin_cannot_change_protected_core_setting(env, category, option, value):
    before = env.value(category, option)
    env.set_value(category, option, value)
    after = env.value(category, option)
    assert after == before, f"{category}.{option} changed from {before!r} to {after!r}"


@pytest.mark.parametrize("plugin,option,value", PROTECTED_PLUGIN)
def test_non_admin_cannot_change_protected_plugin_setting(env, plugin, option, value):
    before = env.plugin_value(plugin, option)
    env.set_value(plugin, option, value, section="plugin")
    after = env.plugin_value(plugin, option)
    assert after == before, f"{plugin}.{option} changed from {before!r} to {after!r}"
