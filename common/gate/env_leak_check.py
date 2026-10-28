#!/usr/bin/env python3
"""env_leak_check.py: does the agent's starting state show where the builder changed code?

    python3 common/gate/env_leak_check.py <task_dir> [<agent-image>] [--reset] [--json]

<agent-image> defaults to the task's reuse tag (cwe-reuse/<task>:env-<hash>, common/harbor_ext/cwe_reuse_tag.py),
the image every gate run and trial starts. Exit 0 = clean, 1 = LEAK, 2 = could not check.

It runs leak_probe.py (same folder) as root in a throwaway container of the image (--network none, probe folder
mounted read-only, removed afterwards) and judges the result. --reset first applies the harness file-time reset
that every agent container gets at start (common/harbor_ext/cwe_tree_reset.py), so it shows what an agent in a
trial sees.

LEAK when any of these points at the files in environment/*.patch (the injection) or solution/*.patch:
  T1 mtime/atime   the patched files sit in their own time group (>= half of a non-majority mtime value is patched
                   files): what `ls -lt`, `find -newer`, `stat` show at a glance
  T2 ctime         the same for ctime (patched files extracted from a later image layer than the rest)
  T3 dir mtime     the folders holding patched files share a non-majority mtime of their own
  T4 index mtime   the git baseline's index (.git/index) records the patched files with their own time
  G1 git           the baseline has uncommitted tracked changes, more than one commit, a stash or other branches
  L1 leftovers     *.orig / *.rej files in the tree
  P1 pristine copy a file anywhere in the image equals the pre-injection version of a patched file
WARN when the tracked files carry more than one distinct mtime at all (after B2b they carry one).

Where it runs (owner decisions 2026-10-28, reports/reward-hacking.md):
  gate     the nop stage runs it once the image exists: a WARNING in the report, permanently, never a failure
  delivery common/util/export_delivery.py refuses a task unless the check is clean
From the investigation's tools/env_leak_check.py (build/audit/timestamp-leak-20261028/).
"""
import argparse
import glob
import json
import os
import shutil
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
HARBOR_EXT = HERE.parent / "harbor_ext"
if str(HARBOR_EXT) not in sys.path:
    sys.path.insert(0, str(HARBOR_EXT))
import cwe_reuse_tag  # noqa: E402
import cwe_tree_reset  # noqa: E402

CLEAN, LEAK, ERROR = "clean", "leak", "error"


def default_image(task_dir) -> str:
    return cwe_reuse_tag.reuse_tag(Path(task_dir) / "environment")


def _inputs(task_dir: Path, folder: Path):
    env = task_dir / "environment"
    with open(folder / "inj.patch", "w") as f:
        for fp in sorted(glob.glob(str(env) + "/**/*.patch", recursive=True) +
                         glob.glob(str(env) + "/**/*.diff", recursive=True)):
            f.write(open(fp, errors="replace").read() + "\n")
    sol = set()
    for fp in glob.glob(str(task_dir / "solution" / "*.patch")):
        for line in open(fp, errors="replace"):
            if line.startswith("+++ ") and "/dev/null" not in line:
                p = line[4:].split("\t")[0].strip()
                sol.add(p[2:] if p[:2] in ("a/", "b/") else p)
    (folder / "sol.txt").write_text("\n".join(sorted(sol)) + "\n")
    shutil.copy(HERE / "leak_probe.py", folder / "probe.py")
    os.chmod(folder, 0o755)
    for x in folder.iterdir():
        os.chmod(x, 0o644)


def _docker(*args, timeout=900):
    return subprocess.run(["docker", *args], capture_output=True, text=True, timeout=timeout)


def probe(task_dir, image, reset=False) -> dict:
    """Run the probe; returns the probe's JSON plus '_reset' (the reset's output) or raises RuntimeError."""
    task_dir = Path(task_dir)
    folder = Path(tempfile.mkdtemp(prefix="leakchk."))
    name = f"cwe-leakcheck-{uuid.uuid4().hex[:10]}"
    try:
        _inputs(task_dir, folder)
        r = _docker("run", "-d", "--name", name, "--network", "none", "--user", "0", "--cpus", "1", "--memory", "3g",
                    "--label", "cwe.started_by=script", "--label", "cwe.kind=leak_check",
                    "--label", f"cwe.task={task_dir.name}",
                    "-v", f"{folder}:/probe:ro", "--entrypoint", "sleep", image, "infinity", timeout=300)
        if r.returncode != 0:
            raise RuntimeError(f"docker run failed: {(r.stderr or r.stdout).strip()[-400:]}")
        reset_out = None
        if reset:
            r = _docker("exec", "-u", "0", name, "bash", "-c", cwe_tree_reset.root_script())
            reset_out = (r.stdout + r.stderr).strip()
            if r.returncode != 0:
                raise RuntimeError(f"reset failed (exit {r.returncode}): {reset_out[-400:]}")
            info = cwe_tree_reset.parse_summary(reset_out)
            if info:
                r = _docker("exec", "-u", info.get("owner", "0:0"), name, "bash", "-c",
                            cwe_tree_reset.refresh_script(info["root"]))
                reset_out += " | " + (r.stdout + r.stderr).strip()
                if r.returncode != 0:
                    raise RuntimeError(f"index refresh failed (exit {r.returncode}): {reset_out[-400:]}")
        r = _docker("exec", "-u", "0", name, "python3", "/probe/probe.py")
        if r.returncode != 0:
            raise RuntimeError(f"probe exit {r.returncode}: {r.stderr.strip()[-400:]}")
        d = json.loads(r.stdout)
        d["_reset"] = reset_out
        return d
    finally:
        _docker("rm", "-f", name, timeout=120)
        shutil.rmtree(folder, ignore_errors=True)


