#!/usr/bin/env python3
"""Turn MITRE's CWE catalogue and the 2025 CWE Top 25 into tables the screener can read.

    python3 research/extract_cwe_hierarchy.py

Input (verbatim downloads, see sources/mitre/SOURCE.md):
    sources/mitre/cwec_latest.xml.zip  full CWE catalogue (contains cwec_v4.20.xml, 2026-04-30)
    sources/mitre/top25_2025.html  the 2025 CWE Top 25 page
Output:
    cwe_hierarchy.tsv   id, name, abstraction (Pillar/Class/Base/Variant/Compound), status,
                        parent (primary ChildOf in the Research view CWE-1000), pillar (top
                        ancestor), depth, path (ids from pillar down to this CWE)
    cwe_top25_2025.tsv  rank, id, name
"""
import re
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE / "sources" / "mitre"
NS = {"c": "http://cwe.mitre.org/cwe-7"}
RESEARCH_VIEW = "1000"


def main():
    with zipfile.ZipFile(SRC / "cwec_latest.xml.zip") as z:          # 2 MB zip kept in the repo
        root = ET.fromstring(z.read("cwec_v4.20.xml"))
    rows, parent = {}, {}
    for w in root.iterfind(".//c:Weaknesses/c:Weakness", NS):
        wid = w.get("ID")
        rows[wid] = {"name": w.get("Name"), "abstraction": w.get("Abstraction"),
                     "status": w.get("Status")}
        prim = alt = None
        for rel in w.iterfind("c:Related_Weaknesses/c:Related_Weakness", NS):
            if rel.get("Nature") == "ChildOf" and rel.get("View_ID") == RESEARCH_VIEW:
                if rel.get("Ordinal") == "Primary":
                    prim = rel.get("CWE_ID")
                elif alt is None:
                    alt = rel.get("CWE_ID")
        if prim or alt:
            parent[wid] = prim or alt

    def path(wid):
        seen, p = [], wid
        while p and p not in seen:
            seen.append(p)
            p = parent.get(p)
        return list(reversed(seen))

    with open(HERE / "cwe_hierarchy.tsv", "w") as f:
        f.write("id\tname\tabstraction\tstatus\tparent\tpillar\tdepth\tpath\n")
        for wid in sorted(rows, key=int):
            p = path(wid)
            r = rows[wid]
            f.write("\t".join([wid, r["name"], r["abstraction"] or "", r["status"] or "",
                               parent.get(wid, ""), p[0], str(len(p) - 1), ">".join(p)]) + "\n")

    import html as htmllib
    page = (SRC / "top25_2025.html").read_text(errors="replace")
    table = page[page.index('id="Detail"'):]
    table = table[:table.index("</table>")]
    top = []
    for tr in re.findall(r"<tr>(.*?)</tr>", table, re.S):
        cells = [htmllib.unescape(re.sub(r"<[^>]+>", "", c)).strip()
                 for c in re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)]
        if len(cells) >= 6 and cells[0].isdigit():
            rank, cwe, name, score, kev, change = cells[:6]
            top.append((int(rank), cwe.replace("CWE-", ""), name, score, kev, change))
    top.sort()
    with open(HERE / "cwe_top25_2025.tsv", "w") as f:
        f.write("rank\tid\tname\tscore\tcves_in_kev\trank_change_vs_2024\n")
        for row in top:
            f.write("\t".join(map(str, row)) + "\n")
    print(f"{len(rows)} weaknesses, {len(parent)} with a Research-view parent; "
          f"Top 25 entries parsed: {len(top)}")


if __name__ == "__main__":
    main()
