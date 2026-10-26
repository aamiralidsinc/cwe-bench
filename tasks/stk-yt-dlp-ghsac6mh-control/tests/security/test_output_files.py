"""Remote media metadata must not choose the type of the file that is saved."""
import pytest

from harness import LocalServer, download
from yt_dlp.utils import YoutubeDLError


@pytest.fixture
def server():
    srv = LocalServer()
    try:
        yield srv
    finally:
        srv.close()


@pytest.mark.parametrize('ext', ['desktop', 'exe', 'url', 'webloc'])
def test_media_metadata_extension_refused(tmp_path, server, ext):
    err, created, _ = download(tmp_path, {'ext': ext}, {'outtmpl': '%(title)s.%(ext)s'}, server)
    assert err is not None, 'the download was not refused'
    assert isinstance(err, YoutubeDLError), f'unexpected error type {type(err).__name__}: {err}'
    assert not [p for p in created if p.lower().endswith('.' + ext)], created
