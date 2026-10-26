"""The unauthenticated limits views must not disclose configured credentials."""

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

LIMIT_SECRETS = (
    SECRET_PASSWORD,
    SECRET_LOGIN,
    URL_USER,
    URL_PASSWORD,
    PROXY_USER,
    PROXY_PASSWORD,
)


def test_all_limits_hides_credentials(api):
    r = requests.get(api + "/all/limits", timeout=10)
    assert_not_disclosed(r, LIMIT_SECRETS)


@pytest.mark.parametrize("plugin", ["ip", "ports"])
def test_plugin_limits_hides_credentials(api, plugin):
    r = requests.get(f"{api}/{plugin}/limits", timeout=10)
    assert_not_disclosed(r, LIMIT_SECRETS)
