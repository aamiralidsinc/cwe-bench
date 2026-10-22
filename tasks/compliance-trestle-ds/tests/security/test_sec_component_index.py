"""Component markdown generation: a companion index file name must stay inside the workspace."""

import pytest

from conftest import assert_refused, load_all, run_trestle, snapshot
from shapes import spell


@pytest.mark.parametrize('shape', ['absolute', 'parent'])
def test_component_generate_index_outside(layout, shape):
    ws, outside = layout
    load_all(ws)
    name = spell(shape, ws, outside / 'idx' / 'component-index.md')
    before = snapshot(ws.parent, ws)
    res = run_trestle(
        ws, 'author', 'component-generate', '-n', 'comp_def_a', '-o', 'md_components', '--index', name
    )
    assert_refused(res, before, snapshot(ws.parent, ws))
