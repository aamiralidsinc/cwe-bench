import gwhelper as gw


def test_location_value_cannot_redirect_the_call():
    canary = gw.Canary()
    try:
        name = gw.unique("location")
        status, data = gw.create_secret(
            name,
            provider="vertex_ai",
            secret_value={"api_key": "test-key", "vertex_credentials": "{}"},
            auth_config={
                "vertex_project": "test-project",
                "vertex_location": f"127.0.0.1:{canary.port}/#",
            },
        )
        assert 400 <= status < 500, status
        assert canary.count() == 0
    finally:
        canary.close()


def test_region_value_cannot_change_the_host():
    name = gw.unique("region")
    status, _ = gw.create_secret(
        name,
        provider="bedrock",
        secret_value={"api_key": "test-key"},
        auth_config={
            "auth_mode": "api_key",
            "aws_region_name": "evil.example@127.0.0.1:9/#",
        },
    )
    assert 400 <= status < 500, status
    assert name not in gw.list_secret_names()
