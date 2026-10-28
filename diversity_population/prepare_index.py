#!/usr/bin/env python3
"""Prepare the experiment's copy of the index so the copied sourcer stages work on the source pool only.

In out/index/candidates.sqlite (a copy of the sources2 index; the originals are never opened for writing):
- pool entries (out/source_pool.sqlite) get status 'pending' and no reject reason;
- every other entry gets status 'deferred'. The copied stages never select 'deferred' rows, but classify still
  counts them as sibling advisories, and can move a shared fix commit from a deferred owner to a pool entry.
  Their reject_reason is kept, so withdrawn advisories stay out of the sibling count.
- the original status of every changed row goes into the table div_original_status.

It also copies cached patches, commit parents and repo metadata for the pool's repos into the experiment's data
folder, so nothing is fetched twice. Run it once; a second run refuses unless --force.

  python3 -I diversity_population/prepare_index.py
"""
import argparse, os, shutil, sqlite3
from pathlib import Path

HERE = Path(__file__).resolve().parent
INDEX = HERE / "out/index/candidates.sqlite"
POOL = HERE / "out/source_pool.sqlite"
DATA = Path(os.path.expanduser("~/.tb-graders/cwe/diversity-data"))
CACHES = [Path(os.path.expanduser(p)) for p in ("~/.tb-graders/cwe/sources2-data", "~/.tb-graders/cwe/sourcer-data")]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    db = sqlite3.connect(INDEX)
    if db.execute("select count(*) from sqlite_master where name='div_original_status'").fetchone()[0] and not a.force:
        raise SystemExit("already prepared (div_original_status exists); use --force to redo")
    pool = sqlite3.connect(f"file:{POOL}?mode=ro", uri=True)
    ids = sorted({r[0] for r in pool.execute("select entry_id from pool")})
    repos = sorted({r[0] for r in pool.execute("select repo from pool")})
    db.execute("create table if not exists div_original_status (entry_id integer primary key, status text, "
               "reject_reason text)")
    db.execute("create temp table p (entry_id integer primary key)")
    db.executemany("insert into p values (?)", [(i,) for i in ids])
    db.execute("insert or ignore into div_original_status select entry_id, status, reject_reason from entries "
               "where status != 'deferred' or entry_id in (select entry_id from p)")
    n_other = db.execute("update entries set status='deferred' where entry_id not in (select entry_id from p) "
                         "and status != 'deferred'").rowcount
    n_pool = db.execute("update entries set status='pending', reject_reason=null "
                        "where entry_id in (select entry_id from p)").rowcount
    db.commit()
    print(f"pool entries set pending: {n_pool}; other entries set deferred: {n_other}")

    copied = {"patches": 0, "repo-meta": 0, "commit-parents": 0}
    for repo in repos:
        owner, name = repo.split("/", 1)
        for c in CACHES:
            src = c / "patches" / owner / name
            if src.is_dir():
                dst = DATA / "patches" / owner / name
                dst.mkdir(parents=True, exist_ok=True)
                for f in src.glob("*.patch.gz"):
                    if not (dst / f.name).exists():
                        shutil.copy2(f, dst / f.name); copied["patches"] += 1
            key = repo.replace("/", "__")
            for sub in ("repo-meta", "commit-parents"):
                d = c / sub
                if not d.is_dir():
                    continue
                for f in d.glob(key + ("*.json" if sub == "commit-parents" else ".json")):
                    (DATA / sub).mkdir(parents=True, exist_ok=True)
                    if not (DATA / sub / f.name).exists():
                        shutil.copy2(f, DATA / sub / f.name); copied[sub] += 1
    print("cache files copied:", copied)


if __name__ == "__main__":
    main()
