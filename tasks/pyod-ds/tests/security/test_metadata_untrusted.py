"""The envelope inspector is documented for callers that only need
metadata, but reading the envelope means reading the whole artifact."""

import os
import tempfile
import unittest

import joblib

from trust_support import MarkerPayload


class TestMetadataReadRefusesUnvouchedArtifact(unittest.TestCase):

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmpdir.cleanup)
        self.dir = self._tmpdir.name

    def test_envelope_inspection_refuses_unvouched_artifact(self):
        from pyod.utils.persistence import inspect_artifact

        marker = os.path.join(self.dir, "meta.marker")
        path = os.path.join(self.dir, "meta.joblib")
        joblib.dump(
            {"_pyod_persistence_version": 1,
             "saved_at": "2026-01-01T00:00:00Z",
             "metadata": {"dataset": "demo"},
             "model": MarkerPayload(marker)},
            path)

        self.assertFalse(os.path.exists(marker))
        with self.assertRaises(Exception):
            inspect_artifact(path)
        self.assertFalse(
            os.path.exists(marker),
            "code stored in the artifact ran while its metadata was read")
