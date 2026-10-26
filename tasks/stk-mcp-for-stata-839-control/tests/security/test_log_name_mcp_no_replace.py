"""A custom log name is still a file name when replacement is off (MCP tool)."""

import support


def test_line_break_is_blocked_when_not_replacing():
    token = support.marker()
    dofile = support.new_dofile("log_name_mcp_noreplace.do")
    support.reset_capture()
    support.clean_state()

    from stata_mcp import mcp_servers

    try:
        mcp_servers.stata_do(
            dofile.as_posix(),
            log_file_name="wave\n%s\n*" % support.command(token),
            is_replace_log=False,
        )
    except Exception:
        pass

    support.assert_no_injected_command(token)
