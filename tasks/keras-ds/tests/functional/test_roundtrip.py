"""Ordinary artifacts must keep loading and round-tripping exactly as today."""

import os
import zipfile

import h5py
import numpy as np

import keras

import _support as support


def _reference_values(model):
    return support.model_values(model)


def _assert_same_as(model, reference):
    actual = support.model_values(model)
    expected = _reference_values(reference)
    assert len(actual) == len(expected)
    for got, want in zip(actual, expected):
        assert np.allclose(got, want)


def test_weights_file_roundtrip(tmp_path):
    reference = support.make_model()
    path = os.path.join(tmp_path, "model.weights.h5")
    reference.save_weights(path)

    model = support.make_model()
    model.load_weights(path)
    _assert_same_as(model, reference)


def test_keras_archive_roundtrip(tmp_path):
    reference = support.make_model()
    path = os.path.join(tmp_path, "model.keras")
    reference.save(path)

    loaded = keras.saving.load_model(path)
    _assert_same_as(loaded, reference)


def test_keras_directory_roundtrip(tmp_path):
    reference = support.make_model()
    archive = os.path.join(tmp_path, "model.keras")
    reference.save(archive)
    directory = os.path.join(tmp_path, "unzipped")
    os.makedirs(directory)
    with zipfile.ZipFile(archive) as handle:
        handle.extractall(directory)

    loaded = keras.saving.load_model(directory)
    _assert_same_as(loaded, reference)


def test_older_layout_roundtrip(tmp_path):
    reference = support.make_model()
    path = os.path.join(tmp_path, "model.weights.h5")
    reference.save_weights(path)
    with h5py.File(path, "r+") as handle:
        handle.copy("layers/dense", "_layer_checkpoint_dependencies/dense")
        del handle["layers/dense"]

    model = support.make_model()
    model.load_weights(path)
    _assert_same_as(model, reference)


def test_sharded_roundtrip(tmp_path):
    reference = support.make_model()
    path = os.path.join(tmp_path, "model.weights.json")
    reference.save_weights(path, max_shard_size=28 / 1024**3)
    assert len(support.shard_files(tmp_path)) == 2

    model = support.make_model()
    model.load_weights(path)
    _assert_same_as(model, reference)


def test_legacy_model_roundtrip(tmp_path):
    reference = support.make_model()
    path = os.path.join(tmp_path, "model.h5")
    reference.save(path)

    loaded = keras.saving.load_model(path)
    _assert_same_as(loaded, reference)


def test_legacy_weight_load_roundtrip(tmp_path):
    reference = support.make_model()
    path = os.path.join(tmp_path, "model.h5")
    reference.save(path)

    model = support.make_model()
    model.load_weights(path)
    _assert_same_as(model, reference)

    model = support.make_model()
    model.load_weights(path, by_name=True)
    _assert_same_as(model, reference)


def test_editor_roundtrip(tmp_path):
    reference = support.make_model()
    path = os.path.join(tmp_path, "model.weights.h5")
    reference.save_weights(path)

    editor = keras.saving.KerasFileEditor(path)
    resaved = os.path.join(tmp_path, "resaved.weights.h5")
    editor.resave_weights(resaved)

    model = support.make_model()
    model.load_weights(resaved)
    _assert_same_as(model, reference)


def test_editor_opens_model_archive(tmp_path):
    reference = support.make_model()
    path = os.path.join(tmp_path, "model.keras")
    reference.save(path)

    editor = keras.saving.KerasFileEditor(path)
    resaved = os.path.join(tmp_path, "resaved.weights.h5")
    editor.resave_weights(resaved)

    model = support.make_model()
    model.load_weights(resaved)
    _assert_same_as(model, reference)


def test_top_level_variable_roundtrip(tmp_path):
    reference = support.make_owned_model()
    reference.w.assign(np.linspace(0.5, 6.0, num=6).reshape(3, 2))
    path = os.path.join(tmp_path, "owned.weights.h5")
    reference.save_weights(path)

    model = support.make_owned_model()
    model.load_weights(path)
    _assert_same_as(model, reference)


def test_legacy_optimizer_state_roundtrip(tmp_path):
    path = support.save_compiled_legacy_model(
        tmp_path, learning_rate=0.125, iteration=7
    )

    error, values = support.compiled_model_attempt(path)
    assert error is None
    assert int(np.asarray(values["iteration"])) == 7
    assert np.allclose(np.float32(values["learning_rate"]), np.float32(0.125))


def test_editor_two_layer_roundtrip(tmp_path):
    def build():
        model = keras.Sequential(
            [
                keras.layers.Input((3,)),
                keras.layers.Dense(4, name="first"),
                keras.layers.Dense(2, name="second"),
            ]
        )
        model(np.zeros((1, 3), dtype="float32"))
        return model

    reference = build()
    path = os.path.join(tmp_path, "two.weights.h5")
    reference.save_weights(path)

    editor = keras.saving.KerasFileEditor(path)
    assert editor.weights_dict
    resaved = os.path.join(tmp_path, "resaved.weights.h5")
    editor.resave_weights(resaved)

    model = build()
    model.load_weights(resaved)
    _assert_same_as(model, reference)


def test_declared_external_value_stays_refused(tmp_path):
    path = support.save_weights_artifact(tmp_path)
    secret = support.write_secret_file(tmp_path)
    support.replace_with_external(path, "layers/dense/vars/0", secret)

    error, values = support.load_weights_attempt(path)
    assert error is not None
    assert not support.holds_marker(values)


def test_declared_external_value_stays_refused_in_editor(tmp_path):
    path = support.save_weights_artifact(tmp_path)
    secret = support.write_secret_file(tmp_path)
    support.replace_with_external(path, "layers/dense/vars/0", secret)

    error, data = support.editor_attempt(path)
    assert error is not None
    assert not support.holds_marker(data)


def test_reduced_precision_roundtrip(tmp_path):
    reference = keras.Sequential(
        [
            keras.layers.Input((3,)),
            keras.layers.Dense(2, name="dense", dtype="bfloat16"),
        ]
    )
    reference(np.zeros((1, 3), dtype="float32"))
    path = os.path.join(tmp_path, "bf16.weights.h5")
    reference.save_weights(path)

    model = keras.Sequential(
        [
            keras.layers.Input((3,)),
            keras.layers.Dense(2, name="dense", dtype="bfloat16"),
        ]
    )
    model(np.zeros((1, 3), dtype="float32"))
    model.load_weights(path)
    _assert_same_as(model, reference)
