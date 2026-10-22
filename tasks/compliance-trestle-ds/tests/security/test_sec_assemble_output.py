"""Assembling a model under a chosen output file name next to another workspace."""

import pytest

from conftest import assert_refused, load_all, run_trestle, snapshot
from shapes import spell


@pytest.mark.parametrize('shape', ['absolute', 'parent'])
def test_assemble_output_outside(layout, neighbour, shape):
    ws, _ = layout
    load_all(ws)
    target = neighbour / 'dist' / 'catalogs' / 'assembled'
    name = spell(shape, ws / 'dist' / 'catalogs', target)
    before = snapshot(ws.parent, ws)
    res = run_trestle(ws, 'assemble', 'catalog', '-n', 'simplified_nist_catalog', '-o', name)
    assert_refused(res, before, snapshot(ws.parent, ws))
