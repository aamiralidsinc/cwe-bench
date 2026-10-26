"""Running a do-file with no custom log name keeps its documented behaviour."""

from pathlib import Path

import support


def test_default_log_name_is_a_timestamp_inside_the_log_directory():
    dofile = support.new_dofile("default_log.do")
    support.reset_capture()

    from stata_mcp.api import stata_do

    result = stata_do(dofile.as_posix())
    assert "error" not in result, result

    text_path = Path(result["log_file_path"]["text"])
    smcl_path = Path(result["log_file_path"]["smcl"])
    log_dir = support.WORK / ".statamcp" / "stata-mcp-log"
    assert text_path.parent == log_dir, text_path
    assert smcl_path.parent == log_dir, smcl_path

    stem = text_path.name[: -len(".log")]
    assert stem.isdigit(), stem
    assert len(stem) == 14, stem
    assert smcl_path.name == stem + ".smcl"

    sent = support.lines()
    assert ('log using "%s", replace text name(text_log)' % text_path.as_posix()) in sent
    assert ('log using "%s", replace smcl name(smcl_log)' % smcl_path.as_posix()) in sent
    assert ('do "%s"' % dofile.as_posix()) in sent


def test_smcl_can_be_disabled_without_changing_the_text_log():
    dofile = support.new_dofile("default_log_no_smcl.do")
    support.reset_capture()

    from stata_mcp.api import stata_do

    result = stata_do(dofile.as_posix(), enable_smcl=False)
    assert "error" not in result, result
    assert set(result["log_file_path"]) == {"text"}
    assert not any("smcl" in line and line.startswith("log using") for line in support.lines())
