"""Grant resolution: an account with no explicit MCP grant has no MCP tools.

Every input form the grant loader accepts (or rejects) must resolve to the
same outcome: nothing is offered, nothing can be loaded.
"""

from __future__ import annotations

import json

import pytest

from harness import (
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


def _batch():
    return [
        [
            llm_chunk(
                tool_calls=[
                    {
                        "id": "load-1",
                        "name": "load_tools",
                        "arguments": json.dumps({"names": [WRITE]}),
                    },
                    {"id": "call-1", "name": WRITE, "arguments": "{}"},
                ]
            )
        ],
        [llm_chunk(content="done")],
    ]


def _write_shape(root, shape: str) -> None:
    grants = root / "system" / "grants"
    if shape == "missing_file":
        return
    if shape == "corrupt":
        write_grant(root, "u_alice", None)
        return
    grants.mkdir(parents=True, exist_ok=True)
    if shape == "v1_absent":
        (grants / "u_alice.json").write_text(json.dumps({"version": 1, "models": {"llm": []}}))
        return
    if shape == "null":
        write_grant(root, "u_alice", {"mcp_tools": None})
        return
    if shape == "non_list":
        write_grant(root, "u_alice", {"mcp_tools": WRITE})
        return
    raise AssertionError(shape)


@pytest.mark.parametrize("shape", ["missing_file", "corrupt", "v1_absent", "null", "non_list"])
@pytest.mark.asyncio
async def test_unassigned_account_has_no_mcp_tools(monkeypatch, isolated_paths, shape):
    root = isolated_paths
    _write_shape(root, shape)
    registry = default_registry()
    client = ScriptedClient(_batch())

    with as_user(user("u_alice")):
        await run_turn(
            monkeypatch,
            registry,
            client,
            UnifiedContext(session_id="sess-shape", user_message="use the write tool"),
        )

    # Not advertised to the model and not loadable.
    assert WRITE not in client.system_prompt(0)
    assert WRITE not in client.offered_names(1)
