"""Shared harness for the hidden suites.

Only test bookkeeping lives here: a scripted LLM stream, a fake tool registry
holding marker tools, and helpers that drive the product's real chat pipeline
and HTTP routers.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from deeptutor.core.context import UnifiedContext
from deeptutor.core.stream import StreamEvent
from deeptutor.core.stream_bus import StreamBus
from deeptutor.core.tool_protocol import BaseTool, ToolDefinition, ToolResult
from deeptutor.multi_user.context import reset_current_user, set_current_user
from deeptutor.multi_user.models import CurrentUser, UserScope

SEARCH = "mcp_demo_search"
WRITE = "mcp_demo_write"
SERVER = "demo"


def llm_chunk(*, content: str | None = None, tool_calls: list[dict[str, Any]] | None = None):
    fields: dict[str, Any] = {"content": content}
    if tool_calls is not None:
        fields["tool_calls"] = [
            SimpleNamespace(
                index=tc.get("index", i),
                id=tc.get("id"),
                function=SimpleNamespace(
                    name=tc.get("name"), arguments=tc.get("arguments")
                ),
            )
            for i, tc in enumerate(tool_calls)
        ]
    else:
        fields["tool_calls"] = None
    return SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(**fields))])


async def _stream(chunks):
    for chunk in chunks:
        yield chunk


class ScriptedClient:
    """Minimal OpenAI-compatible stream that replays scripted rounds."""

    def __init__(self, rounds: list[list[Any]]) -> None:
        self._rounds = list(rounds)
        self.calls: list[dict[str, Any]] = []

        class _Completions:
            def __init__(self, parent: "ScriptedClient") -> None:
                self._parent = parent

            async def create(self, **kwargs: Any):
                self._parent.calls.append(
                    {**kwargs, "messages": list(kwargs.get("messages") or [])}
                )
                if not self._parent._rounds:
                    raise RuntimeError("scripted client exhausted")
                return _stream(self._parent._rounds.pop(0))

        class _Chat:
            def __init__(self, parent: "ScriptedClient") -> None:
                self.completions = _Completions(parent)

        self.chat = _Chat(self)

    def offered_names(self, round_index: int) -> set[str]:
        tools = self.calls[round_index].get("tools") or []
        return {str((t.get("function") or {}).get("name") or "") for t in tools}

    def system_prompt(self, round_index: int = 0) -> str:
        messages = self.calls[round_index].get("messages") or []
        if not messages:
            return ""
        return str(messages[0].get("content") or "")

    def tool_messages(self, round_index: int) -> list[dict[str, Any]]:
        messages = self.calls[round_index].get("messages") or []
        return [m for m in messages if m.get("role") == "tool"]


class MarkerTool(BaseTool):
    """A registry tool that records every execution in a shared sink."""

    def __init__(
        self,
        name: str,
        *,
        deferred: bool = False,
        server: str = "",
        sink: list[dict[str, Any]] | None = None,
    ) -> None:
        self._name = name
        self.deferred = deferred
        if server:
            self.server_name = server
        self._sink = sink

    def get_definition(self) -> ToolDefinition:
        return ToolDefinition(
            name=self._name,
            description=f"marker tool {self._name}",
            raw_parameters={"type": "object", "properties": {}},
        )

    async def execute(self, **kwargs: Any) -> ToolResult:
        if self._sink is not None:
            self._sink.append({"name": self._name})
        return ToolResult(content=f"ran:{self._name}")


class FakeRegistry:
    """Registry surface the product code uses, over marker tools."""

    def __init__(self, tools: list[BaseTool] | None = None) -> None:
        self.executed: list[dict[str, Any]] = []
        self._tools: dict[str, BaseTool] = {}
        for tool in tools or []:
            self.register(tool)

    def register(self, tool: BaseTool) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> BaseTool | None:
        return self._tools.get(name)

    def get_enabled(self, names: list[str]) -> list[BaseTool]:
        return [self._tools[n] for n in names if n in self._tools]

    def get_definitions(self, names: list[str] | None = None) -> list[ToolDefinition]:
        tools = self._tools.values() if names is None else self.get_enabled(names)
        return [t.get_definition() for t in tools]

    def deferred_tools(self) -> list[BaseTool]:
        return [t for t in self._tools.values() if getattr(t, "deferred", False)]

    def build_prompt_text(self, names, **_kwargs: Any) -> str:
        return "- `web_search` - Search the web"

    def build_openai_schemas(self, names=None) -> list[dict[str, Any]]:
        tools = self._tools.values() if names is None else self.get_enabled(names)
        return [t.get_definition().to_openai_schema() for t in tools]

    async def execute(self, name: str, /, **kwargs: Any) -> ToolResult:
        self.executed.append({"name": name})
        tool = self._tools.get(name)
        if tool is None:
            raise KeyError(name)
        return await tool.execute(**kwargs)


def default_registry(*, with_load_tools: bool = True) -> FakeRegistry:
    from deeptutor.tools.builtin import LoadToolsTool

    registry = FakeRegistry()
    registry.register(MarkerTool("web_search", sink=registry.executed))
    registry.register(MarkerTool(SEARCH, deferred=True, server=SERVER, sink=registry.executed))
    registry.register(MarkerTool(WRITE, deferred=True, server=SERVER, sink=registry.executed))
    if with_load_tools:
        registry.register(LoadToolsTool())
    return registry


def executed_names(registry: FakeRegistry) -> list[str]:
    return [row["name"] for row in registry.executed]


def user(uid: str = "u_alice", role: str = "user") -> CurrentUser:
    return CurrentUser(
        id=uid,
        username=uid,
        role=role,  # type: ignore[arg-type]
        scope=UserScope(kind="user", user_id=uid, root=Path("/tmp/deeptutor-test")),
    )


def admin_user() -> CurrentUser:
    from deeptutor.multi_user.paths import local_admin_user

    return local_admin_user()


async def drive_pipeline(pipeline, context: UnifiedContext) -> list[StreamEvent]:
    bus = StreamBus()
    events: list[StreamEvent] = []

    async def consume() -> None:
        async for event in bus.subscribe():
            events.append(event)

    consumer = asyncio.create_task(consume())
    await asyncio.sleep(0)
    await pipeline.run(context, bus)
    await asyncio.sleep(0)
    await bus.close()
    await consumer
    return events


def make_pipeline(registry: FakeRegistry):
    from deeptutor.agents.chat.agentic_pipeline import AgenticChatPipeline

    pipeline = AgenticChatPipeline(language="en")
    pipeline.registry = registry
    return pipeline


def write_grant(root: Path, user_id: str, payload: dict[str, Any] | None) -> None:
    """Write a grant file the way the product stores it (JSON on disk)."""
    grants_dir = root / "system" / "grants"
    grants_dir.mkdir(parents=True, exist_ok=True)
    path = grants_dir / f"{user_id}.json"
    if payload is None:
        path.write_text("not json at all", encoding="utf-8")
        return
    body = {
        "version": 2,
        "user_id": user_id,
        "models": {"llm": []},
        "knowledge_bases": [],
        "skills": [],
        "enabled_tools": None,
        "mcp_tools": None,
        "exec_enabled": None,
    }
    body.update(payload)
    path.write_text(json.dumps(body), encoding="utf-8")


def write_session_tools(root: Path, names: list[str]) -> Path:
    path = root / "loaded_tools.json"
    path.write_text(json.dumps({"loaded_tools": names}), encoding="utf-8")
    return path


from contextlib import contextmanager


@contextmanager
def as_user(current):
    """Install a request user for the duration of a block."""
    token = set_current_user(current)
    try:
        yield current
    finally:
        reset_current_user(token)


async def run_turn(monkeypatch, registry: FakeRegistry, client: ScriptedClient, context: UnifiedContext):
    """Drive the real chat pipeline with a scripted model stream."""
    pipeline = make_pipeline(registry)
    monkeypatch.setattr(pipeline, "_build_openai_client", lambda: client)
    await drive_pipeline(pipeline, context)
    return pipeline


@contextmanager
def plugins_client(current):
    """A real plugins router mounted with the given request user."""
    from fastapi import Depends, FastAPI
    from fastapi.testclient import TestClient

    import deeptutor.api.routers.plugins_api as plugins_api

    app = FastAPI()

    async def _auth():
        token = set_current_user(current)
        try:
            yield
        finally:
            reset_current_user(token)

    app.include_router(
        plugins_api.router, prefix="/api/v1/plugins", dependencies=[Depends(_auth)]
    )
    with TestClient(app) as client:
        yield client


def is_client_error(status: int) -> bool:
    return 400 <= int(status) < 500
