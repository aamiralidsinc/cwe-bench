#!/usr/bin/env python3
"""Step 3 of the stacking pipeline: score stacked designs from the reader's JSON (STACKING-EXPLORATION.md §4).

Probabilistic, on D1-D3 only (D4/D5 deferred). Per model m and independent concept c:
  p(c,m)    = max over the concept's traps of the tier miss probability for m (or the kind prior)
  p_site    = per-extra-location factor, capped
  p_concept = 1 - (1 - p(c,m)) * (1 - p_site)
  P_solve   = prod over concepts of (1 - p_concept);  P_fail3 = (1 - P_solve) ** attempts
  score     = P_fail3(deepseek) * P_fail3(mimo)
It scores the reader's chosen design (falls back to all traps), and flags designs that lack a
DeepSeek-type or MiMo-type trap, or that rest on a single concept.
Assumes independent misses, so scores are upper bounds until calibrated (§6).

  python3 -I stacking/score_stack.py [--reader-dir stacking/out/reader]
Outputs: stacking/out/stack_scores.tsv and stack_scores.md
"""
import argparse, glob, json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W = json.load(open(os.path.join(ROOT, "sourcer", "stacking_weights.json")))
MODELS = ("deepseek", "mimo")


def concept_probs(traps, groups, model):
    tiers = W["tier_miss_probability"][model]
    by_id = {t["id"]: t for t in traps}
    out = []
    for g in groups:
        members = [by_id[i] for i in g if i in by_id]
        if not members:
            continue
        p = max(tiers.get(t.get(f"tier_{model}") or W["kind_prior_tier"].get(t.get("mechanism", ""), "medium"), 0.15)
                for t in members)
        locs = sum(max(1, len(t.get("locations") or [])) for t in members)
        site = min(W["site_factor"]["max"], W["site_factor"]["per_extra_location"] * max(0, locs - 1))
        out.append((tuple(g), 1 - (1 - p) * (1 - site)))
    return out


def fail3(pcs):
    ps = 1.0
    for _, p in pcs:
        ps *= (1 - p)
    return (1 - ps) ** W["attempts"]


def score_design(rec):
    traps = rec.get("traps") or []
    chosen = set((rec.get("design") or {}).get("traps") or []) or {t["id"] for t in traps}
    traps = [t for t in traps if t["id"] in chosen]
    groups = [[i for i in g if i in chosen] for g in (rec.get("independent_groups") or [[t["id"]] for t in traps])]
    groups = [g for g in groups if g]
    grouped = {i for g in groups for i in g}
    groups += [[t["id"]] for t in traps if t["id"] not in grouped]
    res = {}
    for m in MODELS:
        pcs = concept_probs(traps, groups, m)
        res[m] = (fail3(pcs), pcs)
    score = res["deepseek"][0] * res["mimo"][0]
    # single-carry check: drop each model's hardest concept, re-score
    drop, weakest_without = 1.0, 1.0
    for m in MODELS:
        pcs = res[m][1]
        without = fail3([x for x in pcs if x is not max(pcs, key=lambda y: y[1])]) if pcs else 0.0
        drop *= without
        weakest_without = min(weakest_without, without)
    types = {t.get("type") for t in traps}
    flags = []
    if not (types & {"deepseek", "both"}):
        flags.append("no-deepseek-type")
    if not (types & {"mimo", "both"}):
        flags.append("no-mimo-type")
    if len(groups) < 2:
        flags.append("single-concept")
    if weakest_without < W["single_carry_warning"]["min_p_fail3_without_hardest"]:
        flags.append("single-trap-carries")
    if rec.get("fairness_risks"):
        flags.append(f"fairness-risks:{len(rec['fairness_risks'])}")
    return dict(candidate=rec.get("candidate_id"), pattern=rec.get("pattern"), repo=rec.get("repo"),
                concepts=len(groups), traps=len(traps), score=round(score, 3),
                p_fail3_deepseek=round(res["deepseek"][0], 3), p_fail3_mimo=round(res["mimo"][0], 3),
                score_without_hardest=round(drop, 3), effort_min=rec.get("effort_minutes"),
                usable=rec.get("usable"), flags=";".join(flags))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reader-dir", default=os.path.join(ROOT, "stacking", "out", "reader"))
    a = ap.parse_args()
    rows = []
    for f in sorted(glob.glob(os.path.join(a.reader_dir, "*.json"))):
        if f.endswith(".run.json") or os.path.basename(f).startswith("_"):
            continue   # the CLI's own output and logs, not reader records
        try:
            rows.append(score_design(json.load(open(f))))
        except Exception as e:
            print(f"skip {f}: {e}")
    if not rows:
        print("no reader records yet")
        return
    rows.sort(key=lambda r: -r["score"])
    cols = list(rows[0].keys())
    out = os.path.join(ROOT, "stacking", "out")
    with open(os.path.join(out, "stack_scores.tsv"), "w") as o:
        o.write("\t".join(cols) + "\n")
        for r in rows:
            o.write("\t".join(str(r[c]) for c in cols) + "\n")
    md = [f"# Stacked design scores (weights v{W['version']}; upper bounds until calibrated)", "",
          "| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    md += ["| " + " | ".join(str(r[c]) for c in cols) + " |" for r in rows]
    open(os.path.join(out, "stack_scores.md"), "w").write("\n".join(md) + "\n")
    print("\n".join(md[:12]))


if __name__ == "__main__":
    main()
