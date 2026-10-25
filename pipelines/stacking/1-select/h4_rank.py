#!/usr/bin/env python3
"""Step 1a of the stacking pipeline: rank screened hosts for H4 trap stacking (STACKING-EXPLORATION.md §8, §11).

H4 = one protection, several real routes upstream left open, of DIFFERENT mechanism kinds, at least one
where the protection never existed (DeepSeek-type) and a coupled must-keep-working value or a how-type
mechanism (MiMo-type). This is a PRIOR from the screener records only; the stacking reader (step 2)
confirms against the code.

Inputs (read-only):
  common/screener/records/<entry>.json     screener-v2 records
  --built DIR [DIR...]                         task dirs whose task.toml `repo` marks a host as already built
Outputs:
  pipelines/stacking/out/h4_candidates.tsv               every record, with its score breakdown
  pipelines/stacking/out/h4_shortlist.md                 top N hosts offering both a DeepSeek- and a MiMo-type trap

  python3 -I pipelines/stacking/1-select/h4_rank.py --built <tasks dir> [<tasks dir> ...] [--top 20]
"""
import argparse, glob, json, os, re
import sys
from pathlib import Path
sys.path.insert(0, str(next(p for p in Path(__file__).resolve().parents if (p / ".cwe-bench-root").is_file()) / "common"))
import paths  # noqa: E402  (repo locations: common/paths.py)

ROOT = str(paths.ROOT)
RECS = str(paths.SCREENER_RECORDS)
OUT = str(paths.STACKING_OUT)

O2_KIND = {"second_implementation": "M2", "lower_level_api": "M3", "wrapper_or_composition": "M3",
           "save_reload_or_serialization": "M6", "defaults_or_merge_route": "M5", "legacy_path": "M4"}
PRODUCER_KINDS = {"schema", "serializer", "cache", "mapper", "config_loader"}
ABSENT = re.compile(r"\b(no (check|guard|validation|authori[sz]ation|containment|filter)|never (check|validat|"
                    r"authori|filter|appl|call)|without any|not checked|unchecked|unguarded|bypass(es)? the "
                    r"(check|guard)|skips? the (check|guard)|ignores? the|missing entirely|has no)\b", re.I)
MERGE = re.compile(r"\b(default|merge|inherit|template ?defaults|stored|persist|config(uration)? file|patch)\w*", re.I)
HOW = {"M4", "M5", "M6", "M11"}          # kinds whose fix needs the mechanism understood (§2.2 tiers hard/medium)


def built_repos(dirs):
    repos = set()
    for d in dirs:
        for t in glob.glob(os.path.join(d, "*", "task.toml")):
            m = re.search(r'^\s*repo\s*=\s*"([^"]+)"', open(t, errors="replace").read(), re.M)
            if m:
                repos.add(m.group(1).lower().rstrip("/").replace("https://github.com/", ""))
    return repos


def classify(rec):
    kinds, ds_type, notes = set(), False, []
    o2 = rec.get("O2_out_of_scope_site") or {}
    k = O2_KIND.get(o2.get("kind"))
    if k:
        kinds.add(k)
        if k == "M4":
            ds_type = True
    o7 = rec.get("O7_producer") or {}
    if o7.get("kind") in PRODUCER_KINDS and o7.get("check_calls_producer") is False:
        kinds.add("M6")
    o5 = rec.get("O5_coupled_behaviour") or {}
    coupled = bool((o5.get("what") or "").strip()) if isinstance(o5, dict) else bool(o5)
    if coupled:
        kinds.add("M11")
    routes = rec.get("O8_uncovered_routes") or []
    for r in routes:
        text = " ".join(str(r.get(x, "")) for x in ("route", "where")) if isinstance(r, dict) else str(r)
        dismiss = (r.get("reason_to_dismiss") or "").strip() if isinstance(r, dict) else ""
        if ABSENT.search(text):
            kinds.add("M4")
            if dismiss:
                ds_type = True
        elif MERGE.search(text):
            kinds.add("M5")
        else:
            kinds.add("M1")
    mimo_type = coupled or bool(kinds & {"M6"})
    return kinds, ds_type, mimo_type, len(routes), len(rec.get("O8b_injection_room") or []), coupled


