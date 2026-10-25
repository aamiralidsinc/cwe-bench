#!/usr/bin/env python3
"""Did a run look up the upstream fix on the internet? One row per graded trial (research/own-runs).

    python3 research/own-runs/lookup_scan.py

Reads each graded trial's Claude Code transcript (agent/claude-code.txt, stream-json) and counts
tool calls that reach the internet for code or advisories:
    web      WebSearch calls, and WebFetch calls to the hosts below
    gh       Bash curl/wget/git/gh commands with an http(s) URL on github.com, raw.githubusercontent.com, api.github.com,
             gitlab.com, or advisory sites (nvd.nist.gov, osv.dev, github.com/advisories)
    clone    Bash 'git clone' / 'git fetch' of a remote URL
lookup = any of the above. Package installs (pip/npm/cargo/maven) are NOT counted.
Output: lookups.tsv and a summary on stdout (solve rate with vs without a lookup, per model and
track). Trials and verdicts come from build/audit/trials.tsv; used_in_verdict from test_results.tsv.
"""
import csv
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
JOBS = Path.home() / ".tb-graders" / "cwe" / "jobs"
sys.path.insert(0, str(ROOT / "build"))
import audit_results as A                                    # noqa: E402

NET = re.compile(r"github\.com|githubusercontent\.com|gitlab\.com|nvd\.nist\.gov|osv\.dev|"
                 r"security-tracker|cve\.org|cve\.mitre\.org|snyk\.io|huntr\.", re.I)
CLONE = re.compile(r"git\s+(clone|fetch|ls-remote)\s+\S*(https?://|git@)", re.I)


def tool_calls(path):
    for line in open(path, errors="replace"):
        try:
            ev = json.loads(line)
        except ValueError:
            continue
        msg = ev.get("message") if isinstance(ev, dict) else None
        if not isinstance(msg, dict) or ev.get("type") != "assistant":
            continue
        for c in msg.get("content") or []:
            if isinstance(c, dict) and c.get("type") == "tool_use":
                yield c.get("name"), c.get("input") or {}


def scan(trial_dir):
    web = gh = clone = 0
    first = ""
    p = trial_dir / "agent" / "claude-code.txt"
    if not p.exists():
        return None
    for name, inp in tool_calls(p):
        hit = None
        if name == "WebSearch" or (name == "WebFetch" and NET.search(str(inp.get("url", "")))):
            web += 1
            hit = f"{name}: {inp.get('url') or inp.get('query') or ''}"
        elif name == "Bash":
            cmd = str(inp.get("command", ""))
            if CLONE.search(cmd):
                clone += 1
                hit = "Bash: " + cmd
            elif re.search(r"https?://[^\s'\"]*(" + NET.pattern + ")", cmd, re.I) \
                    and re.search(r"\b(curl|wget|git|gh)\b", cmd):
                gh += 1
                hit = "Bash: " + cmd
        if hit and not first:
            first = hit[:160].replace("\t", " ").replace("\n", " ")
    return web, gh, clone, first


def main():
    used = {}
    for r in csv.DictReader(open(HERE / "test_results.tsv"), delimiter="\t"):
        used[r["trial"]] = r["used_in_verdict"] == "1"
    names = {"deepseek-flash[1m]": "DeepSeek", "mimo-v2.6-pro": "MiMo"}
    rows = []
    for t in csv.DictReader(open(ROOT / "build/audit/trials.tsv"), delimiter="\t"):
        if t["reward"] == "":
            continue
        s = scan(JOBS / t["job"] / t["trial"])
        if s is None:
            continue
        m = names.get(t["model"], t["model"])
        rows.append({"task": t["task"], "track": A.track_of(t["task"]), "model": m, "start_utc": t["start_utc"],
                     "reward": t["reward"], "used": int(used.get(t["trial"], False)),
                     "web": s[0], "gh": s[1], "clone": s[2], "lookup": int(any(s[:3])), "first_lookup": s[3],
                     "job": t["job"], "trial": t["trial"]})
    cols = list(rows[0])
    with open(HERE / "lookups.tsv", "w") as f:
        f.write("\t".join(cols) + "\n")
        for r in rows:
            f.write("\t".join(str(r[c]) for c in cols) + "\n")
    agg = defaultdict(lambda: [0, 0, 0, 0])            # key -> [lookup runs, lookup solves, other runs, other solves]
    for r in rows:
        if not r["used"]:
            continue
        solved = float(r["reward"]) == 1.0
        for key in (("all",), ("model", r["model"]), ("track", r["track"]), ("model x track", r["model"], r["track"])):
            a = agg[key]
            if r["lookup"]:
                a[0] += 1
                a[1] += solved
            else:
                a[2] += 1
                a[3] += solved
    print(f"{len(rows)} graded trials scanned; {sum(r['used'] for r in rows)} used in verdicts\n")
    print(f"{'group':40} {'looked up':>14} {'no lookup':>14}")
    for key in sorted(agg, key=lambda k: (len(k), k)):
        a = agg[key]
        f = lambda n, s: f"{s}/{n} ({s / n:.0%})" if n else "-"
        print(f"{' / '.join(key):40} {f(a[0], a[1]):>14} {f(a[2], a[3]):>14}")


if __name__ == "__main__":
    main()
