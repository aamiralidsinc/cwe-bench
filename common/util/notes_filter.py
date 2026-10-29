#!/usr/bin/env python3
"""Build notes without earlier conclusions (client audit PO-3; owner 2026-10-28).

    python3 -I common/util/notes_filter.py <notes.md> <out.md>    writes the filtered copy, prints its stats (JSON)

Who reads the filtered copy: the post-run auditor (common/audit/postmortem.py copies it into the evidence) and the
fairness reviewer (pipelines/*/fairness: build/<slug>/notes.for-review.md). Both must judge on their own. The
repair (fairfix), upgrade and blind-fix agents keep the full notes.md: they need the history, or everything in view.

What goes: statements that report a CONCLUSION about runs or tests:
  - audit verdicts and audit notes, postmortems, "earlier runs audited fair";
  - the fairness review's outcome (FAIRNESS.md, GATE_A, READY / NOT READY, NEEDS_HUMAN_REVIEW);
  - owner, user and client decisions (DECISION, KEEP / DROP / REPAIR / WITHDRAW, CLIENT-AUDIT, "user-approved");
  - outcomes of runs, regrades and rescores (a model's run named or counted, "r12 scored 1.0").
What stays: everything that says how the task is built. That includes original and planted sites, traps and levers,
the test-to-site mapping, the environment and build steps, the trial-environment set-up, gate results, and the
builder's own design notes.

How (by what a section says, not by loose words; "trust decision" or "test results" are product or build words):
  - a section whose subject is a conclusion goes whole, with its subsections. That covers a regrade or rescore,
    an audit finding on a run, a postmortem, a client audit, a human review, an owner or user decision, and trial
    results;
  - a change-log section (test repair, fairness revision, fairfix, upgrade, "items and decisions") stays, because
    it says what the tests and checks are now; only its conclusion statements go, and there "unfair", "lenient",
    "flagged" and run notes count as conclusions too;
  - everywhere else only the statements matching the conclusion patterns go, sentence by sentence in prose and
    bullets, row by row in tables; code blocks are kept as they are.
"""
import json
import re
import sys

HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
FENCE_RE = re.compile(r"^\s*(```|~~~)")
BULLET_RE = re.compile(r"^(\s*(?:[-*+]|\d+[.)])\s+)(.*)$")
SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z*`(\[\"'_])")

# Sections whose subject is a conclusion: dropped whole.
CONCLUSION_SECTION = re.compile(
    r"(?i)\bre-?grad|\brescor|\bpost-?mortem|\bpost-run audit|\baudit (?:findings?|verdicts?|results?|notes?)\b|"
    r"\baudit\b[^\n]*\b(?:deepseek|mimo|ds)\b|\bclient audit\b|\bhuman review\b|"
    r"\b(?:owner|user)(?:'s)? (?:decision|ruling)s?\b|\bdecision for the (?:user|owner)\b|"
    r"\btrial (?:results?|outcomes?|summary)\b|\bresults? of the (?:trials?|runs?)\b|\bwho solved\b")
# Change-log sections: kept, with a stricter statement filter.
CHANGE_LOG_SECTION = re.compile(r"(?i)\btest repair|\brepair\b|\bfairness revision|\bfairfix|\bupgrade\b|"
                                r"\bitems and decisions\b|\brevision\b")

SQL_AFTER = r"(?!\s+(?:TABLE|INDEX|VIEW|DATABASE|COLUMN|SCHEMA|USER|ROLE|TRIGGER|FUNCTION|PROCEDURE|IF)\b)"
CONCLUSION = [
    # pipeline verdict artifacts
    re.compile(r"GATE_A|NEEDS_HUMAN_REVIEW|CONFLICTS-RULED|CLIENT-AUDIT|HUMAN-DECISION|\bDECISION\s*:|"
               r"verdict\.json|POSTMORTEM|postmortem-\d|ledger\.md|\btrustworthy\b"),
    # the review's file is named in build facts too ("static: only the missing FAIRNESS.md"); only its findings go
    re.compile(r"FAIRNESS\.md`?[^.\n]{0,40}\b(?:said|says|flagged|asked|rated|found|verdict|unfair|lenient|"
               r"NOT[ _]READY|READY)\b|\b(?:said|says|flagged|asked|rated|found)\b[^.\n]{0,40}FAIRNESS\.md"),
    # audits
    re.compile(r"(?i)\bpost-?run audit|\bpost-?mortem\b|\b(?:re-?)?audited\b|"
               r"\baudit(?:or)?s?\b[^.\n]{0,40}\b(?:said|says|found|judged|noted|flagged|rated|called|marked|"
               r"verdicts?|findings?|notes?|recs?|recommend\w*)\b"),
    # runs and their outcomes
    re.compile(r"(?i)\b(?:deepseek|mimo|ds)[ -]?r\d+\b|\b(?:deepseek|mimo)-r\d+-n\d+|"
               r"\b(?:deepseek|mimo|ds|both models?)\b[^.\n]{0,40}\b\d+/\d+\b|"
               r"\br\d+\b[^.\n]{0,30}\b(?:scored|reward|solv\w*|fail\w*)\b|\bre-?grad\w*|\brescor\w*|"
               r"\bboth-model breaker|\bBREAKER\b|\bbreaker (?:candidate|verdict|status)\b|"
               r"\b(?:solved|failed) (?:\d+/\d+|by (?:deepseek|mimo|both))"),
    # owner, user and client decisions
    re.compile(r"(?i)\b(?:owner|user|client)(?:'s)?[- ](?:decision|decided|ruled|ruling|approved|chose|kept|"
               r"dropped|asked|confirmed)\b|\b(?:user|owner)-approved\b"),
    re.compile(r"\b(?:KEEP|DROP|REPAIR|WITHDRAW)\b" + SQL_AFTER),
    # the fairness review's outcome
    re.compile(r"\b(?:NOT[ _-]?READY|READY)\b|(?i:\bfairness (?:review|reviewer|verdict|gate)\b[^.\n]{0,40}"
               r"\b(?:said|says|found|flagged|asked|rated|marked|unfair|fair)\b)"),
]
CHANGE_LOG_EXTRA = re.compile(r"(?i)\b(?:un)?fair\b|\blenient\b|\bleniency\b|\bflagged\b|\brecs?\b|\bjudged\b|"
                              r"\bruled\b|\bverdict\b|\bnot applied\b")


