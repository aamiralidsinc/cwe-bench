"""A download's own reported file type must not become an OS launcher/shortcut suffix.

Each test drives the library's public download API through a real download and asserts the
refusal form and the absence of the side effect.
"""
import pytest

from conftest import assert_refused, download, make_info, make_merged_info


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


@pytest.mark.parametrize("ext", ["url", "desktop"])
def test_requested_conversion_does_not_admit_a_launcher_suffix(media_base, tmp_path, ext):
    raised, files = download(tmp_path, make_info(media_base, ext), {"final_ext": "mp4"})
    assert_refused(raised, files)


@pytest.mark.parametrize("ext", ["url", "webloc"])
def test_merged_download_refuses_a_part_with_a_launcher_suffix(media_base, tmp_path, ext):
    info = make_merged_info(media_base, "mp4", ["mp4", ext])
    raised, files = download(tmp_path, info, {"allow_unplayable_formats": True})
    assert_refused(raised, files)
