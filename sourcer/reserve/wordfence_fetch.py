#!/usr/bin/env python3
"""C4 of reports/NEW-SOURCES.md: download the Wordfence Intelligence v3 production feed (the
complete WordPress vulnerability set, one JSON object keyed by record id).

Terms (checked 2026-10-24, scratchpad c4-terms.md): free for personal and commercial use;
perpetual licence to reproduce, prepare derivative works and distribute; every copy must keep the
record's hyperlink, Defiant's copyright designation and its licence text (plus MITRE's notice for
records that came from MITRE). A free wordfence.com account supplies the API key.
WPScan and Patchstack are NOT used: their terms forbid storing the data and third-party use.

The key is read from WORDFENCE_API_KEY in an env file (default /Users/dev/terminal-bench/.env),
or from --key-file (one line); never from the command line, and never printed. The raw feed is untrusted data, saved outside the code tree.

  python3 -I sources2/wordfence_fetch.py [--env-file F | --key-file F] [--data ~/.tb-graders/cwe/sources2-data]
"""
import argparse, json, os, time, urllib.request

URL = "https://www.wordfence.com/api/intelligence/v3/vulnerabilities/production"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--env-file", default="/Users/dev/terminal-bench/.env")
    ap.add_argument("--key-file", default="")
    ap.add_argument("--data", default=os.path.expanduser("~/.tb-graders/cwe/sources2-data"))
    a = ap.parse_args()
    if a.key_file:
        key = open(a.key_file).read().strip()
    else:
        key = next((l.split("=", 1)[1].strip().strip("'\"") for l in open(a.env_file)
                    if l.strip().startswith("WORDFENCE_API_KEY=")), "")
    if not key:
        raise SystemExit("no Wordfence key found (WORDFENCE_API_KEY in the env file, or --key-file)")
    out = os.path.join(a.data, "raw", "wordfence", time.strftime("production-%Y%m%dT%H%M%SZ.json", time.gmtime()))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    req = urllib.request.Request(URL, headers={"Authorization": f"Bearer {key}", "Accept": "application/json",
                                               "User-Agent": "cwe-bench-sourcer/0.1 (security-fix benchmark research)"})
    with urllib.request.urlopen(req, timeout=600) as r, open(out + ".part", "wb") as f:
        while True:
            chunk = r.read(1 << 20)
            if not chunk:
                break
            f.write(chunk)
    os.replace(out + ".part", out)
    feed = json.load(open(out))
    plugins = sum(1 for v in feed.values() for s in v.get("software") or [] if s.get("type") == "plugin")
    print(f"saved {out}: {len(feed)} records; {plugins} plugin software entries")


if __name__ == "__main__":
    main()
