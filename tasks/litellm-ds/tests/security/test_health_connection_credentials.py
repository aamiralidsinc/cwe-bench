"""A management connection test must not pair a caller-chosen destination with
the credentials (or the stored-credential reference) configured for the
deployment it names."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from conftest import as_json

ATTACK_HOST = "https://example.invalid/v1"


@pytest.fixture
def health_call(client, monkeypatch):
    """Drive the real management route; return the params handed downstream."""
    from litellm.proxy import proxy_server
    from litellm.proxy.management_endpoints.model_management_endpoints import (
        ModelManagementAuthChecks,
    )

    monkeypatch.setattr(proxy_server, "prisma_client", MagicMock())
    monkeypatch.setattr(
        ModelManagementAuthChecks,
        "can_user_make_model_call",
        AsyncMock(return_value=None),
    )

    def call(auth, litellm_params):
        import litellm

        recorder = AsyncMock(return_value={"status": "healthy", "response_time_ms": 1})
        monkeypatch.setattr(litellm, "ahealth_check", recorder)
        response = client.post(
            "/health/test_connection",
            headers=auth,
            json={"litellm_params": litellm_params, "mode": "chat"},
        )
        params = recorder.call_args.kwargs.get("model_params", {}) if recorder.called else {}
        return response, params

    return call


@pytest.mark.parametrize(
    "request_params,secret",
    [
        ({"model": "gpt-4o", "api_base": ATTACK_HOST}, "sk-configured-secret"),
        (
            {"model": "gpt-4o", "aws_bedrock_runtime_endpoint": ATTACK_HOST},
            "sk-configured-secret",
        ),
        (
            {"model": "stored-cred-model", "api_base": ATTACK_HOST},
            "sk-stored-cred-secret",
        ),
    ],
)
def test_configured_credentials_do_not_follow_a_caller_destination(
    health_call, auth, request_params, secret
):
    response, params = health_call(auth, request_params)

    assert secret not in as_json(params), (
        "the configured credential was handed to a connection test aimed at the caller's destination"
    )


def test_stored_credential_reference_does_not_follow_a_caller_destination(health_call, auth):
    response, params = health_call(auth, {"model": "stored-cred-model", "api_base": ATTACK_HOST})

    assert "litellm_credential_name" not in params, (
        "the stored-credential reference resolves to the same secrets downstream"
    )
