"""Local fixtures shared by the hidden suites.

Every download goes through the library's public entry point against a loopback HTTP server.
Expected values and cleanup are computed here with the standard library only, so a stricter
product fix cannot change what the fixture produces.
"""
import http.server
import os
import threading

PAYLOAD = b'media-bytes'
TEXTS = {
    'sub.vtt': (b'WEBVTT\n\n00:00.000 --> 00:01.000\nhi\n', 'text/vtt'),
    'sub.json': (b'{"events":[]}', 'application/json'),
    'sub.desktop': (b'[Desktop Entry]\nExec=/bin/true\n', 'text/plain'),
}


class LocalServer:
    def __init__(self):
        class Handler(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                name = self.path.lstrip('/').split('?')[0]
                body, ctype = TEXTS.get(name, (PAYLOAD, 'application/octet-stream'))
                self.send_response(200)
                self.send_header('Content-Type', ctype)
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *args):
                pass

        self.httpd = http.server.ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        self.port = self.httpd.server_address[1]
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()

    def url(self, name):
        return f'http://127.0.0.1:{self.port}/{name}'

    def close(self):
        self.httpd.shutdown()
        self.httpd.server_close()


def _make_ydl(payload, params):
    from yt_dlp import YoutubeDL
    from yt_dlp.extractor.common import InfoExtractor

    class FixtureIE(InfoExtractor):
        _VALID_URL = r'^fixture:(?P<id>[^:]+)$'

        def _real_extract(self, url):
            return dict(payload)

    ydl = YoutubeDL(params)
    ydl.add_info_extractor(FixtureIE(ydl))
    return ydl


def download(tmp_path, info, params, server):
    """Run one download through `YoutubeDL.extract_info`; return (error, created paths, home)."""
    home = tmp_path / 'home'
    home.mkdir(exist_ok=True)
    info = dict(info)
    info.setdefault('id', 'v1')
    info.setdefault('title', 'clip')
    info.setdefault('ext', 'mp4')
    info.setdefault('webpage_url', 'https://example.invalid/watch?v=1')
    formats = info.get('formats')
    if formats is None:
        formats = [{
            'format_id': '0', 'url': server.url('media.mp4'),
            'ext': info.get('ext', 'mp4'), 'vcodec': 'h264', 'acodec': 'aac',
        }]
        info['formats'] = formats
    for fmt in formats:
        fmt.setdefault('url', server.url('media.mp4'))
        fmt.setdefault('vcodec', 'h264')
        fmt.setdefault('acodec', 'aac')
    p = {'quiet': True, 'no_warnings': True, 'noprogress': True}
    p.update(params)
    p.setdefault('paths', {'home': str(home)})
    try:
        _make_ydl(info, p).extract_info('fixture:v1', download=True, ie_key='Fixture')
        err = None
    except Exception as exc:  # noqa: BLE001 - a refusal is any error the library reports
        err = exc
    created = []
    for base, dirs, files in os.walk(tmp_path):
        for name in dirs:
            created.append(os.path.relpath(os.path.join(base, name), tmp_path) + '/')
        for name in files:
            created.append(os.path.relpath(os.path.join(base, name), tmp_path))
    return err, created, home


def outside(created, home):
    home_rel = os.path.relpath(str(home), os.path.dirname(str(home)))
    return [p for p in created if not (p == home_rel + '/' or p.startswith(home_rel + '/'))]
