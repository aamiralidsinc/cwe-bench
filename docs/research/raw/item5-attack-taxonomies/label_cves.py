#!/usr/bin/env python3
"""Label every benchmark CVE with attack-taxonomy classes (research item 5).

    python3 research/raw/item5-attack-taxonomies/label_cves.py

Chain: CVE -> CWE (NVD record) -> CAPEC attack patterns -> CAPEC top classes and ATT&CK tactics;
       CWE -> STRIDE (derived from the CWE's own Common_Consequences impacts; MITRE publishes no
       STRIDE mapping, so this is our derivation, table IMPACT_TO_STRIDE below);
       CVE -> CVSS attack vector / privileges / user interaction / C-I-A impact (NVD vector).

Inputs:
    ../item4-severity/all_cves.txt                         CVEs of the item-4 outcome table
    ~/.tb-graders/cwe/research-raw/item4-severity/nvd/     NVD record per CVE (item 4 cache)
    ../../sources/mitre/cwec_latest.xml.zip                CWE 4.20 (CWE->CAPEC links, consequences)
    ../../cwe_hierarchy.tsv                                Research-view parents (fallback walk)
    ~/.tb-graders/cwe/research-raw/item5-attack-taxonomies/mitre/
        capec_latest.xml       CAPEC 3.9 (patterns, CWE links, ATT&CK mappings, views 1000/3000)
        enterprise-attack.json ATT&CK Enterprise STIX (technique -> tactics)
Output: cve_attack_labels.tsv (one row per CVE; multi-valued cells joined with ';') and
        ../../cwe_attack_classes.tsv (one row per CWE: CAPEC mechanisms and ATT&CK tactics, read
        by the screener through weights.json weakness.attack_label).

CWE -> CAPEC uses both directions (CWE Related_Attack_Patterns and CAPEC Related_Weaknesses).
A CWE with no CAPEC link inherits the links of its nearest Research-view ancestor that has any
(column capec_via says 'own' or 'ancestor:<id>'). Deprecated and obsolete patterns are dropped.
"""
import csv
import json
import xml.etree.ElementTree as ET
import zipfile
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
RES = HERE.parents[1]
I4 = Path.home() / ".tb-graders/cwe/research-raw/item4-severity"
M = Path.home() / ".tb-graders/cwe/research-raw/item5-attack-taxonomies/mitre"
CWE_NS = {"c": "http://cwe.mitre.org/cwe-7"}
CAP_NS = {"c": "http://capec.mitre.org/capec-3"}

# CWE Common_Consequences <Impact> -> STRIDE letters. Impacts not listed carry no STRIDE class.
IMPACT_TO_STRIDE = {
    "Gain Privileges or Assume Identity": "SE",
    "Bypass Protection Mechanism": "E",
    "Execute Unauthorized Code or Commands": "E",
    "Hide Activities": "R",
    "Alter Execution Logic": "T",
}
PREFIX_TO_STRIDE = {"Read ": "I", "Modify ": "T", "DoS:": "D"}
STRIDE_NAMES = {"S": "Spoofing", "T": "Tampering", "R": "Repudiation", "I": "InfoDisclosure",
                "D": "DoS", "E": "ElevationOfPrivilege"}
LEVEL = {"Low": 1, "Medium": 2, "High": 3}


def stride_of(impacts):
    out = set()
    for imp in impacts:
        out.update(IMPACT_TO_STRIDE.get(imp, ""))
        for p, s in PREFIX_TO_STRIDE.items():
            if imp.startswith(p):
                out.add(s)
    return {STRIDE_NAMES[s] for s in out}


def load_cwe():
    with zipfile.ZipFile(RES / "sources/mitre/cwec_latest.xml.zip") as z:
        root = ET.fromstring(z.read("cwec_v4.20.xml"))
    capec, impacts = defaultdict(set), defaultdict(set)
    for w in root.iterfind(".//c:Weaknesses/c:Weakness", CWE_NS):
        wid = w.get("ID")
        for a in w.iterfind("c:Related_Attack_Patterns/c:Related_Attack_Pattern", CWE_NS):
            capec[wid].add(a.get("CAPEC_ID"))
        for i in w.iterfind("c:Common_Consequences/c:Consequence/c:Impact", CWE_NS):
            impacts[wid].add(i.text.strip())
    parent = {r["id"]: r["parent"] for r in csv.DictReader(open(RES / "cwe_hierarchy.tsv"), delimiter="\t")}
    return capec, impacts, parent


