#!/usr/bin/env python3
"""Independent post-run audit: before a graded run may count toward any verdict, an auditor
(a sub-agent on Claude Opus 5.5 at high effort, started from the main session each time a
result comes back, or the main session itself) judges whether its result can be trusted.

    python3 common/audit/postmortem.py prepare <trial_dir>   # evidence folder + AUDITOR_BRIEF.md; prints its path
    python3 common/audit/postmortem.py record <postmortem_dir> [--auditor "..."]
                                                    # validates <dir>/verdict.json, writes POSTMORTEM.json/.md
    python3 common/audit/postmortem.py record-ready          # record every folder whose auditor has finished
    python3 common/audit/postmortem.py pending               # graded runs without a current audit

Why (2026-10-16): two of three reported per-model failures turned out to be faults in our own
tests (docs/research/own-runs/FINDINGS.md). No result is final until an independent auditor has
read the instruction, the tests, the grading output, the model's final code and its transcript.

What the auditor gets (copied into <trial>/postmortem-<UTC>/evidence/, read-only tools only):
    instruction.md, task.toml, tests/, solution/fix.patch, build notes (BRIEF.md / notes.md)
    the grading the audit uses (original verifier/ or the newest regrade-*/): results.json,
        reward.json, the tail of test-stdout.txt, REGRADE.json
    final-code/changes.patch and changed_files.tsv (when harvested)
    transcript.md: a digest of the agent's transcript (tool calls, short results, all of the
        agent's text); the full transcript path is given too
    run.json: the audit row (reward, timeouts, minutes, flags) and Harbor's exception info
The auditor works only from that folder (read-only), writes <dir>/verdict.json matching SCHEMA,
and the main session then runs `record`.

Output: <trial>/postmortem-<UTC>/POSTMORTEM.json (structured verdict, see SCHEMA) and
POSTMORTEM.md, plus the raw CLI output. audit_results.py counts a graded run only when its
newest postmortem audited the grading now in use and says trustworthy=true.
"""
import argparse
import csv
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(next(p for p in Path(__file__).resolve().parents if (p / ".cwe-bench-root").is_file()) / "common"))
import paths  # noqa: E402  (repo locations: common/paths.py)

ROOT = paths.ROOT
JOBS = Path.home() / ".tb-graders" / "cwe" / "jobs"
AUDITOR = "sub-agent, Claude Opus 5.5, effort high"
sys.path.insert(0, str(Path(__file__).resolve().parent))

SCHEMA = {
    "type": "object",
    "required": ["trustworthy", "attribution", "confidence", "summary", "items", "evidence",
                 "recommended_action"],
    "properties": {
        "trustworthy": {"type": "boolean",
                        "description": "true only if the reward reflects the model's work under a fair grader"},
        "attribution": {"type": "string", "enum": [
            "model-solved", "model-failed", "test-fault", "instruction-ambiguity",
            "harness-or-infra", "contaminated", "unclear"]},
        "confidence": {"type": "string", "enum": ["high", "medium", "low"]},
        "summary": {"type": "string"},
        "items": {"type": "array", "items": {
            "type": "object",
            "required": ["test", "outcome", "model_behaviour", "stated_in_instruction",
                         "correct_fix_would_pass", "verdict"],
            "properties": {
                "test": {"type": "string"},
                "outcome": {"type": "string", "enum": ["pass", "fail"]},
                "model_behaviour": {"type": "string"},
                "stated_in_instruction": {"type": "boolean"},
                "correct_fix_would_pass": {"type": "boolean"},
                "verdict": {"type": "string", "enum": [
                    "genuine-pass", "genuine-fail", "test-fault", "instruction-ambiguity",
                    "harness-or-infra", "lenient-test", "unclear"]},
            }}},
        "lookup_or_leak": {"type": "string",
                           "description": "did the run copy an upstream fix or read hidden tests? how"},
        "evidence": {"type": "array", "items": {"type": "string"}},
        "recommended_action": {"type": "string"},
    },
}

