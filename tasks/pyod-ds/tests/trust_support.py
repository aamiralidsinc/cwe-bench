"""Shared helpers for the hidden suites.

Two things live here:

* ``MarkerPayload`` / ``write_marker`` build an artifact whose reading
  has an observable side effect (a file appears next to the artifact).
  A refused read must leave that file absent.
* ``vouched`` calls a reading surface the way a caller that vouches for
  the artifact source does.  The library asks for an explicit
  acknowledgement of trust; a revision that does not accept the
  keyword yet is called without it, so the same functional scenario
  runs before and after the change.
"""

from pathlib import Path


def write_marker(path, text):
    """Reducer target: create a file at ``path`` holding ``text``."""
    Path(path).write_text(text)


class MarkerPayload:
    """Object whose unpickling creates a marker file."""

    def __init__(self, marker_path):
        self.marker_path = marker_path

    def __reduce__(self):
        return (write_marker, (self.marker_path, "executed"))


def vouched(call, *args, **kwargs):
    """Call a reading surface as a caller that vouches for its source."""
    kwargs["trusted"] = True
    try:
        return call(*args, **kwargs)
    except TypeError as exc:
        if "trusted" not in str(exc):
            raise
    kwargs.pop("trusted", None)
    return call(*args, **kwargs)
