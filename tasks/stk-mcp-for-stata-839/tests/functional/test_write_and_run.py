"""A do-file created by the product can be executed by the same session."""

import support


def test_written_dofile_runs_through_the_documented_api():
    from stata_mcp.api import stata_do, write_dofile

    support.reset_capture()
    path = write_dofile("display 1\n")
    result = stata_do(path)
    assert "error" not in result, result
    assert ('do "%s"' % path) in support.lines()
