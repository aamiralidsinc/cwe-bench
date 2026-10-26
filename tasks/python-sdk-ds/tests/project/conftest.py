"""Run the copied project tests on the asyncio backend, as the project's own suite does."""

import pytest


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"
