"""Shared harness for the hidden tests.

Every tool call goes through the real agent loop: a scripted model answers the
loop's first turn with one tool call (the arguments a prompt-steered model would
produce) and its second turn with a final answer. The tool result is read back
from the conversation the loop hands to the model.

Bookkeeping (paths, expected values, clean-up) is computed here with the standard
library only, never with product helpers.
"""

from __future__ import annotations

import json
import os
import shutil
import sys
import uuid
from pathlib import Path
from types import SimpleNamespace

import pytest

AGENT_DIR = Path(os.environ.get("VT_AGENT_DIR", "/workspace/agent")).resolve()
if str(AGENT_DIR) not in sys.path:
    sys.path.insert(0, str(AGENT_DIR))

RUNS_DIR = AGENT_DIR / "runs"
UPLOADS_DIR = AGENT_DIR / "uploads"
SKILLS_DIR = AGENT_DIR / "src" / "skills"

FILE_ROOTS_ENV = "VIBE_TRADING_ALLOWED_FILE_ROOTS"

MARKER = "VT-PRIVATE-MARKER-7f3c1a"


class ScriptedLLM:
    """Stands in for the chat model: one tool call, then a final answer."""

    def __init__(self, tool_name: str, arguments: dict) -> None:
        self.tool_name = tool_name
        self.arguments = arguments
        self.calls = 0
        self.final_messages: list = []

    def stream_chat(self, messages, tools=None, on_text_chunk=None, **_kw):
        from src.providers.chat import LLMResponse, ToolCallRequest

        self.calls += 1
        if self.calls == 1:
            return LLMResponse(
                content=None,
                tool_calls=[ToolCallRequest(id="call_vt_1", name=self.tool_name,
                                            arguments=dict(self.arguments))],
                finish_reason="tool_calls",
            )
        self.final_messages = list(messages)
        return LLMResponse(content="done", finish_reason="stop")

    def chat(self, messages, tools=None, timeout=None):
        from src.providers.chat import LLMResponse

        return LLMResponse(content="summary", finish_reason="stop")


class ToolResult:
    def __init__(self, raw: str) -> None:
        self.raw = raw
        try:
            self.body = json.loads(raw)
        except (TypeError, ValueError):
            self.body = None

    @property
    def ok(self) -> bool:
        return isinstance(self.body, dict) and self.body.get("status") == "ok"

    @property
    def refused(self) -> bool:
        """A tool-level error envelope (the agent's 'client error')."""
        return isinstance(self.body, dict) and self.body.get("status") == "error"


def call_tool(tool_name: str, arguments: dict, run_dir: Path) -> ToolResult:
    """Run one agent turn whose model asks for ``tool_name(arguments)``."""
    from src.agent.loop import AgentLoop
    from src.agent.memory import WorkspaceMemory
    from src.tools import build_registry

    llm = ScriptedLLM(tool_name, arguments)
    loop = AgentLoop(
        registry=build_registry(),
        llm=llm,
        memory=WorkspaceMemory(run_dir=str(run_dir)),
        max_iterations=3,
    )
    loop.run("Please run the requested tool.")
    for msg in llm.final_messages:
        if isinstance(msg, dict) and msg.get("role") == "tool" and msg.get("tool_call_id") == "call_vt_1":
            return ToolResult(msg.get("content", ""))
    raise AssertionError(f"the agent loop did not run {tool_name} (no tool result in the conversation)")


_FRESH_SCRIPT = """
import json, sys
sys.path.insert(0, sys.argv[1])
from conftest import call_tool
res = call_tool(sys.argv[2], json.loads(sys.argv[3]), sys.argv[4])
sys.stdout.write("\\n@@VT-RESULT@@" + res.raw)
"""


def call_tool_fresh(tool_name: str, arguments: dict, run_dir: Path, **env_vars: str) -> ToolResult:
    """Like call_tool, but in a new interpreter whose environment (the current one
    plus ``env_vars``) is in place before any product module is imported, as it
    is for a server started with that configuration."""
    import subprocess

    child_env = dict(os.environ)
    child_env.update(env_vars)
    proc = subprocess.run(
        [sys.executable, "-c", _FRESH_SCRIPT, str(Path(__file__).resolve().parent),
         tool_name, json.dumps(arguments), str(run_dir)],
        cwd=str(AGENT_DIR), env=child_env, capture_output=True, text=True, timeout=300,
    )
    out = proc.stdout
    assert proc.returncode == 0 and "@@VT-RESULT@@" in out, \
        f"tool call process failed ({proc.returncode}): {proc.stderr[-1500:]}"
    return ToolResult(out.rsplit("@@VT-RESULT@@", 1)[1])


