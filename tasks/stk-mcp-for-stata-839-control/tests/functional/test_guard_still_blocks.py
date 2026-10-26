"""The product's dangerous-command guard keeps working."""

import support


def test_guard_still_refuses_a_dangerous_dofile():
    dofile = support.new_dofile("dangerous.do", content="shell echo hello\n")
    support.reset_capture()

    from stata_mcp.api import stata_do

    result = stata_do(dofile.as_posix())
    assert result.get("action") == "Security check, dofile not executed", result
    assert not support.chunks(), "the do-file reached Stata despite the guard"
