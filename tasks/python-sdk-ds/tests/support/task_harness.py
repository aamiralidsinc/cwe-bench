"""Shared harness for the task-visibility suites.

Every test runs a real `Server` with experimental task support over in-memory
streams and drives it with real `ClientSession` objects, one per simulated
client. Nothing here is a stub: the streams, the sessions, the task store and
the default handlers are the product's own.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import AsyncExitStack, asynccontextmanager
from typing import Any

import anyio

import mcp.types as types
from mcp.client.session import ClientSession
from mcp.server import Server
from mcp.server.experimental.task_context import ServerTaskContext
from mcp.shared.experimental.tasks.store import TaskStore
from mcp.shared.message import SessionMessage
from mcp.types import (
    TASK_REQUIRED,
    CallToolResult,
    TextContent,
    Tool,
    ToolExecution,
)

GREET = "greet"
HOLD = "hold"
SLOW_REPORT = "slow_report"
EXPORT = "nightly_export"

# An identifier the application chooses itself instead of letting the SDK mint one.
EXPORT_TASK_ID = "the-nightly-export"

# The bundled store pages listings at ten tasks; more than that spans pages.
MORE_TASKS_THAN_ONE_STORE_PAGE = 11

# Standard JSON-RPC error codes a deliberate refusal may use. An unhandled
# exception in a handler comes back as code 0, which is not a refusal.
CLIENT_ERROR_CODES = {types.INVALID_REQUEST, types.METHOD_NOT_FOUND, types.INVALID_PARAMS}


def build_server(store: TaskStore | None = None) -> Server:
    """A task-enabled server exposing four tools."""
    server = Server("task-visibility-suite")
    server.experimental.enable_tasks(store=store)

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        return [
            Tool(
                name=name,
                description=name,
                inputSchema={"type": "object"},
                execution=ToolExecution(taskSupport=TASK_REQUIRED),
            )
            for name in (GREET, HOLD, SLOW_REPORT, EXPORT)
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict[str, Any]) -> Any:
        async def greet(task: ServerTaskContext) -> CallToolResult:
            return CallToolResult(
                content=[TextContent(type="text", text=f"payload for {arguments.get('name', 'nobody')}")]
            )

        async def hold(task: ServerTaskContext) -> CallToolResult:
            await anyio.sleep_forever()
            raise AssertionError("unreachable")  # pragma: no cover

        async def slow_report(task: ServerTaskContext) -> CallToolResult:
            for step in range(6):
                await task.update_status(f"step {step}")
                await anyio.sleep(0.02)
            return CallToolResult(content=[TextContent(type="text", text="report ready")])

        async def nightly_export(task: ServerTaskContext) -> CallToolResult:
            return CallToolResult(content=[TextContent(type="text", text="exported")])

        run_task = server.request_context.experimental.run_task
        if name == EXPORT:
            return await run_task(nightly_export, task_id=EXPORT_TASK_ID)
        work = {GREET: greet, HOLD: hold, SLOW_REPORT: slow_report}[name]
        return await run_task(work)

    return server


class Client:
    """One client session, plus every notification the server pushed to it."""

    def __init__(self, session: ClientSession) -> None:
        self.session = session
        self.notifications: list[types.ServerNotification] = []

    @property
    def experimental(self) -> Any:
        return self.session.experimental

    def task_notifications_for(self, task_id: str) -> list[types.ServerNotification]:
        found = []
        for notification in self.notifications:
            root = notification.root
            if isinstance(root, types.TaskStatusNotification) and root.params.taskId == task_id:
                found.append(notification)
        return found


Connect = Callable[..., Awaitable[Client]]


@asynccontextmanager
async def sessions(server: Server | None = None) -> AsyncIterator[Connect]:
    """Run a server and hand out a factory that opens more client sessions on it."""
    server = server if server is not None else build_server()
    async with anyio.create_task_group() as task_group, AsyncExitStack() as stack:

        async def connect(*, stateless: bool = False) -> Client:
            server_send, server_receive = anyio.create_memory_object_stream[SessionMessage](100)
            client_send, client_receive = anyio.create_memory_object_stream[SessionMessage](100)

            async def run_server() -> None:
                await server.run(
                    client_receive,
                    server_send,
                    server.create_initialization_options(),
                    stateless=stateless,
                )

            task_group.start_soon(run_server)
            holder: dict[str, Client] = {}

            async def on_message(message: Any) -> None:
                if isinstance(message, types.ServerNotification) and "client" in holder:
                    holder["client"].notifications.append(message)

            session = await stack.enter_async_context(
                ClientSession(server_receive, client_send, message_handler=on_message)
            )
            client = Client(session)
            holder["client"] = client
            await session.initialize()
            return client

        try:
            yield connect
        finally:
            task_group.cancel_scope.cancel()


async def start_task(client: Client, tool: str = SLOW_REPORT, **arguments: Any) -> str:
    """Start `tool` as a task and return its identifier."""
    created = await client.experimental.call_tool_as_task(tool, arguments)
    return created.task.taskId


async def wait_until_finished(client: Client, task_id: str, timeout: float = 10.0) -> None:
    """Poll until the task reaches a terminal status."""
    with anyio.fail_after(timeout):
        async for _ in client.experimental.poll_task(task_id):
            pass


async def listed_ids(client: Client, *, max_pages: int = 20) -> set[str]:
    """Every task identifier the server lists for this client, following cursors."""
    seen: set[str] = set()
    cursor = None
    for _ in range(max_pages):
        page = await client.experimental.list_tasks(cursor)
        seen.update(task.taskId for task in page.tasks)
        cursor = page.nextCursor
        if not cursor:
            return seen
    raise AssertionError(f"listing did not terminate after {max_pages} pages")


async def refused(request: Awaitable[Any]) -> types.ErrorData:
    """Await a request that must be refused as a normal protocol error."""
    try:
        result = await request
    except Exception as exc:  # noqa: BLE001 - the refusal may be any client error
        error = getattr(exc, "error", None)
        assert isinstance(error, types.ErrorData), f"refusal was not a protocol error: {exc!r}"
        assert error.code in CLIENT_ERROR_CODES, f"refusal was not a client error: {error!r}"
        return error
    raise AssertionError(f"the request was not refused; it returned {result!r}")


__all__ = [
    "CLIENT_ERROR_CODES",
    "EXPORT",
    "EXPORT_TASK_ID",
    "GREET",
    "HOLD",
    "MORE_TASKS_THAN_ONE_STORE_PAGE",
    "SLOW_REPORT",
    "Client",
    "Connect",
    "build_server",
    "listed_ids",
    "refused",
    "sessions",
    "start_task",
    "wait_until_finished",
]