def load_capec():
    root = ET.parse(M / "capec_latest.xml").getroot()
    pats, child_of, cwe_links = {}, defaultdict(set), defaultdict(set)
    for a in root.iterfind(".//c:Attack_Patterns/c:Attack_Pattern", CAP_NS):
        if a.get("Status") in ("Deprecated", "Obsolete"):
            continue
        pid = a.get("ID")
        skills = [LEVEL.get(s.get("Level")) for s in a.iterfind("c:Skills_Required/c:Skill", CAP_NS)]
        skills = [s for s in skills if s]
        pats[pid] = {
            "abstraction": a.get("Abstraction"),
            "likelihood": (a.findtext("c:Likelihood_Of_Attack", "", CAP_NS) or "").strip(),
            "severity": (a.findtext("c:Typical_Severity", "", CAP_NS) or "").strip(),
            "skill_min": min(skills) if skills else None,
            "attack": {t.findtext("c:Entry_ID", "", CAP_NS).strip()
                       for t in a.iterfind("c:Taxonomy_Mappings/c:Taxonomy_Mapping", CAP_NS)
                       if t.get("Taxonomy_Name") == "ATTACK" and t.findtext("c:Entry_ID", "", CAP_NS)},
        }
        for r in a.iterfind("c:Related_Attack_Patterns/c:Related_Attack_Pattern", CAP_NS):
            if r.get("Nature") == "ChildOf":
                child_of[pid].add(r.get("CAPEC_ID"))
        for w in a.iterfind("c:Related_Weaknesses/c:Related_Weakness", CAP_NS):
            cwe_links[w.get("CWE_ID")].add(pid)
    cats = {c.get("ID"): (c.get("Name"), {m.get("CAPEC_ID") for m in c.iterfind(".//c:Has_Member", CAP_NS)})
            for c in root.iterfind(".//c:Categories/c:Category", CAP_NS)}
    views = {}
    for v in root.iterfind(".//c:Views/c:View", CAP_NS):
        if v.get("ID") in ("1000", "3000"):
            views[v.get("ID")] = [cats[m.get("CAPEC_ID")] for m in v.iterfind(".//c:Has_Member", CAP_NS)]

    def ancestors(pid, seen=None):
        seen = seen if seen is not None else set()
        for p in child_of.get(pid, ()):
            if p not in seen:
                seen.add(p)
                ancestors(p, seen)
        return seen

    def classes(view, pid):
        family = {pid} | ancestors(pid)
        return {name for name, members in views[view] if family & members}

    for pid, p in pats.items():
        p["mechanism"] = classes("1000", pid)
        p["domain"] = classes("3000", pid)
    return pats, cwe_links


def load_attack():
    d = json.loads((M / "enterprise-attack.json").read_text())
    tactics = {}
    for o in d["objects"]:
        if o["type"] == "attack-pattern" and not o.get("revoked"):
            ext = next((r["external_id"] for r in o.get("external_references", [])
                        if r.get("source_name") == "mitre-attack"), None)
            if ext:
                tactics[ext] = {k["phase_name"] for k in o.get("kill_chain_phases", [])}
    return tactics


def nvd(cve):
    p = I4 / "nvd" / f"{cve}.json"
    v = json.loads(p.read_text()).get("vulnerabilities") or [] if p.exists() else []
    if not v:
        return [], {}
    c = v[0]["cve"]
    prim, sec = [], []
    for w in c.get("weaknesses", []):
        ids = [d["value"].replace("CWE-", "") for d in w.get("description", [])
               if d["value"].startswith("CWE-")]
        (prim if w.get("type") == "Primary" else sec).extend(ids)
    vec = {}
    m = c.get("metrics", {})
    for key in ("cvssMetricV31", "cvssMetricV30", "cvssMetricV40"):
        if m.get(key):
            x = next((x for x in m[key] if x.get("type") == "Primary"), m[key][0])["cvssData"]
            vec = {"av": x.get("attackVector", ""), "pr": x.get("privilegesRequired", ""),
                   "ui": x.get("userInteraction", ""),
                   "c": x.get("confidentialityImpact", x.get("vulnConfidentialityImpact", "")),
                   "i": x.get("integrityImpact", x.get("vulnIntegrityImpact", "")),
                   "a": x.get("availabilityImpact", x.get("vulnAvailabilityImpact", ""))}
            break
    return sorted(set(prim or sec), key=int), vec


