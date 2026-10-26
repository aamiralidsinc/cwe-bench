"""A single-user deployment (access control off) keeps its settings workflow."""

import support


def test_anonymous_caller_can_save_llm_settings():
    with support.make_client() as client:
        response = client.post(
            "/api/v1/settings",
            json=support.llm_payload(
                provider="openai", model="gpt-4o", api_key="sk-single-user-123456"
            ),
        )
        assert response.status_code < 400, response.text[:300]
        assert support.stored_llm_key() == "sk-single-user-123456"


def test_anonymous_caller_can_save_vector_settings():
    with support.make_client() as client:
        response = client.post(
            "/api/v1/settings",
            json=support.vector_payload(
                provider="lancedb",
                url="single-user-store",
                api_key="vdb-single-user-123456",
            ),
        )
        assert response.status_code < 400, response.text[:300]
        assert support.stored_vector_key() == "vdb-single-user-123456"


def test_settings_read_returns_current_values_and_chooser_lists():
    with support.make_client() as client:
        saved = client.post(
            "/api/v1/settings",
            json=support.llm_payload(
                provider="openai", model="gpt-4o", api_key="sk-chooser-test-123456"
            ),
        )
        assert saved.status_code < 400, saved.text[:300]

        response = client.get("/api/v1/settings")
        assert response.status_code < 400, response.text[:300]

        body = response.json()
        assert body["llm"]["provider"] == "openai"
        assert body["llm"]["model"] == "gpt-4o"
        assert {choice["value"] for choice in body["llm"]["providers"]} >= {"openai", "ollama"}
        assert body["llm"]["models"], "the model chooser list is missing"
        assert {choice["value"] for choice in body["vectorDb"]["providers"]} >= {"lancedb"}
