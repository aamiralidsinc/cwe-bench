"""Ports statistics keep the monitoring fields the plugin is meant to show."""

import requests

from conftest import PLAIN_URL


def _by_indice(body, indice):
    for item in body:
        if item.get("indice") == indice:
            return item
    raise AssertionError(f"no {indice} entry in {body}")


def test_plain_url_stays_visible(api):
    r = requests.get(api + "/ports", timeout=10)
    assert r.status_code == 200, r.text
    plain = _by_indice(r.json(), "web_2")
    assert plain["url"] == PLAIN_URL
    assert plain["description"] == "plain-blog"


def test_ports_fields_stay_visible(api):
    r = requests.get(api + "/ports", timeout=10)
    assert r.status_code == 200, r.text
    first = _by_indice(r.json(), "web_1")
    assert first["description"] == "first-blog"
    assert first["url"].startswith("https://")
    assert "127.0.0.1:9" in first["url"]
    assert "timeout" in first
    assert "status" in first
