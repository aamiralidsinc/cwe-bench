"""Round-2 HOST re-rank of the CWE-bench candidate pool (read-only, offline).

Reads cwe-bench/sourcer/index/candidates.sqlite read-only; writes TSVs to argv[2].
Every component is tied to a round-1 lesson (see LESSON comments). No network.
"""
import json, re, sqlite3, sys, csv, os
from collections import Counter

DB, OUT = sys.argv[1], sys.argv[2]
con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
con.row_factory = sqlite3.Row

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


def cwe_nums(s):
    return {int(x) for x in re.findall(r"CWE-(\d+)", s or "")}


def top_dir(p, depth=2):
    parts = [x for x in p.split("/") if x]
    return "/".join(parts[:min(depth, max(1, len(parts) - 1))])


rows = con.execute("""
  select e.*, c.shape as c_shape, c.src_paths as c_src_paths
  from entries e left join commits c on c.repo = e.repo and c.full_sha = e.fix_commit
  where e.status in ('candidate','shortlisted')""").fetchall()

out = []
for r in rows:
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
    pts, why = 0, []

    def add(p, w):
        nonlocal_pts[0] += p
        why.append(f"{w} {p:+d}")
    nonlocal_pts = [0]

    # H1 DISTANCE (lesson marshmallow: small libraries are poor hosts; giants do not build offline)
    kb = r["repo_size_kb"]
    if kb is None:
        why.append("size unknown 0")
    elif kb < 5000:
        add(-2, "repo <5 MB (no distance)")
    elif kb < 20000:
        add(0, "repo 5-20 MB")
    elif kb <= 1_500_000:
        add(2, "repo 20 MB-1.5 GB (distance)")
    else:
        add(-2, "repo >1.5 GB (offline build risk)")
    dirs = {top_dir(p) for p in paths}
    if len(dirs) >= 2:
        add(1, f"fix spans {len(dirs)} directories")

    # H2 RECURRING DECISION = room for undisclosed siblings (S8 proxy; S1 injectability)
    same = r["c_same_check_sites"] or 0
    if same >= 3:
        add(3, f"same check at {same} sites")
    elif same == 2:
        add(2, "same check at 2 sites")
    if r["c_bypass_incomplete"]:
        add(2, "earlier fix bypassed (a route was missed before)")
    elif (r["c_sibling_advisories"] or 0) >= 1:
        add(1, f"{r['c_sibling_advisories']} sibling advisories")

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
        add(h3, "trap room: " + ",".join(shapes))

    # H4 REASON TO DISMISS (wording proxy, weak)
    m = DISMISS_RX.search(text + " " + " ".join(adv.get("multi_site_text", []) + adv.get("defence_text", [])))
    if m:
        add(1, f"reason-to-dismiss wording '{m.group(0)}'")

    # H5 WEAKNESS, re-fitted to round 1 (every failed item was A01/A07/unmapped; S5>=2 items 0/9 failed)
    if cwes & A01_A07:
        add(1, "A01/A07 authz/authn decision")
    if cwes & EASY:
        add(-1, "CWE 78/89 easy to repair")
    if cwes and cwes <= SATURATED:
        add(-2, "saturated CWE only")
    if re.search(json.load(open(os.path.join(os.path.dirname(DB), "..", "weights.json")))
                 ["weakness"]["llm_in_the_loop"]["summary_regex"], text):
        add(1, "LLM output drives the action (literature, untested by us)")

    # H6 CHOKE POINT penalties (async-sib, tomcat-sib abandoned: no room for siblings)
    if r["c_single_sink"]:
        add(-2, "single obvious sink")
    if r["c_one_site_guard"]:
        add(-1, "one-site added guard")
    if r["c_single_compact_hunk"] and not same:
        add(-1, "single compact hunk")
    if (r["n_fix_commits"] or 0) > 4:
        add(-1, ">4 fix commits (hard to pin the vulnerable state)")

    out.append({
        "entry_id": r["entry_id"], "primary_id": r["primary_id"], "repo": r["repo"],
        "language": r["language"], "cwes": r["cwe_ids"], "repo_mb": "" if kb is None else round(kb / 1024),
        "v3_score": r["score"], "host_score": nonlocal_pts[0], "used": int(r["repo"] in USED),
        "status": r["status"], "summary": (text or "")[:140].replace("\t", " "),
        "why": "; ".join(why),
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
with open(os.path.join(OUT, "host-rank-all.tsv"), "w") as f:
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
with open(os.path.join(OUT, "host-shortlist-40.tsv"), "w") as f:
    w = csv.DictWriter(f, cols, delimiter="\t", extrasaction="ignore")
    w.writeheader()
    w.writerows(picked)
print("pool", len(out), "used-repo entries", sum(x["used"] for x in out))
print("score dist", sorted(Counter(x["host_score"] for x in out).items()))
print("languages in top 40", dict(per_lang))