def score(rec, kinds, ds, mm, n_routes):
    flags = set(rec.get("O12_red_flags") or [])
    pen, why = 0.0, []
    if "protection_documented_without_exceptions" in flags:
        pen += 3; why.append("documented-everywhere")
        ds = False                                   # no reason to dismiss exists (§10 of BETTER-PATTERNS lessons)
    for f, p in (("tiny_repo", 3), ("single_site", 2), ("needs_gpu_kernel_gui", 5), ("needs_network_at_runtime", 5),
                 ("regression_tests_in_pinned_commit", 2), ("many_fix_commits", 1), ("giant_repo", 1)):
        if f in flags:
            pen += p; why.append(f)
    if rec.get("O9_dos"):
        pen += 4; why.append("dos")
    fm = rec.get("O11_fix_minutes")
    if isinstance(fm, (int, float)) and fm > 120:
        pen += 2; why.append("fix>120m")
    if rec.get("O13_recall_risk") == "high":
        pen += 1; why.append("recall-high")
    dist = rec.get("O4_distance") or {}
    dist_bonus = 1 if (dist.get("packages") or 0) >= 2 else (0.5 if (dist.get("files") or 0) >= 3 else 0)
    hard = len(kinds & HOW)
    s = 3 * len(kinds) + 2 * hard + 2 * ds + 2 * mm + 0.5 * min(n_routes, 6) + dist_bonus - pen
    return round(s, 2), ds, hard, dist_bonus, why


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--built", nargs="*", default=[])
    ap.add_argument("--top", type=int, default=20)
    ap.add_argument("--recs", nargs="*", default=[RECS, os.path.join(str(paths.STACKING_OUT), "screener")],
                    help="folders of screener-v2 records (default: the sibling records and pipelines/stacking/out/screener)")
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    done = built_repos(a.built)
    rows = []
    files = sorted(f for d in a.recs for f in glob.glob(os.path.join(d, "*.json")))
    for f in files:
        if os.path.basename(f).startswith(("._", "_")) or f.endswith(".run.json"):
            continue
        try:
            rec = json.load(open(f))
        except Exception:
            continue
        repo = str(rec.get("repo", "")).lower().rstrip("/").replace("https://github.com/", "")
        kinds, ds, mm, n8, n8b, coupled = classify(rec)
        s, ds, hard, db, why = score(rec, kinds, ds, mm, n8)
        rows.append(dict(entry=rec.get("entry_id"), repo=repo, built=repo in done, score=s,
                         kinds="+".join(sorted(kinds)), n_kinds=len(kinds), hard_kinds=hard,
                         ds_type=ds, mimo_type=mm, both=ds and mm, uncovered_routes=n8, injection_room=n8b,
                         coupled=coupled, distance=db, penalties=";".join(why),
                         family=str(rec.get("O9_family", ""))[:70], pattern=rec.get("pattern_fit"),
                         language=str((rec.get("O10_build") or {}).get("language", ""))[:20]))
    rows.sort(key=lambda r: -r["score"])
    cols = list(rows[0].keys())
    with open(os.path.join(OUT, "h4_candidates.tsv"), "w") as o:
        o.write("\t".join(cols) + "\n")
        for r in rows:
            o.write("\t".join(str(r[c]) for c in cols) + "\n")
    short = [r for r in rows if r["both"] and not r["built"]][: a.top]
    md = ["# H4 shortlist (prior from screener records; confirm with the stacking reader, step 2)", "",
          f"{len(rows)} records; {sum(r['built'] for r in rows)} hosts already built; "
          f"{sum(r['both'] for r in rows)} offer both a DeepSeek-type and a MiMo-type trap; "
          f"{sum(r['both'] and not r['built'] for r in rows)} of those are unbuilt.", "",
          "| # | Entry | Repo | Score | Kinds | DS-type | MiMo-type | Routes | Language | Penalties | Family |",
          "|---|---|---|---|---|---|---|---|---|---|---|"]
    for i, r in enumerate(short, 1):
        md.append(f"| {i} | {r['entry']} | {r['repo']} | {r['score']} | {r['kinds']} | {r['ds_type']} | "
                  f"{r['mimo_type']} | {r['uncovered_routes']} | {r['language']} | {r['penalties'] or '-'} | {r['family']} |")
    open(os.path.join(OUT, "h4_shortlist.md"), "w").write("\n".join(md) + "\n")
    print("\n".join(md[:3]))


if __name__ == "__main__":
    main()
