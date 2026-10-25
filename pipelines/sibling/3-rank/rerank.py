"""Round-2 HOST re-rank of the CWE-bench candidate pool (read-only, offline).

Reads cwe-bench/sourcer/index/candidates.sqlite read-only; writes TSVs to OUT.
Every component is tied to a round-1 lesson (see LESSON comments). No network.

  python3 -I rerank.py DB OUT                          # host-rank-all.tsv, host-shortlist-40.tsv
  python3 -I rerank.py DB OUT --screened DIR [...]     # also host-rank-screened.tsv

--screened scores screener-v1 records (any *.json under DIR, validated first with
pipelines/sibling/3-rank/validate_screen.py; records with errors are skipped and listed) with screen-weights.json:
score_read = screener observation terms + this script's weakness terms (H5). See
screen-weights.json "about" for why the computed proxies are left out of score_read.
"""
import argparse, glob, json, re, sqlite3, sys, csv, os
from collections import Counter
from pathlib import Path
sys.path.insert(0, str(next(p for p in Path(__file__).resolve().parents if (p / ".cwe-bench-root").is_file()) / "common"))
import paths  # noqa: E402  (repo locations: common/paths.py)

HERE = os.path.dirname(os.path.abspath(__file__))

USED = {  # repos already built or trialled in round 1 (build/ and tasks/)
    "fasterxml/jackson-databind", "asynchttpclient/async-http-client", "hickory-dns/hickory-dns",
    "posit-dev/py-shiny", "rclone/rclone", "eugeny/russh", "pylons/webob", "actualbudget/actual",
    "argoproj/argo-workflows", "ronf/asyncssh", "cloudreve/cloudreve", "filamentphp/filament",
    "saml-toolkits/ruby-saml", "onelogin/ruby-saml", "eidetic-labs/stigmem", "triggerdotdev/trigger.dev",
    "marshmallow-code/marshmallow", "typestack/class-transformer", "better-auth/better-auth",
    "modelcontextprotocol/typescript-sdk",
    # shortlisted and built (build/ dirs) but not trialled as breakers
    "koel/koel", "gitpython-developers/gitpython", "pyload/pyload", "shepherdwind/velocity.js",
    "mariadb-corporation/mariadb-connector-j", "thorsten/phpmyfaq", "flavorjones/loofah",
    "go-gitea/gitea", "apache/tomcat", "coredns/coredns", "ardatan/graphql-tools",
    "style-dictionary/style-dictionary", "gradio-app/gradio", "webpack/webpack-dev-middleware",
}

A01_A07 = {22, 23, 35, 59, 200, 201, 219, 264, 275, 276, 284, 285, 352, 359, 377, 402, 425, 441,
           497, 538, 540, 548, 552, 566, 601, 639, 651, 668, 706, 862, 863, 913, 922, 1275,
           # A07
           258, 259, 287, 288, 290, 294, 295, 297, 300, 302, 304, 306, 307, 346, 384, 521, 613,
           620, 640, 798, 940, 1216, 1391, 1392, 1393}
EASY = {78, 89}
SATURATED = {319, 330, 434, 470, 916, 1104}
ROUTE_CWES = {284, 285, 639, 862, 863, 915, 200, 359, 668, 732, 1220, 287, 306, 288}

