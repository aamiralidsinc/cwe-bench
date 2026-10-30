#!/usr/bin/env python3
"""Audit 1 calibration: compare audit-1 dossiers with the Opus verdicts of the same runs.

    python3 common/audit/audit1/calibrate.py <config.json>

config.json (a file, so no task names reach the command line):
    {"runs": "<folder with one sub-folder per trial (DOSSIER.json, FACTS.json, AUDIT1.json, QUOTECHECK-*.json)>",
     "opus": "<TSV: trial<TAB>path of the Opus verdict.json>",          # read only; never copied next to the runs
     "only": ["<trial>", ...],                                          # optional subset (a re-run round)
     "out": "<prefix for <prefix>.tsv and <prefix>.json>"}

Opus classes (from verdict.json):
    unfair-decided   attribution test-fault (an unfair test decided the run)
    ambiguity        attribution instruction-ambiguity (reported with gate 1 as an extra row)
    infra            attribution harness-or-infra
    contaminated     attribution contaminated
    fair-fail        attribution model-failed (with or without unfair items that did not decide)
    other            model-solved / unclear
Audit-1 route (route.py): infra-rerun, hold-contamination, hold-unfair-deciding, note-unfair, provisional-fail,
unverified.

Metrics: (1) recall on unfair-decided (route hold-unfair-deciding); (2) recall on infra (infra-rerun) and on
contaminated (hold-contamination), plus false contamination holds; (3) first-try quote-check pass rate;
(4) agreement on fair-fail (route provisional-fail or note-unfair); (5) false hold-unfair-deciding on Opus fair-fail
runs; (6) DeepSeek tokens per run and an estimate of the Opus tokens audit 2 would read (dossier + cited slices).
"""
import collections
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import route as routemod  # noqa: E402
import quote_check  # noqa: E402

CHARS_PER_TOKEN = 3.6
SLICE = 8                  # lines either side of a cited line that audit 2 would read
AUDIT2_FIXED = 6000        # brief + tool/system overhead per run (Opus sub-agent), tokens
AUDIT2_OUTPUT = 2500       # verdict.json per run, tokens


def jload(p):
    try:
        return json.loads(Path(p).read_text())
    except (OSError, ValueError):
        return None


def opus_class(v):
    a = (v or {}).get("attribution")
    return {"test-fault": "unfair-decided", "instruction-ambiguity": "ambiguity", "harness-or-infra": "infra",
            "contaminated": "contaminated", "model-failed": "fair-fail"}.get(a, "other")


def deepseek_tokens(a1):
    tot = {"input": 0, "cache_read": 0, "cache_creation": 0, "output": 0}
    for att in (a1 or {}).get("attempts") or []:
        for k in tot:
            tot[k] += int((att.get("tokens") or {}).get(k) or 0)
    tot["total"] = sum(tot.values())
    return tot


def audit2_estimate(folder):
    """Opus tokens to read DOSSIER.json + the cited slices (+-SLICE lines, merged per file) + fixed + output."""
    d = Path(folder)
    dossier = jload(d / "DOSSIER.json")
    if dossier is None:
        return None, None
    chars = len((d / "DOSSIER.json").read_text(errors="replace"))
    ranges = collections.defaultdict(list)
    for _, q in quote_check.quotes_in(dossier):
        try:
            ln = int(q.get("line"))
        except (TypeError, ValueError):
            continue
        ranges[str(q.get("file"))].append((max(1, ln - SLICE), ln + SLICE))
    slice_chars = 0
    for f, rs in ranges.items():
        p = d / f
        if not p.is_file():
            continue
        lines = p.read_text(errors="replace").splitlines()
        merged = []
        for a, b in sorted(rs):
            if merged and a <= merged[-1][1] + 1:
                merged[-1] = (merged[-1][0], max(merged[-1][1], b))
            else:
                merged.append((a, b))
        for a, b in merged:
            slice_chars += sum(len(x) + 1 for x in lines[a - 1:b])
    instr = (d / "evidence" / "instruction.md")
    per_task_chars = len(instr.read_text(errors="replace")) if instr.is_file() else 0
    per_run = int((chars + slice_chars) / CHARS_PER_TOKEN) + AUDIT2_FIXED + AUDIT2_OUTPUT
    return per_run, int(per_task_chars / CHARS_PER_TOKEN)


