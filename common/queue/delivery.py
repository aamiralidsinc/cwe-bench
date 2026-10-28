"""Delivery: everything up to the push, as a queue job, after the owner's KEEP.

  D1 delivery_prep   a task whose HUMAN-DECISION.md says KEEP (current, taskstate stage `kept`), that is a both-model
                     breaker in the audited ledger (DeepSeek and MiMo both failed), and that is not in the delivery
                     register (build/audit/delivered.tsv). One job per decision (args: the decision and its date).
                     A kept task that is not a both-model breaker is reported, never prepared: only both-model
                     breakers are delivered.

The job runs `delivery.py prep <slug>`:
  0. export_delivery.py first runs the file-time leak check (common/gate/env_leak_check.py) on the task's agent image
     and refuses a task that is not clean (exit 4, nothing exported; owner decision 2026-10-28).
  1. common/util/export_delivery.py exports the task package and its counted rollouts into
     <out_dir>/<UTC>-<slug>/ ([delivery] out_dir, default ~/.tb-graders/cwe/deliveries). The export redacts every model
     key value and refuses to run without them.
  2. tasks/<name>/task.toml gets `name = "cwe-bench/<name>"`; nothing else in the package changes.
  3. A pattern scan of the whole export (provider keys, cloud keys, private keys, *_API_KEY= assignments) must
     find nothing.
  4. ready.json records the proposed name (repo + flaw, kebab-case; the orchestrator may change it), the README row,
     the rollouts per model, the runs skipped for lack of a trajectory, and both scan results. Exit 0 = ready.

It never touches the delivery repository: the commit and push stay with a person. After the push,
`cweq delivered <slug> <name> <commit>` appends the register row(s) and the DELIVERED line in HUMAN-DECISION.md.
"""
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import qdb  # noqa: E402
import taskstate  # noqa: E402
import markers  # noqa: E402  (task-folder markers: common/markers.py; on sys.path via taskstate)
from taskstate import paths  # noqa: E402

KIND = "delivery_prep"
REGISTER_HEAD = ("# Tasks delivered to the delivery repository. One row per build slug; -control rows are the stacking\n"
                 "# control of the same task.\n# slug\tdelivered_as\tclient_commit\tdate\n")
DEFAULTS = {"out_dir": "~/.tb-graders/cwe/deliveries", "repo_label": "marahassan8/cwe-bench main"}
PATTERNS = re.compile(r"(?<![A-Za-z0-9])sk-[A-Za-z0-9_-]{32,}|(?<![A-Za-z0-9])AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{30,}|"
                      r"-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY|"
                      r"(?:ANTHROPIC|OPENAI|DEEPSEEK|MIMO|XIAOMI)[A-Z_]*(?:API_KEY|AUTH_TOKEN)[\"']?[=:] ?[\"']?[A-Za-z0-9_-]{16,}")
# `sk-` must start a word (file names such as task-... are not keys). Upstream test fixtures that look like keys (certificates, sample tokens) live under tests/; the pattern scan reports
# them separately and they do not block.
CWE_WORDS = {
    "CWE-20": "input-validation", "CWE-22": "path-traversal", "CWE-23": "path-traversal", "CWE-59": "symlink-following",
    "CWE-78": "command-injection", "CWE-79": "xss", "CWE-88": "argument-injection", "CWE-89": "sql-injection",
    "CWE-94": "code-injection", "CWE-200": "information-exposure", "CWE-201": "information-exposure",
    "CWE-209": "error-information-exposure", "CWE-284": "access-control-bypass", "CWE-285": "authorization-bypass",
    "CWE-287": "authentication-bypass", "CWE-306": "missing-authentication", "CWE-352": "csrf",
    "CWE-400": "resource-exhaustion", "CWE-407": "quadratic-complexity", "CWE-444": "request-smuggling",
    "CWE-476": "null-dereference", "CWE-502": "unsafe-deserialization", "CWE-522": "credential-exposure",
    "CWE-532": "secret-in-logs", "CWE-601": "open-redirect", "CWE-611": "xxe", "CWE-639": "idor",
    "CWE-770": "resource-exhaustion", "CWE-862": "missing-authorization", "CWE-863": "authorization-bypass",
    "CWE-918": "ssrf", "CWE-1321": "prototype-pollution", "CWE-1333": "redos",
}


def settings(cfg):
    out = dict(DEFAULTS)
    out.update((cfg or {}).get("delivery", {}))
    out["out_dir"] = os.path.expanduser(out["out_dir"])
    return out


def register_path():
    return paths.BUILD / "audit" / "delivered.tsv"


