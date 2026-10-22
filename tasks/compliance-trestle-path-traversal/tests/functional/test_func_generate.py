"""Markdown generation keeps working for ordinary, nested output folders."""

from conftest import load_all, run_trestle, snapshot


def _ok(res):
    assert res.returncode == 0, res.stdout[-3000:] + res.stderr[-3000:]


def test_catalog_generate_nested_output(layout):
    ws, outside = layout
    load_all(ws)
    before = snapshot(ws.parent, ws)
    _ok(run_trestle(ws, 'author', 'catalog-generate', '-n', 'simplified_nist_catalog', '-o', 'markdown/catalogs/nist'))
    assert (ws / 'markdown/catalogs/nist/ac/ac-1.md').is_file()
    assert snapshot(ws.parent, ws) == before


def test_catalog_generate_force_overwrite_inside(layout):
    ws, _ = layout
    load_all(ws)
    stale = ws / 'md_cat' / 'stale.md'
    stale.parent.mkdir()
    stale.write_text('old\n')
    _ok(run_trestle(ws, 'author', 'catalog-generate', '-n', 'simplified_nist_catalog', '-o', 'md_cat', '-fo'))
    assert not stale.exists()
    assert (ws / 'md_cat/ac/ac-1.md').is_file()


def test_profile_generate_and_assemble(layout):
    ws, _ = layout
    load_all(ws)
    _ok(run_trestle(ws, 'author', 'profile-generate', '-n', 'simplified_nist_profile', '-o', 'md/profiles/main'))
    assert (ws / 'md/profiles/main/ac/ac-1.md').is_file()
    _ok(
        run_trestle(
            ws, 'author', 'profile-assemble', '-n', 'simplified_nist_profile', '-m', 'md/profiles/main', '-o', 'assembled'
        )
    )
    assert (ws / 'profiles/assembled/profile.json').is_file()


def test_ssp_generate_and_assemble(layout):
    ws, _ = layout
    load_all(ws)
    _ok(run_trestle(ws, 'author', 'ssp-generate', '-p', 'comp_prof_aa', '-cd', 'comp_def_a,comp_def_b', '-o', 'ssp/md'))
    assert (ws / 'ssp/md/ac/ac-1.md').is_file()
    _ok(run_trestle(ws, 'author', 'ssp-assemble', '-m', 'ssp/md', '-cd', 'comp_def_a,comp_def_b', '-o', 'my_ssp'))
    assert (ws / 'system-security-plans/my_ssp/system-security-plan.json').is_file()


def test_component_generate_nested_and_force_overwrite(layout):
    ws, _ = layout
    load_all(ws)
    _ok(run_trestle(ws, 'author', 'component-generate', '-n', 'comp_def_a', '-o', 'md/components'))
    generated = sorted(p.name for p in (ws / 'md/components').iterdir())
    assert generated
    stale = ws / 'md/components/stale.md'
    stale.write_text('old\n')
    _ok(run_trestle(ws, 'author', 'component-generate', '-n', 'comp_def_a', '-o', 'md/components', '-fo'))
    assert not stale.exists()
    assert sorted(p.name for p in (ws / 'md/components').iterdir()) == generated


def test_component_generate_and_assemble(layout):
    ws, _ = layout
    load_all(ws)
    _ok(run_trestle(ws, 'author', 'component-generate', '-n', 'comp_def_a', '-o', 'md_comp'))
    _ok(run_trestle(ws, 'author', 'component-assemble', '-m', 'md_comp', '-n', 'comp_def_a', '-o', 'comp_out'))
    assert (ws / 'component-definitions/comp_out/component-definition.json').is_file()
