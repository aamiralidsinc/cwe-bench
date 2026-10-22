"""Legitimate memory behaviour must survive the hardening."""
import json

import pytest

from helpers import CLEAN, MARKER, PAYLOAD

from tools.memory_tool import MemoryStore, memory_tool


@pytest.fixture()
def mem_dir(tmp_path, monkeypatch):
    d = tmp_path / "memories"
    d.mkdir()
    monkeypatch.setattr("tools.memory_tool.get_memory_dir", lambda: d)
    return d


def _load(mem_dir, name, text):
    (mem_dir / name).write_text(text, encoding="utf-8")
    store = MemoryStore()
    store.load_from_disk()
    return store


def test_clean_entries_pass_through_snapshot(mem_dir):
    store = _load(mem_dir, "MEMORY.md", CLEAN + "\n§\nUser prefers terse responses.")
    snapshot = store.format_for_system_prompt("memory")
    assert "CLEAN-OK" in snapshot
    assert "terse responses" in snapshot
    assert "[BLOCKED:" not in snapshot


def test_clean_operational_wording_passes_snapshot(mem_dir):
    """Ordinary engineering words (node, network, script) are not threats."""
    entry = (
        "The release script runs on the build node; artifacts are shared over the network."
    )
    store = _load(mem_dir, "MEMORY.md", entry)
    snapshot = store.format_for_system_prompt("memory")
    assert "release script" in snapshot
    assert "[BLOCKED:" not in snapshot


def test_poisoned_entry_stays_in_live_state_and_is_removable(mem_dir):
    store = _load(mem_dir, "MEMORY.md", CLEAN + "\n§\n" + PAYLOAD)
    # Live state keeps the raw entry so the user can inspect it.
    assert any(MARKER in entry for entry in store.memory_entries)
    removed = store.remove("memory", MARKER)
    assert removed["success"] is True
    assert not any(MARKER in entry for entry in store.memory_entries)
    assert not (mem_dir / "MEMORY.md").read_text(encoding="utf-8").count(MARKER)


def test_already_blocked_entry_is_not_double_blocked(mem_dir):
    existing = (
        "[BLOCKED: MEMORY.md entry contained threat pattern(s): prompt_injection. "
        "Removed from system prompt.]"
    )
    store = _load(mem_dir, "MEMORY.md", existing + "\n§\nClean fact.")
    snapshot = store.format_for_system_prompt("memory")
    assert snapshot.count("[BLOCKED:") == 1
    assert "Clean fact" in snapshot


def test_snapshot_frozen_across_mid_session_add(mem_dir):
    store = _load(mem_dir, "MEMORY.md", "loaded at start")
    store.add("memory", "added later")
    snapshot = store.format_for_system_prompt("memory")
    assert "loaded at start" in snapshot
    assert "added later" not in snapshot


def test_clean_memory_add_and_replace(mem_dir):
    store = _load(mem_dir, "MEMORY.md", "")
    assert store.add("memory", "Python 3.12 project")["success"] is True
    assert store.replace("memory", "3.12", "Python 3.13 project")["success"] is True
    assert any("3.13" in entry for entry in store.memory_entries)


def test_clean_bulk_import_works(mem_dir):
    store = _load(mem_dir, "MEMORY.md", "")
    raw = memory_tool(
        action="import",
        target="memory",
        content="Fact A about the project.\n§\nFact B about the project.",
        store=store,
    )
    data = json.loads(raw)
    assert data["success"] is True
    assert any("Fact A" in entry for entry in store.memory_entries)
    assert any("Fact B" in entry for entry in store.memory_entries)
    snapshot = store.format_for_system_prompt("memory")
    assert "Fact A" in snapshot
    assert "Fact B" in snapshot


def test_clean_import_deduplicates(mem_dir):
    store = _load(mem_dir, "MEMORY.md", "Existing fact.")
    raw = memory_tool(
        action="import",
        target="memory",
        content="Existing fact.\n§\nNew fact.",
        store=store,
    )
    assert json.loads(raw)["success"] is True
    assert sum(1 for entry in store.memory_entries if entry == "Existing fact.") == 1
