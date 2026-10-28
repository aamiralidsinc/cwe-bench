#!/usr/bin/env python3
"""Write the screener job list for the diversity experiment (out/screener_jobs.jsonl).

One job per pool entry that classify kept (status 'candidate' in out/index/candidates.sqlite), except repos over
1.5 GB (the screener's own size rule). Each job carries the row fields run_screener.py's pick() sends, plus the
entry's pattern(s) and the pattern hint(s) from patterns.json.

Order: round-robin over the 22 patterns by pool rank (newest first), so a partial run covers every pattern evenly.

  python3 -I diversity_population/make_screener_jobs.py
"""
import json, sqlite3
from pathlib import Path

HERE = Path(__file__).resolve().parent
P = {p["id"]: p for p in json.load(open(HERE / "patterns.json"))["patterns"]}
idx = sqlite3.connect(f"file:{HERE / 'out/index/candidates.sqlite'}?mode=ro", uri=True)
idx.row_factory = sqlite3.Row
pool = sqlite3.connect(f"file:{HERE / 'out/source_pool.sqlite'}?mode=ro", uri=True)

keep = {}
for r in idx.execute("select * from entries where status='candidate'"):
    if (r["repo_size_kb"] or 0) > 1_500_000:
        continue
    keep[r["entry_id"]] = r
lists, pats_of = {}, {}
for pat, rank, eid in pool.execute("select pattern, rank, entry_id from pool order by pattern, rank"):
    pats_of.setdefault(eid, []).append(pat)
    if eid in keep:
        lists.setdefault(pat, []).append(eid)

order, seen = [], set()
for i in range(max(len(v) for v in lists.values())):
    for pat in P:
        v = lists.get(pat, [])
        if i < len(v) and v[i] not in seen:
            order.append(v[i]); seen.add(v[i])

out = []
for eid in order:
    r = keep[eid]
    row = {k: r[k] for k in r.keys() if k in ("entry_id", "ids", "cve", "repo", "cwe_ids", "summary", "parent_commit",
                                             "fix_commits", "language", "score", "published") or k.startswith("c_")}
    pats = pats_of[eid]
    hint = " | ".join(f"{P[p]['name']}: {P[p]['other_places_hint']}" for p in pats)
    out.append({"id": f"diversity-{eid}", "entry_id": str(eid), "repo": r["repo"], "row": row,
                "patterns": pats, "pattern_hint": hint})
(HERE / "out").mkdir(exist_ok=True)
with open(HERE / "out/screener_jobs.jsonl", "w") as f:
    f.write("".join(json.dumps(j, default=str) + "\n" for j in out))
print(f"{len(out)} jobs over {len({j['repo'] for j in out})} repos; "
      f"per pattern: " + ", ".join(f"{p} {len(lists.get(p, []))}" for p in P))
