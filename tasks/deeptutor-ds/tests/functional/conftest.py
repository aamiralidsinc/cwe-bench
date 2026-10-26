"""Options for the hidden security suite: isolate runtime state, stub transports."""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

HERE = Path(__file__).resolve().parent
for candidate in (HERE.parent / "support", Path("/workspace/.htests/support")):
    if candidate.is_dir() and str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))


@pytest.fixture(autouse=True)
def isolated_paths(tmp_path, monkeypatch):
    """Every grant/session lookup under this test's tmp_path."""
    from deeptutor.multi_user import grants, paths

    monkeypatch.setattr(grants, "GRANTS_DIR", tmp_path / "system" / "grants")
    monkeypatch.setattr(paths, "SYSTEM_ROOT", tmp_path / "system")
    monkeypatch.setattr(paths, "LEGACY_MULTI_USER_ROOT", tmp_path / "no-legacy-tree")
    monkeypatch.setattr(paths, "_legacy_migration_done", False)
    return tmp_path


@pytest.fixture(autouse=True)
def fake_llm_config(monkeypatch):
    monkeypatch.setattr(
        "deeptutor.agents.chat.agentic_pipeline.get_llm_config",
        lambda: SimpleNamespace(
            binding="openai",
            model="gpt-test",
            api_key="k",
            base_url="http://127.0.0.1:9",
            api_version=None,
            extra_headers={},
            reasoning_effort=None,
        ),
    )


@pytest.fixture(autouse=True)
def fake_mcp(tmp_path, monkeypatch):
    """No MCP connections; per-session loaded-tool state in tmp_path."""
    import deeptutor.services.mcp as mcp_pkg
    import deeptutor.services.mcp.session_state as session_state

    class _Manager:
        async def ensure_started(self) -> None:
            return None

    monkeypatch.setattr(mcp_pkg, "get_mcp_manager", lambda: _Manager())
    state = tmp_path / "loaded_tools.json"
    monkeypatch.setattr(session_state, "_state_file", lambda session_id: state)
    return state


@pytest.fixture
def state_file(fake_mcp):
    return fake_mcp
