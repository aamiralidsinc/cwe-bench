"""Base weight store: indirect values and links must not reach outside."""

import os

import h5py

import _support as support


def test_virtual_dataset_in_weights_file(tmp_path):
    path = support.save_weights_artifact(tmp_path)
    source = support.make_source_h5(tmp_path)
    support.replace_with_virtual(path, "layers/dense/vars/0", source)

    error, values = support.load_weights_attempt(path)
    assert error is not None
    assert not support.holds_marker(values)


def test_virtual_dataset_through_model_method(tmp_path):
    path = support.save_weights_artifact(tmp_path)
    source = support.make_source_h5(tmp_path)
    support.replace_with_virtual(path, "layers/dense/vars/0", source)

    error, values = support.model_method_attempt(path)
    assert error is not None
    assert not support.holds_marker(values)


def test_virtual_dataset_in_unzipped_model(tmp_path):
    directory = support.save_keras_directory(tmp_path)
    weights = str(tmp_path / "model_dir" / "model.weights.h5")
    source = support.make_source_h5(tmp_path)
    support.replace_with_virtual(weights, "layers/dense/vars/0", source)

    error, values = support.load_model_attempt(directory)
    assert error is not None
    assert not support.holds_marker(values)


def test_external_link_at_layer_group(tmp_path):
    path = support.save_weights_artifact(tmp_path)
    target = support.make_external_weights(tmp_path)
    support.replace_with_external_link(
        path, "layers/dense", target, "layers/dense"
    )

    error, values = support.load_weights_attempt(path)
    assert error is not None
    assert not support.holds_marker(values)


def test_soft_link_at_dataset(tmp_path):
    path = support.save_weights_artifact(tmp_path)
    support.add_hidden_dataset(path, "hidden/kernel")
    support.replace_with_soft_link(path, "layers/dense/vars/0", "/hidden/kernel")

    error, values = support.load_weights_attempt(path)
    assert error is not None
    assert not support.holds_marker(values)


def test_soft_link_in_zipped_model(tmp_path):
    archive = support.save_keras_archive(tmp_path)
    weights = support.extract_keras_archive(archive, str(tmp_path))
    support.add_hidden_dataset(weights, "hidden/kernel")
    support.replace_with_soft_link(weights, "layers/dense/vars/0", "/hidden/kernel")
    support.rezip_keras_archive(archive, str(tmp_path))

    error, values = support.load_model_attempt(archive)
    assert error is not None
    assert not support.holds_marker(values)


def test_top_level_container_external_link(tmp_path):
    path = os.path.join(tmp_path, "own.weights.h5")
    support.make_owned_model().save_weights(path)
    target = os.path.join(tmp_path, "top-target.h5")
    with h5py.File(target, "w") as handle:
        handle.create_dataset("vars/0", data=support.KERNEL)
    with h5py.File(path, "r+") as handle:
        del handle["vars"]
        handle["vars"] = h5py.ExternalLink(target, "vars")

    error, values = support.owned_weights_attempt(path)
    assert error is not None
    assert not support.holds_marker(values)


def test_soft_link_in_older_layout_group(tmp_path):
    path = support.save_weights_artifact(tmp_path)
    with h5py.File(path, "r+") as handle:
        handle.copy("layers/dense", "hidden/dense")
        handle["hidden/dense/vars/0"][...] = support.KERNEL
        del handle["layers/dense"]
        handle["_layer_checkpoint_dependencies/dense"] = h5py.SoftLink(
            "/hidden/dense"
        )

    error, values = support.load_weights_attempt(path)
    assert error is not None
    assert not support.holds_marker(values)
