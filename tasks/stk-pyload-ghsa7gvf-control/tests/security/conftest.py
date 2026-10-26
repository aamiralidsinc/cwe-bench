import os

import pytest

from support import harness


@pytest.fixture(scope="session")
def env():
    environment = harness.Env(os.environ.get("PYLOAD_SRC", "/workspace/src"))
    yield environment
    environment.close()
