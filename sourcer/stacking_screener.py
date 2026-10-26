#!/usr/bin/env python3
"""Branch C screener: find SMALL, easy-to-build repos where several REAL security
vulns are simultaneously open at one version point (stacking candidates).

Reads the already-downloaded OSV dumps (no network). For each package it finds
the version point of maximum co-presence of CWE-bearing advisories, lists the
advisories open there, filters to small/buildable mid co-presence repos, and
ranks by favoured-class co-presence and build-ease. Writes a top-20 build
shortlist.

    python3 -I sourcer/stacking_screener.py
Output: sourcer/stacking-shortlist.tsv and .md (top 20)

Tunables below: CO_MIN/CO_MAX (how many bugs to stack), MAX_TOTAL_ADV (smallness
proxy), EASY_ECOS (offline-buildable ecosystems), TOP_N.

NOTE: co-presence here is SEMVER/ECOSYSTEM version-range overlap, a proxy for
"unpatched in that release". The builder still picks the real commit (via clone)
and confirms each vuln is reproducible and reachable offline.
"""
import glob
import json
import os
import re
import zipfile
import collections

HERE = os.path.dirname(os.path.abspath(__file__))   # sourcer/
DUMPS = glob.glob(os.path.expanduser("~/.tb-graders/cwe/sourcer-data/dumps/*.zip"))
OUT_TSV = os.path.join(HERE, "stacking-shortlist.tsv")
OUT_MD = os.path.join(HERE, "stacking-shortlist.md")

CO_MIN, CO_MAX = 4, 10          # stack 4-10 real bugs: hard but buildable, not a monster
MAX_TOTAL_ADV = 60              # smallness proxy: skip projects with huge advisory histories
TOP_N = 20

# Ecosystems that build cleanly offline in a lean container (ease weight).
EASE = {"PyPI": 5, "npm": 5, "Go": 4, "RubyGems": 4, "Packagist": 4,
        "crates.io": 4, "Maven": 2}

GIANTS = ("tensorflow", "magento", "moodle", "jenkins", "wordpress", "drupal",
          "gitlab", "kubernetes", "openshift", "chromium", "firefox", "android",
          "linux", "mattermost", "openclaw", "pimcore", "concrete", "nextcloud",
          "owncloud", "mediawiki", "joomla", "dotcms", "liferay", "spree",
          "saleor", "frappe", "zulip", "discourse", "gitea", "forgejo",
          "transformers", "vllm", "ray", "airflow", "superset", "ckan")

FAVOURED_CWES = {
    "287", "384", "613", "620", "306", "294", "522", "523", "640", "645",
    "862", "863", "284", "285", "639", "266", "269",
    "345", "346", "347", "353", "354", "494", "565", "829", "915", "502",
    "840", "841", "799",
}


def vkey(v):
    parts = re.findall(r"\d+", v or "")
    return tuple(int(p) for p in parts[:6]) if parts else (0,)


def cwes_of(a):
    return [c.split("-")[-1] for c in (a.get("database_specific") or {}).get("cwe_ids", []) or []]


