"""The unauthenticated configuration views must not disclose configured credentials."""

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

CONFIG_SECRETS = (
    SECRET_PASSWORD,
    SECRET_LOGIN,
    URL_USER,
    URL_PASSWORD,
    PROXY_USER,
    PROXY_PASSWORD,
)


def test_config_list_hides_credentials(api):
    r = requests.get(api + "/config", timeout=10)
    assert_not_disclosed(r, CONFIG_SECRETS)


def test_config_section_hides_credentials(api):
    for section in ("ip", "ports", "influxdb", "passthrough"):
        r = requests.get(f"{api}/config/{section}", timeout=10)
        assert_not_disclosed(r, CONFIG_SECRETS)


@pytest.mark.parametrize(
    "item",
    ["ip/public_username", "passthrough/user", "passthrough/login", "passthrough/username"],
)
def test_config_item_hides_login(api, item):
    r = requests.get(f"{api}/config/{item}", timeout=10)
    assert_not_disclosed(r, (SECRET_LOGIN,))


@pytest.mark.parametrize("item", ["ip/public_api", "ports/web_1_url", "ports/web_1_http_proxy"])
def test_config_item_hides_url_userinfo(api, item):
    r = requests.get(f"{api}/config/{item}", timeout=10)
    assert_not_disclosed(r, (URL_USER, URL_PASSWORD, PROXY_USER, PROXY_PASSWORD))
