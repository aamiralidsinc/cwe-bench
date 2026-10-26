"""The arguments view keeps its types and its existing hidden values."""

import requests


def test_args_keep_their_types(api):
    r = requests.get(api + "/args", timeout=10)
    assert r.status_code == 200, r.text
    body = r.json()
    assert isinstance(body["port"], int)
    assert isinstance(body["time"], float)
    assert body["disable_webui"] is True
    assert body["debug"] is False
    assert body["username_used"] is None


def test_args_sensitive_values_stay_hidden(api):
    r = requests.get(api + "/args", timeout=10)
    assert r.status_code == 200, r.text
    body = r.json()
    for key in ("password", "username", "snmp_community", "snmp_user", "snmp_auth", "conf_file"):
        # The existing hidden form is either a mask or omission.
        assert body.get(key) in (None, "********"), key


def test_args_item_stays_available(api):
    r = requests.get(api + "/args/port", timeout=10)
    assert r.status_code == 200, r.text
    assert isinstance(r.json(), int)
