"""Legitimate use must keep working, including the values coupled to the screened options."""
import io
import os

from conftest import make_repo
from git import Git, Repo


def _repo(tmp_path):
    return Repo(make_repo(str(tmp_path / "source")))


def test_clone_with_origin_name(tmp_path):
    source = make_repo(str(tmp_path / "source"))
    destination = str(tmp_path / "clone")
    Repo.clone_from(source, destination, o="upstream")
    cloned = Repo(destination)
    assert cloned.remotes["upstream"].url.endswith("source")


def test_clone_with_joined_safe_short_option(tmp_path):
    source = make_repo(str(tmp_path / "source"))
    destination = str(tmp_path / "joined")
    Repo.clone_from(source, destination, multi_options=["-oupstream"])
    cloned = Repo(destination)
    assert cloned.remotes["upstream"].url.endswith("source")


def test_option_screening_accepts_attached_safe_short_values():
    Git.check_unsafe_options(
        options=["-oupstream", "-bcurrent"],
        unsafe_options=["--upload-pack", "-u", "--config", "-c"],
    )


def test_diff_accepts_joined_similarity_value(tmp_path):
    repo = _repo(tmp_path)
    joined = repo.commit("HEAD").diff(
        repo.commit("HEAD~1"),
        split_single_char_options=False,
        M="75%",
    )
    renamed = [item for item in joined if item.renamed_file]
    assert len(joined) == 2
    assert len(renamed) == 1
    assert {renamed[0].rename_from, renamed[0].rename_to} == {"file_a.txt", "file_b.txt"}


def test_diff_accepts_common_options(tmp_path):
    repo = _repo(tmp_path)
    result = repo.commit("HEAD").diff(repo.commit("HEAD~1"), R=True, find_renames=True)
    paths = {item.a_path for item in result} | {item.b_path for item in result}
    assert "keep.txt" in paths


def test_archive_writes_the_requested_format(tmp_path):
    repo = _repo(tmp_path)
    stream = io.BytesIO()
    repo.archive(stream, "HEAD", format="tar")
    content = stream.getvalue()
    assert content
    assert "file_b.txt" in content.decode("latin-1")


def test_remote_listing_lists_references(tmp_path):
    source = make_repo(str(tmp_path / "source"))
    repo = Repo(source)
    assert "refs/heads/main" in repo.git.ls_remote(source)
    assert "refs/heads/main" in repo.git.ls_remote("--heads", source)


def test_clone_still_accepts_a_safe_single_char_value(tmp_path):
    source = make_repo(str(tmp_path / "source"))
    destination = str(tmp_path / "safe")
    Repo.clone_from(source, destination, b="main")
    assert os.path.isdir(os.path.join(destination, ".git"))
