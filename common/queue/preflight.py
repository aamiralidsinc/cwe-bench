"""Preflight: read-only checks of the machine's setup before the pipeline launches work.

    python3 common/queue/cweq.py preflight          exit 0 = all OK, 1 = something needs applying, 2 = critical

Every check reports OK, NEEDS APPLYING (with the exact command or setting; nothing is applied here, and anything that
needs root or a Docker restart is only reported) or CRITICAL. `cweq dispatch` refuses to start while a check is
critical, unless it is given --skip-preflight. Secret values are never read into the report: model env files are
checked for the presence of non-empty *KEY* settings only.

Checks:
  docker_daemon     the daemon answers (`docker version`)                                         CRITICAL if not
  daemon_json       shutdown-timeout >= 60, default nofile >= 65536, json-file log rotation (log-opts max-size,
                    or per container through the compose override in common/harbor_ext/cwe_labels.py)
  docker_tuning     common/gate/docker-tuning.env: COMPOSE_HTTP_TIMEOUT and DOCKER_CLIENT_TIMEOUT >= 300,
                    DOCKER_BUILDKIT=0, COMPOSE_DOCKER_CLI_BUILD=0; sourced by run_trial.sh and gate_one_ds.sh
  harbor_patches    the installed Harbor carries the teardown patch and the 300 s kernel-probe timeout
                    (common/trial/harbor/README.md)                                           CRITICAL if Harbor is missing
  image_reuse       common/harbor_ext is present and wired into run_trial.sh and gate.py, CWE_IMAGE_REUSE is not 0
  gate_limits       ~/.tb-graders/cwe/slots/limits.env holds every gate slot and disk floor setting
  model_keys        a model env file with at least one non-empty *KEY* setting                    CRITICAL if none
  versions          harbor, uv and Docker versions (information)
  headroom          free disk, memory and /tmp inodes against the queue's admission limits        CRITICAL when over
  queue_loops       the reconcile and monitor loops are running (information for an operator)
  frozen_processes  no builder, gate or trial is stopped by SIGSTOP (frozen.py); its timers keep running and fire
                    on resume                                                                  CRITICAL if any
"""
import glob
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import procs  # noqa: E402
from taskstate import paths  # noqa: E402

OK, NEEDS, CRITICAL = "OK", "NEEDS APPLYING", "CRITICAL"


def _frozen_scan():
    import frozen
    return frozen.scan()
GATE_KEYS = ("GATE_TASK_SLOTS", "GATE_GLOBAL_SLOTS", "DISK_MIN_FREE_GB_GATE", "DISK_MIN_FREE_GB_TRIAL",
             "DISK_MIN_FREE_GB_BUILD")
DEFAULTS = {
    "daemon_json": "/etc/docker/daemon.json",
    "tuning_env": None,                                   # None = paths.DOCKER_TUNING
    "harbor_docker_glob": "~/.local/share/uv/tools/harbor/lib/python3*/site-packages/harbor/environments/docker/docker.py",
    "limits_env": "~/.tb-graders/cwe/slots/limits.env",
    "model_env": ["~/.config/cwe/models.env", "~/.tb-graders/cwe/models.env"],
    "min_shutdown_timeout": 60, "min_nofile": 65536, "min_client_timeout": 300,
}


def settings(cfg):
    return {**DEFAULTS, **(cfg.get("preflight") or {})}


def read(p):
    try:
        return Path(os.path.expanduser(str(p))).read_text(errors="replace")
    except OSError:
        return None


def run(cmd, timeout=20):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.returncode, (r.stdout or r.stderr).strip()
    except (OSError, subprocess.SubprocessError) as e:
        return None, str(e)


def env_values(text):
    """KEY=value pairs of a shell env file (export, quotes and comments handled)."""
    out = {}
    for line in (text or "").splitlines():
        m = re.match(r"\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)=(.*)", line)
        if m and not line.lstrip().startswith("#"):
            out[m.group(1)] = m.group(2).split("#")[0].strip().strip("\"'")
    return out


def check_docker_daemon(s, runner):
    rc, out = runner(["docker", "version", "--format", "{{.Server.Version}}"], 30)
    if rc == 0 and out:
        return OK, f"Docker server {out}", None
    return CRITICAL, f"the Docker daemon does not answer ({out[:120]})", "start Docker (needs root): sudo systemctl start docker"


