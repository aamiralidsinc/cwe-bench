"""Do-file paths that work today keep working."""

from pathlib import Path

import support


def _run(dofile):
    support.reset_capture()
    from stata_mcp.api import stata_do

    result = stata_do(dofile.as_posix())
    assert "error" not in result, result
    return result


def test_absolute_path_with_spaces_is_executed():
    dofile = support.new_dofile("quarterly report 2026.do")
    _run(dofile)
    assert ('do "%s"' % dofile.as_posix()) in support.lines()


def test_nested_relative_style_path_is_executed():
    dofile = support.new_dofile("reports/weekly.do")
    _run(dofile)
    assert ('do "%s"' % dofile.as_posix()) in support.lines()


def test_non_ascii_file_name_is_executed():
    dofile = support.new_dofile("季度报告.do")
    _run(dofile)
    assert ('do "%s"' % dofile.as_posix()) in support.lines()


def test_log_paths_stay_in_the_log_directory():
    dofile = support.new_dofile("log_location.do")
    result = _run(dofile)
    log_dir = support.WORK / ".statamcp" / "stata-mcp-log"
    for path in result["log_file_path"].values():
        assert Path(path).parent == log_dir, path
