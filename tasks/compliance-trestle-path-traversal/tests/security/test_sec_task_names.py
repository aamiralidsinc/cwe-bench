"""Other commands that take a markdown folder or task name relative to the workspace."""

import pytest

from conftest import assert_refused, load_all, run_trestle, snapshot
from shapes import spell

SHAPES = ['absolute', 'nested_parent']


@pytest.mark.parametrize('shape', SHAPES)
def test_component_generate_output_outside(layout, shape):
    ws, outside = layout
    load_all(ws)
    name = spell(shape, ws, outside / 'comp_md')
    before = snapshot(ws.parent, ws)
    res = run_trestle(ws, 'author', 'component-generate', '-n', 'comp_def_a', '-o', name)
    assert_refused(res, before, snapshot(ws.parent, ws))


@pytest.mark.parametrize('shape', SHAPES)
def test_docs_setup_task_outside(layout, shape):
    ws, outside = layout
    name = spell(shape, ws, outside / 'docs_task')
    before = snapshot(ws.parent, ws)
    res = run_trestle(ws, 'author', 'docs', 'setup', '-tn', name)
    assert_refused(res, before, snapshot(ws.parent, ws))


def test_folders_setup_task_outside(layout):
    ws, outside = layout
    name = spell('absolute', ws, outside / 'folders_task')
    before = snapshot(ws.parent, ws)
    res = run_trestle(ws, 'author', 'folders', 'setup', '-tn', name)
    assert_refused(res, before, snapshot(ws.parent, ws))
