"""Clean memory sources still reach the model context."""
from agent.memory_manager import MemoryManager, build_memory_context_block
from agent.memory_provider import MemoryProvider


class StubProvider(MemoryProvider):
    name = "stub-memory"

    def __init__(self, block):
        self._block = block

    def is_available(self):
        return True

    def initialize(self, session_id, **kwargs):
        return None

    def get_tool_schemas(self):
        return []

    def system_prompt_block(self):
        return self._block


def test_clean_provider_block_included():
    manager = MemoryManager()
    manager.add_provider(StubProvider("Memory backend is connected for this user."))
    out = manager.build_system_prompt()
    assert "Memory backend is connected" in out
    assert "[BLOCKED:" not in out


def test_two_clean_provider_blocks_joined():
    class BuiltinProvider(StubProvider):
        name = "builtin"

    manager = MemoryManager()
    manager.add_provider(BuiltinProvider("First provider note."))
    manager.add_provider(StubProvider("Second provider note."))
    out = manager.build_system_prompt()
    assert "First provider note." in out
    assert "Second provider note." in out


def test_clean_recall_fenced_with_system_note():
    out = build_memory_context_block("Project uses pytest with xdist.")
    assert out.startswith("<memory-context>")
    assert out.rstrip().endswith("</memory-context>")
    assert "NOT new user input" in out
    assert "Project uses pytest with xdist." in out


def test_empty_recall_returns_empty():
    assert build_memory_context_block("") == ""
    assert build_memory_context_block("   ") == ""
