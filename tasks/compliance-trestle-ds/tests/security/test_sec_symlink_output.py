"""A name that only leaves the workspace after following a link inside it."""

from conftest import assert_refused, load_all, run_trestle, snapshot


def test_catalog_generate_symlinked_output_outside(layout):
    ws, outside = layout
    load_all(ws)
    target = outside / 'through'
    target.mkdir()
    (ws / 'mdlink').symlink_to(target, target_is_directory=True)
    before = snapshot(ws.parent, ws)
    res = run_trestle(ws, 'author', 'catalog-generate', '-n', 'simplified_nist_catalog', '-o', 'mdlink')
    assert_refused(res, before, snapshot(ws.parent, ws))
