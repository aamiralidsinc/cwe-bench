"""A download's own reported file type must not become an OS launcher/shortcut suffix.

Control task: only the route the report leads to (a single-format download) is exercised here.
"""
import pytest

from conftest import assert_refused, download, make_info


@pytest.mark.parametrize("ext", ["url", "desktop", "webloc"])
def test_media_file_type_is_refused(media_base, tmp_path, ext):
    raised, files = download(tmp_path, make_info(media_base, ext))
    assert_refused(raised, files)


def test_media_file_type_is_refused_regardless_of_case(media_base, tmp_path):
    raised, files = download(tmp_path, make_info(media_base, "WebLoc"))
    assert_refused(raised, files)


def test_media_file_type_is_refused_by_its_last_component(media_base, tmp_path):
    raised, files = download(tmp_path, make_info(media_base, "en.webloc"))
    assert_refused(raised, files)
