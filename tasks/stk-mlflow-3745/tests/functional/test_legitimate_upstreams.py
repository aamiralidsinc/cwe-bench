import gwhelper as gw


def test_shipped_local_default_is_still_called():
    canary = gw.Canary(11434)
    try:
        name = gw.unique("ollama")
        status, data = gw.create_secret(
            name, provider="ollama", secret_value={"api_key": "ollama"}
        )
        assert status == 200, data
        secret_id = data["secret"]["secret_id"]

        status, data = gw.create_model_definition(
            name + "-md", secret_id, "ollama", "llama3"
        )
        assert status == 200, data
        model_definition_id = data["model_definition"]["model_definition_id"]

        status, data = gw.create_endpoint(name + "-ep", model_definition_id)
        assert status == 200, data

        response = gw.invoke(name + "-ep")
        assert canary.count() >= 1, "the shipped local default was not called"
        assert response.status_code == 200, response.text
    finally:
        canary.close()


def test_public_third_party_configuration_still_used():
    name = gw.unique("cohere")
    status, data = gw.create_secret(
        name,
        provider="cohere",
        secret_value={"api_key": "sk-test", "client_label": "team-a"},
        auth_config={"api_base": "https://8.8.8.8/v1", "version": "2024-01"},
    )
    assert status == 200, data
    secret_id = data["secret"]["secret_id"]

    status, data = gw.create_model_definition(name + "-md", secret_id, "cohere", "command-r")
    assert status == 200, data
    model_definition_id = data["model_definition"]["model_definition_id"]

    status, data = gw.create_endpoint(name + "-ep", model_definition_id)
    assert status == 200, data


def test_legitimate_region_and_location_names_are_accepted():
    for location in ("global", "us-central1", "europe-west4"):
        name = gw.unique("vertex")
        status, data = gw.create_secret(
            name,
            provider="vertex_ai",
            secret_value={"api_key": "test-key", "vertex_credentials": "{}"},
            auth_config={"vertex_project": "test-project", "vertex_location": location},
        )
        assert status == 200, (location, data)

    for region in ("us-east-1", "eu-west-1"):
        name = gw.unique("bedrock")
        status, data = gw.create_secret(
            name,
            provider="bedrock",
            secret_value={"api_key": "test-key"},
            auth_config={"auth_mode": "api_key", "aws_region_name": region},
        )
        assert status == 200, (region, data)
