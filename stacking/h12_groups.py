#!/usr/bin/env python3
"""Step 1d of the stacking pipeline: H1 / H2 groups (STACKING-EXPLORATION.md §8).

Co-present bugs = advisories on the same package whose affected version ranges overlap, so one
checkout can hold them all. Each co-present group is split by how upstream fixed them:
  H1 = they share a fix commit (fixed together);  H2 = different fix commits (fixed separately).
Fix commits come from the advisories' commit references. DoS-only advisories are left out (not built).

Inputs (read-only): ~/.tb-graders/cwe/sourcer-data/dumps/*.zip
Outputs: stacking/out/h12_groups.tsv, stacking/out/h12_summary.md

  python3 -I stacking/h12_groups.py
"""
import collections, glob, json, os, re, zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "stacking", "out")
DUMPS = glob.glob(os.path.expanduser("~/.tb-graders/cwe/sourcer-data/dumps/*.zip"))
COMMIT = re.compile(r"https?://(?:www\.)?github\.com/([^/\s]+/[^/\s]+?)(?:\.git)?/commit/([0-9a-f]{7,40})", re.I)
DOS = {"CWE-400", "CWE-770", "CWE-1333", "CWE-674", "CWE-834", "CWE-407", "CWE-606"}


def vkey(v):
    """Loose version key: numeric parts compared numerically, the rest as text."""
    return tuple((0, int(p)) if p.isdigit() else (1, p) for p in re.split(r"[.\-+_]", str(v)) if p != "")


def main():
    os.makedirs(OUT, exist_ok=True)
    by_pkg = collections.defaultdict(dict)
    for z in DUMPS:
        with zipfile.ZipFile(z) as zf:
            for nm in zf.namelist():
                if not nm.endswith(".json"):
                    continue
                try:
                    a = json.loads(zf.read(nm))
                except Exception:
                    continue
                aid = a.get("id", "")
                if not aid.startswith("GHSA") or a.get("withdrawn"):
                    continue
                cwes = set((a.get("database_specific") or {}).get("cwe_ids") or [])
                if cwes and cwes <= DOS:
                    continue
                fixes = {(m.group(1).lower(), m.group(2)[:12].lower()) for r in a.get("references") or []
                         for m in [COMMIT.search(r.get("url", ""))] if m}
                for aff in a.get("affected") or []:
                    p = aff.get("package") or {}
                    for rng in aff.get("ranges") or []:
                        if rng.get("type") not in ("ECOSYSTEM", "SEMVER"):
                            continue
                        lo, hi = "0", None
                        for ev in rng.get("events") or []:
                            lo = ev.get("introduced", lo)
                            hi = ev.get("fixed", hi)
                        if hi:
                            by_pkg[(p.get("ecosystem"), p.get("name"))][aid] = (lo, hi, fixes, ",".join(sorted(cwes)))
    rows = []
    for (eco, name), advs in by_pkg.items():
        items = [(aid, vkey(lo), vkey(hi), fx, cw) for aid, (lo, hi, fx, cw) in advs.items() if fx]
        if len(items) < 2:
            continue
        # pins = every fixed version minus epsilon: test which advisories are open just before each fix
        best = None
        for _, _, pin_hi, _, _ in items:
            open_ = [it for it in items if it[1] < pin_hi and pin_hi <= it[2]]
            if len(open_) >= 2 and (best is None or len(open_) > len(best)):
                best = open_
        if not best:
            continue
        fixsets = [frozenset(c for _, c in it[3]) for it in best]
        repos = collections.Counter(r for it in best for r, _ in it[3])
        shared = collections.Counter(c for fs in fixsets for c in fs)
        together = sum(1 for fs in fixsets if any(shared[c] >= 2 for c in fs))
        kind = "H1" if together == len(best) else ("H2" if together == 0 else "H1+H2")
        rows.append(dict(ecosystem=eco, package=name, repo=repos.most_common(1)[0][0], co_present=len(best),
                         fixed_together=together, distinct_fix_commits=len(set().union(*fixsets)), pattern=kind,
                         cwes=";".join(sorted({it[4] for it in best if it[4]}))[:120],
                         advisories=";".join(it[0] for it in best)))
    rows.sort(key=lambda r: (-r["co_present"], r["pattern"]))
    cols = list(rows[0].keys())
    with open(os.path.join(OUT, "h12_groups.tsv"), "w") as o:
        o.write("\t".join(cols) + "\n")
        for r in rows:
            o.write("\t".join(str(r[c]) for c in cols) + "\n")
    c = collections.Counter(r["pattern"] for r in rows)
    mid = [r for r in rows if 3 <= r["co_present"] <= 8]
    md = ["# H1 / H2 groups: co-present advisories split by how upstream fixed them", "",
          f"Packages with 2+ co-present, non-DoS advisories that carry fix commits: {len(rows)}. "
          f"H1 (all fixed together) {c['H1']}, H2 (all fixed separately) {c['H2']}, mixed {c['H1+H2']}.", "",
          f"Mid-size groups (3-8 co-present, the useful zone): {len(mid)}; by pattern: "
          + ", ".join(f"{k} {v}" for k, v in collections.Counter(r['pattern'] for r in mid).most_common()) + ".", "",
          "| Package | Repo | Co-present | Fixed together | Distinct fix commits | Pattern | CWEs |", "|---|---|---|---|---|---|---|"]
    for r in mid[:40]:
        md.append(f"| {r['ecosystem']}:{r['package']} | {r['repo']} | {r['co_present']} | {r['fixed_together']} | "
                  f"{r['distinct_fix_commits']} | {r['pattern']} | {r['cwes'][:60]} |")
    open(os.path.join(OUT, "h12_summary.md"), "w").write("\n".join(md) + "\n")
    print("\n".join(md[:5]))


if __name__ == "__main__":
    main()
