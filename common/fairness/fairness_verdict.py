#!/usr/bin/env python3
"""fairness_verdict.py <slug> : the fairness verdict in build/<slug>/FAIRNESS.md, read strictly.
Prints `READY (<source>)`, `NOT_READY (<source>)` or `ERROR: <why>`; exit 0 / 1 / 2.

Only the verdict TOKEN of the review counts, never prose. Until 2026-10-20 the scripts grepped the
whole file for "not ready", so a READY review that wrote "(not a reason for NOT READY)" read as
NOT READY (litellm-ds, airflow-info-exposure-inj, summarize-ds), and a missing file or verdict read
as READY. Three review formats exist; the newest one present wins:
  gate_a    a `GATE_A: READY|NOT_READY` line (FAIRNESS-REVIEW-BRIEF.md step 5; last one counts)
  two-gate  the unfairness-gate line, e.g. `### a. UNFAIRNESS gate — **NOT READY**`, or that
            heading followed by a paragraph opening with `**READY.**`
  legacy    the single verdict of reviews before the two-gate split (2026-10-20): a `Verdict:`
            or `Status:` line (`## 5. Verdict: NOT READY`, `Status: READY.`), or a Verdict
            heading followed by a paragraph opening with the token. Such a NOT READY may be
            leniency, not unfairness (the 2026-10-19 audit); the source label says so.
A missing file, no verdict in any format, or a fairness run that did not finish
(build/<slug>/fairness_status.txt, written by pipelines/sibling/9-fairness/run_fairness.sh) is ERROR: a person decides.

Human decisions (2026-10-25): build/<slug>/HUMAN-DECISION.md holds a `DECISION: KEEP|REPAIR|DROP` line and a
`DATE: YYYY-MM-DD` line. It is the ONE place a person's answer to a fairness question is recorded (before this,
answers sat in HUMAN-REVIEW.md, NEEDS_HUMAN_REVIEW.md "User decision" sections or build/audit/
UNCOVERED-UPSTREAM-CLASS.md, which this reader never saw). KEEP reads as READY (it may overrule a NOT_READY the
person judged stale or wrong); REPAIR and DROP read as NOT_READY. A decision dated before the current FAIRNESS.md
was written is reported as stale and ignored. A review that sets `NEEDS_HUMAN_REVIEW: YES` with no current
decision is reported with "human question open".
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(next(p for p in Path(__file__).resolve().parents if (p / ".cwe-bench-root").is_file()) / "common"))
import paths  # noqa: E402  (repo locations: common/paths.py)
import markers  # noqa: E402  (common/markers.py)

ROOT = paths.ROOT
TOKEN = r"(NOT[ _-]?READY|READY)\b"
GATE_A = re.compile(r"(?mi)^[\s>*`_|-]*GATE_A[*`_]*\s*[:=]\s*[*`_]*\s*" + TOKEN)
# A labelled line: optional heading marks / list marks / a section number like "5." or "5a.".
LABEL = r"(?mi)^[#\s>*_|-]*(?:\d*[a-z]?[.)]\s*)?[*_]*(?:{})\b(.*)$"
UNFAIR = re.compile(LABEL.format(r"unfairness gate"))
VERDICT = re.compile(LABEL.format(r"verdict|status"))
SAME_LINE = re.compile(r"^[^\n]{0,40}?[:—–-]\s*[*`_]*\s*" + TOKEN, re.I)   # "Verdict: **READY**"
LEAD_TOKEN = re.compile(r"(?mi)^[\s>*`_]*" + TOKEN)                       # "**READY.** No live test..."
HEADING = re.compile(r"(?m)^#{1,6}\s")


def norm(tok):
    return "NOT_READY" if tok.upper().startswith("NOT") else "READY"


def labelled(text, label):
    """Verdict under the LAST line carrying `label` that has one: the token right after the label
    on that line, else the first token opening a line before the next heading."""
    for m in reversed(list(label.finditer(text))):
        same = SAME_LINE.search(m.group(1))
        if same:
            return norm(same.group(1))
        body = text[m.end():]
        nxt = HEADING.search(body)
        lead = LEAD_TOKEN.search(body[:nxt.start()] if nxt else body)
        if lead:
            return norm(lead.group(1))
    return None


DECISION = re.compile(r"(?mi)^\s*DECISION\s*:\s*(KEEP|REPAIR|DROP)\b")
DATE = re.compile(r"(?mi)^\s*DATE\s*:\s*(\d{4}-\d{2}-\d{2})")
NEEDS_HUMAN = re.compile(r"(?mi)^[\s>*`_|-]*NEEDS_HUMAN_REVIEW[*`_]*\s*[:=]\s*[*`_]*\s*YES")


def human_decision(slug):
    """(decision, date, stale) from build/<slug>/HUMAN-DECISION.md, or None (common/markers.py human_decision)."""
    return markers.human_decision(ROOT / "build" / slug)


def verdict(slug):
    b = ROOT / "build" / slug
    st = b / "fairness_status.txt"
    if st.is_file() and not st.read_text().startswith("ok"):
        return "ERROR", "last fairness run did not finish: " + st.read_text().strip()[:200]
    f = b / "FAIRNESS.md"
    if not f.is_file():
        return "ERROR", "no FAIRNESS.md"
    text = f.read_text(errors="replace")
    hits = GATE_A.findall(text)
    if hits:
        return norm(hits[-1]), "gate_a"
    v = labelled(text, UNFAIR)
    if v:
        return v, "two-gate"
    v = labelled(text, VERDICT)
    if v:
        return v, "legacy single verdict"
    return "ERROR", "FAIRNESS.md states no verdict in any known format"


def final(slug):
    """The review's verdict, then a current human decision on top of it."""
    v, why = verdict(slug)
    hd = human_decision(slug)
    if hd and not hd[2]:
        dec, date, _ = hd
        base = f"{v} ({why})" if v != "ERROR" else f"ERROR: {why}"
        return ("READY" if dec == "KEEP" else "NOT_READY"), f"human decision {dec} {date}; review said {base}"
    note = f"; stale human decision {hd[0]} {hd[1]} (older than FAIRNESS.md)" if hd else ""
    f = ROOT / "build" / slug / "FAIRNESS.md"
    if v != "ERROR" and f.is_file() and NEEDS_HUMAN.search(f.read_text(errors="replace")):
        note += "; human question open (NEEDS_HUMAN_REVIEW: YES, no decision in HUMAN-DECISION.md)"
    return v, why + note


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("usage: fairness_verdict.py <slug>")
    v, why = final(sys.argv[1])
    print(f"{v} ({why})" if v != "ERROR" else f"ERROR: {why}")
    sys.exit({"READY": 0, "NOT_READY": 1}.get(v, 2))
