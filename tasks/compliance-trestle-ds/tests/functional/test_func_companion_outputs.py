"""Legitimate use of the companion output names keeps working."""

import json

from conftest import load_all, run_trestle


def _ok(res):
    assert res.returncode == 0, res.stdout[-3000:] + res.stderr[-3000:]


def test_assemble_custom_output_inside(layout):
    ws, _ = layout
    load_all(ws)
    _ok(run_trestle(ws, 'assemble', 'catalog', '-n', 'simplified_nist_catalog', '-o', 'my_assembled_name'))
    out = ws / 'dist' / 'catalogs' / 'my_assembled_name.json'
    assert out.is_file()
    assert 'catalog' in json.loads(out.read_text())
    # the default output naming is untouched
    _ok(run_trestle(ws, 'assemble', 'catalog', '-n', 'simplified_nist_catalog'))
    assert (ws / 'dist' / 'catalogs' / 'simplified_nist_catalog.json').is_file()


def test_component_generate_index_inside(layout):
    ws, _ = layout
    load_all(ws)
    _ok(
        run_trestle(
            ws,
            'author',
            'component-generate',
            '-n',
            'comp_def_a',
            '-o',
            'md_components',
            '--index',
            'docs/index/component-index.md',
        )
    )
    index = ws / 'docs' / 'index' / 'component-index.md'
    assert index.is_file()
    text = index.read_text()
    folders = sorted(p.name for p in (ws / 'md_components').iterdir() if p.is_dir())
    assert folders
    for folder in folders:
        assert folder in text
    assert (ws / 'md_components' / folders[0]).is_dir()


def _make_ssp(ws):
    _ok(run_trestle(ws, 'author', 'ssp-generate', '-p', 'comp_prof_aa', '-cd', 'comp_def_a,comp_def_b', '-o', 'md_ssp'))
    _ok(run_trestle(ws, 'author', 'ssp-assemble', '-m', 'md_ssp', '-cd', 'comp_def_a,comp_def_b', '-o', 'my_ssp'))


def test_ssp_inheritance_view_inside(layout):
    ws, _ = layout
    load_all(ws)
    _make_ssp(ws)
    _ok(
        run_trestle(
            ws,
            'author',
            'ssp-generate',
            '-p',
            'comp_prof_aa',
            '-cd',
            'comp_def_a,comp_def_b',
            '-o',
            'md_inherit',
            '-ls',
            'my_ssp',
            '--inheritance-view',
            'legacy_view',
        )
    )
    assert (ws / 'md_inherit' / 'legacy_view').is_dir()
    # the default folder name is unchanged when the option is omitted
    _ok(
        run_trestle(
            ws,
            'author',
            'ssp-generate',
            '-p',
            'comp_prof_aa',
            '-cd',
            'comp_def_a,comp_def_b',
            '-o',
            'md_default',
            '-ls',
            'my_ssp',
        )
    )
    assert (ws / 'md_default' / 'inheritance').is_dir()