RX = {
    # LESSON (argo templateDefaults): a merged/default/inherited route reaches the sink
    "merged_or_default_route": re.compile(r"default|merge|inherit|template|fallback|override|cascade|"
                                          r"overlay|patch|extend|base_?config|global", re.I),
    # LESSON (async-http-client cookie, Hadi): parser/decoder differential or producer
    "parser_mismatch": re.compile(r"pars|decod|unmarshal|deserial|normali[sz]|canonical|split|"
                                  r"cookie|header|url|uri|path_?clean|unescape|unquote", re.I),
    # LESSON (rclone): fail-open fallback / legacy compatibility branch
    "fail_open_fallback": re.compile(r"fallback|legacy|compat|deprecated|optional|maybe|or_?else|"
                                     r"default_?(user|role|perm)|anonymous|guest", re.I),
    # LESSON (jackson views/any-setter): protection ignored on one route; linked visible value
    "route_protection": re.compile(r"view|serializ|visib|filter|expos|field|propert|attribute|"
                                   r"scope|permission|policy|acl|role|access|readonly|read_only|"
                                   r"hidden|mass|bind|setter|any", re.I),
}
# LESSON (jackson-readonly vs sib2): a REASON TO DISMISS — a route the protection arguably never covered
DISMISS_RX = re.compile(r"\b(legacy|deprecated|compat(ibility)?|alias(es)?|alternat(e|ive)|unsupported|"
                        r"undocumented|plugin|extension|catch-?all|wildcard|any[- ]?setter|"
                        r"bulk|batch|import|export|webhook|api v?1|v1 api|graphql|rpc|websocket|"
                        r"admin(istrative)? api|cli|backup|restore|sync)\b", re.I)

ROW_SQL = """
  select e.*, c.shape as c_shape, c.src_paths as c_src_paths
  from entries e left join commits c on c.repo = e.repo and c.full_sha = e.fix_commit"""


def cwe_nums(s):
    return {int(x) for x in re.findall(r"CWE-(\d+)", s or "")}


def top_dir(p, depth=2):
    parts = [x for x in p.split("/") if x]
    return "/".join(parts[:min(depth, max(1, len(parts) - 1))])


def host_terms(r, llm_rx):
    """The host re-rank's terms for one index row: [(points, reason, group)]; group H1-H6."""
    shape = json.loads(r["c_shape"] or "{}")
    paths = shape.get("changed_files") or json.loads(r["c_src_paths"] or "[]")
    names = []
    for f, fns in (shape.get("hunk_funcs") or {}).items():
        names += fns
    for u in shape.get("units") or []:
        names.append(u[1])
    ident = " ".join(names + [p.rsplit("/", 1)[-1] for p in paths])
    cwes = cwe_nums(r["cwe_ids"])
    text = (r["summary"] or "")
    try:
        adv = json.loads(r["adv_signals"] or "{}")
    except Exception:
        adv = {}
    terms = []

    def add(p, w, g):
        terms.append((p, w, g))

    # H1 DISTANCE (lesson marshmallow: small libraries are poor hosts; giants do not build offline)
    kb = r["repo_size_kb"]
    if kb is None:
        add(None, "size unknown 0", "H1")
    elif kb < 5000:
        add(-2, "repo <5 MB (no distance)", "H1")
    elif kb < 20000:
        add(0, "repo 5-20 MB", "H1")
    elif kb <= 1_500_000:
        add(2, "repo 20 MB-1.5 GB (distance)", "H1")
    else:
        add(-2, "repo >1.5 GB (offline build risk)", "H1")
    dirs = {top_dir(p) for p in paths}
    if len(dirs) >= 2:
        add(1, f"fix spans {len(dirs)} directories", "H1")

    # H2 RECURRING DECISION = room for undisclosed siblings (S8 proxy; S1 injectability)
    same = r["c_same_check_sites"] or 0
    if same >= 3:
        add(3, f"same check at {same} sites", "H2")
    elif same == 2:
        add(2, "same check at 2 sites", "H2")
    if r["c_bypass_incomplete"]:
        add(2, "earlier fix bypassed (a route was missed before)", "H2")
    elif (r["c_sibling_advisories"] or 0) >= 1:
        add(1, f"{r['c_sibling_advisories']} sibling advisories", "H2")

    # H3 TRAP-SHAPE ROOM from the identifiers the fix touches (cap +3)
    h3, shapes = 0, []
    for k, rx in RX.items():
        if k == "route_protection" and not (cwes & ROUTE_CWES):
            continue
        if rx.search(ident):
            h3 += 1
            shapes.append(k)
    s2b = shape.get("s2b") or {}
    if s2b.get("strict") and s2b.get("diff_dir"):
        h3 += 2
        shapes.append("producer_off_check_path(S2b strict, other dir)")
    elif s2b.get("fires"):
        h3 += 1
        shapes.append("producer_off_check_path(S2b)")
    h3 = min(h3, 3)
    if h3:
        add(h3, "trap room: " + ",".join(shapes), "H3")

    # H4 REASON TO DISMISS (wording proxy, weak)
    m = DISMISS_RX.search(text + " " + " ".join(adv.get("multi_site_text", []) + adv.get("defence_text", [])))
    if m:
        add(1, f"reason-to-dismiss wording '{m.group(0)}'", "H4")

    # H5 WEAKNESS, re-fitted to round 1 (every failed item was A01/A07/unmapped; S5>=2 items 0/9 failed)
    if cwes & A01_A07:
        add(1, "A01/A07 authz/authn decision", "H5")
    if cwes & EASY:
        add(-1, "CWE 78/89 easy to repair", "H5")
    if cwes and cwes <= SATURATED:
        add(-2, "saturated CWE only", "H5")
    if re.search(llm_rx, text):
        add(1, "LLM output drives the action (literature, untested by us)", "H5")

    # H6 CHOKE POINT penalties (async-sib, tomcat-sib abandoned: no room for siblings)
    if r["c_single_sink"]:
        add(-2, "single obvious sink", "H6")
    if r["c_one_site_guard"]:
        add(-1, "one-site added guard", "H6")
    if r["c_single_compact_hunk"] and not same:
        add(-1, "single compact hunk", "H6")
    if (r["n_fix_commits"] or 0) > 4:
        add(-1, ">4 fix commits (hard to pin the vulnerable state)", "H6")
    return terms


