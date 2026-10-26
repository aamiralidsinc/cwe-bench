"""A documentation topic is data, never Stata syntax (MCP tool)."""

import support


def test_line_break_in_help_topic_does_not_run_a_command():
    token = support.marker()
    support.reset_capture()
    support.clean_state()

    from stata_mcp import mcp_servers

    try:
        mcp_servers.help("describe\n%s\n*" % support.command(token))
    except Exception:
        pass

    support.assert_no_injected_command(token)
