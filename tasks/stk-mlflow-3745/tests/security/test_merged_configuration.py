import gwhelper as gw


def test_encrypted_secret_value_cannot_override_the_upstream():
    canary = gw.Canary()
    try:
        name = gw.unique("merged")
        status, data = gw.create_secret(
            name,
            provider="cohere",
            secret_value={
                "api_key": "sk-test",
                "api_base": f"http://127.0.0.1:{canary.port}/v1",
            },
            auth_config={"api_base": "https://8.8.8.8/v1"},
        )
        if 400 <= status < 500:
            # Refused before it was stored: nothing can reach the address.
            assert canary.count() == 0
            return
        assert status == 200, data
        secret_id = data["secret"]["secret_id"]

        status, data = gw.create_model_definition(
            name + "-md", secret_id, "cohere", "command-r"
        )
        assert status == 200, data
        model_definition_id = data["model_definition"]["model_definition_id"]

        status, data = gw.create_endpoint(name + "-ep", model_definition_id)
        assert status == 200, data

        response = gw.invoke(name + "-ep")
        assert canary.count() == 0, "the gateway called the supplied internal address"
        assert 400 <= response.status_code < 500, response.text
    finally:
        canary.close()
