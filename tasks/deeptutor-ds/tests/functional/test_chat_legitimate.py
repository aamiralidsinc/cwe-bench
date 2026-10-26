"""Legitimate chat use keeps working next to the assignment check."""

from __future__ import annotations

import json

import pytest

from harness import (
    SEARCH,
    WRITE,
    ScriptedClient,
    admin_user,
    as_user,
    default_registry,
    executed_names,
    llm_chunk,
    run_turn,
    user,
    write_grant,
)
from deeptutor.core.context import UnifiedContext


def _invoke(name: str):
    return [
        [llm_chunk(tool_calls=[{"id": "call-1", "name": name, "arguments": "{}"}])],
        [llm_chunk(content="done")],
    ]


def _load_then_invoke(name: str):
    return [
        [
            llm_chunk(
                tool_calls=[
                    {
                        "id": "load-1",
                        "name": "load_tools",
                        "arguments": json.dumps({"names": [name]}),
                    }
                ]
            )
        ],
        [llm_chunk(tool_calls=[{"id": "call-1", "name": name, "arguments": "{}"}])],
        [llm_chunk(content="done")],
    ]


@pytest.mark.asyncio
async def test_administrator_keeps_full_access(monkeypatch):
    registry = default_registry()
    client = ScriptedClient(_load_then_invoke(WRITE))

    with as_user(admin_user()):
        await run_turn(
            monkeypatch,
            registry,
            client,
            UnifiedContext(
                session_id="sess-admin",
                user_message="use the write tool",
                enabled_tools=["web_search"],
            ),
        )

    assert WRITE in client.system_prompt(0)
    assert WRITE in client.offered_names(1)
    assert WRITE in executed_names(registry)


@pytest.mark.asyncio
async def test_assigned_tool_loads_and_runs(monkeypatch, isolated_paths):
    write_grant(isolated_paths, "u_alice", {"mcp_tools": [SEARCH]})
    registry = default_registry()
    client = ScriptedClient(_load_then_invoke(SEARCH))

    with as_user(user("u_alice")):
        await run_turn(
            monkeypatch,
            registry,
            client,
            UnifiedContext(
                session_id="sess-granted",
                user_message="use the search tool",
                enabled_tools=["web_search"],
            ),
        )

    assert SEARCH in client.system_prompt(0)
    assert SEARCH in client.offered_names(1)
    assert SEARCH in executed_names(registry)


@pytest.mark.asyncio
async def test_ordinary_tools_stay_available_without_an_assignment(monkeypatch, isolated_paths):
    registry = default_registry()
    client = ScriptedClient(_invoke("web_search"))

    with as_user(user("u_alice")):
        await run_turn(
            monkeypatch,
            registry,
            client,
            UnifiedContext(
                session_id="sess-builtin",
                user_message="search the web",
                enabled_tools=["web_search"],
            ),
        )

    assert "web_search" in executed_names(registry)


@pytest.mark.asyncio
async def test_explicit_empty_assignment_keeps_ordinary_tools(monkeypatch, isolated_paths):
    write_grant(isolated_paths, "u_alice", {"mcp_tools": []})
    registry = default_registry()
    client = ScriptedClient(_invoke("web_search"))

    with as_user(user("u_alice")):
        await run_turn(
            monkeypatch,
            registry,
            client,
            UnifiedContext(
                session_id="sess-empty",
                user_message="search the web",
                enabled_tools=["web_search"],
            ),
        )

    assert "web_search" in executed_names(registry)
    assert SEARCH not in client.system_prompt(0)
    assert WRITE not in client.system_prompt(0)


@pytest.mark.asyncio
async def test_partial_assignment_narrows_the_surface(monkeypatch, isolated_paths):
    write_grant(isolated_paths, "u_alice", {"mcp_tools": [SEARCH]})
    registry = default_registry()
    client = ScriptedClient(
        [
            [
                llm_chunk(
                    tool_calls=[
                        {
                            "id": "load-1",
                            "name": "load_tools",
                            "arguments": json.dumps({"names": [WRITE]}),
                        }
                    ]
                )
            ],
            [llm_chunk(content="done")],
        ]
    )

    with as_user(user("u_alice")):
        await run_turn(
            monkeypatch,
            registry,
            client,
            UnifiedContext(session_id="sess-narrow", user_message="use the write tool"),
        )

    assert SEARCH in client.system_prompt(0)
    assert WRITE not in client.system_prompt(0)
    assert WRITE not in client.offered_names(1)
