"""A do-file path is a path for the tool, never Stata syntax (Python API)."""

import support


def test_line_break_in_dofile_name_does_not_run_a_command():
    token = support.marker()
    dofile = support.new_dofile("run\n%s\nz.do" % support.command(token))
    support.reset_capture()
    support.clean_state()

    from stata_mcp.api import stata_do

    try:
        stata_do(dofile.as_posix())
    except Exception:
        pass

    support.assert_no_injected_command(token)
