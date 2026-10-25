#!/usr/bin/env python3
"""listing_verdict.py <slug> : verdict of the stacking listing check (build rule 7).

Reads build/<slug>/listing.json (from stacking/run_listing_check.sh) and the trap origins from
build/<slug>/manifest.json (never from the reviewer). Traps with origin `advisory_route` (the reported
bug, which the impact example may show) are exempt; every other trap is hidden.

Prints one line `PASS|FAIL|ERROR named=<n> described=<n> general=<n> absent=<n> ...`, then one line
per hidden trap that is NAMED or DESCRIBED. Exit 0 PASS, 1 FAIL, 2 ERROR.
FAIL: any hidden trap NAMED, or more than MAX_DESCRIBED hidden traps DESCRIBED.
ERROR: no finished review, unreadable JSON, a hidden trap the review does not classify, or a label
outside NAMED/DESCRIBED/GENERAL/ABSENT (2026-10-24: such a label used to count as neither and could pass).
"""
import json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXEMPT = {"advisory_route"}
MAX_DESCRIBED = 1
LABELS = ("NAMED", "DESCRIBED", "GENERAL", "ABSENT")


def main():
    slug = sys.argv[1]
    b = os.path.join(ROOT, "build", slug)
    status = open(os.path.join(b, "listing_status.txt")).read().strip() if os.path.isfile(os.path.join(b, "listing_status.txt")) else "none"
    try:
        traps = json.load(open(os.path.join(b, "manifest.json"))).get("traps") or []
        review = {t["id"]: t for t in json.load(open(os.path.join(b, "listing.json"))).get("traps") or []}
    except Exception as e:
        print(f"ERROR unreadable ({type(e).__name__}: {e}); status={status}")
        sys.exit(2)
    if status != "ok":
        print(f"ERROR review not finished: {status}")
        sys.exit(2)
    hidden = [t for t in traps if t.get("origin") not in EXEMPT]
    missing = [t["id"] for t in hidden if t["id"] not in review]
    if missing:
        print(f"ERROR hidden traps not classified: {' '.join(missing)}")
        sys.exit(2)
    cov = {t["id"]: str(review[t["id"]].get("coverage", "")).strip().upper() for t in hidden}
    # A label outside the four (e.g. "PARTIAL", empty) is an unfinished review, never a silent pass.
    bad = {i: c for i, c in cov.items() if c not in LABELS}
    if bad:
        print(f"ERROR hidden traps with an unknown label: {' '.join(f'{i}={c!r}' for i, c in bad.items())}")
        sys.exit(2)
    n = {k: sum(v == k for v in cov.values()) for k in LABELS}
    fail = n["NAMED"] > 0 or n["DESCRIBED"] > MAX_DESCRIBED
    print(f"{'FAIL' if fail else 'PASS'} named={n['NAMED']} described={n['DESCRIBED']} general={n['GENERAL']} "
          f"absent={n['ABSENT']} hidden={len(hidden)} exempt={len(traps) - len(hidden)}")
    for i, c in cov.items():
        if c in ("NAMED", "DESCRIBED"):
            print(f"  {i}: {c}: {review[i].get('quote', '')!r}")
    sys.exit(1 if fail else 0)


if __name__ == "__main__":
    main()
