#!/usr/bin/env python3
"""Re-run facts.py on every calibration run after a facts change (deterministic; no LLM).

    python3 common/audit/audit1/calibration/refacts.py <config.json>

config.json: {"work": "/home/mara/scratch/audit1-cal", "keep_as": "FACTS.r1.json"}
Reads <work>/opus.tsv for the trials and the original postmortem folders (read only), keeps the previous FACTS.json
as <keep_as> (once), and writes the new FACTS.json + facts-input/ into <work>/runs/<trial>/.
"""
import json
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import facts  # noqa: E402


def main():
    cfg = json.loads(Path(sys.argv[1]).read_text())
    work = Path(cfg["work"])
    keep = cfg.get("keep_as", "FACTS.r1.json")
    changed = 0
    for line in (work / "opus.tsv").read_text().splitlines():
        if not line.strip():
            continue
        trial, verdict = line.split("\t")[:2]
        pm = Path(verdict).parent
        dest = work / "runs" / trial
        old = dest / "FACTS.json"
        if old.exists() and not (dest / keep).exists():
            shutil.copy2(old, dest / keep)
        before = json.loads((dest / keep).read_text()) if (dest / keep).exists() else {}
        _, f = facts.build(pm, pm.parent, dest)
        kinds = lambda x: sorted((s["kind"], s["infra"]) for s in x.get("infra_signals") or [])  # noqa: E731
        if kinds(before) != kinds(f):
            changed += 1
            print(f"{trial}: infra signals {kinds(before)} -> {kinds(f)}")
    print(f"done; {changed} runs with changed infra signals")


if __name__ == "__main__":
    main()
