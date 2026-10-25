#!/usr/bin/env python3
"""The sibling-injection lane for the sibling2 batch: pipeline/make_pool.py and pipeline/prepare_lane.py
logic, unchanged, with every input and output redirected into sibling2/ so batch-1's files
(build/pipeline/pool.jsonl, selection_*.json, specs_*, slugs_*.txt) are never touched.

  python3 -I sibling2/lane.py pool                 # sibling2/out/screener -> sibling2/out/pipeline/pool.jsonl
  bash sibling2/select.sh deepseek                 # driver picks -> sibling2/out/pipeline/selection_deepseek.json
  python3 -I sibling2/lane.py prepare deepseek     # -> build/<slug>/BUILD-PROMPT.md + sibling2/out/pipeline/slugs_deepseek.txt
"""
import importlib.util, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RECS = os.path.join(ROOT, "sibling2", "out", "screener")
PIPE = os.path.join(ROOT, "sibling2", "out", "pipeline")


def load(name, rel):
    spec = importlib.util.spec_from_file_location(name, os.path.join(ROOT, rel))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def pool():
    mp = load("make_pool", "pipeline/make_pool.py")
    mp.RECS, mp.OUT = RECS, os.path.join(PIPE, "pool.jsonl")
    mp.main()


def prepare(driver):
    pl = load("prepare_lane", "pipeline/prepare_lane.py")      # for PLAN and VM_ROOT, read as is
    bp = load("build_prepare", "sourcer/rerank-v4-draft/build_prepare.py")
    bp.RECORDS = RECS
    suffix = "ds" if driver == "deepseek" else "mm"
    sel = json.load(open(os.path.join(PIPE, f"selection_{driver}.json")))
    specdir = os.path.join(PIPE, f"specs_{driver}")
    os.makedirs(specdir, exist_ok=True)
    slugs = []
    for row in sel:
        eid = str(row["entry_id"])
        rp = os.path.join(RECS, f"{eid}.json")
        if not os.path.exists(rp):
            print("skip (no record):", eid); continue
        r = json.load(open(rp))
        repo = r.get("repo", "")
        slug = f"{repo.split('/')[-1].lower().replace('_', '-')}-{suffix}"
        if os.path.exists(os.path.join(ROOT, "build", slug)):
            print(f"skip (build/{slug} already exists, would overwrite another batch):", eid); continue
        pf = r.get("pattern_fit") if r.get("pattern_fit") in ("A", "B", "A+B") else "A+B"
        adv = r.get("advisory_ids"); adv = adv if isinstance(adv, str) else json.dumps(adv)
        fc = r.get("fix_commits")
        fc = fc if isinstance(fc, list) else ([fc] if fc else ["(none given)"])
        spec = {"slug": slug, "entry_id": eid, "pattern": pf, "track": "injected",
                "advisory": f"{adv}; {repo}; {r.get('O9_family', '')}",
                "vuln_commit": str(r.get("pinned_commit", "(see record)")),
                "fix_commits": fc, "design_plan": pl.PLAN, "host_notes": "none",
                "project_root": pl.VM_ROOT}
        sp = os.path.join(specdir, f"{slug}.json")
        json.dump(spec, open(sp, "w"), indent=1)
        try:
            bp.main(sp)
            slugs.append(slug)
        except Exception as e:
            print("prepare failed:", slug, e)
    listf = os.path.join(PIPE, f"slugs_{driver}.txt")
    open(listf, "w").write("\n".join(slugs) + "\n")
    print(f"{driver}: prepared {len(slugs)} BUILD-PROMPTs -> {listf}")


if __name__ == "__main__":
    os.makedirs(PIPE, exist_ok=True)
    {"pool": lambda: pool(), "prepare": lambda: prepare(sys.argv[2])}[sys.argv[1]]()
