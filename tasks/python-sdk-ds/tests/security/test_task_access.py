"""One client must not read another client's task."""

import pytest

from mcp.types import CallToolResult

from task_harness import GREET, HOLD, refused, sessions, start_task, wait_until_finished


@pytest.mark.anyio
async def test_another_client_cannot_read_a_tasks_status() -> None:
    async with sessions() as connect:
        creator = await connect()
        other = await connect()
        task_id = await start_task(creator, GREET, name="ada")
        await wait_until_finished(creator, task_id)

        await refused(other.experimental.get_task(task_id))

        # The task is unchanged and the client that started it still uses it.
        assert (await creator.experimental.get_task(task_id)).status == "completed"


@pytest.mark.anyio
async def test_another_client_cannot_read_a_tasks_payload() -> None:
    async with sessions() as connect:
        creator = await connect()
        other = await connect()
        task_id = await start_task(creator, GREET, name="ada")
        await wait_until_finished(creator, task_id)

        await refused(other.experimental.get_task_result(task_id, CallToolResult))

        result = await creator.experimental.get_task_result(task_id, CallToolResult)
        assert result.content[0].text == "payload for ada"
        # The requesting client's own session keeps working after the refusal.
        own_task = await start_task(other, GREET, name="bob")
        await wait_until_finished(other, own_task)
        assert (await other.experimental.get_task(own_task)).status == "completed"


@pytest.mark.anyio
async def test_another_client_cannot_cancel_a_task() -> None:
    async with sessions() as connect:
        creator = await connect()
        other = await connect()
        task_id = await start_task(creator, HOLD)

        await refused(other.experimental.cancel_task(task_id))

        # Nothing happened to the task: it is still running, and its owner can cancel it.
        assert (await creator.experimental.get_task(task_id)).status == "working"
        cancelled = await creator.experimental.cancel_task(task_id)
        assert cancelled.status == "cancelled"
