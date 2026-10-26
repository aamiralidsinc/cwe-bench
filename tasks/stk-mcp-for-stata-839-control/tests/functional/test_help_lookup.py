"""Documented help lookups keep working through both public surfaces."""

import support


def test_python_api_help_lookup_returns_text():
    support.reset_capture()
    support.clean_state()
    from stata_mcp.api import stata_help

    text = stata_help("regress")
    assert isinstance(text, str) and text.strip()
    assert "help regress" in support.lines()


def test_mcp_tool_help_lookup_returns_text():
    support.reset_capture()
    support.clean_state()
    from stata_mcp import mcp_servers

    text = mcp_servers.help("xtreg")
    assert isinstance(text, str) and text.strip()
    assert "help xtreg" in support.lines()
