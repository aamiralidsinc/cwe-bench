"""Fixtures shared by the hidden suites.

The temporary-directory behaviour under test depends on the process umask, so pin a common
default here (the same one a normal login shell has) and restore it afterwards. Nothing in this
file calls product code.
"""
import os

import pytest


@pytest.fixture(autouse=True)
def _common_umask():
    previous = os.umask(0o022)
    try:
        yield
    finally:
        os.umask(previous)
