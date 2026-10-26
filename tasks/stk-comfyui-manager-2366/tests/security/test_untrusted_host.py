"""A host with no protected location must never trust the public folder."""
import json
import os

from conftest import any_client_error, marker_path


def _seed_old_host(host, level="weak", extra=""):
    host.seed("legacy", "config.ini", host.config_text(level=level, extra=extra))


def test_old_host_forces_the_strongest_level(host_legacy, evil_repo, tmp_path):
    _seed_old_host(host_legacy, level="weak")
    # On a host without system users every folder below the user directory is reachable.
    host_legacy.seed("protected", "config.ini", host_legacy.config_text(level="weak"))
    marker = marker_path(tmp_path)
    result = host_legacy.scenario(
        {"mode": "http", "method": "POST", "path": "/customnode/install/git_url",
         "body": evil_repo.url, "marker": marker},
        extra_env={"TASK_MARKER": marker})
    assert any_client_error(result.get("status")), result
    assert not os.path.exists(marker), "the old host honoured the planted level"


def test_old_host_defaulted_level_is_not_enough(host_legacy):
    host_legacy.seed("legacy", "config.ini", host_legacy.config_text(level=None))
    host_legacy.seed("legacy", "snapshots/legit.json", '{"custom_nodes": []}')
    host_legacy.seed("protected", "snapshots/legit.json", '{"custom_nodes": []}')
    result = host_legacy.scenario(
        {"mode": "http", "method": "GET", "path": "/snapshot/restore?target=legit"})
    assert any_client_error(result.get("status")), result
    for state in (host_legacy.legacy_manager, host_legacy.protected_manager):
        queued = os.path.join(state, "startup-scripts", "restore-snapshot.json")
        assert not os.path.exists(queued), (
            "the old host queued a restore for the next start (%s)" % queued)


def test_old_host_cannot_launch_planted_restore(host_legacy, evil_repo, tmp_path):
    _seed_old_host(host_legacy)
    snapshot = {"custom_nodes": [], "git_custom_nodes": {evil_repo.url: {"hash": "main"}}}
    host_legacy.seed("legacy", "startup-scripts/restore-snapshot.json", json.dumps(snapshot))
    marker = marker_path(tmp_path)
    host_legacy.scenario({"mode": "prestartup"}, extra_env={"TASK_MARKER": marker})
    assert not os.path.exists(marker), "the old host carried out a restore from the public folder"


def test_old_host_ignores_planted_startup_environment(host_legacy):
    _seed_old_host(host_legacy, extra="bypass_ssl = true\nfile_logging = false\n")
    host_legacy.seed("legacy", "pip_overrides.json",
                     json.dumps({"task-attacker-package": "evil-remapped"}))
    host_legacy.seed("legacy", "pip_blacklist.list", "attacker-pinned-package\n")
    result = host_legacy.scenario({"mode": "observe"})
    assert result.get("bypass") is False, ("TLS verification was disabled: %r" % (result,))
    assert result.get("override") == "task-attacker-package", (
        "a planted package remap was applied: %r" % (result,))
    assert not result.get("blacklist_hit"), "a planted blacklist entry was loaded"


def test_old_host_does_not_use_planted_package_index(host_legacy, index_server):
    _seed_old_host(host_legacy)
    host_legacy.seed(
        "legacy", "pip_auto_fix.list",
        "task-sentinel-pkg==9.9.9 --index-url %s\n" % index_server.url)
    host_legacy.scenario({"mode": "prestartup"})
    assert index_server.hits == 0, (
        "the old host used a package index named by the public folder (%d requests)"
        % index_server.hits)
