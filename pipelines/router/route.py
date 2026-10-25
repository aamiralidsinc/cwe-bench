#!/usr/bin/env python3
"""Router for the three-step scale run (docs/PIPELINE-3STEP-DESIGN.md). Run on the VM from ~/cwe-bench.

  step 1  stacking-batch  stacking's batch: the best usable stacked design per unbuilt repo, from the DeepSeek reader
                          (pipelines/stacking/out/stack_scores.tsv + reader_jobs_ds.jsonl + reader-ds/), then its
                          BUILD-PROMPTs. Writes pipelines/stacking/out/<name>.{tsv,txt}; registers the batch.
  step 2  step2           sibling pool: every DeepSeek screen record (pipelines/stacking/out/screener-ds/) whose repo
                          stacking did NOT take (any registered batch, any stk- build) and that is not built already.
                          Writes pipelines/router/out/step2/screener/.
  step 3  step3           sibling on solved stacked tasks: every task of a registered stacking batch that ANY model
                          solved (ledger: a SOLVED cell; this includes single-model breakers, owner decision
                          2026-10-25) is routed once: its repo's DeepSeek screen record goes to
                          pipelines/router/out/step3/screener/ and its entry to step3/pipeline/selection_deepseek.json.
                          Re-run it whenever new stacked verdicts arrive (regenerate the ledger first).
          status          what is where.

  python3 -I pipelines/router/route.py stacking-batch --name batch2 [--top N] [--min-score S] [--prepare]
  python3 -I pipelines/router/route.py step2
  python3 -I common/audit/audit_results.py >/dev/null && python3 -I pipelines/router/route.py step3
  python3 -I pipelines/router/route.py status

What each step then runs is printed at the end (the stacking queue, or the sibling lane with LANE_RECS / LANE_PIPE /
LANE_SUFFIX pointing at the router's folders). Task names: stacking stk-<repo>-<id>; step 2 <repo>-s2; step 3 <repo>-s3.
"""
import argparse, csv, glob, importlib.util, json, os, re, shutil, subprocess, sys
from pathlib import Path

sys.path.insert(0, str(next(p for p in Path(__file__).resolve().parents if (p / ".cwe-bench-root").is_file()) / "common"))
import paths  # noqa: E402

ROOT = paths.ROOT
SO = paths.STACKING_OUT
OUT = ROOT / "pipelines" / "router" / "out"
REG = OUT / "stacking_batches.txt"
SCREENS = SO / "screener-ds"


def norm(repo):
    p = str(repo or "").lower().rstrip("/").replace(".git", "").replace("https://github.com/", "").split("/")
    return "/".join(p[-2:]) if len(p) >= 2 else "/".join(p)


def built_repos():
    out = {}
    for t in (ROOT / "tasks").glob("*/task.toml"):
        m = re.search(r'^\s*repo\s*=\s*"([^"]+)"', t.read_text(errors="replace"), re.M)
        if m:
            out.setdefault(norm(m.group(1)), []).append(t.parent.name)
    return out


def batches():
    return [l.strip() for l in REG.read_text().splitlines() if l.strip()] if REG.is_file() else []


def task_repo(slug):
    t = ROOT / "tasks" / slug / "task.toml"
    m = re.search(r'^\s*repo\s*=\s*"([^"]+)"', t.read_text(errors="replace"), re.M) if t.is_file() else None
    return norm(m.group(1)) if m else ""


def batch_rows(name):
    """Rows of a stacking batch file; batch 1's file has no repo column, so it comes from the task."""
    p = SO / f"{name}.tsv"
    rows = list(csv.DictReader(open(p), delimiter="\t")) if p.is_file() else []
    for r in rows:
        r["repo"] = norm(r.get("repo") or task_repo(r["slug"]))
    return rows


def screens_by_repo():
    if not SCREENS.is_dir():
        sys.exit(f"no {SCREENS}: run pipelines/stacking/1-select/select_ds_fullpool.sh first")
    out = {}
    for f in sorted(SCREENS.glob("*.json")):
        if f.name.startswith(("_", ".")) or f.name.endswith(".run.json"):
            continue
        try:
            r = json.loads(f.read_text())
        except Exception:
            continue
        out.setdefault(norm(r.get("repo")), f)
    return out


