"""Harness for the yt-dlp download-naming task.

Every test drives the library's public download API against a video served from a loopback
HTTP server and inspects the files it leaves behind. All expectations are computed here from
plain filesystem checks, never with product helpers, so a stricter fix cannot break the
harness.
"""
import http.server
import os
import threading

import pytest

PAYLOAD = b"yt-dlp task fixture payload\n" * 16
LAUNCHER_SUFFIXES = ("url", "desktop", "webloc")


class _Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/octet-stream")
        self.send_header("Content-Length", str(len(PAYLOAD)))
        self.end_headers()
        self.wfile.write(PAYLOAD)

    def log_message(self, *args):
        pass


@pytest.fixture(scope="session")
def media_base():
    """A loopback origin that serves the video bytes for every download in the suite."""
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield "http://127.0.0.1:%d" % server.server_address[1]
    finally:
        server.shutdown()
        server.server_close()


def make_info(base, ext, **extra):
    info = {
        "id": "taskfixture",
        "title": "task fixture",
        "ext": ext,
        "protocol": "http",
        "url": base + "/media",
        "webpage_url": base + "/watch",
    }
    info.update(extra)
    return info


def make_merged_info(base, merged_ext, format_exts):
    return {
        "id": "merged",
        "title": "merged fixture",
        "ext": merged_ext,
        "requested_formats": [
            {"format_id": "f%d" % index, "ext": ext, "protocol": "http",
             "url": base + "/part%d" % index}
            for index, ext in enumerate(format_exts)
        ],
        "webpage_url": base + "/watch",
    }


def download(tmp_path, info, params=None):
    """Process one resolved download; return (exception or None, files written under tmp_path)."""
    from yt_dlp import YoutubeDL

    options = {
        "outtmpl": {"default": os.path.join(str(tmp_path), "%(title)s [%(id)s].%(ext)s")},
        "paths": {},
        "quiet": True,
        "no_warnings": True,
        "noprogress": True,
        "socket_timeout": 10,
        "retries": 0,
    }
    if params:
        options.update(params)

    ydl = YoutubeDL(options)
    raised = None
    try:
        ydl.process_info(dict(info))
    except Exception as error:  # the suite asserts the refusal form, so keep the object
        raised = error

    files = []
    for root, _dirs, names in os.walk(str(tmp_path)):
        for name in names:
            files.append(os.path.join(root, name))
    return raised, files


def launcher_files(files):
    """Files whose final suffix the desktop treats as a launcher/shortcut type."""
    return [path for path in files
            if os.path.splitext(path)[1].lstrip(".").lower() in LAUNCHER_SUFFIXES]


def assert_refused(raised, files):
    """A refused download raises the library's download error and leaves no launcher file."""
    from yt_dlp.utils import DownloadError

    written = launcher_files(files)
    assert written == [], "a download wrote launcher-type files: %r" % (written,)
    assert isinstance(raised, DownloadError), (
        "the download was not refused with the library's download error: %r" % (raised,))
