"""The per-plugin settings views must not disclose configured credentials."""

import pytest
import requests

from conftest import (
    PROXY_PASSWORD,
    PROXY_USER,
    SECRET_LOGIN,
    SECRET_PASSWORD,
    URL_PASSWORD,
    URL_USER,
    assert_not_disclosed,
)

SETTINGS_SECRETS = (
    SECRET_PASSWORD,
    SECRET_LOGIN,
    URL_USER,
    URL_PASSWORD,
    PROXY_USER,
    PROXY_PASSWORD,
)


@pytest.mark.parametrize("plugin", ["ip", "ports"])
def test_plugin_settings_hide_credentials(api, plugin):
    r = requests.get(f"{api}/{plugin}/settings", timeout=10)
    assert_not_disclosed(r, SETTINGS_SECRETS)
