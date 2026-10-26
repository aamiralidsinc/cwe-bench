"""The per-plugin settings views keep their legitimate values."""

import requests

from conftest import PLAIN_URL, SECRET_PASSWORD


def test_ip_settings_keep_plain_values(api):
    r = requests.get(api + "/ip/settings", timeout=10)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["public_field"] == "ip"
    assert body["public_disabled"] == "True"
    assert body.get("public_password") != SECRET_PASSWORD


def test_ports_settings_keep_plain_values(api):
    r = requests.get(api + "/ports/settings", timeout=10)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["web_2_url"] == PLAIN_URL
    assert body["web_1_description"] == "first-blog"
    assert body["web_1_url"].startswith("https://")
