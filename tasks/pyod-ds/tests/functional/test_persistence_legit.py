"""A caller that vouches for the artifact source keeps every reading
behaviour the library offers today."""

import copy
import os
import tempfile
import unittest
import warnings

import joblib
import numpy as np
from numpy.testing import assert_allclose
from sklearn.ensemble import IsolationForest
from sklearn.tree._tree import Tree as _SkTree

from trust_support import vouched


# ---------------------------------------------------------------------
# An artifact whose stored tree layout no longer matches the running
# sklearn: reading it raises the documented dtype error and the
# library's repair path must recover it.
# ---------------------------------------------------------------------

def _current_node_dtype():
    from sklearn.tree import _tree
    return _tree.NODE_DTYPE


def _strip_field(nodes, field):
    names = [n for n in nodes.dtype.names if n != field]
    dtype = np.dtype([(n, nodes.dtype.fields[n][0]) for n in names])
    out = np.zeros(len(nodes), dtype=dtype)
    for name in names:
        out[name] = nodes[name]
    return out


def _build_tree(n_features, n_classes, n_outputs):
    return _SkTree(n_features, n_classes, n_outputs)


class _AgedTree:
    """Replaces a fitted tree so that unpickling feeds an older node
    layout to ``Tree.__setstate__``."""

    def __init__(self, real_tree, field):
        self._args = (real_tree.n_features, real_tree.n_classes,
                      real_tree.n_outputs)
        state = dict(real_tree.__getstate__())
        state["nodes"] = _strip_field(state["nodes"], field)
        self._state = state

    def __reduce__(self):
        return (_build_tree, self._args, self._state)


def _aged(detector, field="missing_go_to_left"):
    aged = copy.deepcopy(detector)
    for est in aged.estimators_:
        est.tree_ = _AgedTree(est.tree_, field)
    return aged


def _fit_forest(n_estimators=1, seed=0):
    rng = np.random.RandomState(seed)
    X = rng.randn(64, 4)
    clf = IsolationForest(n_estimators=n_estimators, random_state=seed)
    clf.fit(X)
    return clf, X


class TestVouchedReadsKeepWorking(unittest.TestCase):

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmpdir.cleanup)
        self.dir = self._tmpdir.name

    def _p(self, name):
        return os.path.join(self.dir, name)

    def test_save_and_read_round_trip(self):
        from pyod.utils.persistence import load, save

        clf, X = _fit_forest(n_estimators=2)
        path = self._p("roundtrip.joblib")
        save(clf, path, metadata={"dataset": "demo"})

        out = vouched(load, path)
        self.assertIsInstance(out, IsolationForest)
        assert_allclose(out.decision_function(X), clf.decision_function(X))

    def test_envelope_metadata_round_trip(self):
        from pyod.utils.persistence import load, save

        clf, _ = _fit_forest()
        path = self._p("withmeta.joblib")
        save(clf, path, metadata={"run": "abc", "n": 3})

        out, envelope = vouched(load, path, return_metadata=True)
        self.assertIsInstance(out, IsolationForest)
        self.assertNotIn("model", envelope)
        self.assertEqual(envelope["metadata"], {"run": "abc", "n": 3})
        self.assertEqual(envelope["_pyod_persistence_version"], 1)

    def test_raw_legacy_artifact_still_reads(self):
        from pyod.utils.persistence import load

        clf, X = _fit_forest(n_estimators=2)
        path = self._p("legacy.joblib")
        joblib.dump(clf, path)

        out = vouched(load, path)
        self.assertIsInstance(out, IsolationForest)
        assert_allclose(out.decision_function(X), clf.decision_function(X))

    def test_older_tree_layout_is_repaired_through_the_loader(self):
        from pyod.utils.persistence import load

        clf, X = _fit_forest(n_estimators=2)
        path = self._p("aged.joblib")
        joblib.dump(_aged(clf), path)

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            out = vouched(load, path)
        self.assertIsInstance(out, IsolationForest)
        for est in out.estimators_:
            self.assertEqual(
                est.tree_.__getstate__()["nodes"].dtype,
                _current_node_dtype())
        assert_allclose(out.decision_function(X), clf.decision_function(X))
        self.assertTrue(any("recover" in str(w.message).lower()
                            for w in caught))

    def test_compat_reader_repairs_older_tree_layout(self):
        from pyod.utils.persistence import compat_load

        clf, X = _fit_forest(n_estimators=2)
        path = self._p("aged_compat.joblib")
        joblib.dump(_aged(clf), path)

        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            out = vouched(compat_load, path)
        self.assertIsInstance(out, IsolationForest)
        assert_allclose(out.decision_function(X), clf.decision_function(X))

    def test_compat_reader_passes_non_tree_artifact_through(self):
        import pyod.utils.persistence as persistence

        payload = {"kind": "plain", "values": [1, 2, 3]}
        path = self._p("plain.joblib")
        joblib.dump(payload, path)
        out = vouched(persistence.compat_load, path)
        self.assertEqual(out, payload)

    def test_open_file_and_path_inputs_are_accepted(self):
        from pathlib import Path

        from pyod.utils.persistence import load, save

        clf, _ = _fit_forest()
        path = self._p("inputs.joblib")
        save(clf, path)

        self.assertIsInstance(vouched(load, Path(path)), IsolationForest)
        with open(path, "rb") as handle:
            self.assertIsInstance(vouched(load, handle), IsolationForest)
