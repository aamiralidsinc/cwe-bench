"""Apply the screener-v2 choice rule (builder/SCREENER-PROMPT-v2.md, "Choice") to a calibration run.

  python3 -I screen_choose.py STAGING claims      # write the blind fact-check sample
  python3 -I screen_choose.py STAGING report      # gates, fact precision, ranking with intervals

STAGING: screen_prepare.py output with runs/<model>/<entry_id>/{host.json, validate.json, ...}.
`claims` picks the 5 hosts that beat a model plus 5 solved hosts (random, seed 20261017) and writes
  fact-check/claims.tsv     claim_id, entry_id, field, where, text   (no model names)
  fact-check/key.tsv        claim_id -> model                       (kept away from checkers)
Checkers fill fact-check/verdicts.tsv: claim_id <TAB> holds|fails|unclear <TAB> note.
`report` prints one row per model and writes choice.md.
"""
import csv, hashlib, json, os, random, re, sys
from itertools import combinations

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import screen_calibrate as sc  # noqa: E402  (label(), and the scoring path through rerank)
import validate_screen  # noqa: E402

SEED = 20261017


def labels(S):
    hosts = [l.rstrip("\n").split("\t") for l in open(os.path.join(S, "hosts.tsv")) if l.strip()]
    adv2eid = {h[4].upper(): h[0] for h in hosts}
    lab = {}
    for r in csv.DictReader(open(os.path.join(S, "labels.tsv")), delimiter="\t"):
        e = adv2eid[r["advisory"].upper()]
        lab[e] = max(lab.get(e, 0), sc.label(r["outcome"]))
    return [h[0] for h in hosts], lab


def sample_hosts(eids, lab):
    pos = sorted(e for e in eids if lab[e] >= 1)
    neg = sorted(e for e in eids if lab[e] == 0)
    return pos + sorted(random.Random(SEED).sample(neg, 5))


def load(S, m, e):
    try:
        return json.load(open(os.path.join(S, "runs", m, e, "host.json")))
    except (OSError, ValueError):
        return None


def cmd_claims(S):
    eids, lab = labels(S)
    models = sorted(os.listdir(os.path.join(S, "runs")))
    d = os.path.join(S, "fact-check")
    os.makedirs(d, exist_ok=True)
    rows, key = [], []
    for e in sample_hosts(eids, lab):
        for m in models:
            r = load(S, m, e)
            if not isinstance(r, dict):
                continue
            o2 = r.get("O2_out_of_scope_site") or {}
            cl = []
            if isinstance(o2, dict) and o2.get("kind") not in (None, "none", "unknown"):
                cl.append(("O2", o2.get("where", ""), f"out-of-scope-looking site of kind {o2.get('kind')}; "
                           f"reason to dismiss: {r.get('O3_reason_to_dismiss', '')}"))
            for x in r.get("O8_uncovered_routes") or []:
                if isinstance(x, dict) and str(x.get("where") or "").strip() not in ("", "path:line"):
                    cl.append(("O8", x.get("where", ""), str(x.get("route", ""))))
            for f, w, t in cl:
                cid = hashlib.sha1(f"{m}|{e}|{f}|{w}|{t}".encode()).hexdigest()[:10]
                rows.append((cid, e, f, w.replace("\t", " "), t.replace("\t", " ").replace("\n", " ")))
                key.append((cid, m))
    random.Random(SEED).shuffle(rows)  # model order must not show
    with open(os.path.join(d, "claims.tsv"), "w") as f:
        f.write("claim_id\tentry_id\tfield\twhere\ttext\n")
        for r in rows:
            f.write("\t".join(r) + "\n")
    with open(os.path.join(d, "key.tsv"), "w") as f:
        f.write("claim_id\tmodel\n")
        for k in key:
            f.write("\t".join(k) + "\n")
    print(f"{len(rows)} claims on hosts {sample_hosts(eids, lab)} -> {d}/claims.tsv")


def concordance(pairs_scores):
    p = c = 0.0
    for (l1, s1), (l2, s2) in combinations(pairs_scores, 2):
        if l1 == l2:
            continue
        p += 1
        hi, lo = (s1, s2) if l1 > l2 else (s2, s1)
        c += 1 if hi > lo else 0.5 if hi == lo else 0
    return c / p if p else float("nan")


