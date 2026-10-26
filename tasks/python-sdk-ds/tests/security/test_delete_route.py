"""One client must not remove another client's task."""

import pytest

import mcp.types as types
from mcp.types import CallToolResult

from task_harness import GREET, refused, sessions, start_task, wait_until_finished


async def remove(client, task_id: str):
    return await client.session.send_request(
        types.ClientRequest(types.DeleteTaskRequest(params=types.DeleteTaskRequestParams(taskId=task_id))),
        types.DeleteTaskResult,
    )


@pytest.mark.anyio
async def test_another_client_cannot_remove_a_task() -> None:
    async with sessions() as connect:
        creator = await connect()
        other = await connect()
        task_id = await start_task(creator, GREET, name="ada")
        await wait_until_finished(creator, task_id)

        await refused(remove(other, task_id))

        # Both the task and its payload are still there for the client that started it.
        assert (await creator.experimental.get_task(task_id)).status == "completed"
        result = await creator.experimental.get_task_result(task_id, CallToolResult)
        assert result.content[0].text == "payload for ada"
