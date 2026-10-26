"""Partner turns keep the tool set their owner configured."""

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
)
from deeptutor.core.context import UnifiedContext


def _context(filter_names):
    metadata = {"source": "partner", "partner_id": "math-bot"}
    if filter_names is not None:
        metadata["mcp_tools_filter"] = list(filter_names)
    return UnifiedContext(
        session_id="partner:math-bot:chat-1",
        user_message="help",
        enabled_tools=["web_search"],
        metadata=metadata,
    )


@pytest.mark.asyncio
async def test_configured_partner_tool_runs(monkeypatch):
    registry = default_registry()
    client = ScriptedClient(
        [
            [llm_chunk(tool_calls=[{"id": "call-1", "name": SEARCH, "arguments": "{}"}])],
            [llm_chunk(content="done")],
        ]
    )
    with as_user(user("partner_math-bot")):
        await run_turn(monkeypatch, registry, client, _context([SEARCH]))

    assert SEARCH in client.system_prompt(0)
    assert SEARCH in executed_names(registry)
    assert WRITE not in client.system_prompt(0)


@pytest.mark.asyncio
async def test_configured_partner_tool_loads(monkeypatch):
    registry = default_registry()
    client = ScriptedClient(
        [
            [
                llm_chunk(
                    tool_calls=[
                        {
                            "id": "load-1",
                            "name": "load_tools",
                            "arguments": json.dumps({"names": [SEARCH]}),
                        }
                    ]
                )
            ],
            [llm_chunk(content="done")],
        ]
    )
    with as_user(user("partner_math-bot")):
        await run_turn(monkeypatch, registry, client, _context([SEARCH]))

    assert SEARCH in client.offered_names(1)


@pytest.mark.asyncio
async def test_partner_default_surface_is_unchanged(monkeypatch):
    registry = default_registry()
    client = ScriptedClient([[llm_chunk(content="hello")]])
    with as_user(user("partner_math-bot")):
        await run_turn(monkeypatch, registry, client, _context(None))

    assert SEARCH in client.system_prompt(0)
    assert WRITE in client.system_prompt(0)
