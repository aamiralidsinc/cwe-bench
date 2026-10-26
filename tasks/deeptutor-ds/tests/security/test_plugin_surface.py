"""The tool tester surface reaches the same tools; it must respect assignments."""

from __future__ import annotations

import pytest

import deeptutor.api.routers.plugins_api as plugins_api
from harness import (
    SEARCH,
    WRITE,
    default_registry,
    executed_names,
    is_client_error,
    plugins_client,
    user,
    write_grant,
)


@pytest.fixture
def registry(monkeypatch):
    registry = default_registry()
    monkeypatch.setattr(plugins_api, "get_tool_registry", lambda: registry)
    return registry


@pytest.mark.parametrize("granted", [None, [SEARCH]])
def test_direct_tool_execution_refused(monkeypatch, isolated_paths, registry, granted):
    if granted is not None:
        write_grant(isolated_paths, "u_alice", {"mcp_tools": granted})
    with plugins_client(user("u_alice")) as client:
        response = client.post(
            f"/api/v1/plugins/tools/{WRITE}/execute", json={"params": {}}
        )
    assert is_client_error(response.status_code)
    assert WRITE not in executed_names(registry)


def test_streamed_tool_execution_refused(monkeypatch, isolated_paths, registry):
    write_grant(isolated_paths, "u_alice", {"mcp_tools": [SEARCH]})
    with plugins_client(user("u_alice")) as client:
        response = client.post(
            f"/api/v1/plugins/tools/{WRITE}/execute-stream", json={"params": {}}
        )
    events = [
        line[len("event: ") :]
        for line in response.text.splitlines()
        if line.startswith("event: ")
    ]
    assert "result" not in events
    assert WRITE not in executed_names(registry)


def test_tool_catalogue_hides_unassigned_tools(monkeypatch, isolated_paths, registry):
    write_grant(isolated_paths, "u_alice", {"mcp_tools": [SEARCH]})
    with plugins_client(user("u_alice")) as client:
        response = client.get("/api/v1/plugins/list")
    names = {tool["name"] for tool in response.json()["tools"]}
    assert response.status_code == 200
    assert WRITE not in names
