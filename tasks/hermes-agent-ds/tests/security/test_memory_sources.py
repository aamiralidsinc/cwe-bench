"""Every memory source that feeds the model context must be checked."""
from helpers import MARKER, PAYLOAD, assert_blocked

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


def test_backend_prompt_block_blocked():
    manager = MemoryManager()
    manager.add_provider(StubProvider(PAYLOAD))
    out = manager.build_system_prompt()
    assert_blocked(out, MARKER)


def test_recalled_context_blocked():
    out = build_memory_context_block(PAYLOAD)
    assert_blocked(out, MARKER)