def delivered_names():
    out = {}
    try:
        for line in register_path().read_text().splitlines():
            c = line.split("\t")
            if line.startswith("#") or len(c) < 2:
                continue
            out[c[0].strip()] = c[1].strip()
    except OSError:
        pass
    return out


def both_failed(t):
    return all(t["models"].get(m, {}).get("ledger") == "failed" for m in taskstate.MODELS)


def plan(states):
    """([{kind, task, args}], notes) for every kept, undelivered task."""
    jobs, notes = [], []
    for slug, t in sorted(states.items()):
        if t["stage"] != "kept":
            continue
        if not both_failed(t):
            notes.append(f"{slug}: kept, but not a both-model breaker (only both-model breakers are delivered)")
            continue
        jobs.append({"kind": KIND, "task": slug, "args": {"decision": t["decision"]}})
    return jobs, notes


def reconcile(conn, cfg, states, dry_run=False):
    """One pass of D1. Returns [{task, stage, want, notes}] like the other phases."""
    if not (cfg.get("delivery", {}) or {}).get("enabled", True):
        return []
    jobs, notes = plan(states)
    out = []
    for w in jobs:
        if not dry_run:
            w["id"], _ = qdb.enqueue(conn, KIND, w["task"], w["args"], priority=cfg["priority"].get(KIND, 0),
                                     max_attempts=cfg["max_attempts"].get(KIND, 1), origin="reconciler")
        out.append({"task": w["task"], "stage": "kept", "want": [w], "notes": []})
    if notes:
        out.append({"task": "_delivery", "stage": "delivery", "want": [], "notes": notes})
    return out


def command(row, cfg):
    """argv for a delivery_prep job (worker.py), or None for other kinds."""
    if row["kind"] != KIND:
        return None
    return [sys.executable, "-I", str(Path(__file__).resolve()), "prep", row["task"]]


# ---------- the prep step

def _meta(slug):
    import tomllib
    try:
        return tomllib.loads((paths.TASKS / slug / "task.toml").read_text()).get("metadata", {})
    except (OSError, tomllib.TOMLDecodeError):
        return {}


def kebab(text):
    return re.sub(r"-{2,}", "-", re.sub(r"[^a-z0-9]+", "-", text.lower())).strip("-")


def title(slug):
    try:
        return (paths.TASKS / slug / "instruction.md").read_text().splitlines()[0].lstrip("# ").strip()
    except (OSError, IndexError):
        return ""


def propose_name(slug, taken=()):
    """<repo>-<flaw>: the upstream repository's name and the CWE's short name (else words from the report title)."""
    m = _meta(slug)
    repo = kebab((m.get("repo") or "").rstrip("/").split("/")[-1] or re.sub(r"^stk-|-(s\d|ds|ghsa\w+|\d+)$", "", slug))
    flaw = CWE_WORDS.get(str(m.get("cwe_id", "")).split(",")[0].strip())
    if not flaw:
        words = [w for w in kebab(title(slug)).split("-") if len(w) > 3][:3]
        flaw = "-".join(words) or "security-fix"
    name = f"{repo}-{flaw}"
    base, n = name, 2
    while name in set(taken):
        name, n = f"{base}-{n}", n + 1
    return name


def readme_row(name, slug):
    return f"| `{name}` | {title(slug)} |"


def pattern_scan(root):
    """[(relative file, under tests/)] for every file with a key-like string."""
    hits = []
    for p in Path(root).rglob("*"):
        if not p.is_file():
            continue
        try:
            t = p.read_text(errors="ignore")
        except OSError:
            continue
        if PATTERNS.search(t):
            rel = str(p.relative_to(root))
            hits.append((rel, "/tests/" in f"/{rel}"))
    return hits


