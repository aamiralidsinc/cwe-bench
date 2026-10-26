"""The settings read must work when the deployment has no key configured."""

import support


def test_read_works_when_no_llm_key_is_configured():
    with support.make_client() as client:
        assert support.stored_llm_key() in (None, "")

        response = client.get("/api/v1/settings")
        assert response.status_code < 400, (
            "the settings read failed for a deployment without a key: %s %s"
            % (response.status_code, response.text[:300])
        )

        body = response.json()
        assert "llm" in body and "vectorDb" in body
        assert body["llm"].get("providers"), "the provider chooser list is missing"
        assert body["llm"].get("models"), "the model chooser list is missing"
