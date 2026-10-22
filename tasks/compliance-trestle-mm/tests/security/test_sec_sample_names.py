"""Names given to the sample document or folder a task creates."""

import pytest

from conftest import assert_refused, run_trestle, snapshot
from shapes import spell

SHAPES = ['absolute', 'parent', 'nested_parent']


@pytest.mark.parametrize('shape', SHAPES)
def test_docs_create_sample_name_outside(layout, shape):
    ws, outside = layout
    setup = run_trestle(ws, 'author', 'docs', 'setup', '-tn', 'policies')
    assert setup.returncode == 0, setup.stdout[-2000:] + setup.stderr[-2000:]
    name = spell(shape, ws / 'policies', outside / 'sample_doc')
    before = snapshot(ws.parent, ws)
    res = run_trestle(ws, 'author', 'docs', 'create-sample', '-tn', 'policies', '--sample-name', name)
    assert_refused(res, before, snapshot(ws.parent, ws))


@pytest.mark.parametrize('shape', SHAPES)
def test_folders_create_sample_name_outside(layout, shape):
    ws, outside = layout
    setup = run_trestle(ws, 'author', 'folders', 'setup', '-tn', 'arch')
    assert setup.returncode == 0, setup.stdout[-2000:] + setup.stderr[-2000:]
    name = spell(shape, ws / 'arch', outside / 'sample_folder')
    before = snapshot(ws.parent, ws)
    res = run_trestle(ws, 'author', 'folders', 'create-sample', '-tn', 'arch', '--sample-name', name)
    assert_refused(res, before, snapshot(ws.parent, ws))
