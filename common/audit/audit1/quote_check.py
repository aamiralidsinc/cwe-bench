#!/usr/bin/env python3
"""Audit 1, step 3 (no LLM): every quote in a DOSSIER.json must exist verbatim in the cited file near the cited line.

    python3 common/audit/audit1/quote_check.py <run-folder> [--json <out.json>] [--window 3]

A quote is any object {"file", "line", "quote"} anywhere in DOSSIER.json. It passes when its text, with whitespace
normalised (runs of spaces, tabs and newlines count as one space), occurs in <run-folder>/<file> and the occurrence
STARTS within --window lines (default 3) of the cited line. Choices made where the design left room:
  - A quote may span lines (the file text is normalised as a whole, so wrapped instruction sentences match).
  - In a .patch/.diff file the leading diff marker of each line (+, -, space) may be left out of the quote.
  - In evidence/transcript.md the digest replaces newlines inside a tool result with " | "; a quote that copies
    the original newlines instead (or the reverse) still matches.
  - In evidence/transcript.md (the digest: one tool call, result or agent message per block, a block starts with
    "AGENT: ", "CALL " or "RESULT: ") a quote also passes when the cited line is within --window lines of the FIRST
    line of the block that holds the quote: citing where a long agent message starts still leads the reader to it.
    --strict-lines turns this off (calibration reports both).
  - Nothing else is forgiven: no case folding, no ellipsis gaps, no paraphrase. An empty quote, a file outside the
    run folder, a missing file or a non-integer line fails.
A dossier passes when every quote passes and it has at least one quote. Exit 0 = pass, 1 = fail, 2 = no dossier.
"""
import argparse
import json
import re
import sys
from pathlib import Path

WS = re.compile(r"\s+")


def norm(s):
    return WS.sub(" ", s).strip()


def quotes_in(obj, path="$"):
    if isinstance(obj, dict):
        if {"file", "quote"} <= set(obj) and isinstance(obj.get("quote"), str):
            yield path, obj
            return
        for k, v in obj.items():
            yield from quotes_in(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from quotes_in(v, f"{path}[{i}]")


class FileText:
    """Whitespace-normalised text of a file with a map from normalised offsets to 1-based line numbers."""

    def __init__(self, lines, strip_markers=False, pipes=False):
        chars, line_at = [], []
        prev_space = True
        for n, line in enumerate(lines, 1):
            if strip_markers and line[:1] in "+- " and not line.startswith(("+++", "---")):
                line = line[1:]
            if pipes:
                line = line.replace(" | ", "\n")
            for ch in line + "\n":
                if ch.isspace():
                    if not prev_space:
                        chars.append(" ")
                        line_at.append(n)
                    prev_space = True
                else:
                    chars.append(ch)
                    line_at.append(n)
                    prev_space = False
        self.text = "".join(chars)
        self.line_at = line_at

    def starts(self, q):
        out, i = [], self.text.find(q)
        while i >= 0:
            out.append(self.line_at[i])
            i = self.text.find(q, i + 1)
        return out


_cache = {}


def views(path):
    if path not in _cache:
        lines = path.read_text(errors="replace").splitlines()
        v = [FileText(lines)]
        if path.suffix in (".patch", ".diff"):
            v.append(FileText(lines, strip_markers=True))
        if path.name == "transcript.md":
            v.append(FileText(lines, pipes=True))
        _cache[path] = v
    return _cache[path]


BLOCK_START = ("AGENT: ", "CALL ", "RESULT: ")
_blocks = {}


def block_start(path, line):
    """First line of the transcript-digest block holding `line` (1-based)."""
    if path not in _blocks:
        starts, cur = [], 1
        for n, text in enumerate(path.read_text(errors="replace").splitlines(), 1):
            if text.startswith(BLOCK_START):
                cur = n
            starts.append(cur)
        _blocks[path] = starts
    st = _blocks[path]
    return st[line - 1] if 0 < line <= len(st) else line


def check_one(root, q, window, strict_lines=False):
    f, line, text = q.get("file"), q.get("line"), q.get("quote")
    res = {"file": f, "line": line, "quote": (text or "")[:200]}
    if not isinstance(text, str) or not norm(text):
        return {**res, "ok": False, "why": "empty quote"}
    try:
        line = int(line)
    except (TypeError, ValueError):
        return {**res, "ok": False, "why": "line is not an integer"}
    if not isinstance(f, str) or not f:
        return {**res, "ok": False, "why": "no file"}
    p = (root / f.split(":", 1)[0]).resolve()
    if root not in p.parents:
        return {**res, "ok": False, "why": "file is outside the run folder"}
    if not p.is_file():
        return {**res, "ok": False, "why": "file not found"}
    nq = norm(text)
    found = []
    for v in views(p):
        variants = {nq, nq.replace(" | ", " ")}
        for qq in variants:
            found += v.starts(qq)
    if not found:
        return {**res, "ok": False, "why": "text not found in the file"}
    best = min(found, key=lambda n: abs(n - line))
    if abs(best - line) > window and not strict_lines and p.name == "transcript.md":
        near = [n for n in found if abs(block_start(p, n) - line) <= window]
        if near:
            return {**res, "ok": True, "found_line": near[0], "via": "message block start"}
    if abs(best - line) > window:
        return {**res, "ok": False, "why": f"found at line {best}, not within {window} lines of {line}",
                "found_line": best}
    return {**res, "ok": True, "found_line": best}


def check(root, window=3, strict_lines=False):
    root = Path(root).resolve()
    d = root / "DOSSIER.json"
    if not d.is_file():
        return None
    try:
        dossier = json.loads(d.read_text(), strict=False)   # raw tabs/newlines copied from code inside strings
    except ValueError as e:
        return {"pass": False, "quotes": 0, "failed": 0, "error": f"DOSSIER.json is not JSON: {e}", "results": []}
    results = []
    for where, q in quotes_in(dossier):
        r = check_one(root, q, window, strict_lines)
        r["at"] = where
        results.append(r)
    failed = [r for r in results if not r["ok"]]
    return {"pass": bool(results) and not failed, "quotes": len(results), "failed": len(failed),
            "error": None if results else "no quotes in the dossier", "results": results}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run_folder")
    ap.add_argument("--json")
    ap.add_argument("--window", type=int, default=3)
    ap.add_argument("--strict-lines", action="store_true")
    a = ap.parse_args()
    rep = check(a.run_folder, a.window, a.strict_lines)
    if rep is None:
        print(f"{a.run_folder}: no DOSSIER.json")
        sys.exit(2)
    if a.json:
        Path(a.json).write_text(json.dumps(rep, indent=1))
    print(f"quote check: {'PASS' if rep['pass'] else 'FAIL'} ({rep['quotes'] - rep['failed']}/{rep['quotes']} quotes ok)"
          + (f"; {rep['error']}" if rep.get("error") else ""))
    for r in rep["results"]:
        if not r["ok"]:
            print(f"  FAIL {r['at']}: {r['file']}:{r['line']} {r['why']}: {r['quote'][:100]!r}")
    sys.exit(0 if rep["pass"] else 1)


if __name__ == "__main__":
    main()
