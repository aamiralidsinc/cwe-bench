"""Older single-file model format: every weight read must be confined."""

import os

import h5py
import numpy as np

import _support as support


def _mark_external_legacy(directory):
    """A complete older-format model whose weights carry the marker."""
    path = os.path.join(directory, "external-legacy.h5")
    support.make_model().save(path)
    with h5py.File(path, "r+") as handle:
        group = handle["model_weights"]
        parent, name = support.find_named_dataset(group, "kernel")
        parent[name][...] = support.KERNEL
        parent, name = support.find_named_dataset(group, "bias")
        parent[name][...] = support.BIAS
    return path


def _kernel_path(handle):
    parent, name = support.find_named_dataset(handle["model_weights"], "kernel")
    return parent[name].name.lstrip("/")


def test_legacy_external_storage_on_model_load(tmp_path):
    path = support.save_legacy_model(tmp_path)
    secret = support.write_secret_file(tmp_path)
    with h5py.File(path, "r+") as handle:
        dataset_path = _kernel_path(handle)
    support.replace_with_external(path, dataset_path, secret)

    error, values = support.load_model_attempt(path)
    assert error is not None
    assert not support.holds_marker(values)


def test_legacy_external_storage_on_weight_load(tmp_path):
    path = support.save_legacy_model(tmp_path)
    secret = support.write_secret_file(tmp_path)
    with h5py.File(path, "r+") as handle:
        dataset_path = _kernel_path(handle)
    support.replace_with_external(path, dataset_path, secret)

    error, values = support.load_weights_attempt(path)
    assert error is not None
    assert not support.holds_marker(values)


def test_legacy_virtual_dataset_on_model_load(tmp_path):
    path = support.save_legacy_model(tmp_path)
    source = support.make_source_h5(tmp_path)
    support.replace_with_virtual(path, _relative_kernel_path(path), source)

    error, values = support.load_model_attempt(path)
    assert error is not None
    assert not support.holds_marker(values)


def _relative_kernel_path(path):
    with h5py.File(path, "r") as handle:
        return _kernel_path(handle)


def test_legacy_by_name_external_link(tmp_path):
    path = support.save_legacy_model(tmp_path)
    target = _mark_external_legacy(tmp_path)
    with h5py.File(target, "r") as handle:
        target_dataset = _kernel_path(handle)
    with h5py.File(path, "r+") as handle:
        dataset_path = _kernel_path(handle)
    support.replace_with_external_link(
        path, dataset_path, target, target_dataset
    )

    error, values = support.load_weights_attempt(path, by_name=True)
    assert error is not None
    assert not support.holds_marker(values)


def test_optimizer_state_external_link(tmp_path):
    path = support.save_compiled_legacy_model(tmp_path)
    target = os.path.join(tmp_path, "optimizer-target.h5")
    with h5py.File(target, "w") as handle:
        handle.create_dataset(
            "marker", data=np.float32(support.KERNEL.ravel()[0])
        )
    with h5py.File(path, "r+") as handle:
        group = handle["optimizer_weights"]
        names = [
            name.decode() if isinstance(name, bytes) else name
            for name in group.attrs["weight_names"]
        ]
        name = next(n for n in names if n.endswith("learning_rate"))
        parent_path, _, leaf = name.rpartition("/")
        holder = group[parent_path] if parent_path else group
        del holder[leaf]
        holder[leaf] = h5py.ExternalLink(target, "marker")

    error, values = support.compiled_model_attempt(path)
    assert error is not None
    assert not support.holds_marker(list(values.values()))


def test_model_weights_group_external_link(tmp_path):
    path = support.save_legacy_model(tmp_path)
    target = _mark_external_legacy(tmp_path)
    with h5py.File(path, "r+") as handle:
        del handle["model_weights"]
        handle["model_weights"] = h5py.ExternalLink(target, "model_weights")

    error, values = support.load_weights_attempt(path)
    assert error is not None
    assert not support.holds_marker(values)
