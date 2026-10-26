"""Legitimate downloads and every documented output behaviour must keep working."""
import os

import pytest

from conftest import download, make_info, make_merged_info


def test_regular_media_download(media_base, tmp_path):
    raised, files = download(tmp_path, make_info(media_base, "mp4"))
    assert raised is None, "an ordinary download was refused: %r" % (raised,)
    assert [os.path.basename(path) for path in files] == ["task fixture [taskfixture].mp4"]


def test_requested_conversion_keeps_the_downloaded_suffix(media_base, tmp_path):
    raised, files = download(tmp_path, make_info(media_base, "webm"), {"final_ext": "mp4"})
    assert raised is None, "a conversion download was refused: %r" % (raised,)
    assert [os.path.basename(path) for path in files] == ["task fixture [taskfixture].webm"]


def test_merged_download_writes_each_part(media_base, tmp_path):
    info = make_merged_info(media_base, "mp4", ["mp4", "mp4"])
    raised, files = download(tmp_path, info, {"allow_unplayable_formats": True})
    assert raised is None, "a merged download was refused: %r" % (raised,)
    assert sorted(os.path.basename(path) for path in files) == [
        "merged fixture [merged].ff0.mp4", "merged fixture [merged].ff1.mp4"]


@pytest.mark.parametrize("option, suffix", [
    ("writeurllink", "url"),
    ("writedesktoplink", "desktop"),
    ("writewebloclink", "webloc"),
])
def test_shortcut_file_is_written_when_requested(media_base, tmp_path, option, suffix):
    raised, files = download(tmp_path, make_info(media_base, "mp4"), {option: True})
    assert raised is None, "the shortcut download was refused: %r" % (raised,)
    names = sorted(os.path.basename(path) for path in files)
    assert "task fixture [taskfixture].mp4" in names
    assert "task fixture [taskfixture].%s" % suffix in names


def test_default_shortcut_option_is_written(media_base, tmp_path):
    raised, files = download(tmp_path, make_info(media_base, "mp4"), {"writelink": True})
    assert raised is None, "the shortcut download was refused: %r" % (raised,)
    suffixes = {os.path.splitext(path)[1].lstrip(".") for path in files}
    assert suffixes & {"url", "desktop", "webloc"}
    assert "mp4" in suffixes


def test_prepend_extension_keeps_unlisted_infixes():
    from yt_dlp.utils import prepend_extension, replace_extension

    assert prepend_extension("abc.ext", "f137", "ext") == "abc.f137.ext"
    assert prepend_extension("abc.ext", "exe", "ext") == "abc.exe.ext"
    assert prepend_extension("abc.ext", "temp") == "abc.temp.ext"
    assert replace_extension("abc.ext", "bin") == "abc.unknown_video"


@pytest.mark.parametrize("ext", [
    "mp4", "webm", "mkv", "m4a", "mp3", "vtt", "srt", "json",
    "mhtml", "svg", "xml", "m3u", "unknown_video", "f4m", "mpd",
])
def test_legitimate_extensions_are_accepted(ext):
    from yt_dlp.utils import replace_extension

    assert replace_extension("abc.old", ext) == "abc." + ext
