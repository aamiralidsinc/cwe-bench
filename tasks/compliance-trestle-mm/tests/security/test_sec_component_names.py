"""Names that become the folder a component's markdown is written into.

One comes from the model content itself, the other from a naming option on the
command that generates the markdown.
"""

import json

import pytest

from conftest import FIXTURES, assert_refused, load_all, run_trestle, snapshot
from shapes import spell

SHAPES = ['absolute', 'parent', 'nested_parent']


def _set_title(ws, title):
    path = ws / 'component-definitions' / 'comp_def_a' / 'component-definition.json'
    data = json.loads((FIXTURES / 'comp_def_a.json').read_text())
    data['component-definition']['components'][0]['title'] = title
    path.write_text(json.dumps(data))


@pytest.mark.parametrize('shape', SHAPES)
def test_component_title_lands_outside(layout, shape):
    ws, outside = layout
    load_all(ws)
    _set_title(ws, spell(shape, ws / 'md', outside / 'titled'))
    before = snapshot(ws.parent, ws)
    res = run_trestle(ws, 'author', 'component-generate', '-n', 'comp_def_a', '-o', 'md')
    assert_refused(res, before, snapshot(ws.parent, ws))


@pytest.mark.parametrize('shape', SHAPES)
def test_component_generate_named_subfolder_outside(layout, shape):
    ws, outside = layout
    load_all(ws)
    name = spell(shape, ws / 'md', outside / 'named')
    before = snapshot(ws.parent, ws)
    res = run_trestle(ws, 'author', 'component-generate', '-n', 'comp_def_a', '-o', 'md', '--component-name', name)
    assert_refused(res, before, snapshot(ws.parent, ws))