def check_daemon_json(s):
    text = read(s["daemon_json"])
    if text is None:
        return NEEDS, f"{s['daemon_json']} not found: Docker defaults apply", daemon_fix(["all three settings"])
    try:
        d = json.loads(text)
    except ValueError as e:
        return CRITICAL, f"{s['daemon_json']} is not valid JSON ({e}); Docker would refuse to restart", \
            "fix the file before any Docker restart"
    missing = []                                          # (what, JSON to add)
    st = d.get("shutdown-timeout")
    if not isinstance(st, int) or st < s["min_shutdown_timeout"]:
        missing.append(("shutdown-timeout", f'"shutdown-timeout": {max(120, s["min_shutdown_timeout"])}'))
    nofile = ((d.get("default-ulimits") or {}).get("nofile") or {})
    if min(int(nofile.get("Soft") or 0), int(nofile.get("Hard") or 0)) < s["min_nofile"]:
        missing.append(("nofile limit",
                        '"default-ulimits": {"nofile": {"Name": "nofile", "Soft": 1048576, "Hard": 1048576}}'))
    driver = d.get("log-driver", "json-file")
    per_container = per_container_rotation()
    rotation = d.get("log-opts")
    if driver in ("json-file", "local") and not (d.get("log-opts") or {}).get("max-size"):
        if per_container:
            rotation = "per container (common/harbor_ext/cwe_labels.py; the daemon default is optional)"
        else:
            missing.append(("container log rotation",
                            '"log-driver": "json-file", "log-opts": {"max-size": "50m", "max-file": "3"}'))
    if not missing:
        return OK, f"shutdown-timeout {st}, nofile {nofile.get('Soft')}, log rotation {rotation}", None
    return NEEDS, "daemon.json lacks " + ", ".join(w for w, _ in missing), daemon_fix([j for _, j in missing])


def per_container_rotation():
    """True when every pipeline container gets json-file rotation from the compose override (cwe_labels.py), which
    applies without restarting Docker."""
    if os.environ.get("CWE_LOG_ROTATE", "1") == "0":
        return False
    lab = read(paths.COMMON / "harbor_ext" / "cwe_labels.py") or ""
    env = read(paths.COMMON / "harbor_ext" / "cwe_reuse_env.py") or ""
    return "max-size" in lab and "LOGGING" in env


def daemon_fix(items):
    return ("add to /etc/docker/daemon.json (root): " + ", ".join(items) +
            "; then `sudo systemctl restart docker` only while no build, gate or trial runs "
            "(log rotation applies to containers created after the restart)")


def check_docker_tuning(s):
    f = s["tuning_env"] or str(paths.DOCKER_TUNING)
    v = env_values(read(f))
    if not v:
        return NEEDS, f"{f} missing or empty", f"restore {f} from git (common/gate/docker-tuning.env)"
    bad = []
    for k in ("COMPOSE_HTTP_TIMEOUT", "DOCKER_CLIENT_TIMEOUT"):
        try:
            if int(v.get(k, 0)) < s["min_client_timeout"]:
                bad.append(f"{k}={s['min_client_timeout']}")
        except ValueError:
            bad.append(f"{k}={s['min_client_timeout']}")
    for k in ("DOCKER_BUILDKIT", "COMPOSE_DOCKER_CLI_BUILD"):
        if v.get(k) != "0":
            bad.append(f"{k}=0")
    users = [u for u in (paths.COMMON / "trial" / "run_trial.sh", paths.COMMON / "gate" / "gate_one_ds.sh")
             if u.is_file() and "CWE_DOCKER_TUNING" not in u.read_text(errors="replace")]
    if bad or users:
        return NEEDS, ("settings: " + ", ".join(bad) if bad else "") + \
            ("; not sourced by " + ", ".join(u.name for u in users) if users else ""), \
            f"set {', '.join(bad)} in {f}" if bad else "source $CWE_DOCKER_TUNING at the top of those scripts"
    return OK, f"client/compose timeouts {v.get('DOCKER_CLIENT_TIMEOUT')}/{v.get('COMPOSE_HTTP_TIMEOUT')} s, BuildKit off", None


def check_harbor_patches(s):
    files = sorted(glob.glob(os.path.expanduser(s["harbor_docker_glob"])))
    if not files:
        return CRITICAL, "Harbor is not installed (no environments/docker/docker.py)", \
            "uv tool install harbor, then re-apply common/trial/harbor/patch_*.sh"
    text = Path(files[-1]).read_text(errors="replace")
    missing = []
    if 'if "down" in full_command' not in text:
        missing.append(("teardown", "bash common/trial/harbor/patch_teardown.sh"))
    if "timeout=300" not in text:
        missing.append(("kernel-probe timeout 300 s", "bash common/trial/harbor/patch_probe_timeout.sh"))
    if missing:
        return NEEDS, "Harbor patch missing: " + ", ".join(n for n, _ in missing), " && ".join(c for _, c in missing)
    return OK, "teardown patch and 300 s kernel-probe timeout present", None


def check_image_reuse(s):
    ext = paths.COMMON / "harbor_ext"
    problems = []
    if not (ext / "cwe_reuse_env.py").is_file():
        problems.append("common/harbor_ext/cwe_reuse_env.py missing")
    for f in (paths.COMMON / "trial" / "run_trial.sh", paths.COMMON / "gate" / "gate.py"):
        if f.is_file() and "harbor_ext" not in f.read_text(errors="replace"):
            problems.append(f"{f.name} does not use harbor_ext")
    if os.environ.get("CWE_IMAGE_REUSE") == "0":
        problems.append("CWE_IMAGE_REUSE=0 in this environment")
    if problems:
        return NEEDS, "; ".join(problems), "deploy common/harbor_ext with run_trial.sh and gate.py; unset CWE_IMAGE_REUSE"
    return OK, "image reuse wired into trials, gates and regrades", None


