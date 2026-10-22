"""Multipart callers express nested settings with bracket notation. A
destination-selecting value hidden behind that notation must be refused before
any provider call, for every nested container the request may carry."""

import pytest

ATTACK_HOST = "https://example.invalid/v1"


def _upload(client, auth, outbound, fields):
    data = {"purpose": "batch"}
    data.update(fields)
    with outbound("acreate_file") as stub:
        response = client.post(
            "/v1/files",
            headers=auth,
            data=data,
            files={"file": ("batch.jsonl", b'{"id": 1}\n', "application/jsonl")},
        )
    return response, stub.mock


@pytest.mark.parametrize(
    "fields",
    [
        {"litellm_metadata[langfuse_host]": ATTACK_HOST},
        {"litellm_metadata[api_base]": ATTACK_HOST},
        {"metadata[api_base]": ATTACK_HOST},
        {"extra_body[api_base]": ATTACK_HOST},
        {"extra_body[aws_bedrock_runtime_endpoint]": ATTACK_HOST},
    ],
)
def test_bracket_notation_destination_is_refused(client, auth, outbound, fields):
    response, provider = _upload(client, auth, outbound, fields)

    assert 400 <= response.status_code < 500, response.text[:300]
    assert not provider.called, "the destination-selecting form field reached the provider call"
