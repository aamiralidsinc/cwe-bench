#!/usr/bin/env python3
"""Stacking copy of common/builder/build_prepare.py (the original is untouched).

Fills common/builder/TASK-BUILD-PROMPT-v1.md (read as is) for ONE stacked candidate, from the stacking
reader's record instead of a screener record, then appends pipelines/stacking/2-prepare/STACKING-BUILD-ADDENDUM.md with
the reader record filled in. Writes <out-root>/build/<slug>/BUILD-PROMPT.md, which the unchanged
common/launch/run_build.sh / common/launch/drive.sh then run.

  python3 -I pipelines/stacking/2-prepare/build_prepare_stack.py JOB_ID --project-root /home/<user>/cwe-bench [--out-root DIR]
JOB_ID: an id from pipelines/stacking/out/reader_jobs.jsonl that has pipelines/stacking/out/reader/<JOB_ID>.json.
Slug: stk-<repo-name>-<short-id>; its one-bug control is <slug>-control (built by the same builder).
"""
import argparse, json, os, re
import sys
from pathlib import Path
sys.path.insert(0, str(next(p for p in Path(__file__).resolve().parents if (p / ".cwe-bench-root").is_file()) / "common"))
import paths  # noqa: E402  (repo locations: common/paths.py)

ROOT = str(paths.ROOT)
TEMPLATE = str(paths.BUILD_TEMPLATE)
ADDENDUM = os.path.join(str(paths.STACKING), "2-prepare", "STACKING-BUILD-ADDENDUM.md")
MARK = "---8<---"


def slug_for(job):
    name = re.sub(r"[^a-z0-9]+", "-", job["repo"].split("/")[-1].lower()).strip("-")[:24]
    short = re.sub(r"[^a-z0-9]+", "", job["id"].split("-", 1)[-1].lower())[:8]
    return f"stk-{name}-{short}"


def sites(traps, origins):
    rows = []
    for t in traps:
        if t.get("origin") in origins:
            for loc in t.get("locations") or ["(location in the reader record)"]:
                rows.append(f"  - {loc} — {t['id']} {t.get('mechanism', '')} "
                            f"(reason to dismiss: {t.get('reason_to_dismiss') or 'none'})")
    return "\n".join(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("job_id")
    ap.add_argument("--project-root", required=True, help="cwe-bench path ON THE BUILD MACHINE")
    ap.add_argument("--out-root", default=ROOT, help="where build/<slug>/BUILD-PROMPT.md is written")
    a = ap.parse_args()
    jobs = {j["id"]: j for j in (json.loads(l) for l in open(os.path.join(str(paths.STACKING_OUT), "reader_jobs.jsonl")) if l.strip())}
    job = jobs[a.job_id]
    rec = json.load(open(os.path.join(str(paths.STACKING_OUT), "reader", f"{a.job_id}.json")))
    if not rec.get("usable"):
        raise SystemExit(f"{a.job_id}: the reader marked this candidate not usable; not preparing a build")
    slug = slug_for(job)
    traps = rec.get("traps") or []
    design = rec.get("design") or {}
    cand = job.get("candidate") or {}
    advisory = "; ".join(x for x in (cand.get("a"), cand.get("b"), cand.get("entry"), cand.get("family")) if x) or job["repo"]
    fixes = [c for c in job.get("pin_from") or []] + [c for c in str(cand.get("b_fix", "")).split(";") if c]
    fix_sites = sites(traps, {"advisory_route", "published_fix_far_site"}) or "  (see the reader record)"
    uncovered = sites(traps, {"uncovered_upstream"}) or "none"
    plan = (f"TRACK = STACKED ({rec.get('pattern')}). Build the stacked design the reader chose: traps "
            f"{', '.join(design.get('traps') or [])}. Why: {design.get('why', '')} "
            "Follow the stacked-task rules appended at the end of this prompt; they add to the rules above.")
    notes = ("Reader fairness risks (resolve each in the report's contracts or the tests): "
             + " | ".join(rec.get("fairness_risks") or ["none"])
             + ". Conflicts the reader found: "
             + " | ".join(str(c.get("what", c)) if isinstance(c, dict) else str(c) for c in (rec.get("conflicts") or [])) or "none")
    body = open(TEMPLATE, encoding="utf-8").read().split(MARK)[1].strip("\n") + "\n"
    out = (body.replace("{{SLUG}}", slug).replace("{{PATTERN}}", "A+B").replace("{{TRACK}}", "stacked")
               .replace("{{ADVISORY}}", advisory).replace("{{VULN_COMMIT}}", str(rec.get("pinned_commit", "")))
               .replace("{{FIX_COMMITS}}", ", ".join(fixes) or "(see the reader record)")
               .replace("{{SCREEN_RECORD}}", json.dumps(rec, indent=1)).replace("{{FIX_SITES}}", fix_sites)
               .replace("{{UNCOVERED_ROUTES}}", uncovered).replace("{{DESIGN_PLAN}}", plan)
               .replace("{{HOST_NOTES}}", notes).replace("{{PROJECT_ROOT}}", a.project_root))
    add = open(ADDENDUM, encoding="utf-8").read().split(MARK, 1)[1].strip("\n")
    out += "\n\n" + add.replace("{{READER_RECORD}}", f"`{a.project_root}/pipelines/stacking/out/reader/{a.job_id}.json`") + "\n"
    out += (f"\nStacked task slug: `{slug}`. Control task slug: `{slug}-control`. "
            f"Manifest `stacking.reader_record`: `pipelines/stacking/out/reader/{a.job_id}.json`.\n")
    # only the template's own slots: record text may hold literal {{...}} (nuclei templates use {{ENV}})
    slots = set(re.findall(r"\{\{[A-Z_]+\}\}", body + add))
    left = [x for x in slots if x in out]
    if left:
        raise SystemExit(f"unfilled slots: {sorted(set(left))}")
    d = os.path.join(a.out_root, "build", slug)
    os.makedirs(d, exist_ok=True)
    open(os.path.join(d, "BUILD-PROMPT.md"), "w").write(out)
    print(f"{a.job_id} -> build/{slug}/BUILD-PROMPT.md ({len(out.split())} words); control {slug}-control")


if __name__ == "__main__":
    main()
