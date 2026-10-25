#!/usr/bin/env python3
"""Pick a fresh batch for the sibling-injection lane: the next N candidates by index score that no
earlier experiment has touched, one per repo, excluded by entry_id AND by repo.

Used sets: common/screener/records (the screened 150), experiments/precision_validation (all arms and inputs),
the shortlists and annotations, the screener calibration hosts, local tasks/*/task.toml, and the VM
side collected into pipelines/sibling/out/vm_used.json (selections, stacking screener/reader jobs, batch1, VM
tasks and build prompts). Filters are the ones common/screener/run_screener.py applies (imported from it).

  python3 -I pipelines/sibling/1-pick/pick.py --n 300
Writes pipelines/sibling/out/screener_jobs.jsonl (run_screener.py job format) and pipelines/sibling/out/exclusion.json.
"""
import argparse, csv, glob, importlib.util, json, os, re, sqlite3
import sys
from pathlib import Path
sys.path.insert(0, str(next(p for p in Path(__file__).resolve().parents if (p / ".cwe-bench-root").is_file()) / "common"))
import paths  # noqa: E402  (repo locations: common/paths.py)

ROOT = str(paths.ROOT)
OUT = str(paths.SIBLING_OUT)
DB = str(paths.CANDIDATES_DB)

spec = importlib.util.spec_from_file_location("run_screener", str(paths.SCREENER_RUNNER))
rs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rs)
norm = rs.norm

GHSA_RE = re.compile(r"GHSA-[0-9a-z]{4}-[0-9a-z]{4}-[0-9a-z]{4}", re.I)


def table_rows(path):
    delim = "\t" if path.endswith(".tsv") else ","
    try:
        return list(csv.DictReader(open(path, encoding="utf-8", errors="replace"), delimiter=delim))
    except Exception:
        return []


def collect():
    ids, repos, by = set(), set(), {}

    def add(key, entry_id=None, repo=None):
        if entry_id not in (None, ""):
            ids.add(str(entry_id).strip())
        if repo:
            repos.add(norm(repo))
        by[key] = by.get(key, 0) + 1

    vm = json.load(open(os.path.join(OUT, "vm_used.json")))
    ids.update(vm["ids"])
    repos.update(vm["repos"])
    by["vm_used"] = len(vm["ids"]) + len(vm["repos"])

    for f in glob.glob(os.path.join(str(paths.SCREENER_RECORDS), "*.json")) + \
             glob.glob(os.path.join(str(paths.PRECISION_VALIDATION), "results", "screener_v2", "*.json")):
        if os.path.basename(f).startswith(("_", "._")) or f.endswith(".run.json"):
            continue
        try:
            add("screener_records", os.path.splitext(os.path.basename(f))[0], json.load(open(f)).get("repo"))
        except Exception:
            pass

    tables = glob.glob(os.path.join(str(paths.PRECISION_VALIDATION), "results", "*.csv")) + [
        os.path.join(ROOT, "sourcer", "shortlist-20.tsv"),
        os.path.join(ROOT, "sourcer", "stacking-shortlist.tsv"),
        os.path.join(ROOT, "sourcer", "review", "annotations.tsv"),
        os.path.join(str(paths.SIBLING_OUT), "rerank-batch1-20261017", "host-rank-screened.tsv")]
    for f in tables:
        for r in table_rows(f):
            add(os.path.basename(f), r.get("entry_id"), r.get("repo"))

    for f in glob.glob(os.path.join(str(paths.PRECISION_VALIDATION), "inputs", "*.jsonl")):
        for l in open(f):
            if l.strip():
                j = json.loads(l)
                add(os.path.basename(f), j.get("entry_id"), j.get("repo"))

    for t in glob.glob(os.path.join(ROOT, "tasks", "*", "task.toml")):
        m = re.search(r'^\s*repo\s*=\s*"([^"]+)"', open(t, errors="replace").read(), re.M)
        if m:
            add("local_task_toml", repo=m.group(1))

    # calibration hosts are listed by advisory (GHSA), resolved to entries/repos through the index in main()
    prompt = open(str(paths.SCREENER_PROMPT), errors="replace").read()
    table = prompt[prompt.find("### Calibration set"):prompt.find("Added in v2")]
    ghsas = {g.upper() for g in GHSA_RE.findall(table)}
    by["calibration_ghsas"] = len(ghsas)

    repos.discard("")
    return ids, repos, ghsas, by


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=300)
    a = ap.parse_args()
    ids, repos, ghsas, by = collect()

    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    hits = 0
    for r in con.execute("select entry_id, repo, ids from entries"):
        if ghsas & set((r["ids"] or "").upper().split()):
            ids.add(str(r["entry_id"]))
            hits += 1
    by["calibration_entries"] = hits
    for r in con.execute(f"select entry_id, repo from entries where entry_id in ({','.join('?' * len(ids))})",
                         sorted(int(i) for i in ids if i.isdigit())):
        repos.add(norm(r["repo"]))   # an excluded entry excludes its whole repo

    out, seen, why = [], set(), {}
    for r in con.execute("select * from entries where status='candidate' order by score desc"):
        repo = norm(r["repo"])
        cwes = set((r["cwe_ids"] or "").split())
        reason = ("no repo" if not repo else "used id" if str(r["entry_id"]) in ids else "used repo" if repo in repos
                  else "repo taken" if repo in seen else "no fix commit" if not (r["fix_commits"] or r["fix_commit"])
                  else "DoS only" if cwes and cwes <= rs.DOS else "repo > 1.5 GB" if (r["repo_size_kb"] or 0) > 1_500_000
                  else None)
        if reason:
            why[reason] = why.get(reason, 0) + 1
            continue
        row = {k: r[k] for k in r.keys() if k in ("entry_id", "ids", "cve", "repo", "cwe_ids", "summary", "parent_commit",
                                                 "fix_commits", "language", "score", "published")
               or k.startswith("c_")}
        out.append(dict(id=f"scr-{r['entry_id']}", entry_id=str(r["entry_id"]), repo=repo, row=row))
        seen.add(repo)
        if len(out) >= a.n:
            break

    os.makedirs(OUT, exist_ok=True)
    open(os.path.join(OUT, "screener_jobs.jsonl"), "w").write("".join(json.dumps(j, default=str) + "\n" for j in out))
    json.dump({"ids": sorted(ids), "repos": sorted(repos), "by_source": by}, open(os.path.join(OUT, "exclusion.json"), "w"), indent=1)
    print(f"excluded: {len(ids)} entry ids, {len(repos)} repos  (sources: {by})")
    print(f"skipped while picking: {why}")
    print(f"picked {len(out)} -> pipelines/sibling/out/screener_jobs.jsonl")
    if out:
        print(f"score range: {out[0]['row']['score']} .. {out[-1]['row']['score']}")
        for j in out[:10]:
            print(f"  {j['id']:12} {j['repo']:45} score={j['row']['score']}")


if __name__ == "__main__":
    main()
