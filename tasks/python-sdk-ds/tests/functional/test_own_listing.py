"""A client's own listing stays complete, however many tasks it has."""

import pytest

from task_harness import (
    GREET,
    MORE_TASKS_THAN_ONE_STORE_PAGE,
    listed_ids,
    sessions,
    start_task,
    wait_until_finished,
)


@pytest.mark.anyio
async def test_a_client_with_more_than_one_store_page_of_tasks_sees_all_of_them() -> None:
    async with sessions() as connect:
        client = await connect()
        started = {
            await start_task(client, GREET, name=f"person-{index}")
            for index in range(MORE_TASKS_THAN_ONE_STORE_PAGE)
        }
        for task_id in started:
            await wait_until_finished(client, task_id)

        assert started <= await listed_ids(client)


@pytest.mark.anyio
async def test_another_clients_tasks_do_not_hide_a_clients_own_listing() -> None:
    async with sessions() as connect:
        client = await connect()
        other = await connect()
        mine = {
            await start_task(client, GREET, name=f"mine-{index}")
            for index in range(MORE_TASKS_THAN_ONE_STORE_PAGE)
        }
        for task_id in mine:
            await wait_until_finished(client, task_id)
        for index in range(3):
            await start_task(other, GREET, name=f"theirs-{index}")

        assert mine <= await listed_ids(client)
