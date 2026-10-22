"""Helpers shared by the hidden tests.

Only public library APIs and the file format are used: the tests build ordinary
artifacts, then rewrite one entry of a copy to point outside the artifact.

The marker is a distinctive float pattern. A test passes when the loader either
raises a client-side error or leaves every model variable clear of the marker.
"""

import json
import os
import zipfile

import h5py
import numpy as np

import keras

KERNEL = np.array(
    [[12345.0, 67890.0], [11111.0, 22222.0], [33333.0, 44444.0]],
    dtype="float32",
)
BIAS = np.array([12345.0, 67890.0], dtype="float32")


def make_model():
    model = keras.Sequential(
        [keras.layers.Input((3,)), keras.layers.Dense(2, name="dense")]
    )
    model(np.zeros((1, 3), dtype="float32"))
    return model


class OwnedModel(keras.Model):
    """A model whose own variable is kept at the artifact's top level."""

    def __init__(self):
        super().__init__()
        self.w = self.add_weight(
            shape=KERNEL.shape, initializer="zeros", name="w"
        )

    def call(self, inputs):
        return keras.ops.matmul(inputs, self.w)


def make_owned_model():
    model = OwnedModel()
    model(np.zeros((1, 3), dtype="float32"))
    return model


def owned_weights_attempt(path):
    """Load weights into a fresh model that owns a top-level variable."""
    model = make_owned_model()
    error = None
    try:
        model.load_weights(path)
    except Exception as exc:
        error = exc
    return error, model_values(model)


def make_compiled_model(learning_rate=0.25):
    """A compiled model whose optimizer state is saved alongside the weights."""
    model = make_model()
    model.compile(
        optimizer=keras.optimizers.SGD(learning_rate=learning_rate),
        loss=keras.losses.MeanSquaredError(),
    )
    model.optimizer.build(model.trainable_variables)
    return model


def save_compiled_legacy_model(directory, learning_rate=0.25, iteration=0):
    """Save a compiled model in the older single-file format."""
    model = make_compiled_model(learning_rate)
    for variable in model.optimizer.variables:
        if variable.path.endswith("iteration"):
            variable.assign(np.asarray(iteration, dtype=variable.dtype))
        elif variable.path.endswith("learning_rate"):
            variable.assign(np.asarray(learning_rate, dtype=variable.dtype))
    path = os.path.join(directory, "compiled.h5")
    model.save(path)
    return path


def optimizer_values(model):
    """Map each optimizer variable's leaf name to its value."""
    optimizer = getattr(model, "optimizer", None)
    if optimizer is None:
        return {}
    return {
        variable.path.rsplit("/", 1)[-1]: np.asarray(variable)
        for variable in optimizer.variables
    }


def compiled_model_attempt(path):
    """Load a compiled model; return (error, optimizer variable values)."""
    error = None
    values = {}
    try:
        model = keras.saving.load_model(path)
    except Exception as exc:
        return exc, values
    return None, optimizer_values(model)


def model_values(model):
    values = []
    for variable in model.weights:
        try:
            values.append(np.array(variable.numpy()))
        except Exception:
            values.append(np.asarray(variable))
    return values


def _array_holds_marker(value):
    try:
        array = np.asarray(value)
    except Exception:
        return False
    if array.size == 0:
        return False
    try:
        return bool(np.isin(array, KERNEL.ravel()).any())
    except Exception:
        return False


def holds_marker(value):
    """True if a model's values or an inspector's data carry the marker."""
    if isinstance(value, dict):
        return any(holds_marker(item) for item in value.values())
    if isinstance(value, (list, tuple)):
        return any(holds_marker(item) for item in value)
    if value is None:
        return False
    return _array_holds_marker(value)


def load_weights_attempt(path, **kwargs):
    """Load weights into a fresh model; return (error, model values)."""
    model = make_model()
    error = None
    try:
        keras.saving.load_weights(model, path, **kwargs)
    except Exception as exc:  # any client-side error is a valid refusal
        error = exc
    return error, model_values(model)


def load_model_attempt(path):
    """Load a saved model; return (error, model values or None)."""
    error = None
    model = None
    try:
        model = keras.saving.load_model(path)
    except Exception as exc:  # any client-side error is a valid refusal
        error = exc
    return error, (model_values(model) if model is not None else None)


def model_method_attempt(path):
    model = make_model()
    error = None
    try:
        model.load_weights(path)
    except Exception as exc:
        error = exc
    return error, model_values(model)


def editor_attempt(path):
    error = None
    data = None
    try:
        editor = keras.saving.KerasFileEditor(path)
        data = editor.weights_dict
    except Exception as exc:
        error = exc
    return error, data


# ---------------------------------------------------------------------------
# Ordinary artifacts
# ---------------------------------------------------------------------------


def save_weights_artifact(directory):
    path = os.path.join(directory, "model.weights.h5")
    make_model().save_weights(path)
    return path


def save_keras_archive(directory):
    path = os.path.join(directory, "model.keras")
    make_model().save(path)
    return path


