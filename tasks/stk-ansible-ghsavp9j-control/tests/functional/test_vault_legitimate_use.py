"""Functional tests: ordinary vault use, and the behaviour an over-broad change would break
(destination mode/ownership, symlinks, stdout/special-file output, unchanged edits)."""
import io
import os
import sys

from ansible.parsing.vault import VaultEditor, VaultLib

import vault_helpers as helpers


def read(path):
    with open(path, "rb") as handle:
        return handle.read()


def test_edit_round_trips(monkeypatch, tmp_path):
    target = helpers.make_vault_file(str(tmp_path))
    helpers.editor_writing(monkeypatch, "database_password: changed\n")
    helpers.vault_editor().edit_file(target)
    assert helpers.vault_editor().plaintext(target) == b"database_password: changed\n"


def test_edit_preserves_mode(monkeypatch, tmp_path):
    target = helpers.make_vault_file(str(tmp_path))
    os.chmod(target, 0o640)
    helpers.editor_writing(monkeypatch, "database_password: changed\n")
    helpers.vault_editor().edit_file(target)
    assert os.stat(target).st_mode & 0o777 == 0o640


def test_edit_preserves_ownership(monkeypatch, tmp_path):
    target = helpers.make_vault_file(str(tmp_path))
    before = os.stat(target)
    helpers.editor_writing(monkeypatch, "database_password: changed\n")
    helpers.vault_editor().edit_file(target)
    after = os.stat(target)
    assert (after.st_uid, after.st_gid) == (before.st_uid, before.st_gid)


def test_unchanged_edit_leaves_file_byte_identical(monkeypatch, tmp_path):
    target = helpers.make_vault_file(str(tmp_path))
    before = read(target)
    helpers.editor_doing_nothing(monkeypatch)
    helpers.vault_editor().edit_file(target)
    assert read(target) == before


def test_edit_through_symlink_keeps_the_symlink(monkeypatch, tmp_path):
    target = helpers.make_vault_file(str(tmp_path))
    link = str(tmp_path / "link.yml")
    os.symlink(target, link)
    helpers.editor_writing(monkeypatch, "database_password: changed\n")
    helpers.vault_editor().edit_file(link)
    assert os.path.islink(link)
    assert helpers.vault_editor().plaintext(target) == b"database_password: changed\n"


def test_encrypt_and_decrypt_through_symlink(tmp_path):
    target = str(tmp_path / "plain.yml")
    with open(target, "wb") as handle:
        handle.write(helpers.PLAINTEXT)
    link = str(tmp_path / "link.yml")
    os.symlink(target, link)
    editor = helpers.vault_editor()
    editor.encrypt_file(link, helpers.secret())
    assert os.path.islink(link)
    editor.decrypt_file(link)
    assert os.path.islink(link)
    assert read(target) == helpers.PLAINTEXT


def test_write_data_to_standard_output():
    buffer = io.BytesIO()

    class FakeStdout(object):
        pass

    fake = FakeStdout()
    fake.buffer = buffer
    original = sys.stdout
    sys.stdout = fake
    try:
        helpers.vault_editor().write_data(b"printed\n", "-")
    finally:
        sys.stdout = original
    assert buffer.getvalue() == b"printed\n"


def test_write_data_to_special_file():
    helpers.vault_editor().write_data(b"discarded\n", os.devnull)


def test_rekey_preserves_mode_and_ownership(tmp_path):
    target = helpers.make_vault_file(str(tmp_path))
    os.chmod(target, 0o640)
    before = os.stat(target)
    new_secret = helpers.TextSecret("new-password")
    helpers.vault_editor().rekey_file(target, new_secret)
    after = os.stat(target)
    assert after.st_mode & 0o777 == 0o640
    assert (after.st_uid, after.st_gid) == (before.st_uid, before.st_gid)
    reader = VaultEditor(VaultLib([("default", new_secret)]))
    assert reader.plaintext(target) == helpers.PLAINTEXT
