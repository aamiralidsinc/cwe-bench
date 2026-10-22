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


@pytest.mark.parametrize('command', [['author', 'catalog-generate', '-n', 'simplified_nist_catalog'],
                                     ['author', 'component-generate', '-n', 'comp_def_a']])
def test_force_overwrite_clears_workspace_folder(layout, tmp_path, command):
    """Regenerating from another working directory must clear the folder the name designates in the workspace."""
    ws, _ = layout
    load_all(ws)
    (ws / 'md_cat').mkdir()
    (ws / 'md_cat' / 'stale.md').write_text('old\n')
    elsewhere = tmp_path / 'elsewhere'
    (elsewhere / 'md_cat').mkdir(parents=True)
    (elsewhere / 'md_cat' / 'keep.txt').write_text('outside data\n')
    before = snapshot(elsewhere, ws)
    res = run_trestle(ws, *command, '-o', 'md_cat', '-fo', '--trestle-root', str(ws), cwd=elsewhere)
    assert snapshot(elsewhere, ws) == before, 'the command changed a folder outside the workspace'
    assert res.returncode == 0, res.stdout[-2000:] + res.stderr[-2000:]
    assert not (ws / 'md_cat' / 'stale.md').exists(), 'the folder inside the workspace was not the one cleared'
