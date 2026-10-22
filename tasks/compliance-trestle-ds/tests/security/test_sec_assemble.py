"""Commands that write a model back into the workspace under an output name."""

import pytest

from conftest import assert_refused, load_all, run_trestle, snapshot
from shapes import spell


def _generate(ws, *args):
    res = run_trestle(ws, 'author', *args)
    assert res.returncode == 0, res.stdout + res.stderr


@pytest.mark.parametrize('shape', ['parent', 'nested_parent'])
def test_catalog_assemble_output_outside(layout, shape):
    ws, outside = layout
    load_all(ws)
    _generate(ws, 'catalog-generate', '-n', 'simplified_nist_catalog', '-o', 'md_cat')
    # the output name designates the existing outside directory itself
    name = spell(shape, ws / 'catalogs', outside)
    before = snapshot(ws.parent, ws)
    res = run_trestle(ws, 'author', 'catalog-assemble', '-m', 'md_cat', '-o', name)
    assert_refused(res, before, snapshot(ws.parent, ws))


def test_component_assemble_output_outside(layout):
    ws, outside = layout
    load_all(ws)
    _generate(ws, 'component-generate', '-n', 'comp_def_a', '-o', 'md_comp')
    name = spell('parent', ws / 'component-definitions', outside)
    before = snapshot(ws.parent, ws)
    res = run_trestle(ws, 'author', 'component-assemble', '-m', 'md_comp', '-n', 'comp_def_a', '-o', name)
    assert_refused(res, before, snapshot(ws.parent, ws))


def test_profile_resolve_output_outside(layout):
    ws, outside = layout
    load_all(ws)
    name = spell('parent', ws / 'catalogs', outside / 'resolved')
    before = snapshot(ws.parent, ws)
    res = run_trestle(ws, 'author', 'profile-resolve', '-n', 'simplified_nist_profile', '-o', name)
    assert_refused(res, before, snapshot(ws.parent, ws))


def test_ssp_assemble_output_outside(layout):
    ws, outside = layout
    load_all(ws)
    _generate(ws, 'ssp-generate', '-p', 'comp_prof_aa', '-cd', 'comp_def_a,comp_def_b', '-o', 'md_ssp')
    name = spell('parent', ws / 'system-security-plans', outside / 'assembled_ssp')
    before = snapshot(ws.parent, ws)
    res = run_trestle(ws, 'author', 'ssp-assemble', '-m', 'md_ssp', '-cd', 'comp_def_a,comp_def_b', '-o', name)
    assert_refused(res, before, snapshot(ws.parent, ws))


def test_profile_assemble_output_outside(layout):
    ws, outside = layout
    load_all(ws)
    _generate(ws, 'profile-generate', '-n', 'simplified_nist_profile', '-o', 'md_prof')
    name = spell('parent', ws / 'profiles', outside)
    before = snapshot(ws.parent, ws)
    res = run_trestle(
        ws, 'author', 'profile-assemble', '-n', 'simplified_nist_profile', '-m', 'md_prof', '-o', name
    )
    assert_refused(res, before, snapshot(ws.parent, ws))


def _assembled_ssp(ws):
    load_all(ws)
    _generate(ws, 'ssp-generate', '-p', 'comp_prof_aa', '-cd', 'comp_def_a,comp_def_b', '-o', 'md_ssp')
    _generate(ws, 'ssp-assemble', '-m', 'md_ssp', '-cd', 'comp_def_a,comp_def_b', '-o', 'my_ssp')


def test_ssp_filter_output_outside(layout):
    ws, outside = layout
    _assembled_ssp(ws)
    name = spell('parent', ws / 'system-security-plans', outside / 'filtered_ssp')
    before = snapshot(ws.parent, ws)
    res = run_trestle(ws, 'author', 'ssp-filter', '-n', 'my_ssp', '-p', 'comp_prof_aa', '-o', name)
    assert_refused(res, before, snapshot(ws.parent, ws))


def test_profile_inherit_output_outside(layout):
    ws, outside = layout
    _assembled_ssp(ws)
    name = spell('parent', ws / 'profiles', outside / 'inherited')
    before = snapshot(ws.parent, ws)
    res = run_trestle(ws, 'author', 'profile-inherit', '-s', 'my_ssp', '-p', 'comp_prof_aa', '-o', name)
    assert_refused(res, before, snapshot(ws.parent, ws))
