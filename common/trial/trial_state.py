#!/usr/bin/env python3
"""trial_state.py <slug> <model> [--runs N] : how far one model's trials of the CURRENT task
version got, from build/<slug>/runs_<model>.log (snapshot_experiment.sh moves it away with each
version, so it never mixes versions).

Prints one line: `<state> graded=<n> ungraded=<n> rewards=<r,...>` where state is
    none        no run recorded                                             exit 1
    incomplete  no solve and fewer than N graded runs (infra errors, cuts)  exit 2
    stuck       incomplete, and STUCK_AFTER or more runs produced no result:
                stop re-queuing, a person looks at why                      exit 3
    solved      at least one graded run at reward 1.0                       exit 0
    failed      N or more graded runs, none at 1.0                          exit 0
For LAUNCH decisions only (trial it again or not). Per-model verdicts come from
common/audit/audit_results.py, which also applies the post-run audit.

drop (2026-10-29): job names of graded runs whose post-run audit is UNTRUSTED and that the queue re-runs
(common/queue/untrusted.py). They count neither as graded nor as ungraded, the same as a provider stop's
reward=None row counts toward no verdict, so the launch rules plan a fresh run for each. Until then the runs log
counted them as graded fails while the ledger excluded them, and neither side planned the missing runs.

Until 2026-10-20 launchers grepped `reward=[0-9.]+` (hiding every reward=None), tested `-s` on the
log (one infra row meant "trialed"), and matched "1.0" as a regex ("0.9231,0.5" contains "1,0").
"""
import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(next(p for p in Path(__file__).resolve().parents if (p / ".cwe-bench-root").is_file()) / "common"))
import paths  # noqa: E402  (repo locations: common/paths.py)
import markers  # noqa: E402  (common/markers.py)

ROOT = paths.ROOT
STUCK_AFTER = 6   # ungraded runs: trial.py makes at most 2 per run slot, so 3 slots' worth


def rows(slug, model):
    """[(reward or None, job name)] of the runs log in order. The job name is the row's last tab field ('' when the
    row has none)."""
    log = markers.runs_log(ROOT / "build" / slug, model)
    out = []
    if log.is_file():
        for line in log.read_text(errors="replace").splitlines():
            m = re.search(r"\breward=(None|[0-9.]+)\b", line)
            if m:
                job = line.rsplit("\t", 1)[-1].strip() if "\t" in line else ""
                out.append((None if m.group(1) == "None" else float(m.group(1)), job))
    return out


def state(slug, model, runs=3, drop=()):
    """(state, graded rewards, ungraded count). drop: job names whose graded rows do not count (see the module doc)."""
    rewards = [r for r, job in rows(slug, model) if not (r is not None and job and job in drop)]
    graded = [r for r in rewards if r is not None]
    if not rewards:
        s = "none"
    elif any(abs(r - 1.0) < 1e-9 for r in graded):
        s = "solved"
    elif len(graded) >= runs:
        s = "failed"
    elif len(rewards) - len(graded) >= STUCK_AFTER:
        s = "stuck"
    else:
        s = "incomplete"
    return s, graded, len(rewards) - len(graded)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    ap.add_argument("model")
    ap.add_argument("--runs", type=int, default=3)
    a = ap.parse_args()
    s, graded, ungraded = state(a.slug, a.model, a.runs)
    print(f"{s} graded={len(graded)} ungraded={ungraded} rewards={','.join(f'{r:g}' for r in graded) or '-'}")
    sys.exit({"solved": 0, "failed": 0, "none": 1, "stuck": 3}.get(s, 2))
