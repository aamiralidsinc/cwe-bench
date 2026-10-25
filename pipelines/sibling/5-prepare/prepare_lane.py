#!/usr/bin/env python3
"""Turn a lane's selection into lane-namespaced BUILD-PROMPTs.

For each chosen entry_id, build a build_prepare spec with:
  - a lane-namespaced slug (repo with '/'->'-', lowercased, + '-ds'/'-mm');
  - the SAME constant self-design plan (pipelines/sibling/5-prepare/SELFDESIGN-PLAN.md) for every candidate,
    so the DRIVER model designs the injection itself (no per-candidate human plan);
  - track=injected, pattern from the record (A/B/A+B, else A+B);
  - the VM project root.
Then runs common/builder/build_prepare.py to write build/<slug>/BUILD-PROMPT.md, and lists the slugs in
build/pipeline/slugs_<driver>.txt.

  python3 -I pipelines/sibling/5-prepare/prepare_lane.py <deepseek|mimo>
"""
import json, os, subprocess, sys
from pathlib import Path
sys.path.insert(0, str(next(p for p in Path(__file__).resolve().parents if (p / ".cwe-bench-root").is_file()) / "common"))
import paths  # noqa: E402  (repo locations: common/paths.py)

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = str(paths.ROOT)
RECS = str(paths.SCREENER_RECORDS)
PREPARE = str(paths.BUILD_PREPARE)
PLAN = open(os.path.join(HERE, "SELFDESIGN-PLAN.md")).read().strip()
VM_ROOT = "/home/mara/cwe-bench"


def main(driver):
    suffix = "ds" if driver == "deepseek" else "mm"
    sel = json.load(open(os.path.join(str(paths.BUILD_PIPELINE), f"selection_{driver}.json")))
    slugs, specdir = [], os.path.join(str(paths.BUILD_PIPELINE), f"specs_{driver}")
    os.makedirs(specdir, exist_ok=True)
    for row in sel:
        eid = str(row["entry_id"])
        rp = os.path.join(RECS, f"{eid}.json")
        if not os.path.exists(rp):
            print("skip (no record):", eid); continue
        r = json.load(open(rp))
        repo = r.get("repo", "")
        base = repo.split("/")[-1].lower().replace("_", "-")
        slug = f"{base}-{suffix}"
        pf = r.get("pattern_fit") if r.get("pattern_fit") in ("A", "B", "A+B") else "A+B"
        adv = r.get("advisory_ids"); adv = adv if isinstance(adv, str) else json.dumps(adv)
        fc = r.get("fix_commits")
        fc = fc if isinstance(fc, list) else ([fc] if fc else ["(none given)"])
        spec = {"slug": slug, "entry_id": eid, "pattern": pf, "track": "injected",
                "advisory": f"{adv}; {repo}; {r.get('O9_family','')}",
                "vuln_commit": str(r.get("pinned_commit", "(see record)")),
                "fix_commits": fc, "design_plan": PLAN, "host_notes": "none",
                "project_root": VM_ROOT}
        sp = os.path.join(specdir, f"{slug}.json")
        json.dump(spec, open(sp, "w"), indent=1)
        rc = subprocess.run([sys.executable, "-I", PREPARE, sp]).returncode
        if rc == 0:
            slugs.append(slug)
        else:
            print("prepare failed:", slug)
    listf = os.path.join(str(paths.BUILD_PIPELINE), f"slugs_{driver}.txt")
    open(listf, "w").write("\n".join(slugs) + "\n")
    print(f"{driver}: prepared {len(slugs)} BUILD-PROMPTs -> {listf}")


if __name__ == "__main__":
    main(sys.argv[1])
