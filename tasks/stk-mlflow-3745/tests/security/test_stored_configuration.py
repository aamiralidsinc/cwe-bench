import gwhelper as gw


def test_already_stored_internal_upstream_is_never_dialed():
    canary = gw.Canary()
    try:
        name = gw.unique("stored")
        status, data = gw.create_secret(
            name,
            provider="openai",
            secret_value={"api_key": "sk-test"},
            auth_config={"api_base": "https://8.8.8.8/v1"},
        )
        assert status == 200, data
        secret_id = data["secret"]["secret_id"]

        status, data = gw.create_model_definition(name + "-md", secret_id, "openai", "gpt-4o")
        assert status == 200, data
        model_definition_id = data["model_definition"]["model_definition_id"]

        status, data = gw.create_endpoint(name + "-ep", model_definition_id)
        assert status == 200, data

        # The row is changed outside the request path, as a stored configuration
        # written before any check existed would be.
        gw.raw_sql_set_auth_config(
            secret_id, {"api_base": f"http://127.0.0.1:{canary.port}/v1"}
        )

        gw.invoke(name + "-ep")
        assert canary.count() == 0, "the gateway called an address held in stored configuration"
    finally:
        canary.close()
