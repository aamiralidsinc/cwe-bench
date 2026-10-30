#!/usr/bin/env python3
"""Held-out check of the deterministic infra route (facts.py + route.py's hard-infra rule, no LLM) against Opus.

    python3 common/audit/audit1/calibration/infra_holdout.py <config.json>

config.json: {"jobs": "/home/mara/.tb-graders/cwe/jobs", "work": "/home/mara/scratch/audit1-cal",
              "since": "2026-10-20T00:00:00Z", "exclude_tsv": "<opus.tsv of the calibration set>"}
For every trial's newest postmortem with an Opus verdict.json (not model-solved), newer than "since" and not in the
calibration set, FACTS is built into a temporary folder (reads the jobs folder only) and the run counts as
"infra by facts" when it has a hard infra signal (route.HARD_INFRA, soft kinds excluded). Prints the confusion
against Opus attribution harness-or-infra and lists every disagreement. Writes <work>/infra-holdout.tsv.
"""
import json
import shutil
import sys
import tempfile
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import facts  # noqa: E402
import route  # noqa: E402


def main():
    cfg = json.loads(Path(sys.argv[1]).read_text())
    jobs, work = Path(cfg["jobs"]), Path(cfg["work"])
    since = datetime.fromisoformat(cfg["since"].replace("Z", "+00:00")).timestamp()
    excl = {ln.split("\t")[0] for ln in Path(cfg["exclude_tsv"]).read_text().splitlines() if ln.strip()}
    newest = {}
    for v in jobs.glob("*/*/postmortem-*/verdict.json"):
        t = v.parent.parent.name
        if t in excl or v.stat().st_mtime < since:
            continue
        if t not in newest or v.parent.name > newest[t].parent.name:
            newest[t] = v
    rows, tmp = [], Path(tempfile.mkdtemp(prefix="a1-holdout-"))
    try:
        for t, v in sorted(newest.items()):
            try:
                verdict = json.loads(v.read_text())
            except ValueError:
                continue
            att = verdict.get("attribution")
            if att == "model-solved":
                continue
            pm = v.parent
            if not (pm / "evidence").is_dir():
                continue
            out = tmp / t
            shutil.copytree(pm / "evidence", out / "evidence")
            try:
                _, f = facts.build(pm, pm.parent, out)
            except Exception as e:
                rows.append((t, att, "error", f"{type(e).__name__}: {e}"))
                continue
            hard = [s for s in f["infra_signals"] if s.get("infra") and s["kind"] in route.HARD_INFRA
                    and s["kind"] not in route.SOFT_KINDS]
            rows.append((t, att, "infra" if hard else "-", "; ".join(f"{s['kind']}: {s['detail'][:90]}" for s in hard)))
            shutil.rmtree(out)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    tp = sum(1 for r in rows if r[1] == "harness-or-infra" and r[2] == "infra")
    fn = [r for r in rows if r[1] == "harness-or-infra" and r[2] != "infra"]
    fp = [r for r in rows if r[1] != "harness-or-infra" and r[2] == "infra"]
    n_inf = tp + len(fn)
    print(f"held-out runs: {len(rows)}; Opus harness-or-infra: {n_inf}; facts infra on those: {tp}; "
          f"facts infra on other runs (false): {len(fp)}; errors: {sum(1 for r in rows if r[2] == 'error')}")
    for title, rs in (("MISSED infra (Opus harness-or-infra, facts none)", fn), ("FALSE infra", fp)):
        print(f"\n{title}:")
        for r in rs:
            print(f"  {r[0]}  opus={r[1]}  {r[3][:200]}")
    with open(work / "infra-holdout.tsv", "w") as fh:
        for r in rows:
            fh.write("\t".join(r) + "\n")


if __name__ == "__main__":
    main()