def term_text(terms):
    return "; ".join(w if p is None else f"{w} {p:+d}" for p, w, _g in terms)


def term_sum(terms, groups=None):
    return sum(p for p, _w, g in terms if p is not None and (groups is None or g in groups))


def screen_terms(rec, W):
    """Points for one validated screener-v1 record, from screen-weights.json."""
    t = []

    def add(p, w):
        if p:
            t.append((p, w))
    o1 = rec.get("O1_entry_points")
    if isinstance(o1, int):
        add(W["O1_entry_points"]["3plus"] if o1 >= 3 else W["O1_entry_points"]["2"] if o1 == 2 else 0,
            f"O1 {o1} entry points")
    o2 = rec.get("O2_out_of_scope_site") or {}
    if o2.get("kind") not in (None, "none", "unknown"):
        add(W["O2_out_of_scope_site"]["any_kind"], f"O2 {o2['kind']}")
    if str(rec.get("O3_reason_to_dismiss") or "").strip() not in ("", "unknown"):
        add(W["O3_reason_to_dismiss"]["filled"], "O3 reason to dismiss")
    o4 = rec.get("O4_distance") or {}
    files = o4.get("files") if isinstance(o4.get("files"), int) else 0
    pkgs = o4.get("packages") if isinstance(o4.get("packages"), int) else 0
    if files >= 3 or pkgs >= 2:
        add(W["O4_distance"]["files_3plus_or_packages_2plus"], f"O4 distance {files} files/{pkgs} pkgs")
    elif files >= 2 or pkgs >= 1:
        add(W["O4_distance"]["files_2_or_packages_1"], f"O4 distance {files} files/{pkgs} pkgs")
    o5 = rec.get("O5_coupled_behaviour") or {}
    if str(o5.get("what") or "").strip() not in ("", "unknown"):
        add(W["O5_coupled_behaviour"]["filled"], "O5 coupled behaviour")
    if len(rec.get("O6_input_shapes") or []) >= 2:
        add(W["O6_input_shapes"]["2plus"], f"O6 {len(rec['O6_input_shapes'])} input shapes")
    o7 = rec.get("O7_producer") or {}
    if o7.get("kind") in ("schema", "serializer", "cache", "mapper", "config_loader"):
        key = "infrastructure_not_called" if o7.get("check_calls_producer") is False \
            else "infrastructure_called_or_unknown"
        add(W["O7_producer"][key], f"O7 {o7['kind']} ({key})")
    routes = [r for r in rec.get("O8_uncovered_routes") or []
              if isinstance(r, dict) and str(r.get("where") or "").strip() not in ("", "unknown", "path:line")]
    if routes:
        add(W["O8_uncovered_routes"]["2plus"] if len(routes) >= 2 else W["O8_uncovered_routes"]["1"],
            f"O8 {len(routes)} uncovered routes")
        n = sum(1 for r in routes if str(r.get("reason_to_dismiss") or "").strip())
        add(min(n, 2) * W["O8_uncovered_routes"]["per_route_with_reason_to_dismiss_max2"],
            f"O8 {n} routes with a reason to dismiss")
    if any(isinstance(r, dict) and str(r.get("where") or "").strip() not in ("", "path:line")
           for r in rec.get("O8b_injection_room") or []):
        add(W["O8b_injection_room"]["any"], "O8b injection room")
    if rec.get("O9_dos") is True:
        add(W["O9_dos"]["true"], "O9 DoS")
    if (rec.get("O10_build") or {}).get("offline_after_build") is False:
        add(W["O10_build"]["offline_false"], "O10 not offline after build")
    m = rec.get("O11_fix_minutes")
    if isinstance(m, int) and m > 60:
        add(W["O11_fix_minutes"]["over_60"], f"O11 {m} min fix")
    elif isinstance(m, int) and 0 < m < 10:
        add(W["O11_fix_minutes"]["under_10"], f"O11 {m} min fix")
    for flag in rec.get("O12_red_flags") or []:
        add(W["O12_red_flags"].get(flag, 0), f"O12 {flag}")
    if rec.get("O13_recall_risk") == "high":
        add(W["O13_recall_risk"]["high"], "O13 high recall risk")
    if rec.get("pattern_fit") == "none":
        add(W["pattern_fit"]["none"], "pattern_fit none")
    return t


