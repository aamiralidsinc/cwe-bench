"""An ado package name is data, never Stata syntax (Python API, SSC source)."""

import support


def test_line_break_in_package_name_does_not_run_a_command():
    token = support.marker()
    support.reset_capture()
    support.clean_state()

    from stata_mcp.api import ado_package_install

    try:
        ado_package_install("outreg2\n%s\n*" % support.command(token))
    except Exception:
        pass

    support.assert_no_injected_command(token)
