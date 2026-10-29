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

Conflicts (client audit PO-3, 2026-10-28): a review written with the conflict check carries a
`CONFLICTS: <n>; DECIDING: <m>` line (FAIRNESS-REVIEW-BRIEF.md step 1a): n tests disagree with an
instruction sentence or pin one implementation (or are out of scope / unreachable), m of them decided a run
(`DECIDING: unknown`, or no DECIDING part, counts all n as deciding). Owner rule: if a test and the instruction
disagree, the failure is unfair. So a READY review with a deciding conflict and no current human decision reads
as NOT_READY here, and neither an automatic KEEP (`--auto-keep`) nor a delivery (`--delivery`) goes ahead. Only an
explicit `CONFLICTS-RULED: <YYYY-MM-DD> <KEEP|DROP|REPAIR> <short reason>` line in HUMAN-DECISION.md, dated on or
after the review, rules on deciding conflicts (owner 2026-10-28); a KEEP decision alone does not. Delivery also needs
a recorded DECISION (KEEP) and refuses a task whose NEWEST client-audit outcome is not a KEEP (`CLIENT-AUDIT:
WITHDRAW`, `REPAIR FIRST`, `WAITING`; `KEEP (confirmed)` / `KEEP, CONFIDENCE: ...` pass, and a later KEEP section
clears an earlier one).

Proven conflicts (owner 2026-10-28): an `other_reading` check (a fix that follows the other sentence of a flagged
conflict, written in the repair step) that FAILS a named test is recorded by the gate in build/<slug>/gate_report.json
(stages.patches.conflict_proven). Such a test blocks an automatic KEEP and the delivery until a later test repair
(a repaired-tests-* / removed-tests-* folder newer than that gate report; the re-gate then reports afresh). A
CONFLICTS-RULED line does not clear a proven conflict.

    fairness_verdict.py <slug>               the verdict (exit 0 READY / 1 NOT_READY / 2 ERROR)
    fairness_verdict.py --auto-keep <slug>   may the standing owner rule write KEEP? exit 0 yes / 1 no (reasons)
    fairness_verdict.py --delivery <slug>    may the task be delivered? exit 0 yes / 1 no (reasons)
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
# `CONFLICTS: 2; DECIDING: 1` (also `CONFLICTS: 0`, `CONFLICTS: 3 (deciding: unknown)`); the last such line counts.
CONFLICTS = re.compile(r"(?mi)^[\s>*`_|-]*CONFLICTS[*`_]*\s*[:=]\s*[*`_]*\s*(\d+)\b([^\n]*)$")
DECIDING = re.compile(r"(?i)DECIDING[*`_]*\s*[:=]?\s*[*`_]*\s*(\d+|unknown)")


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


def _review_text(slug):
    f = ROOT / "build" / slug / "FAIRNESS.md"
    return f.read_text(errors="replace") if f.is_file() else ""


def conflicts(slug):
    """(n, deciding) from the review's last CONFLICTS line, or None when the review has none (written before the
    conflict check of 2026-10-28). A missing or `unknown` DECIDING part counts every conflict as deciding."""
    hits = CONFLICTS.findall(_review_text(slug))
    if not hits:
        return None
    n, rest = int(hits[-1][0]), hits[-1][1]
    m = DECIDING.search(rest)
    deciding = n if not m or m.group(1).lower() == "unknown" else min(n, int(m.group(1)))
    return n, deciding


def question_open(slug):
    """True when FAIRNESS.md sets NEEDS_HUMAN_REVIEW: YES and HUMAN-DECISION.md has no current decision."""
    hd = human_decision(slug)
    return bool(NEEDS_HUMAN.search(_review_text(slug))) and not (hd and not hd[2])


