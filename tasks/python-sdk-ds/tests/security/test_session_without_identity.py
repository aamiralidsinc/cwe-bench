"""A client session with no identity of its own must not reach other clients' tasks."""

import pytest

from mcp.types import CallToolResult

from task_harness import GREET, HOLD, refused, sessions, start_task, wait_until_finished


@pytest.mark.anyio
async def test_a_client_without_an_identity_cannot_read_another_clients_task() -> None:
    async with sessions() as connect:
        creator = await connect()
        anonymous = await connect(stateless=True)
        task_id = await start_task(creator, GREET, name="ada")
        await wait_until_finished(creator, task_id)

        await refused(anonymous.experimental.get_task(task_id))
        await refused(anonymous.experimental.get_task_result(task_id, CallToolResult))

        assert (await creator.experimental.get_task(task_id)).status == "completed"


@pytest.mark.anyio
async def test_a_client_without_an_identity_cannot_cancel_another_clients_task() -> None:
    async with sessions() as connect:
        creator = await connect()
        anonymous = await connect(stateless=True)
        task_id = await start_task(creator, HOLD)

        await refused(anonymous.experimental.cancel_task(task_id))

        assert (await creator.experimental.get_task(task_id)).status == "working"
