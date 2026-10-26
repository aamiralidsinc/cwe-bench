"""Legitimate configuration values keep working exactly as before."""

import requests

from conftest import PLAIN_URL, SECRET_PASSWORD


def test_cpu_and_load_thresholds_stay_visible(api):
    r = requests.get(api + "/config", timeout=10)
    assert r.status_code == 200, r.text
    body = r.json()
    cpu = body["cpu"]
    assert cpu["user_careful"] == "50"
    assert cpu["user_warning"] == "70"
    assert cpu["user_critical"] == "90"
    assert cpu["user_log"] == "True"
    assert body["load"]["user_careful"] == "2"


def test_plain_config_values_stay_visible(api):
    r = requests.get(api + "/config", timeout=10)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["ip"]["public_field"] == "ip"
    assert body["ports"]["web_1_description"] == "first-blog"
    assert body["ports"]["web_2_url"] == PLAIN_URL
    assert body["ports"]["web_2_description"] == "plain-blog"


def test_config_section_stays_available(api):
    r = requests.get(api + "/config/ip", timeout=10)
    assert r.status_code == 200, r.text
    assert r.json()["public_field"] == "ip"


def test_password_stays_hidden(api):
    r = requests.get(api + "/config/ip/public_password", timeout=10)
    assert r.status_code < 500, r.text
    assert SECRET_PASSWORD not in r.text
