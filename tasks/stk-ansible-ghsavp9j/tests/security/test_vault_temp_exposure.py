"""Security tests: a decrypted vault working copy must not be reachable by another local user,
must not be replaceable by name, and must not survive a failed save or the cleanup of a second
decryption path."""
import os
import tempfile

import pytest

from ansible.parsing.dataloader import DataLoader

import vault_helpers as helpers


def test_edit_working_copy_is_owner_only(monkeypatch, tmp_path):
    target = helpers.make_vault_file(str(tmp_path))
    seen = {}

    def during(temp_path):
        seen["mode"] = os.stat(temp_path).st_mode & 0o777
        with open(temp_path, "rb") as handle:
            seen["content"] = handle.read()

    helpers.editor_doing_nothing(monkeypatch, during=during)
    helpers.vault_editor().edit_file(target)

    assert "mode" in seen, "the editor was not given a working copy"
    assert seen["mode"] & 0o077 == 0, "the decrypted working copy is accessible to other local users"
    assert seen["content"] == helpers.PLAINTEXT


def test_edit_working_copy_cannot_be_replaced_by_name(monkeypatch, tmp_path):
    target = helpers.make_vault_file(str(tmp_path))

    attacker_copy = str(tmp_path / "attacker-copy")
    with open(attacker_copy, "wb") as handle:
        handle.write(b"")
    os.chmod(attacker_copy, 0o644)

    roots = [
        os.path.abspath(tempfile.gettempdir()),
        os.path.abspath(os.path.join(os.path.expanduser("~"), ".ansible")),
    ]
    real_remove = os.remove
    state = {"armed": True, "fired": False}
    seen = {}

    def under_temp_locations(path):
        absolute = os.path.abspath(path)
        return any(absolute == root or absolute.startswith(root + os.sep) for root in roots)

    def replace_after_unlink(path):
        real_remove(path)
        # The attack only happens while the product writes the decrypted bytes, i.e. before
        # the editor is started. Anything later is not the plaintext window.
        if state["armed"] and not state["fired"] and under_temp_locations(path):
            state["fired"] = True
            os.symlink(attacker_copy, path)

    monkeypatch.setattr(helpers.vault_module.os, "remove", replace_after_unlink)

    def during(_temp_path):
        # The editor is the window in which a local attacker would read their own file.
        state["armed"] = False
        with open(attacker_copy, "rb") as handle:
            seen["attacker"] = handle.read()

    helpers.editor_doing_nothing(monkeypatch, during=during)
    try:
        helpers.vault_editor().edit_file(target)
    except Exception:
        pass  # refusing the operation is an acceptable outcome

    assert "attacker" in seen, "the editor was not invoked"
    assert helpers.PLAINTEXT not in seen["attacker"], (
        "decrypted content reached a file another local user substituted for the working copy")


def test_failed_save_destroys_working_copy(monkeypatch, tmp_path):
    target = helpers.make_vault_file(str(tmp_path))
    edited_marker = b"edited_secret_marker_7f3a: changed\n"
    helpers.editor_writing(monkeypatch, edited_marker)

    editor = helpers.vault_editor()

    def fail_encrypt(*args, **kwargs):
        raise RuntimeError("simulated encryption failure")

    monkeypatch.setattr(editor.vault, "encrypt", fail_encrypt)

    before = set(helpers.plaintext_files(marker=edited_marker))
    with pytest.raises(Exception):
        editor.edit_file(target)
    after = set(helpers.plaintext_files(marker=edited_marker))

    leftovers = sorted(after - before)
    assert not leftovers, "decrypted content outlived a save that could not complete: %s" % (leftovers,)


def test_second_decryption_path_destroys_its_copy(tmp_path):
    target = helpers.make_vault_file(str(tmp_path))
    loader = DataLoader()
    loader.set_vault_secrets([("default", helpers.secret())])
    working = loader.get_real_file(target)
    recoverable = working + ".recoverable"

    with open(working, "rb") as handle:
        assert handle.read() == helpers.PLAINTEXT
    os.link(working, recoverable)

    loader.cleanup_tmp_file(working)

    with open(recoverable, "rb") as handle:
        remaining = handle.read()
    os.unlink(recoverable)

    assert helpers.PLAINTEXT not in remaining, (
        "the decrypted copy was only unlinked, so its contents are still recoverable")
