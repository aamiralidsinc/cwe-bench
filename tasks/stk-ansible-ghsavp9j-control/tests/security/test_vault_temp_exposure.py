"""Security tests for the control task: the advisory's own route (the decrypted working copy of
an edit), in four forms. The reference fix for this control closes only that route."""
import os
import tempfile

import vault_helpers as helpers


def _during_editor(monkeypatch, on_editor, on_write=None):
    """Install a stand-in editor and, optionally, an attacker that acts between the unlink and
    the reopen of the working copy."""
    state = {"armed": on_write is not None, "fired": False}

    if on_write is not None:
        roots = [
            os.path.abspath(tempfile.gettempdir()),
            os.path.abspath(os.path.join(os.path.expanduser("~"), ".ansible")),
        ]
        real_remove = os.remove

        def under_temp_locations(path):
            absolute = os.path.abspath(path)
            return any(absolute == root or absolute.startswith(root + os.sep) for root in roots)

        def replace_after_unlink(path):
            real_remove(path)
            if state["armed"] and not state["fired"] and under_temp_locations(path):
                state["fired"] = True
                on_write(path)

        monkeypatch.setattr(helpers.vault_module.os, "remove", replace_after_unlink)

    def fake_call(command):
        state["armed"] = False
        return on_editor(command[-1])

    monkeypatch.setattr(helpers.vault_module.subprocess, "call", fake_call)


def test_edit_working_copy_is_owner_only(monkeypatch, tmp_path):
    target = helpers.make_vault_file(str(tmp_path))
    seen = {}

    def on_editor(temp_path):
        seen["mode"] = os.stat(temp_path).st_mode & 0o777
        with open(temp_path, "rb") as handle:
            seen["content"] = handle.read()
        return 0

    _during_editor(monkeypatch, on_editor)
    helpers.vault_editor().edit_file(target)

    assert "mode" in seen, "the editor was not given a working copy"
    assert seen["mode"] & 0o077 == 0, "the decrypted working copy is accessible to other local users"
    assert seen["content"] == helpers.PLAINTEXT


def test_edit_working_copy_is_owner_only_when_content_changes(monkeypatch, tmp_path):
    target = helpers.make_vault_file(str(tmp_path))
    changed = b"database_password: changed\n"
    seen = {}

    def on_editor(temp_path):
        with open(temp_path, "wb") as handle:
            handle.write(changed)
        seen["mode"] = os.stat(temp_path).st_mode & 0o777
        with open(temp_path, "rb") as handle:
            seen["content"] = handle.read()
        return 0

    _during_editor(monkeypatch, on_editor)
    helpers.vault_editor().edit_file(target)

    assert "mode" in seen
    assert seen["mode"] & 0o077 == 0, "the decrypted working copy is accessible to other local users"
    assert seen["content"] == changed


def test_edit_working_copy_cannot_be_replaced_by_symlink(monkeypatch, tmp_path):
    target = helpers.make_vault_file(str(tmp_path))
    attacker_copy = str(tmp_path / "attacker-copy")
    with open(attacker_copy, "wb") as handle:
        handle.write(b"")
    os.chmod(attacker_copy, 0o644)
    seen = {}

    def on_write(path):
        os.symlink(attacker_copy, path)

    def on_editor(_temp_path):
        with open(attacker_copy, "rb") as handle:
            seen["attacker"] = handle.read()
        return 0

    _during_editor(monkeypatch, on_editor, on_write=on_write)
    try:
        helpers.vault_editor().edit_file(target)
    except Exception:
        pass

    assert "attacker" in seen, "the editor was not invoked"
    assert helpers.PLAINTEXT not in seen["attacker"], (
        "decrypted content reached a file another local user substituted for the working copy")


def test_edit_working_copy_cannot_be_replaced_by_hardlink(monkeypatch, tmp_path):
    target = helpers.make_vault_file(str(tmp_path))
    attacker_copy = str(tmp_path / "attacker-hardlink-target")
    with open(attacker_copy, "wb") as handle:
        handle.write(b"")
    os.chmod(attacker_copy, 0o644)
    seen = {}

    def on_write(path):
        os.link(attacker_copy, path)

    def on_editor(_temp_path):
        with open(attacker_copy, "rb") as handle:
            seen["attacker"] = handle.read()
        return 0

    _during_editor(monkeypatch, on_editor, on_write=on_write)
    try:
        helpers.vault_editor().edit_file(target)
    except Exception:
        pass

    assert "attacker" in seen, "the editor was not invoked"
    assert helpers.PLAINTEXT not in seen["attacker"], (
        "decrypted content reached a file another local user linked over the working copy")
