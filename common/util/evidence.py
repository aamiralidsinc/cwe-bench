#!/usr/bin/env python3
"""Full error evidence for root-cause analysis.

Every pipeline error record carries the error's class, its FULL message, its FULL traceback or
stack, every failing test's complete output, the raw process output, and the paths of the raw
artifacts. All of it goes to an evidence file (JSON + a readable .txt beside it); logs and reports
carry a one-line summary plus that file's path. Until 2026-10-21 several paths kept only the class
(trial.py: cause="exception:<Type>") or 160-600 characters, and Harbor's exception_traceback was
dropped everywhere, which made root-cause analysis impossible.

    python3 common/util/evidence.py <trial_dir>      # print the full evidence of one trial
"""
import json
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path

STDOUT_TAIL = 200_000      # characters of verifier stdout kept in an evidence file
PROC_TAIL = 200_000        # characters of a process's stdout / stderr kept


def read(path, tail=None):
    try:
        text = Path(path).read_text(errors="replace")
    except OSError:
        return None
    return text[-tail:] if tail and len(text) > tail else text


def one_line(text, n=300):
    """A single-line summary for logs; the full text lives in the evidence file."""
    s = " ".join(str(text or "").split())
    return s if len(s) <= n else s[: n - 3] + "..."


def harbor_exception(trial_dir):
    """Harbor's exception record for a trial, complete: type, message, traceback, time."""
    try:
        res = json.loads(Path(trial_dir, "result.json").read_text())
    except (OSError, ValueError) as e:
        return {"type": "UnreadableResultJson", "message": f"{type(e).__name__}: {e}", "traceback": None}
    exc = res.get("exception_info") or {}
    if not exc:
        return None
    return {"type": exc.get("exception_type"), "message": exc.get("exception_message"),
            "traceback": exc.get("exception_traceback"), "occurred_at": exc.get("occurred_at")}


def junit_failures(trial_dir):
    """Every failing or erroring test case in the trial's JUnit XML, with its complete output."""
    out = []
    for xml in sorted(Path(trial_dir, "verifier").rglob("*.xml")):
        try:
            root = ET.parse(xml).getroot()
        except (ET.ParseError, OSError) as e:
            out.append({"file": str(xml), "parse_error": f"{type(e).__name__}: {e}"})
            continue
        for case in root.iter("testcase"):
            bad = [b for b in case if b.tag in ("failure", "error")]
            if not bad:
                continue
            rec = {"file": str(xml), "classname": case.get("classname"), "name": case.get("name"),
                   "problems": [{"kind": b.tag, "type": b.get("type"), "message": b.get("message"),
                                 "text": b.text} for b in bad]}
            for tag in ("system-out", "system-err"):
                el = case.find(tag)
                if el is not None and (el.text or "").strip():
                    rec[tag] = el.text
            out.append(rec)
    return out


def collect(trial_dir, proc=None):
    """Everything known about one Harbor trial (and the process that ran it, if given)."""
    t = Path(trial_dir) if trial_dir else None
    rec = {"trial_dir": str(t) if t else None}
    if t and t.is_dir():
        rec["exception"] = harbor_exception(t)
        rec["failing_tests"] = junit_failures(t)
        rec["verifier_stdout_tail"] = read(t / "verifier" / "test-stdout.txt", STDOUT_TAIL)
        rec["trial_log_tail"] = read(t / "trial.log", 50_000)
        rec["artifacts"] = {k: str(t / p) for k, p in [
            ("result_json", "result.json"), ("verifier_dir", "verifier"),
            ("agent_log", "agent/claude-code.txt"), ("trial_log", "trial.log")] if (t / p).exists()}
    if proc is not None:
        rec["process"] = {"args": getattr(proc, "args", None), "returncode": proc.returncode,
                          "stdout_tail": (proc.stdout or "")[-PROC_TAIL:],
                          "stderr_tail": (proc.stderr or "")[-PROC_TAIL:]}
    return rec


def render(record):
    """Readable text form of an evidence record: summary first, then each full section."""
    lines = [f"WHAT: {record.get('what')}", f"KIND: {record.get('kind')}", f"WHEN: {record.get('utc')}",
             "", "SUMMARY", "-------", str(record.get("summary") or ""), ""]
    d = record.get("details") or {}
    exc = d.get("exception")
    if exc:
        lines += ["EXCEPTION", "---------", f"type: {exc.get('type')}", f"occurred_at: {exc.get('occurred_at')}",
                  "message:", str(exc.get("message")), "traceback:", str(exc.get("traceback")), ""]
    for i, ft in enumerate(d.get("failing_tests") or [], 1):
        lines += [f"FAILING TEST {i}: {ft.get('classname')} :: {ft.get('name')}", f"  file: {ft.get('file')}"]
        for p in ft.get("problems") or []:
            lines += [f"  {p.get('kind')} type={p.get('type')}", f"  message: {p.get('message')}", str(p.get("text") or "")]
        for tag in ("system-out", "system-err"):
            if ft.get(tag):
                lines += [f"  {tag}:", ft[tag]]
        lines.append("")
    for key in ("traceback", "agent_result", "stderr_tail"):
        if d.get(key):
            lines += [key.upper(), "-" * len(key), str(d[key]), ""]
    p = d.get("process")
    if p:
        lines += ["PROCESS", "-------", f"args: {p.get('args')}", f"returncode: {p.get('returncode')}",
                  "stdout (tail):", str(p.get("stdout_tail")), "stderr (tail):", str(p.get("stderr_tail")), ""]
    if d.get("verifier_stdout_tail"):
        lines += ["VERIFIER STDOUT (tail)", "----------------------", d["verifier_stdout_tail"], ""]
    if d.get("trial_log_tail"):
        lines += ["TRIAL LOG (tail)", "----------------", d["trial_log_tail"], ""]
    rest = {k: v for k, v in d.items() if k not in (
        "exception", "failing_tests", "traceback", "agent_result", "stderr_tail", "process",
        "verifier_stdout_tail", "trial_log_tail")}
    if rest:
        lines += ["OTHER DETAILS", "-------------", json.dumps(rest, indent=1, default=str)]
    return "\n".join(lines)


def write(directory, name, what, kind, summary, details):
    """Write <directory>/<UTC>-<name>.json and .txt; return the .txt path (the one to read)."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    utc = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    safe = "".join(c if c.isalnum() or c in "-_." else "-" for c in name)[:120]
    base = directory / f"{utc}-{safe}"
    record = {"what": what, "kind": kind, "utc": utc, "summary": summary, "details": details}
    base.with_suffix(".json").write_text(json.dumps(record, indent=1, default=str))
    base.with_suffix(".txt").write_text(render(record))
    return str(base.with_suffix(".txt"))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("usage: evidence.py <trial_dir>")
    rec = {"what": f"trial {sys.argv[1]}", "kind": "inspection", "utc": "-", "summary": "",
           "details": collect(sys.argv[1])}
    print(render(rec))
