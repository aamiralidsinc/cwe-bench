#!/usr/bin/env python3
"""Export tasks plus their trial rollouts in the layout the client asked for (Klavis, 2026-10-25):

    <out>/tasks/<task_name>/                       the Harbor task package (as in tasks/<slug>/)
    <out>/trajectory/<task_name>/<model_name>/rollout<N>/
        reward.json        required: the grading the verdict uses (a regrade replaces the original)
        trajectory.json    required: the agent trajectory, ATIF-v1.7 (Harbor's agent/trajectory.json)
        verifier/          optional: the verifier logs of that grading

    python3 common/util/export_delivery.py <out_dir> <slug> [<slug> ...] [--name slug=delivered-name ...]

Which runs: every run the ledger (common/audit/audit_results.py) counts for the task: graded, not excluded
(build/audit/excluded_runs.tsv), not contaminated, not a harness fault (reviews.tsv), and not an untrusted
audit. Rollouts are numbered per model in start order. A run without agent/trajectory.json (for example the
precision_validation runs imported from GitHub Actions) cannot meet the "required" rule: it is skipped and
listed in <out>/EXPORT-REPORT.md. Each trajectory is checked with Harbor's own validator when available.
Every key value in the model env files is redacted from the export ([REDACTED]); the report lists the files.
Read-only on the sources; writes only under <out_dir>.
"""
import argparse
import csv
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(next(p for p in Path(__file__).resolve().parents if (p / ".cwe-bench-root").is_file()) / "common"))
import paths  # noqa: E402

sys.path.insert(0, str(paths.AUDIT_TOOLS))
import audit_results as ar  # noqa: E402  (same exclusion rules as the ledger)

MODEL_NAMES = {"deepseek": "deepseek-v4.1-flash", "mimo": "mimo-v2.6-pro"}
HARBOR_PY = Path.home() / ".local/share/uv/tools/harbor/bin/python"
SKIP_TASK_FILES = {".git"}


def counted_runs(slug, trials):
    tainted, decided, excl = ar.contaminated(), ar.reviews(), ar.excluded_runs()
    out = []
    for t in trials:
        if t["task"] != slug or not ar.model_key(t["model"]):
            continue
        if t["reward"] in ("", None):
            continue
        key = (t["job"], t["trial"])
        if key in tainted or key in excl:
            continue
        if t["flags"] and decided.get((t["job"], t["trial"], t["grading"])) != "model":
            continue
        state = ar.postmortem_state(t["job"], t["trial"], t["grading"])
        if state == "untrusted" or (state == "awaiting" and float(t["reward"]) != 1.0):
            continue
        out.append(t)
    return sorted(out, key=lambda t: t["start_utc"])


KEY_FILES = [Path.home() / ".config/cwe/models.env", Path.home() / ".tb-graders/cwe/models.env"]


def secret_values():
    """Values of every *KEY*/*TOKEN*/*SECRET* setting in the model env files (never printed)."""
    vals = set()
    for f in KEY_FILES:
        if f.is_file():
            for line in f.read_text().splitlines():
                m = re.match(r"(?:export )?[A-Z_]*(?:KEY|TOKEN|SECRET)[A-Z_]*=(.*)", line.strip())
                if m and len(m.group(1).strip().strip("\"'")) > 12:
                    vals.add(m.group(1).strip().strip("\"'"))
    return vals


def redact_tree(root, vals):
    """Replace every secret value under root with [REDACTED] (an agent that prints its environment puts the
    provider key in its trajectory). Returns the files changed."""
    changed = []
    for p in Path(root).rglob("*"):
        if not p.is_file():
            continue
        try:
            t = p.read_text()
        except (UnicodeDecodeError, OSError):
            continue
        t2 = t
        for v in vals:
            t2 = t2.replace(v, "[REDACTED]")
        if t2 != t:
            p.write_text(t2)
            changed.append(str(p.relative_to(root)))
    return changed


def validate(traj):
    if not HARBOR_PY.exists():
        return "not checked (harbor not installed here)"
    r = subprocess.run([str(HARBOR_PY), "-c",
                        "import sys; from harbor.utils.trajectory_validator import validate_trajectory as v; "
                        "print('valid' if v(sys.argv[1]) else 'INVALID')", str(traj)],
                       capture_output=True, text=True, timeout=300)
    if r.stdout.strip():
        return r.stdout.strip().splitlines()[-1]
    return "INVALID: " + ((r.stderr.strip().splitlines() or ["?"])[-1])[:200]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("slugs", nargs="+")
    ap.add_argument("--name", action="append", default=[], help="slug=delivered-task-name")
    a = ap.parse_args()
    names = dict(n.split("=", 1) for n in a.name)
    out = Path(a.out)
    trials = list(csv.DictReader(open(paths.AUDIT_DIR / "trials.tsv"), delimiter="\t"))
    report = ["# Export report", "", "| task | model | rollout | job/trial | reward | trajectory |", "|---|---|---|---|---|---|"]
    skipped = []
    for slug in a.slugs:
        name = names.get(slug, slug)
        src = paths.TASKS / slug
        if not (src / "task.toml").is_file():
            sys.exit(f"no task package at {src}")
        dst = out / "tasks" / name
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src, dst, ignore=shutil.ignore_patterns(*SKIP_TASK_FILES))
        n = {}
        for t in counted_runs(slug, trials):
            mk = ar.model_key(t["model"])
            d = ar.JOBS / t["job"] / t["trial"]
            traj = d / "agent" / "trajectory.json"
            if not traj.is_file():
                skipped.append(f"{slug} {mk} {t['job']}/{t['trial']} (reward {t['reward']}): no agent/trajectory.json")
                continue
            n[mk] = n.get(mk, 0) + 1
            r = out / "trajectory" / name / MODEL_NAMES[mk] / f"rollout{n[mk]}"
            r.mkdir(parents=True, exist_ok=True)
            g = d if t["grading"] == "original" else d / t["grading"]
            (r / "reward.json").write_text(json.dumps({"reward": float(t["reward"])}))
            shutil.copy2(traj, r / "trajectory.json")
            if (g / "verifier").is_dir():
                shutil.copytree(g / "verifier", r / "verifier", dirs_exist_ok=True)
            v = validate(r / "trajectory.json")
            report.append(f"| {name} | {MODEL_NAMES[mk]} | rollout{n[mk]} | {t['job']}/{t['trial']} | {t['reward']} | {v} |")
        print(f"{name}: " + ", ".join(f"{MODEL_NAMES[k]} {v}" for k, v in n.items()))
    if skipped:
        report += ["", "## Skipped (no trajectory)", ""] + [f"- {s}" for s in skipped]
    vals = secret_values()
    if not vals:
        sys.exit("secret scan impossible: no key values found in " + ", ".join(map(str, KEY_FILES)))
    red = redact_tree(out, vals)
    report += ["", f"## Secret scan: {len(vals)} key values checked, {len(red)} files redacted", ""] + [f"- {r}" for r in red]
    (out / "EXPORT-REPORT.md").write_text("\n".join(report) + "\n")
    print(f"wrote {out} ({len(skipped)} runs skipped, see EXPORT-REPORT.md)")


if __name__ == "__main__":
    main()
