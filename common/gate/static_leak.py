#!/usr/bin/env python3
"""static_leak.py: the static half of the file-time leak check (2026-10-28, reports/reward-hacking.md section 6).

    python3 common/gate/static_leak.py <task_dir | tasks_root> [...]      TSV, one row per task

A task's starting tree shows the builder's edits through file times when, after the source is fetched, a later step
rewrites tracked files (patch / git apply / sed -i / perl -i / COPY over the tree / cp into it / rsync / a Python
edit) and no whole-tree time reset follows (the B2b step of common/builder/templates/environment.Dockerfile, or the
step common/builder/tree_time_reset.py inserts). Rule for builders: never write the source tree after B2.

The gate's static stage reports a "yes" or "maybe" verdict as a WARNING (gate.py leak_warnings). Owner decision
2026-10-28: it stays a warning permanently, never a failure. From the investigation's tools/static_classify.py
(build/audit/timestamp-leak-20261028/), which predicted the dynamic result for 221 of 222 probed tasks.
"""
import os
import re
import sys
from pathlib import Path


def instructions(text):
    """Dockerfile -> list of (keyword, body) with continuations joined."""
    out, buf = [], ""
    for line in text.splitlines():
        s = line.rstrip()
        if not buf and (not s.strip() or s.lstrip().startswith("#")):
            continue
        if s.lstrip().startswith("#") and buf:
            continue
        if s.endswith("\\"):
            buf += s[:-1] + " "
            continue
        buf += s
        m = re.match(r"\s*(\w+)\s+(.*)", buf, re.S)
        if m:
            out.append((m.group(1).upper(), m.group(2)))
        buf = ""
    if buf:
        m = re.match(r"\s*(\w+)\s+(.*)", buf, re.S)
        if m:
            out.append((m.group(1).upper(), m.group(2)))
    return out


FETCH = re.compile(r"git\s+(-C\s+\S+\s+)?(checkout|clone)|git\s+.*fetch|curl[^|;&]*(\.tar|\.zip|archive|codeload)|wget|tar\s+-?x|unzip|pip\s+download")
MOD = [
    ("patch", re.compile(r"(^|[;&|(\s])patch\s+(-|<)")),
    ("git-apply", re.compile(r"git\s+(-C\s+\S+\s+)?(apply|am)\b")),
    ("sed-i", re.compile(r"\bsed\s+(-[a-zA-Z]*\s+)*-[a-zA-Z]*i")),
    ("perl-i", re.compile(r"\bperl\s+-[a-zA-Z]*i")),
    ("python-edit", re.compile(r"python3?\s+(-c|-\s*<<|/tmp/\S+\.py|\S+\.py)")),
    ("cp-into", re.compile(r"\bcp\s+(-[a-zA-Z]+\s+)*\S+\s+(/workspace|/app|\.)")),
    ("rsync", re.compile(r"\brsync\b")),
    ("heredoc-write", re.compile(r"(cat|tee)\s+[^|;&]*>\s*/(workspace|app)/|<<\s*'?EOF")),
]
NORM = re.compile(r"touch\s+(-[a-zA-Z]*\s+)*(-d|-t|-r|--date|--reference)|SOURCE_DATE_EPOCH|--mtime|os\.utime")


def classify(df: Path):
    text = df.read_text(errors="replace")
    ins = instructions(text)
    env = df.parent
    ctx_files = sorted(str(p.relative_to(env)) for p in env.rglob("*") if p.is_file() and p.name != "Dockerfile")
    patch_files = [f for f in ctx_files if f.endswith((".patch", ".diff"))]
    fetched = None
    events = []
    workdir = "/"
    for i, (kw, body) in enumerate(ins):
        if kw == "WORKDIR":
            workdir = body.strip()
        if kw == "RUN":
            if fetched is None and FETCH.search(body):
                fetched = i
            if NORM.search(body):
                events.append((i, "normalise", body[:80]))
            if fetched is not None:
                for name, rx in MOD:
                    if rx.search(body):
                        # same RUN as the fetch still leaks (seconds apart) unless normalised in it
                        events.append((i, name + ("@fetch-run" if i == fetched else ""), body[:100]))
        if kw in ("COPY", "ADD"):
            parts = [p for p in body.split() if not p.startswith("--")]
            if len(parts) >= 2:
                dest = parts[-1]
                srcs = parts[:-1]
                tgt = dest if dest.startswith("/") else os.path.join(workdir, dest)
                into_tree = tgt.startswith(("/workspace", "/app", "/src", "/code", "/repo")) or tgt in (".", "./")
                is_patch_copy = all(s.endswith((".patch", ".diff")) or "inject" in s for s in srcs) and tgt.startswith("/tmp")
                if into_tree and not is_patch_copy:
                    events.append((i, "copy-into-tree" + ("" if fetched is not None else "-before-fetch"), body[:100]))
    mods = [e for e in events if e[1] != "normalise"]
    norms = [e for e in events if e[1] == "normalise"]
    last_mod = max((e[0] for e in mods), default=-1)
    normalised_after = any(n[0] >= last_mod for n in norms) if mods else bool(norms)
    a6 = any("Starting project" in b for _, b in ins)
    # crude "source modified after fetch" decision
    strong = [e for e in mods if e[1].split("@")[0] in ("patch", "git-apply", "copy-into-tree", "sed-i", "perl-i", "cp-into", "rsync")]
    weak = [e for e in mods if e not in strong]
    if strong and not normalised_after:
        verdict = "yes"
    elif weak and not normalised_after:
        verdict = "maybe"
    elif mods and normalised_after:
        verdict = "no-normalised"
    else:
        verdict = "no"
    return {
        "patch_files": ",".join(patch_files),
        "n_ctx_files": len(ctx_files),
        "fetch_step": fetched,
        "mod_steps": ";".join(f"{e[0]}:{e[1]}" for e in mods),
        "normalised": int(normalised_after),
        "a6_baseline": int(a6),
        "static_leak": verdict,
    }


COLS = ["patch_files", "n_ctx_files", "fetch_step", "mod_steps", "normalised", "a6_baseline", "static_leak"]


def warnings(task_dir) -> list:
    """Gate warnings for tasks/<slug>/: [] when the Dockerfile resets the tree's times after its last edit."""
    df = Path(task_dir) / "environment" / "Dockerfile"
    if not df.is_file():
        return []
    try:
        r = classify(df)
    except Exception as e:          # a warning check must never break the gate
        return [f"file-time leak rule: could not classify environment/Dockerfile ({type(e).__name__}: {e})"]
    if r["static_leak"] == "yes":
        return [f"file-time leak: environment/Dockerfile changes the source tree after the fetch ({r['mod_steps']}) "
                f"with no whole-tree time reset afterwards, so the changed files keep their own time "
                f"(fix: python3 common/builder/tree_time_reset.py tasks/<slug>/environment/Dockerfile)"]
    if r["static_leak"] == "maybe":
        return [f"file-time leak (possible): environment/Dockerfile may edit the source tree after the fetch "
                f"({r['mod_steps']}) with no whole-tree time reset afterwards"]
    return []


def main(argv):
    if not argv:
        sys.exit(__doc__)
    print("slug\t" + "\t".join(COLS))
    for a in argv:
        p = Path(a)
        dirs = [p] if (p / "environment").is_dir() else sorted(d for d in p.iterdir() if d.is_dir())
        for d in dirs:
            df = d / "environment" / "Dockerfile"
            if df.is_file():
                r = classify(df)
                print(d.name + "\t" + "\t".join(str(r[c]) for c in COLS))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
