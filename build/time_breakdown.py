#!/usr/bin/env python3
"""Where did each trial's agent time go? Build vs test vs deps vs other commands vs model.

    python3 build/time_breakdown.py            -> build/audit/time_breakdown.tsv + summary

Source: the Claude Code session transcript saved in each trial
(agent/sessions/**/*.jsonl). Every tool_use and its tool_result carry timestamps, so a
command's duration = result time - call time. Command time is the union of those
intervals (parallel calls are not double counted); model time = agent time - command time.
"""
import json
import re
import statistics
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
JOBS = Path.home() / ".tb-graders" / "cwe" / "jobs"
OUT = ROOT / "build" / "audit"

# Order matters: the first matching class wins.
CLASSES = [
    ("test", r"\bpytest\b|\bgo test\b|\bcargo (test|nextest)\b|\bmvn\b[^|;&]*\b(test|verify)\b|"
             r"\bgradlew?\b[^|;&]*\btest\b|\b(npm|pnpm|yarn)\b[^|;&]*\btest\b|\b(jest|vitest)\b|"
             r"\bphpunit\b|\bpest\b|artisan test|\brspec\b|\brake\b[^|;&]*test|-m unittest"),
    ("deps", r"\bpip3? install\b|\buv (pip|sync|add)\b|\b(npm|pnpm|yarn) (install|ci|add)\b|"
             r"\bcomposer (install|update|require)\b|\bbundle (install|update)\b|"
             r"\bgo mod (download|tidy)\b|\bgo get\b|\bcargo fetch\b|\bapt(-get)? install\b|"
             r"dependency:(resolve|go-offline)"),
    ("build", r"\bmvn\b|\bgradlew?\b|\bjavac\b|\bcargo (build|check|clippy)\b|\bgo (build|vet)\b|"
              r"\btsc\b|\b(npm|pnpm|yarn)\b[^|;&]*\b(build|typecheck|tsc)\b|\bmake\b|\bcomposer dump"),
]


def ts(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def classify(cmd):
    c = cmd.lower()
    for name, pat in CLASSES:
        if re.search(pat, c):
            return name
    return "other"


def union_minutes(intervals):
    total, end = 0.0, None
    for a, b in sorted(intervals):
        if end is None or a > end:
            total += (b - a).total_seconds()
            end = b
        elif b > end:
            total += (b - end).total_seconds()
            end = b
    return total / 60


def language(task):
    toml = ROOT / "tasks" / task / "task.toml"
    m = re.search(r'^\s*language\s*=\s*"([^"]+)"', toml.read_text(), re.M) if toml.is_file() else None
    return m.group(1).lower() if m else "?"


def analyse(trial):
    res = json.loads((trial / "result.json").read_text())
    ae = res.get("agent_execution") or {}
    if not (ae.get("started_at") and ae.get("finished_at")):
        return None
    a0, a1 = ts(ae["started_at"]), ts(ae["finished_at"])
    calls, results = {}, {}
    for f in (trial / "agent" / "sessions").rglob("*.jsonl"):
        for line in f.read_text(errors="replace").splitlines():
            try:
                e = json.loads(line)
            except Exception:
                continue
            content = (e.get("message") or {}).get("content")
            if not isinstance(content, list) or not e.get("timestamp"):
                continue
            for x in content:
                if x.get("type") == "tool_use":
                    inp = x.get("input") or {}
                    cmd = inp.get("command") or ""
                    calls[x["id"]] = (ts(e["timestamp"]), x.get("name"), cmd)
                elif x.get("type") == "tool_result":
                    results[x.get("tool_use_id")] = ts(e["timestamp"])
    if not calls:
        return None
    by = {"build": [], "test": [], "deps": [], "other": []}
    longest = (0.0, "")
    for cid, (t0, name, cmd) in calls.items():
        t1 = results.get(cid) or a1           # no result: the call was still running at the cut
        t0, t1 = max(t0, a0), min(t1, a1)
        if t1 <= t0:
            continue
        kind = classify(cmd) if name == "Bash" else "other"
        by[kind].append((t0, t1))
        d = (t1 - t0).total_seconds() / 60
        if d > longest[0]:
            longest = (d, cmd.replace("\n", " ")[:90])
    agent_min = (a1 - a0).total_seconds() / 60
    tool_min = union_minutes([iv for v in by.values() for iv in v])
    ex = (res.get("exception_info") or {}).get("exception_type") or ""
    task = Path(res["config"]["task"]["path"]).name
    return {"task": task, "lang": language(task), "model": res["config"]["agent"]["model_name"],
            "timed_out": ex == "AgentTimeoutError", "agent_min": round(agent_min, 1),
            "build_min": round(union_minutes(by["build"]), 1), "test_min": round(union_minutes(by["test"]), 1),
            "deps_min": round(union_minutes(by["deps"]), 1), "other_cmd_min": round(union_minutes(by["other"]), 1),
            "all_cmd_min": round(tool_min, 1), "model_min": round(agent_min - tool_min, 1),
            "n_calls": len(calls), "longest_min": round(longest[0], 1), "longest_cmd": longest[1],
            "job": trial.parent.name}


def main():
    rows = []
    for job in sorted(JOBS.iterdir()):
        if job.is_dir():
            for trial in (p for p in job.iterdir() if p.is_dir()):
                if (trial / "result.json").is_file() and (ROOT / "tasks" / trial.name.split("__")[0]).is_dir():
                    r = analyse(trial)
                    if r:
                        rows.append(r)
    rows.sort(key=lambda r: (r["task"], r["model"], r["job"]))
    OUT.mkdir(parents=True, exist_ok=True)
    cols = list(rows[0].keys())
    with open(OUT / "time_breakdown.tsv", "w") as f:
        f.write("\t".join(cols) + "\n")
        for r in rows:
            f.write("\t".join(str(r[c]) for c in cols) + "\n")

    def share(group, key):
        tot = sum(r["agent_min"] for r in group)
        return f"{100 * sum(r[key] for r in group) / tot:4.0f}%" if tot else "  - "

    print(f"{len(rows)} trials with a session transcript\n")
    print("group                              n   build   test   deps  other-cmd  model   median agent min")
    groups = [("timed out, Java/Rust", lambda r: r["timed_out"] and r["lang"] in ("java", "rust")),
              ("timed out, other languages", lambda r: r["timed_out"] and r["lang"] not in ("java", "rust")),
              ("finished, Java/Rust", lambda r: not r["timed_out"] and r["lang"] in ("java", "rust")),
              ("finished, other languages", lambda r: not r["timed_out"] and r["lang"] not in ("java", "rust"))]
    for name, pred in groups:
        g = [r for r in rows if pred(r)]
        if g:
            print(f"{name:32} {len(g):3}   {share(g,'build_min')}  {share(g,'test_min')}  {share(g,'deps_min')}"
                  f"     {share(g,'other_cmd_min')}  {share(g,'model_min')}   {statistics.median(r['agent_min'] for r in g):5.1f}")
    print("\nTimed-out runs, one by one:")
    print("task                  lang        model          agent  build  test  deps other model  longest call")
    for r in rows:
        if r["timed_out"]:
            print(f"{r['task']:21} {r['lang']:11} {r['model'][:14]:14} {r['agent_min']:5.0f} {r['build_min']:6.1f}"
                  f" {r['test_min']:5.1f} {r['deps_min']:5.1f} {r['other_cmd_min']:5.1f} {r['model_min']:5.1f}"
                  f"  {r['longest_min']:4.1f}m {r['longest_cmd'][:60]}")


if __name__ == "__main__":
    main()
