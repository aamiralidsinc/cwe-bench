#!/usr/bin/env python3
"""Persistent host ledger over the 150 screened hosts + any built task, merged with VM trial
outcomes. Writes build/audit/host-ledger.tsv. Status decides what NOT to rebuild and what to
replace. Run: python3 -I build_ledger.py VM_OUTCOMES.tsv

Status per repo:
  breaker        both models 0/N (no solve either) - KEEP, the goal
  deepseek-only / mimo-only   one model 0/N, other solved - lead, keep
  solved         >=1 model solved and not a breaker - do NOT rebuild; REPLACE with new injection
  parked         classifier-stopped twice - do not rebuild as-is
  trialing/built in progress
  screened       scored, not built - candidate pool for new batches
"""
import csv, glob, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
REC = os.path.join(HERE, "..", "review", "screener-v2")
OUT = os.path.join(HERE, "..", "..", "build", "audit", "host-ledger.tsv")


def classify(ds, mm, parked, built):
    def solved(xs):
        return any(abs(x - 1.0) < 1e-6 for x in xs)
    def failed_only(xs):
        return len(xs) >= 1 and not solved(xs)
    if parked:
        return "parked"
    if not built:
        return "screened"
    ds_s, mm_s = solved(ds), solved(mm)
    ds_f3, mm_f3 = (len(ds) >= 3 and not ds_s), (len(mm) >= 3 and not mm_s)
    if ds_f3 and mm_f3:
        return "breaker"
    if ds_s and mm_s:
        return "solved"
    if ds_f3 and mm_s:
        return "deepseek-only"
    if mm_f3 and ds_s:
        return "mimo-only"
    if ds_s or mm_s:
        return "solved"          # one solved, other still running -> not a breaker
    return "trialing"            # built, failing-so-far but < 3 runs / unfinished


def inj_score(rec):
    o8b = len([x for x in rec.get("O8b_injection_room") or [] if isinstance(x, dict) and str(x.get("where") or "").strip() not in ("", "path:line")])
    o8 = len([x for x in rec.get("O8_uncovered_routes") or [] if isinstance(x, dict) and str(x.get("where") or "").strip() not in ("", "path:line")])
    o1 = rec.get("O1_entry_points") or 0
    dos = rec.get("O9_dos"); flags = rec.get("O12_red_flags") or []
    s = o8b * 3 + o8 * 2 + (3 if o1 >= 4 else 2 if o1 == 3 else 0)
    if dos: s -= 5
    if "single_site" in flags: s -= 3
    if "tiny_repo" in flags: s -= 2
    return s


def main(vm_tsv):
    # VM outcomes keyed by repo (built tasks carry repo); also keep slug rows w/o repo (old tasks)
    vm = {}
    old_built_slugs = []
    for r in csv.DictReader(open(vm_tsv), delimiter="\t"):
        repo = r.get("repo", "").strip()
        ds = [float(x) for x in r["deepseek"].split(",") if x]
        mm = [float(x) for x in r["mimo"].split(",") if x]
        if repo:
            vm[repo] = {"slug": r["slug"], "track": r.get("track", ""), "ds": ds, "mm": mm,
                        "parked": r.get("parked") == "yes", "pb": r.get("policy_b") == "yes"}
        else:
            old_built_slugs.append((r["slug"], ds, mm))

    rows = []
    seen_repos = set()
    for p in sorted(glob.glob(os.path.join(REC, "*.json"))):
        try:
            rec = json.load(open(p))
        except ValueError:
            continue
        if not isinstance(rec, dict) or "screener_version" not in rec:
            continue
        repo = rec.get("repo", "")
        seen_repos.add(repo)
        v = vm.get(repo)
        built = v is not None
        ds = v["ds"] if v else []
        mm = v["mm"] if v else []
        status = classify(ds, mm, v and v["parked"], built)
        rows.append({
            "repo": repo, "entry_id": rec.get("entry_id"), "status": status,
            "track": (v or {}).get("track", ""), "slug": (v or {}).get("slug", ""),
            "deepseek": ",".join(str(x) for x in ds), "mimo": ",".join(str(x) for x in mm),
            "policy_b": "yes" if v and v.get("pb") else "",
            "inj_score": inj_score(rec), "pattern": rec.get("pattern_fit", ""),
            "lang": (rec.get("O10_build") or {}).get("language", "")[:14],
            "fix_min": rec.get("O11_fix_minutes"),
            "family": (rec.get("O9_family") or "")[:50].replace("\t", " "),
        })
    # old built tasks not in the 150 (prior rounds) - record so we never rebuild them
    for slug, ds, mm in old_built_slugs:
        rows.append({"repo": "(prior round)", "entry_id": "", "status": classify(ds, mm, False, True),
                     "track": "prior", "slug": slug, "deepseek": ",".join(str(x) for x in ds),
                     "mimo": ",".join(str(x) for x in mm), "policy_b": "", "inj_score": "",
                     "pattern": "", "lang": "", "fix_min": "", "family": ""})

    order = {"breaker": 0, "deepseek-only": 1, "mimo-only": 1, "trialing": 2, "built": 3,
             "parked": 4, "solved": 5, "screened": 6}
    rows.sort(key=lambda r: (order.get(r["status"], 9), -(r["inj_score"] or 0) if isinstance(r["inj_score"], int) else 0))
    cols = ["status", "repo", "slug", "entry_id", "track", "deepseek", "mimo", "policy_b",
            "inj_score", "pattern", "lang", "fix_min", "family"]
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        w = csv.DictWriter(f, cols, delimiter="\t", extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    from collections import Counter
    c = Counter(r["status"] for r in rows)
    print("wrote", OUT, dict(c))


if __name__ == "__main__":
    main(sys.argv[1])
