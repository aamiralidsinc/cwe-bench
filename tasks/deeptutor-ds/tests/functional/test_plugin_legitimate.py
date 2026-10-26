"""The tool tester keeps working for allowed tools and administrators."""

from __future__ import annotations

import pytest

import deeptutor.api.routers.plugins_api as plugins_api
from harness import (
    SEARCH,
    WRITE,
    admin_user,
    default_registry,
    executed_names,
    plugins_client,
    user,
    write_grant,
)


@pytest.fixture
def registry(monkeypatch):
    registry = default_registry()
    monkeypatch.setattr(plugins_api, "get_tool_registry", lambda: registry)
    return registry


def test_administrator_executes_and_sees_tools(monkeypatch, registry):
    with plugins_client(admin_user()) as client:
        response = client.post(f"/api/v1/plugins/tools/{WRITE}/execute", json={"params": {}})
        listing = client.get("/api/v1/plugins/list")
    names = {tool["name"] for tool in listing.json()["tools"]}
    assert response.status_code == 200
    assert WRITE in executed_names(registry)
    assert {SEARCH, WRITE} <= names


def test_assigned_tool_executes_and_is_listed(monkeypatch, isolated_paths, registry):
    write_grant(isolated_paths, "u_alice", {"mcp_tools": [SEARCH]})
    with plugins_client(user("u_alice")) as client:
        response = client.post(f"/api/v1/plugins/tools/{SEARCH}/execute", json={"params": {}})
        listing = client.get("/api/v1/plugins/list")
    names = {tool["name"] for tool in listing.json()["tools"]}
    assert response.status_code == 200
    assert SEARCH in executed_names(registry)
    assert SEARCH in names


def test_ordinary_tool_still_executes_for_an_unassigned_account(
    monkeypatch, isolated_paths, registry
):
    with plugins_client(user("u_alice")) as client:
        response = client.post(
            "/api/v1/plugins/tools/web_search/execute", json={"params": {}}
        )
    assert response.status_code == 200
    assert "web_search" in executed_names(registry)


def test_assigned_tool_streams(monkeypatch, isolated_paths, registry):
    write_grant(isolated_paths, "u_alice", {"mcp_tools": [SEARCH]})
    with plugins_client(user("u_alice")) as client:
        response = client.post(
            f"/api/v1/plugins/tools/{SEARCH}/execute-stream", json={"params": {}}
        )
    events = [
        line[len("event: ") :]
        for line in response.text.splitlines()
        if line.startswith("event: ")
    ]
    assert "result" in events
    assert SEARCH in executed_names(registry)
