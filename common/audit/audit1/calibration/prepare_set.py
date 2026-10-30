#!/usr/bin/env python3
"""Calibration set for audit 1: copy each run's evidence (never the Opus verdict) and write its FACTS.

    python3 common/audit/audit1/calibration/prepare_set.py <config.json>

config.json (a file, so no task names reach a command line):
    {"jobs": "/home/mara/.tb-graders/cwe/jobs",
     "since": "2026-10-29T21:50:00Z",          # every postmortem whose verdict.json is newer than this
     "extra": ["<trial>", ...],                # older runs to add (infra / contamination / ambiguity verdicts)
     "work": "/home/mara/scratch/audit1-cal"}

For each selected trial, the newest postmortem folder with a verdict.json is used. Copied into <work>/runs/<trial>/:
evidence/ and PREPARED.json only. facts.py then reads the ORIGINAL trial folder (read only) and writes FACTS.json and
facts-input/ into the copy. <work>/opus.tsv maps trial -> the Opus verdict.json path, for calibrate.py; the verdicts
stay where they are and are never copied next to the runs. Nothing under the jobs folder is written.
"""
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import facts  # noqa: E402


def main():
    cfg = json.loads(Path(sys.argv[1]).read_text())
    jobs, work = Path(cfg["jobs"]), Path(cfg["work"])
    since = datetime.fromisoformat(cfg["since"].replace("Z", "+00:00")).timestamp()
    extra = set(cfg.get("extra") or [])
    chosen = {}
    for v in jobs.glob("*/*/postmortem-*/verdict.json"):
        trial = v.parent.parent.name
        if v.stat().st_mtime > since or trial in extra:
            if trial not in chosen or v.parent.name > chosen[trial].parent.name:
                chosen[trial] = v
    missing = extra - set(chosen)
    runs = work / "runs"
    runs.mkdir(parents=True, exist_ok=True)
    tsv = []
    for trial, v in sorted(chosen.items()):
        pm = v.parent
        dest = runs / trial
        if (dest / "FACTS.json").exists():
            tsv.append(f"{trial}\t{v}\t{'extra' if trial in extra else 'tonight'}")
            continue
        dest.mkdir(exist_ok=True)
        if not (dest / "evidence").exists():
            shutil.copytree(pm / "evidence", dest / "evidence")
        shutil.copy2(pm / "PREPARED.json", dest / "PREPARED.json")
        try:
            _, f = facts.build(pm, pm.parent, dest)
            print(f"{trial}: {len(f['failing_tests'])} failing, infra_hint={f['infra_hint']}, "
                  f"{len(f['contamination_hits'])} hits")
        except Exception as e:
            print(f"{trial}: FACTS FAILED {type(e).__name__}: {e}")
        tsv.append(f"{trial}\t{v}\t{'extra' if trial in extra else 'tonight'}")
    (work / "opus.tsv").write_text("\n".join(tsv) + "\n")
    print(f"{len(chosen)} runs ({len(chosen) - len(extra - missing)} tonight, {len(extra - missing)} extra); "
          f"missing extra: {sorted(missing)}")


if __name__ == "__main__":
    main()
