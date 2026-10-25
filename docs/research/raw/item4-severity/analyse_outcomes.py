#!/usr/bin/env python3
"""Cross-benchmark test: do CVSS, EPSS or CISA KEV relate to LLM repair success? (item 4)

    python3 research/raw/item4-severity/analyse_outcomes.py [--runs-filter deepseek]

Input: outcomes_long.tsv (build_outcomes.py) and severity.tsv (fetch_severity.py).
Unit: one CVE within one benchmark, scored by the share of that benchmark's (non-excluded)
runs that solved it. Benchmarks differ hugely in difficulty, so every comparison is made
WITHIN a benchmark and combined as a CVE-weighted average of the per-benchmark differences.
p-values: severity labels are permuted among CVEs within each benchmark (stratified), so
benchmark difficulty cannot create an effect.
"""
import argparse
import csv
import random
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load(run_filter):
    sev = {r["cve"]: r for r in csv.DictReader(open(HERE / "severity.tsv"), delimiter="\t")}
    acc = defaultdict(list)                                   # (bench, cve) -> [solved...]
    for r in csv.DictReader(open(HERE / "outcomes_long.tsv"), delimiter="\t"):
        if r["excluded_run"] or (run_filter and run_filter not in r["run"].lower()):
            continue
        acc[(r["benchmark"], r["cve"])].append(int(r["solved"]))
    units = []
    for (bench, cve), v in acc.items():
        s = sev.get(cve)
        if s:
            units.append({"bench": bench, "cve": cve, "rate": sum(v) / len(v), "runs": len(v), **s})
    return units


def cvss_hi(u):
    try:
        return float(u["cvss_score"]) >= 7.0
    except ValueError:
        return None


def kev(u):
    return u["kev"] == "1"


def epss_hi_factory(units):
    med = {}
    for b in {u["bench"] for u in units}:
        vals = sorted(float(u["epss_percentile"]) for u in units if u["bench"] == b and u["epss_percentile"])
        med[b] = vals[len(vals) // 2] if vals else None

    def f(u):
        try:
            return float(u["epss_percentile"]) >= med[u["bench"]]
        except (ValueError, TypeError):
            return None
    return f


def stratified_diff(units, label):
    """CVE-weighted mean over benchmarks of (mean rate where label) - (mean rate where not label)."""
    num = den = 0.0
    per = {}
    for b in sorted({u["bench"] for u in units}):
        g = [u for u in units if u["bench"] == b and label(u) is not None]
        yes = [u["rate"] for u in g if label(u)]
        no = [u["rate"] for u in g if not label(u)]
        if yes and no:
            d = sum(yes) / len(yes) - sum(no) / len(no)
            per[b] = (d, len(yes), len(no), sum(yes) / len(yes), sum(no) / len(no))
            num += d * len(g)
            den += len(g)
    return (num / den if den else None), per


def perm_p(units, label, n=4000, seed=7):
    obs, _ = stratified_diff(units, label)
    if obs is None:
        return None, None
    rnd = random.Random(seed)
    by = defaultdict(list)
    for u in units:
        if label(u) is not None:
            by[u["bench"]].append(u)
    hits = 0
    for _ in range(n):
        shuffled = {}
        for b, g in by.items():
            labs = [label(u) for u in g]
            rnd.shuffle(labs)
            for u, l in zip(g, labs):
                shuffled[(b, u["cve"])] = l
        d, _ = stratified_diff(units, lambda u: shuffled.get((u["bench"], u["cve"])))
        if d is not None and abs(d) >= abs(obs):
            hits += 1
    return obs, hits / n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs-filter", default="", help="only runs whose name contains this (e.g. deepseek)")
    ap.add_argument("--drop", action="append", default=[], help="leave this benchmark out (repeatable)")
    a = ap.parse_args()
    units = [u for u in load(a.runs_filter.lower()) if u["bench"] not in a.drop]
    print(f"{len(units)} CVE-in-benchmark units with severity"
          + (f" (runs matching '{a.runs_filter}')" if a.runs_filter else ""))
    for name, label in (("CVSS >= 7.0 (high/critical) vs < 7.0", cvss_hi),
                        ("EPSS above vs below the benchmark's median", epss_hi_factory(units)),
                        ("in CISA KEV vs not", kev)):
        obs, p = perm_p(units, label)
        _, per = stratified_diff(units, label)
        print(f"\n== {name} ==")
        for b, (d, ny, nn, ry, rn) in per.items():
            print(f"  {b:13} yes n={ny:>3} solved {ry:5.1%}   no n={nn:>3} solved {rn:5.1%}   diff {d:+6.1%}")
        if obs is None:
            print("  no benchmark has both groups: cannot test")
        else:
            print(f"  COMBINED (CVE-weighted, within-benchmark) diff {obs:+.1%}   stratified permutation p = {p:.3f}")


if __name__ == "__main__":
    main()