def main():
    cwe_capec, cwe_impacts, parent = load_cwe()
    pats, capec_cwe = load_capec()
    tactics = load_attack()
    links = defaultdict(set)
    for wid, ps in cwe_capec.items():
        links[wid] |= ps
    for wid, ps in capec_cwe.items():
        links[wid] |= ps
    links = {w: {p for p in ps if p in pats} for w, ps in links.items()}

    def capec_for(wid):
        p, hops = wid, 0
        while p and hops < 10:
            if links.get(p):
                return links[p], "own" if p == wid else f"ancestor:{p}"
            p, hops = parent.get(p), hops + 1
        return set(), ""

    def classes_of(caps):
        mech = set().union(*(pats[p]["mechanism"] for p in caps)) if caps else set()
        techs = set().union(*(pats[p]["attack"] for p in caps)) if caps else set()
        tac = set()
        for t in techs:
            tac |= tactics.get(f"T{t}" if not t.startswith("T") else t, set())
        return mech, techs, tac

    # Per-CWE table for the screener (weights.json weakness.attack_label reads it).
    with open(RES / "cwe_attack_classes.tsv", "w") as f:
        f.write("cwe\tcapec_via\tmechanism\tattack_tactic\n")
        for wid in sorted(parent, key=int):
            caps, via = capec_for(wid)
            mech, _techs, tac = classes_of(caps)
            f.write(f"{wid}\t{via}\t{';'.join(sorted(mech))}\t{';'.join(sorted(tac))}\n")

    cves = sorted({l.strip() for l in (HERE.parent / "item4-severity/all_cves.txt").read_text().split()
                   if l.startswith("CVE-")})
    cols = ["cve", "cwes", "capec_ids", "capec_via", "n_capec", "mechanism", "domain", "attack_tactic",
            "n_attack_techniques", "capec_skill_min", "capec_likelihood_max", "stride",
            "cvss_av", "cvss_pr", "cvss_ui", "cvss_c", "cvss_i", "cvss_a"]
    with open(HERE / "cve_attack_labels.tsv", "w") as f:
        f.write("\t".join(cols) + "\n")
        for cve in cves:
            cwes, vec = nvd(cve)
            caps, via, impacts = set(), [], set()
            for w in cwes:
                ps, v = capec_for(w)
                caps |= ps
                if v:
                    via.append(f"{w}:{v}")
                impacts |= cwe_impacts.get(w, set())
            mech, techs, tac = classes_of(caps)
            dom = set().union(*(pats[p]["domain"] for p in caps)) if caps else set()
            skills = [pats[p]["skill_min"] for p in caps if pats[p]["skill_min"]]
            likes = [LEVEL.get(pats[p]["likelihood"]) for p in caps if LEVEL.get(pats[p]["likelihood"])]
            row = [cve, ";".join(cwes), ";".join(sorted(caps, key=int)), ";".join(via), len(caps),
                   ";".join(sorted(mech)), ";".join(sorted(dom)), ";".join(sorted(tac)), len(techs),
                   min(skills) if skills else "", max(likes) if likes else "",
                   ";".join(sorted(stride_of(impacts))),
                   vec.get("av", ""), vec.get("pr", ""), vec.get("ui", ""),
                   vec.get("c", ""), vec.get("i", ""), vec.get("a", "")]
            f.write("\t".join(map(str, row)) + "\n")
    print(f"{len(cves)} CVEs labelled -> cve_attack_labels.tsv")


if __name__ == "__main__":
    main()
