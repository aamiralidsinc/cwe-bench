"""A model identifier placed in a deployment-scoped URL path must not become
an outbound destination, even though the request body's model is ordinary."""

import pytest

ATTACK_HOST = "https://example.invalid/v1"


def _chat(client, auth, outbound, path):
    with outbound("acompletion") as stub:
        response = client.post(
            path,
            headers=auth,
            json={
                "model": "gpt-4o",
                "messages": [{"role": "user", "content": "hello"}],
            },
        )
    return response, stub.mock


@pytest.mark.parametrize(
    "path",
    [
        f"/openai/deployments/huggingface/{ATTACK_HOST}/chat/completions",
        f"/engines/huggingface/{ATTACK_HOST}/chat/completions",
        f"/openai/deployments/{ATTACK_HOST}/chat/completions",
    ],
)
def test_url_valued_path_model_is_refused(client, auth, outbound, path):
    response, provider = _chat(client, auth, outbound, path)

    assert 400 <= response.status_code < 500, response.text[:300]
    assert not provider.called, "the gateway reached a provider at the caller's destination"


@pytest.mark.parametrize(
    "path",
    [
        f"/openai/deployments/huggingface/{ATTACK_HOST}/embeddings",
        f"/engines/huggingface/{ATTACK_HOST}/embeddings",
        f"/openai/deployments/{ATTACK_HOST}/embeddings",
    ],
)
def test_url_valued_path_model_on_embeddings_is_refused(client, auth, outbound, path):
    with outbound("aembedding") as stub:
        response = client.post(
            path,
            headers=auth,
            json={"model": "gpt-4o", "input": "hello"},
        )

    assert 400 <= response.status_code < 500, response.text[:300]
    assert not stub.mock.called, "the gateway reached an embedding provider at the caller's destination"
