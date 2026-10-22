"""Memory written through the tool must be validated, including bulk imports."""
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


@pytest.fixture()
def store(mem_dir):
    s = MemoryStore()
    s.load_from_disk()
    return s


def _result(raw):
    data = json.loads(raw)
    assert isinstance(data, dict)
    return data


def _all_text(store):
    return "\n".join(store.memory_entries + store.user_entries)


def test_add_promptware_refused(store):
    before = _all_text(store)
    data = _result(memory_tool(action="add", target="memory", content=PAYLOAD, store=store))
    assert data["success"] is False
    assert data.get("error")
    assert MARKER not in _all_text(store)
    assert _all_text(store) == before


def test_add_promptware_leaves_disk_unchanged(store, mem_dir):
    data = _result(memory_tool(action="add", target="memory", content=PAYLOAD, store=store))
    assert data["success"] is False
    path = mem_dir / "MEMORY.md"
    assert not path.exists() or MARKER not in path.read_text(encoding="utf-8")


def test_replace_with_promptware_refused(store):
    assert _result(memory_tool(action="add", target="memory", content=CLEAN, store=store))["success"] is True
    data = _result(
        memory_tool(
            action="replace",
            target="memory",
            old_text="CLEAN-OK",
            content=PAYLOAD,
            store=store,
        )
    )
    assert data["success"] is False
    assert data.get("error")
    assert MARKER not in _all_text(store)
    assert any("CLEAN-OK" in entry for entry in store.memory_entries)


def test_bulk_import_promptware_refused(store, mem_dir):
    data = _result(
        memory_tool(
            action="import",
            target="memory",
            content=CLEAN + "\n§\n" + PAYLOAD,
            store=store,
        )
    )
    assert data["success"] is False
    assert data.get("error")
    # A refused write changes no state: the non-matching entries from the same
    # import must not be applied either.
    assert MARKER not in _all_text(store)
    assert not any("CLEAN-OK" in entry for entry in store.memory_entries)
    snapshot = store.format_for_system_prompt("memory") or ""
    assert MARKER not in snapshot
    assert "CLEAN-OK" not in snapshot
    path = mem_dir / "MEMORY.md"
    if path.exists():
        on_disk = path.read_text(encoding="utf-8")
        assert MARKER not in on_disk
        assert "CLEAN-OK" not in on_disk
