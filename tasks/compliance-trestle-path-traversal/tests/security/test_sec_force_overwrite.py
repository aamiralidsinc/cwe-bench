"""Regenerating component markdown over an existing folder (--force-overwrite)."""

import pytest

from conftest import assert_refused, load_all, run_trestle, snapshot
from shapes import spell


@pytest.mark.parametrize('shape', ['absolute', 'nested_parent'])
def test_component_generate_force_overwrite_outside(layout, shape):
    ws, outside = layout
    load_all(ws)
    name = spell(shape, ws, outside)
    before = snapshot(ws.parent, ws)
    res = run_trestle(ws, 'author', 'component-generate', '-n', 'comp_def_a', '-o', name, '-fo')
    assert_refused(res, before, snapshot(ws.parent, ws))
