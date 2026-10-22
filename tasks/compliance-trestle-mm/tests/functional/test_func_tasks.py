"""Task folders for governed documents: nested task names and workspace-wide validation."""

import shutil

from conftest import FIXTURES, run_trestle


def _ok(res):
    assert res.returncode == 0, res.stdout[-3000:] + res.stderr[-3000:]


def test_docs_setup_nested_task(layout):
    ws, _ = layout
    _ok(run_trestle(ws, 'author', 'docs', 'setup', '-tn', 'policies/access'))
    assert (ws / 'policies/access').is_dir()
    assert (ws / '.trestle/author/policies/access').is_dir()


def test_folders_setup_nested_task(layout):
    ws, _ = layout
    _ok(run_trestle(ws, 'author', 'folders', 'setup', '-tn', 'architecture/diagrams'))
    assert (ws / 'architecture/diagrams').is_dir()


def test_reserved_task_name_still_refused(layout):
    ws, _ = layout
    res = run_trestle(ws, 'author', 'docs', 'setup', '-tn', 'catalogs')
    assert res.returncode != 0


def _global_headers(ws):
    _ok(run_trestle(ws, 'author', 'headers', 'setup', '--global'))
    tdir = ws / '.trestle/author/__global__'
    templates = list(tdir.rglob('template.md'))
    assert templates, 'headers setup created no template'
    for t in templates:
        shutil.copy2(FIXTURES / 'headers_template.md', t)


def _doc(path, header_ok):
    path.parent.mkdir(parents=True, exist_ok=True)
    head = 'hello: world\nreally: awesome\n' if header_ok else 'missing: world\n'
    path.write_text(f'---\n{head}---\n\n# Heading\n')


def test_headers_validate_whole_workspace(layout):
    ws, _ = layout
    _global_headers(ws)
    _doc(ws / 'reports/q1/summary.md', True)
    _doc(ws / 'guides/intro.md', True)
    _ok(run_trestle(ws, 'author', 'headers', 'validate', '--global', '-r'))
    _doc(ws / 'drafts/bad.md', False)
    res = run_trestle(ws, 'author', 'headers', 'validate', '--global', '-r')
    assert res.returncode != 0, 'a document with a non-conforming header in a workspace folder was not reported'


def test_docs_create_sample_named_inside_task(layout):
    ws, _ = layout
    _ok(run_trestle(ws, 'author', 'docs', 'setup', '-tn', 'policies'))
    _ok(run_trestle(ws, 'author', 'docs', 'create-sample', '-tn', 'policies'))
    _ok(run_trestle(ws, 'author', 'docs', 'create-sample', '-tn', 'policies', '--sample-name', 'intro.md'))
    assert (ws / 'policies' / 'intro.md').is_file()
    _ok(run_trestle(ws, 'author', 'docs', 'create-sample', '-tn', 'policies', '--sample-name', 'notes/plan.md'))
    assert (ws / 'policies' / 'notes' / 'plan.md').is_file()


def test_folders_create_sample_named_inside_task(layout):
    ws, _ = layout
    _ok(run_trestle(ws, 'author', 'folders', 'setup', '-tn', 'architecture'))
    _ok(run_trestle(ws, 'author', 'folders', 'create-sample', '-tn', 'architecture', '--sample-name', 'sample_a'))
    assert (ws / 'architecture' / 'sample_a').is_dir()
    assert any((ws / 'architecture' / 'sample_a').iterdir())
