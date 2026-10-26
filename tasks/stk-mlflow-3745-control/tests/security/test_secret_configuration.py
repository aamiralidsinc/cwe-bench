import gwhelper as gw


def is_client_error(status):
    return 400 <= status < 500


def _assert_refused(auth_config):
    name = gw.unique("refused")
    status, _ = gw.create_secret(name, auth_config=auth_config)
    assert is_client_error(status), status
    assert name not in gw.list_secret_names()


def test_create_rejects_loopback_upstream():
    _assert_refused({"api_base": "http://127.0.0.1:9/v1"})


def test_create_rejects_private_network_upstream():
    _assert_refused({"api_base": "http://10.1.2.3/v1"})


def test_create_rejects_link_local_upstream():
    _assert_refused({"api_base": "http://169.254.169.254/latest/meta-data"})


def test_create_rejects_unspecified_address_upstream():
    _assert_refused({"api_base": "http://0.0.0.0:8080/v1"})
