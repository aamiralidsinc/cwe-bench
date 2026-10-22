"""Saving a model under a name the user chose, through the command that writes it.

The mapper builds the model folder by joining the name after the model-type
folder, so only a name that walks out from there escapes.
"""

import pytest

from conftest import assert_refused, load_all, run_trestle, snapshot
from shapes import spell

SHAPES = ['parent', 'nested_parent']


@pytest.mark.parametrize('shape', SHAPES)
def test_catalog_assemble_output_outside(layout, shape):
    ws, outside = layout
    load_all(ws)
    _res = run_trestle(ws, 'author', 'catalog-generate', '-n', 'simplified_nist_catalog', '-o', 'md_cat')
    assert _res.returncode == 0, _res.stdout[-2000:] + _res.stderr[-2000:]
    name = spell(shape, ws / 'catalogs', outside / 'assembled')
    before = snapshot(ws.parent, ws)
    res = run_trestle(ws, 'author', 'catalog-assemble', '-m', 'md_cat', '-o', name)
    assert_refused(res, before, snapshot(ws.parent, ws))


@pytest.mark.parametrize('shape', SHAPES)
def test_component_assemble_output_outside(layout, shape):
    ws, outside = layout
    load_all(ws)
    _res = run_trestle(ws, 'author', 'component-generate', '-n', 'comp_def_a', '-o', 'md_comp')
    assert _res.returncode == 0, _res.stdout[-2000:] + _res.stderr[-2000:]
    name = spell(shape, ws / 'component-definitions', outside / 'assembled_comp')
    before = snapshot(ws.parent, ws)
    res = run_trestle(ws, 'author', 'component-assemble', '-m', 'md_comp', '-n', 'comp_def_a', '-o', name)
    assert_refused(res, before, snapshot(ws.parent, ws))


@pytest.mark.parametrize('shape', SHAPES)
def test_profile_resolve_output_outside(layout, shape):
    ws, outside = layout
    load_all(ws)
    name = spell(shape, ws / 'catalogs', outside / 'resolved')
    before = snapshot(ws.parent, ws)
    res = run_trestle(ws, 'author', 'profile-resolve', '-n', 'simplified_nist_profile', '-o', name)
    assert_refused(res, before, snapshot(ws.parent, ws))
