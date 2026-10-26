"""Multi-user deployments: the bootstrap account manages settings; users read them."""

import support

SUPERUSER_EMAIL = "default_user@example.com"
SUPERUSER_PASSWORD = "default_password"


def _superuser_headers(client):
    logged_in = support.login(client, SUPERUSER_EMAIL, SUPERUSER_PASSWORD)
    assert logged_in.status_code < 400, logged_in.text[:300]
    return support.bearer(logged_in.json()["access_token"])


def test_bootstrap_account_can_save_settings():
    with support.make_client() as client:
        headers = _superuser_headers(client)
        response = client.post(
            "/api/v1/settings",
            json=support.llm_payload(
                provider="openai", model="gpt-4o", api_key="sk-superuser-save-123456"
            ),
            headers=headers,
        )
        assert response.status_code < 400, response.text[:300]
        assert support.stored_llm_key() == "sk-superuser-save-123456"


def test_ordinary_user_can_read_settings():
    with support.make_client() as client:
        headers = _superuser_headers(client)
        saved = client.post(
            "/api/v1/settings",
            json=support.llm_payload(
                provider="openai", model="gpt-4o", api_key="sk-visible-account-123456"
            ),
            headers=headers,
        )
        assert saved.status_code < 400, saved.text[:300]

        email = support.provision_ordinary_user(client)
        logged_in = support.login(client, email)
        assert logged_in.status_code < 400, logged_in.text[:300]
        user_headers = support.bearer(logged_in.json()["access_token"])

        response = client.get("/api/v1/settings", headers=user_headers)
        assert response.status_code < 400, (
            "an ordinary user lost access to the settings read: %s %s"
            % (response.status_code, response.text[:300])
        )
        body = response.json()
        assert body["llm"]["models"], "the model chooser list is missing"
        assert body["vectorDb"]["providers"], "the vector chooser list is missing"