BRIEF = """You are an independent auditor for a security-fix benchmark. A coding agent (model:
{model}) was given the task in evidence/instruction.md inside a container with the vulnerable
repository, worked for {minutes} minutes, and was then graded by hidden tests (evidence/tests/).
The grader produced reward {reward} (1.0 = every security and functional test passed).

Your job: decide whether this reward can be TRUSTED as a measure of the model's work. Results
are reported to people who will act on them; a wrong verdict in either direction is costly.

Check, at least:
1. Every FAILING test: what did the model actually do for that item (evidence/final-code/changes.patch,
   evidence/transcript.md)? Did the test demand something the instruction never states (an exact
   status code, a constant, a specific layer, a specific config knob)? Would a reasonable correct
   fix pass it? Did the test crash on its own (e.g. it calls product code the fix hardened)?
2. Every PASSING test that matters: is the pass real, or is the test too lenient?
3. Harness/infra: grader setup errors, timeouts, crashes, provider refusals, missing results
   (evidence/grading/test-stdout.tail.txt, evidence/run.json). On a timeout the agent may have kept
   running: evidence/run.json "timing" lists its tool calls INSIDE the grading window. Only those can
   change what was graded; edits after the window ended cannot. Judge the code as it was at grading.
   evidence/tests is the task's current version, which may be newer than the graded one.
   evidence/netguard.log (if present) lists every request to a code host or package registry and
   whether the trial's repository block refused it; a route around the block is contamination.
4. Contamination: did the agent read or run the hidden tests? Did it copy the upstream fix from
   the internet? (Copying upstream is allowed and does not make a solve untrustworthy; reading the
   hidden tests does.)
5. Is the reference fix (evidence/solution/fix.patch) consistent with the instruction and tests?

Attribution: model-solved / model-failed (a fair grader, the model's own shortfall) / test-fault /
instruction-ambiguity / harness-or-infra / contaminated / unclear. trustworthy=true only for
model-solved or model-failed with at least medium confidence. Cite evidence as file:line or short
quotes. Judge ONLY from the files under this folder (and the full transcript path in
evidence/run.json if you need more); do not rely on any earlier conclusions about this task or
benchmark you may have seen elsewhere. Do not run code and do not modify anything except the
one output file.

Write your answer as JSON to {out}/verdict.json, matching the schema in {out}/verdict.schema.json
(keys: trustworthy, attribution, confidence, summary, items[], lookup_or_leak, evidence[],
recommended_action). One item per test that failed, plus any passing test you judge lenient."""


def jload(p):
    try:
        return json.loads(Path(p).read_text())
    except (OSError, ValueError):
        return None


def grading_dir(trial):
    regs = sorted(p for p in trial.glob("regrade-*") if (p / "verifier").is_dir())
    return (regs[-1], regs[-1].name) if regs else (trial, "original")


