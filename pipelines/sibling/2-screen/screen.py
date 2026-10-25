#!/usr/bin/env python3
"""Run the UNCHANGED sibling screener (common/screener/run_screener.py --run, common/screener/SCREENER-PROMPT-v2.md)
on the sibling2 batch, writing records to pipelines/sibling/out/screener/ instead of pipelines/stacking/out/screener/.
Clones are shared with stacking (keyed by repo); worktrees go to their own folder.

  CLAUDE_BIN=... python3 -I pipelines/sibling/2-screen/screen.py --run --parallel 4 --model claude-opus-5-5 [--dry-run] [--only scr-N ...]
"""
import importlib.util, os, sys
from pathlib import Path
sys.path.insert(0, str(next(p for p in Path(__file__).resolve().parents if (p / ".cwe-bench-root").is_file()) / "common"))
import paths  # noqa: E402  (repo locations: common/paths.py)

ROOT = str(paths.ROOT)
spec = importlib.util.spec_from_file_location("run_screener", str(paths.SCREENER_RUNNER))
rs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rs)

rs.OUTDIR = os.path.join(str(paths.SIBLING_OUT), "screener")
rs.JOBS = os.path.join(str(paths.SIBLING_OUT), "screener_jobs.jsonl")
rs.TREES = os.path.expanduser("~/.tb-graders/cwe/sibling2/screen-trees")

if "--pick" in sys.argv:
    sys.exit("use pipelines/sibling/1-pick/pick.py to pick; this wrapper only runs the screener")
rs.main()
