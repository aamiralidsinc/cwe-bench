#!/usr/bin/env python3
"""Build the experiment's source pool: the newest N distinct repos per pattern, in reverse chronological order.

Reads (read-only):
- the main index, sourcer/index/candidates.sqlite: entries with status 'deferred' (outside the main window);
- the sources2 index, sourcer/reserve/index/candidates.sqlite: new-source entries only (entry_id above the main
  index's maximum), with status 'pending' or 'deferred'.

Excludes:
- every repo that has a candidate in the main pipeline's pool (main index status 'candidate' or 'shortlisted');
- every repo already built by any pipeline (--built, one owner/name per line).

Date used for ordering ("date"):
- the earliest fetched fix-commit date when known (date_basis 'fix'), else the advisory's published date
  ('published');
- reason: some new-source records are old bugs that only recently got a CVE (for example a 2017 Discourse bug
  published in 2026-10), so the published date alone overstates recency.

Unit:
- one row per (pattern, repo), keeping the repo's newest advisory for that pattern;
- an advisory with several CWEs can appear under several patterns (the column n_patterns says how many).

Writes out/source_pool.sqlite with three tables:
- pool: the first --per-pattern rows of each pattern;
- pattern_depth: per pattern, how far back the list goes;
- meta: how the pool was built.

  python3 -I diversity_population/build_source_pool.py --built diversity_population/out/built_repos_20261027.txt
"""
import argparse, collections, datetime, json, re, sqlite3
from email.utils import parsedate_to_datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
MAIN = ROOT / "sourcer/index/candidates.sqlite"
RESERVE = ROOT / "sourcer/reserve/index/candidates.sqlite"


def ro(p):
    return sqlite3.connect(f"file:{p}?mode=ro", uri=True)


def cwes(s):
    return {int(x) for x in re.findall(r"CWE-(\d+)", s or "")}


def fix_dates(con, min_id=0):
    out = {}
    for eid, d in con.execute("select entry_id, commit_date from commits where fetch_status='ok' "
                              "and commit_date is not null and entry_id > ?", (min_id,)):
        try:
            x = parsedate_to_datetime(d).date().isoformat()
        except Exception:
            continue
        out[eid] = min(out.get(eid, x), x)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--built", required=True)
    ap.add_argument("--per-pattern", type=int, default=50)
    ap.add_argument("--out", default=str(HERE / "out/source_pool.sqlite"))
    a = ap.parse_args()

    patterns = json.load(open(HERE / "patterns.json"))["patterns"]
    built = {l.strip().lower() for l in open(a.built) if l.strip()}
    m = ro(MAIN)
    main_pool = {r for (r,) in m.execute("select repo from entries where status in ('candidate','shortlisted')") if r}
    main_max = m.execute("select max(entry_id) from entries").fetchone()[0]
    cols = "entry_id, primary_id, ids, repo, published, cwe_ids, ecosystems, status, fix_commit, n_fix_commits, summary"
    rows = [("main",) + r for r in m.execute(f"select {cols} from entries where status='deferred'")]
    rs = ro(RESERVE)
    rows += [("sources2",) + r for r in rs.execute(
        f"select {cols} from entries where entry_id > ? and status in ('pending','deferred')", (main_max,))]
    fd = {("main", k): v for k, v in fix_dates(m).items()}
    fd.update({("sources2", k): v for k, v in fix_dates(rs, main_max).items()})

    def eff(r):
        f = fd.get((r[0], r[1]))
        p = (r[5] or "")[:10]
        return (f, "fix") if f and f < p else (p, "published")

    excluded = collections.Counter()
    by_pattern = {p["id"]: {} for p in patterns}
    for r in rows:
        src, eid, pid, ids, repo, pub, cw, eco, st, fix, nfix, summ = r
        repo = (repo or "").lower()
        if not repo or not pub:
            excluded["no repo or date"] += 1
            continue
        if repo in built:
            excluded["repo built"] += 1
            continue
        if repo in main_pool:
            excluded["repo in main pool"] += 1
            continue
        c = cwes(cw)
        for p in patterns:
            if c & set(p["cwes"]):
                cur = by_pattern[p["id"]].get(repo)
                d = eff(r)
                if cur is None or d[0] > cur[1][0]:
                    by_pattern[p["id"]][repo] = (r, d)

    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        out.unlink()
    o = sqlite3.connect(out)
    o.executescript("""
    create table pool (pattern text, rank integer, source text, entry_id integer, primary_id text, ids text,
        repo text, date text, date_basis text, published text, fix_date text, cwe_ids text, ecosystems text, source_status text, slice text,
        fix_commit text, n_fix_commits integer, summary text, n_patterns integer, primary key (pattern, rank));
    create table pattern_depth (pattern text primary key, name text, owasp text, repos_available integer,
        listed integer, newest text, oldest_listed text, date_10th text, date_25th text, date_50th text,
        from_main integer, from_sources2 integer);
    create table meta (k text primary key, v text);
    """)

    def slice_of(src, pub):
        if pub >= "2025-01-01":
            return "D1" if src == "main" else "D2"
        return "older-main" if src == "main" else "older-sources2"

    listed = {}
    for p in patterns:
        items = sorted(by_pattern[p["id"]].values(), key=lambda x: x[1][0], reverse=True)
        listed[p["id"]] = items[: a.per_pattern]
    count = collections.Counter(x[0][4].lower() + "|" + str(x[0][1]) for v in listed.values() for x in v)
    for p in patterns:
        items = listed[p["id"]]
        for i, (r, (dt, basis)) in enumerate(items, 1):
            src, eid, pid, ids, repo, pub, cw, eco, st, fix, nfix, summ = r
            o.execute("insert into pool values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                      (p["id"], i, src, eid, pid, ids, repo.lower(), dt, basis, pub[:10], fd.get((src, eid)),
                       cw, eco, st, slice_of(src, dt),
                       fix, nfix, (summ or "")[:300], count[repo.lower() + "|" + str(eid)]))
        d = [x[1][0] for x in items]
        pick = lambda k: d[k - 1] if len(d) >= k else None
        o.execute("insert into pattern_depth values (?,?,?,?,?,?,?,?,?,?,?,?)",
                  (p["id"], p["name"], p["owasp"], len(by_pattern[p["id"]]), len(items), d[0] if d else None,
                   d[-1] if d else None, pick(10), pick(25), pick(50),
                   sum(x[0][0] == "main" for x in items), sum(x[0][0] == "sources2" for x in items)))
    meta = {"built_utc": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%MZ"),
            "per_pattern": a.per_pattern, "main_index": str(MAIN), "reserve_index": str(RESERVE),
            "main_max_entry_id": main_max, "built_repos_file": a.built, "built_repos": len(built),
            "main_pool_repos": len(main_pool), "rows_read": len(rows), "excluded": dict(excluded),
            "rows_with_fix_date": len(fd)}
    for k, v in meta.items():
        o.execute("insert into meta values (?,?)", (k, json.dumps(v)))
    o.commit()
    print(json.dumps(meta, indent=1))
    for r in o.execute("select pattern, repos_available, listed, newest, date_10th, date_25th, date_50th, "
                       "from_main, from_sources2 from pattern_depth order by date_50th desc"):
        print("\t".join(str(x) for x in r))


if __name__ == "__main__":
    main()
