#!/usr/bin/env python3
"""Stand-in for the Stata command-line executable.

The product starts this program instead of Stata.  It records every byte it
receives (env STATA_MCP_TEST_CAPTURE) and then behaves like a session that
succeeded, so a suite can see exactly what the product sent to Stata.
"""
import os
import sys

CAPTURE = os.environ.get("STATA_MCP_TEST_CAPTURE", "")
BANNER = b"\r\nInstalling into /fake/ado\r\ninstallation complete\r\n. "
CHUNK = "@@STATA_CHUNK:"
END = "@@STATA_END@@"


def record(kind, data):
    if not CAPTURE:
        return
    with open(CAPTURE, "ab") as handle:
        handle.write((CHUNK + kind + "@@\n").encode("utf-8"))
        handle.write(data)
        handle.write(("\n" + END + "\n").encode("utf-8"))


def main():
    if not os.isatty(0):
        record("pipe", sys.stdin.buffer.read())
        sys.stdout.write("fake-stata: done\n")
        return 0
    try:
        os.write(1, b"\r\n. ")
    except OSError:
        return 0
    while True:
        try:
            chunk = os.read(0, 65536)
        except OSError:
            break
        if not chunk:
            break
        record("tty", chunk)
        try:
            os.write(1, BANNER)
        except OSError:
            break
        if b"exit, clear" in chunk.lower():
            break
    return 0


if __name__ == "__main__":
    sys.exit(main())
