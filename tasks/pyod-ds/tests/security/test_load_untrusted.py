"""Reading a detector with the library's public loader must not run
code stored in the file before the caller vouches for its source."""

import os
import pickle
import tempfile
import unittest

import joblib

from trust_support import MarkerPayload


class TestLoadRefusesUnvouchedArtifact(unittest.TestCase):

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmpdir.cleanup)
        self.dir = self._tmpdir.name

    # -- artifact builders -------------------------------------------------
    def _marker(self, name):
        return os.path.join(self.dir, name + ".marker")

    def _envelope(self, name, marker, compress=0):
        path = os.path.join(self.dir, name)
        joblib.dump(
            {"_pyod_persistence_version": 1, "model": MarkerPayload(marker)},
            path, compress=compress)
        return path

    def _raw_pickle(self, name, marker):
        path = os.path.join(self.dir, name)
        with open(path, "wb") as handle:
            pickle.dump(MarkerPayload(marker), handle)
        return path

    # -- assertion shared by every case ------------------------------------
    def _assert_refused(self, marker, read):
        self.assertFalse(os.path.exists(marker),
                         "the fixture must not have run before the read")
        with self.assertRaises(Exception):
            read()
        self.assertFalse(
            os.path.exists(marker),
            "code stored in the artifact ran while the file was read")

    # -- cases -------------------------------------------------------------
    def test_envelope_artifact(self):
        from pyod.utils.persistence import load

        marker = self._marker("envelope")
        path = self._envelope("envelope.joblib", marker)
        self._assert_refused(marker, lambda: load(path))

    def test_compressed_artifact(self):
        from pyod.utils.persistence import load

        marker = self._marker("compressed")
        path = self._envelope("compressed.joblib", marker, compress=3)
        self._assert_refused(marker, lambda: load(path))

    def test_raw_pickle_artifact(self):
        from pyod.utils.persistence import load

        marker = self._marker("raw")
        path = self._raw_pickle("raw.pkl", marker)
        self._assert_refused(marker, lambda: load(path))

    def test_open_file_input(self):
        from pyod.utils.persistence import load

        marker = self._marker("openfile")
        path = self._envelope("openfile.joblib", marker)

        def read():
            with open(path, "rb") as handle:
                return load(handle)

        self._assert_refused(marker, read)

    def test_strict_mode_artifact(self):
        from pyod.utils.persistence import load

        marker = self._marker("strict")
        path = self._envelope("strict.joblib", marker)
        self._assert_refused(marker, lambda: load(path, strict=True))
