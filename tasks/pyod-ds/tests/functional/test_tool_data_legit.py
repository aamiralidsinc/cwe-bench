"""The agent-facing tool server keeps loading the data files it
supports, including the pickled ones, for a caller that vouches."""

import json
import os
import pickle
import tempfile
import unittest

import numpy as np

from trust_support import vouched


class TestToolDataPathsKeepWorking(unittest.TestCase):

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmpdir.cleanup)
        self.dir = self._tmpdir.name
        self.result = json.dumps(
            {"scores_train": [0.1, 0.2, 0.3, 0.4],
             "labels_train": [0, 1, 0, 1]})

    def _assert_loaded(self, path):
        from pyod.mcp_server import explain_findings

        out = vouched(explain_findings, result=self.result,
                      data_path=path, top_k=1)
        self.assertIsInstance(out, str)
        self.assertNotIn("Failed to load data", out)

    def test_npy_data_path(self):
        path = os.path.join(self.dir, "data.npy")
        np.save(path, np.arange(8, dtype=float).reshape(4, 2))
        self._assert_loaded(path)

    def test_csv_data_path(self):
        path = os.path.join(self.dir, "data.csv")
        with open(path, "w") as handle:
            handle.write("a,b,label\n")
            handle.write("0.0,1.0,0\n1.0,0.0,1\n2.0,3.0,0\n3.0,2.0,1\n")
        self._assert_loaded(path)

    def test_json_data_path(self):
        path = os.path.join(self.dir, "data.json")
        with open(path, "w") as handle:
            json.dump([[0.0, 1.0], [1.0, 0.0], [2.0, 3.0], [3.0, 2.0]], handle)
        self._assert_loaded(path)

    def test_pickled_data_path_when_vouched(self):
        path = os.path.join(self.dir, "data.pkl")
        with open(path, "wb") as handle:
            pickle.dump(np.arange(8, dtype=float).reshape(4, 2), handle)
        self._assert_loaded(path)