def main():
    cfg = json.loads(Path(sys.argv[1]).read_text())
    runs = Path(cfg["runs"])
    opus = {}
    for line in Path(cfg["opus"]).read_text().splitlines():
        if line.strip() and not line.startswith("#"):
            t, p = line.split("\t")[:2]
            opus[t] = p
    only = set(cfg.get("only") or [])
    rows = []
    for t in sorted(opus):
        if only and t not in only:
            continue
        d = runs / t
        v = jload(opus[t])
        a1 = jload(d / "AUDIT1.json") or {}
        r = routemod.route(d)
        q1 = jload(d / "QUOTECHECK-1.json")
        est, per_task = audit2_estimate(d)
        unfair_items = [it for it in (v or {}).get("items") or []
                        if it.get("outcome") == "fail" and it.get("unfair_kind", "none") not in ("none", None)]
        rows.append({
            "trial": t, "task": t.split("__")[0], "opus": opus_class(v), "opus_attribution": (v or {}).get("attribution"),
            "opus_unfair_items": len(unfair_items), "route": r["route"], "why": "; ".join(r["why"])[:300],
            "agent_attr": r["agent_attribution"], "a1_status": a1.get("status"),
            "first_try_quote": (q1 or {}).get("pass"), "q1_failed": (q1 or {}).get("failed"),
            "q1_quotes": (q1 or {}).get("quotes"), "attempts": len(a1.get("attempts") or []),
            "unfair_flagged": len(r["unfair"]), "uncovered": len(r["uncovered"]),
            "thin": r["thin"], "ds_tokens": deepseek_tokens(a1), "audit2_est": est, "audit2_per_task": per_task,
            "wall_sec": a1.get("wall_sec"),
        })

    def recall(cls, routes):
        pos = [x for x in rows if x["opus"] == cls]
        hit = [x for x in pos if x["route"] in routes]
        return len(hit), len(pos), [x for x in pos if x["route"] not in routes]

    out = []
    h, n, miss1 = recall("unfair-decided", {"hold-unfair-deciding"})
    out.append(("1 recall unfair-decided (gate >= 90%)", h, n, n and h / n >= 0.9))
    ha, na, missa = recall("ambiguity", {"hold-unfair-deciding"})
    out.append(("1b instruction-ambiguity routed to hold (report)", ha, na, None))
    hi, ni, missi = recall("infra", {"infra-rerun"})
    out.append(("2a recall infra (gate 100%)", hi, ni, ni == 0 or hi == ni))
    hc, nc, missc = recall("contaminated", {"hold-contamination"})
    out.append(("2b recall contaminated (gate 100%)", hc, nc, nc == 0 or hc == nc))
    fc = [x for x in rows if x["route"] == "hold-contamination" and x["opus"] != "contaminated"]
    tried = [x for x in rows if x["first_try_quote"] is not None]
    qp = [x for x in tried if x["first_try_quote"]]
    out.append(("3 quote check first-try pass (gate >= 90%)", len(qp), len(rows), rows and len(qp) / len(rows) >= 0.9))
    ff = [x for x in rows if x["opus"] == "fair-fail"]
    agree = [x for x in ff if x["route"] in ("provisional-fail", "note-unfair")]
    out.append(("4 agreement on fair model fail (report)", len(agree), len(ff), None))
    false_hold = [x for x in ff if x["route"] == "hold-unfair-deciding"]
    out.append(("5 false hold-unfair-deciding on Opus fair fails (count)", len(false_hold), len(ff), None))
    out.append(("2c false contamination holds (count)", len(fc), len(rows), None))
    toks = [x["ds_tokens"]["total"] for x in rows if x["ds_tokens"]["total"]]
    outs = [x["ds_tokens"]["output"] for x in rows if x["ds_tokens"]["total"]]
    uncached = [x["ds_tokens"]["input"] + x["ds_tokens"]["cache_creation"] for x in rows if x["ds_tokens"]["total"]]
    est = [x["audit2_est"] for x in rows if x["audit2_est"]]
    tasks = collections.defaultdict(list)
    for x in rows:
        if x["audit2_per_task"]:
            tasks[x["task"]].append(x["audit2_per_task"])
    per_task_extra = sum(v[0] for v in tasks.values()) / max(1, len(rows))

    print(f"runs: {len(rows)}   (Opus classes: {dict(collections.Counter(x['opus'] for x in rows))})")
    print(f"routes: {dict(collections.Counter(x['route'] for x in rows))}")
    print()
    print(f"{'metric':58} {'value':>10}  gate")
    for name, a, b, ok in out:
        val = f"{a}/{b}" + (f" ({100 * a / b:.0f}%)" if b else "")
        print(f"{name:58} {val:>14}  {'' if ok is None else ('PASS' if ok else 'FAIL')}")
    if toks:
        toks.sort()
        print(f"\n6 DeepSeek tokens per run (input+cache+output): mean {sum(toks) / len(toks):,.0f}, "
              f"median {toks[len(toks) // 2]:,}, max {max(toks):,}; output mean {sum(outs) / len(outs):,.0f}; "
              f"uncached input mean {sum(uncached) / len(uncached):,.0f}")
    if est:
        print(f"6 Opus audit-2 estimate per run (dossier + cited slices +-{SLICE} lines + {AUDIT2_FIXED} fixed + "
              f"{AUDIT2_OUTPUT} output): mean {sum(est) / len(est):,.0f}, max {max(est):,}; plus instruction once per "
              f"task (~{per_task_extra:,.0f} per run amortised)")
    for title, miss in (("misses on 1 (unfair-decided)", miss1), ("ambiguity not held", missa),
                        ("misses on 2a (infra)", missi), ("misses on 2b (contaminated)", missc),
                        ("false unfair-deciding holds", false_hold), ("false contamination holds", fc)):
        if miss:
            print(f"\n{title}:")
            for x in miss:
                print(f"  {x['trial']}: opus={x['opus_attribution']} route={x['route']} ({x['why'][:160]}) "
                      f"agent_attr={x['agent_attr']} status={x['a1_status']}")
    prefix = Path(cfg.get("out") or (runs.parent / "calibration"))
    keys = [k for k in rows[0] if k != "ds_tokens"] + ["ds_total", "ds_output"] if rows else []
    with open(f"{prefix}.tsv", "w") as fh:
        fh.write("\t".join(keys) + "\n")
        for x in rows:
            vals = [x.get(k) for k in keys[:-2]] + [x["ds_tokens"]["total"], x["ds_tokens"]["output"]]
            fh.write("\t".join("" if v is None else str(v) for v in vals) + "\n")
    Path(f"{prefix}.json").write_text(json.dumps({"metrics": [list(m) for m in out], "rows": rows}, indent=1,
                                                 default=str))
    print(f"\nwrote {prefix}.tsv and {prefix}.json")


if __name__ == "__main__":
    main()
