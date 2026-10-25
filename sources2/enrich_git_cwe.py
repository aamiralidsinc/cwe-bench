#!/usr/bin/env python3
"""C2 of reports/NEW-SOURCES.md: add CWE ids from the NVD feeds to the OSV `GIT` dump, so that the
unchanged sourcer's parse stage (which rejects a record with no CWE as `no_cwe`) can keep them.

OSV's GIT ecosystem is converted from NVD CVE records; only about 37% carry
database_specific.cwe_ids. For every record without one, the CVE id (record id or alias) is looked
up in the NVD 2.0 yearly feeds; its CWE ids (`weaknesses[].description[].value`, ignoring
NVD-CWE-Other / NVD-CWE-noinfo) are written into database_specific.cwe_ids, with
database_specific.cwe_source = "nvd". Nothing else in the record changes.

Input : <data>/raw/GIT.orig.zip (moved there from dumps/GIT.zip on the first run), NVD feeds
        (--nvd DIR [DIR...], nvdcve-2.0-<year>.json.gz; a later directory wins for the same year).
Output: <data>/dumps/GIT.zip (enriched). All input is untrusted data, parsed as JSON only.

  python3 -I sources2/enrich_git_cwe.py --nvd ~/.tb-graders/cwe/research-raw/item4-severity/nvd-feeds ~/.tb-graders/cwe/sources2-data/nvd
"""
import argparse, glob, gzip, json, os, re, shutil, zipfile


def nvd_cwes(dirs):
    feeds = {}
    for d in dirs:
        for f in glob.glob(os.path.join(os.path.expanduser(d), "nvdcve-2.0-*.json.gz")):
            feeds[os.path.basename(f)] = f            # a later directory replaces the same year
    out = {}
    for f in sorted(feeds.values()):
        for v in json.load(gzip.open(f)).get("vulnerabilities") or []:
            c = v.get("cve") or {}
            ids = sorted({d.get("value") for w in c.get("weaknesses") or [] for d in w.get("description") or []
                          if re.fullmatch(r"CWE-\d+", str(d.get("value", "")))})
            if c.get("id") and ids:
                out[c["id"].upper()] = ids
    return out, sorted(feeds)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=os.path.expanduser("~/.tb-graders/cwe/sources2-data"))
    ap.add_argument("--nvd", nargs="+", required=True)
    a = ap.parse_args()
    orig = os.path.join(a.data, "raw", "GIT.orig.zip")
    dump = os.path.join(a.data, "dumps", "GIT.zip")
    if not os.path.isfile(orig):
        shutil.move(dump, orig)
    cwemap, feeds = nvd_cwes(a.nvd)
    print(f"NVD feeds: {len(feeds)} ({feeds[0]} .. {feeds[-1]}); CVEs with a CWE: {len(cwemap)}")
    n = had = added = still = 0
    tmp = dump + ".part"
    with zipfile.ZipFile(orig) as zin, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
        for name in zin.namelist():
            raw = zin.read(name)
            try:
                rec = json.loads(raw.decode("utf-8", "replace"))
            except Exception:
                zout.writestr(name, raw)
                continue
            n += 1
            ds = rec.setdefault("database_specific", {}) if isinstance(rec.get("database_specific", {}), dict) else None
            if ds is None or ds.get("cwe_ids"):
                had += ds is not None
                zout.writestr(name, raw)
                continue
            ids = [rec.get("id", "")] + list(rec.get("aliases") or [])
            cwes = sorted({c for i in ids if str(i).upper().startswith("CVE-") for c in cwemap.get(str(i).upper(), [])})
            if cwes:
                ds["cwe_ids"], ds["cwe_source"] = cwes, "nvd"
                added += 1
            else:
                still += 1
            zout.writestr(name, json.dumps(rec))
    os.replace(tmp, dump)
    print(f"GIT records {n}: already had a CWE {had}; CWE added from NVD {added}; still none {still}")


if __name__ == "__main__":
    main()
