#!/usr/bin/env python3
"""Replace the weak picks of the 6 topped-up patterns (owner, 2026-10-28).

Rule:
- the 16 other patterns keep their 12 picks unchanged (out/selection/selected.tsv);
- in each of the 6 patterns, a pick with score_read >= THRESHOLD (12, the median of the first 581 records) stays;
- the freed slots are filled from the pattern's expanded pool (old + top-up candidates), in the same order as the
  first selection (mean of the 3-pass DeepSeek rank and the rerank rank), taking only candidates with score_read >=
  THRESHOLD and repos not already selected anywhere;
- if a pattern runs short, its best remaining weak picks are kept so every pattern still has 12.

Uses the same copies as select_per_pattern.py (rerank.py, make_pool.py, select.sh, combine.py); the DeepSeek passes
run again for the 6 patterns because their pools changed. The first selection is kept; the result is
out/selection/selected_v2.tsv plus out/selection/topup_changes.tsv.

  CLAUDE_BIN=... python3 -I topup_replace.py
"""
import argparse, csv, json, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
C = HERE / "copied"; OUT = HERE / "out" / "selection"; RECS = HERE / "out" / "screener"
IDX = HERE / "out" / "index" / "candidates.sqlite"
P6 = ["memory-safety", "algorithmic-dos", "redos", "sql-query-injection", "deserialization", "input-validation"]
THRESHOLD = 12.0


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError(f"{cmd[:3]} exit {r.returncode}: {r.stdout[-300:]} {r.stderr[-300:]}")
    return r.stdout


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--passes", type=int, default=3)
    ap.add_argument("--pick-n", type=int, default=15)
    a = ap.parse_args()
    jobs = [json.loads(l) for l in open(HERE / "out/screener_jobs.jsonl")]
    have = {p.stem for p in RECS.glob("*.json") if not p.name.endswith(".run.json")}
    repo_of = {j["entry_id"]: j["repo"] for j in jobs}
    by_pat = {p: [j["entry_id"] for j in jobs if p in j["patterns"] and j["entry_id"] in have] for p in P6}

    rk = OUT / "rank_v2"; rk.mkdir(parents=True, exist_ok=True)
    print(run([sys.executable, "-I", str(C / "sibling/3-rank/rerank.py"), str(IDX), str(rk), "--screened", str(RECS)])
          .strip().splitlines()[-1].split(" skipped")[0], flush=True)
    rr = {r["entry_id"]: float(r["score_read"]) for r in csv.DictReader(open(rk / "host-rank-screened.tsv"), delimiter="\t")}

    V2 = OUT / "v2"
    for p in P6:
        d = V2 / p; d.mkdir(parents=True, exist_ok=True)
        (d / "ids.txt").write_text("".join(e + "\n" for e in by_pat[p]))
        run([sys.executable, "-I", str(C / "sibling/4-select/make_pool.py"), "--recs", str(RECS), "--out",
             str(d / "pool.jsonl"), "--ids", str(d / "ids.txt")])

    def one(job):
        p, k = job
        pd = V2 / p / f"pass{k}"
        for attempt in range(2):
            if (pd / "selection_deepseek.json").is_file():
                break
            try:
                run(["bash", str(C / "sibling/4-select/select.sh"), "deepseek", str(V2 / p / "pool.jsonl"), str(pd),
                     str(a.pick_n)])
            except RuntimeError as e:
                print(f"pass failed: {p} pass{k} attempt {attempt + 1}: {str(e)[:120]}", flush=True)
        return p, k, (pd / "selection_deepseek.json").is_file()
    with ThreadPoolExecutor(len(P6) * a.passes) as ex:
        for p, k, ok in ex.map(one, [(p, k) for p in P6 for k in range(1, a.passes + 1)]):
            print(f"pass {'done' if ok else 'MISSING'}: {p} pass{k}", flush=True)
    order = {}
    for p in P6:
        d = V2 / p
        passes = [str(d / f"pass{k}" / "selection_deepseek.json") for k in range(1, a.passes + 1)
                  if (d / f"pass{k}" / "selection_deepseek.json").is_file()]
        run([sys.executable, "-I", str(C / "sibling/4-select/combine.py"), str(d / "combined.json"), str(d / "pool.jsonl"),
             *passes])
        ds = [str(x["entry_id"]) for x in json.load(open(d / "combined.json"))]
        rrk = sorted(by_pat[p], key=lambda e: (-rr.get(e, -99), e))
        rank = lambda lst, e: lst.index(e) + 1 if e in lst else len(lst) + 1
        order[p] = sorted(by_pat[p], key=lambda e: ((rank(ds, e) + rank(rrk, e)) / 2, rank(ds, e), e))

    v1 = list(csv.DictReader(open(OUT / "selected.tsv"), delimiter="\t"))
    keep = [r for r in v1 if r["pattern"] not in P6]
    used = {r["repo"] for r in keep}
    changes, final = [], list(keep)
    for p in sorted(P6, key=lambda p: len(order[p])):          # scarcest first, as in the first selection
        old = [r for r in v1 if r["pattern"] == p]
        strong = [r["entry_id"] for r in old if rr.get(r["entry_id"], -99) >= THRESHOLD]
        weak = sorted([r["entry_id"] for r in old if rr.get(r["entry_id"], -99) < THRESHOLD], key=lambda e: -rr.get(e, -99))
        picks = list(strong); used |= {repo_of[e] for e in strong}
        for e in order[p]:
            if len(picks) >= 12:
                break
            if e in picks or repo_of[e] in used or rr.get(e, -99) < THRESHOLD:
                continue
            picks.append(e); used.add(repo_of[e])
        for e in weak:                                          # short of strong ones: keep the best weak picks
            if len(picks) >= 12:
                break
            if repo_of[e] not in used:
                picks.append(e); used.add(repo_of[e])
        for e in weak:
            if e not in picks:
                changes.append((p, "out", e, repo_of[e], rr.get(e)))
        for e in picks:
            if e not in [r["entry_id"] for r in old]:
                changes.append((p, "in", e, repo_of[e], rr.get(e)))
        comb = {str(x["entry_id"]): x for x in json.load(open(V2 / p / "combined.json"))}
        for i, e in enumerate(picks, 1):
            c = comb.get(e, {})
            final.append({"pattern": p, "slot": str(i), "entry_id": e, "repo": repo_of[e], "score_read": rr.get(e, ""),
                          "deepseek_score": c.get("score", 0), "deepseek_picked_by": c.get("picked_by", 0)})
    cols = ["pattern", "slot", "entry_id", "repo", "score_read", "deepseek_score", "deepseek_picked_by"]
    with open(OUT / "selected_v2.tsv", "w") as f:
        w = csv.DictWriter(f, cols, delimiter="\t"); w.writeheader(); w.writerows(final)
    with open(OUT / "topup_changes.tsv", "w") as f:
        w = csv.writer(f, delimiter="\t"); w.writerow(["pattern", "change", "entry_id", "repo", "score_read"]); w.writerows(changes)
    per = {}
    for r in final:
        per[r["pattern"]] = per.get(r["pattern"], 0) + 1
    weak_left = sum(1 for r in final if r["pattern"] in P6 and float(r["score_read"] or -99) < THRESHOLD)
    print(json.dumps({"total": len(final), "distinct_repos": len({r['repo'] for r in final}),
                      "replaced": sum(1 for c in changes if c[1] == "in"), "weak_kept_in_6": weak_left,
                      "per_pattern": per}))


if __name__ == "__main__":
    main()
