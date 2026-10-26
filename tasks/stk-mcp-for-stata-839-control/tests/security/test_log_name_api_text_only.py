"""A custom log name is still a file name when the SMCL log is disabled (Python API)."""

import support


def test_line_break_is_blocked_without_smcl():
    token = support.marker()
    dofile = support.new_dofile("log_name_api_text.do")
    support.reset_capture()
    support.clean_state()

    from stata_mcp.api import stata_do

    try:
        stata_do(
            dofile.as_posix(),
            log_file_name="wave\n%s\n*" % support.command(token),
            enable_smcl=False,
        )
    except Exception:
        pass

    support.assert_no_injected_command(token)
