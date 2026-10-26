import gwhelper as gw


def is_client_error(status):
    return 400 <= status < 500


def test_create_rejects_loopback_upstream():
    name = gw.unique("loopback")
    status, _ = gw.create_secret(
        name, auth_config={"api_base": "http://127.0.0.1:9/v1"}
    )
    assert is_client_error(status), status
    assert name not in gw.list_secret_names()


def test_create_rejects_private_network_upstream():
    name = gw.unique("private")
    status, _ = gw.create_secret(
        name, auth_config={"api_base": "http://10.1.2.3/v1"}
    )
    assert is_client_error(status), status
    assert name not in gw.list_secret_names()


def test_create_rejects_link_local_upstream():
    name = gw.unique("linklocal")
    status, _ = gw.create_secret(
        name, auth_config={"api_base": "http://169.254.169.254/latest/meta-data"}
    )
    assert is_client_error(status), status
    assert name not in gw.list_secret_names()


def test_update_rejects_internal_upstream_and_keeps_previous_value():
    name = gw.unique("update")
    status, data = gw.create_secret(
        name, auth_config={"api_base": "https://8.8.8.8/v1"}
    )
    assert status == 200, data
    secret_id = data["secret"]["secret_id"]

    status, _ = gw.update_secret(
        secret_id, auth_config={"api_base": "http://127.0.0.1:9/v1"}
    )
    assert is_client_error(status), status

    status, data = gw.get_secret(secret_id)
    assert status == 200, data
    assert data["secret"]["auth_config"]["api_base"] == "https://8.8.8.8/v1"
