"""The compatibility reader is a second public way into the same
artifact, and it accepts an older on-disk shape as well."""

import os
import pickle
import tempfile
import unittest
import zlib

import joblib

from trust_support import MarkerPayload

# Width of the length field in the pre-0.10 z-file container: the
# reader takes a fixed-width hexadecimal length after a two byte tag.
_ZFILE_LENGTH_WIDTH = len(hex(2 ** 64))


def _write_legacy_container(path, obj):
    """Write ``obj`` in the pre-0.10 joblib container format."""
    payload = pickle.dumps(obj, protocol=2)
    with open(path, "wb") as handle:
        handle.write(b"ZF")
        handle.write(hex(len(payload))[2:].encode()
                     .ljust(_ZFILE_LENGTH_WIDTH))
        handle.write(zlib.compress(payload))


class TestCompatLoadRefusesUnvouchedArtifact(unittest.TestCase):

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmpdir.cleanup)
        self.dir = self._tmpdir.name

    def _marker(self, name):
        return os.path.join(self.dir, name + ".marker")

    def _assert_refused(self, marker, read):
        self.assertFalse(os.path.exists(marker),
                         "the fixture must not have run before the read")
        with self.assertRaises(Exception):
            read()
        self.assertFalse(
            os.path.exists(marker),
            "code stored in the artifact ran while the file was read")

    def test_envelope_artifact(self):
        from pyod.utils.persistence import compat_load

        marker = self._marker("compat-envelope")
        path = os.path.join(self.dir, "compat-envelope.joblib")
        joblib.dump(
            {"_pyod_persistence_version": 1, "model": MarkerPayload(marker)},
            path)
        self._assert_refused(marker, lambda: compat_load(path))

    def test_older_serialization_shape(self):
        # An artifact in the pre-0.10 container format: the reader
        # hands it to a different loader than the one it configures
        # itself, so a guard attached to that configuration is not
        # reached.
        from pyod.utils.persistence import compat_load

        marker = self._marker("compat-legacy")
        path = os.path.join(self.dir, "compat-legacy.pkl")
        _write_legacy_container(path, MarkerPayload(marker))
        self._assert_refused(marker, lambda: compat_load(path))
