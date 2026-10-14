#!/usr/bin/env python3
"""Deterministic acceptance gate for one built task.

    gate.py <slug> [--only static|nop|oracle|patches] [--keep-jobs]

Layout it expects (paths relative to cwe-bench/):
    tasks/<slug>/   instruction.md task.toml environment/ solution/ tests/
    build/<slug>/   manifest.json  checks/*.patch

Checks, in order (it stops at the first failing group):
  static   required files, metadata, agent layer, no leaks in instruction.md
  nop      untouched vulnerable code: every security test FAILS, every
           functional test PASSES
  oracle   reference fix, run twice: reward 1.0 and identical results
  patches  every patch listed in manifest["patch_checks"] behaves as declared:
             security_fail    at least one security test fails, functional all pass
             functional_fail  at least one functional test fails
             pass             reward 1.0 (an independent correct fix)

The result is written to build/<slug>/gate_report.json. Exit code 0 = passed.
Decisions here are made by scripts only; no model judgement is involved.
"""
import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

try:
    import tomllib  # Python 3.11+
    def load_toml(text: str) -> dict:
        return tomllib.loads(text)
except ModuleNotFoundError:  # 3.9/3.10 host without tomllib
    def load_toml(text: str) -> dict:
        """Minimal reader for our own task.toml: flat tables of key = scalar.
        Enough for the metadata/verifier fields the gate inspects; not a full
        TOML parser."""
        import ast
        data = {}
        cur = data
        for raw in text.splitlines():
            line = raw.split("#", 1)[0].strip()
            if not line:
                continue
            if line.startswith("[") and line.endswith("]"):
                cur = data
                for part in line[1:-1].split("."):
                    cur = cur.setdefault(part.strip(), {})
                continue
            if "=" not in line:
                continue
            key, _, val = line.partition("=")
            key, val = key.strip(), val.strip()
            try:
                cur[key] = ast.literal_eval(val)
            except (ValueError, SyntaxError):
                cur[key] = val.strip('"').strip("'")
        return data

ROOT = Path(__file__).resolve().parent.parent
JOBS = Path.home() / ".tb-graders" / "cwe" / "gate-jobs"
REQUIRED = [
    "instruction.md",
    "task.toml",
    "environment/Dockerfile",
    "solution/solve.sh",
    "solution/fix.patch",
    "tests/test.sh",
    "tests/score.py",
]
META_KEYS = ["cwe_id", "language", "repo", "source", "entry_point"]
MIN_SECURITY, MIN_FUNCTIONAL = 4, 5
# Infrastructure errors worth one retry (Docker name lookups are flaky here).
RETRYABLE = ("NetworkConnectionError", "Could not resolve", "ENOTFOUND", "TLS handshake")


class GateFailure(Exception):
    pass


def run_harbor(task_dir: Path, agent: str, label: str) -> dict:
    """Run one Harbor trial and return {'reward', 'security', 'functional'}."""
    for attempt in (1, 2):
        name = f"{task_dir.name}-{label}-{int(time.time())}"
        cmd = ["harbor", "run", "-p", str(task_dir), "-a", agent, "-o", str(JOBS),
               "--job-name", name, "-y", "-q"]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        trials = [p for p in (JOBS / name).glob("*/") if (p / "result.json").exists()]
        if not trials:
            raise GateFailure(f"{label}: Harbor produced no trial ({proc.stdout[-400:]}{proc.stderr[-400:]})")
        trial = trials[0]
        result = json.loads((trial / "result.json").read_text())
        exc = result.get("exception_info")
        if exc:
            text = json.dumps(exc)
            if attempt == 1 and any(r in text for r in RETRYABLE):
                continue
            raise GateFailure(f"{label}: trial raised {exc.get('exception_type')}: "
                              f"{str(exc.get('exception_message'))[:300]}")
        detail = trial / "verifier" / "results.json"
        if not detail.exists():
            raise GateFailure(f"{label}: tests wrote no results.json (see {trial}/verifier)")
        data = json.loads(detail.read_text())
        data["trial_dir"] = str(trial)
        return data
    raise GateFailure(f"{label}: infrastructure error twice")


