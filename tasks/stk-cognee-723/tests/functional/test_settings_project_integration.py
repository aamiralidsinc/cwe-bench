"""The project's own settings-endpoint integration check (single-user posture).

Ported from the repository's conditional-authentication suite: with access
control off, the settings read reaches the default user and returns the
configured values instead of an authentication error.
"""

import importlib
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import support


def test_settings_endpoint_uses_the_default_user():
    settings_module = importlib.import_module("cognee.modules.settings.get_settings")
    auth_module = importlib.import_module("cognee.modules.users.methods.get_authenticated_user")

    default_user = SimpleNamespace(
        id=uuid4(), email="default@example.com", is_active=True, tenant_id=uuid4()
    )
    llm_config = SimpleNamespace(
        llm_provider="openai",
        llm_model="gpt-4o",
        llm_endpoint=None,
        llm_api_version=None,
        llm_api_key="test_key_1234567890",
    )
    vector_config = SimpleNamespace(
        vector_db_provider="lancedb",
        vector_db_url="localhost:5432",
        vector_db_key="test_vector_key",
    )

    client = support.make_client()
    with patch.object(settings_module, "get_llm_config", return_value=llm_config), patch.object(
        settings_module, "get_vectordb_config", return_value=vector_config
    ), patch.object(auth_module, "get_default_user", new_callable=AsyncMock) as get_default:
        get_default.return_value = default_user
        response = client.get("/api/v1/settings")

    assert get_default.call_count == 1
    assert response.status_code != 401
    body = response.json()
    assert body["llm"]["provider"] == "openai"
    assert body["llm"]["model"] == "gpt-4o"
    assert body["vectorDb"]["provider"] == "lancedb"