def save_keras_directory(directory):
    """The unzipped form of a model archive."""
    archive = save_keras_archive(directory)
    target = os.path.join(directory, "model_dir")
    os.makedirs(target, exist_ok=True)
    with zipfile.ZipFile(archive) as handle:
        handle.extractall(target)
    return target


def save_legacy_model(directory):
    path = os.path.join(directory, "model.h5")
    make_model().save(path)
    return path


def save_sharded_weights(directory):
    """A two-shard set where the dense layer's values span both shards."""
    path = os.path.join(directory, "model.weights.json")
    make_model().save_weights(path, max_shard_size=28 / 1024**3)
    return path


def shard_files(directory):
    return sorted(
        os.path.join(directory, name)
        for name in os.listdir(directory)
        if name.startswith("model_") and name.endswith(".weights.h5")
    )


def rezip_keras_archive(archive, working_dir):
    with zipfile.ZipFile(archive, "w") as handle:
        for name in ("model.weights.h5", "config.json", "metadata.json"):
            path = os.path.join(working_dir, name)
            if os.path.exists(path):
                handle.write(path, name)


def extract_keras_archive(archive, directory):
    with zipfile.ZipFile(archive) as handle:
        handle.extractall(directory)
    return os.path.join(directory, "model.weights.h5")


# ---------------------------------------------------------------------------
# Rewrite one entry of an artifact so it reaches outside the artifact
# ---------------------------------------------------------------------------


def write_secret_file(directory):
    path = os.path.join(directory, "secret.bin")
    with open(path, "wb") as handle:
        handle.write(KERNEL.tobytes())
    return path


def make_source_h5(directory):
    """An HDF5 file on the host that holds the marker as a regular dataset."""
    path = os.path.join(directory, "host-source.h5")
    with h5py.File(path, "w") as handle:
        handle.create_dataset("secret", data=KERNEL)
    return path


def make_external_weights(directory, kernel_value=KERNEL, bias_value=BIAS):
    """A complete weights file used as an external target for group links."""
    path = os.path.join(directory, "external-target.weights.h5")
    make_model().save_weights(path)
    with h5py.File(path, "r+") as handle:
        handle["layers/dense/vars/0"][...] = kernel_value
        handle["layers/dense/vars/1"][...] = bias_value
    return path


def make_partial_external_weights(directory, bias_value=BIAS):
    """An external target group holding only the value kept in a later shard."""
    path = os.path.join(directory, "partial-target.weights.h5")
    with h5py.File(path, "w") as handle:
        handle.create_dataset("layers/dense/vars/1", data=bias_value)
    return path


def replace_with_virtual(artifact, dataset_path, source_h5):
    with h5py.File(artifact, "r+") as handle:
        group, _, name = dataset_path.rpartition("/")
        parent = handle[group] if group else handle
        del parent[name]
        layout = h5py.VirtualLayout(shape=KERNEL.shape, dtype=KERNEL.dtype)
        layout[...] = h5py.VirtualSource(
            source_h5, "secret", shape=KERNEL.shape, dtype=KERNEL.dtype
        )
        parent.create_virtual_dataset(name, layout)


def replace_with_external(
    artifact, dataset_path, secret_file, shape=KERNEL.shape, dtype="float32"
):
    nbytes = int(np.prod(shape)) * np.dtype(dtype).itemsize
    with h5py.File(artifact, "r+") as handle:
        group, _, name = dataset_path.rpartition("/")
        parent = handle[group] if group else handle
        del parent[name]
        parent.create_dataset(
            name,
            shape=shape,
            dtype=dtype,
            external=[(secret_file, 0, nbytes)],
        )


def replace_with_soft_link(artifact, dataset_path, target_path):
    with h5py.File(artifact, "r+") as handle:
        group, _, name = dataset_path.rpartition("/")
        parent = handle[group] if group else handle
        del parent[name]
        parent[name] = h5py.SoftLink(target_path)


def replace_with_external_link(artifact, path, target_file, target_path):
    with h5py.File(artifact, "r+") as handle:
        del handle[path]
        handle[path] = h5py.ExternalLink(target_file, target_path)


def add_hidden_dataset(artifact, path, value=KERNEL):
    with h5py.File(artifact, "r+") as handle:
        handle.create_dataset(path, data=value)


def find_named_dataset(group, suffix):
    """Return (parent, name) of the first dataset whose name ends with suffix."""
    found = []

    def visit(name, obj):
        if isinstance(obj, h5py.Dataset) and name.endswith(suffix):
            found.append((name, obj))

    group.visititems(visit)
    if not found:
        raise AssertionError(f"no dataset ending with {suffix!r}")
    name, obj = found[0]
    parent_path, _, leaf = name.rpartition("/")
    parent = group[parent_path] if parent_path else group
    return parent, leaf


def load_shard_index(path):
    with open(path) as handle:
        return json.load(handle)


def save_shard_index(path, index):
    with open(path, "w") as handle:
        json.dump(index, handle)
