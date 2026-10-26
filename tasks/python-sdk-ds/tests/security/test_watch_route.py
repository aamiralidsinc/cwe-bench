"""A client must not be able to follow another client's task."""

import anyio
import pytest

import mcp.types as types

from task_harness import SLOW_REPORT, refused, sessions, start_task, wait_until_finished


async def follow(client, task_id: str):
    return await client.session.send_request(
        types.ClientRequest(types.WatchTaskRequest(params=types.WatchTaskRequestParams(taskId=task_id))),
        types.WatchTaskResult,
    )


@pytest.mark.anyio
async def test_another_client_cannot_follow_a_task() -> None:
    async with sessions() as connect:
        creator = await connect()
        other = await connect()
        task_id = await start_task(creator, SLOW_REPORT)

        await refused(follow(other, task_id))

        # The task runs to completion and nothing about it reaches the other client.
        await wait_until_finished(creator, task_id)
        with anyio.move_on_after(0.5):
            while not other.task_notifications_for(task_id):
                await anyio.sleep(0.02)

        assert other.task_notifications_for(task_id) == []