def score_screened(con, llm_rx, screened_dir, weights_path, out_dir):
    sys.path.insert(0, HERE)  # validate_screen.py sits next to this file
    import validate_screen
    W = json.load(open(weights_path))
    rows, skipped = [], []
    for path in sorted(glob.glob(os.path.join(screened_dir, "**", "*.json"), recursive=True)):
        try:
            rec = json.load(open(path, encoding="utf-8"))
        except (OSError, ValueError) as e:
            skipped.append((path, f"unreadable: {e}"))
            continue
        if not isinstance(rec, dict) or "screener_version" not in rec:
            continue  # not a screener record (candidate inputs, run metadata)
        res = validate_screen.validate(rec, validate_screen.schema_for(rec.get("screener_version")))
        if res["errors"]:
            skipped.append((path, "; ".join(res["errors"][:3])))
            continue
        r = con.execute(ROW_SQL + " where e.entry_id = ?", (int(rec["entry_id"]),)).fetchone()
        if r is None:
            skipped.append((path, f"entry_id {rec['entry_id']} not in the index"))
            continue
        ht = host_terms(r, llm_rx)
        rec = validate_screen.normalise(rec)
        st = screen_terms(rec, W)
        weak = [x for x in ht if x[2] == "H5"]
        s = sum(p for p, _w in st)
        rows.append({
            "score_read": s + term_sum(weak), "screen_score": s, "weakness": term_sum(weak),
            "host_score": term_sum(ht), "entry_id": r["entry_id"], "primary_id": r["primary_id"],
            "repo": r["repo"], "model": rec.get("model", ""), "pattern_fit": rec.get("pattern_fit", ""),
            "refs": f"{res['refs_ok']}/{res['refs_total']}",
            "record": os.path.relpath(path, screened_dir),
            "why": "; ".join(f"{w} {p:+d}" for p, w in st) + (" | " + term_text(weak) if weak else ""),
        })
    by_model = Counter()
    for x in sorted(rows, key=lambda x: (x["model"], -x["score_read"], x["entry_id"])):
        by_model[x["model"]] += 1
        x["model_rank"] = by_model[x["model"]]
    rows.sort(key=lambda x: (x["model"], x["model_rank"]))
    cols = ["model", "model_rank", "score_read", "screen_score", "weakness", "host_score", "entry_id",
            "primary_id", "repo", "pattern_fit", "refs", "record", "why"]
    with open(os.path.join(out_dir, "host-rank-screened.tsv"), "w") as f:
        w = csv.DictWriter(f, cols, delimiter="\t", extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    print(f"screened: {len(rows)} records scored with {W['version']}"
          f" (validated: {W['validated']}), {len(skipped)} skipped")
    for p, why in skipped:
        print("  skipped", p, "-", why)


def main(argv=None):
    ap = argparse.ArgumentParser(description="host re-rank v4-draft")
    ap.add_argument("db")
    ap.add_argument("out")
    ap.add_argument("--screened", help="directory of screener-v1 records to score")
    ap.add_argument("--screen-weights", default=os.path.join(HERE, "screen-weights.json"))
    a = ap.parse_args(argv)
    con = sqlite3.connect(f"file:{a.db}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    llm_rx = json.load(open(os.path.join(os.path.dirname(a.db), "..", "weights.json"))) \
        ["weakness"]["llm_in_the_loop"]["summary_regex"]

    out = []
    for r in con.execute(ROW_SQL + " where e.status in ('candidate','shortlisted')").fetchall():
        terms = host_terms(r, llm_rx)
        kb = r["repo_size_kb"]
        out.append({
            "entry_id": r["entry_id"], "primary_id": r["primary_id"], "repo": r["repo"],
            "language": r["language"], "cwes": r["cwe_ids"], "repo_mb": "" if kb is None else round(kb / 1024),
            "v3_score": r["score"], "host_score": term_sum(terms), "used": int(r["repo"] in USED),
            "status": r["status"], "summary": (r["summary"] or "")[:140].replace("\t", " "),
            "why": term_text(terms),
        })

    # ranks
    v3_sorted = sorted(out, key=lambda x: -(x["v3_score"] or -99))
    for i, x in enumerate(v3_sorted, 1):
        x["v3_rank"] = i
    host_sorted = sorted(out, key=lambda x: (-x["host_score"], -(x["v3_score"] or -99), x["entry_id"]))
    for i, x in enumerate(host_sorted, 1):
        x["host_rank"] = i

    cols = ["host_rank", "host_score", "v3_rank", "v3_score", "used", "entry_id", "primary_id", "repo",
            "language", "cwes", "repo_mb", "status", "summary", "why"]
    with open(os.path.join(a.out, "host-rank-all.tsv"), "w") as f:
        w = csv.DictWriter(f, cols, delimiter="\t", extrasaction="ignore")
        w.writeheader()
        w.writerows(host_sorted)

    # diversified shortlist: unused repos, one entry per repo, at most 8 per language
    picked, per_lang, seen = [], Counter(), set()
    for x in host_sorted:
        if x["used"] or x["repo"] in seen or per_lang[x["language"]] >= 8:
            continue
        seen.add(x["repo"]); per_lang[x["language"]] += 1; picked.append(x)
        if len(picked) == 40:
            break
    with open(os.path.join(a.out, "host-shortlist-40.tsv"), "w") as f:
        w = csv.DictWriter(f, cols, delimiter="\t", extrasaction="ignore")
        w.writeheader()
        w.writerows(picked)
    print("pool", len(out), "used-repo entries", sum(x["used"] for x in out))
    print("score dist", sorted(Counter(x["host_score"] for x in out).items()))
    print("languages in top 40", dict(per_lang))

    if a.screened:
        score_screened(con, llm_rx, a.screened, a.screen_weights, a.out)


if __name__ == "__main__":
    main()