def main():
    per_pkg = collections.defaultdict(list)    # pkg -> [(intro, fixed|None, aid, cwes)]
    pkg_repo = {}
    for z in DUMPS:
        try:
            zf = zipfile.ZipFile(z)
        except Exception:
            continue
        for nm in zf.namelist():
            if not nm.endswith(".json"):
                continue
            try:
                a = json.loads(zf.read(nm))
            except Exception:
                continue
            if a.get("withdrawn") or a.get("id", "").startswith("MAL"):
                continue
            cwes = cwes_of(a)
            if not cwes:
                continue
            aid = a.get("id", "")
            repo = None
            for r in a.get("references", []) or []:
                m = re.search(r"github\.com/([^/]+/[^/#?]+)", r.get("url", ""))
                if m:
                    repo = m.group(1).lower().removesuffix(".git")
                    break
            for aff in a.get("affected", []) or []:
                pkg = aff.get("package") or {}
                name = pkg.get("name")
                if not name:
                    continue
                key = f"{pkg.get('ecosystem')}:{name}"
                if repo:
                    pkg_repo[key] = repo
                for rng in aff.get("ranges", []) or []:
                    if rng.get("type") not in ("SEMVER", "ECOSYSTEM"):
                        continue
                    intro = fixed = None
                    for ev in rng.get("events", []) or []:
                        intro = ev.get("introduced", intro)
                        fixed = ev.get("fixed", fixed)
                    per_pkg[key].append((vkey(intro) if intro and intro != "0" else (0,),
                                         vkey(fixed) if fixed else None, aid, tuple(cwes)))

    rows = []
    for key, ivs in per_pkg.items():
        repo = pkg_repo.get(key, "")
        eco = key.split(":", 1)[0]
        if not repo or any(g in repo or g in key.lower() for g in GIANTS):
            continue
        total_adv = len({aid for _, _, aid, _ in ivs})
        if total_adv > MAX_TOTAL_ADV:                 # not a small repo
            continue
        events = []
        for lo, hi, aid, cwes in ivs:
            events.append((lo, 1))
            if hi is not None:
                events.append((hi, -1))
        events.sort()
        cur = best = 0
        best_pt = None
        for pt, d in sorted(events):
            cur += d
            if cur > best:
                best, best_pt = cur, pt
        if not (CO_MIN <= best <= CO_MAX):
            continue
        open_here, seen = [], set()
        for lo, hi, aid, cwes in ivs:
            if lo <= best_pt and (hi is None or best_pt < hi) and aid not in seen:
                seen.add(aid)
                open_here.append((aid, cwes))
        fav = sum(1 for _, cwes in open_here if any(c in FAVOURED_CWES for c in cwes))
        allc = sorted({c for _, cwes in open_here for c in cwes})
        ease = EASE.get(eco, 1)
        # rank: favoured-class co-presence dominates, then build-ease, then smallness
        rank = fav * 3 + best + ease - min(total_adv / 10.0, 6)
        rows.append({
            "package": key, "repo": repo, "eco": eco, "co_present": len(open_here),
            "favoured": fav, "total_adv": total_adv, "ease": ease, "rank": round(rank, 1),
            "cwes": ",".join("CWE-" + c for c in allc[:12]),
            "advisories": ",".join(aid for aid, _ in open_here[:12]),
        })

    rows.sort(key=lambda r: r["rank"], reverse=True)
    top = rows[:TOP_N]
    with open(OUT_TSV, "w") as f:
        f.write("rank_score\tpackage\trepo\teco\tco_present\tfavoured\ttotal_adv\tease\tcwes\tsample_advisories\n")
        for r in top:
            f.write(f"{r['rank']}\t{r['package']}\t{r['repo']}\t{r['eco']}\t{r['co_present']}\t"
                    f"{r['favoured']}\t{r['total_adv']}\t{r['ease']}\t{r['cwes']}\t{r['advisories']}\n")
    with open(OUT_MD, "w") as f:
        f.write("# Stacking build shortlist (Branch C) — small, buildable repos with co-present real vulns\n\n")
        f.write(f"{len(rows)} repos passed the filter (co-present {CO_MIN}-{CO_MAX}, "
                f"<= {MAX_TOTAL_ADV} total advisories, not a giant). Top {len(top)} by "
                f"favoured-class co-presence x build-ease.\n\n")
        f.write("Co-presence is version-range overlap (proxy); the builder confirms the real commit and offline reachability.\n\n")
        f.write("| # | repo | eco | co-present | favoured | total adv | CWEs |\n|---|---|---|---|---|---|---|\n")
        for i, r in enumerate(top, 1):
            f.write(f"| {i} | {r['repo']} | {r['eco']} | {r['co_present']} | {r['favoured']} | {r['total_adv']} | {r['cwes']} |\n")
    print(f"candidates after small/buildable filter: {len(rows)}; wrote top {len(top)}")
    for r in top[:TOP_N]:
        print(f"  rank {r['rank']:>5}  {r['co_present']:>2}cp {r['favoured']:>2}fav {r['eco']:<9} "
              f"{r['repo']:<34} {r['cwes'][:44]}")


if __name__ == "__main__":
    main()
