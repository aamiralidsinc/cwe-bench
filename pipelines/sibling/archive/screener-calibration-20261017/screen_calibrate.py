"""Compare screener-v1 calibration runs across models (SCREENER-PROMPT-v1.md, "Model comparison").

  python3 -I screen_calibrate.py STAGING --reference claude-opus-5-5 [--md]

STAGING is the screen_prepare.py output after the runs came back:
  labels.tsv, hosts.tsv, runs/<model>/<entry_id>/{host.json, run.json, exit.txt, validate.json?}
  hosts/<entry_id>/repo/ (optional locally; used for file:line checks when validate.json is absent)

Metrics per model:
- agreement: share of (host, field) pairs equal to the reference, over O1-O8 and pattern_fit,
  compared in buckets (FIELDS below). The reference's own row is 100% by definition; its
  readings need the lead's check before the other rows mean anything.
- wrong evidence: file:line references that do not resolve (validator), over all references.
- ranking: pairwise concordance of score_read with the known outcomes (2 = both models failed,
  1 = one model failed, 0 = solved; best outcome per advisory); ties count 0.5.
- cost / time / turns from run.json; stops = runs that ended in a refusal or error, or wrote
  no valid record.
"""
import argparse, csv, json, os, re, sqlite3, sys, time
from collections import defaultdict
from itertools import combinations

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import validate_screen  # noqa: E402
import rerank  # noqa: E402

DB = os.path.join(HERE, "..", "index", "candidates.sqlite")


def b_count(v, cuts):
    if not isinstance(v, int):
        return "unknown"
    for c in cuts:
        if v < c:
            return f"<{c}"
    return f">={cuts[-1]}"


def filled(s):
    return bool(str(s or "").strip()) and str(s).strip() != "unknown"


def routes(r):
    return [x for x in r.get("O8_uncovered_routes") or [] if isinstance(x, dict) and filled(x.get("where"))
            and x.get("where") != "path:line"]


FIELDS = {
    "O1": lambda r: b_count(r.get("O1_entry_points"), [2, 3]),
    "O2": lambda r: (r.get("O2_out_of_scope_site") or {}).get("kind"),
    "O3": lambda r: filled(r.get("O3_reason_to_dismiss")),
    "O4": lambda r: b_count((r.get("O4_distance") or {}).get("files"), [2, 3]),
    "O5": lambda r: filled((r.get("O5_coupled_behaviour") or {}).get("what")),
    "O6": lambda r: len(r.get("O6_input_shapes") or []) >= 2,
    "O7": lambda r: (r.get("O7_producer") or {}).get("kind"),
    "O8": lambda r: b_count(len(routes(r)), [1, 2]),
    "pattern_fit": lambda r: r.get("pattern_fit"),
}


def label(outcome):
    o = outcome.lower()
    if "both models 0/" in o:
        return 2
    if re.search(r"\b0/\d", o):
        return 1
    return 0


