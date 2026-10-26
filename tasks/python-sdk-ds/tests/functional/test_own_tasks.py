"""A client keeps full use of the tasks it started."""

import anyio
import pytest

import mcp.types as types
from mcp.types import CallToolResult

from task_harness import (
    GREET,
    HOLD,
    SLOW_REPORT,
    listed_ids,
    sessions,
    start_task,
    wait_until_finished,
)


async def remove(client, task_id: str):
    return await client.session.send_request(
        types.ClientRequest(types.DeleteTaskRequest(params=types.DeleteTaskRequestParams(taskId=task_id))),
        types.DeleteTaskResult,
    )


async def follow(client, task_id: str):
    return await client.session.send_request(
        types.ClientRequest(types.WatchTaskRequest(params=types.WatchTaskRequestParams(taskId=task_id))),
        types.WatchTaskResult,
    )


@pytest.mark.anyio
async def test_a_client_reads_the_status_and_payload_of_its_own_task() -> None:
    async with sessions() as connect:
        client = await connect()
        task_id = await start_task(client, GREET, name="ada")
        await wait_until_finished(client, task_id)

        assert (await client.experimental.get_task(task_id)).status == "completed"
        result = await client.experimental.get_task_result(task_id, CallToolResult)
        assert result.content[0].text == "payload for ada"


@pytest.mark.anyio
async def test_each_client_reads_its_own_task() -> None:
    async with sessions() as connect:
        first = await connect()
        second = await connect()
        first_task = await start_task(first, GREET, name="ada")
        second_task = await start_task(second, GREET, name="bob")
        await wait_until_finished(first, first_task)
        await wait_until_finished(second, second_task)

        assert (await first.experimental.get_task_result(first_task, CallToolResult)).content[0].text == (
            "payload for ada"
        )
        assert (await second.experimental.get_task_result(second_task, CallToolResult)).content[0].text == (
            "payload for bob"
        )


@pytest.mark.anyio
async def test_a_client_cancels_its_own_task() -> None:
    async with sessions() as connect:
        client = await connect()
        task_id = await start_task(client, HOLD)

        cancelled = await client.experimental.cancel_task(task_id)

        assert cancelled.status == "cancelled"
        assert (await client.experimental.get_task(task_id)).status == "cancelled"


@pytest.mark.anyio
async def test_a_client_removes_its_own_finished_task() -> None:
    async with sessions() as connect:
        client = await connect()
        task_id = await start_task(client, GREET, name="ada")
        await wait_until_finished(client, task_id)

        removed = await remove(client, task_id)

        assert removed.taskId == task_id
        assert task_id not in await listed_ids(client)


@pytest.mark.anyio
async def test_a_client_follows_its_own_task() -> None:
    async with sessions() as connect:
        client = await connect()
        task_id = await start_task(client, SLOW_REPORT)

        followed = await follow(client, task_id)
        assert followed.watching is True

        await wait_until_finished(client, task_id)
        with anyio.move_on_after(1.0):
            while not client.task_notifications_for(task_id):
                await anyio.sleep(0.02)

        assert client.task_notifications_for(task_id)
