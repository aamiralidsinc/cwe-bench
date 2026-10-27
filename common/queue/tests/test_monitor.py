"""Resource monitor (monitor.py) and preflight (preflight.py)."""
import json

import cweq
import dispatch
import monitor
import preflight
import qdb


def mon(conn, cfg, root, values, t):
    """A Monitor whose sample() returns the given values at epoch t (no machine reads, no Docker)."""
    m = monitor.Monitor(conn, cfg, root, proc_list=[], now=lambda: t, docker=False)

    def fake():
        s = {"ts": qdb.utc(t), "epoch": t, **values, "jobs": "{}"}
        m.forecast(s)
        return s
    m.sample = fake
    return m


def test_burn_rate_and_forecast(conn, cfg, root):
    cfg["limits"]["min_free_disk_gb"] = 150
    t0 = 1_800_000_000
    for i, free in enumerate([500, 490, 480, 470]):          # 10 GB per 10 min = 60 GB/h
        rep = mon(conn, cfg, root, {"free_disk_gb": free, "root_inode_pct": 10 + i}, t0 + 600 * i).tick()
    s = rep["sample"]
    assert abs(s["disk_burn_gb_h"] - 60) < 0.01
    assert abs(s["disk_floor_h"] - (470 - 150) / 60) < 0.01
    assert abs(s["inode_burn_pct_h"] - 6) < 0.01
    assert abs(s["inode_full_h"] - (100 - 13) / 6) < 0.01
    assert conn.execute("SELECT COUNT(*) FROM metrics").fetchone()[0] == 4


def test_no_forecast_while_disk_grows_or_too_few_points(conn, cfg, root):
    t0 = 1_800_000_000
    rep = mon(conn, cfg, root, {"free_disk_gb": 500}, t0).tick()
    assert "disk_floor_h" not in rep["sample"]
    for i, free in enumerate([510, 520, 530]):
        rep = mon(conn, cfg, root, {"free_disk_gb": free}, t0 + 600 * (i + 1)).tick()
    assert rep["sample"]["disk_burn_gb_h"] < 0 and "disk_floor_h" not in rep["sample"]


def test_alerts_raise_once_and_clear(conn, cfg, root):
    cfg["monitor"] = {"disk_free_gb_warn": 300}
    t0 = 1_800_000_000
    names = lambda rep: [(n, st) for n, st, *_ in rep["alerts"]]                    # noqa: E731
    assert names(mon(conn, cfg, root, {"free_disk_gb": 400}, t0).tick()) == []
    assert ("disk_free_low", "raised") in names(mon(conn, cfg, root, {"free_disk_gb": 250}, t0 + 60).tick())
    assert "disk_free_low" not in [n for n, _ in names(mon(conn, cfg, root, {"free_disk_gb": 240}, t0 + 120).tick())]
    assert ("disk_free_low", "cleared") in names(mon(conn, cfg, root, {"free_disk_gb": 350}, t0 + 180).tick())
    rows = conn.execute("SELECT name, state FROM monitor_alerts ORDER BY id").fetchall()
    assert [(r["name"], r["state"]) for r in rows if r["name"] == "disk_free_low"] == \
        [("disk_free_low", "raised"), ("disk_free_low", "cleared")]


def test_disk_forecast_queues_one_extra_cleanup_per_hour(conn, cfg, root):
    cfg["limits"]["min_free_disk_gb"] = 150
    cfg["monitor"] = {"disk_floor_within_h": 6, "disk_free_gb_warn": 0}
    t0 = 1_800_000_000 - 1_800_000_000 % 3600                 # the top of an hour
    for i, free in enumerate([400, 350, 300, 250, 200]):        # 50 GB per 10 min: the floor is under an hour away
        mon(conn, cfg, root, {"free_disk_gb": free}, t0 + 600 * i).tick()
    extra = qdb.jobs(conn, "kind='cleanup'")
    assert len(extra) == 1 and qdb.args_of(extra[0])["extra"] == "disk forecast"
    assert extra[0]["origin"] == "monitor"


