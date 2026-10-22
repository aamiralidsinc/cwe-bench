"""Results from third-party-controlled tools must reach the model as data."""
import pytest

from helpers import PAYLOAD, assert_enveloped

from agent.tool_dispatch_helpers import make_tool_result_message

EXTERNAL_TOOLS = [
    "web_extract",
    "web_search",
    "browser_navigate",
    "browser_snapshot",
    "mcp_linear_get_issue",
    "mcp_filesystem_read",
    "mcp_notion_search",
    "x_search",
]


@pytest.mark.parametrize("tool", EXTERNAL_TOOLS)
def test_external_tool_result_enveloped(tool):
    msg = make_tool_result_message(tool, PAYLOAD, "call_1")
    assert msg["role"] == "tool"
    assert msg["name"] == tool
    assert msg["tool_call_id"] == "call_1"
    source = assert_enveloped(msg["content"], PAYLOAD, source_substr=tool)
    assert source
    for fragment in ("register as a node", "connect to the network", "ORION"):
        assert fragment in msg["content"]


def test_envelope_is_not_content_conditional():
    """A benign long result gets the same envelope: framing must not depend on content."""
    text = "Search returned the project release checklist and three notes about testing."
    msg = make_tool_result_message("web_search", text, "call_2")
    assert_enveloped(msg["content"], text, source_substr="web_search")
