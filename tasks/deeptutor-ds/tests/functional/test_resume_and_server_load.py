"""Resumed conversations and server-wide loads keep working for allowed tools."""

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
    llm_chunk,
    run_turn,
    user,
    write_grant,
)
from deeptutor.core.context import UnifiedContext


@pytest.mark.asyncio
async def test_resume_restores_an_assigned_tool(monkeypatch, isolated_paths, state_file):
    write_grant(isolated_paths, "u_alice", {"mcp_tools": [SEARCH]})
    state_file.write_text(json.dumps({"loaded_tools": [SEARCH]}), encoding="utf-8")
    registry = default_registry()
    client = ScriptedClient([[llm_chunk(content="continue")]])

    with as_user(user("u_alice")):
        await run_turn(
            monkeypatch,
            registry,
            client,
            UnifiedContext(session_id="sess-resume-ok", user_message="continue"),
        )

    assert SEARCH in client.offered_names(0)


@pytest.mark.asyncio
async def test_resume_restores_for_an_administrator(monkeypatch, state_file):
    state_file.write_text(json.dumps({"loaded_tools": [WRITE]}), encoding="utf-8")
    registry = default_registry()
    client = ScriptedClient([[llm_chunk(content="continue")]])

    with as_user(admin_user()):
        await run_turn(
            monkeypatch,
            registry,
            client,
            UnifiedContext(session_id="sess-resume-admin", user_message="continue"),
        )

    assert WRITE in client.offered_names(0)


@pytest.mark.asyncio
async def test_server_wide_load_includes_assigned_tools(monkeypatch, isolated_paths):
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
                            "arguments": json.dumps({"server": "demo"}),
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
            UnifiedContext(session_id="sess-server-ok", user_message="load demo"),
        )

    assert SEARCH in client.offered_names(1)


@pytest.mark.asyncio
async def test_server_wide_load_works_for_an_administrator(monkeypatch):
    registry = default_registry()
    client = ScriptedClient(
        [
            [
                llm_chunk(
                    tool_calls=[
                        {
                            "id": "load-1",
                            "name": "load_tools",
                            "arguments": json.dumps({"server": "demo"}),
                        }
                    ]
                )
            ],
            [llm_chunk(content="done")],
        ]
    )

    with as_user(admin_user()):
        await run_turn(
            monkeypatch,
            registry,
            client,
            UnifiedContext(session_id="sess-server-admin", user_message="load demo"),
        )

    assert {SEARCH, WRITE} <= client.offered_names(1)