def test_dry_run_writes_nothing(conn, cfg, root):
    rep = mon(conn, cfg, root, {"free_disk_gb": 100}, 1_800_000_000).tick(dry_run=True)
    assert rep["sample"]["free_disk_gb"] == 100
    assert not monitor.has_table(conn, "metrics")
    assert qdb.jobs(conn) == []


def test_dispatcher_uses_a_fresh_sample_only(conn, cfg, root):
    cfg["monitor"] = {"fresh_sec": 120}
    now = 1_800_000_000
    mon(conn, cfg, root, {"free_disk_gb": 5, "load1": 1, "mem_available_gb": 100, "tmp_inode_pct": 1}, now).tick()
    fresh = monitor.fresh_headroom(conn, cfg, now=now + 60)
    assert fresh == {"free_disk_gb": 5, "load": 1, "mem_available_gb": 100, "tmp_inode_pct": 1}
    assert monitor.fresh_headroom(conn, cfg, now=now + 600) is None
    d = dispatch.Dispatcher(conn, cfg, cfg["db"], proc_list=[], spawn=lambda i: 1)
    monitor_fresh = monitor.fresh_headroom
    try:
        monitor.fresh_headroom = lambda c, k, now=None: monitor_fresh(c, k, now=1_800_000_060)
        assert d.metrics()["free_disk_gb"] == 5                  # the sample, not a fresh measurement
    finally:
        monitor.fresh_headroom = monitor_fresh


# ---------- preflight

def pf_cfg(cfg, tmp_path, daemon=None, tuning=None, limits=None, models=None, harbor=None):
    def w(name, text):
        if text is None:
            return str(tmp_path / f"missing-{name}")
        p = tmp_path / name
        p.write_text(text)
        return str(p)
    cfg["preflight"] = {"daemon_json": w("daemon.json", daemon), "tuning_env": w("tuning.env", tuning),
                        "limits_env": w("limits.env", limits), "model_env": [w("models.env", models)],
                        "harbor_docker_glob": w("docker.py", harbor)}
    return cfg


GOOD_DAEMON = json.dumps({"shutdown-timeout": 120, "default-ulimits": {"nofile": {"Soft": 1048576, "Hard": 1048576}},
                          "log-driver": "json-file", "log-opts": {"max-size": "50m", "max-file": "3"}})
GOOD_TUNING = "export COMPOSE_HTTP_TIMEOUT=300\nexport DOCKER_CLIENT_TIMEOUT=300\nexport DOCKER_BUILDKIT=0\n" \
              "export COMPOSE_DOCKER_CLI_BUILD=0\n"
GOOD_LIMITS = "\n".join(f"{k}=10" for k in preflight.GATE_KEYS) + "\n"
GOOD_HARBOR = 'if "down" in full_command:\n    pass\nx(timeout=300)\n'
ANSWERING = lambda cmd, timeout=20: (0, "29.9.1")                                   # noqa: E731


def by_name(results):
    return {n: (st, d, f) for n, st, d, f in results}


def test_preflight_all_ok_but_log_rotation(cfg, tmp_path, root):
    no_rotation = json.dumps({"shutdown-timeout": 120, "default-ulimits": {"nofile": {"Soft": 1048576,
                                                                                       "Hard": 1048576}}})
    pf_cfg(cfg, tmp_path, no_rotation, GOOD_TUNING, GOOD_LIMITS, "DEEPSEEK_API_KEY=abc123\n", GOOD_HARBOR)
    r = by_name(preflight.run_all(cfg, runner=ANSWERING, proc_list=[]))
    assert r["daemon_json"][0] == preflight.NEEDS and "log-opts" in r["daemon_json"][2]
    assert "restart docker" in r["daemon_json"][2] and "no build, gate or trial runs" in r["daemon_json"][2]
    for name in ("docker_daemon", "docker_tuning", "harbor_patches", "gate_limits", "model_keys"):
        assert r[name][0] == preflight.OK, (name, r[name])
    assert "abc123" not in json.dumps(r)                       # secret values never reach the report


