"""Nested form metadata that does not choose a destination keeps working,
including under the operator's explicit client-side-credentials opt-in."""

import pytest


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


def test_benign_bracket_metadata_reaches_the_call(client, auth, outbound):
    response, provider = _upload(
        client,
        auth,
        outbound,
        {
            "litellm_metadata[tags]": "production",
            "litellm_metadata[spend_logs_metadata][owner]": "john",
        },
    )

    assert response.status_code == 200, response.text[:300]
    assert provider.called
    metadata = provider.call_args.kwargs.get("litellm_metadata", {})
    assert metadata.get("tags") == "production"
    assert metadata.get("spend_logs_metadata", {}).get("owner") == "john"


def test_benign_extra_body_bracket_field_reaches_the_call(client, auth, outbound):
    response, provider = _upload(
        client,
        auth,
        outbound,
        {"extra_body[api_version]": "2024-01-01"},
    )

    assert response.status_code == 200, response.text[:300]
    assert provider.called
    assert provider.call_args.kwargs.get("extra_body", {}).get("api_version") == "2024-01-01"


def test_admin_opt_in_restores_client_side_metadata(client, auth, outbound, monkeypatch):
    from litellm.proxy import proxy_server

    monkeypatch.setitem(proxy_server.general_settings, "allow_client_side_credentials", True)
    response, provider = _upload(
        client,
        auth,
        outbound,
        {"litellm_metadata[langfuse_host]": "https://byok.example.test"},
    )

    assert response.status_code == 200, response.text[:300]
    assert provider.called
    assert provider.call_args.kwargs["litellm_metadata"]["langfuse_host"] == "https://byok.example.test"


def test_admin_opt_in_restores_client_side_extra_body(client, auth, outbound, monkeypatch):
    from litellm.proxy import proxy_server

    monkeypatch.setitem(proxy_server.general_settings, "allow_client_side_credentials", True)
    response, provider = _upload(
        client,
        auth,
        outbound,
        {"extra_body[api_base]": "https://byok.example.test/v1"},
    )

    assert response.status_code == 200, response.text[:300]
    assert provider.called
    assert provider.call_args.kwargs["extra_body"]["api_base"] == "https://byok.example.test/v1"
