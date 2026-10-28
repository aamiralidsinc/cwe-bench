#!/usr/bin/env python3
"""Append screener jobs for the top-up entries (out/source_pool_ext.sqlite) to out/screener_jobs.jsonl.

Same job format and filters as make_screener_jobs.py: classify kept the entry ('candidate') and the repo is at most
1.5 GB. A job that is already in the file is not added again. The runner skips jobs that already have a record.

  python3 -I diversity_population/make_topup_jobs.py
"""
import json, sqlite3
from pathlib import Path

HERE = Path(__file__).resolve().parent
P = {p["id"]: p for p in json.load(open(HERE / "patterns.json"))["patterns"]}
idx = sqlite3.connect(f"file:{HERE / 'out/index/candidates.sqlite'}?mode=ro", uri=True)
idx.row_factory = sqlite3.Row
ext = sqlite3.connect(f"file:{HERE / 'out/source_pool_ext.sqlite'}?mode=ro", uri=True)
jf = HERE / "out/screener_jobs.jsonl"
have = {json.loads(l)["id"] for l in open(jf) if l.strip()}
pats_of = {}
for pat, eid in ext.execute("select pattern, entry_id from ext order by pattern, rank"):
    pats_of.setdefault(eid, []).append(pat)
new, per = [], {}
for eid, pats in pats_of.items():
    r = idx.execute("select * from entries where entry_id=?", (eid,)).fetchone()
    if r is None or r["status"] != "candidate" or (r["repo_size_kb"] or 0) > 1_500_000 or f"diversity-{eid}" in have:
        continue
    row = {k: r[k] for k in r.keys() if k in ("entry_id", "ids", "cve", "repo", "cwe_ids", "summary", "parent_commit",
                                             "fix_commits", "language", "score", "published") or k.startswith("c_")}
    hint = " | ".join(f"{P[p]['name']}: {P[p]['other_places_hint']}" for p in pats)
    new.append({"id": f"diversity-{eid}", "entry_id": str(eid), "repo": r["repo"], "row": row, "patterns": pats,
                "pattern_hint": hint, "topup": True})
    for p in pats:
        per[p] = per.get(p, 0) + 1
with open(jf, "a") as f:
    f.write("".join(json.dumps(j, default=str) + "\n" for j in new))
print(f"appended {len(new)} top-up jobs; per pattern: {per}")
