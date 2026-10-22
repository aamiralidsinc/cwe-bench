"""Clean Codex projections keep their documented shape."""
from agent.transports.codex_event_projector import CodexEventProjector

CLEAN_TEXT = "Found three notes about the project release checklist."


def _project(item):
    result = CodexEventProjector().project(
        {"method": "item/completed", "params": {"item": item}}
    )
    assert len(result.messages) == 2
    return result.messages


def test_clean_mcp_result_keeps_role_id_and_payload():
    msgs = _project(
        {
            "type": "mcpToolCall",
            "id": "m1",
            "server": "obsidian",
            "tool": "search_notes",
            "status": "completed",
            "arguments": {"query": "hermes"},
            "result": {"content": [{"text": CLEAN_TEXT}]},
            "error": None,
        }
    )
    assistant, tool = msgs
    assert assistant["tool_calls"][0]["function"]["name"] == "mcp.obsidian.search_notes"
    assert tool["role"] == "tool"
    assert tool["tool_call_id"] == assistant["tool_calls"][0]["id"]
    assert CLEAN_TEXT in tool["content"]


def test_command_projection_not_enveloped():
    msgs = _project(
        {
            "type": "commandExecution",
            "id": "c1",
            "command": "ls",
            "cwd": "/tmp",
            "aggregatedOutput": "a.txt\nb.txt",
            "exitCode": 0,
        }
    )
    tool = msgs[1]
    assert tool["role"] == "tool"
    assert "<untrusted_tool_result" not in tool["content"]
    assert "a.txt" in tool["content"]


def test_agent_message_projection_unchanged():
    result = CodexEventProjector().project(
        {
            "method": "item/completed",
            "params": {"item": {"type": "agentMessage", "id": "a1", "text": "hello"}},
        }
    )
    assert result.final_text == "hello"
    assert result.messages == [{"role": "assistant", "content": "hello"}]
