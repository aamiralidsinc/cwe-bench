#!/usr/bin/env python3
"""Did a run reach the task's OWN repository (or a fixed release of its own package)?

The client's trial rule (2026-10-14): trials have internet but no access to the task's own
repository. Our runs before the netguard sidecar (common/trial/netguard, 2026-10-16) had open
internet, so a solve that fetched the task's repo does not count; audit_results.py excludes it.

    python3 common/audit/own_repo.py <trial_dir>      # prints the hits

Detection (transcript, agent/claude-code.txt): a WebFetch/WebSearch/Bash tool call naming
  - <host>/<owner>/<repo> on github.com, raw.githubusercontent.com, api.github.com/repos,
    codeload.github.com or gitlab.com, or any GitHub/GitLab path whose repo segment is <repo>
    (forks and mirrors);
  - the repo or package name on a package registry or source CDN (PyPI, npm, Maven Central,
    crates.io, Go proxy, RubyGems, Packagist, jsDelivr, unpkg, docs.rs).
  - a package-manager command fetching the task's package (pip download/install, npm pack/view/
    install, cargo add/download/install, go get / go mod download, gem fetch/install, composer
    require/show/download), e.g. `pip download asyncssh==2.20.0` (seen 2026-10-16).
A WebSearch query that merely names the project is NOT a hit (searching is allowed; opening the
repository is not). Results are cached in build/audit/own_repo_cache.json by transcript size.
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(next(p for p in Path(__file__).resolve().parents if (p / ".cwe-bench-root").is_file()) / "common"))
import paths  # noqa: E402  (repo locations: common/paths.py)

ROOT = paths.ROOT
CACHE = ROOT / "build/audit/own_repo_cache.json"
REGISTRIES = (r"pypi\.org|files\.pythonhosted\.org|registry\.npmjs\.org|npmjs\.com|repo1\.maven\.org|"
              r"repo\.maven\.apache\.org|central\.sonatype\.com|crates\.io|static\.crates\.io|docs\.rs|"
              r"proxy\.golang\.org|pkg\.go\.dev|rubygems\.org|packagist\.org|cdn\.jsdelivr\.net|unpkg\.com")


def task_names(task):
    """(owner, repo, extra package names) from tasks/<task>/task.toml."""
    t = (ROOT / "tasks" / task / "task.toml").read_text()
    m = re.search(r'repo\s*=\s*"https?://(?:www\.)?(?:github|gitlab)\.com/([^/"]+)/([^/"]+?)(?:\.git)?"', t)
    owner, repo = (m.group(1).lower(), m.group(2).lower()) if m else (None, None)
    pk = re.search(r'packages?\s*=\s*\[([^\]]*)\]', t)
    extra = [x.strip().strip('"').lower() for x in pk.group(1).split(",")] if pk else []
    return owner, repo, [x for x in extra if x]


def patterns(owner, repo, extra):
    names = {repo, *extra} - {None}
    alt = "|".join(re.escape(n) for n in sorted(names))
    pats = [rf"(github\.com|githubusercontent\.com|api\.github\.com/repos|gitlab\.com)[/:]{re.escape(owner)}/{re.escape(repo)}\b",
            rf"(github\.com|githubusercontent\.com|api\.github\.com/repos|gitlab\.com)[/:][\w.-]+/({alt})(\.git)?([/\"'\s?#]|$)",
            rf"({REGISTRIES})[^\s\"']*[/=@]({alt})([/\"'\s@?#._-]|$)",
            rf"\b(pip3?|python3? -m pip|uv pip|pipx)\s+(download|install|wheel|index)\b[^\n;&|]*?(?<![\w./-])({alt})(\[[^\]]*\])?([=<>~!]=?[\w.*]+)?(?![\w/.-])",
            rf"\b(npm|pnpm|yarn)\s+(pack|view|info|show|install|i|add)\b[^\n;&|]*?(?<![\w./-])({alt})(@[\w.^~*-]+)?(?![\w/-])",
            rf"\bcargo\s+(add|download|install|clone|info)\b[^\n;&|]*?\b({alt})\b",
            rf"\bgo\s+(get|install|mod\s+download)\b[^\n;&|]*?/({alt})(@[\w.-]+)?\b",
            rf"\bgem\s+(fetch|install|unpack)\b[^\n;&|]*?\b({alt})\b",
            rf"\bcomposer\s+(require|show|create-project|download)\b[^\n;&|]*?/({alt})\b"]
    return [re.compile(p, re.I) for p in pats]


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


def hits(trial, task):
    owner, repo, extra = task_names(task)
    p = Path(trial) / "agent" / "claude-code.txt"
    if not owner or not p.exists():
        return []
    pats = patterns(owner, repo, extra)
    out = []
    for name, inp in tool_calls(p):
        if name == "WebSearch":
            continue
        if name not in ("WebFetch", "Bash"):
            continue
        s = json.dumps(inp)
        if any(x.search(s) for x in pats):
            out.append(f"{name}: {s[:160]}")
    return out


def cached_hits(trial, task):
    p = Path(trial) / "agent" / "claude-code.txt"
    key = f"{Path(trial).parent.name}/{Path(trial).name}"
    size = p.stat().st_size if p.exists() else -1
    cache = json.loads(CACHE.read_text()) if CACHE.exists() else {}
    if key in cache and cache[key]["size"] == size:
        return cache[key]["hits"]
    h = hits(trial, task)
    cache[key] = {"size": size, "hits": h[:5], "n": len(h)}
    CACHE.write_text(json.dumps(cache, indent=0))
    return h[:5]


if __name__ == "__main__":
    t = Path(sys.argv[1])
    res = json.loads((t / "result.json").read_text())
    for h in hits(t, Path(res["config"]["task"]["path"]).name):
        print(h)
