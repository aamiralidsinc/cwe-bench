"""The do-file directory boundary keeps refusing files outside the allowed roots."""

import support


def test_dofile_outside_the_allowed_roots_is_refused():
    outside = support.ROOT / "outside" / "blocked.do"
    outside.parent.mkdir(parents=True, exist_ok=True)
    outside.write_text("display 1\n", encoding="utf-8")
    support.reset_capture()

    from stata_mcp.api import stata_do

    result = stata_do(outside.as_posix())
    assert "error" in result, result
    assert "Access denied" in result["error"], result
    assert not support.chunks(), "a refused do-file still reached Stata"
