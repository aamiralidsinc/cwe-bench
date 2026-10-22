"""Model management by name keeps working inside the workspace."""

import json
import shutil

from conftest import FIXTURES, load_all, run_trestle, snapshot


def _ok(res):
    assert res.returncode == 0, res.stdout[-3000:] + res.stderr[-3000:]


def test_create_replicate_import(layout, neighbour):
    ws, _ = layout
    load_all(ws)
    before = snapshot(ws.parent, ws)
    _ok(run_trestle(ws, 'create', '-t', 'catalog', '-o', 'fresh'))
    assert (ws / 'catalogs/fresh/catalog.json').is_file()
    _ok(run_trestle(ws, 'replicate', 'catalog', '-n', 'simplified_nist_catalog', '-o', 'copy'))
    assert (ws / 'catalogs/copy/catalog.json').is_file()
    _ok(run_trestle(ws, 'create', '-t', 'profile', '-o', 'fresh_profile'))
    assert (ws / 'profiles/fresh_profile/profile.json').is_file()
    assert snapshot(ws.parent, ws) == before


def test_import_named(layout):
    ws, _ = layout
    src = ws.parent / 'incoming' / 'catalog.json'
    src.parent.mkdir()
    shutil.copy2(FIXTURES / 'simplified_nist_catalog.json', src)
    _ok(run_trestle(ws, 'import', '-f', str(src), '-o', 'imported'))
    data = json.loads((ws / 'catalogs/imported/catalog.json').read_text())
    assert 'catalog' in data


def test_catalog_assemble_overwrites_own_output(layout):
    ws, _ = layout
    load_all(ws)
    _ok(run_trestle(ws, 'author', 'catalog-generate', '-n', 'simplified_nist_catalog', '-o', 'md_cat'))
    _ok(run_trestle(ws, 'author', 'catalog-assemble', '-m', 'md_cat', '-o', 'assembled'))
    out = ws / 'catalogs/assembled/catalog.json'
    assert out.is_file()
    _ok(run_trestle(ws, 'author', 'catalog-assemble', '-m', 'md_cat', '-o', 'assembled', '-vn', '9.9'))
    assert json.loads(out.read_text())['catalog']['metadata']['version'] == '9.9'


def test_profile_resolve(layout):
    ws, _ = layout
    load_all(ws)
    _ok(run_trestle(ws, 'author', 'profile-resolve', '-n', 'simplified_nist_profile', '-o', 'resolved'))
    assert (ws / 'catalogs/resolved/catalog.json').is_file()


def test_create_output_outside_any_workspace_still_refused(layout):
    """A bare outside path is refused today and must stay refused."""
    ws, outside = layout
    res = run_trestle(ws, 'create', '-t', 'catalog', '-o', str(outside / 'bare'))
    assert res.returncode != 0
    assert not (outside / 'bare').exists()
