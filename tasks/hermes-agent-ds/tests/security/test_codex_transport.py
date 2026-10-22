"""The alternate Codex transport must not bypass the untrusted-data framing."""
from helpers import PAYLOAD, assert_enveloped

from agent.transports.codex_event_projector import CodexEventProjector


def _mcp_event(text, item_id="m1"):
    return {
        "method": "item/completed",
        "params": {
            "item": {
                "type": "mcpToolCall",
                "id": item_id,
                "server": "evil",
                "tool": "read",
                "status": "completed",
                "arguments": {"query": "x"},
                "result": {"content": [{"text": text}]},
                "error": None,
            }
        },
    }


def test_codex_mcp_result_enveloped():
    result = CodexEventProjector().project(_mcp_event(PAYLOAD))
    assert len(result.messages) == 2
    tool_msg = result.messages[1]
    assert tool_msg["role"] == "tool"
    source = assert_enveloped(tool_msg["content"], PAYLOAD, source_substr="mcp")
    assert "evil" in source and "read" in source


def test_codex_mcp_namespaced_tool_name_keeps_envelope():
    result = CodexEventProjector().project(_mcp_event(PAYLOAD))
    name = result.messages[0]["tool_calls"][0]["function"]["name"]
    assert name == "mcp.evil.read"
    assert_enveloped(result.messages[1]["content"], PAYLOAD, source_substr="mcp")
