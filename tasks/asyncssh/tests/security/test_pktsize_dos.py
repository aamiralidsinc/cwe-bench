"""Security: a peer must not be able to wedge the connection by advertising a
channel maximum packet size of zero.

When a channel is opened, each side tells the other the largest packet it is
willing to receive. If an endpoint accepts a peer-advertised maximum of zero
and later has to send channel data, it tries to split that data into
zero-length pieces and never makes progress -- a single crafted channel open
hangs the endpoint (denial of service).

Because a vulnerable endpoint hangs in a tight synchronous loop (it does not
merely block on I/O), it cannot be detected from within the same event loop.
These tests run each scenario in a SUBPROCESS and enforce a wall-clock timeout:
a correct endpoint rejects the zero packet size during channel open and the
subprocess exits promptly; a vulnerable endpoint hangs until the timeout and is
killed, which fails the test.
"""
import os
import subprocess
import sys

import pytest

SCENARIO = os.path.join(os.path.dirname(__file__), "_pktsize_scenario.py")
HARD_TIMEOUT = 30.0


def _run_scenario(tmp_path, mode):
    proc = subprocess.Popen(
        [sys.executable, SCENARIO, str(tmp_path), mode],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        out, err = proc.communicate(timeout=HARD_TIMEOUT)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.communicate()
        pytest.fail(
            "endpoint hung on a channel whose peer advertised packet size 0 "
            "(denial of service): it did not reject the zero size [%s]" % mode)

    assert proc.returncode == 0, (
        "zero packet-size channel was not rejected cleanly [%s] "
        "(rc=%s, stdout=%r, stderr=%r)" % (mode, proc.returncode, out, err[-400:]))
    assert "blocked" in out, (
        "expected a prompt protocol-level rejection [%s]; got stdout=%r" % (mode, out))


def test_channel_zero_pktsize_dos(tmp_path):
    # The client opens a channel advertising 0; the server must reject it.
    _run_scenario(tmp_path, "open")


def test_channel_zero_pktsize_dos_dropbear_compression(tmp_path):
    # Same zero advertisement, from a peer whose software version names
    # dropbear, with compression negotiated (the library's default list).
    _run_scenario(tmp_path, "open-dropbear")


def test_channel_zero_pktsize_in_open_confirmation(tmp_path):
    # The other direction: the server accepts the client's channel and its
    # confirmation advertises 0; the client must reject it, not hang sending.
    _run_scenario(tmp_path, "confirm")


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
