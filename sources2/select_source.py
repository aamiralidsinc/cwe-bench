#!/usr/bin/env python3
"""Pick the candidates of ONE source (see ../sources_and_usage.md) as a TSV, so a reserve source can
be brought forward on its own.

  python3 -I sources2/select_source.py SOURCE [--status pending] [--only] [--out FILE]

SOURCE (index sources; from the sources2 index, entries above BASE_MAX_ENTRY_ID, i.e. added by sources2):
  GIT | NuGet | GHSA-unreviewed      the entry's `ecosystems` contains SOURCE
                                      (--only: SOURCE is its only ecosystem, i.e. no other source has it)
SOURCE (table sources):
  wordfence                           sources2/out/wordfence_candidates.tsv
  gitlab                              sources2/out/gitlab_unique.tsv (no status column: --status ignored)
  osv-main                            the main index (sourcer/index/candidates.sqlite), all 7 OSV ecosystems
--status: pending | candidate | deferred | rejected | duplicate | any  (default pending)
"""
import argparse, csv, os, sqlite3, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
BASE_MAX_ENTRY_ID = 37416          # the main index's last entry when sources2 copied it (2026-10-24)
INDEX_SOURCES = {"GIT", "NuGet", "GHSA-unreviewed"}
COLS = ["entry_id", "primary_id", "ids", "ecosystems", "repo", "fix_commits", "cwe_ids", "published",
        "status", "reject_reason", "summary"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("source")
    ap.add_argument("--status", default="pending")
    ap.add_argument("--only", action="store_true")
    ap.add_argument("--out", default="")
    a = ap.parse_args()
    out = open(a.out, "w") if a.out else sys.stdout
    w = csv.writer(out, delimiter="\t", lineterminator="\n")
    if a.source in INDEX_SOURCES or a.source == "osv-main":
        db = os.path.join(ROOT, "sourcer" if a.source == "osv-main" else "sources2", "index", "candidates.sqlite")
        c = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
        q, p = f"select {', '.join(COLS)} from entries where 1=1", []
        if a.source != "osv-main":
            q += " and entry_id > ? and (' ' || ecosystems || ' ') like ?"
            p += [BASE_MAX_ENTRY_ID, f"% {a.source} %"]
            if a.only:
                q += " and ecosystems = ?"
                p.append(a.source)
        if a.status != "any":
            q += " and status = ?"
            p.append(a.status)
        rows = c.execute(q + " order by published desc", p).fetchall()
        w.writerow(COLS)
        w.writerows(rows)
    elif a.source in ("wordfence", "gitlab"):
        f = os.path.join(HERE, "out", "wordfence_candidates.tsv" if a.source == "wordfence" else "gitlab_unique.tsv")
        rd = csv.DictReader(open(f), delimiter="\t")
        w.writerow(rd.fieldnames)
        rows = [r for r in rd if a.source == "gitlab" or a.status == "any" or r["status"] == a.status]
        w.writerows([r[k] for k in rd.fieldnames] for r in rows)
    else:
        sys.exit(f"unknown source {a.source}")
    print(f"{a.source}: {len(rows)} rows", file=sys.stderr)


if __name__ == "__main__":
    main()
