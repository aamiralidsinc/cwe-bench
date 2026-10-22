"""Shared harness for the hidden behavioural tests.

The tests drive the real proxy application over HTTP with FastAPI's TestClient
(in-process, no listening socket). Provider calls are stubbed at the outbound
callable so no request ever leaves the process; a session-wide socket guard
turns any accidental outbound attempt into an immediate failure.
"""

import asyncio
import json
import os
import socket
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

os.environ.setdefault("LITELLM_LOG", "ERROR")
os.environ["LITELLM_TELEMETRY"] = "False"
os.environ["LITELLM_DONT_SHOW_FEEDBACK_BOX"] = "True"
os.environ["DISABLE_SCHEMA_UPDATE"] = "True"

import litellm

litellm.suppress_debug_info = True

# A configured gateway: one ordinary deployment, one whose name contains a
# provider prefix (a legitimate deployment name, not a URL), one provider
# wildcard used by pattern routing, one moderation deployment, and one
# deployment that references a stored credential.
CONFIG = """
model_list:
  - model_name: "gpt-4o"
    litellm_params:
      model: "openai/gpt-4o"
      api_key: "sk-configured-secret"
      api_base: "https://configured.example.test/v1"
  - model_name: "openai/gpt-4o"
    litellm_params:
      model: "openai/gpt-4o"
      api_key: "sk-second-secret"
  - model_name: "huggingface/*"
    litellm_params:
      model: "huggingface/*"
      api_key: "hf-configured-secret"
  - model_name: "text-moderation-stable"
    litellm_params:
      model: "openai/text-moderation-stable"
      api_key: "sk-moderation-secret"
  - model_name: "stored-cred-model"
    litellm_params:
      model: "openai/gpt-4o"
      api_key: "sk-stored-cred-secret"
      litellm_credential_name: "OpenAI-prod"
general_settings:
  master_key: "sk-1234"
files_settings:
  - custom_llm_provider: openai
    api_key: "sk-files-secret"
"""


def _blocked(*args, **kwargs):
    raise AssertionError("outbound network access attempted by a hidden test")


@pytest.fixture(scope="session", autouse=True)
def no_network():
    """Fail the test if product or test code opens an outbound connection."""
    with patch.object(socket.socket, "connect", _blocked), patch.object(
        socket.socket, "connect_ex", _blocked
    ), patch.object(socket, "create_connection", _blocked), patch.object(
        socket, "getaddrinfo", _blocked
    ):
        yield


@pytest.fixture(scope="session")
def client(no_network):
    """Initialise the real proxy app once and return a TestClient for it."""
    from litellm.proxy.proxy_server import (
        app,
        cleanup_router_config_variables,
        initialize,
    )

    cleanup_router_config_variables()
    tmpdir = tempfile.mkdtemp(prefix="litellm-hidden-")
    config_fp = str(Path(tmpdir) / "config.yaml")
    with open(config_fp, "w") as f:
        f.write(CONFIG)

    asyncio.run(initialize(config=config_fp, debug=False))

    from fastapi.testclient import TestClient

    # Not entered as a context manager: the app lifespan (DB/worker startup) is
    # not needed for these routes.
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture
def auth():
    return {"Authorization": "Bearer sk-1234"}


@pytest.fixture(autouse=True)
def _reset_destination_allowlist():
    """Each test starts with no operator-allowed destination hosts."""
    previous = getattr(litellm, "provider_url_destination_allowed_hosts", [])
    litellm.provider_url_destination_allowed_hosts = []
    try:
        yield
    finally:
        litellm.provider_url_destination_allowed_hosts = previous


def _stub_response():
    response = MagicMock()
    response._hidden_params = {}
    response.model = "stub-model"
    response.id = "stub-id"
    response.object = "stub"
    response.choices = []
    response.data = []
    response.results = []
    response.usage = None
    return response


class _StubOutbound:
    """Context manager that replaces the outbound provider callables.

    Both the module-level callable and the router's bound callable are replaced
    with the same AsyncMock: the router captures its callables when it is built,
    so patching only the module would not intercept router-routed calls.
    """

    def __init__(self, *names):
        self.names = names
        self.mock = AsyncMock(return_value=_stub_response())
        self._patchers = []

    def __enter__(self):
        from litellm.proxy import proxy_server

        router = getattr(proxy_server, "llm_router", None)
        for name in self.names:
            self._patchers.append(patch.object(litellm, name, self.mock))
            if router is not None and hasattr(router, name):
                self._patchers.append(patch.object(router, name, self.mock))
        for patcher in self._patchers:
            patcher.start()
        return self

    def __exit__(self, *exc):
        for patcher in reversed(self._patchers):
            patcher.stop()
        return False


@pytest.fixture
def outbound():
    return _StubOutbound


def as_json(value):
    return json.dumps(value, default=str, sort_keys=True)
