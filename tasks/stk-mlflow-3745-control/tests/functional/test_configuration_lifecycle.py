import gwhelper as gw


def test_public_configuration_round_trip():
    name = gw.unique("public")
    status, data = gw.create_secret(
        name, provider="openai", auth_config={"api_base": "https://8.8.8.8/v1"}
    )
    assert status == 200, data
    secret_id = data["secret"]["secret_id"]
    assert name in gw.list_secret_names()

    status, data = gw.get_secret(secret_id)
    assert status == 200, data
    assert data["secret"]["auth_config"]["api_base"] == "https://8.8.8.8/v1"

    status, data = gw.update_secret(
        secret_id, auth_config={"api_base": "https://1.1.1.1/v1"}
    )
    assert status == 200, data

    status, data = gw.get_secret(secret_id)
    assert status == 200, data
    assert data["secret"]["auth_config"]["api_base"] == "https://1.1.1.1/v1"


def test_endpoint_and_model_definition_lifecycle():
    name = gw.unique("lifecycle")
    status, data = gw.create_secret(
        name, provider="openai", auth_config={"api_base": "https://8.8.8.8/v1"}
    )
    assert status == 200, data
    secret_id = data["secret"]["secret_id"]

    status, data = gw.create_model_definition(
        name + "-md", secret_id, "openai", "gpt-4o"
    )
    assert status == 200, data
    model_definition_id = data["model_definition"]["model_definition_id"]

    status, data = gw.create_endpoint(name + "-ep", model_definition_id)
    assert status == 200, data

    status, data = gw.get_endpoint(name + "-ep")
    assert status == 200, data
    assert data["endpoint"]["name"] == name + "-ep"