def digest_transcript(path, limit=180_000):
    """Tool calls with short inputs/results and all agent text, as markdown."""
    out = []
    if not path.exists():
        return "(no transcript)"
    for line in open(path, errors="replace"):
        try:
            ev = json.loads(line)
        except ValueError:
            continue
        msg = ev.get("message") if isinstance(ev, dict) else None
        if not isinstance(msg, dict):
            continue
        for c in msg.get("content") or []:
            if not isinstance(c, dict):
                continue
            if c.get("type") == "text" and ev.get("type") == "assistant":
                out.append("AGENT: " + c.get("text", "").strip())
            elif c.get("type") == "tool_use":
                out.append(f"CALL {c.get('name')}: " + json.dumps(c.get("input"), ensure_ascii=False)[:400])
            elif c.get("type") == "tool_result":
                cont = c.get("content")
                txt = cont if isinstance(cont, str) else " ".join(
                    x.get("text", "") for x in (cont or []) if isinstance(x, dict))
                out.append("RESULT: " + txt.strip()[:400].replace("\n", " | "))
    text = "\n".join(out)
    if len(text) > limit:
        text = text[: limit // 2] + "\n\n[... middle of transcript omitted ...]\n\n" + text[-limit // 2:]
    return text


def timing(trial, res):
    """Agent activity after Harbor's recorded agent end, and tool calls inside the grading
    window (Harbor did not kill the in-container agent on timeout before 2026-10-16)."""
    ag = ((res.get("agent_execution") or {}).get("finished_at") or "")[:23]
    vf = res.get("verifier") or {}
    vs, ve = (vf.get("started_at") or "")[:23], (vf.get("finished_at") or "")[:23]
    after, during = 0, []
    p = trial / "agent" / "claude-code.txt"
    if ag and p.exists():
        for line in open(p, errors="replace"):
            try:
                ev = json.loads(line)
            except ValueError:
                continue
            ts = (ev.get("timestamp") or "")[:23] if isinstance(ev, dict) else ""
            if not ts or ts <= ag:
                continue
            after += 1
            msg = ev.get("message") or {}
            for c in (msg.get("content") or []) if isinstance(msg, dict) else []:
                if isinstance(c, dict) and c.get("type") == "tool_use" and vs and vs <= ts <= ve:
                    inp = c.get("input") or {}
                    during.append(f"{ts} {c.get('name')} {str(inp.get('file_path') or inp.get('command') or '')[:100]}")
    return {"agent_end": ag, "grading_window": [vs, ve], "agent_events_after_end": after,
            "tool_calls_during_grading": during}


def audit_row(trial):
    """The run's row in build/audit/trials.tsv, or (for a run newer than the table) the same key
    facts read from its own result.json."""
    rows = [r for r in csv.DictReader(open(ROOT / "build/audit/trials.tsv"), delimiter="\t")
            if r["trial"] == trial.name]
    if rows:
        return rows[0]
    res = jload(trial / "result.json") or {}
    rew = ((res.get("verifier_result") or {}).get("rewards") or {}).get("reward")
    agent = (res.get("config") or {}).get("agent") or {}
    return {"trial": trial.name, "reward": rew, "model": agent.get("model_name") or agent.get("model") or "?",
            "agent_min": "?", "note": (res.get("exception_info") or {}).get("exception_type", "")}


def build_evidence(trial, out):
    res = jload(trial / "result.json") or {}
    task = Path(res["config"]["task"]["path"]).name
    tdir, bdir = ROOT / "tasks" / task, ROOT / "build" / task
    ev = out / "evidence"
    (ev / "grading").mkdir(parents=True)
    for f in ("instruction.md", "task.toml"):
        shutil.copy2(tdir / f, ev / f)
    shutil.copytree(tdir / "tests", ev / "tests")
    (ev / "solution").mkdir()
    shutil.copy2(tdir / "solution" / "fix.patch", ev / "solution" / "fix.patch")
    for f in ("BRIEF.md", "notes.md"):
        if (bdir / f).exists():
            shutil.copy2(bdir / f, ev / f"build-{f}")
    gdir, gname = grading_dir(trial)
    for f in ("results.json", "reward.json"):
        if (gdir / "verifier" / f).exists():
            shutil.copy2(gdir / "verifier" / f, ev / "grading" / f)
    so = gdir / "verifier" / "test-stdout.txt"
    if so.exists():
        lines = so.read_text(errors="replace").splitlines()
        (ev / "grading" / "test-stdout.tail.txt").write_text("\n".join(lines[-600:]))
    if (gdir / "REGRADE.json").exists():
        shutil.copy2(gdir / "REGRADE.json", ev / "grading" / "REGRADE.json")
    if (trial / "netguard.log").exists():          # repository block decisions (common/trial/netguard)
        shutil.copy2(trial / "netguard.log", ev / "netguard.log")
    if (trial / "final-code").is_dir():
        shutil.copytree(trial / "final-code", ev / "final-code")
    transcript = trial / "agent" / "claude-code.txt"
    (ev / "transcript.md").write_text(digest_transcript(transcript))
    row = audit_row(trial)
    run = {"task": task, "trial": trial.name, "grading_audited": gname, "audit_row": row,
           "timing": timing(trial, res),
           "tests_note": "evidence/tests is the task's CURRENT version; if test names in grading/results.json "
                         "differ, the task changed after this run: judge by the graded names and results",
           "exception_info": res.get("exception_info"), "full_transcript": str(transcript)}
    (ev / "run.json").write_text(json.dumps(run, indent=1, default=str))
    return task, gname, row


def current_postmortem(trial):
    """Newest POSTMORTEM.json, or None. It is current only if it audited the grading now in use."""
    pms = sorted(trial.glob("postmortem-*/POSTMORTEM.json"))
    if not pms:
        return None
    pm = jload(pms[-1]) or {}
    return pm if pm.get("grading_audited") == grading_dir(trial)[1] else None


def prepare(trial):
    trial = Path(trial).resolve()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = trial / f"postmortem-{stamp}"
    task, gname, row = build_evidence(trial, out)
    (out / "verdict.schema.json").write_text(json.dumps(SCHEMA, indent=1))
    (out / "AUDITOR_BRIEF.md").write_text(BRIEF.format(
        model=row.get("model", "?"), minutes=row.get("agent_min", "?"), reward=row.get("reward", "?"),
        out=out))
    (out / "PREPARED.json").write_text(json.dumps(
        {"trial": trial.name, "task": task, "grading_audited": gname,
         "prepared_utc": datetime.now(timezone.utc).isoformat(timespec="seconds")}, indent=1))
    return out


def validate(v):
    errs = []
    for k in SCHEMA["required"]:
        if k not in v:
            errs.append(f"missing {k}")
    if v.get("attribution") not in SCHEMA["properties"]["attribution"]["enum"]:
        errs.append(f"bad attribution {v.get('attribution')!r}")
    if not isinstance(v.get("trustworthy"), bool):
        errs.append("trustworthy must be true/false")
    item_enum = SCHEMA["properties"]["items"]["items"]["properties"]["verdict"]["enum"]
    for it in v.get("items", []):
        if it.get("verdict") not in item_enum:
            errs.append(f"bad item verdict {it.get('verdict')!r}")
    return errs


def record(out, auditor=AUDITOR):
    out = Path(out).resolve()
    prep = jload(out / "PREPARED.json")
    verdict = jload(out / "verdict.json")
    if not prep or verdict is None:
        sys.exit(f"{out}: needs PREPARED.json and verdict.json")
    errs = validate(verdict)
    if errs:
        sys.exit(f"{out}/verdict.json invalid: {errs}")
    row = jload(out / "evidence" / "run.json").get("audit_row", {})
    pm = {**prep, "auditor": auditor, "recorded_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
          "verdict": verdict}
    (out / "POSTMORTEM.json").write_text(json.dumps(pm, indent=1))
    md = [f"# Post-run audit: {prep['trial']}", "",
          f"Auditor: {auditor}; grading audited: {prep['grading_audited']}; reward {row.get('reward')}.", "",
          f"**Trustworthy:** {verdict.get('trustworthy')}  **Attribution:** {verdict.get('attribution')}  "
          f"**Confidence:** {verdict.get('confidence')}", "", verdict.get("summary", ""), "",
          "| Test | Outcome | Verdict | Stated in instruction | Correct fix would pass |", "|---|---|---|---|---|"]
    for it in verdict.get("items", []):
        md.append(f"| {it.get('test')} | {it.get('outcome')} | {it.get('verdict')} | "
                  f"{it.get('stated_in_instruction')} | {it.get('correct_fix_would_pass')} |")
    md += ["", "**Lookup or leak:** " + str(verdict.get("lookup_or_leak", "")), "", "**Evidence:**"] + \
          [f"- {e}" for e in verdict.get("evidence", [])] + \
          ["", "**Recommended action:** " + str(verdict.get("recommended_action", ""))]
    (out / "POSTMORTEM.md").write_text("\n".join(md) + "\n")
    return {"trial": prep["trial"], "trustworthy": verdict["trustworthy"],
            "attribution": verdict["attribution"], "confidence": verdict["confidence"]}


def pending():
    """Runs that would count toward a verdict but lack a current audit, as listed by
    common/audit/audit_results.py in build/audit/awaiting_audit.tsv (run that first)."""
    f = ROOT / "build/audit/awaiting_audit.tsv"
    return [JOBS / r["job"] / r["trial"] for r in csv.DictReader(open(f), delimiter="\t")] if f.exists() else []


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("prepare")
    p.add_argument("trial_dir")
    p = sub.add_parser("record")
    p.add_argument("postmortem_dir")
    p.add_argument("--auditor", default=AUDITOR)
    sub.add_parser("pending")
    sub.add_parser("record-ready", help="record every prepared folder whose auditor wrote verdict.json")
    a = ap.parse_args()
    if a.cmd == "prepare":
        print(prepare(a.trial_dir))
    elif a.cmd == "record":
        print(json.dumps(record(a.postmortem_dir, a.auditor)))
    elif a.cmd == "record-ready":
        for v in sorted(JOBS.glob("*/*/postmortem-*/verdict.json")):
            if not (v.parent / "POSTMORTEM.json").exists():
                print(json.dumps(record(v.parent)))
    else:
        for t in pending():
            print(t)


if __name__ == "__main__":
    main()
