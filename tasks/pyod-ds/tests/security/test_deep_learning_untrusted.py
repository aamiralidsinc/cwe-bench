"""The deep-learning detectors' own save/read pair reads a file the
caller names, and it has never asked anything about the source."""

import os
import pickle
import tempfile
import unittest

from trust_support import MarkerPayload


class TestDeepLearningLoadRefusesUnvouchedArtifact(unittest.TestCase):

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmpdir.cleanup)
        self.dir = self._tmpdir.name

    def test_detector_read_refuses_unvouched_file(self):
        from pyod.models.auto_encoder import AutoEncoder

        marker = os.path.join(self.dir, "dl.marker")
        path = os.path.join(self.dir, "dl.pkl")
        with open(path, "wb") as handle:
            pickle.dump(MarkerPayload(marker), handle)

        self.assertFalse(os.path.exists(marker))
        with self.assertRaises(Exception):
            AutoEncoder.load(path)
        self.assertFalse(
            os.path.exists(marker),
            "code stored in the file ran while the detector was read")