def stacking_batch(a):
    spec = importlib.util.spec_from_file_location("bps", ROOT / "pipelines/stacking/2-prepare/build_prepare_stack.py")
    bps = importlib.util.module_from_spec(spec); spec.loader.exec_module(bps)
    jobs = {j["id"]: j for j in (json.loads(l) for l in open(SO / "reader_jobs_ds.jsonl") if l.strip())}
    scores = [r for r in csv.DictReader(open(SO / "stack_scores.tsv"), delimiter="\t") if r["usable"] == "True"]
    built = built_repos()
    taken = {norm(r["repo"]) for b in batches() for r in batch_rows(b)}
    best = {}
    for r in sorted(scores, key=lambda r: -float(r["score"])):
        j = jobs.get(r["candidate"])
        if not j:
            continue
        repo = norm(j["repo"])
        if repo in built or repo in taken or repo in best or float(r["score"]) < a.min_score:
            continue
        best[repo] = (r, j)
    chosen = list(best.values())[: a.top] if a.top else list(best.values())
    tsv, txt = SO / f"{a.name}.tsv", SO / f"{a.name}.txt"
    if tsv.exists():
        sys.exit(f"{tsv} exists: choose another --name (a batch is never rewritten)")
    with open(tsv, "w") as f:
        f.write("job_id\tslug\tpattern\tscore\trepo\n")
        for r, j in chosen:
            f.write(f"{j['id']}\t{bps.slug_for(j)}\t{r['pattern']}\t{r['score']}\t{norm(j['repo'])}\n")
    with open(txt, "w") as f:
        for r, j in chosen:
            f.write(f"{bps.slug_for(j)}  # {j['id']} {r['pattern']} {r['score']}\n")
    OUT.mkdir(parents=True, exist_ok=True)
    with open(REG, "a") as f:
        f.write(a.name + "\n")
    print(f"{a.name}: {len(chosen)} stacked tasks (one per unbuilt repo; {len(scores)} usable designs) -> {tsv}")
    if a.prepare:
        ok = 0
        for r, j in chosen:
            slug = bps.slug_for(j)
            if (ROOT / "build" / slug / "BUILD-PROMPT.md").exists():
                print("  prepared already:", slug); ok += 1; continue
            p = subprocess.run([sys.executable, "-I", str(ROOT / "pipelines/stacking/2-prepare/build_prepare_stack.py"), j["id"],
                                "--project-root", str(ROOT), "--jobs-file", str(SO / "reader_jobs_ds.jsonl"),
                                "--reader-dir", str(SO / "reader-ds")], cwd=ROOT, capture_output=True, text=True)
            print("  " + (p.stdout.strip() or p.stderr.strip())[-200:]); ok += p.returncode == 0
        print(f"prepared {ok}/{len(chosen)} BUILD-PROMPTs")
    print(f"next: nohup python3 -I pipelines/stacking/6-trial/stk_queue.py build --slugs-file {txt.relative_to(ROOT)} "
          f"> pipelines/stacking/out/queue/{a.name}.nohup 2>&1 &")


def step2(a):
    stacked = {norm(r["repo"]) for b in batches() for r in batch_rows(b)}
    built = built_repos()
    stacked |= {repo for repo, slugs in built.items() if any(s.startswith("stk-") for s in slugs)}
    d = OUT / "step2" / "screener"
    if d.exists():
        shutil.rmtree(d)
    d.mkdir(parents=True)
    n = skip_s = skip_b = 0
    for repo, f in screens_by_repo().items():
        if repo in stacked:
            skip_s += 1; continue
        if repo in built:
            skip_b += 1; continue
        shutil.copy2(f, d / f.name); n += 1
    (OUT / "step2" / "pipeline").mkdir(parents=True, exist_ok=True)
    print(f"step 2 pool: {n} screened repos (excluded: {skip_s} taken by stacking, {skip_b} already built) -> {d.relative_to(ROOT)}")
    env = f"LANE_RECS={d.relative_to(ROOT)} LANE_PIPE=pipelines/router/out/step2/pipeline LANE_SUFFIX=s2"
    print("next:\n"
          f"  {env} python3 -I pipelines/sibling/4-select/lane.py pool\n"
          f"  {env} bash pipelines/sibling/4-select/select.sh deepseek\n"
          f"  {env} python3 -I pipelines/sibling/4-select/lane.py prepare deepseek\n"
          f"  then build the slugs in pipelines/router/out/step2/pipeline/slugs_deepseek.txt (pipelines/sibling/6-build/run_lane.sh)")


def solved_cells():
    led = (ROOT / "build/audit/ledger.md").read_text().split("## All tasks")[1]
    out = {}
    for l in led.splitlines():
        c = [x.strip() for x in l.split("|")]
        if len(c) > 5:
            out[c[2]] = (c[3].startswith("SOLVED"), c[4].startswith("SOLVED"), c[5])
    return out


def reader_job(job_id):
    for f in sorted(SO.glob("reader_jobs*.jsonl")) + sorted(SO.glob("batch1-selection-*/reader_jobs.jsonl")):
        for l in open(f):
            if l.strip():
                j = json.loads(l)
                if j.get("id") == job_id:
                    return j
    return None


def screen_job_for(slug, job):
    """A screener job for a solved stacked task's repo that was never screened (H3 pairs need no screen):
    its advisories and fix commits come from the stacking reader job."""
    c = job.get("candidate") or {}
    fixes = [x for x in (job.get("pin_from") or [])] + [x for x in str(c.get("b_fix", "")).split(";") if x]
    eid = "s3-" + slug
    row = {"entry_id": eid, "ids": " ".join(x for x in (c.get("a"), c.get("b"), c.get("entry")) if x),
           "cve": "", "repo": norm(job["repo"]), "cwe_ids": str(c.get("cwes", "")).replace(";", " "),
           "summary": c.get("family") or c.get("summary") or f"stacked task {slug} (solved); its advisories",
           "parent_commit": None, "fix_commits": " ".join(fixes), "language": c.get("language", ""),
           "score": 0, "published": ""}
    return {"id": f"scr-{eid}", "entry_id": eid, "repo": norm(job["repo"]), "row": row}


