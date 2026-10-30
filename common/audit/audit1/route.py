#!/usr/bin/env python3
"""Audit 1, step 4 (no LLM): the deterministic route of one run from FACTS.json, DOSSIER.json and the quote check.

    python3 common/audit/audit1/route.py <run-folder>        # prints the route as JSON

Routes (the routing table of docs/AUDIT-TWO-STAGE-DESIGN.md):
  infra-rerun            a hard infra fact (provider stop, API cut, no result, harness exception, tool calls inside the
                         grading window, broken workspace transfer), or the dossier labels EVERY failing test infra
  hold-contamination     the dossier judges a contamination hit real                               -> Opus
  hold-unfair-deciding   every failing test is labelled possibly-unfair or infra, at least one possibly-unfair, and
                         no possibly-unfair item says fair_version_passes=false (decided_by_unfair is recomputed from
                         the labels, never taken from the agent)                                    -> Opus, 1 item
  note-unfair            some failing tests possibly-unfair, at least one fair: provisional fail + note for the review
  provisional-fail       every failing test fair
  unverified             the quote check failed (after the retry) or the dossier does not cover every failing test or
                         is missing/invalid; replaces provisional-fail / note-unfair only (a hold stays a hold)
"""
import json
import sys
from pathlib import Path

HARD_INFRA = {"provider-stop", "no-result", "no-result-event", "api-cut", "exception", "agent-cut",
              "tool-calls-in-grading-window", "trial-log", "agent-error", "verifier-setup-flag",
              "permission-denied", "same-env-crash-everywhere"}
SOFT_KINDS = {"verifier-setup-flag"}      # a flag only: real infra only when the dossier agrees


def jload(p):
    try:
        return json.loads(Path(p).read_text(), strict=False)
    except (OSError, ValueError):
        return None


def labels(dossier, demote=False):
    """{test id: label}. A possibly-unfair item whose fair_version_passes is false (this model's code would fail a fair
    version of the test too) cannot decide the run: it is returned as "unfair-not-deciding:<kind>"."""
    out = {}
    for g in (dossier or {}).get("failing") or []:
        lab = str(g.get("label") or "")
        if demote and lab.startswith("possibly-unfair") and g.get("fair_version_passes") is False:
            lab = "unfair-not-deciding:" + lab.split(":", 1)[-1]
        for t in g.get("tests") or []:
            out[t] = lab
    return out


def route(folder, demote=False):
    """demote: a possibly-unfair item with fair_version_passes=false cannot decide the run (round-2 rule)."""
    d = Path(folder)
    facts = jload(d / "FACTS.json") or {}
    dossier = jload(d / "DOSSIER.json")
    qc = None
    for n in (2, 1):
        qc = jload(d / f"QUOTECHECK-{n}.json")
        if qc is not None:
            break
    failing = [t["id"] for t in facts.get("failing_tests") or []]
    lab = labels(dossier, demote)
    covered = [t for t in failing if t in lab]
    uncovered = [t for t in failing if t not in lab]
    run = (dossier or {}).get("run") or {}
    infra_facts = [s for s in facts.get("infra_signals") or [] if s.get("infra") and s.get("kind") in HARD_INFRA]
    hard = [s for s in infra_facts if s["kind"] not in SOFT_KINDS]
    soft = [s for s in infra_facts if s["kind"] in SOFT_KINDS]
    all_infra_labels = bool(covered) and all(lab[t] == "infra" for t in covered) and not uncovered
    unfair = [t for t in covered if lab[t].startswith("possibly-unfair")]
    not_deciding = [t for t in covered if lab[t].startswith("unfair-not-deciding")]
    fair = [t for t in covered if lab[t] == "fair"]
    other = [t for t in covered if t not in unfair and t not in fair and t not in not_deciding and lab[t] != "infra"]
    decided = bool(unfair) and not fair and not other and not not_deciding and not uncovered
    contam = [c for c in run.get("contamination") or [] if c.get("real") is True] or \
             ([{"hit": "run", "real": True}] if run.get("contamination_real") is True else [])
    verified = dossier is not None and qc is not None and qc.get("pass") is True and not uncovered
    why = []
    if hard or (soft and run.get("infra", {}).get("value") is True) or all_infra_labels:
        r = "infra-rerun"
        why = [f"{s['id']} {s['kind']}" for s in hard + soft] or ["every failing test labelled infra"]
    elif contam:
        r = "hold-contamination"
        why = [f"real contamination hit {c.get('hit')}" for c in contam]
    elif decided:
        r = "hold-unfair-deciding"
        why = [f"{t}: {lab[t]}" for t in unfair]
    elif dossier is None:
        r, why = "unverified", ["no DOSSIER.json"]
    elif not verified:
        r = "unverified"
        why = (["quote check failed"] if not (qc or {}).get("pass") else []) + \
              ([f"{len(uncovered)} failing tests not in the dossier"] if uncovered else [])
    elif unfair or not_deciding:
        r = "note-unfair"
        why = [f"{t}: {lab[t]}" for t in unfair + not_deciding]
    else:
        r = "provisional-fail"
    return {"route": r, "why": why, "verified": verified, "decided_by_unfair": decided,
            "failing": len(failing), "unfair": unfair, "unfair_not_deciding": not_deciding, "fair": fair, "uncovered": uncovered,
            "agent_decided_by_unfair": run.get("decided_by_unfair"), "agent_attribution": run.get("attribution"),
            "thin": run.get("thin"), "contamination_real": bool(contam)}


if __name__ == "__main__":
    print(json.dumps(route(sys.argv[1]), indent=1))
