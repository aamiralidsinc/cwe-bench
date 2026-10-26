"""An ado package name is data, never Stata syntax (MCP tool, GitHub source)."""

import support


def test_line_break_in_package_name_does_not_run_a_command():
    token = support.marker()
    support.reset_capture()
    support.clean_state()

    from stata_mcp import mcp_servers

    try:
        mcp_servers.ado_package_install(
            "SepineTam/TexIV\n%s\n*" % support.command(token), source="github"
        )
    except Exception:
        pass

    support.assert_no_injected_command(token)
