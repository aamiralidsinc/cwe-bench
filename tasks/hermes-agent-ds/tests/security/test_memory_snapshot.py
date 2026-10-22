"""Memory loaded from disk must not inject into the frozen system-prompt snapshot."""
import pytest

from helpers import CLEAN, MARKER, PAYLOAD, assert_blocked

from tools.memory_tool import MemoryStore


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


def test_poisoned_memory_file_replaced_in_snapshot(mem_dir):
    store = _load(mem_dir, "MEMORY.md", CLEAN + "\n§\n" + PAYLOAD)
    snapshot = store.format_for_system_prompt("memory")
    assert_blocked(snapshot, MARKER)
    assert "CLEAN-OK" in snapshot


def test_poisoned_user_file_replaced_in_snapshot(mem_dir):
    store = _load(mem_dir, "USER.md", PAYLOAD)
    snapshot = store.format_for_system_prompt("user")
    assert_blocked(snapshot, MARKER)


def test_promptware_planted_after_clean_entry_blocked(mem_dir):
    """Ordering must not matter: a clean first entry cannot hide a poisoned second one."""
    store = _load(mem_dir, "MEMORY.md", CLEAN + "\n§\n" + PAYLOAD)
    snapshot = store.format_for_system_prompt("memory")
    assert_blocked(snapshot, MARKER, "register as a node")
