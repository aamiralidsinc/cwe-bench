"""Creating and replicating models by name, next to another trestle workspace."""

import pytest

from conftest import assert_refused, load_all, run_trestle, snapshot
from shapes import spell


@pytest.mark.parametrize('shape', ['parent', 'nested_parent', 'absolute'])
def test_create_output_outside(layout, neighbour, shape):
    ws, _ = layout
    name = spell(shape, ws / 'catalogs', neighbour / 'catalogs' / 'created')
    before = snapshot(ws.parent, ws)
    res = run_trestle(ws, 'create', '-t', 'catalog', '-o', name)
    assert_refused(res, before, snapshot(ws.parent, ws))


@pytest.mark.parametrize('shape', ['parent', 'absolute'])
def test_replicate_output_outside(layout, neighbour, shape):
    ws, _ = layout
    load_all(ws)
    name = spell(shape, ws / 'catalogs', neighbour / 'catalogs' / 'replicated')
    before = snapshot(ws.parent, ws)
    res = run_trestle(ws, 'replicate', 'catalog', '-n', 'simplified_nist_catalog', '-o', name)
    assert_refused(res, before, snapshot(ws.parent, ws))
