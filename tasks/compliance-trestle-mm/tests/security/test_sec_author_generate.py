"""Names the markdown generate commands and task setup join onto the workspace."""

import pytest

from conftest import assert_refused, load_all, run_trestle, snapshot
from shapes import spell

SHAPES = ['absolute', 'nested_parent']


@pytest.mark.parametrize('shape', SHAPES)
def test_catalog_generate_output_outside(layout, shape):
    ws, outside = layout
    load_all(ws)
    name = spell(shape, ws, outside / 'cat_md')
    before = snapshot(ws.parent, ws)
    res = run_trestle(ws, 'author', 'catalog-generate', '-n', 'simplified_nist_catalog', '-o', name)
    assert_refused(res, before, snapshot(ws.parent, ws))


@pytest.mark.parametrize('shape', SHAPES)
def test_profile_generate_output_outside(layout, shape):
    ws, outside = layout
    load_all(ws)
    name = spell(shape, ws, outside / 'prof_md')
    before = snapshot(ws.parent, ws)
    res = run_trestle(ws, 'author', 'profile-generate', '-n', 'simplified_nist_profile', '-o', name)
    assert_refused(res, before, snapshot(ws.parent, ws))


@pytest.mark.parametrize('shape', SHAPES)
def test_docs_setup_task_outside(layout, shape):
    ws, outside = layout
    name = spell(shape, ws, outside / 'docs_task')
    before = snapshot(ws.parent, ws)
    res = run_trestle(ws, 'author', 'docs', 'setup', '-tn', name)
    assert_refused(res, before, snapshot(ws.parent, ws))


@pytest.mark.parametrize('shape', SHAPES)
def test_folders_setup_task_outside(layout, shape):
    ws, outside = layout
    name = spell(shape, ws, outside / 'folders_task')
    before = snapshot(ws.parent, ws)
    res = run_trestle(ws, 'author', 'folders', 'setup', '-tn', name)
    assert_refused(res, before, snapshot(ws.parent, ws))
