"""Reading only an artifact's envelope keeps returning the recorded
versions and the user metadata."""

import os
import tempfile
import unittest

from sklearn.ensemble import IsolationForest

from trust_support import vouched


class TestMetadataReadKeepsWorking(unittest.TestCase):

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmpdir.cleanup)
        self.dir = self._tmpdir.name

    def test_envelope_is_returned_without_the_model(self):
        from pyod.utils.persistence import inspect_artifact, save

        clf = IsolationForest(n_estimators=1, random_state=0)
        path = os.path.join(self.dir, "meta.joblib")
        save(clf, path, metadata={"dataset": "demo", "fold": 2})

        envelope = vouched(inspect_artifact, path)
        self.assertIsInstance(envelope, dict)
        self.assertNotIn("model", envelope)
        self.assertEqual(envelope["metadata"], {"dataset": "demo", "fold": 2})
        self.assertEqual(envelope["_pyod_persistence_version"], 1)
        self.assertIn("sklearn_version", envelope)

    def test_artifact_without_envelope_is_still_rejected(self):
        import joblib
        from pyod.utils.persistence import inspect_artifact

        path = os.path.join(self.dir, "plain.joblib")
        joblib.dump({"not": "an envelope"}, path)
        with self.assertRaises(ValueError):
            vouched(inspect_artifact, path)