def concluding(text, strict=False):
    return any(p.search(text) for p in CONCLUSION) or bool(strict and CHANGE_LOG_EXTRA.search(text))


def scrub(text, strict=False):
    """The statement without its concluding parentheticals ('(REC mimo-r1-n001)', '(deepseek r11, mimo r11)'), or
    None when what remains still concludes something."""
    out = re.sub(r"\s*\([^()]*\)", lambda m: "" if concluding(m.group(0), strict) else m.group(0), text)
    return None if concluding(out, strict) else out


def _filter_block(lines, strict, removed):
    """A bullet or paragraph: kept as it is, or with its concluding sentences dropped (re-joined on one line)."""
    text = " ".join(x.strip() for x in lines)
    if not concluding(text, strict):
        return lines
    m = BULLET_RE.match(lines[0])
    prefix, body = (m.group(1), " ".join([m.group(2)] + [x.strip() for x in lines[1:]])) if m \
        else (re.match(r"^\s*", lines[0]).group(0), text)
    kept = []
    for s in SENTENCE_SPLIT.split(body):
        t = scrub(s, strict)
        if t is None:
            removed.append(s)
        else:
            kept.append(t)
            if t != s:
                removed.append(s)
    return [prefix + " ".join(kept)] if kept and re.search(r"\w", " ".join(kept)) else []


def strip_conclusions(text):
    """(filtered text, [headings of sections dropped whole], lines removed, [removed statements])."""
    out, dropped, removed = [], [], []
    stack = []                      # [(level, kind)] kind: drop | log | keep
    block, fence = [], False
    n_in = len(text.splitlines())

    def kind():
        return stack[-1][1] if stack else "keep"

    def flush():
        nonlocal block
        if block:
            out.extend(_filter_block(block, kind() == "log", removed))
        block = []

    for line in text.splitlines():
        h = HEADING_RE.match(line) if not fence else None
        if h:
            flush()
            level, title = len(h.group(1)), h.group(2)
            while stack and stack[-1][0] >= level:
                stack.pop()
            parent = kind()
            if parent == "drop":
                stack.append((level, "drop"))
                continue
            if level >= 2 and CONCLUSION_SECTION.search(title):
                stack.append((level, "drop"))
                dropped.append(title.strip())
                continue
            k = "log" if parent == "log" or (level >= 2 and CHANGE_LOG_SECTION.search(title)) else "keep"
            stack.append((level, k))
            title2 = re.sub(r"\s*\([^()]*\)", lambda m: "" if concluding(m.group(0)) else m.group(0), title)
            out.append(h.group(1) + " " + title2)
            continue
        if kind() == "drop":
            continue
        if FENCE_RE.match(line):
            flush()
            fence = not fence
            out.append(line)
            continue
        if fence:
            out.append(line)
            continue
        if not line.strip():
            flush()
            out.append(line)
            continue
        if line.lstrip().startswith("|"):                       # a table row: kept or dropped whole
            flush()
            t = line if not concluding(line, kind() == "log") else scrub(line, kind() == "log")
            if t is None:
                removed.append(line.strip())
            else:
                out.append(t)
                if t != line:
                    removed.append(line.strip())
            continue
        if BULLET_RE.match(line) and block:
            flush()
        block.append(line)
    flush()
    res = "\n".join(re.sub(r"\n{3,}", "\n\n", "\n".join(out)).splitlines())
    res += "\n" if text.endswith("\n") else ""
    return res, dropped, max(0, n_in - len(res.splitlines())), removed


def main(argv):
    if len(argv) != 3:
        sys.exit("usage: notes_filter.py <notes.md> <out.md>")
    try:
        text = open(argv[1], errors="replace").read()
    except OSError:
        text = ""
    res, dropped, n, removed = strip_conclusions(text)
    with open(argv[2], "w") as f:
        f.write(res)
    print(json.dumps({"in": argv[1], "out": argv[2], "lines_in": len(text.splitlines()),
                      "lines_out": len(res.splitlines()), "sections_left_out": dropped,
                      "statements_left_out": len(removed)}))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
