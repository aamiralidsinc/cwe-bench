"""The settings read response must never disclose a stored key, in any part."""

import support

LLM_KEY = "sk-live-9f3aQ2secretvalue8471x"
VECTOR_KEY = "vdb-live-Zx81secretkey77q"


def _save_keys(client):
    response = client.post(
        "/api/v1/settings",
        json={
            "llm": {"provider": "openai", "model": "gpt-4o", "api_key": LLM_KEY},
            "vector_db": {
                "provider": "lancedb",
                "url": "local-vector-store",
                "api_key": VECTOR_KEY,
            },
        },
    )
    assert response.status_code < 400, response.text[:300]
    assert support.stored_llm_key() == LLM_KEY
    assert support.stored_vector_key() == VECTOR_KEY


def test_read_response_does_not_disclose_the_llm_key():
    with support.make_client() as client:
        _save_keys(client)

        response = client.get("/api/v1/settings")
        assert response.status_code < 400, response.text[:300]

        text = response.text
        assert LLM_KEY not in text, "the stored LLM key is echoed in the response"
        assert LLM_KEY[:8] not in text, "a prefix of the stored LLM key is disclosed"
        assert LLM_KEY[-6:] not in text, "the tail of the stored LLM key is disclosed"


def test_read_response_does_not_disclose_the_vector_db_key():
    with support.make_client() as client:
        _save_keys(client)

        response = client.get("/api/v1/settings")
        assert response.status_code < 400, response.text[:300]

        text = response.text
        assert VECTOR_KEY not in text, "the stored vector key is echoed in the response"
        assert VECTOR_KEY[:8] not in text, "a prefix of the stored vector key is disclosed"
        assert VECTOR_KEY[-6:] not in text, "the tail of the stored vector key is disclosed"
