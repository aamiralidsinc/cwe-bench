#!/usr/bin/env python3
"""Do attack-taxonomy labels relate to LLM repair success? (research item 5)

    python3 research/raw/item5-attack-taxonomies/analyse_labels.py [--runs-filter deepseek] [--within-owasp]

Same method as item 4 (../item4-severity/analyse_outcomes.py): unit = one CVE within one benchmark,
scored by the share of the benchmark's non-excluded runs that fixed it; every label is compared
WITHIN each benchmark, combined as a CVE-weighted average, and tested by permuting the label among
CVEs inside each benchmark. Each class of a multi-valued label (e.g. a CAPEC mechanism) is tested
as "CVE has this class" vs "CVE has a label but not this class"; unlabelled CVEs are left out.
With many labels tested at once, q is the Benjamini-Hochberg false-discovery-rate adjusted p.

--within-screener stratifies by benchmark x the sourcer's current weakness points (weights.json
via osv_sourcer.weakness_points), so a label only counts if it separates CVEs our screener
already scores the same. The screener's own points are also tested ("screener: weakness points
>= favoured threshold").

--within-owasp also stratifies by the CVE's OWASP 2025 category (from its first mapped CWE), so a
label only counts if it matters among CVEs of the same weakness family. Every label here is derived
from the CWE, so this asks whether the attack view adds anything beyond the weakness category.
"""
import argparse
import csv
import json
import random
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
I4 = HERE.parent / "item4-severity"
MIN_GROUP = 25                 # a class needs at least this many units on each side to be tested

MULTI = ["mechanism", "domain", "attack_tactic", "stride"]
BINARY = {
    "capec_skill: low skill suffices": ("capec_skill_min", lambda v: v == "1"),
    "capec_likelihood: high": ("capec_likelihood_max", lambda v: v == "3"),
    "cvss_av: network": ("cvss_av", lambda v: v == "NETWORK"),
    "cvss_pr: none needed": ("cvss_pr", lambda v: v == "NONE"),
    "cvss_ui: none needed": ("cvss_ui", lambda v: v == "NONE"),
    "cvss_c: high": ("cvss_c", lambda v: v == "HIGH"),
    "cvss_i: high": ("cvss_i", lambda v: v == "HIGH"),
    "cvss_a: high": ("cvss_a", lambda v: v == "HIGH"),
    "has an ATT&CK mapping": ("n_attack_techniques", lambda v: v != "0"),
    "screener: weakness points >= favoured threshold": ("screener_favoured", lambda v: v == "1"),
}


def screener():
    sys.path.insert(0, str(HERE.parents[2] / "sourcer"))
    import osv_sourcer
    thr = osv_sourcer.weights()["weakness"]["favoured_threshold"]

    def points(cwes):
        if not cwes:
            return None, None
        pts = osv_sourcer.weakness_points(" ".join(f"CWE-{w}" for w in cwes.split(";")))[0]
        return pts, pts >= thr
    return points


def owasp_of():
    """CWE id -> OWASP 2025 category, falling back to the nearest mapped Research-view ancestor
    (as the sourcer does)."""
    m = json.loads((HERE.parents[1] / "owasp2025_cwe_map.json").read_text())["categories"]
    direct = {str(c): cat for cat, info in m.items() for c in info["cwes"]}
    parent = {r["id"]: r["parent"] for r in csv.DictReader(open(HERE.parents[1] / "cwe_hierarchy.tsv"),
                                                           delimiter="\t")}
    out = {}
    for w in parent:
        p, hops = w, 0
        while p and hops < 10 and p not in direct:
            p, hops = parent.get(p), hops + 1
        if p in direct:
            out[w] = direct[p]
    return out


def load(run_filter, within_owasp, within_screener=False):
    labels = {r["cve"]: r for r in csv.DictReader(open(HERE / "cve_attack_labels.tsv"), delimiter="\t")}
    acc = defaultdict(list)
    for r in csv.DictReader(open(I4 / "outcomes_long.tsv"), delimiter="\t"):
        if r["excluded_run"] or (run_filter and run_filter not in r["run"].lower()):
            continue
        acc[(r["benchmark"], r["cve"])].append(int(r["solved"]))
    cat = owasp_of() if within_owasp else {}
    points = screener()
    units = []
    for (bench, cve), v in acc.items():
        lab = labels.get(cve)
        if not lab:
            continue
        stratum = bench
        pts, fav = points(lab["cwes"])
        lab = {**lab, "screener_favoured": "" if fav is None else str(int(fav))}
        if within_screener:
            if pts is None:
                continue
            stratum = f"{bench}|pts{pts}"
        if within_owasp:
            c = next((cat[w] for w in lab["cwes"].split(";") if w in cat), None)
            if not c:
                continue
            stratum = f"{bench}|{c}"
        units.append({"stratum": stratum, "bench": bench, "rate": sum(v) / len(v), **lab})
    return units


