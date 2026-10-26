"""Tasks the application creates without a session stay reachable by their identifier."""

import pytest

from mcp.types import CallToolResult

from task_harness import (
    EXPORT,
    EXPORT_TASK_ID,
    GREET,
    sessions,
    start_task,
    wait_until_finished,
)


@pytest.mark.anyio
async def test_a_task_with_an_application_chosen_identifier_is_reachable_by_that_identifier() -> None:
    async with sessions() as connect:
        creator = await connect()
        other = await connect()
        created = await start_task(creator, EXPORT)
        assert created == EXPORT_TASK_ID
        await wait_until_finished(creator, EXPORT_TASK_ID)

        status = await other.experimental.get_task(EXPORT_TASK_ID)
        result = await other.experimental.get_task_result(EXPORT_TASK_ID, CallToolResult)

        assert status.status == "completed"
        assert result.content[0].text == "exported"
        assert (await creator.experimental.get_task(EXPORT_TASK_ID)).status == "completed"


@pytest.mark.anyio
async def test_a_task_created_without_a_session_survives_into_a_later_one() -> None:
    """A deployment where every request runs as a fresh session must keep serving its tasks."""
    async with sessions() as connect:
        first = await connect(stateless=True)
        second = await connect(stateless=True)
        task_id = await start_task(first, GREET, name="ada")
        await wait_until_finished(second, task_id)

        result = await second.experimental.get_task_result(task_id, CallToolResult)
        status = await second.experimental.get_task(task_id)

        assert result.content[0].text == "payload for ada"
        assert status.status == "completed"
