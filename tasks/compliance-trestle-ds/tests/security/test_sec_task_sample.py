"""Sample creation for governed documents must not write through an existing link out of the workspace."""

from conftest import assert_refused, run_trestle, snapshot


def test_docs_create_sample_symlinked_task_outside(layout):
    ws, outside = layout
    target = outside / 'linked'
    target.mkdir()
    (ws / 'mdlink').symlink_to(target, target_is_directory=True)
    run_trestle(ws, 'author', 'docs', 'setup', '-tn', 'mdlink')
    before = snapshot(ws.parent, ws)
    res = run_trestle(ws, 'author', 'docs', 'create-sample', '-tn', 'mdlink')
    assert_refused(res, before, snapshot(ws.parent, ws))


def test_folders_create_sample_symlinked_task_outside(layout):
    ws, outside = layout
    target = outside / 'linked_folders'
    target.mkdir()
    (ws / 'folink').symlink_to(target, target_is_directory=True)
    run_trestle(ws, 'author', 'folders', 'setup', '-tn', 'folink')
    before = snapshot(ws.parent, ws)
    res = run_trestle(ws, 'author', 'folders', 'create-sample', '-tn', 'folink')
    assert_refused(res, before, snapshot(ws.parent, ws))
