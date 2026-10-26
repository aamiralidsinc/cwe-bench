"""A task with no creator must not be enumerated to anyone."""

import pytest

from task_harness import EXPORT, EXPORT_TASK_ID, listed_ids, sessions, start_task, wait_until_finished


@pytest.mark.anyio
async def test_a_task_without_a_creator_is_not_enumerated() -> None:
    async with sessions() as connect:
        creator = await connect()
        other = await connect()
        await start_task(creator, EXPORT)
        await wait_until_finished(creator, EXPORT_TASK_ID)

        assert EXPORT_TASK_ID not in await listed_ids(creator)
        assert EXPORT_TASK_ID not in await listed_ids(other)
