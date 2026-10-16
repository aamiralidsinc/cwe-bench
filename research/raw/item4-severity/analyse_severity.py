#!/usr/bin/env python3
"""Does CVSS / EPSS / KEV relate to LLM repair success? (research item 4, our own evidence)

    python3 research/raw/item4-severity/analyse_severity.py

Joins SEC-bench's published per-instance patch results (7 agent setups, 200 real C/C++
CVEs; copied in ~/.tb-graders/cwe/research-raw/item1-owasp-and-repair/secb/) with each
CVE's CVSS, EPSS and KEV status (severity.tsv from fetch_severity.py). For each signal it
reports solve rates per group, per setup and pooled, plus a two-sided permutation test on
the pooled difference, and writes the joined table to secbench_severity_joined.tsv.
"""
import csv
import json
import random
from pathlib import Path

HERE = Path(__file__).resolve().parent
SECB = Path.home() / ".tb-graders/cwe/research-raw/item1-owasp-and-repair/secb"
RUNS = ["oh_sonnet", "swea_sonnet", "aider_sonnet", "agenticrepair_gpt-5.2",
        "agenticrepair_gpt-5-mini", "smola_gpt-5.2", "smola_gpt-5-mini"]


def load():
    inst = json.loads((SECB / "cwe.json").read_text())             # instance id -> {cve, cwes}
    sev = {r["cve"]: r for r in csv.DictReader(open(HERE / "severity.tsv"), delimiter="\t")}
    res = {}
    for run in RUNS:
        for r in json.loads((SECB / f"{run}.slim.json").read_text()):
            res.setdefault(r["id"], {})[run] = bool(r["success"])
    rows = []
    for iid, meta in inst.items():
        s = sev.get(meta.get("cve") or "")
        if not s or iid not in res:
            continue
        rows.append({"id": iid, "cve": meta["cve"], **{k: s[k] for k in s if k != "cve"},
                     **{run: res[iid].get(run) for run in RUNS}})
    return rows


def band(r):
    try:
        x = float(r["cvss_score"])
    except ValueError:
        return None
    return "critical (9-10)" if x >= 9 else "high (7-8.9)" if x >= 7 else "medium (4-6.9)" if x >= 4 else "low (<4)"


def epss_median_split(rows):
    """EPSS split at the dataset's own median (benchmark CVEs skew high, so a fixed 50th
    percentile cut gives lopsided groups)."""
    vals = sorted(float(r["epss_percentile"]) for r in rows if r["epss_percentile"])
    med = vals[len(vals) // 2] if vals else 0

    def key(r):
        try:
            return "EPSS above median" if float(r["epss_percentile"]) >= med else "EPSS below median"
        except ValueError:
            return None
    return key


def kev(r):
    return "in KEV" if r["kev"] == "1" else "not in KEV"


def rate(rows, run):
    vals = [r[run] for r in rows if r[run] is not None]
    return (sum(vals) / len(vals), len(vals)) if vals else (None, 0)


def pooled(rows):
    vals = [r[run] for r in rows for run in RUNS if r[run] is not None]
    return sum(vals) / len(vals) if vals else None


def perm_test(groups, n=5000, seed=1):
    """Two groups: p-value of the pooled solve-rate difference by label permutation."""
    (a, ra), (b, rb) = groups
    obs = abs(pooled(ra) - pooled(rb))
    both, k, rnd, hits = ra + rb, len(ra), random.Random(seed), 0
    for _ in range(n):
        rnd.shuffle(both)
        if abs(pooled(both[:k]) - pooled(both[k:])) >= obs:
            hits += 1
    return obs, hits / n


def report(rows, name, key):
    print(f"\n== {name} ==")
    groups = {}
    for r in rows:
        g = key(r)
        if g:
            groups.setdefault(g, []).append(r)
    print(f"{'group':18} {'n':>4} " + " ".join(f"{r[:12]:>12}" for r in RUNS) + "   pooled")
    for g, rs in sorted(groups.items()):
        cells = []
        for run in RUNS:
            v, n = rate(rs, run)
            cells.append(f"{v:12.0%}" if v is not None else f"{'-':>12}")
        print(f"{g:18} {len(rs):>4} " + " ".join(cells) + f"   {pooled(rs):.0%}")
    if len(groups) == 2:
        obs, p = perm_test(sorted(groups.items()))
        print(f"pooled difference {obs:.1%}, permutation p = {p:.3f}")
    return groups


def main():
    rows = load()
    print(f"{len(rows)} SEC-bench CVE instances joined with severity data")
    cols = list(rows[0].keys())
    with open(HERE / "secbench_severity_joined.tsv", "w") as f:
        f.write("\t".join(cols) + "\n")
        for r in rows:
            f.write("\t".join("" if r[c] is None else str(r[c]) for c in cols) + "\n")
    report(rows, "CVSS band", band)
    report(rows, "CVSS high+critical vs below",
           lambda r: (None if band(r) is None else
                      "high or critical" if band(r).startswith(("high", "crit")) else "medium or low"))
    report(rows, "EPSS (median split)", epss_median_split(rows))
    report(rows, "CISA KEV", kev)


if __name__ == "__main__":
    main()


def vulnrepaireval():
    """Second dataset: VulnRepairEval Table 6 (23 Python CVEs x 6 models, incl. DeepSeek R1)."""
    sev = {r["cve"]: r for r in csv.DictReader(open(HERE / "severity.tsv"), delimiter="\t")}
    rows = list(csv.DictReader((l for l in open(HERE / "vulnrepaireval_table6.tsv")
                                if not l.startswith("#")), delimiter="\t"))
    models = [c for c in rows[0] if c not in ("cve", "description")]
    joined = []
    for r in rows:
        s = sev.get(r["cve"])
        if s:
            joined.append({**s, **{m: r[m] == "1" for m in models}})
    print(f"\n\n######## VulnRepairEval: {len(joined)} CVEs x {len(models)} models ########")
    global RUNS
    saved, RUNS = RUNS, models
    try:
        report(joined, "CVSS high+critical vs below",
               lambda r: (None if band(r) is None else
                          "high or critical" if band(r).startswith(("high", "crit")) else "medium or low"))
        report(joined, "EPSS (median split)", epss_median_split(joined))
        report(joined, "CISA KEV", kev)
    finally:
        RUNS = saved


if __name__ == "__main__":
    vulnrepaireval()
