"""Only a deployment-privileged caller may overwrite the global model settings."""

import support


def _non_superuser_headers(client):
    registered, email = support.register(client)
    assert registered.status_code < 400, registered.text[:300]
    logged_in = support.login(client, email)
    assert logged_in.status_code < 400, logged_in.text[:300]
    return support.bearer(logged_in.json()["access_token"])


def test_non_superuser_cannot_overwrite_llm_settings():
    with support.make_client() as client:
        before = support.snapshot()
        headers = _non_superuser_headers(client)

        response = client.post(
            "/api/v1/settings",
            json=support.llm_payload(
                provider="anthropic",
                model="attacker-chosen-model",
                api_key="sk-attacker-controlled-000111222",
            ),
            headers=headers,
        )

        after = support.snapshot()
        assert support.is_client_error(
            response.status_code
        ), "the write was not refused: %s %s" % (
            response.status_code,
            response.text[:300],
        )
        assert after == before, "the deployment configuration changed despite the refusal"


def test_non_superuser_cannot_overwrite_vector_settings():
    with support.make_client() as client:
        before = support.snapshot()
        headers = _non_superuser_headers(client)

        response = client.post(
            "/api/v1/settings",
            json=support.vector_payload(
                provider="pgvector",
                url="attacker-controlled-store",
                api_key="vdb-attacker-controlled-333444",
            ),
            headers=headers,
        )

        after = support.snapshot()
        assert support.is_client_error(
            response.status_code
        ), "the vector write was not refused: %s %s" % (
            response.status_code,
            response.text[:300],
        )
        assert after == before, "the vector configuration changed despite the refusal"


def test_non_superuser_cannot_overwrite_both_settings_at_once():
    with support.make_client() as client:
        before = support.snapshot()
        headers = _non_superuser_headers(client)

        payload = support.llm_payload(
            provider="mistral", model="attacker-combined-model", api_key="sk-combined-555666"
        )
        payload.update(
            support.vector_payload(
                provider="pgvector",
                url="attacker-combined-store",
                api_key="vdb-combined-777888",
            )
        )
        response = client.post("/api/v1/settings", json=payload, headers=headers)

        after = support.snapshot()
        assert support.is_client_error(
            response.status_code
        ), "the combined write was not refused: %s %s" % (
            response.status_code,
            response.text[:300],
        )
        assert after == before, "the deployment configuration changed despite the refusal"
