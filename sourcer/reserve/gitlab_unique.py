#!/usr/bin/env python3
"""Item 5 of reports/NEW-SOURCES.md: which GitLab advisories are NOT already in our index?

Input : a clone of gitlab.com/gitlab-org/advisories-community (MIT; a 30-day-delayed copy of the
        GitLab Advisory Database), one YAML file per advisory; the sources2 index (main index + C1-C3).
Steps, per record:
  1. ids     : any identifier (CVE / GHSA / GMS / ...) already in entry_ids  -> duplicate
  2. commit  : any github.com/<o>/<r>/commit/<sha> in `urls` already in the commits table -> duplicate
  3. the rest are unique; reported with: has a GitHub fix commit, inside the recency window.
(The planned (package, fixed version) match is not possible: the index stores no fixed versions.)
No YAML library: the few flat fields needed are read with patterns. Input is untrusted text.

  python3 -I sources2/gitlab_unique.py [--since 2026-06-01] [--out sources2/out/gitlab_unique.tsv]
"""
import argparse, collections, glob, os, re, sqlite3

HERE = os.path.dirname(os.path.abspath(__file__))
COMMIT = re.compile(r"github\.com/([^/\s\"]+)/([^/\s\"]+)/(?:pull/\d+/)?commits?/([0-9a-fA-F]{7,40})")


def items(text, key):
    m = re.search(rf"^{key}:\n((?:- .*\n?)+)", text, re.M)
    return [x.strip().strip('"') for x in re.findall(r"^- (.*)$", m.group(1), re.M)] if m else []


def field(text, key):
    m = re.search(rf'^{key}: "?([^"\n]*)"?', text, re.M)
    return m.group(1) if m else ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--clone", default=os.path.expanduser("~/.tb-graders/cwe/sources2-data/raw/advisories-community"))
    ap.add_argument("--index", default=os.path.join(HERE, "index", "candidates.sqlite"))
    ap.add_argument("--since", default="2026-06-01")
    ap.add_argument("--out", default=os.path.join(HERE, "out", "gitlab_unique.tsv"))
    a = ap.parse_args()
    db = sqlite3.connect(f"file:{a.index}?mode=ro", uri=True)
    seen_ids = {r[0].upper() for r in db.execute("select id from entry_ids")}
    seen_commits = {}
    for repo, sha in db.execute("select repo, sha from commits"):
        seen_commits.setdefault(repo, []).append(sha)
    tally = collections.Counter()
    rows = []
    for f in glob.glob(os.path.join(a.clone, "*", "**", "*.yml"), recursive=True):
        eco = os.path.relpath(f, a.clone).split(os.sep)[0]
        t = open(f, encoding="utf-8", errors="replace").read()
        ids = [i.upper() for i in items(t, "identifiers")] or [field(t, "identifier").upper()]
        tally[(eco, "records")] += 1
        if any(i in seen_ids for i in ids):
            tally[(eco, "dup_id")] += 1
            continue
        commits = [(f"{o}/{r}".lower(), s.lower()) for o, r, s in COMMIT.findall(t)]
        if any(any(s.startswith(x) or x.startswith(s) for x in seen_commits.get(repo, [])) for repo, s in commits):
            tally[(eco, "dup_commit")] += 1
            continue
        tally[(eco, "unique")] += 1
        recent = field(t, "pubdate") >= a.since
        tally[(eco, "unique_with_commit")] += bool(commits)
        tally[(eco, "unique_with_commit_recent")] += bool(commits) and recent
        rows.append((eco, " ".join(ids), field(t, "package_slug"), field(t, "pubdate"), " ".join(items(t, "cwe_ids")),
                     commits[0][0] if commits else "", " ".join(s for _, s in commits[:3])))
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    with open(a.out, "w") as o:
        o.write("ecosystem\tids\tpackage\tpubdate\tcwe_ids\trepo\tfix_commits\n")
        for r in sorted(rows, key=lambda r: r[3], reverse=True):
            o.write("\t".join(r) + "\n")
    cols = ["records", "dup_id", "dup_commit", "unique", "unique_with_commit", "unique_with_commit_recent"]
    print("| ecosystem | " + " | ".join(cols) + " |")
    print("|---" * (len(cols) + 1) + "|")
    for eco in sorted({e for e, _ in tally}) + ["TOTAL"]:
        vals = [sum(v for (e, k), v in tally.items() if k == c and (eco == "TOTAL" or e == eco)) for c in cols]
        print(f"| {eco} | " + " | ".join(map(str, vals)) + " |")
    print(f"unique rows written to {a.out}")


if __name__ == "__main__":
    main()
