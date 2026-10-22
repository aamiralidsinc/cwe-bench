#!/usr/bin/env python3
"""Step 1b of the stacking pipeline: H3b (incomplete fix) candidate pairs (STACKING-EXPLORATION.md §8).

A later advisory B says it is an incomplete fix / bypass / regression of an earlier advisory A. The
task pins the code BEFORE A's fix, and the reference is the complete fix (A + B), so upstream's first
fix (A) is a wrong fix. This script resolves each pair to its repo and fix commits from the OSV dumps.

Inputs (read-only): ~/.tb-graders/cwe/sourcer-data/dumps/*.zip
Outputs: stacking/out/h3b_pairs.tsv (one row per pair), stacking/out/h3b_summary.md

  python3 -I stacking/h3b_pairs.py
"""
import collections, glob, json, os, re, zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "stacking", "out")
DUMPS = glob.glob(os.path.expanduser("~/.tb-graders/cwe/sourcer-data/dumps/*.zip"))
LINK = re.compile(r"(incomplete fix|bypass(?:es|ed)?(?: of)?(?: the)? (?:fix|patch)|regression|not (?:fully|completely) "
                  r"(?:fixed|patched)|previous(?:ly)? (?:fix|patch)|fix for)[^.]{0,120}?((?:CVE-\d{4}-\d+)|(?:GHSA(?:-[a-z0-9]{4}){3}))", re.I)
COMMIT = re.compile(r"https?://(?:www\.)?(github\.com|gitlab\.com)/([^/\s]+/[^/\s]+?)(?:\.git)?/-?/?commit/([0-9a-f]{7,40})", re.I)


def load():
    adv, alias = {}, {}
    for z in DUMPS:
        with zipfile.ZipFile(z) as zf:
            for nm in zf.namelist():
                if not nm.endswith(".json"):
                    continue
                try:
                    a = json.loads(zf.read(nm))
                except Exception:
                    continue
                aid = a.get("id")
                if not aid or a.get("withdrawn"):
                    continue
                prev = adv.get(aid)
                if prev is None or len(a.get("references") or []) > len(prev.get("references") or []):
                    adv[aid] = a
                for x in [aid] + (a.get("aliases") or []):
                    alias.setdefault(x.upper(), set()).add(aid)
    return adv, alias


def commits(a):
    out = []
    for r in a.get("references") or []:
        m = COMMIT.search(r.get("url", ""))
        if m:
            out.append((m.group(2).lower(), m.group(3).lower()))
    return out


def pkg(a):
    p = ((a.get("affected") or [{}])[0].get("package") or {})
    return p.get("ecosystem"), p.get("name")


def main():
    os.makedirs(OUT, exist_ok=True)
    adv, alias = load()
    rows, seen = [], set()
    for bid, b in adv.items():
        if not bid.startswith("GHSA"):
            continue
        text = (b.get("summary", "") + " " + b.get("details", ""))
        m = LINK.search(text)
        if not m:
            continue
        ref = m.group(2).upper()
        if ref in {x.upper() for x in [bid] + (b.get("aliases") or [])}:
            continue
        cands = [x for x in alias.get(ref, ()) if x.startswith("GHSA")] or list(alias.get(ref, ()))
        a = adv.get(cands[0]) if cands else None
        bc = commits(b)
        ac = commits(a) if a else []
        brepos = {r for r, _ in bc}
        arepos = {r for r, _ in ac}
        same = bool(brepos & arepos)
        key = (bid, ref)
        if key in seen:
            continue
        seen.add(key)
        eco, name = pkg(b)
        cwes = ",".join((b.get("database_specific") or {}).get("cwe_ids") or [])
        shared_fix = bool({c[:12] for _, c in ac} & {c[:12] for _, c in bc})
        status = ("same-fix-commit" if shared_fix else
                  "ready" if a and ac and bc and same else
                  "a-not-in-dumps" if not a else
                  "missing-a-commit" if not ac else
                  "missing-b-commit" if not bc else "different-repos")
        rows.append(dict(b=bid, link=m.group(1).lower(), a_ref=ref, a=(a or {}).get("id", ""), status=status,
                         ecosystem=eco, package=name, cwes=cwes,
                         repo=";".join(sorted(brepos & arepos or brepos or arepos)),
                         a_fix=";".join(c[:12] for r, c in ac), b_fix=";".join(c[:12] for r, c in bc),
                         a_published=((a or {}).get("published") or "")[:10], b_published=(b.get("published") or "")[:10],
                         summary=(b.get("summary") or "")[:100].replace("\t", " ")))
    rows.sort(key=lambda r: (r["status"] != "ready", r["ecosystem"] or "", r["package"] or ""))
    cols = list(rows[0].keys())
    with open(os.path.join(OUT, "h3b_pairs.tsv"), "w") as o:
        o.write("\t".join(cols) + "\n")
        for r in rows:
            o.write("\t".join(str(r[c]) for c in cols) + "\n")
    st = collections.Counter(r["status"] for r in rows)
    ready = [r for r in rows if r["status"] == "ready"]
    md = ["# H3b candidate pairs (incomplete fix): resolved from the OSV dumps", "",
          f"Linked pairs: {len(rows)}. By status: " + ", ".join(f"{k} {v}" for k, v in st.most_common()) + ".", "",
          "`ready` = both advisories found, both have fix commits, in the same repo. The task would pin the parent "
          "of A's first fix commit; the reference is A's fix plus B's fix.", "",
          f"Ready pairs by ecosystem: " + ", ".join(f"{k} {v}" for k, v in collections.Counter(r['ecosystem'] for r in ready).most_common()) + ".",
          "", "| B (later) | A (earlier) | Link | Repo | A fix | B fix | B published | Summary |", "|---|---|---|---|---|---|---|---|"]
    for r in ready[:60]:
        md.append(f"| {r['b']} | {r['a']} | {r['link']} | {r['repo']} | {r['a_fix']} | {r['b_fix']} | {r['b_published']} | {r['summary']} |")
    open(os.path.join(OUT, "h3b_summary.md"), "w").write("\n".join(md) + "\n")
    print("\n".join(md[:7]))


if __name__ == "__main__":
    main()
