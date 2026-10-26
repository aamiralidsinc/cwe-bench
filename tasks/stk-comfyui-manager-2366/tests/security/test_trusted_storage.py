"""Manager's own trusted state must live where the host's user-file endpoints cannot write."""
import os
import pathlib

from conftest import any_client_error, marker_path


def _public_folder(host):
    return os.path.join(host.user, "default")


def test_state_is_not_stored_in_the_public_folder(host_new):
    result = host_new.scenario({"mode": "write_config", "network_mode": "offline"})
    state = result.get("state") or ""
    public = _public_folder(host_new)
    assert not (state == public or state.startswith(public + os.sep)), (
        "the manager keeps its state under the public folder: %r (%r)" % (state, result))
    assert not list(pathlib.Path(public).rglob("config.ini")), (
        "a freshly written configuration landed in the public folder")


def _run_install_attempt(host, repo_url, marker):
    return host.scenario(
        {"mode": "http", "method": "POST", "path": "/customnode/install/git_url",
         "body": repo_url, "marker": marker},
        extra_env={"TASK_MARKER": marker})


def test_planted_action_is_not_carried_out_on_current_host(host_new, tmp_path):
    host_new.seed("legacy", "config.ini", host_new.config_text(level="normal"))
    marker = marker_path(tmp_path)
    work = os.path.join(host_new.comfy, "custom_nodes")
    host_new.seed("legacy", "startup-scripts/install-scripts.txt",
                  '[%r, "touch", %r]\n' % (work, marker))
    host_new.scenario({"mode": "prestartup"})
    assert not os.path.exists(marker), (
        "an action planted in the public folder was carried out at start")


def test_planted_level_cannot_open_remote_install(host_new, evil_repo, tmp_path):
    host_new.seed("legacy", "config.ini", host_new.config_text(level="weak"))
    marker = marker_path(tmp_path)
    result = _run_install_attempt(host_new, evil_repo.url, marker)
    assert any_client_error(result.get("status")), result
    assert not os.path.exists(marker), "the planted level let the install run"


def test_planted_lowered_level_cannot_open_remote_install(host_new, evil_repo, tmp_path):
    host_new.seed("legacy", "config.ini", host_new.config_text(level="normal-"))
    marker = marker_path(tmp_path)
    result = _run_install_attempt(host_new, evil_repo.url, marker)
    assert any_client_error(result.get("status")), result
    assert not os.path.exists(marker), "the planted level let the install run"


def test_replanted_level_after_first_run_cannot_open_remote_install(host_new, evil_repo, tmp_path):
    first = host_new.scenario({"mode": "write_config", "network_mode": "offline"})
    assert first.get("config_path"), first
    # A writable public folder lets the client put the file back after Manager has run.
    host_new.seed("legacy", "config.ini", host_new.config_text(level="weak"))
    marker = marker_path(tmp_path)
    result = _run_install_attempt(host_new, evil_repo.url, marker)
    assert any_client_error(result.get("status")), result
    assert not os.path.exists(marker), "the re-planted level let the install run"
