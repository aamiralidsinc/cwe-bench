#!/usr/bin/env python3
"""Did a run use the internet to look things up? (CWE-bench runs agents OFFLINE: "Each attempt runs
in an isolated container whose only network access is the model provider's API", arXiv 2610.17020.)

    python3 build/internet_use.py <trial_dir>     # prints the hits

Our tasks switched to that setting per task at the time in build/audit/offline_since.tsv. A run that
started before its task's switch had open internet; audit_results.py counts its SOLVE only if this
finds no lookup (a failure with more access than CWE-bench allows still counts).

A hit is a tool call in agent/claude-code.txt that fetched information from the internet:
  - any WebSearch or WebFetch call;
  - a Bash command naming an external http(s)/git/ssh URL (curl, wget, git clone/fetch/ls-remote,
    python/node one-liners), i.e. a host with a public top-level domain, not localhost/127.x/0.0.0.0;
  - a package-SOURCE download: pip download, npm view/pack/info, cargo download/clone, go mod
    download, gem fetch/unpack, composer download.
Installing ordinary tools (pip install pytest) is not a hit. Cached in build/audit/internet_use_cache.json.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path("/Users/dev/terminal-bench/cwe-bench")
CACHE = Path(__file__).resolve().parent.parent / "out/internet_use_cache.json"
SINCE = ROOT / "build/audit/offline_since.tsv"
LOCAL = r"(?:localhost|127\.\d+\.\d+\.\d+|0\.0\.0\.0|\[::1\]|host\.docker\.internal)"
URL = re.compile(rf"(?:https?|git|ssh|ftp)://(?!{LOCAL}[:/])[A-Za-z0-9.-]+\.[A-Za-z]{{2,}}(?::\d+)?|git@[A-Za-z0-9.-]+\.[a-z]{{2,}}:", re.I)
SOURCE_DL = re.compile(r"\b(pip3?\s+download|python3? -m pip\s+download|npm\s+(view|pack|info|show)|pnpm\s+(view|pack|info)|"
                       r"yarn\s+info|cargo\s+(download|clone)|go\s+mod\s+download|gem\s+(fetch|unpack)|composer\s+download)\b", re.I)


def tool_calls(path):
    for line in open(path, errors="replace"):
        try:
            ev = json.loads(line)
        except ValueError:
            continue
        msg = ev.get("message") if isinstance(ev, dict) else None
        if isinstance(msg, dict) and ev.get("type") == "assistant":
            for c in msg.get("content") or []:
                if isinstance(c, dict) and c.get("type") == "tool_use":
                    yield c.get("name"), c.get("input") or {}


def hits(trial):
    p = Path(trial) / "agent" / "claude-code.txt"
    if not p.exists():
        return []
    out = []
    for name, inp in tool_calls(p):
        if name in ("WebSearch", "WebFetch"):
            out.append(f"{name}: {(inp.get('url') or inp.get('query') or '')[:140]}")
        elif name == "Bash":
            cmd = str(inp.get("command", ""))
            if URL.search(cmd) or SOURCE_DL.search(cmd):
                out.append("Bash: " + cmd[:140].replace("\n", " "))
    return out


def offline_since():
    """task -> UTC 'YYYY-MM-DDTHH:MM' when its trials became offline (empty file -> none)."""
    if not SINCE.exists():
        return {}
    return {l.split("\t")[0]: l.split("\t")[1] for l in SINCE.read_text().splitlines()
            if l and not l.startswith(("#", "task\t"))}


def cached_hits(trial):
    p = Path(trial) / "agent" / "claude-code.txt"
    key = f"{Path(trial).parent.name}/{Path(trial).name}"
    size = p.stat().st_size if p.exists() else -1
    cache = json.loads(CACHE.read_text()) if CACHE.exists() else {}
    if key in cache and cache[key]["size"] == size:
        return cache[key]["hits"]
    h = hits(trial)
    cache[key] = {"size": size, "hits": h[:5], "n": len(h)}
    CACHE.write_text(json.dumps(cache, indent=0))
    return h[:5]


if __name__ == "__main__":
    for h in hits(sys.argv[1]):
        print(h)
