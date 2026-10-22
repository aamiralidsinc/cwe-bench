"""SSP generation: the inheritance view folder name must stay inside the workspace."""

import pytest

from conftest import assert_refused, load_all, run_trestle, snapshot
from shapes import spell


def _make_ssp(ws):
    res = run_trestle(ws, 'author', 'ssp-generate', '-p', 'comp_prof_aa', '-cd', 'comp_def_a,comp_def_b', '-o', 'md_ssp')
    assert res.returncode == 0, res.stdout + res.stderr
    res = run_trestle(ws, 'author', 'ssp-assemble', '-m', 'md_ssp', '-cd', 'comp_def_a,comp_def_b', '-o', 'my_ssp')
    assert res.returncode == 0, res.stdout + res.stderr


@pytest.mark.parametrize('shape', ['absolute', 'parent'])
def test_ssp_inheritance_view_outside(layout, shape):
    ws, outside = layout
    load_all(ws)
    _make_ssp(ws)
    # the name is offered for a folder placed under the generated ssp markdown folder
    name = spell(shape, ws / 'md_more', outside / 'inh')
    before = snapshot(ws.parent, ws)
    res = run_trestle(
        ws,
        'author',
        'ssp-generate',
        '-p',
        'comp_prof_aa',
        '-cd',
        'comp_def_a,comp_def_b',
        '-o',
        'md_more',
        '-ls',
        'my_ssp',
        '--inheritance-view',
        name,
    )
    assert_refused(res, before, snapshot(ws.parent, ws))
