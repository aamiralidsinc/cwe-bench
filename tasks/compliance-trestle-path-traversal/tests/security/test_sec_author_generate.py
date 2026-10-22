"""Markdown generation commands: the output folder name must stay inside the workspace."""

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


def test_catalog_generate_force_overwrite_outside(layout):
    ws, outside = layout
    load_all(ws)
    before = snapshot(ws.parent, ws)
    res = run_trestle(ws, 'author', 'catalog-generate', '-n', 'simplified_nist_catalog', '-o', str(outside), '-fo')
    assert_refused(res, before, snapshot(ws.parent, ws))


@pytest.mark.parametrize('shape', SHAPES)
def test_profile_generate_output_outside(layout, shape):
    ws, outside = layout
    load_all(ws)
    name = spell(shape, ws, outside / 'prof_md')
    before = snapshot(ws.parent, ws)
    res = run_trestle(ws, 'author', 'profile-generate', '-n', 'simplified_nist_profile', '-o', name)
    assert_refused(res, before, snapshot(ws.parent, ws))


def test_profile_generate_force_overwrite_outside(layout):
    ws, outside = layout
    load_all(ws)
    before = snapshot(ws.parent, ws)
    res = run_trestle(ws, 'author', 'profile-generate', '-n', 'simplified_nist_profile', '-o', str(outside), '-fo')
    assert_refused(res, before, snapshot(ws.parent, ws))


@pytest.mark.parametrize('shape', SHAPES)
def test_ssp_generate_output_outside(layout, shape):
    ws, outside = layout
    load_all(ws)
    name = spell(shape, ws, outside / 'ssp_md')
    before = snapshot(ws.parent, ws)
    res = run_trestle(
        ws, 'author', 'ssp-generate', '-p', 'comp_prof_aa', '-cd', 'comp_def_a,comp_def_b', '-o', name
    )
    assert_refused(res, before, snapshot(ws.parent, ws))


def test_ssp_generate_force_overwrite_outside(layout):
    ws, outside = layout
    load_all(ws)
    before = snapshot(ws.parent, ws)
    res = run_trestle(
        ws, 'author', 'ssp-generate', '-p', 'comp_prof_aa', '-cd', 'comp_def_a,comp_def_b', '-o', str(outside), '-fo'
    )
    assert_refused(res, before, snapshot(ws.parent, ws))