def false_hard(ls):
    pos = sorted(s for l, s in ls if l >= 1)
    neg = [s for l, s in ls if l == 0]
    if not pos or not neg:
        return float("nan")
    med = pos[len(pos) // 2] if len(pos) % 2 else (pos[len(pos) // 2 - 1] + pos[len(pos) // 2]) / 2
    return sum(1 for s in neg if s > med) / len(neg)


def boot(ls, fn, n=2000):
    rng = random.Random(SEED)
    pos = [x for x in ls if x[0] >= 1]
    neg = [x for x in ls if x[0] == 0]
    vals = []
    for _ in range(n):  # stratified: keep the class sizes
        b = [rng.choice(pos) for _ in pos] + [rng.choice(neg) for _ in neg]
        v = fn(b)
        if v == v:
            vals.append(v)
    vals.sort()
    return vals[int(0.05 * len(vals))], vals[int(0.95 * len(vals)) - 1]


def cmd_report(S):
    eids, lab = labels(S)
    models = sorted(os.listdir(os.path.join(S, "runs")))
    W = json.load(open(os.path.join(HERE, "screen-weights.json")))
    import sqlite3, rerank
    con = sqlite3.connect(f"file:{sc.DB}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    llm_rx = json.load(open(os.path.join(HERE, "..", "weights.json")))["weakness"]["llm_in_the_loop"]["summary_regex"]
    verdicts = {}
    vp = os.path.join(S, "fact-check", "verdicts.tsv")
    if os.path.exists(vp):
        for r in csv.reader(open(vp), delimiter="\t"):
            if r and r[0] != "claim_id":
                verdicts[r[0]] = r[1].strip()
    key = {}
    kp = os.path.join(S, "fact-check", "key.tsv")
    if os.path.exists(kp):
        key = {r["claim_id"]: r["model"] for r in csv.DictReader(open(kp), delimiter="\t")}
    out = []
    for m in models:
        valid = refs_t = refs_ok = notes = selfc = stops = 0
        scored = {}
        for e in eids:
            rec = load(S, m, e)
            v = None
            vpth = os.path.join(S, "runs", m, e, "validate.json")
            if os.path.exists(vpth):
                v = json.load(open(vpth))
            run = {}
            for fn in ("run.json",):
                try:
                    run = json.load(open(os.path.join(S, "runs", m, e, fn)))
                except (OSError, ValueError):
                    pass
            if run.get("is_error"):
                stops += 0  # API errors are not safety stops; listed separately below
            if rec is None or v is None or v["errors"]:
                continue
            valid += 1
            refs_t += v["refs_total"]; refs_ok += v["refs_ok"]
            notes += sum("note after the value" in w for w in v["warnings"])
            selfc += sum("self-citation" in b for b in v["refs_bad"])
            row = con.execute(rerank.ROW_SQL + " where e.entry_id = ?", (int(e),)).fetchone()
            r2 = validate_screen.normalise(rec)
            weak = [x for x in rerank.host_terms(row, llm_rx) if x[2] == "H5"]
            scored[e] = sum(p for p, _w in rerank.screen_terms(r2, W)) + rerank.term_sum(weak)
        mine = [c for c, mm in key.items() if mm == m and c in verdicts]
        held = sum(verdicts[c] == "holds" for c in mine)
        judged = sum(verdicts[c] in ("holds", "fails") for c in mine)
        out.append({"model": m, "valid": valid, "n": len(eids), "refs_t": refs_t, "refs_ok": refs_ok,
                    "notes": notes, "selfc": selfc, "scored": scored,
                    "prec": (held / judged) if judged else None, "claims": judged,
                    "unclear": sum(verdicts[c] == "unclear" for c in mine)})
    common = set(eids)
    for o in out:
        common &= set(o["scored"])
    lines = ["| Model | Valid | Wrong evidence | Gates | Fact precision | Ranking (90% CI) | False-hard (90% CI) | Enum notes |",
             "|---|---|---|---|---|---|---|---|"]
    for o in out:
        ls = [(lab[e], o["scored"][e]) for e in sorted(common)]
        we = (o["refs_t"] - o["refs_ok"]) / o["refs_t"] if o["refs_t"] else 1
        gates = o["valid"] / o["n"] >= 0.95 and we < 0.05
        c, (clo, chi) = concordance(ls), boot(ls, concordance)
        fh, (flo, fhi) = false_hard(ls), boot(ls, false_hard)
        o.update(gates=gates, conc=c, fh=fh)
        prec = f"{100 * o['prec']:.0f}% ({o['claims']} claims, {o['unclear']} unclear)" if o["prec"] is not None else "not checked"
        lines.append(f"| {o['model']} | {o['valid']}/{o['n']} | {100 * we:.1f}% ({o['selfc']} self-cited) | "
                     f"{'pass' if gates else 'FAIL'} | {prec} | {c:.2f} ({clo:.2f}-{chi:.2f}) | "
                     f"{fh:.2f} ({flo:.2f}-{fhi:.2f}) | {o['notes']} |")
    lines.append(f"\nRanking and false-hard on the {len(common)} hosts every model returned valid "
                 f"({sum(lab[e] >= 1 for e in common)} beat a model). Safety stops: none recorded by the runner.")
    text = "\n".join(lines)
    open(os.path.join(S, "choice.md"), "w").write(text + "\n")
    print(text)


if __name__ == "__main__":
    S, cmd = sys.argv[1], sys.argv[2]
    {"claims": cmd_claims, "report": cmd_report}[cmd](S)
