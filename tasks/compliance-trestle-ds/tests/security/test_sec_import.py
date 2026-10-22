"""Importing an external model file under a chosen name, next to another trestle workspace."""

import shutil

import pytest

from conftest import FIXTURES, assert_refused, run_trestle, snapshot
from shapes import spell


@pytest.mark.parametrize('shape', ['parent', 'absolute'])
def test_import_output_outside(layout, neighbour, shape):
    ws, _ = layout
    src = ws.parent / 'incoming' / 'catalog.json'
    src.parent.mkdir()
    shutil.copy2(FIXTURES / 'simplified_nist_catalog.json', src)
    name = spell(shape, ws / 'catalogs', neighbour / 'catalogs' / 'imported')
    before = snapshot(ws.parent, ws)
    res = run_trestle(ws, 'import', '-f', str(src), '-o', name)
    assert_refused(res, before, snapshot(ws.parent, ws))
