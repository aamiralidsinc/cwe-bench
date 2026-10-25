#!/usr/bin/env python3
"""C1 of reports/NEW-SOURCES.md: GitHub's UNREVIEWED advisories -> one OSV-style dump the unchanged
sourcer (sourcer/osv_sourcer.py parse --ecosystems GHSA-unreviewed) can read.

Input : a sparse checkout of github/advisory-database (advisories/unreviewed/**/GHSA-*.json, OSV format).
Output: <data>/dumps/GHSA-unreviewed.zip with ONLY the records that reference a GitHub fix commit
        (github.com/<owner>/<repo>/commit/<sha> or /pull/<n>/commits/<sha>), as the user asked;
        prints a funnel (records, withdrawn, with a fix commit, with a CWE, both).
All input is untrusted data: parsed as JSON only.

  python3 -I sources2/make_unreviewed_zip.py --data ~/.tb-graders/cwe/sources2-data
"""
import argparse, glob, json, os, re, zipfile

COMMIT = re.compile(r"github\.com/[^/\s]+/[^/\s]+/(?:pull/\d+/)?commits?/[0-9a-fA-F]{7,40}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=os.path.expanduser("~/.tb-graders/cwe/sources2-data"))
    a = ap.parse_args()
    src = os.path.join(a.data, "raw", "advisory-database", "advisories", "unreviewed")
    out = os.path.join(a.data, "dumps", "GHSA-unreviewed.zip")
    n = withdrawn = fix = cwe = both = 0
    tmp = out + ".part"
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as z:
        for f in glob.iglob(os.path.join(src, "**", "*.json"), recursive=True):
            try:
                rec = json.load(open(f, encoding="utf-8", errors="replace"))
            except Exception:
                continue
            n += 1
            if rec.get("withdrawn"):
                withdrawn += 1
                continue
            has_fix = any(COMMIT.search(r.get("url") or "") for r in rec.get("references") or [])
            has_cwe = bool((rec.get("database_specific") or {}).get("cwe_ids"))
            fix += has_fix
            cwe += has_cwe
            if has_fix:
                both += has_cwe
                z.writestr(os.path.basename(f), json.dumps(rec))
    os.replace(tmp, out)
    print(f"unreviewed records {n}; withdrawn {withdrawn}; with a GitHub fix commit {fix}; "
          f"with a CWE {cwe}; fix commit AND CWE {both}; written to {out}: {fix}")


if __name__ == "__main__":
    main()