def final(slug):
    """The review's verdict, then a current human decision on top of it."""
    v, why = verdict(slug)
    hd = human_decision(slug)
    if hd and not hd[2]:
        dec, date, _ = hd
        base = f"{v} ({why})" if v != "ERROR" else f"ERROR: {why}"
        c = conflicts(slug) if v != "ERROR" else None
        r = conflicts_ruled(slug)
        if c and c[1] > 0 and not (r and not r[3]):
            base += f"; {c[1]} deciding conflict(s) without a current CONFLICTS-RULED line (delivery refused)"
        if conflicts_proven(slug):
            base += f"; {len(conflicts_proven(slug))} test(s) CONFLICT-PROVEN by the gate (delivery refused)"
        return ("READY" if dec == "KEEP" else "NOT_READY"), f"human decision {dec} {date}; review said {base}"
    note = f"; stale human decision {hd[0]} {hd[1]} (older than FAIRNESS.md)" if hd else ""
    if v != "ERROR" and question_open(slug):
        note += "; human question open (NEEDS_HUMAN_REVIEW: YES, no decision in HUMAN-DECISION.md)"
    c = conflicts(slug) if v != "ERROR" else None
    if c and c[1] > 0:
        note += f"; {c[1]} deciding test(s) conflict with the instruction (CONFLICTS: {c[0]}, deciding {c[1]})"
        if v == "READY":           # owner rule 2026-10-28: a test that disagrees with the instruction is unfair
            return "NOT_READY", why + note + "; a READY review cannot stand with a deciding conflict"
    elif c and c[0] > 0:
        note += f"; {c[0]} conflicting test(s) decided no run (test-only repair before delivery)"
    pr = conflicts_proven(slug)
    if pr:
        note += f"; {len(pr)} test(s) CONFLICT-PROVEN by the gate's other_reading check (repair before delivery)"
    return v, why + note


def auto_keep_blockers(slug):
    """Why the standing owner rule (READY + NEEDS_HUMAN_REVIEW: NO -> KEEP) must not write KEEP; [] = it may."""
    v, why = verdict(slug)
    out = []
    if v != "READY":
        out.append(f"review verdict {v} ({why})")
    if NEEDS_HUMAN.search(_review_text(slug)):
        out.append("NEEDS_HUMAN_REVIEW: YES (a person rules)")
    c = conflicts(slug)
    if c is None and v != "ERROR":
        out.append("no CONFLICTS line (review predates the conflict check): re-run the review or a person decides")
    elif c and c[0] > 0:
        out.append(f"CONFLICTS: {c[0]} (deciding {c[1]}): repair the tests or a person decides")
    pr = conflicts_proven(slug)
    if pr:
        out.append(f"{len(pr)} test(s) CONFLICT-PROVEN by the gate: repair the tests")
    return out


def conflicts_proven(slug):
    """[test] the last gate proved to conflict with the instruction (other_reading checks), or [] when none, or when
    a test repair (repaired-tests-* / removed-tests-*) is newer than that gate report (the re-gate decides then)."""
    b = ROOT / "build" / slug
    rep = b / "gate_report.json"
    try:
        import json
        proven = (json.loads(rep.read_text()).get("stages", {}).get("patches") or {}).get("conflict_proven") or []
    except (OSError, ValueError, AttributeError):
        return []
    if not proven:
        return []
    t = rep.stat().st_mtime
    if any((b / r).stat().st_mtime > t for r in markers.repairs(b)):
        return []
    return [str(x.get("test")) for x in proven if isinstance(x, dict)]


def conflicts_ruled(slug):
    """(ruling, date, reason, stale) from the last `CONFLICTS-RULED:` line of HUMAN-DECISION.md, or None."""
    return markers.conflicts_ruled(ROOT / "build" / slug)