def step3(a):
    led = solved_cells()
    by_repo = screens_by_repo()
    own = OUT / "step3" / "screens"            # DeepSeek screens made for step 3 (see --screen-missing)
    if own.is_dir():
        for f in sorted(own.glob("*.json")):
            if f.name.startswith(("_", ".")) or f.name.endswith(".run.json"):
                continue
            try:
                by_repo.setdefault(norm(json.loads(f.read_text()).get("repo")), f)
            except Exception:
                pass
    built = built_repos()
    missing = []
    d = OUT / "step3"; (d / "screener").mkdir(parents=True, exist_ok=True); (d / "pipeline").mkdir(parents=True, exist_ok=True)
    state = d / "routed.tsv"
    done = {l.split("\t")[0] for l in state.read_text().splitlines()[1:]} if state.is_file() else set()
    sel_p = d / "pipeline" / "selection_deepseek.json"
    sel = json.loads(sel_p.read_text()) if sel_p.is_file() else []
    new = []
    routed_repos = {norm(x.get("repo", "")) for x in sel if x.get("repo")}
    for b in batches():
        for r in batch_rows(b):
            slug = r["slug"]
            if slug in done or slug not in led:
                continue
            if norm(r["repo"]) in routed_repos:
                continue                                  # one sibling task per repo
            ds, mm, verdict = led[slug]
            if not (ds or mm):
                continue
            sib = [x for x in built.get(norm(r["repo"]), []) if not x.startswith("stk-")]
            if sib:
                print(f"  {slug}: solved, but {r['repo']} already has a sibling build {sib}; not routed (no duplicates)")
                continue
            f = by_repo.get(norm(r["repo"]))
            if not f:
                j = reader_job(r.get("job_id", ""))
                if j:
                    missing.append(screen_job_for(slug, j))
                print(f"  {slug}: solved, but {r['repo']} has no DeepSeek screen yet; "
                      + ("screen job written (--screen-missing)" if j else "no reader job found; not routed"))
                continue
            rec = json.loads(f.read_text())
            eid = str(rec.get("entry_id") or f.stem)
            shutil.copy2(f, d / "screener" / f"{eid}.json")
            sel.append({"entry_id": eid, "repo": norm(r["repo"]), "source": "step3", "from_stacked": slug,
                        "why": verdict})
            routed_repos.add(norm(r["repo"]))
            new.append((slug, eid, verdict))
    sel_p.write_text(json.dumps(sel, indent=1))
    if not state.is_file():
        state.write_text("slug\tentry_id\tverdict\n")
    with open(state, "a") as f:
        for s, e, v in new:
            f.write(f"{s}\t{e}\t{v}\n")
    print(f"step 3: {len(new)} newly routed ({len(done)} earlier); selection has {len(sel)} entries -> {sel_p.relative_to(ROOT)}")
    if missing:
        jf = d / "screen_jobs.jsonl"
        jf.write_text("".join(json.dumps(j) + "\n" for j in {j["repo"]: j for j in missing}.values()))
        print(f"{len(missing)} solved stacked tasks wait for a screen: run\n"
              f"  common/launch/drive.sh deepseek bash -c 'CLAUDE_BIN=$HOME/.local/bin/claude python3 -I "
              f"common/screener/run_screener.py --run --parallel 70 --model \"$MODEL\" --outdir "
              f"{(d / 'screens').relative_to(ROOT)} --jobs-file {jf.relative_to(ROOT)}'\n  then run step3 again")
    env = "LANE_RECS=pipelines/router/out/step3/screener LANE_PIPE=pipelines/router/out/step3/pipeline LANE_SUFFIX=s3"
    if new:
        print(f"next:\n  {env} python3 -I pipelines/sibling/4-select/lane.py prepare deepseek\n"
              "  then build the slugs in pipelines/router/out/step3/pipeline/slugs_deepseek.txt")


def status(a):
    print("registered stacking batches:", batches() or "none")
    for b in batches():
        rows = batch_rows(b)
        snd = sum((ROOT / "build" / r["slug"] / ".sound").exists() for r in rows)
        print(f"  {b}: {len(rows)} tasks, {snd} sound")
    for st in ("step2", "step3"):
        d = OUT / st / "screener"
        print(f"{st}: {len(list(d.glob('*.json'))) if d.is_dir() else 0} screen records in the pool")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("stacking-batch"); s.add_argument("--name", required=True)
    s.add_argument("--top", type=int, default=0); s.add_argument("--min-score", type=float, default=0.0)
    s.add_argument("--prepare", action="store_true")
    sub.add_parser("step2"); sub.add_parser("step3"); sub.add_parser("status")
    a = ap.parse_args()
    {"stacking-batch": stacking_batch, "step2": step2, "step3": step3, "status": status}[a.cmd](a)


if __name__ == "__main__":
    main()
