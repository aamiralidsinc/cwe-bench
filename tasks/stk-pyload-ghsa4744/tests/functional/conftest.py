import pytest

from support import harness


@pytest.fixture(scope="session")
def env():
    return harness.env()
