"""Pytest configuration for the hidden suites."""
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "runner"))

from helpers import PDEnv  # noqa: E402


@pytest.fixture
def pdenv(tmp_path):
    """An isolated runtime tree and a directory outside every container."""
    return PDEnv(tmp_path / "pd")
