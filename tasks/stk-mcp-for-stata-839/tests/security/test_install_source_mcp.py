"""A network source address is data, never Stata syntax (MCP tool, net source)."""

import support


def test_line_break_in_source_address_does_not_run_a_command():
    token = support.marker()
    support.reset_capture()
    support.clean_state()

    from stata_mcp import mcp_servers

    try:
        mcp_servers.ado_package_install(
            "custompkg",
            source="net",
            package_source_from="https://example.com/stata/\n%s\n*" % support.command(token),
        )
    except Exception:
        pass

    support.assert_no_injected_command(token)
