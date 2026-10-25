#!/usr/bin/env python3
"""C4 of reports/NEW-SOURCES.md: Wordfence Intelligence feed -> WordPress plugin candidates.

Wordfence records carry no fix commit and no GitHub repo (the only reference is the Wordfence
page), so the unchanged OSV sourcer would reject all of them; they get their own table instead.
The fix is the difference between the last affected version and the first patched version of the
plugin on WordPress.org (downloads.wordpress.org/plugin/<slug>.<version>.zip; not fetched here).

Kept: type plugin, patched, not informational. Status per row:
  duplicate  its CVE is already in the sources2 index (main index + C1-C3)
  pending    published on/after --since
  deferred   older
Every row keeps its record link; the per-record copyright notice and licence (which must travel
with any copy, per the Wordfence terms) go to wordfence_attribution.jsonl, keyed by record id.

  python3 -I sources2/wordfence_candidates.py [--since 2026-06-01]
"""
import argparse, collections, glob, json, os, sqlite3

HERE = os.path.dirname(os.path.abspath(__file__))
DOS = {400, 770, 1333, 674, 834, 407, 606}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--feed", default="")
    ap.add_argument("--index", default=os.path.join(HERE, "index", "candidates.sqlite"))
    ap.add_argument("--since", default="2026-06-01")
    ap.add_argument("--out", default=os.path.join(HERE, "out"))
    a = ap.parse_args()
    feed = a.feed or sorted(glob.glob(os.path.expanduser("~/.tb-graders/cwe/sources2-data/raw/wordfence/production-*.json")))[-1]
    recs = json.load(open(feed))
    db = sqlite3.connect(f"file:{a.index}?mode=ro", uri=True)
    seen = {r[0].upper() for r in db.execute("select id from entry_ids where id like 'CVE-%'")}
    os.makedirs(a.out, exist_ok=True)
    tally = collections.Counter()
    rows = []
    with open(os.path.join(a.out, "wordfence_attribution.jsonl"), "w") as att:
        for r in recs.values():
            sw = [s for s in r.get("software") or [] if s.get("type") == "plugin"]
            if not sw or r.get("informational"):
                tally["not_plugin_or_informational"] += 1
                continue
            s = sw[0]
            if not s.get("patched") or not s.get("patched_versions"):
                tally["unpatched"] += 1
                continue
            cwe = (r.get("cwe") or {}).get("id")
            cve = (r.get("cve") or "").upper()
            pub = (r.get("published") or "")[:10]
            if cve and cve in seen:
                status = "duplicate"
            elif cwe in DOS:
                status = "rejected_dos"
            elif pub >= a.since:
                status = "pending"
            else:
                status = "deferred"
            tally[status] += 1
            last_affected = max((v.get("to_version") or "" for v in (s.get("affected_versions") or {}).values()), default="")
            link = next((u for u in r.get("references") or [] if "wordfence.com" in u), "")
            rows.append(dict(source="wordfence", record_id=r["id"], status=status, slug=s.get("slug", ""),
                             last_affected=last_affected, first_patched=sorted(s["patched_versions"])[0],
                             cwe=f"CWE-{cwe}" if cwe else "", cve=cve, cvss=(r.get("cvss") or {}).get("score", ""),
                             published=pub, title=(r.get("title") or "").replace("\t", " ")[:200], record_link=link))
            att.write(json.dumps({"record_id": r["id"], "record_link": link, "copyrights": r.get("copyrights")}) + "\n")
    rows.sort(key=lambda x: (x["status"] != "pending", x["published"]), reverse=False)
    cols = list(rows[0].keys())
    with open(os.path.join(a.out, "wordfence_candidates.tsv"), "w") as o:
        o.write("\t".join(cols) + "\n")
        for x in rows:
            o.write("\t".join(str(x[c]) for c in cols) + "\n")
    pend = [x for x in rows if x["status"] == "pending"]
    print(f"feed {os.path.basename(feed)}: {len(recs)} records; " + ", ".join(f"{k} {v}" for k, v in tally.most_common()))
    print(f"pending: {len(pend)} records over {len({x['slug'] for x in pend})} plugins; "
          f"top CWEs {collections.Counter(x['cwe'] for x in pend).most_common(6)}")
    print(f"written: {a.out}/wordfence_candidates.tsv, {a.out}/wordfence_attribution.jsonl")


if __name__ == "__main__":
    main()