def upload(content: bytes, filename: str) -> Path:
    """Store a file through the HTTP upload endpoint; return the path it reports."""
    from fastapi.testclient import TestClient

    import api_server

    client = TestClient(api_server.app)
    resp = client.post("/upload", files={"file": (filename, content, "application/octet-stream")})
    assert resp.status_code == 200, resp.text
    return Path(resp.json()["file_path"])


def preview(path: str):
    """Ask the HTTP API to show a stored document; returns the response."""
    from fastapi.testclient import TestClient

    import api_server

    client = TestClient(api_server.app)
    return client.get("/uploads/preview", params={"path": path})


def run_route(suffix: str):
    """Ask the HTTP API for a stored run's code or pine file.

    ``suffix`` is what follows ``/runs/`` (for example ``"<id>/code"``), so a
    caller can hand in a run identifier spelled however the request spells it.
    """
    from fastapi.testclient import TestClient

    import api_server

    client = TestClient(api_server.app)
    return client.get("/runs/" + suffix)


@pytest.fixture
def env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """A user home and an unrelated directory private to the test, a scratch
    directory inside the application directory (the server's working directory),
    and a fresh run workspace in the application's run storage."""
    home = tmp_path / "home"
    outside = tmp_path / "outside"
    for d in (home, outside):
        d.mkdir()
    proj = AGENT_DIR / f"vtgrade_{uuid.uuid4().hex[:12]}"
    proj.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))
    monkeypatch.delenv(FILE_ROOTS_ENV, raising=False)
    monkeypatch.delenv("API_AUTH_KEY", raising=False)
    monkeypatch.chdir(AGENT_DIR)

    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    run_dir = RUNS_DIR / f"vtgrade_{uuid.uuid4().hex[:12]}"
    run_dir.mkdir()
    created: list[Path] = [proj]
    before_uploads = set(os.listdir(UPLOADS_DIR))

    ns = SimpleNamespace(tmp=tmp_path, home=home, proj=proj, outside=outside,
                         run_dir=run_dir, created=created)
    yield ns

    shutil.rmtree(run_dir, ignore_errors=True)
    for p in created:
        if p.is_symlink() or p.is_file():
            p.unlink()
        elif p.is_dir():
            shutil.rmtree(p, ignore_errors=True)
    for name in set(os.listdir(UPLOADS_DIR)) - before_uploads:
        p = UPLOADS_DIR / name
        if p.is_symlink() or p.is_file():
            p.unlink()
        else:
            shutil.rmtree(p, ignore_errors=True)


# ---------------------------------------------------------------- fixtures data

def journal_csv(n_symbols: int = 5) -> str:
    """A Tonghuashun-style broker export with 15 profitable round trips."""
    header = "成交时间,证券代码,证券名称,操作,成交数量,成交价格,成交金额,手续费,印花税,过户费"
    rows = [header]
    symbols = ["600519", "000001", "300750", "600036", "000858"][:n_symbols]
    for sym in symbols:
        for i in range(3):
            buy_day = 1 + i * 4
            sell_day = buy_day + 2
            rows.append(f"2026-01-{buy_day:02d} 10:30:00,{sym},标的{sym},买入,100.0,10.0,1000.0,0.25,0.0,0.0")
            rows.append(f"2026-01-{sell_day:02d} 14:15:00,{sym},标的{sym},卖出,100.0,10.2,1020.0,0.26,1.02,0.0")
    return "\n".join(rows) + "\n"


def ohlcv_csv(n: int = 40) -> str:
    import datetime as _dt

    rows = ["date,open,high,low,close,volume"]
    start = _dt.date(2026, 1, 1)
    for i in range(n):
        base = 100 + (i % 7) * 1.5 + i * 0.2
        day = (start + _dt.timedelta(days=i)).isoformat()
        rows.append(f"{day},{base:.2f},{base + 2:.2f},{base - 2:.2f},{base + 0.5:.2f},{1000 + i}")
    return "\n".join(rows) + "\n"


def factor_pair_csv() -> tuple[str, str]:
    """Factor values and next-day returns for 8 assets over 12 days."""
    codes = [f"S{i}" for i in range(8)]
    f_rows = ["date," + ",".join(codes)]
    r_rows = ["date," + ",".join(codes)]
    for d in range(12):
        day = f"2026-02-{d + 1:02d}"
        f_rows.append(day + "," + ",".join(f"{(i * 7 + d * 3) % 11 / 10:.3f}" for i in range(8)))
        r_rows.append(day + "," + ",".join(f"{((i * 5 + d) % 9 - 4) / 100:.4f}" for i in range(8)))
    return "\n".join(f_rows) + "\n", "\n".join(r_rows) + "\n"
