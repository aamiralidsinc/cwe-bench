#!/usr/bin/env python3
"""Fill fetch_severity.py's NVD cache from NVD's bulk yearly feeds instead of the rate-limited API.

    python3 research/raw/item4-severity/seed_nvd_cache.py <cves.txt>

Feeds: https://nvd.nist.gov/feeds/json/cve/2.0/nvdcve-2.0-<year>.json.gz, downloaded to
~/.tb-graders/cwe/research-raw/item4-severity/nvd-feeds/ (download time in DOWNLOADED_AT).
A feed item has the same shape as an API 2.0 record, so each wanted CVE is written as
nvd/<CVE>.json = {"vulnerabilities": [item]}. Records already cached from the API are kept.
CVEs missing from the feeds are left for fetch_severity.py to fetch from the API.
"""
import gzip
import json
import sys
from pathlib import Path

BULK = Path.home() / ".tb-graders" / "cwe" / "research-raw" / "item4-severity"


def main():
    want = {l.strip() for l in Path(sys.argv[1]).read_text().split() if l.startswith("CVE-")}
    out = BULK / "nvd"
    out.mkdir(parents=True, exist_ok=True)
    cached = {p.stem for p in out.glob("CVE-*.json")}
    written = 0
    for feed in sorted((BULK / "nvd-feeds").glob("nvdcve-2.0-*.json.gz")):
        with gzip.open(feed) as f:
            for item in json.load(f).get("vulnerabilities", []):
                cve = item["cve"]["id"]
                if cve in want and cve not in cached:
                    (out / f"{cve}.json").write_text(json.dumps({"vulnerabilities": [item], "source": feed.name}))
                    cached.add(cve)
                    written += 1
    missing = sorted(want - cached)
    print(f"{written} records written from feeds; {len(want) - len(missing)}/{len(want)} cached; "
          f"missing {len(missing)}: {' '.join(missing[:20])}{' ...' if len(missing) > 20 else ''}")


if __name__ == "__main__":
    main()
