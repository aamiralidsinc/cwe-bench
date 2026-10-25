#!/usr/bin/env python3
"""Run the UNCHANGED sibling screener (stacking/run_screener.py --run, builder/SCREENER-PROMPT-v2.md)
on the sibling2 batch, writing records to sibling2/out/screener/ instead of stacking/out/screener/.
Clones are shared with stacking (keyed by repo); worktrees go to their own folder.

  CLAUDE_BIN=... python3 -I sibling2/screen.py --run --parallel 4 --model claude-opus-5-5 [--dry-run] [--only scr-N ...]
"""
import importlib.util, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
spec = importlib.util.spec_from_file_location("run_screener", os.path.join(ROOT, "stacking", "run_screener.py"))
rs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rs)

rs.OUTDIR = os.path.join(ROOT, "sibling2", "out", "screener")
rs.JOBS = os.path.join(ROOT, "sibling2", "out", "screener_jobs.jsonl")
rs.TREES = os.path.expanduser("~/.tb-graders/cwe/sibling2/screen-trees")

if "--pick" in sys.argv:
    sys.exit("use sibling2/pick.py to pick; this wrapper only runs the screener")
rs.main()
