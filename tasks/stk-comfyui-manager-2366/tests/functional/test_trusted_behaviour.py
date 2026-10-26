"""Legitimate operator behaviour that must keep working after the fix."""
import os

from conftest import marker_path


def test_saved_level_and_preference_survive_first_run(host_new):
    host_new.seed("legacy", "config.ini",
                  host_new.config_text(level="normal",
                                       extra="update_policy = nightly-comfyui\n"))
    result = host_new.scenario({"mode": "level"})
    assert result.get("level") == "normal", result
    assert result.get("policy") == "nightly-comfyui", result


def test_queue_written_by_manager_runs_on_current_host(host_new, tmp_path):
    marker = marker_path(tmp_path)
    host_new.seed("legacy", "config.ini", host_new.config_text(level="normal"))
    produced = host_new.scenario(
        {"mode": "reserve", "cwd": os.path.join(host_new.comfy, "custom_nodes"),
         "command": ["touch", marker]})
    assert produced.get("state"), produced
    host_new.scenario({"mode": "prestartup"})
    assert os.path.exists(marker), "the queue Manager itself wrote was not carried out"


def test_scheduled_restore_runs_on_current_host(host_new, evil_repo, tmp_path):
    marker = marker_path(tmp_path)
    host_new.seed("legacy", "config.ini", host_new.config_text(level="normal"))
    scheduled = host_new.scenario({"mode": "schedule", "git_url": evil_repo.url},
                                  extra_env={"TASK_MARKER": marker})
    assert scheduled.get("queued"), scheduled
    host_new.scenario({"mode": "prestartup"}, extra_env={"TASK_MARKER": marker})
    assert os.path.exists(marker), "a restore the operator scheduled was not carried out"


def test_trusted_install_preferences_still_apply(host_new, index_server):
    host_new.seed("legacy", "config.ini", host_new.config_text(level="normal"))
    seeded = host_new.scenario({"mode": "seed_trusted", "index_url": index_server.url})
    assert seeded.get("config_path"), seeded
    result = host_new.scenario({"mode": "observe"})
    assert result.get("bypass") is True, ("a trusted setting stopped applying: %r" % (result,))
    assert result.get("override") == "evil-remapped", result
    assert result.get("blacklist_hit"), result
    assert index_server.hits >= 1, "a trusted auto-fix list stopped being used"


def test_self_update_stays_reachable_on_old_host(host_legacy):
    host_legacy.seed("legacy", "config.ini", host_legacy.config_text(level="weak"))
    result = host_legacy.scenario(
        {"mode": "http", "method": "GET", "path": "/manager/queue/update_comfyui"})
    assert result.get("status") == 200, result


def test_saved_level_not_overwritten_on_old_host(host_legacy):
    host_legacy.seed("legacy", "config.ini", host_legacy.config_text(level="normal"))
    result = host_legacy.scenario(
        {"mode": "http", "method": "GET", "path": "/manager/policy/update?value=nightly-comfyui",
         "stored_level": True})
    assert result.get("status") == 200, result
    assert result.get("stored_level") == "normal", (
        "the enforced value was written over the operator's saved value: %r" % (result,))
