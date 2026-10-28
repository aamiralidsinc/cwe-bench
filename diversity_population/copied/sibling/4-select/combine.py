#!/usr/bin/env python3
"""Combine several selection passes over the same pool into one ranking.

One driver-model pass that scores a pool of hundreds of candidates in one call is noisy: two passes over the same pool
agreed on about half of their picks (2026-10-27). Each pass returns its top N with a 0-10 score; a candidate a pass
did not return counts 0 for that pass. The combined score is the mean over the passes; ties go to the candidate more
passes picked, then to the better best rank.

  python3 -I combine.py OUT.json POOL.jsonl PASS1.json PASS2.json [...] [--top N]

Writes OUT.json in selection_<driver>.json form (entry_id, score, reason) plus the evidence (passes, picked_by,
scores, best_rank). Only ids in POOL count.
"""
import argparse
import json


def combine(pool_ids, passes, top=None):
    n = len(passes)
    rows = {}
    for p, sel in enumerate(passes):
        for rank, x in enumerate(sel, 1):
            k = str(x.get("entry_id"))
            if k not in pool_ids:
                continue
            r = rows.setdefault(k, {"entry_id": k, "scores": [0] * n, "reasons": {}, "best_rank": rank})
            if r["scores"][p]:                            # a pass that names an id twice: keep its first entry
                continue
            r["scores"][p] = float(x.get("score") or 0)
            r["reasons"][p] = x.get("reason", "")
            r["best_rank"] = min(r["best_rank"], rank)
    out = []
    for r in rows.values():
        picked = sum(1 for s in r["scores"] if s)
        best_pass = max(r["reasons"], key=lambda p: r["scores"][p])
        out.append({"entry_id": r["entry_id"], "score": round(sum(r["scores"]) / n, 2),
                    "reason": r["reasons"][best_pass], "picked_by": picked, "passes": n,
                    "scores": r["scores"], "best_rank": r["best_rank"]})
    out.sort(key=lambda r: (-r["score"], -r["picked_by"], r["best_rank"], r["entry_id"]))
    return out[:top] if top else out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("pool")
    ap.add_argument("passes", nargs="+")
    ap.add_argument("--top", type=int)
    a = ap.parse_args()
    pool_ids = {str(json.loads(l)["entry_id"]) for l in open(a.pool) if l.strip()}
    passes = [json.load(open(p)) for p in a.passes]
    out = combine(pool_ids, passes, a.top)
    json.dump(out, open(a.out, "w"), indent=1)
    agree = sum(1 for r in out if r["picked_by"] == len(passes))
    print(f"combined {len(passes)} passes: {len(out)} candidates -> {a.out}; picked by every pass: {agree}")


if __name__ == "__main__":
    main()
