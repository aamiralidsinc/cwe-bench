"""Make the shared harness importable and run the coroutine tests on asyncio."""

import sys
from pathlib import Path

import pytest

SUPPORT = Path(__file__).resolve().parent.parent / "support"
sys.path.insert(0, str(SUPPORT))


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"
