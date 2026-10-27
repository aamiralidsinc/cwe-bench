#!/usr/bin/env python3
"""Task-quality lint: a warning-only check of a task's tests before trials (docs/TASK-QUALITY.md).

    python3 common/lint/task_lint.py tasks/<slug> [tasks/<slug> ...] [--repo DIR] [--json OUT]
    python3 common/lint/task_lint.py --all TASKS_ROOT [--repo-root DIR] [--out DIR]

It never fails a task and never changes a file. Exit code 0 always (2 only for a usage error). Per task it reports:
  - static findings (common/lint/checks.py): stand-ins against the real code, network stand-ins above the layer a
    fix may use, flaky timing, security tests that drive internal code without accepting a refusal, project tests
    read from the agent's workspace, custom report writers;
  - the scorer check (common/lint/score_check.py): the task's own score.py run against synthetic results.
--repo DIR (or --repo-root DIR holding <slug>/repo or <slug>/src checkouts) lets stand-ins be compared member by
member with the real classes.
--all writes <out>/<slug>.json for every task and <out>/SUMMARY.md (findings by kind, tasks per kind).
"""
import argparse
import hashlib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import checks  # noqa: E402
import score_check  # noqa: E402

_score_cache = {}


def score_findings(task):
    sp = Path(task) / "tests" / "score.py"
    if not sp.is_file():
        return [checks.Finding("no-score-py", "info", "tests/score.py", 0, "no tests/score.py")]
    digest = hashlib.sha256(sp.read_bytes()).hexdigest()
    if digest not in _score_cache:
        _score_cache[digest] = score_check.check(sp)
    bad = _score_cache[digest]
    if not bad:
        return []
    return [checks.Finding("scoring", "warn", "tests/score.py", 0,
                           f"score.py mis-scores {len(bad)} of {len(score_check.SCENARIOS)} grading outcomes: "
                           + "; ".join(f"{name} (reward {reward}): {why}" for name, reward, why in bad))]


def lint(task, repo=None, with_score=True):
    out = checks.run(task, repo)
    if with_score:
        out += score_findings(task)
    return out


def find_repo(repo_root, slug):
    if not repo_root:
        return None
    for sub in ("repo", "src", "workspace"):
        p = Path(repo_root) / slug / sub
        if p.is_dir():
            return p
    return None


def print_task(task, findings):
    print(f"== {Path(task).name}: {sum(f.severity == 'warn' for f in findings)} warnings, "
          f"{sum(f.severity == 'info' for f in findings)} notes")
    for f in findings:
        print(f"  [{f.severity}] {f.kind} {f.file}:{f.line} {f.message}")


def summary(results, out_dir):
    tasks_by_kind, count_by_kind, sev = defaultdict(set), Counter(), {}
    for slug, findings in results.items():
        for f in findings:
            tasks_by_kind[f.kind].add(slug)
            count_by_kind[f.kind] += 1
            sev[f.kind] = f.severity if sev.get(f.kind) != "warn" else "warn"
    lines = ["# Task-quality lint summary", "", f"Tasks linted: {len(results)}", "",
             "| Finding | Severity | Tasks | Findings | Example tasks |", "|---|---|---|---|---|"]
    for kind in sorted(tasks_by_kind, key=lambda k: (sev[k] != "warn", -len(tasks_by_kind[k]))):
        ex = ", ".join(sorted(tasks_by_kind[kind])[:5])
        lines.append(f"| {kind} | {sev[kind]} | {len(tasks_by_kind[kind])} | {count_by_kind[kind]} | {ex} |")
    clean = [s for s, f in results.items() if not any(x.severity == "warn" for x in f)]
    clean_but_scoring = [s for s, f in results.items()
                         if not any(x.severity == "warn" and x.kind != "scoring" for x in f)]
    lines += ["", f"Tasks with no warning: {len(clean)}",
              f"Tasks whose only warning is the scorer (a task built before the current score.py template): "
              f"{len(clean_but_scoring) - len(clean)}"]
    (Path(out_dir) / "SUMMARY.md").write_text("\n".join(lines) + "\n")
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("tasks", nargs="*")
    ap.add_argument("--all", metavar="TASKS_ROOT")
    ap.add_argument("--repo")
    ap.add_argument("--repo-root")
    ap.add_argument("--json")
    ap.add_argument("--out", default="lint-out")
    ap.add_argument("--no-score", action="store_true", help="skip running score.py")
    a = ap.parse_args(argv)
    if not a.tasks and not a.all:
        ap.print_usage()
        return 2
    if a.all:
        out = Path(a.out)
        out.mkdir(parents=True, exist_ok=True)
        results = {}
        for task in sorted(p for p in Path(a.all).iterdir() if (p / "tests").is_dir()):
            f = lint(task, find_repo(a.repo_root, task.name), not a.no_score)
            results[task.name] = f
            (out / f"{task.name}.json").write_text(checks.to_json(f))
        print(summary(results, out))
        return 0
    allf = {}
    for t in a.tasks:
        f = lint(t, a.repo or find_repo(a.repo_root, Path(t).name), not a.no_score)
        allf[Path(t).name] = [x.as_dict() for x in f]
        print_task(t, f)
    if a.json:
        Path(a.json).write_text(json.dumps(allf, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