def check_gate_limits(s):
    v = env_values(read(s["limits_env"]))
    missing = [k for k in GATE_KEYS if not v.get(k)]
    if missing:
        return NEEDS, f"{s['limits_env']} lacks {', '.join(missing)}: built-in defaults apply", \
            f"add {', '.join(k + '=<n>' for k in missing)} to {s['limits_env']}"
    return OK, ", ".join(f"{k}={v[k]}" for k in GATE_KEYS), None


def check_model_keys(s):
    found = []
    for f in s["model_env"]:
        v = env_values(read(f))
        if any(re.search(r"KEY", k) and val for k, val in v.items()):
            found.append(os.path.expanduser(f))
    if not found:
        return CRITICAL, "no model env file with a non-empty *KEY* setting", \
            "create ~/.config/cwe/models.env from common/launch/models.env.example"
    return OK, "keys present in " + ", ".join(found) + " (values not shown)", None


def check_versions(s, runner):
    parts = []
    for name, cmd in (("harbor", ["harbor", "--version"]), ("uv", ["uv", "--version"])):
        rc, out = runner(cmd, 20)
        v = re.search(r"\d+\.\d+[\w.+-]*", out or "") if rc == 0 else None
        parts.append(f"{name} {v.group(0) if v else 'unavailable'}")
    return OK, ", ".join(parts), None


def check_headroom(s, cfg):
    m = procs.headroom(str(paths.ROOT))
    over = procs.over_limits(m, cfg["limits"])
    if over:
        return CRITICAL, "; ".join(over), "free space or lower the load before launching (hourly cleanup, cweq status)"
    return OK, (f"free disk {m['free_disk_gb']} GB, memory {m['mem_available_gb']} GB, load {m['load']}, "
                f"/tmp inodes {m['tmp_inode_pct']}%"), None


def check_queue_loops(s, proc_list):
    cmds = [" ".join(argv) for _p, argv, _c, _e in proc_list]
    have = {k: any(f"cweq.py {k}" in c for c in cmds) for k in ("reconcile", "dispatch", "monitor")}
    missing = [k for k, v in have.items() if not v]
    if missing:
        return OK, "not running: " + ", ".join(missing) + " (start them as in docs/WORK-QUEUE.md, Operations)", None
    return OK, "reconcile, dispatch and monitor running", None


def check_frozen(scanner):
    fz = scanner()
    if fz:
        names = ", ".join(sorted({f"{p.get('task') or '?'} (pid {p['pid']})" for p in fz}))[:300]
        return CRITICAL, f"{len(fz)} pipeline process(es) stopped by SIGSTOP: {names}", \
            "resume them (kill -CONT) or stop them; to pause, stop new starts (queue enabled = false), never freeze"
    return OK, "no builder, gate or trial is stopped", None


def run_all(cfg, runner=run, proc_list=None, frozen_scan=None):
    """[(name, status, detail, fix)]."""
    s = settings(cfg)
    plist = procs.list_processes() if proc_list is None else proc_list
    checks = [("docker_daemon", lambda: check_docker_daemon(s, runner)),
              ("daemon_json", lambda: check_daemon_json(s)),
              ("docker_tuning", lambda: check_docker_tuning(s)),
              ("harbor_patches", lambda: check_harbor_patches(s)),
              ("image_reuse", lambda: check_image_reuse(s)),
              ("gate_limits", lambda: check_gate_limits(s)),
              ("model_keys", lambda: check_model_keys(s)),
              ("versions", lambda: check_versions(s, runner)),
              ("headroom", lambda: check_headroom(s, cfg)),
              ("queue_loops", lambda: check_queue_loops(s, plist)),
              ("frozen_processes", lambda: check_frozen(frozen_scan or _frozen_scan))]
    out = []
    for name, fn in checks:
        try:
            st, detail, fix = fn()
        except Exception as e:                            # a broken check is reported, never hidden
            st, detail, fix = NEEDS, f"check failed: {type(e).__name__}: {e}", None
        out.append((name, st, detail, fix))
    return out


def exit_code(results):
    states = {st for _n, st, _d, _f in results}
    return 2 if CRITICAL in states else 1 if NEEDS in states else 0


def report(results, out=print):
    for name, st, detail, fix in results:
        out(f"{st:<15} {name:<15} {detail}")
        if fix:
            out(f"{'':<15} {'':<15} -> {fix}")
    code = exit_code(results)
    out("preflight: " + ("CRITICAL" if code == 2 else "OK, with settings to apply" if code == 1 else "OK"))
    return code
