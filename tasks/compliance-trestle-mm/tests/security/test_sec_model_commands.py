"""Model commands that write a new model under a name the user chose.

They already refuse a target that is in no trestle project, so the reachable
outside is another trestle workspace.
"""

import pytest

from conftest import assert_refused, load_all, run_trestle, snapshot
from shapes import spell

SHAPES = ['absolute', 'parent', 'nested_parent']


@pytest.mark.parametrize('shape', SHAPES)
def test_create_output_in_other_workspace(layout, neighbour, shape):
    ws, _ = layout
    other = neighbour
    load_all(ws)
    name = spell(shape, ws / 'catalogs', other / 'stolen')
    before = snapshot(ws.parent, ws)
    res = run_trestle(ws, 'create', '-t', 'catalog', '-o', name)
    after = snapshot(ws.parent, ws)
    assert_refused(res, before, after)


@pytest.mark.parametrize('shape', SHAPES)
def test_replicate_output_in_other_workspace(layout, neighbour, shape):
    ws, _ = layout
    other = neighbour
    load_all(ws)
    name = spell(shape, ws / 'catalogs', other / 'stolen_copy')
    before = snapshot(ws.parent, ws)
    res = run_trestle(ws, 'replicate', 'catalog', '-n', 'simplified_nist_catalog', '-o', name)
    assert_refused(res, before, snapshot(ws.parent, ws))
