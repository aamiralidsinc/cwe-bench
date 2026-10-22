"""Legitimate use next to the derived-location guards: a caller-chosen location
inside the sandbox may still have its own pre-existing temp file or item file,
and the run keeps working exactly as today."""


def _ok(status, data):
    assert status == 200, (status, data)
    assert data.get("ok") is True, data
    inner = data.get("data")
    if isinstance(inner, dict) and "ok" in inner:
        assert inner["ok"] is True, inner


def test_data_dedup_inside_with_stale_tmp_file(run, inside):
    state = inside / "state"
    state.mkdir()
    (state / "seen.tmp").write_text("stale")
    hashes = state / "seen.json"
    _ok(*run("data.dedup", {
        "items": [{"a": 1}, {"a": 1}], "keys": ["a"], "hash_file": str(hashes),
    }))
    assert hashes.is_file()
    status, data = run("data.dedup", {
        "items": [{"a": 1}, {"a": 2}], "keys": ["a"], "hash_file": str(hashes),
    })
    _ok(status, data)
    assert data["data"]["items"] == [{"a": 2}]


def test_browser_pagination_stale_siblings_inside(run, browser_session, inside):
    state = inside / "state"
    state.mkdir()
    (state / "progress.jsonl").write_text("")
    (state / "progress.tmp").write_text("stale")
    sid = browser_session(fail_after_first=True)
    status, data = run("browser.pagination", {
        "item_selector": ".item", "checkpoint_path": str(state / "progress.json"),
        "max_pages": 3, "wait_between_pages_ms": 0, "no_more_indicator": ".end",
    }, {"browser_session": sid})
    _ok(status, data)
    assert (state / "progress.json").is_file()
    assert (state / "progress.jsonl").is_file()
