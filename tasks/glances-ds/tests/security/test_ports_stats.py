"""Monitoring statistics must not disclose credentials configured for the service."""

import requests

from conftest import PROXY_PASSWORD, PROXY_USER, URL_PASSWORD, URL_USER, assert_not_disclosed


def test_ports_stats_hide_url_credentials(api):
    r = requests.get(api + "/ports", timeout=10)
    assert_not_disclosed(r, (URL_USER, URL_PASSWORD))


def test_ports_stats_hide_nested_proxy_credentials(api):
    r = requests.get(api + "/ports", timeout=10)
    assert_not_disclosed(r, (PROXY_USER, PROXY_PASSWORD))
