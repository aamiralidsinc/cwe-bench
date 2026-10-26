"""Loading a whole server must not widen what the account may use."""

from __future__ import annotations

import json

import pytest

from harness import (
    SEARCH,
    WRITE,
    ScriptedClient,
    as_user,
    default_registry,
    llm_chunk,
    run_turn,
    user,
    write_grant,
)
from deeptutor.core.context import UnifiedContext


@pytest.mark.asyncio
async def test_server_wide_load_keeps_the_assignment(monkeypatch, isolated_paths):
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
            UnifiedContext(session_id="sess-server-1", user_message="load the demo server"),
        )

    assert WRITE not in client.offered_names(1)
