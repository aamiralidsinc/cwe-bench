#!/usr/bin/env python3
"""Write build/<slug>/trial_summary.md: per-trap, per-model results of the task's graded trial runs.

Input for the hardening agent: which model solved, and which traps each model's runs fixed or left
open. Reads the runs in ~/.tb-graders/cwe/jobs/<slug>-<model>-r*/ (the current version). When none
are there (already moved by snapshot_experiment.sh), it reads the latest experiment version's runs.
Never fails the caller: on any problem it writes what it can and exits 0.

  python3 -I pipeline/trial_summary.py SLUG
"""
import glob, json, os, re, sys

HOME = os.path.expanduser("~")
JOBS = os.path.join(HOME, ".tb-graders/cwe/jobs")
EXP = os.path.join(HOME, ".tb-graders/cwe/experiments")
ROOT = os.path.join(HOME, "cwe-bench")


def key(name):
    name = str(name).split("::")[-1].strip()
    name = re.split(r"\s|\(", name, maxsplit=1)[0]   # drop manifest notes after the test name
    name = re.sub(r"\[.*\]$", "", name)
    return re.sub(r"[^a-z0-9]", "", name.lower())


def run_dirs(slug):
    pat = re.compile(r"^" + re.escape(slug) + r"-(deepseek|mimo)-r\d+-\d{8}-\d{6}-n\d+$")
    def scan(base):
        out = []
        for jd in sorted(glob.glob(os.path.join(base, slug + "-*"))):
            m = pat.match(os.path.basename(jd))
            if not m:
                continue
            for td in sorted(glob.glob(os.path.join(jd, "*", ""))):
                if os.path.isdir(os.path.join(td, "verifier")):
                    out.append((m.group(1), os.path.basename(jd), td))
        return out
    found = scan(JOBS)
    if found:
        return found, "current runs (jobs/)"
    vers = sorted(glob.glob(os.path.join(EXP, slug, "v*-*", "runs")))
    if vers:
        return scan(vers[-1]), "latest archived version (" + os.path.basename(os.path.dirname(vers[-1])) + ")"
    return [], "none"


def reward_of(td):
    for p in (os.path.join(td, "verifier", "reward.json"),):
        try:
            return json.load(open(p)).get("reward")
        except Exception:
            pass
    try:
        r = json.load(open(os.path.join(td, "result.json")))
        return ((r.get("verifier_result") or {}).get("rewards") or {}).get("reward")
    except Exception:
        return None


def main(slug):
    out_path = os.path.join(ROOT, "build", slug, "trial_summary.md")
    traps, tmap = [], {}
    try:
        traps = json.load(open(os.path.join(ROOT, "build", slug, "manifest.json"))).get("traps") or []
    except Exception:
        pass
    for t in traps:
        if not isinstance(t, dict):
            continue
        tid = str(t.get("id") or t.get("name") or "?")
        for kind, field in (("security", "security_tests"), ("functional", "coupled_functional_tests")):
            for name in t.get(field) or []:
                tmap[(kind, key(name))] = tid
    runs, source = run_dirs(slug)
    lines = [f"# Trial summary for {slug}", "",
             f"Source: {source}. Raw verifier results, not audited. A run solves at reward 1.0.", ""]
    if not runs:
        lines += ["No graded trial runs were found for this task.", ""]
        open(out_path, "w").write("\n".join(lines))
        return
    per = {}  # trap -> model -> [failed runs, total runs]
    models = {}
    unmapped = {}
    lines += ["## Runs", "", "| Model | Run | Reward | Security passed | Functional passed | Failing tests |", "|---|---|---|---|---|---|"]
    for model, job, td in runs:
        rw = reward_of(td)
        try:
            res = json.load(open(os.path.join(td, "verifier", "results.json")))
        except Exception:
            res = {}
        sec, fun = res.get("security") or {}, res.get("functional") or {}
        models.setdefault(model, []).append(rw)
        failing = [("security", n) for n, v in sec.items() if v != "pass"] + \
                  [("functional", n) for n, v in fun.items() if v != "pass"]
        hit = set()
        for kind, name in failing:
            k = key(name)
            tid = tmap.get((kind, k)) or next((v for (kk, tk), v in tmap.items()
                                               if kk == kind and tk and (tk.endswith(k[-30:]) or k.endswith(tk[-30:]))), None)
            if tid:
                hit.add(tid)
            else:
                unmapped[name] = unmapped.get(name, 0) + 1
        for t in traps:
            if not isinstance(t, dict):
                continue
            tid = str(t.get("id") or t.get("name") or "?")
            c = per.setdefault(tid, {}).setdefault(model, [0, 0])
            c[1] += 1
            if tid in hit:
                c[0] += 1
        sp = f"{sum(v == 'pass' for v in sec.values())}/{len(sec)}" if sec else "-"
        fp = f"{sum(v == 'pass' for v in fun.values())}/{len(fun)}" if fun else "-"
        lines.append(f"| {model} | {job} | {rw} | {sp} | {fp} | {len(failing)} |")
    lines += ["", "## Who solved", ""]
    for model, rws in sorted(models.items()):
        solved = sum(1 for r in rws if r == 1.0)
        lines.append(f"- {model}: {len(rws)} graded run(s), solved {solved}" + (" -> SOLVED" if solved else " -> not solved"))
    lines += ["", "## Per trap (runs that failed the trap's tests / runs of that model)", "",
              "| Trap | Shape | " + " | ".join(sorted(models)) + " |", "|---|---|" + "---|" * len(models)]
    for t in traps:
        if not isinstance(t, dict):
            continue
        tid = str(t.get("id") or t.get("name") or "?")
        shape = str(t.get("shape") or "")[:90].replace("|", "/")
        cells = []
        for model in sorted(models):
            f, n = per.get(tid, {}).get(model, [0, 0])
            cells.append(f"{f}/{n}" + (" (fixed every run)" if n and not f else ""))
        lines.append(f"| {tid} | {shape} | " + " | ".join(cells) + " |")
    if unmapped:
        lines += ["", "## Failing tests not mapped to a trap", ""]
        lines += [f"- {n} (in {c} run(s))" for n, c in sorted(unmapped.items())]
    lines += ["", "Read: a trap every run of the solving model fixed is not difficulty for that model. "
              "Add the kind of trap that model misses, and make sure no single trap carries the task."]
    open(out_path, "w").write("\n".join(lines) + "\n")


if __name__ == "__main__":
    try:
        main(sys.argv[1])
    except Exception as e:  # never block the caller
        print(f"trial_summary: {e}", file=sys.stderr)
    sys.exit(0)