def failing(group: dict) -> list:
    return sorted(k for k, v in group.items() if v != "pass")


def check_static(task: Path, build: Path, manifest: dict) -> dict:
    problems = []
    for rel in REQUIRED:
        if not (task / rel).is_file():
            problems.append(f"missing {rel}")
    if problems:
        raise GateFailure("; ".join(problems))

    toml = load_toml((task / "task.toml").read_text())
    meta = toml.get("metadata", {})
    for key in META_KEYS:
        if not str(meta.get(key, "")).strip():
            problems.append(f"task.toml [metadata].{key} is empty")
    if meta.get("source") not in ("mined", "mined+injected", "injected", "stacking", "mined+stacking"):
        problems.append("task.toml [metadata].source must be mined, mined+injected, injected, stacking or mined+stacking")

    docker = (task / "environment/Dockerfile").read_text()
    if "claude-code-releases/bootstrap.sh" not in docker:
        problems.append("Dockerfile lacks the agent layer (harness/claude-code.Dockerfile.snippet)")
    if ".git" not in docker:
        problems.append("Dockerfile does not remove the repository's .git history")

    # Leaks: the report must not name the advisory, the fix, or where the fix goes.
    instr = (task / "instruction.md").read_text()
    low = instr.lower()
    leaks = [m for m in re.findall(r"CVE-\d{4}-\d+|GHSA-[0-9a-z-]{10,}", instr, flags=re.I)]
    for sha_key in ("fix_commit", "vulnerable_commit"):
        sha = str(meta.get(sha_key, ""))
        if len(sha) >= 7 and sha[:7].lower() in low:
            leaks.append(f"{sha_key} sha")
    fix = (task / "solution/fix.patch").read_text()
    for path in sorted(set(re.findall(r"^\+\+\+ b/(\S+)", fix, flags=re.M))):
        base = path.rsplit("/", 1)[-1]
        if path.lower() in low or re.search(rf"(?<![\w.]){re.escape(base.lower())}(?![\w])", low):
            leaks.append(f"file named in the fix: {base}")
    for term in manifest.get("leak_terms", []):
        if term and re.search(rf"(?<![\w]){re.escape(term.lower())}(?![\w])", low):
            leaks.append(f"leak term: {term}")
    if leaks:
        problems.append("instruction.md leaks: " + ", ".join(sorted(set(leaks))))
    if len(instr.split()) < 60:
        problems.append("instruction.md is under 60 words; a real report states impact and trigger")

    declared = {c.get("patch") for c in manifest.get("patch_checks", [])}
    for c in manifest.get("patch_checks", []):
        if not (build / "checks" / str(c.get("patch"))).is_file():
            problems.append(f"patch check file missing: checks/{c.get('patch')}")
    kinds = {c.get("expect") for c in manifest.get("patch_checks", [])}
    for need in ("security_fail", "functional_fail"):
        if need not in kinds:
            problems.append(f"manifest.patch_checks has no '{need}' patch")
    if problems:
        raise GateFailure("; ".join(problems))
    return {"ok": True, "patch_checks": sorted(declared)}


def check_nop(task: Path) -> dict:
    r = run_harbor(task, "nop", "nop")
    sec, fun = r["security"], r["functional"]
    problems = []
    if len(sec) < MIN_SECURITY:
        problems.append(f"only {len(sec)} security tests (need {MIN_SECURITY}+)")
    if len(fun) < MIN_FUNCTIONAL:
        problems.append(f"only {len(fun)} functional tests (need {MIN_FUNCTIONAL}+)")
    passing_sec = sorted(k for k, v in sec.items() if v == "pass")
    if passing_sec:
        problems.append(f"security tests that PASS on vulnerable code (not exploits): {passing_sec}")
    if failing(fun):
        problems.append(f"functional tests that fail on vulnerable code: {failing(fun)}")
    if problems:
        raise GateFailure("nop: " + "; ".join(problems))
    return {"ok": True, "security": len(sec), "functional": len(fun), "trial": r["trial_dir"]}


