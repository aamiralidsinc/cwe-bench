"""The moderation handler selects its model itself. A URL-valued deployment
segment must not become the outbound destination of the moderation call."""

import pytest

ATTACK_HOST = "https://example.invalid/v1"


@pytest.mark.parametrize(
    "path",
    [
        f"/openai/deployments/huggingface/{ATTACK_HOST}/moderations",
        f"/openai/deployments/{ATTACK_HOST}/moderations",
    ],
)
def test_url_valued_path_model_on_moderation_is_refused(client, auth, outbound, path):
    with outbound("amoderation") as stub:
        response = client.post(
            path,
            headers=auth,
            json={"model": "text-moderation-stable", "input": "hello"},
        )

    assert 400 <= response.status_code < 500, response.text[:300]
    assert not stub.mock.called, "the moderation call used the caller's destination"
