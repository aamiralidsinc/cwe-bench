#!/usr/bin/env python3
"""Refresh docs/RESULTS.md's task table from the audited ledger (run after every recorded verdict).

    python3 common/audit/postmortem.py record-ready && python3 common/audit/audit_results.py && python3 common/audit/update_results.py

Rewrites only the DeepSeek / MiMo / Verdict cells of the "All trialed tasks" table and the
"Audited verdicts as of" stamp; prose (executive summary, open pairs, corrections) is edited by
hand when a verdict changes, and this script prints which pairs changed so that is not missed.
Cells of decided pairs drop "(+N awaiting audit)" (extra solves of an already-SOLVED pair are not
all audited); undecided pairs keep it.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(next(p for p in Path(__file__).resolve().parents if (p / ".cwe-bench-root").is_file()) / "common"))
import paths  # noqa: E402  (repo locations: common/paths.py)

ROOT = paths.ROOT
TRACKS = ("mined", "stacking", "injection")


def main():
    led = (ROOT / "build/audit/ledger.md").read_text()
    stamp = re.search(r"_Generated ([^_]+)_", led).group(1)
    cells = {}
    for line in led.split("## All tasks")[1].splitlines():
        c = [x.strip() for x in line.strip().strip("|").split("|")]
        if len(c) == 5 and c[0] in TRACKS:
            fix = lambda s: re.sub(r" \(\+\d+ awaiting audit\)", "", s) if s.startswith(("SOLVED", "**failed")) else s
            cells[c[1]] = (fix(c[2]), fix(c[3]), c[4])
    p = ROOT / "docs" / "RESULTS.md"
    out, changed = [], []
    in_table = False
    for line in p.read_text().splitlines():
        if line.startswith("## All trialed tasks"):
            in_table = True
        elif line.startswith("## ") and in_table:
            in_table = False
        c = [x.strip() for x in line.strip().strip("|").split("|")] if line.startswith("|") else []
        if in_table and len(c) == 8 and c[0] in TRACKS and c[1] in cells:
            ds, mi, ver = cells[c[1]]
            for who, old, new in (("DeepSeek", c[3], ds), ("MiMo", c[4], mi), ("Verdict", c[5], ver)):
                if old != new:
                    changed.append(f"{c[1]} {who}: {old}  ->  {new}")
            c[3], c[4], c[5] = ds, mi, ver
            line = "| " + " | ".join(c) + " |"
        out.append(line)
    text = "\n".join(out) + "\n"
    text = re.sub(r"_Audited verdicts as of [^(]+\(", f"_Audited verdicts as of {stamp} (", text, count=1)
    p.write_text(text)
    print("RESULTS.md table refreshed;", "changes:" if changed else "no verdict cell changed")
    for c in changed:
        print("  " + c)


if __name__ == "__main__":
    main()
