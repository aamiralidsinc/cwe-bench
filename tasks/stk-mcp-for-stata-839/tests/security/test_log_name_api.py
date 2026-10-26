"""A custom log name is a file name for the tool, never Stata syntax (Python API)."""

import support


def test_line_break_in_log_name_does_not_run_a_command():
    token = support.marker()
    dofile = support.new_dofile("log_name_api.do")
    support.reset_capture()
    support.clean_state()

    from stata_mcp.api import stata_do

    try:
        stata_do(dofile.as_posix(), log_file_name="wave\n%s\n*" % support.command(token))
    except Exception:
        pass

    support.assert_no_injected_command(token)
