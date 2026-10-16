#!/usr/bin/env python3
"""Fetch CVSS, EPSS and CISA KEV status for a list of CVEs (research item 4).

    python3 research/raw/item4-severity/fetch_severity.py <cves.txt> <out.tsv>

Raw responses are cached (bulk, outside the repo) in
~/.tb-graders/cwe/research-raw/item4-severity/:
    nvd/<CVE>.json   NVD API 2.0 record (CVSS v4.0 / v3.1 / v3.0 / v2 metrics)
    epss.json        FIRST EPSS API responses (current scores)
    kev.json         CISA Known Exploited Vulnerabilities catalogue
Output TSV columns:
    cve, cvss_version, cvss_score, cvss_severity, cvss_source, epss, epss_percentile, kev, kev_date_added
NVD allows ~5 requests / 30 s without an API key, so NVD calls are spaced 6.5 s apart and
cached, so a rerun only fetches what is missing.
"""
import json
import sys
import time
import urllib.request
from pathlib import Path

BULK = Path.home() / ".tb-graders" / "cwe" / "research-raw" / "item4-severity"
UA = {"User-Agent": "cwe-bench-research/0.1 (security benchmark research; cached, polite)"}


def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
        return json.loads(r.read().decode())


def nvd(cve):
    p = BULK / "nvd" / f"{cve}.json"
    if not p.exists():
        for attempt in range(3):
            try:
                data = get(f"https://services.nvd.nist.gov/rest/json/cves/2.0?cveId={cve}")
                p.write_text(json.dumps(data))
                break
            except Exception as e:                       # rate limit or transient error
                print(f"  {cve}: {e}; retrying", flush=True)
                time.sleep(30)
        time.sleep(6.5)
    if not p.exists():
        return None
    vulns = json.loads(p.read_text()).get("vulnerabilities") or []
    if not vulns:
        return None
    metrics = vulns[0]["cve"].get("metrics", {})
    for key, ver in (("cvssMetricV40", "4.0"), ("cvssMetricV31", "3.1"),
                     ("cvssMetricV30", "3.0"), ("cvssMetricV2", "2.0")):
        ms = metrics.get(key) or []
        if ms:
            m = next((x for x in ms if x.get("type") == "Primary"), ms[0])
            d = m["cvssData"]
            return ver, d.get("baseScore"), d.get("baseSeverity") or m.get("baseSeverity"), m.get("source")
    return None


def main():
    cves = sorted({l.strip() for l in Path(sys.argv[1]).read_text().split() if l.startswith("CVE-")})
    (BULK / "nvd").mkdir(parents=True, exist_ok=True)
    kev_p = BULK / "kev.json"
    if not kev_p.exists():
        kev_p.write_text(json.dumps(get(
            "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json")))
    kev = {v["cveID"]: v.get("dateAdded") for v in json.loads(kev_p.read_text())["vulnerabilities"]}
    epss_p = BULK / "epss.json"
    epss = json.loads(epss_p.read_text()) if epss_p.exists() else {}
    todo = [c for c in cves if c not in epss]
    for i in range(0, len(todo), 80):
        batch = todo[i:i + 80]
        for row in get("https://api.first.org/data/v1/epss?cve=" + ",".join(batch)).get("data", []):
            epss[row["cve"]] = {"epss": row["epss"], "percentile": row["percentile"], "date": row["date"]}
        for c in batch:
            epss.setdefault(c, None)
        time.sleep(1)
    epss_p.write_text(json.dumps(epss, indent=0))
    with open(sys.argv[2], "w") as f:
        f.write("cve\tcvss_version\tcvss_score\tcvss_severity\tcvss_source\tepss\tepss_percentile\tkev\tkev_date_added\n")
        for n, c in enumerate(cves, 1):
            v = nvd(c) or ("", "", "", "")
            e = epss.get(c) or {}
            f.write("\t".join(map(str, [c, *v, e.get("epss", ""), e.get("percentile", ""),
                                        int(c in kev), kev.get(c, "")])) + "\n")
            f.flush()
            if n % 20 == 0:
                print(f"{n}/{len(cves)}", flush=True)
    print(f"done: {len(cves)} CVEs, {sum(c in kev for c in cves)} in KEV")


if __name__ == "__main__":
    main()
