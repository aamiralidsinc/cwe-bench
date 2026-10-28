#!/usr/bin/env python3
"""Add the top-up entries (out/source_pool_ext.sqlite, table ext) to the experiment's index copy.

Sets those entries to 'pending' (no reject reason) so the copied sourcer stages pick them up, keeps their original
status in div_original_status, and copies cached patches, commit parents and repo metadata for their repos into the
experiment's data folder. Entries already in the pool are not touched.

  python3 -I diversity_population/extend_index.py
"""
import os, shutil, sqlite3
from pathlib import Path

HERE = Path(__file__).resolve().parent
db = sqlite3.connect(HERE / "out/index/candidates.sqlite")
ext = sqlite3.connect(f"file:{HERE / 'out/source_pool_ext.sqlite'}?mode=ro", uri=True)
ids = sorted({r[0] for r in ext.execute("select entry_id from ext")})
repos = sorted({r[0] for r in ext.execute("select repo from ext")})
db.execute("create temp table p (entry_id integer primary key)")
db.executemany("insert into p values (?)", [(i,) for i in ids])
db.execute("insert or ignore into div_original_status select e.entry_id, o.status, o.reject_reason from entries e "
           "join p using (entry_id) left join div_original_status o using (entry_id) where 0")  # schema check only
# original status = the status in the source index before prepare_index.py set everything else to 'deferred'
src = sqlite3.connect(f"file:{HERE.parent / 'sourcer/reserve/index/candidates.sqlite'}?mode=ro", uri=True)
orig = {r[0]: (r[1], r[2]) for r in src.execute(
    "select entry_id, status, reject_reason from entries where entry_id in (%s)" % ",".join(map(str, ids)))}
db.executemany("insert or ignore into div_original_status values (?,?,?)",
               [(i, orig[i][0], orig[i][1]) for i in ids if i in orig])
n = db.execute("update entries set status='pending', reject_reason=null where entry_id in (select entry_id from p) "
               "and status='deferred'").rowcount
db.commit()
print(f"top-up entries set pending: {n} of {len(ids)}")
DATA = Path(os.path.expanduser("~/.tb-graders/cwe/diversity-data"))
copied = 0
for repo in repos:
    owner, name = repo.split("/", 1)
    for c in (Path(os.path.expanduser("~/.tb-graders/cwe/sources2-data")), Path(os.path.expanduser("~/.tb-graders/cwe/sourcer-data"))):
        s = c / "patches" / owner / name
        if s.is_dir():
            d = DATA / "patches" / owner / name; d.mkdir(parents=True, exist_ok=True)
            for f in s.glob("*.patch.gz"):
                if not (d / f.name).exists():
                    shutil.copy2(f, d / f.name); copied += 1
print("cached patches copied:", copied)
