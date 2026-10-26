"""Shared offline fixtures for the hidden suites.

Blender is replaced by an in-process stand-in and every remote service by in-process
responses; the add-on's own local socket command protocol is the entry point each test drives.
"""

import os
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "support" / "block_bpy"))
sys.path.insert(0, str(HERE))

import pytest  # noqa: E402


@pytest.fixture
def product(tmp_path):
    from support.harness import Product

    workspace = pathlib.Path(os.environ.get("PRODUCT_WORKSPACE", "/workspace"))
    with Product(workspace, tmp_path) as running:
        yield running
