"""Legitimate downloads keep working, including the values coupled to each rule."""
import os

import pytest

from harness import LocalServer, download


@pytest.fixture
def server():
    srv = LocalServer()
    try:
        yield srv
    finally:
        srv.close()


def test_media_download(tmp_path, server):
    err, created, home = download(tmp_path, {'ext': 'mp4'}, {'outtmpl': '%(title)s.%(ext)s'}, server)
    assert err is None, err
    assert (home / 'clip.mp4').is_file()


def test_subtitle_languages_and_formats(tmp_path, server):
    info = {'subtitles': {
        'zh-Hans': [{'url': server.url('sub.vtt')}],
        'pt-BR': [{'url': server.url('sub.json')}],
    }}
    params = {'outtmpl': '%(title)s.%(ext)s', 'writesubtitles': True,
              'subtitleslangs': ['zh-Hans', 'pt-BR']}
    err, created, home = download(tmp_path, info, params, server)
    assert err is None, err
    assert (home / 'clip.zh-Hans.vtt').is_file(), created
    assert (home / 'clip.pt-BR.json').is_file(), created


def test_thumbnails(tmp_path, server):
    info = {'thumbnails': [
        {'url': server.url('thumb0.jpg')},
        {'url': server.url('thumb1.png')},
        {'url': server.url('thumb2.webp')},
    ]}
    params = {'outtmpl': '%(title)s.%(ext)s', 'writethumbnail': True, 'write_all_thumbnails': True}
    err, created, _ = download(tmp_path, info, params, server)
    assert err is None, err
    for suffix in ('.jpg', '.png', '.webp'):
        assert [p for p in created if p.endswith(suffix)], created


def test_shortcut_links(tmp_path, server):
    params = {'outtmpl': '%(title)s.%(ext)s', 'writedesktoplink': True, 'writeurllink': True}
    err, created, _ = download(tmp_path, {'ext': 'mp4'}, params, server)
    assert err is None, err
    assert [p for p in created if p.endswith('.desktop')], created
    assert [p for p in created if p.endswith('.url')], created


def test_ids_keep_leading_dot_and_dash(tmp_path, server):
    err, created, home = download(
        tmp_path, {'id': '.abcd', 'title': '--gasdgf'}, {'outtmpl': '%(id)s.%(ext)s'}, server)
    assert err is None, err
    assert (home / '.abcd.mp4').is_file(), created


def test_literal_dotdot_template_keeps_working(tmp_path, server):
    err, created, home = download(
        tmp_path, {'ext': 'mp4'}, {'outtmpl': 'sub/../%(title)s.%(ext)s'}, server)
    assert err is None, err
    assert (home / 'clip.mp4').is_file(), created


def test_extensionless_template_keeps_working(tmp_path, server):
    err, created, home = download(
        tmp_path, {'title': 'My.Talk.Show'}, {'outtmpl': '%(title)s'}, server)
    assert err is None, err
    assert (home / 'My.Talk.Show').is_file(), created


def test_literal_extension_template_keeps_working(tmp_path, server):
    err, created, home = download(
        tmp_path, {'ext': 'mp4'}, {'outtmpl': '%(title)s.txt'}, server)
    assert err is None, err
    assert (home / 'clip.txt').is_file(), created


@pytest.mark.parametrize('ext', ['unknown_video', 'mhtml', 'f4m', 'mpd'])
def test_uncommon_legitimate_extensions(tmp_path, server, ext):
    err, created, home = download(tmp_path, {'ext': ext}, {'outtmpl': '%(title)s.%(ext)s'}, server)
    assert err is None, err
    assert (home / f'clip.{ext}').is_file(), created
