"""The documented custom log name form keeps working verbatim."""

from pathlib import Path

import support


def test_documented_custom_log_name_is_used_verbatim():
    dataset = "wave1.dta"
    name = "analysis_%s" % dataset
    dofile = support.new_dofile("custom_log.do")
    support.reset_capture()

    from stata_mcp.api import stata_do

    result = stata_do(dofile.as_posix(), log_file_name=name)
    assert "error" not in result, result

    text_path = Path(result["log_file_path"]["text"])
    assert text_path.name == "analysis_wave1.dta.log", text_path
    assert text_path.parent == support.WORK / ".statamcp" / "stata-mcp-log"
    assert ('log using "%s", replace text name(text_log)' % text_path.as_posix()) in support.lines()


def test_custom_log_name_is_returned_to_the_caller():
    dofile = support.new_dofile("custom_log_returned.do")
    support.reset_capture()

    from stata_mcp.api import stata_do

    result = stata_do(dofile.as_posix(), log_file_name="my_results", enable_smcl=False)
    assert "error" not in result, result
    assert Path(result["log_file_path"]["text"]).name == "my_results.log"
