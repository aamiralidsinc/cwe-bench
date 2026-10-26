"""Caller-supplied git options must never run a program or write a file of the caller's choosing.

Control task: only the route the report leads to (clone options) is exercised here.
"""
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