def test(units, label, n=2000, seed=11):
    """label(u) -> True / False / None. Returns diff, p, n_yes, n_no, fixed_yes, fixed_no."""
    strata = defaultdict(list)
    for u in units:
        lab = label(u)
        if lab is not None:
            strata[u["stratum"]].append((u["rate"], lab))
    usable = {s: g for s, g in strata.items() if any(l for _, l in g) and not all(l for _, l in g)}
    ny = sum(l for g in usable.values() for _, l in g)
    nn = sum(not l for g in usable.values() for _, l in g)
    if ny < MIN_GROUP or nn < MIN_GROUP:
        return None
    pre = []
    for g in usable.values():
        rates = [r for r, _ in g]
        labs = [l for _, l in g]
        pre.append((rates, labs, sum(labs), len(g), sum(rates)))
    den = sum(len(g) for g in usable.values())

    def diff(shuffle=None):
        num = 0.0
        for rates, labs, k, size, total in pre:
            if shuffle:
                labs = labs[:]
                shuffle(labs)
            s_yes = sum(r for r, l in zip(rates, labs) if l)
            num += (s_yes / k - (total - s_yes) / (size - k)) * size
        return num / den

    obs = diff()
    rnd = random.Random(seed)
    hits = sum(abs(diff(rnd.shuffle)) >= abs(obs) - 1e-12 for _ in range(n))
    fy = sum(r for g in usable.values() for r, l in g if l) / ny
    fn = sum(r for g in usable.values() for r, l in g if not l) / nn
    return obs, (hits + 1) / (n + 1), ny, nn, fy, fn


def bh(ps):
    order = sorted(range(len(ps)), key=lambda i: ps[i])
    q, prev = [0.0] * len(ps), 1.0
    for rank, i in reversed(list(enumerate(order, 1))):
        prev = min(prev, ps[i] * len(ps) / rank)
        q[i] = prev
    return q


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs-filter", default="")
    ap.add_argument("--within-owasp", action="store_true")
    ap.add_argument("--within-screener", action="store_true")
    a = ap.parse_args()
    units = load(a.runs_filter.lower(), a.within_owasp, a.within_screener)
    tests = []
    for col in MULTI:
        classes = sorted({v for u in units for v in u[col].split(";") if v})
        for c in classes:
            tests.append((f"{col}: {c}",
                          lambda u, col=col, c=c: None if not u[col] else c in u[col].split(";")))
    for name, (col, f) in BINARY.items():
        tests.append((name, lambda u, col=col, f=f: None if u[col] == "" else f(u[col])))
    rows = []
    for name, label in tests:
        r = test(units, label)
        if r:
            rows.append((name, *r))
    qs = bh([r[2] for r in rows])
    print(f"{len(units)} CVE-in-benchmark units"
          + (f", runs matching '{a.runs_filter}'" if a.runs_filter else "")
          + (", stratified by benchmark x OWASP category" if a.within_owasp else
             ", stratified by benchmark x screener weakness points" if a.within_screener else
             ", stratified by benchmark")
          + f"; {len(rows)} labels tested (each side >= {MIN_GROUP} units)")
    print(f"{'label':48} {'n yes':>6} {'n no':>6} {'fixed yes':>9} {'fixed no':>9} {'diff':>7} {'p':>6} {'q':>6}")
    for (name, d, p, ny, nn, fy, fn), q in sorted(zip(rows, qs), key=lambda x: x[0][2]):
        flag = "  *" if q < 0.05 else ("  ." if p < 0.05 else "")
        print(f"{name[:48]:48} {ny:>6} {nn:>6} {fy:>9.1%} {fn:>9.1%} {d:>+7.1%} {p:>6.3f} {q:>6.3f}{flag}")
    print("(* q < 0.05 after false-discovery correction; . p < 0.05 uncorrected only)")


if __name__ == "__main__":
    main()
