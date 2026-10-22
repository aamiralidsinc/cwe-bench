#!/usr/bin/env python3
"""Build the reader job list (step 2 input) from the Phase 1 shortlists.

Jobs (one JSON object per line in stacking/out/reader_jobs.jsonl):
  H4 : unbuilt hosts offering both a DeepSeek-type and a MiMo-type trap (h4_candidates.tsv)
  H3 : ready fix-of-fix pairs (h3b_pairs.tsv), ordered by the SZZ result:
       H3a-regression, H3b-touching, H3b-elsewhere, add-only, then pairs not yet mined
Each job carries `pin_from`: commits whose EARLIEST one's parent is the pinned commit (the launcher
resolves it in the clone), so the code is checked out before any of the fixes.

  python3 -I stacking/make_reader_jobs.py [--h4 9] [--h3 12]
"""
import argparse, csv, json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "stacking", "out")
RECS = os.path.join(ROOT, "sourcer", "review", "screener-v2")
DOS = {"CWE-400", "CWE-770", "CWE-1333", "CWE-674", "CWE-834", "CWE-407", "CWE-606"}
SZZ_ORDER = {"H3a-regression": 0, "H3b-touching": 1, "H3b-elsewhere": 2, "add-only": 3}


def tsv(name):
    p = os.path.join(OUT, name)
    return list(csv.DictReader(open(p), delimiter="\t")) if os.path.isfile(p) else []


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--h4", type=int, default=9)
    ap.add_argument("--h3", type=int, default=12)
    a = ap.parse_args()
    jobs = []
    h4 = [r for r in tsv("h4_candidates.tsv") if r["both"] == "True" and r["built"] == "False"]
    for r in h4[: a.h4]:
        rec_path = os.path.join(RECS, f"{r['entry']}.json")
        rec = json.load(open(rec_path)) if os.path.isfile(rec_path) else {}
        fixes = rec.get("fix_commits") or []
        if isinstance(fixes, str):
            fixes = [fixes]
        jobs.append(dict(id=f"h4-{r['entry']}", pattern="H4", repo=r["repo"], pin_from=[str(c) for c in fixes],
                         candidate=r, screener_record=rec_path if rec else None))
    szz = {(r["b"], r["a"]): r["status"] for r in tsv("szz_pairs.tsv")}
    pairs = [r for r in tsv("h3b_pairs.tsv") if r["status"] == "ready"
             and not (set(filter(None, r["cwes"].replace(";", ",").split(","))) and
                      set(filter(None, r["cwes"].replace(";", ",").split(","))) <= DOS)]
    pairs.sort(key=lambda r: SZZ_ORDER.get(szz.get((r["b"], r["a"])), 4))
    for r in pairs[: a.h3]:
        st = szz.get((r["b"], r["a"]), "not-mined")
        pattern = "H3a" if st == "H3a-regression" else "H3b"
        jobs.append(dict(id=f"h3-{r['b'].lower()}", pattern=pattern, repo=r["repo"].split(";")[0],
                         pin_from=[c for c in r["a_fix"].split(";") if c], candidate=dict(r, szz_status=st),
                         screener_record=None))
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "reader_jobs.jsonl"), "w") as o:
        for j in jobs:
            o.write(json.dumps(j) + "\n")
    print(f"{len(jobs)} jobs -> stacking/out/reader_jobs.jsonl "
          f"(H4 {sum(j['pattern']=='H4' for j in jobs)}, H3 {sum(j['pattern']!='H4' for j in jobs)})")
    for j in jobs:
        print(f"  {j['id']:28} {j['pattern']:4} {j['repo']}")


if __name__ == "__main__":
    main()