def delivery_blockers(slug):
    """Why build/<slug>/ must not be delivered; [] = no objection. A `<slug>-control` task (stacking) is judged by its
    stacked task's files. Rules (client audit PO-3, owner 2026-10-28):
      - HUMAN-DECISION.md must record a DECISION, and it must be KEEP (a clean READY review is not enough);
      - the newest `CLIENT-AUDIT:` line must be a KEEP (WITHDRAW, REPAIR FIRST, WAITING refuse; a later KEEP clears);
      - an open human question (NEEDS_HUMAN_REVIEW: YES), no finished review, or a NOT_READY review needs a KEEP
        dated on or after the day FAIRNESS.md was last written (a stale KEEP does not count);
      - a deciding conflict (CONFLICTS line) needs its own ruling, `CONFLICTS-RULED: <date> KEEP <reason>`, dated on
        or after the review: a KEEP decision alone does not rule on it, and a DROP or REPAIR ruling refuses."""
    s = slug[: -len("-control")] if slug.endswith("-control") and (ROOT / "build" / slug[: -len("-control")]).is_dir() \
        else slug
    v, why = verdict(s)
    hd = human_decision(s)
    tag = f"{s}: " if s != slug else ""
    out = []
    if not hd:
        out.append(f"{tag}no DECISION recorded in HUMAN-DECISION.md (delivery needs the owner's KEEP)")
    elif hd[0] != "KEEP":
        out.append(f"{tag}owner decision is {hd[0]} {hd[1]}" + (" (stale)" if hd[2] else "") + ", not KEEP")
    audits = markers.client_audit(ROOT / "build" / s)
    if audits and not re.match(r"(?i)KEEP\b", audits[-1]):      # the newest client-audit outcome decides
        value = audits[-1]
        word = "withdrawn by" if value.upper().startswith("WITHDRAW") else "not kept by"
        out.append(f"{tag}{word} a client audit (CLIENT-AUDIT: {value}); only a KEEP outcome is delivered")
    pr = conflicts_proven(s)
    if pr:
        out.append(f"{tag}{len(pr)} test(s) proven to conflict with the instruction by an other_reading check "
                   f"(gate_report.json) and not repaired since: {', '.join(pr)[:300]}")
    current = bool(hd and not hd[2] and hd[0] == "KEEP")
    stale = f" (the KEEP of {hd[1]} is older than FAIRNESS.md: stale)" if hd and hd[2] and hd[0] == "KEEP" else ""
    if hd and hd[0] == "KEEP" and not current:
        if v == "ERROR":
            out.append(f"{tag}no finished fairness review ({why}) and no current KEEP{stale}")
        elif v == "NOT_READY":
            out.append(f"{tag}fairness review is NOT_READY ({why}) and no current KEEP{stale}")
        if v != "ERROR" and NEEDS_HUMAN.search(_review_text(s)):
            out.append(f"{tag}open human question: FAIRNESS.md sets NEEDS_HUMAN_REVIEW: YES and HUMAN-DECISION.md "
                       f"records no ruling dated on or after the review{stale}")
    c = conflicts(s) if v != "ERROR" else None
    if c and c[1] > 0:
        r = conflicts_ruled(s)
        what = f"{c[1]} deciding test(s) conflict with the instruction (CONFLICTS: {c[0]})"
        if r is None:
            out.append(f"{tag}{what} and HUMAN-DECISION.md has no `CONFLICTS-RULED: <date> <KEEP|DROP|REPAIR> "
                       f"<reason>` line (a KEEP decision alone does not rule on them)")
        elif r[3]:
            out.append(f"{tag}{what}; the ruling CONFLICTS-RULED {r[1]} {r[0]} is older than FAIRNESS.md (stale)")
        elif r[0] != "KEEP":
            out.append(f"{tag}{what}; ruled {r[0]} on {r[1]}: {r[2]}")
    return out


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] in ("--auto-keep", "--delivery"):
        reasons = (auto_keep_blockers if sys.argv[1] == "--auto-keep" else delivery_blockers)(sys.argv[2])
        word = "AUTO-KEEP" if sys.argv[1] == "--auto-keep" else "DELIVERY"
        print(f"{word} OK" if not reasons else f"{word} REFUSED: " + "; ".join(reasons))
        sys.exit(1 if reasons else 0)
    if len(sys.argv) != 2:
        sys.exit("usage: fairness_verdict.py [--auto-keep | --delivery] <slug>")
    v, why = final(sys.argv[1])
    print(f"{v} ({why})" if v != "ERROR" else f"ERROR: {why}")
    sys.exit({"READY": 0, "NOT_READY": 1}.get(v, 2))
