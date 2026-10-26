"""Re-submitting the settings a client just read must keep the stored values.

This is the save/read cycle the settings screen performs: it reads the current
configuration, the user edits provider or model, and the screen posts the whole
form back.  The hidden key value the screen shows must keep working as a value.
"""

import support

LLM_KEY = "sk-roundtrip-7788aabbccdd"
VECTOR_KEY = "vdb-roundtrip-99eeff0011"


def test_resaving_the_visible_settings_keeps_the_stored_llm_key():
    with support.make_client() as client:
        saved = client.post(
            "/api/v1/settings",
            json=support.llm_payload(provider="openai", model="gpt-4o", api_key=LLM_KEY),
        )
        assert saved.status_code < 400, saved.text[:300]

        current = client.get("/api/v1/settings")
        assert current.status_code < 400, current.text[:300]
        visible = current.json()["llm"]

        again = client.post(
            "/api/v1/settings",
            json={
                "llm": {
                    "provider": visible["provider"],
                    "model": visible["model"],
                    "api_key": visible["apiKey"],
                }
            },
        )
        assert again.status_code < 400, again.text[:300]
        assert support.stored_llm_key() == LLM_KEY, (
            "saving the settings a client just read replaced the stored key with %r"
            % (support.stored_llm_key(),)
        )


def test_resaving_the_visible_settings_keeps_the_stored_vector_key():
    with support.make_client() as client:
        saved = client.post(
            "/api/v1/settings",
            json=support.vector_payload(
                provider="lancedb", url="roundtrip-store", api_key=VECTOR_KEY
            ),
        )
        assert saved.status_code < 400, saved.text[:300]

        current = client.get("/api/v1/settings")
        assert current.status_code < 400, current.text[:300]
        visible = current.json()["vectorDb"]

        again = client.post(
            "/api/v1/settings",
            json={
                "vector_db": {
                    "provider": visible["provider"],
                    "url": visible["url"],
                    "api_key": visible["apiKey"],
                }
            },
        )
        assert again.status_code < 400, again.text[:300]
        assert support.stored_vector_key() == VECTOR_KEY, (
            "saving the settings a client just read replaced the stored key with %r"
            % (support.stored_vector_key(),)
        )
