"""The deep-learning detectors' own save/read pair keeps working for a
caller that vouches for the file."""

import os
import tempfile
import unittest

from trust_support import vouched


class TestDeepLearningRoundTrip(unittest.TestCase):

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmpdir.cleanup)
        self.dir = self._tmpdir.name

    def test_save_and_read_round_trip(self):
        from pyod.models.auto_encoder import AutoEncoder

        clf = AutoEncoder(contamination=0.05, epoch_num=3, verbose=0)
        path = os.path.join(self.dir, "detector.pkl")
        clf.save(path)
        self.assertTrue(os.path.exists(path))

        out = vouched(AutoEncoder.load, path)
        self.assertIsInstance(out, AutoEncoder)
        self.assertEqual(out.epoch_num, 3)
        self.assertAlmostEqual(out.contamination, 0.05)
