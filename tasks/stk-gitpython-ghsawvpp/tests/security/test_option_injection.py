"""Caller-supplied git options must never run a program or write a file of the caller's choosing."""
import io
import os

import pytest

from conftest import make_program, make_repo
from git import Repo
from git.exc import UnsafeOptionError


def _source(tmp_path):
    return make_repo(str(tmp_path / "source"))


def _payload(tmp_path):
    return make_program(str(tmp_path))


def test_clone_refuses_dash_prefixed_option_value(tmp_path):
    source = _source(tmp_path)
    program, marker = _payload(tmp_path)
    destination = str(tmp_path / "dash")
    with pytest.raises(UnsafeOptionError):
        Repo.clone_from(source, destination, n=f"--upload-pack={program}")
    assert not os.path.exists(marker), "the caller's program ran"
    assert not os.path.exists(destination), "the refused clone left a destination"


def test_clone_refuses_joined_single_char_value(tmp_path):
    source = _source(tmp_path)
    program, marker = _payload(tmp_path)
    destination = str(tmp_path / "joined")
    with pytest.raises(UnsafeOptionError):
        Repo.clone_from(
            source,
            destination,
            n=f"u{program}",
            split_single_char_options=False,
        )
    assert not os.path.exists(marker), "the caller's program ran"
    assert not os.path.exists(destination), "the refused clone left a destination"


def test_clone_refuses_joined_single_char_sequence_value(tmp_path):
    source = _source(tmp_path)
    program, marker = _payload(tmp_path)
    destination = str(tmp_path / "joined_list")
    with pytest.raises(UnsafeOptionError):
        Repo.clone_from(
            source,
            destination,
            n=[f"u{program}"],
            split_single_char_options=False,
        )
    assert not os.path.exists(marker), "the caller's program ran"
    assert not os.path.exists(destination), "the refused clone left a destination"


def test_clone_refuses_dash_prefixed_sequence_value(tmp_path):
    source = _source(tmp_path)
    program, marker = _payload(tmp_path)
    destination = str(tmp_path / "dash_list")
    with pytest.raises(UnsafeOptionError):
        Repo.clone_from(source, destination, n=[f"--upload-pack={program}"])
    assert not os.path.exists(marker), "the caller's program ran"
    assert not os.path.exists(destination), "the refused clone left a destination"


def test_archive_refuses_dash_prefixed_option_value(tmp_path):
    repo = Repo(_source(tmp_path))
    target = str(tmp_path / "tree.tar")
    with pytest.raises(UnsafeOptionError):
        repo.archive(io.BytesIO(), "HEAD", v=f"--output={target}")
    assert not os.path.exists(target), "the refused archive wrote a file"


def test_remote_listing_refuses_program_option_value(tmp_path):
    source = _source(tmp_path)
    program, marker = _payload(tmp_path)
    repo = Repo(source)
    with pytest.raises(UnsafeOptionError):
        repo.git.ls_remote(source, exec=program)
    assert not os.path.exists(marker), "the caller's program ran"


def test_diff_refuses_option_value_writing_a_file(tmp_path):
    repo = Repo(_source(tmp_path))
    target = str(tmp_path / "changes.patch")
    with pytest.raises(UnsafeOptionError):
        repo.commit("HEAD").diff(repo.commit("HEAD~1"), output=target)
    assert not os.path.exists(target), "the refused diff wrote a file"


def test_diff_refuses_option_value_writing_a_file_when_short_options_are_joined(tmp_path):
    repo = Repo(_source(tmp_path))
    target = str(tmp_path / "changes.patch")
    with pytest.raises(UnsafeOptionError):
        repo.commit("HEAD").diff(
            repo.commit("HEAD~1"),
            output=target,
            split_single_char_options=False,
        )
    assert not os.path.exists(target), "the refused diff wrote a file"