def test_preflight_good_daemon_json(cfg, tmp_path, root):
    pf_cfg(cfg, tmp_path, GOOD_DAEMON, GOOD_TUNING, GOOD_LIMITS, "K_API_KEY=x\n", GOOD_HARBOR)
    assert by_name(preflight.run_all(cfg, runner=ANSWERING, proc_list=[]))["daemon_json"][0] == preflight.OK


def test_preflight_needs_and_critical(cfg, tmp_path, root):
    pf_cfg(cfg, tmp_path, GOOD_DAEMON, "export DOCKER_BUILDKIT=1\n", "GATE_TASK_SLOTS=3\n", "NOTHING=1\n",
           'x(timeout=30)\n')
    r = by_name(preflight.run_all(cfg, runner=lambda cmd, timeout=20: (1, "cannot connect"), proc_list=[]))
    assert r["docker_daemon"][0] == preflight.CRITICAL
    assert r["model_keys"][0] == preflight.CRITICAL
    assert r["docker_tuning"][0] == preflight.NEEDS and "DOCKER_BUILDKIT=0" in r["docker_tuning"][2]
    assert r["harbor_patches"][0] == preflight.NEEDS and "patch_probe_timeout.sh" in r["harbor_patches"][2]
    assert r["gate_limits"][0] == preflight.NEEDS
    assert preflight.exit_code(preflight.run_all(cfg, runner=ANSWERING, proc_list=[])) == 2   # model keys missing


def test_dispatch_refuses_on_critical_preflight(cfg, tmp_path, root, monkeypatch, capsys):
    monkeypatch.setattr(preflight, "run_all", lambda cfg, **k: [("model_keys", preflight.CRITICAL, "none", None)])
    cfgfile = tmp_path / "queue.toml"
    rc = cweq.main(["--config", str(cfgfile), "dispatch", "--once"])
    assert rc == 2 and "dispatch refused" in capsys.readouterr().out
    rc = cweq.main(["--config", str(cfgfile), "dispatch", "--once", "--skip-preflight"])
    assert rc == 0


DF_OUT = ('{"Type":"Images","TotalCount":"382","Size":"3.539TB"}\\n'
          '{"Type":"Build Cache","TotalCount":"71","Size":"18.41GB"}')


def test_docker_df_runs_in_the_background(conn, cfg, root, monkeypatch):
    import time as _t
    monkeypatch.setattr(monitor, "DF_CMD", ["sh", "-c", f"sleep 0.3; printf '{DF_OUT}\\n'"])
    monkeypatch.setattr(monitor, "docker_counts", lambda timeout=20: (10, 4))
    clock = [1_800_000_000.0]
    m = monitor.Monitor(conn, cfg, root, proc_list=[], now=lambda: clock[0])
    m.prev_cpu = (0, 0)
    first = m.sample()                                    # starts `docker system df`, does not wait for it
    assert first.get("images") is None and first["containers_running"] == 4
    _t.sleep(0.6)
    clock[0] += 60
    second = m.sample()                                   # the background result lands here
    assert second["images"] == 382 and second["build_cache_gb"] == 18.4


def test_docker_df_waits_in_one_shot_mode(conn, cfg, root, monkeypatch):
    monkeypatch.setattr(monitor, "DF_CMD", ["sh", "-c", f"sleep 0.2; printf '{DF_OUT}\\n'"])
    monkeypatch.setattr(monitor, "docker_counts", lambda timeout=20: (None, None))
    m = monitor.Monitor(conn, cfg, root, proc_list=[], now=lambda: 1_800_000_000.0, wait_df=True)
    m.prev_cpu = (0, 0)
    s = m.sample()
    assert s["images"] == 382 and s["build_cache_gb"] == 18.4
