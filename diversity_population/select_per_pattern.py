#!/usr/bin/env python3
"""One selection run for the diversity experiment: 12 candidates per pattern, each repo used once.

Uses only the copies in copied/ (the originals are never run or changed):
  1. rerank.py --screened: score_read for every screener record (out/rank/host-rank-screened.tsv);
  2. per pattern: make_pool.py --ids builds the pattern's pool, then select.sh (DeepSeek) picks its top N, PASSES
     times (3, as the latest pipeline does), all (pattern, pass) calls at once; combine.py merges the passes (one
     pass is noisy: two passes agreed on about half, 2026-10-27);
  3. per pattern, the final order is the mean of two ranks: the combined DeepSeek rank and the rerank rank (a
     candidate missing from a list gets that list's length + 1). This is the per-pattern form of sibling2's
     "DeepSeek top 50 + rerank top 50" union;
  4. assignment: patterns are filled scarcest first, so a repo that sits in several patterns goes to the pattern
     that needs it most; each repo is used once.

Writes out/selection/<pattern>/..., out/selection/selected.tsv and out/selection/summary.json.

  CWE_MODELS_ENV=/Users/dev/terminal-bench/.env CLAUDE_BIN=... python3 -I diversity_population/select_per_pattern.py
"""
import argparse, csv, json, os, sqlite3, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
C = HERE / "copied"
OUT = HERE / "out" / "selection"
RECS = HERE / "out" / "screener"
IDX = HERE / "out" / "index" / "candidates.sqlite"


def run(cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if r.returncode:
        raise RuntimeError(f"{cmd[:3]} exit {r.returncode}: {r.stdout[-400:]} {r.stderr[-400:]}")
    return r.stdout


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-pattern", type=int, default=12)
    ap.add_argument("--pick-n", type=int, default=15, help="DeepSeek returns its top N per pattern and pass")
    ap.add_argument("--passes", type=int, default=3, help="DeepSeek passes per pattern (the latest pipeline uses 3)")
    ap.add_argument("--parallel", type=int, default=66)
    ap.add_argument("--only", nargs="*", default=[], help="patterns to run (default: all)")
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    pats = json.load(open(HERE / "patterns.json"))["patterns"]
    jobs = [json.loads(l) for l in open(HERE / "out" / "screener_jobs.jsonl")]
    have = {p.stem for p in RECS.glob("*.json") if not p.name.endswith(".run.json")}
    by_pat = {p["id"]: [j for j in jobs if p["id"] in j["patterns"] and j["entry_id"] in have] for p in pats}
    repo_of = {j["entry_id"]: j["repo"] for j in jobs}

    # 1. rerank over every record
    rk = OUT / "rank"; rk.mkdir(exist_ok=True)
    print(run([sys.executable, "-I", str(C / "sibling/3-rank/rerank.py"), str(IDX), str(rk), "--screened", str(RECS)])
          .strip().splitlines()[-1])
    rr = {}
    for row in csv.DictReader(open(rk / "host-rank-screened.tsv"), delimiter="\t"):
        rr[row["entry_id"]] = float(row["score_read"])

    # 2. DeepSeek select: every (pattern, pass) runs at once, then the passes are combined per pattern
    todo = [p["id"] for p in pats if not a.only or p["id"] in a.only]
    for pid in todo:
        d = OUT / pid; d.mkdir(exist_ok=True)
        ids = d / "ids.txt"; ids.write_text("".join(j["entry_id"] + "\n" for j in by_pat[pid]))
        run([sys.executable, "-I", str(C / "sibling/4-select/make_pool.py"), "--recs", str(RECS),
             "--out", str(d / "pool.jsonl"), "--ids", str(ids)])
    def one(job):
        pid, k = job
        pd = OUT / pid / f"pass{k}"
        for attempt in range(2):                      # one retry: a pass that returns no JSON array is redone once
            if (pd / "selection_deepseek.json").is_file():
                break
            try:
                run(["bash", str(C / "sibling/4-select/select.sh"), "deepseek", str(OUT / pid / "pool.jsonl"), str(pd),
                     str(a.pick_n)])
            except RuntimeError as e:
                print(f"pass failed: {pid} pass{k} attempt {attempt + 1}: {str(e)[:160]}", flush=True)
        return pid, k, (pd / "selection_deepseek.json").is_file()
    jobs = [(pid, k) for pid in todo for k in range(1, a.passes + 1)]
    with ThreadPoolExecutor(a.parallel) as ex:
        for pid, k, ok in ex.map(one, jobs):
            print(f"pass {'done' if ok else 'MISSING'}: {pid} pass{k}", flush=True)
    for pid in todo:
        d = OUT / pid
        passes = [str(d / f"pass{k}" / "selection_deepseek.json") for k in range(1, a.passes + 1)
                  if (d / f"pass{k}" / "selection_deepseek.json").is_file()]
        if not passes:
            raise SystemExit(f"no DeepSeek pass succeeded for {pid}")
        run([sys.executable, "-I", str(C / "sibling/4-select/combine.py"), str(d / "combined.json"),
             str(d / "pool.jsonl"), *passes])

    # 3. per-pattern order: mean of the DeepSeek rank and the rerank rank
    order = {}
    for pid in todo:
        ids = [j["entry_id"] for j in by_pat[pid]]
        ds = [str(x["entry_id"]) for x in json.load(open(OUT / pid / "combined.json"))]
        rrk = sorted(ids, key=lambda e: (-rr.get(e, -99), e))
        def rank(lst, e):
            return lst.index(e) + 1 if e in lst else len(lst) + 1
        order[pid] = sorted(ids, key=lambda e: ((rank(ds, e) + rank(rrk, e)) / 2, rank(ds, e), e))

    # 4. assignment, scarcest pattern first; a repo is used once
    used, picked = set(), {}
    for pid in sorted(todo, key=lambda p: len(order[p])):
        picked[pid] = []
        for e in order[pid]:
            if len(picked[pid]) >= a.per_pattern:
                break
            if repo_of[e] in used:
                continue
            used.add(repo_of[e]); picked[pid].append(e)
    names = {p["id"]: p["name"] for p in pats}
    with open(OUT / "selected.tsv", "w") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(["pattern", "slot", "entry_id", "repo", "score_read", "deepseek_score", "deepseek_picked_by"])
        for pid in todo:
            comb = {str(x["entry_id"]): x for x in json.load(open(OUT / pid / "combined.json"))}
            for i, e in enumerate(picked[pid], 1):
                c = comb.get(e, {})
                w.writerow([pid, i, e, repo_of[e], rr.get(e, ""), c.get("score", 0), c.get("picked_by", 0)])
    summary = {pid: {"name": names[pid], "screened": len(by_pat[pid]), "picked": len(picked[pid])} for pid in todo}
    json.dump(summary, open(OUT / "summary.json", "w"), indent=1)
    print(json.dumps({"total": sum(len(v) for v in picked.values()), "per_pattern": {k: v["picked"] for k, v in summary.items()}}))


if __name__ == "__main__":
    main()