def load_json(p):
    try:
        return json.load(open(p, encoding="utf-8"))
    except (OSError, ValueError):
        return None


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("staging")
    ap.add_argument("--reference", default="claude-opus-5-5")
    ap.add_argument("--weights", default=os.path.join(HERE, "screen-weights.json"))
    ap.add_argument("--md", action="store_true", help="print comparison-log rows in markdown")
    a = ap.parse_args(argv)
    S = a.staging
    W = json.load(open(a.weights))
    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    llm_rx = json.load(open(os.path.join(HERE, "..", "weights.json")))["weakness"]["llm_in_the_loop"]["summary_regex"]

    hosts = [l.rstrip("\n").split("\t") for l in open(os.path.join(S, "hosts.tsv")) if l.strip()]
    adv2eid = {h[4].upper(): h[0] for h in hosts}
    lab = {}
    for r in csv.DictReader(open(os.path.join(S, "labels.tsv")), delimiter="\t"):
        eid = adv2eid[r["advisory"].upper()]
        lab[eid] = max(lab.get(eid, 0), label(r["outcome"]))
    models = sorted(os.listdir(os.path.join(S, "runs")))

    recs, info = {}, {}
    for m in models:
        for h in hosts:
            eid = h[0]
            d = os.path.join(S, "runs", m, eid)
            rec = load_json(os.path.join(d, "host.json"))
            run = load_json(os.path.join(d, "run.json")) or {}
            val = load_json(os.path.join(d, "validate.json"))
            if rec is not None and val is None:
                repo = os.path.join(S, "hosts", eid, "repo")
                val = validate_screen.validate(rec, validate_screen.schema_for(rec.get("screener_version")),
                                               repo if os.path.isdir(repo) else None)
            ok = rec is not None and val is not None and not val["errors"]
            txt = json.dumps(run).lower()
            stopped = (not ok) or bool(run.get("is_error")) or "refus" in str(run.get("stop_reason", "")).lower() \
                or '"stop_reason": "refusal"' in txt
            score = None
            if ok:
                rec = validate_screen.normalise(rec)
                row = con.execute(rerank.ROW_SQL + " where e.entry_id = ?", (int(eid),)).fetchone()
                weak = [x for x in rerank.host_terms(row, llm_rx) if x[2] == "H5"]
                score = sum(p for p, _w in rerank.screen_terms(rec, W)) + rerank.term_sum(weak)
            info[m, eid] = {"ok": ok, "stopped": stopped, "score": score, "val": val,
                            "cost": run.get("total_cost_usd"), "ms": run.get("duration_ms"),
                            "turns": run.get("num_turns"),
                            "errors": (val or {}).get("errors", ["no host.json"]) if not ok else []}
            if ok:
                recs[m, eid] = rec = validate_screen.normalise(rec)

    out_rows, detail = [], []
    for m in models:
        agree = tot = 0
        for h in hosts:
            eid = h[0]
            ref, rec = recs.get((a.reference, eid)), recs.get((m, eid))
            for f, fn in FIELDS.items():
                if ref is None or rec is None:
                    continue
                tot += 1
                same = fn(ref) == fn(rec)
                agree += same
                detail.append((m, eid, f, fn(ref), fn(rec), int(same)))
        refs_t = sum((info[m, h[0]]["val"] or {}).get("refs_total", 0) for h in hosts if info[m, h[0]]["ok"])
        refs_ok = sum((info[m, h[0]]["val"] or {}).get("refs_ok", 0) for h in hosts if info[m, h[0]]["ok"])
        pairs = conc = 0.0
        scored = [(lab[h[0]], info[m, h[0]]["score"]) for h in hosts if info[m, h[0]]["score"] is not None]
        for (l1, s1), (l2, s2) in combinations(scored, 2):
            if l1 == l2:
                continue
            pairs += 1
            hi, lo = ((s1, s2) if l1 > l2 else (s2, s1))
            conc += 1 if hi > lo else 0.5 if hi == lo else 0
        cost = sum(info[m, h[0]]["cost"] or 0 for h in hosts)
        mins = sum((info[m, h[0]]["ms"] or 0) for h in hosts) / 60000
        n_ok = sum(info[m, h[0]]["ok"] for h in hosts)
        stops = sum(info[m, h[0]]["stopped"] for h in hosts)
        out_rows.append({
            "model": m, "valid": f"{n_ok}/{len(hosts)}",
            "agreement": f"{100 * agree / tot:.0f}% ({agree}/{tot})" if tot else "n/a",
            "wrong_evidence": f"{100 * (refs_t - refs_ok) / refs_t:.0f}% ({refs_t - refs_ok}/{refs_t})" if refs_t else "n/a",
            "ranking": f"{conc / pairs:.2f} ({int(pairs)} pairs)" if pairs else "n/a",
            "cost_time": f"${cost:.2f} / {mins:.0f} min total",
            "stops": str(stops),
        })

    with open(os.path.join(S, "calibration-detail.tsv"), "w") as f:
        f.write("model\tentry_id\tfield\treference\tvalue\tagree\n")
        for d in detail:
            f.write("\t".join(map(str, d)) + "\n")
    with open(os.path.join(S, "calibration-scores.tsv"), "w") as f:
        f.write("model\tentry_id\tlabel\tscore_read\tvalid\tcost_usd\tminutes\tturns\terrors\n")
        for (m, eid), x in sorted(info.items()):
            f.write(f"{m}\t{eid}\t{lab[eid]}\t{x['score']}\t{int(x['ok'])}\t{x['cost']}\t"
                    f"{(x['ms'] or 0) / 60000:.1f}\t{x['turns']}\t{'; '.join(x['errors'][:2])}\n")
    for r in out_rows:
        if a.md:
            print(f"| {time.strftime('%Y-%m-%d', time.gmtime())} | {r['model']} | {r['agreement']} | "
                  f"{r['wrong_evidence']} | {r['ranking']} | {r['cost_time']} | {r['stops']} | "
                  f"valid {r['valid']}; reference {a.reference} |")
        else:
            print(r)


if __name__ == "__main__":
    sys.exit(main())
