"""Remote metadata must not choose the type or location of a created file."""
import os

import pytest

from harness import LocalServer, download, outside
from yt_dlp.utils import YoutubeDLError


@pytest.fixture
def server():
    srv = LocalServer()
    try:
        yield srv
    finally:
        srv.close()


def _refused_without(err, created, suffix):
    assert err is not None, 'the download was not refused'
    assert isinstance(err, YoutubeDLError), f'unexpected error type {type(err).__name__}: {err}'
    assert not [p for p in created if p.lower().endswith(suffix)], created


@pytest.mark.parametrize('ext', ['desktop', 'exe', 'url', 'webloc'])
def test_media_metadata_extension_refused(tmp_path, server, ext):
    err, created, _ = download(tmp_path, {'ext': ext}, {'outtmpl': '%(title)s.%(ext)s'}, server)
    _refused_without(err, created, '.' + ext)


def test_subtitle_extension_refused(tmp_path, server):
    info = {'subtitles': {'en': [{'url': server.url('sub.desktop')}]}}
    params = {'outtmpl': '%(title)s.%(ext)s', 'writesubtitles': True, 'subtitleslangs': ['en']}
    err, created, _ = download(tmp_path, info, params, server)
    _refused_without(err, created, '.desktop')


def test_thumbnail_extension_refused(tmp_path, server):
    info = {'thumbnails': [{'url': server.url('thumb.desktop')}]}
    params = {'outtmpl': '%(title)s.%(ext)s', 'writethumbnail': True}
    err, created, _ = download(tmp_path, info, params, server)
    _refused_without(err, created, '.desktop')


@pytest.mark.parametrize('field', ['uploader', 'title'])
def test_metadata_component_cannot_escape(tmp_path, server, field):
    info = {'ext': 'mp4', field: '..'}
    params = {'outtmpl': f'%({field})s/%(title)s.%(ext)s'}
    err, created, home = download(tmp_path, info, params, server)
    assert not outside(created, home), f'created outside the chosen folder: {outside(created, home)}'


@pytest.mark.parametrize('field', ['format_id', 'format_note'])
def test_extension_from_another_field_refused(tmp_path, server, field):
    info = {'ext': 'mp4', 'formats': [
        {'format_id': 'v', 'ext': 'mp4', 'vcodec': 'h264', 'acodec': 'aac', field: 'desktop'},
    ]}
    params = {'outtmpl': f'%(title)s.%({field})s'}
    err, created, _ = download(tmp_path, info, params, server)
    _refused_without(err, created, '.desktop')


@pytest.mark.parametrize('name', ['tool.exe', 'tool.desktop'])
def test_whole_name_extension_refused(tmp_path, server, name):
    err, created, _ = download(tmp_path, {'title': name}, {'outtmpl': '%(title)s'}, server)
    _refused_without(err, created, os.path.splitext(name)[1])


def test_refusal_leaves_no_directory(tmp_path, server):
    info = {'ext': 'desktop', 'uploader': 'chosen-by-site'}
    params = {'outtmpl': '%(uploader)s/%(title)s.%(ext)s'}
    err, created, home = download(tmp_path, info, params, server)
    assert err is not None
    assert not os.path.exists(home / 'chosen-by-site'), f'refusal left a directory: {created}'
    assert not [p for p in created if p.lower().endswith('.desktop')], created
