"""In-process stand-in for the ``requests`` module used by the add-on.

Tests register the responses the add-on should see.  Nothing reaches the network.
"""


class FakeHTTPError(Exception):
    pass


class FakeExceptions:
    class Timeout(Exception):
        pass


class _Utils:
    @staticmethod
    def default_headers():
        return {"User-Agent": "test"}


class FakeResponse:
    def __init__(self, status_code=200, content=b"", json_data=None, headers=None):
        self.status_code = status_code
        self.content = content
        self._json = json_data
        self.headers = headers or {}

    def json(self):
        if self._json is None:
            raise ValueError("no JSON body")
        return self._json

    def raise_for_status(self):
        if self.status_code >= 400:
            raise FakeHTTPError("HTTP %s" % self.status_code)

    def iter_content(self, chunk_size=8192):
        for i in range(0, len(self.content), chunk_size):
            yield self.content[i:i + chunk_size]


class FakeRequests:
    """Routes requests by exact URL (or by a callable predicate)."""

    exceptions = FakeExceptions
    utils = _Utils

    def __init__(self):
        self.routes = []
        self.seen = []

    def add(self, matcher, response):
        self.routes.append((matcher, response))

    def _dispatch(self, method, url, kwargs):
        self.seen.append((method, url))
        for matcher, response in self.routes:
            if callable(matcher):
                if matcher(url):
                    return response
            elif matcher == url:
                return response
        raise AssertionError("unexpected %s %s" % (method, url))

    def get(self, url, **kwargs):
        return self._dispatch("GET", url, kwargs)

    def post(self, url, **kwargs):
        return self._dispatch("POST", url, kwargs)
