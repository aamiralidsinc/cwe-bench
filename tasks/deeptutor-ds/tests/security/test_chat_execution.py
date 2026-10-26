"""Invocation: a tool the turn may not use is never executed.

The model can name any tool in a turn's tool calls. The account's assignment
decides whether the call runs; a name outside it is refused.
"""

from __future__ import annotations

import json

import pytest

from harness import (
    SEARCH,
    WRITE,
    ScriptedClient,
    as_user,
    default_registry,
    executed_names,
    llm_chunk,
    run_turn,
    user,
    write_grant,
)
from deeptutor.core.context import UnifiedContext


def _direct(name: str):
    return [
        [llm_chunk(tool_calls=[{"id": "call-1", "name": name, "arguments": "{}"}])],
        [llm_chunk(content="done")],
    ]


@pytest.mark.asyncio
async def test_unassigned_account_cannot_invoke_mcp_tool(monkeypatch, isolated_paths):
    registry = default_registry()
    client = ScriptedClient(_direct(WRITE))

    with as_user(user("u_alice")):
        await run_turn(
            monkeypatch,
            registry,
            client,
            UnifiedContext(session_id="sess-invoke-1", user_message="run it"),
        )

    assert WRITE not in executed_names(registry)


@pytest.mark.asyncio
async def test_assigned_tool_does_not_open_its_siblings(monkeypatch, isolated_paths):
    write_grant(isolated_paths, "u_alice", {"mcp_tools": [SEARCH]})
    registry = default_registry()
    client = ScriptedClient(_direct(WRITE))

    with as_user(user("u_alice")):
        await run_turn(
            monkeypatch,
            registry,
            client,
            UnifiedContext(session_id="sess-invoke-2", user_message="run it"),
        )

    assert WRITE not in executed_names(registry)


@pytest.mark.asyncio
async def test_loading_is_not_a_way_to_invoke(monkeypatch, isolated_paths):
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
            [llm_chunk(tool_calls=[{"id": "call-1", "name": WRITE, "arguments": "{}"}])],
            [llm_chunk(content="done")],
        ]
    )

    with as_user(user("u_alice")):
        await run_turn(
            monkeypatch,
            registry,
            client,
            UnifiedContext(session_id="sess-invoke-3", user_message="load then run it"),
        )

    assert WRITE not in executed_names(registry)
