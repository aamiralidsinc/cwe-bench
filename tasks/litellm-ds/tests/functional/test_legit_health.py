"""Management connection tests keep working: a configured model inherits the
configuration's credentials, a complete request is tested as sent, and the
operator's opt-in restores inheritance for a caller-supplied endpoint."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from conftest import as_json


@pytest.fixture
def health_call(client, monkeypatch):
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


def test_configured_model_inherits_configuration_credentials(health_call, auth):
    response, params = health_call(auth, {"model": "gpt-4o"})

    assert response.status_code == 200, response.text[:300]
    assert params.get("api_key") == "sk-configured-secret"
    assert params.get("api_base") == "https://configured.example.test/v1"


def test_complete_request_is_tested_as_sent(health_call, auth):
    response, params = health_call(
        auth,
        {
            "model": "gpt-4o",
            "api_base": "https://new-deployment.example.test/v1",
            "api_key": "sk-new-deployment",
        },
    )

    assert response.status_code == 200, response.text[:300]
    assert params.get("api_base") == "https://new-deployment.example.test/v1"
    assert params.get("api_key") == "sk-new-deployment"
    assert "sk-configured-secret" not in as_json(params)


def test_non_destination_override_keeps_configuration_credentials(health_call, auth):
    response, params = health_call(auth, {"model": "gpt-4o", "rpm": 100})

    assert response.status_code == 200, response.text[:300]
    assert params.get("api_key") == "sk-configured-secret"
    assert params.get("rpm") == 100


def test_operator_opt_in_restores_inheritance_for_a_caller_endpoint(health_call, auth, monkeypatch):
    from litellm.proxy import proxy_server

    monkeypatch.setitem(proxy_server.general_settings, "allow_client_side_credentials", True)
    response, params = health_call(
        auth, {"model": "gpt-4o", "api_base": "https://byok.example.test/v1"}
    )

    assert response.status_code == 200, response.text[:300]
    assert params.get("api_key") == "sk-configured-secret"


def test_stored_credential_reference_is_kept_when_no_connection_field_is_set(health_call, auth):
    response, params = health_call(
        auth, {"model": "stored-cred-model", "custom_llm_provider": "openai"}
    )

    assert response.status_code == 200, response.text[:300]
    assert params.get("litellm_credential_name") == "OpenAI-prod"
    assert params.get("api_key") == "sk-stored-cred-secret"