def judge(d: dict):
    """(leaks, warns) from the probe's JSON."""
    leaks, warns = [], []

    def pure(x):
        return (x or {}).get("pure_recall") or 0

    if d.get("n_injected"):
        if pure(d["mtime"]["cohort"]) >= 0.5 or pure(d["atime"]["cohort"]) >= 0.5:
            leaks.append(f"T1 mtime: patched files form their own time group "
                         f"({(d['mtime']['cohort'] or {}).get('injected_cohorts', [])[:3]})")
        if pure(d["ctime"]["cohort"]) >= 0.5:
            leaks.append("T2 ctime: patched files come from a later image layer")
        if pure(d.get("dir_mtime_cohort")) >= 0.5:
            leaks.append("T3 dir mtime: folders of patched files share their own time")
        if pure(d.get("index_mtime_cohort")) >= 0.5:
            leaks.append("T4 index mtime: .git/index records the patched files with their own time")
    elif pure(d.get("mtime_sol_cohort")) >= 0.5:
        leaks.append("T1 mtime: files the reference fix touches form their own time group")
    g = d.get("git") or {}
    if d.get("git_baseline"):
        dirty = [l for l in g.get("status_sample", []) if not l.startswith("??")]
        if dirty or g.get("diff_names") or (g.get("commits") or 0) > 1 or g.get("stash") or \
                len([b for b in g.get("branches", []) if b != "*"]) > 1:
            leaks.append(f"G1 git: baseline not a single clean commit ({g})")
    lo = [x for x in d.get("leftovers_workspace", []) if x.endswith((".orig", ".rej"))]
    if lo:
        leaks.append(f"L1 leftovers: {lo[:5]}")
    if d.get("pristine_copies"):
        leaks.append(f"P1 pristine copy: {d['pristine_copies'][:3]}")
    if (d["mtime"]["cohort"] or {}).get("distinct_values", 1) > 1:
        warns.append(f"tracked files carry {d['mtime']['cohort']['distinct_values']} distinct mtimes "
                     f"(expected 1 after B2b)")
    return leaks, warns


def check(task_dir, image=None, reset=False) -> dict:
    """{'status': clean|leak|error, 'leaks': [...], 'warns': [...], 'summary': str, 'image': str}. Never raises."""
    task_dir = Path(task_dir)
    try:
        image = image or default_image(task_dir)
    except Exception as e:
        return {"status": ERROR, "leaks": [], "warns": [], "image": image,
                "summary": f"could not check: no image tag ({type(e).__name__}: {e})"}
    out = {"image": image, "reset": bool(reset), "leaks": [], "warns": []}
    if _docker("image", "inspect", "--format", "{{.Id}}", image, timeout=120).returncode != 0:
        return {**out, "status": ERROR, "summary": f"could not check: image {image} not found"}
    try:
        d = probe(task_dir, image, reset=reset)
    except Exception as e:
        return {**out, "status": ERROR, "summary": f"could not check: {type(e).__name__}: {e}"}
    leaks, warns = judge(d)
    targets = "injection" if d.get("n_injected") else "solution"
    n = d.get("n_injected") or d.get("n_sol_existing")
    out.update(status=LEAK if leaks else CLEAN, leaks=leaks, warns=warns, reset_output=d.get("_reset"),
               summary=("LEAK" if leaks else "clean") + f" ({targets} files: {n}, tracked {d.get('n_tracked')})")
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("task_dir")
    ap.add_argument("image", nargs="?")
    ap.add_argument("--reset", action="store_true", help="apply the harness reset (trial start) before probing")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    r = check(a.task_dir, a.image, reset=a.reset)
    if a.json:
        print(json.dumps(r, indent=1))
    else:
        for w in r["warns"]:
            print("WARN " + w)
        for l in r["leaks"]:
            print("LEAK " + l)
        print(r["summary"] + f" [image {r.get('image')}{', after harness reset' if a.reset else ''}]")
    return {CLEAN: 0, LEAK: 1}.get(r["status"], 2)


if __name__ == "__main__":
    sys.exit(main())
