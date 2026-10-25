#!/usr/bin/env python3
"""Precision-validation copy of the VM pipeline/make_pool.py (10-21 snapshot): same digest, paths changed.

Build the candidate pool the driver model scores and chooses from.

Reads every screener-v2 record and emits a neutral per-candidate digest (facts
relevant to breaker/injection potential) to build/pipeline/pool.jsonl. The
model's own prior score and any pick/verdict are NOT included -- the lane must
score and choose for itself. Confirmed both-models breakers are excluded
(EXCLUDE_REPOS); solved and blocked hosts stay in as controls.

  python3 -I make_pool.py            # writes build/pipeline/pool.jsonl
"""
import glob, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
PV = os.path.abspath(os.path.join(HERE, ".."))
RECS = os.path.join(PV, "results", "screener_v2")
OUT = os.path.join(PV, "results", "pool_stacking21.jsonl")

# Confirmed both-models breakers: keep out so the model must find new ones.
EXCLUDE_REPOS = {"fasterxml/jackson-databind"}


def asdict(v):
    if isinstance(v, str):
        try:
            return json.loads(v.replace("'", '"'))
        except Exception:
            return v
    return v


def trim(v, n=240):
    s = v if isinstance(v, str) else json.dumps(v, ensure_ascii=False)
    return s if len(s) <= n else s[:n] + "…"


def wheres(lst):
    lst = asdict(lst)
    if not isinstance(lst, list):
        return []
    out = []
    for x in lst:
        if isinstance(x, dict):
            w = str(x.get("where") or "").strip()
            if w and w != "path:line":
                out.append(w)
    return out


def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    n = 0
    with open(OUT, "w") as f:
        for p in sorted(glob.glob(os.path.join(RECS, "*.json"))):
            try:
                r = json.load(open(p))
            except ValueError:
                continue
            if p.endswith(".run.json") or not isinstance(r, dict) or "entry_id" not in r:
                continue
            if r.get("repo") in EXCLUDE_REPOS:
                continue
            build = asdict(r.get("O10_build")) or {}
            o8 = wheres(r.get("O8_uncovered_routes"))
            o8b = wheres(r.get("O8b_injection_room"))
            o2 = asdict(r.get("O2_out_of_scope_site")) or {}
            digest = {
                "entry_id": r.get("entry_id"),
                "repo": r.get("repo"),
                "advisory": trim(asdict(r.get("advisory_ids")), 120),
                "family": trim(r.get("O9_family"), 160),
                "pattern_fit": r.get("pattern_fit"),
                "language": (build.get("language") if isinstance(build, dict) else "") or "",
                "services": (build.get("services") if isinstance(build, dict) else "") or [],
                "offline_ok": (build.get("offline") if isinstance(build, dict) else None),
                "fix_minutes": r.get("O11_fix_minutes"),
                "entry_points": r.get("O1_entry_points"),
                "out_of_scope_site": {"kind": (o2.get("kind") if isinstance(o2, dict) else ""),
                                      "where": trim((o2.get("where") if isinstance(o2, dict) else ""), 120)},
                "reason_to_dismiss": trim(r.get("O3_reason_to_dismiss"), 200),
                "distance": asdict(r.get("O4_distance")),
                "coupled_behaviour": trim(asdict(r.get("O5_coupled_behaviour")), 200),
                "input_shapes": trim(asdict(r.get("O6_input_shapes")), 160),
                "uncovered_routes_n": len(o8), "uncovered_routes": o8[:6],
                "injection_room_n": len(o8b), "injection_room": o8b[:6],
                "dos": asdict(r.get("O9_dos")),
                "red_flags": asdict(r.get("O12_red_flags")),
            }
            f.write(json.dumps(digest, ensure_ascii=False) + "\n")
            n += 1
    print(f"wrote {OUT}: {n} candidates")


if __name__ == "__main__":
    main()