def check_oracle(task: Path) -> dict:
    runs = [run_harbor(task, "oracle", f"oracle{i}") for i in (1, 2)]
    for i, r in enumerate(runs, 1):
        bad = failing(r["security"]) + failing(r["functional"])
        if r["reward"] != 1.0 or bad:
            raise GateFailure(f"oracle run {i}: reward {r['reward']}, failing {bad}")
    if runs[0]["security"] != runs[1]["security"] or runs[0]["functional"] != runs[1]["functional"]:
        raise GateFailure("oracle: the two runs disagree (flaky tests)")
    return {"ok": True, "trials": [r["trial_dir"] for r in runs]}


def check_patches(task: Path, build: Path, manifest: dict) -> dict:
    out = {}
    for check in manifest.get("patch_checks", []):
        patch, expect = check["patch"], check["expect"]
        with tempfile.TemporaryDirectory(prefix="gate-") as tmp:
            variant = Path(tmp) / task.name
            shutil.copytree(task, variant)
            shutil.copy(build / "checks" / patch, variant / "solution" / "fix.patch")
            r = run_harbor(variant, "oracle", "chk-" + re.sub(r"\W+", "-", Path(patch).stem))
        sec_bad, fun_bad = failing(r["security"]), failing(r["functional"])
        if expect == "security_fail":
            ok = bool(sec_bad) and not fun_bad
            why = "must leave a security test failing while all functional tests pass"
        elif expect == "functional_fail":
            ok = bool(fun_bad)
            why = "must break at least one functional test"
        elif expect == "pass":
            ok = r["reward"] == 1.0
            why = "is a correct fix and must score 1.0"
        else:
            raise GateFailure(f"patches: unknown expect '{expect}' for {patch}")
        out[patch] = {"expect": expect, "ok": ok, "reward": r["reward"],
                      "security_failing": sec_bad, "functional_failing": fun_bad}
        if not ok:
            raise GateFailure(f"patches: {patch} {why}; got reward {r['reward']}, "
                              f"security failing {sec_bad}, functional failing {fun_bad}")
    return {"ok": True, "checks": out}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("slug")
    ap.add_argument("--only", choices=["static", "nop", "oracle", "patches"])
    ap.add_argument("--keep-jobs", action="store_true", help="kept for compatibility; jobs are always kept")
    args = ap.parse_args()

    task, build = ROOT / "tasks" / args.slug, ROOT / "build" / args.slug
    report = {"slug": args.slug, "started": time.strftime("%Y-%m-%dT%H:%M:%S"), "passed": False, "stages": {}}
    stages = ["static", "nop", "oracle", "patches"]
    if args.only:
        stages = [args.only]
    try:
        if not task.is_dir():
            raise GateFailure(f"no task directory {task}")
        mpath = build / "manifest.json"
        if not mpath.is_file():
            raise GateFailure(f"no manifest at {mpath}")
        manifest = json.loads(mpath.read_text())
        JOBS.mkdir(parents=True, exist_ok=True)
        for stage in stages:
            print(f"[gate] {args.slug}: {stage} ...", flush=True)
            if stage == "static":
                report["stages"][stage] = check_static(task, build, manifest)
            elif stage == "nop":
                report["stages"][stage] = check_nop(task)
            elif stage == "oracle":
                report["stages"][stage] = check_oracle(task)
            else:
                report["stages"][stage] = check_patches(task, build, manifest)
        report["passed"] = not args.only
        report["partial"] = bool(args.only)
    except GateFailure as e:
        report["failure"] = str(e)
        print(f"[gate] FAIL: {e}", file=sys.stderr)
    report["finished"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    if build.is_dir():
        (build / "gate_report.json").write_text(json.dumps(report, indent=1))
    ok = "failure" not in report
    print(f"[gate] {args.slug}: {'PASSED' if ok else 'FAILED'}"
          f"{' (' + args.only + ' only)' if args.only and ok else ''}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
