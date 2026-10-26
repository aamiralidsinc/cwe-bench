"""Isolation must not depend on the bundled in-memory store."""

import pytest

from mcp.shared.experimental.tasks.in_memory_task_store import InMemoryTaskStore

from task_harness import GREET, build_server, refused, sessions, start_task, wait_until_finished


class ApplicationTaskStore(InMemoryTaskStore):
    """Stands in for a store an application supplies itself."""


@pytest.mark.anyio
async def test_another_client_cannot_read_a_task_in_an_application_supplied_store() -> None:
    async with sessions(build_server(store=ApplicationTaskStore())) as connect:
        creator = await connect()
        other = await connect()
        task_id = await start_task(creator, GREET, name="ada")
        await wait_until_finished(creator, task_id)

        await refused(other.experimental.get_task(task_id))
        await refused(other.experimental.cancel_task(task_id))

        assert (await creator.experimental.get_task(task_id)).status == "completed"
