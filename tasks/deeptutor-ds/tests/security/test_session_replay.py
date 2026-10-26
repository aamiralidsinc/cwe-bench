"""A resumed conversation must not restore tools the account may not use."""

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
async def test_resume_does_not_restore_unassigned_tool(
    monkeypatch, isolated_paths, state_file
):
    state_file.write_text(json.dumps({"loaded_tools": [WRITE]}), encoding="utf-8")
    registry = default_registry()
    client = ScriptedClient([[llm_chunk(content="hello again")]])

    with as_user(user("u_alice")):
        await run_turn(
            monkeypatch,
            registry,
            client,
            UnifiedContext(session_id="sess-resume-1", user_message="continue"),
        )

    assert WRITE not in client.offered_names(0)
    assert WRITE not in client.system_prompt(0)


@pytest.mark.asyncio
async def test_resume_respects_a_partial_assignment(
    monkeypatch, isolated_paths, state_file
):
    write_grant(isolated_paths, "u_alice", {"mcp_tools": [SEARCH]})
    state_file.write_text(json.dumps({"loaded_tools": [SEARCH, WRITE]}), encoding="utf-8")
    registry = default_registry()
    client = ScriptedClient([[llm_chunk(content="continue")]])

    with as_user(user("u_alice")):
        await run_turn(
            monkeypatch,
            registry,
            client,
            UnifiedContext(session_id="sess-resume-2", user_message="continue"),
        )

    assert WRITE not in client.offered_names(0)
