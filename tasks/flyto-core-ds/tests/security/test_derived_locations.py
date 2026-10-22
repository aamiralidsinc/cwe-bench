"""Files a run derives beside a caller-chosen location are locations too: the
atomic temp file of a dedup hash store, and the item log and metadata temp file
of a pagination checkpoint. Each test runs one module through POST /v1/execute
with a symbolic link at the derived name that points outside the operator's
sandbox, and asserts that the run is refused and that nothing outside changes."""
import os

from conftest import refused, snapshot


def _blocked(outside, before, status, data):
    assert refused(status, data), f"run was not refused: {status} {data}"
    assert snapshot(outside) == before, "the run changed files outside the sandbox"


def test_data_dedup_tmp_sibling_through_symlink(run, inside, outside):
    """The hash file is rewritten through a temp file kept beside it."""
    state = inside / "state"
    state.mkdir()
    victim = outside / "victim.json"
    victim.write_text("precious")
    os.symlink(victim, state / "seen.tmp")
    before = snapshot(outside)
    status, data = run("data.dedup", {
        "items": [{"a": 1}, {"a": 2}], "keys": ["a"],
        "hash_file": str(state / "seen.json"),
    })
    _blocked(outside, before, status, data)
    assert victim.read_text() == "precious"


def test_browser_pagination_items_file_through_symlink(run, browser_session, inside, outside):
    """The resume state is appended to an item file derived from the checkpoint."""
    state = inside / "state"
    state.mkdir()
    victim = outside / "items.jsonl"
    victim.write_text("precious\n")
    os.symlink(victim, state / "progress.jsonl")
    sid = browser_session(fail_after_first=False)
    before = snapshot(outside)
    status, data = run("browser.pagination", {
        "item_selector": ".item", "checkpoint_path": str(state / "progress.json"),
        "max_pages": 1, "wait_between_pages_ms": 0,
    }, {"browser_session": sid})
    _blocked(outside, before, status, data)
    assert victim.read_text() == "precious\n"


def test_browser_pagination_metadata_tmp_through_symlink(run, browser_session, inside, outside):
    """The checkpoint metadata is written through a temp file kept beside it."""
    state = inside / "state"
    state.mkdir()
    victim = outside / "meta.json"
    victim.write_text("precious")
    os.symlink(victim, state / "progress.tmp")
    sid = browser_session(fail_after_first=False)
    before = snapshot(outside)
    status, data = run("browser.pagination", {
        "item_selector": ".item", "checkpoint_path": str(state / "progress.json"),
        "max_pages": 1, "wait_between_pages_ms": 0,
    }, {"browser_session": sid})
    _blocked(outside, before, status, data)
    assert victim.read_text() == "precious"
