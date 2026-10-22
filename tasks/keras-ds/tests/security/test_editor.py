"""The weights-file inspection utility must be confined like the loaders."""

import h5py

import _support as support


def test_editor_virtual_dataset(tmp_path):
    path = support.save_weights_artifact(tmp_path)
    source = support.make_source_h5(tmp_path)
    support.replace_with_virtual(path, "layers/dense/vars/0", source)

    error, data = support.editor_attempt(path)
    assert error is not None
    assert not support.holds_marker(data)


def test_editor_soft_link(tmp_path):
    path = support.save_weights_artifact(tmp_path)
    support.add_hidden_dataset(path, "hidden/kernel")
    support.replace_with_soft_link(path, "layers/dense/vars/0", "/hidden/kernel")

    error, data = support.editor_attempt(path)
    assert error is not None
    assert not support.holds_marker(data)


def test_editor_vars_container_external_link(tmp_path):
    path = support.save_weights_artifact(tmp_path)
    target = support.make_external_weights(tmp_path)
    with h5py.File(path, "r+") as handle:
        del handle["layers/dense/vars"]
        handle["layers/dense/vars"] = h5py.ExternalLink(
            target, "layers/dense/vars"
        )

    error, data = support.editor_attempt(path)
    assert error is not None
    assert not support.holds_marker(data)


def test_editor_external_link(tmp_path):
    path = support.save_weights_artifact(tmp_path)
    target = support.make_external_weights(tmp_path)
    with h5py.File(target, "r") as handle:
        target_dataset = handle["layers/dense/vars/0"].name
    support.replace_with_external_link(
        path, "layers/dense/vars/0", target, target_dataset
    )

    error, data = support.editor_attempt(path)
    assert error is not None
    assert not support.holds_marker(data)
