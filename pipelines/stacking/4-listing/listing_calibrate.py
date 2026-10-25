#!/usr/bin/env python3
"""listing_calibrate.py SLUG [SLUG ...] [--enforce] : calibrate the listing-check reviewer (2026-10-24).

Compares each build/<slug>/listing.json (a finished pipelines/stacking/4-listing/run_listing_check.sh review) with the
hand audit pipelines/stacking/out/listing_audit.json, trap by trap, on the hidden traps (origin != advisory_route,
as listing_verdict.py counts them). Reports:
  - verdict match: the reviewer's PASS/FAIL vs the audit's, under the listing_verdict.py rule;
  - per-trap agreement, and leniency: hidden traps the reviewer labels LESS severe than the audit
    (severity NAMED > DESCRIBED > GENERAL > ABSENT), the failure mode of the earlier fairness reviewer.
Calibrated = every verdict matches AND at most 10% of hidden traps are lenient.
With --enforce and a calibrated result, creates pipelines/stacking/4-listing/LISTING_ENFORCE, which makes
pipelines/stacking/3-build-gate/run_stack_pipeline.sh withhold .sound on a listing FAIL. Exit 0 calibrated, 1 not, 2 error.

  common/launch/drive.sh deepseek bash pipelines/stacking/4-listing/run_listing_check.sh SLUG     # for each slug first
  python3 -I pipelines/stacking/4-listing/listing_calibrate.py stk-dagu-ghsaph8x stk-mlflow-3745 ...
"""
import json, os, sys
from pathlib import Path
sys.path.insert(0, str(next(p for p in Path(__file__).resolve().parents if (p / ".cwe-bench-root").is_file()) / "common"))
import paths  # noqa: E402  (repo locations: common/paths.py)

ROOT = str(paths.ROOT)
SEV = {"NAMED": 3, "DESCRIBED": 2, "GENERAL": 1, "ABSENT": 0}
MAX_DESCRIBED, MAX_LENIENT = 1, 0.10


def verdict(labels):
    return "FAIL" if labels.count("NAMED") > 0 or labels.count("DESCRIBED") > MAX_DESCRIBED else "PASS"


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        sys.exit(__doc__)
    audit = json.load(open(os.path.join(str(paths.STACKING_OUT), "listing_audit.json")))
    tot = lenient = agree = 0
    mismatched, missing = [], []
    for slug in args:
        b = os.path.join(ROOT, "build", slug)
        status = open(os.path.join(b, "listing_status.txt")).read().strip() if os.path.isfile(os.path.join(b, "listing_status.txt")) else "none"
        if slug not in audit or status != "ok" or not os.path.isfile(os.path.join(b, "listing.json")):
            missing.append(f"{slug} (audit={'yes' if slug in audit else 'no'}, review status={status})")
            continue
        traps = json.load(open(os.path.join(b, "manifest.json"))).get("traps") or []
        hidden = [t["id"] for t in traps if t.get("origin") != "advisory_route"]
        rev = {t["id"]: str(t.get("coverage", "")).strip().upper() for t in json.load(open(os.path.join(b, "listing.json"))).get("traps") or []}
        aud = {t["id"]: str(t.get("coverage", "")).strip().upper() for t in audit[slug]["traps"]}
        rl, al = [rev.get(i, "?") for i in hidden], [aud.get(i, "?") for i in hidden]
        rv, av = verdict(rl), verdict(al)
        if rv != av:
            mismatched.append(slug)
        rows = []
        for i, r, a in zip(hidden, rl, al):
            tot += 1
            agree += r == a
            if SEV.get(r, -1) < SEV.get(a, -1):
                lenient += 1
            if r != a:
                rows.append(f"{i}: reviewer {r} vs audit {a}{'  (LENIENT)' if SEV.get(r, -1) < SEV.get(a, -1) else ''}")
        print(f"{slug}: reviewer {rv} / audit {av}{'' if rv == av else '  <-- MISMATCH'}; hidden traps {len(hidden)}")
        for r in rows:
            print("    " + r)
    if missing:
        print("not compared: " + "; ".join(missing))
    if not tot:
        print("ERROR: nothing to compare")
        sys.exit(2)
    share = lenient / tot
    ok = not mismatched and not missing and share <= MAX_LENIENT
    print(f"\nverdicts matched {len(args) - len(missing) - len(mismatched)}/{len(args) - len(missing)}; "
          f"trap labels agree {agree}/{tot}; lenient {lenient}/{tot} ({share:.0%}, limit {MAX_LENIENT:.0%})")
    print("CALIBRATED" if ok else "NOT CALIBRATED: keep the listing check advisory (no pipelines/stacking/4-listing/LISTING_ENFORCE)")
    if ok and "--enforce" in sys.argv:
        open(os.path.join(str(paths.STACKING), "4-listing", "LISTING_ENFORCE"), "w").write(
            f"calibrated {args} lenient {lenient}/{tot}\n")
        print("created pipelines/stacking/4-listing/LISTING_ENFORCE: the listing check now withholds .sound on FAIL")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
