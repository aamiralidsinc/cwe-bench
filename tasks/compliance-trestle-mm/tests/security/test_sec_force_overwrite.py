"""Replacing a folder must not delete anything outside the workspace first."""

import pytest

from conftest import assert_refused, load_all, run_trestle, snapshot
from shapes import spell

ALL_SHAPES = ['absolute', 'parent', 'nested_parent']
# The name is judged before the folder is cleared, so a leading '..' name is
# refused without touching anything. Only those spellings that get past that
# first look reach the clear.
UNGUARDED_SHAPES = ['absolute', 'nested_parent']


@pytest.mark.parametrize('shape', ALL_SHAPES)
def test_component_generate_force_overwrite_clears_outside(layout, shape):
    """The replace runs before any name is judged, so an outside folder is emptied first."""
    ws, outside = layout
    load_all(ws)
    name = spell(shape, ws, outside)
    before = snapshot(ws.parent, ws)
    res = run_trestle(ws, 'author', 'component-generate', '-n', 'comp_def_a', '-o', name, '-fo')
    assert_refused(res, before, snapshot(ws.parent, ws))


@pytest.mark.parametrize('shape', UNGUARDED_SHAPES)
def test_catalog_generate_force_overwrite_clears_outside(layout, shape):
    ws, outside = layout
    load_all(ws)
    name = spell(shape, ws, outside)
    before = snapshot(ws.parent, ws)
    res = run_trestle(ws, 'author', 'catalog-generate', '-n', 'simplified_nist_catalog', '-o', name, '-fo')
    assert_refused(res, before, snapshot(ws.parent, ws))
