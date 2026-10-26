"""Drive a real notebook server through its HTTP entry point."""

import http.client

import requests
from tornado.httputil import url_concat

from notebook.tests.launchnotebook import NotebookTestBase


class NotebookServer(NotebookTestBase):
    """A notebook server for one hidden test class.

    Subclasses set ``port`` and, when needed, ``url_prefix`` and ``config``.
    """


def login(server, next_value):
    """Post the login form with a destination and return the response."""
    first = requests.get(server.base_url() + "login", timeout=30)
    first.raise_for_status()
    return requests.post(
        url_concat(server.base_url() + "login", {"next": next_value}),
        allow_redirects=False,
        data={
            "password": server.token,
            "_xsrf": first.cookies.get("_xsrf", ""),
        },
        cookies=first.cookies,
        timeout=30,
    )


def raw_get(server, target):
    """Send the request target verbatim, as a browser would send it."""
    connection = http.client.HTTPConnection("localhost", server.port, timeout=30)
    try:
        connection.putrequest("GET", target)
        connection.endheaders()
        response = connection.getresponse()
        response.read()
        return response.status, response.getheader("Location")
    finally:
        connection.close()
