"""Sharded weight sets: group and value lookups in any shard must be confined."""

import _support as support


def test_external_link_group_in_later_shard(tmp_path):
    path = support.save_sharded_weights(tmp_path)
    target = support.make_partial_external_weights(tmp_path)
    shards = support.shard_files(tmp_path)
    support.replace_with_external_link(
        shards[1], "layers/dense", target, "layers/dense"
    )

    error, values = support.load_weights_attempt(path)
    assert error is not None
    assert not support.holds_marker(values)


def test_external_storage_in_later_shard(tmp_path):
    path = support.save_sharded_weights(tmp_path)
    secret = support.write_secret_file(tmp_path)
    shards = support.shard_files(tmp_path)
    support.replace_with_external(
        shards[1], "layers/dense/vars/1", secret, shape=(2,)
    )

    error, values = support.load_weights_attempt(path)
    assert error is not None
    assert not support.holds_marker(values)


def test_unlisted_entry_group_in_open_shard(tmp_path):
    path = support.save_sharded_weights(tmp_path)
    target = support.make_external_weights(tmp_path)
    shards = support.shard_files(tmp_path)
    support.replace_with_external_link(
        shards[0], "layers/dense", target, "layers/dense"
    )
    index = support.load_shard_index(path)
    index["weight_map"] = {}
    support.save_shard_index(path, index)

    error, values = support.load_weights_attempt(path)
    assert error is not None
    assert not support.holds_marker(values)