def prep(slug, cfg, name=None, out_dir=None, export=None):
    """Run the export and checks for one task. Returns (exit code, ready dict)."""
    st = settings(cfg)
    taken = set(delivered_names().values())
    name = name or propose_name(slug, taken)
    out = Path(out_dir or Path(st["out_dir"]) / f"{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}-{slug}")
    out.mkdir(parents=True, exist_ok=True)
    argv = export or [sys.executable, "-I", str(paths.COMMON / "util" / "export_delivery.py"), str(out), slug,
                      "--name", f"{slug}={name}"]
    r = subprocess.run(argv, cwd=str(paths.ROOT), capture_output=True, text=True)
    ready = {"slug": slug, "name": name, "out": str(out), "readme_row": readme_row(name, slug),
             "export_exit": r.returncode, "export_tail": (r.stdout + r.stderr).strip().splitlines()[-3:],
             "prepared": qdb.utc(), "ready": False}
    rep = (out / "EXPORT-REPORT.md").read_text() if (out / "EXPORT-REPORT.md").exists() else ""
    m = re.search(r"## Secret scan: (\d+) key values checked, (\d+) files redacted", rep)
    ready["secret_scan"] = {"key_values": int(m.group(1)), "files_redacted": int(m.group(2))} if m else None
    ready["skipped_runs"] = len(re.findall(r"(?m)^- .*no agent/trajectory\.json", rep))
    traj = out / "trajectory" / name
    ready["rollouts"] = {d.name: len([x for x in d.iterdir() if x.is_dir()]) for d in sorted(traj.iterdir())} \
        if traj.is_dir() else {}
    toml = out / "tasks" / name / "task.toml"
    if toml.exists():
        t = toml.read_text()
        t2, k = re.subn(r'(?m)^name = "cwe-bench/[^"]+"', f'name = "cwe-bench/{name}"', t, count=1)
        if k:
            toml.write_text(t2)
        ready["renamed"] = bool(k)
    hits = pattern_scan(out)
    ready["pattern_hits"] = [h for h, in_tests in hits if not in_tests]
    ready["pattern_hits_in_tests"] = [h for h, in_tests in hits if in_tests]
    problems = []
    if r.returncode == 4:
        # export_delivery.py refuses a task whose agent image leaks file times, or that could not be checked
        # (owner decision 2026-10-28: a hard refusal at delivery)
        ready["leak_refusal"] = [l.strip() for l in (r.stdout + r.stderr).splitlines() if "leak check" in l]
        problems.append("refused: file-time leak check not clean (" + "; ".join(ready["leak_refusal"])[:300] + ")")
    elif r.returncode != 0:
        problems.append(f"export exit {r.returncode}")
    if not ready["secret_scan"] or ready["secret_scan"]["key_values"] == 0:
        problems.append("secret scan did not run")
    if ready["pattern_hits"]:
        problems.append(f"{len(ready['pattern_hits'])} files with key-like strings outside tests/")
    if not toml.exists():
        problems.append("no task package in the export")
    ready["problems"] = problems
    ready["ready"] = not problems
    (out / "ready.json").write_text(json.dumps(ready, indent=2) + "\n")
    print(json.dumps({k: ready[k] for k in ("slug", "name", "out", "ready", "problems", "rollouts")}))
    return (0 if ready["ready"] else 3), ready


def prepared():
    """[ready dict] of every prepared package, newest first."""
    out = []
    root = Path(settings({})["out_dir"])
    for f in sorted(root.glob("*/ready.json"), reverse=True):
        try:
            out.append(json.loads(f.read_text()))
        except (OSError, ValueError):
            pass
    return out


# ---------- after the push

def record_delivered(slug, name, commit, date=None, note="", repo_label=None):
    """Append the register row(s) (the task, and its -control when one exists) and the DELIVERED line. Idempotent."""
    date = date or time.strftime("%Y-%m-%d", time.gmtime())
    label = repo_label or DEFAULTS["repo_label"]
    reg = register_path()
    reg.parent.mkdir(parents=True, exist_ok=True)
    have = delivered_names()
    rows = [slug] + ([f"{slug}-control"] if (paths.TASKS / f"{slug}-control").is_dir() else [])
    added = []
    with open(reg, "a") as f:
        if reg.stat().st_size == 0:
            f.write(REGISTER_HEAD)
        for s in rows:
            if s not in have:
                f.write(f"{s}\t{name}\t{commit}\t{date}\n")
                added.append(s)
    dec = markers.path(paths.BUILD / slug, "HUMAN-DECISION.md")
    line = f"DELIVERED: {date} to {label}, commit {commit}, as tasks/{name}" + (f" ({note})" if note else "")
    text = markers.read_text(dec)
    wrote_line = False
    if f"commit {commit}" not in text:
        markers.write_atomic(dec, text + ("" if text.endswith("\n") or not text else "\n") + line + "\n")
        wrote_line = True
    return added, wrote_line


def main(argv=None):
    import argparse
    import config
    ap = argparse.ArgumentParser(prog="delivery.py")
    ap.add_argument("--config")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("prep")
    p.add_argument("slug")
    p.add_argument("--name")
    p.add_argument("--out")
    a = ap.parse_args(argv)
    cfg = config.load(a.config)
    rc, _ = prep(a.slug, cfg, name=a.name, out_dir=a.out)
    return rc


if __name__ == "__main__":
    sys.exit(main())
