#!/usr/bin/env python3
"""Re-score each run's FIRST-TRY dossier with the current quote_check.py, strict and with the transcript block rule.

    python3 common/audit/audit1/calibration/quote_rescore.py <config.json>

config.json: {"work": "/home/mara/scratch/audit1-cal",
              "rounds": {"r1": {"<trial>": "<folder holding that round's outputs>", ...}, ...}}
or, simpler, {"work": ..., "r2_set": "<work>/r2-set.json"}: round r1 = r1-archive/<trial> for re-run trials and
runs/<trial> otherwise; round r2 = runs/<trial> for the re-run trials.
The first-try dossier is DOSSIER.try1.json when a retry happened, else DOSSIER.json. Each is checked in a temporary
copy holding evidence/ and facts-input/ of the run (so the folder rule of the checker holds).
"""
import json
import shutil
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import quote_check  # noqa: E402


def first_try(folder):
    for name in ("DOSSIER.try1.json", "DOSSIER.json"):
        if (folder / name).exists():
            return folder / name
    return None


def score(run_dir, dossier):
    tmp = Path(tempfile.mkdtemp(prefix="a1-q-")) / "r"
    try:
        shutil.copytree(run_dir / "evidence", tmp / "evidence")
        if (run_dir / "facts-input").is_dir():
            shutil.copytree(run_dir / "facts-input", tmp / "facts-input")
        shutil.copy(dossier, tmp / "DOSSIER.json")
        out = {}
        for mode, strict in (("strict", True), ("block", False)):
            quote_check._cache.clear()
            quote_check._blocks.clear()
            out[mode] = quote_check.check(tmp, strict_lines=strict)
        return out
    finally:
        shutil.rmtree(tmp.parent, ignore_errors=True)


def main():
    cfg = json.loads(Path(sys.argv[1]).read_text())
    work = Path(cfg["work"])
    r2 = json.loads(Path(cfg["r2_set"]).read_text())
    rerun = set(r2["misses"]) | set(r2["random"])
    trials = sorted(p.name for p in (work / "runs").iterdir() if p.is_dir())
    rounds = {"r1": {t: (work / "r1-archive" / t if t in rerun else work / "runs" / t) for t in trials},
              "r2 (re-run set)": {t: work / "runs" / t for t in sorted(rerun)}}
    for name, folders in rounds.items():
        tot = {"strict": [0, 0, 0, 0], "block": [0, 0, 0, 0]}   # dossiers pass, dossiers, quotes failed, quotes
        notfound = 0
        for t, f in folders.items():
            d = first_try(f)
            if d is None:
                continue
            r = score(work / "runs" / t, d)
            for mode in tot:
                tot[mode][0] += bool(r[mode]["pass"])
                tot[mode][1] += 1
                tot[mode][2] += r[mode]["failed"]
                tot[mode][3] += r[mode]["quotes"]
            notfound += sum(1 for x in r["block"]["results"] if not x["ok"] and "not found" in x["why"])
        for mode, (ok, n, qf, q) in tot.items():
            print(f"{name:16} {mode:6}: first-try dossiers passing {ok}/{n} ({100 * ok / max(1, n):.1f}%); "
                  f"quotes failing {qf}/{q}")
        print(f"{name:16} quotes whose text is not in the cited file at all: {notfound}")


if __name__ == "__main__":
    main()
