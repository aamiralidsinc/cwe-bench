"""repair: an audit-driven, test-only repair of one task, on DeepSeek (common/queue/repairjob.py).

The fairfix step brought back as a queue job (history: common/queue/repairstep.py, docs/WORK-QUEUE.md). Planned by
repairstep.plan (rule T1; [repair] auto = false queues nothing and shows the plan), or by hand:
    cweq enqueue repair <slug> --args '{"finding": "<key from cweq explain>"}'
    cweq enqueue repair <slug> --args '{"finding": "the owner's own words, or {\"tests\": [...], \"why\": ...}"}'
The job holds the task, waits for its other work, gives the agent the finding and the failing runs' evidence, runs
the fairfix script in repair mode through common/launch/drive.sh deepseek, checks the result in code, and on success
leaves the hold and queues the re-gate; the reconciler's rules regrade every graded run and lift the hold (R2, R6).
Exit codes: repairjob.py.
"""
import sys

from kinds import Kind, register


def command(row, cfg):
    import qdb
    import json
    a = qdb.args_of(row)
    return ["bash", "common/launch/drive.sh", "deepseek", sys.executable, "-I", "common/queue/repairjob.py",
            row["task"], "--job", str(row["id"]), "--config", cfg["_file"],
            "--finding", json.dumps(a.get("finding", ""), sort_keys=True)]


def plan(conn, cfg, ctx, states, dry_run=False):
    import repairstep
    return repairstep.plan(conn, cfg, ctx, states, dry_run=dry_run)


def check(task, args, t0, cfg):
    """The job's own record says repaired: JOB-RESULT.json written after the start in a repair-inputs-* folder, a new
    repair folder with a README, instruction.md as before, the hold kept for the re-gate and regrades."""
    import json
    import markers
    import qdb
    from taskstate import paths
    b = paths.BUILD / task
    recs = sorted(b.glob("repair-inputs-*/JOB-RESULT.json"))
    res, f = {}, None
    for f in reversed(recs):
        try:
            res = json.loads(f.read_text())
        except (OSError, ValueError):
            res = {}
        break
    fresh = bool(f and (qdb.parse_utc(res.get("finished_utc")) or 0) >= t0 - 2)
    out = [("repair.result", fresh and res.get("result") == "repaired",
            f"{f.parent.name if f else '-'}: {res.get('result', 'no JOB-RESULT.json')}", False)]
    folder = b / str(res.get("folder") or "-")
    out.append(("repair.folder", folder.is_dir() and (folder / "README.md").is_file(),
                f"{folder.name} with README.md" if folder.is_dir() else "no new repair folder", False))
    import hashlib
    cur = hashlib.sha256((paths.TASKS / task / "instruction.md").read_bytes()).hexdigest() \
        if (paths.TASKS / task / "instruction.md").is_file() else ""
    out.append(("repair.instruction_kept", bool(cur) and cur == res.get("instruction_sha256"),
                "instruction.md unchanged" if cur == res.get("instruction_sha256") else "instruction.md changed", True))
    out.append(("repair.held", markers.has(b, ".hold-repair"), ".hold-repair kept for the re-gate and regrades", False))
    return out


register(Kind(name="repair", command=command, check=check, plan=plan, exclusive=True, foreign="repair",
              count_foreign=True, priority=32, max_running=4, max_attempts=1, retry_exit_codes=(75,),
              disk_floor="DISK_MIN_FREE_GB_GATE",
              reads=("<trial>/postmortem-*/POSTMORTEM.json", "<trial>/verifier/", "<trial>/final-code/",
                     "<trial>/agent/claude-code.txt", "build/<slug>/FAIRNESS.md", "build/<slug>/HUMAN-DECISION.md",
                     "build/<slug>/notes.md", "build/<slug>/history/"),
              writes=("build/<slug>/repair-inputs-<UTC>/", "build/<slug>/repaired-tests-<date>-repair/",
                      "build/<slug>/history/<date>-repair.md", "tasks/<slug>/tests/", "build/<slug>/.hold-repair",
                      "build/<slug>/repair-<date>.log", "a regate job")))
