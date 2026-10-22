"""Shared helpers for the hidden tests (identical copy in security/ and functional/).

Every test drives the real `trestle` command line in a subprocess, inside a fresh
trestle workspace under pytest's tmp_path. Expected values and clean-up are computed
here with the standard library only, never with trestle code.
"""

import os
import pathlib
import shutil
import subprocess
import sys

import pytest

FIXTURES = pathlib.Path(__file__).resolve().parent.parent / 'fixtures'

MODEL_DIRS = {
    'catalog': 'catalogs',
    'profile': 'profiles',
    'component-definition': 'component-definitions',
    'system-security-plan': 'system-security-plans',
}

_TEMPLATE_WS = {}


def run_trestle(ws: pathlib.Path, *args: str, cwd: pathlib.Path = None) -> subprocess.CompletedProcess:
    """Run `trestle <args>` with the workspace as working directory."""
    env = dict(os.environ)
    env.pop('PYTHONPATH', None)
    return subprocess.run(
        [sys.executable, '-m', 'trestle', *args],
        cwd=str(cwd or ws),
        env=env,
        capture_output=True,
        text=True,
        timeout=300,
    )


def _template_workspace(tmp_path_factory) -> pathlib.Path:
    if 'ws' not in _TEMPLATE_WS:
        base = tmp_path_factory.mktemp('template')
        ws = base / 'ws'
        ws.mkdir()
        res = run_trestle(ws, 'init')
        assert res.returncode == 0, res.stdout + res.stderr
        _TEMPLATE_WS['ws'] = ws
    return _TEMPLATE_WS['ws']


def put_model(ws: pathlib.Path, model_type: str, fixture: str, name: str) -> pathlib.Path:
    """Place a fixture model into the workspace as <model dir>/<name>/<type>.json."""
    dst = ws / MODEL_DIRS[model_type] / name / f'{model_type}.json'
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(FIXTURES / f'{fixture}.json', dst)
    return dst


@pytest.fixture
def layout(tmp_path, tmp_path_factory):
    """A trestle workspace at <tmp>/ws next to an unrelated directory <tmp>/ws-outside.

    The outside directory's name starts with the workspace's name, so a bare string-prefix
    comparison of the two paths would wrongly count it as inside.

    The outside directory already holds some user data (a marker file and a
    sub-directory) so that deletion or overwrite outside the workspace is visible.
    """
    ws = tmp_path / 'ws'
    shutil.copytree(_template_workspace(tmp_path_factory), ws, symlinks=True)
    outside = tmp_path / 'ws-outside'
    (outside / 'keep').mkdir(parents=True)
    (outside / 'marker.txt').write_text('outside data\n')
    (outside / 'keep' / 'notes.txt').write_text('more outside data\n')
    return ws, outside


@pytest.fixture
def neighbour(tmp_path, tmp_path_factory, layout):
    """A second, unrelated trestle workspace at <tmp>/ws-neighbour that already holds a catalog."""
    other = tmp_path / 'ws-neighbour'
    shutil.copytree(_template_workspace(tmp_path_factory), other, symlinks=True)
    put_model(other, 'catalog', 'simplified_nist_catalog', 'theirs')
    return other


def load_all(ws: pathlib.Path) -> None:
    """Catalog, profiles and component definitions used by the author commands."""
    put_model(ws, 'catalog', 'simplified_nist_catalog', 'simplified_nist_catalog')
    for prof in ('simplified_nist_profile', 'comp_prof_aa', 'comp_prof_ab', 'comp_prof_ba', 'comp_prof_bb'):
        put_model(ws, 'profile', prof, prof)
    for cd in ('comp_def_a', 'comp_def_b'):
        put_model(ws, 'component-definition', cd, cd)


def snapshot(root: pathlib.Path, exclude: pathlib.Path) -> dict:
    """Map of every path under root (except the workspace) to its content (files) or None (dirs)."""
    out = {}
    for dirpath, dirnames, filenames in os.walk(root):
        d = pathlib.Path(dirpath)
        if d == exclude or exclude in d.parents:
            dirnames[:] = []
            continue
        dirnames[:] = [n for n in dirnames if d / n != exclude]
        for n in dirnames:
            out[str((d / n).relative_to(root))] = None
        for n in filenames:
            p = d / n
            try:
                out[str(p.relative_to(root))] = p.read_bytes()
            except OSError:
                out[str(p.relative_to(root))] = b'<unreadable>'
    return out


def rel_from(base: pathlib.Path, target: pathlib.Path) -> str:
    """A relative spelling of target as seen from base (uses '..' as needed)."""
    return os.path.relpath(str(target), str(base))


def assert_refused(res: subprocess.CompletedProcess, before: dict, after: dict) -> None:
    """The command must fail and nothing outside the workspace may change."""
    changed = sorted(set(before) ^ set(after)) + sorted(k for k in before if k in after and before[k] != after[k])
    assert not changed, f'paths outside the workspace were created, changed or deleted: {changed[:10]}'
    assert res.returncode != 0, (
        'command reported success for an output name outside the workspace\n' + res.stdout[-2000:] + res.stderr[-2000:]
    )
