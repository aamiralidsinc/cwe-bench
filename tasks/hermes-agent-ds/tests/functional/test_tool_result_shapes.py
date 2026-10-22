"""The envelope must not disturb shapes that are not plain third-party strings."""
from helpers import PAYLOAD

from agent.tool_dispatch_helpers import make_tool_result_message

LOW_RISK = ["terminal", "read_file", "write_file", "patch", "memory", "skill_view"]


def test_low_risk_tool_unchanged():
    for name in LOW_RISK:
        msg = make_tool_result_message(name, PAYLOAD, "call_1")
        assert msg["content"] == PAYLOAD
        assert "<untrusted_tool_result" not in msg["content"]


def test_short_external_result_unchanged():
    short = "ok: 3 results"
    msg = make_tool_result_message("web_search", short, "call_1")
    assert msg["content"] == short


def test_multimodal_content_keeps_list_identity():
    content = [
        {"type": "text", "text": "page contents"},
        {"type": "image_url", "image_url": {"url": "data:image/png;base64,AAAA"}},
    ]
    msg = make_tool_result_message("browser_snapshot", content, "call_1")
    assert msg["content"] is content
    assert isinstance(msg["content"], list)


def test_already_enveloped_content_not_wrapped_again():
    already = (
        '<untrusted_tool_result source="web_extract">\n'
        "pre-wrapped payload\n"
        "</untrusted_tool_result>"
    )
    msg = make_tool_result_message("mcp_linear_get_issue", already, "call_1")
    assert msg["content"] == already
    assert msg["content"].count("<untrusted_tool_result") == 1


def test_none_and_empty_content_unchanged():
    assert make_tool_result_message("web_extract", None, "c")["content"] is None
    assert make_tool_result_message("web_extract", "", "c")["content"] == ""


def test_message_schema_fields_preserved():
    msg = make_tool_result_message("web_extract", PAYLOAD, "call_9")
    assert msg["role"] == "tool"
    assert msg["name"] == "web_extract"
    assert msg["tool_name"] == "web_extract"
    assert msg["tool_call_id"] == "call_9"
