"""The agent-facing tool server takes a data-file path from its
client; the file the client names must not run code either."""

import json
import os
import pickle
import tempfile
import unittest

from trust_support import MarkerPayload


class TestToolDataPathRefusesUnvouchedArtifact(unittest.TestCase):

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmpdir.cleanup)
        self.dir = self._tmpdir.name

    def test_tool_data_path_refuses_unvouched_pickle(self):
        from pyod.mcp_server import explain_findings

        marker = os.path.join(self.dir, "tool.marker")
        path = os.path.join(self.dir, "data.pkl")
        with open(path, "wb") as handle:
            pickle.dump(MarkerPayload(marker), handle)

        result = json.dumps({"scores_train": [0.1, 0.2],
                             "labels_train": [0, 1]})
        out = explain_findings(result=result, data_path=path, top_k=1)
        self.assertIsInstance(out, str)
        self.assertFalse(
            os.path.exists(marker),
            "code stored in the client-supplied file ran while it was read")
