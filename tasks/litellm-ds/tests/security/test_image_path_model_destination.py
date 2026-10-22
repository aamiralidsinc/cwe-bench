"""The image-generation handler chooses its model separately from the shared
request processor; a URL-valued deployment segment must be refused there too."""

import pytest

ATTACK_HOST = "https://example.invalid/v1"


@pytest.mark.parametrize(
    "path",
    [
        f"/openai/deployments/huggingface/{ATTACK_HOST}/images/generations",
        f"/openai/deployments/{ATTACK_HOST}/images/generations",
    ],
)
def test_url_valued_path_model_on_image_generation_is_refused(client, auth, outbound, path):
    with outbound("aimage_generation") as stub:
        response = client.post(
            path,
            headers=auth,
            json={"model": "dall-e-3", "prompt": "a harmless picture", "n": 1},
        )

    assert 400 <= response.status_code < 500, response.text[:300]
    assert not stub.mock.called, "the gateway asked an image provider to use the caller's destination"
