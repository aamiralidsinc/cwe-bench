"""A listing must not expose another client's tasks."""

import pytest

from task_harness import (
    GREET,
    MORE_TASKS_THAN_ONE_STORE_PAGE,
    SLOW_REPORT,
    listed_ids,
    sessions,
    start_task,
)


@pytest.mark.anyio
async def test_a_listing_does_not_include_another_clients_task() -> None:
    async with sessions() as connect:
        creator = await connect()
        other = await connect()
        task_id = await start_task(creator, SLOW_REPORT)
        await start_task(other, GREET, name="bob")

        listed = await listed_ids(other)

        assert task_id not in listed


@pytest.mark.anyio
async def test_a_listing_does_not_identify_another_clients_tasks_through_its_cursor() -> None:
    """Whatever a listing carries must not point at a task the caller did not start."""
    async with sessions() as connect:
        creator = await connect()
        other = await connect()
        creator_tasks = {
            await start_task(creator, GREET, name=f"person-{index}")
            for index in range(MORE_TASKS_THAN_ONE_STORE_PAGE)
        }

        page = await other.experimental.list_tasks()

        # Neither the page nor the pagination state may point at the creator's tasks.
        assert page.tasks == []
        assert page.nextCursor is None
        assert {task.taskId for task in page.tasks}.isdisjoint(creator_tasks)
