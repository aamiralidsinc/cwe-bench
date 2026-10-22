"""Writing an incoming model under a name the user chose."""

import pytest

from conftest import FIXTURES, assert_refused, load_all, run_trestle, snapshot
from shapes import spell

SHAPES = ['absolute', 'parent', 'nested_parent']


@pytest.mark.parametrize('shape', SHAPES)
def test_import_output_in_other_workspace(layout, neighbour, shape):
    ws, _ = layout
    other = neighbour
    load_all(ws)
    name = spell(shape, ws / 'catalogs', other / 'smuggled')
    before = snapshot(ws.parent, ws)
    res = run_trestle(ws, 'import', '-f', str(FIXTURES / 'simplified_nist_catalog.json'), '-o', name)
    assert_refused(res, before, snapshot(ws.parent, ws))
