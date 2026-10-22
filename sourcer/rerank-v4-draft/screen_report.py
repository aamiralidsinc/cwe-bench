"""Write sourcer/review/screener-v2/RANKING.md from host-rank-screened.tsv and the screener records.

  python3 -I screen_report.py        # after: rerank.py ../index/candidates.sqlite . --screened ../review/screener-v2

Counts only for uncovered routes (no route text): write-ups stay at summary level
(builder/PROMPT-TEMPLATES-SPEC.md §1.5).
"""
import csv, collections, glob, json, os, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import rerank, validate_screen  # noqa: E402
R = os.path.join(HERE, "..", "review", "screener-v2")
OUT = os.path.join(R, "RANKING.md")


def status(rec):
    lat = [x.get("present_in_latest") for x in rec.get("O8_uncovered_routes") or []
           if isinstance(x, dict) and str(x.get("where") or "").strip()]
    if not lat:
        return "none", lat
    if "yes" in lat:
        return "still upstream", lat
    if all(v == "no" for v in lat):
        return "fixed upstream", lat
    return "unknown", lat


def main():
    rows = list(csv.DictReader(open(os.path.join(HERE, "host-rank-screened.tsv")), delimiter="\t"))
    W = json.load(open(os.path.join(HERE, "screen-weights.json")))
    ranked = {r["entry_id"] for r in rows}
    all_ids = {os.path.basename(p)[:-5] for p in glob.glob(os.path.join(R, "*.json"))}
    table, st_all, st_top = [], collections.Counter(), collections.Counter()
    routes = collections.Counter()
    for i, r in enumerate(rows, 1):
        rec = json.load(open(os.path.join(R, f"{r['entry_id']}.json")))
        o8pts = sum(p for p, w in rerank.screen_terms(validate_screen.normalise(rec), W) if w.startswith("O8 "))
        a_only = int(r["score_read"]) - o8pts
        st, lat = status(rec)
        st_all[st] += 1
        if int(r["score_read"]) >= 21:
            st_top[st] += 1
        c = collections.Counter(lat)
        routes.update(lat)
        o2 = (rec.get("O2_out_of_scope_site") or {}).get("kind", "")
        b = rec.get("O10_build") or {}
        table.append("| {} | {} | {} | {} | {} | {} | {} | {} | {} | {} | {} | {} | {} | {} | {} |".format(
            i, r["score_read"], a_only, r["repo"], r["primary_id"], (b.get("language") or "")[:18].replace("|", "/"),
            ", ".join(sorted({x for x in rec.get("advisory_ids") or [] if str(x).upper().startswith("CVE")})) or "-",
            r["pattern_fit"], rec.get("O1_entry_points"), o2.replace("_", " ") if o2 != "none" else "-",
            f"{c['yes']}/{c['no']}/{c['unknown']}" if lat else "-",
            f"{rec.get('O11_fix_minutes')}m", ", ".join(rec.get("O12_red_flags") or []).replace("_", " ") or "-",
            rec.get("O13_recall_risk", ""), "yes" if rec.get("O9_dos") else "-"))
    n, top = len(rows), sum(st_top.values())
    pf = collections.Counter(r["pattern_fit"] for r in rows)
    dist = collections.Counter(int(r["score_read"]) for r in rows)
    unranked = sorted(all_ids - ranked)

    def pct(a, b):
        return f"{100 * a / b:.0f}%" if b else "-"

    md = f"""# Screened hosts: ranking and how to move forward

Generated {time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime())} by `sourcer/rerank-v4-draft/screen_report.py`.
**Internal.** It counts uncovered routes in named projects that may not be publicly reported. Do not
share it outside the project until the client has decided on disclosure (NEXT-STEPS item 4).

## What this is
- {len(all_ids)} published, already-fixed advisories screened as task hosts by Opus 5.5 with
  `builder/SCREENER-PROMPT-v2.md` (the model the v2 calibration rule ranked third on fact precision,
  chosen by the user to keep GPT limits free). {n} records are valid and ranked below.
- Hosts came from the computed rerank in three batches of 50 (ranks 1-149, 64-309, 128-454; one
  advisory per repo; repos already built and the 37 calibration hosts left out).
- **Score** = `score_read` from `rerank.py --screened`: the screener's observations × draft weights
  `screen-w0` (not fitted) + the advisory's weakness terms. On the calibration hosts this score
  ranked hosts that beat a model above solved ones about 75% of the time (Opus, 90% interval
  0.58-0.90). Scores cluster: order within a score is not meaningful.
- Evidence checked by script against the pinned and current-upstream code: under 1% of file:line
  references are wrong in every batch.

Score distribution: {", ".join(f"{k}: {v}" for k, v in sorted(dist.items(), reverse=True))}.

## The upstream ratio
An uncovered route (pattern B) is a route into the advisory's own protected sink that the
published fix left untouched. The screener also checked whether each route is still present in
current upstream code (default-branch HEAD, 2026-10-17).

| Hosts | All {n} | Score ≥ 21 ({top}) |
|---|---|---|
| No uncovered routes (pattern A only) | {st_all['none']} ({pct(st_all['none'], n)}) | {st_top['none']} ({pct(st_top['none'], top)}) |
| Routes, all fixed upstream since | {st_all['fixed upstream']} ({pct(st_all['fixed upstream'], n)}) | {st_top['fixed upstream']} ({pct(st_top['fixed upstream'], top)}) |
| At least one route still upstream | {st_all['still upstream']} ({pct(st_all['still upstream'], n)}) | {st_top['still upstream']} ({pct(st_top['still upstream'], top)}) |
| Presence unknown or mixed | {st_all['unknown']} ({pct(st_all['unknown'], n)}) | {st_top['unknown']} ({pct(st_top['unknown'], top)}) |

Routes claimed: {sum(routes.values())} (still upstream {routes['yes']}, fixed {routes['no']}, unknown
{routes['unknown']}). These are the screener's leads, not confirmed: in the blind fact check, 4 of 6
Opus route claims held on hosts that beat a model, 1 of 3 on solved hosts. A builder confirms each
route with a test before it counts.

Pattern fit: A+B {pf['A+B']}, A {pf['A']}, B {pf['B']}, injection only {pf['injection_only']}, none {pf['none']}.

**The score favours pattern B.** Uncovered routes earn up to +6 in `screen-w0`, so no host without
routes reaches 21. For a policy that builds pattern A only on some hosts (P1, P3), pick those
hosts by the **A-only score** column (the same score without the route points), not by Score.

## How to move forward
### 1. Choose a policy for routes still upstream
| Policy | What gets built | Shareable now | Cost |
|---|---|---|---|
| **P1, pattern A only** | Every host on the published fix's own sites | All | Drops pattern B, the strongest single lever so far (DeepSeek 0/6 on jackson-sib; both models 0/3 on sib2) |
| **P2, A+B everywhere** | Every host with its routes | Hosts with no route still upstream | {st_top['still upstream']} of the {top} top hosts are held until the client decides |
| **P3, mixed** | A+B where routes are fixed upstream or absent; A only where a route is still upstream; upgrade to A+B after the client decides | All | Weaker tasks on the held hosts until then |

Recommendation: **P3 now, and put the disclosure question to the client at once** (it is already
NEXT-STEPS item 4). The ratio above is what the client needs to see: most strong hosts carry
routes still present upstream, so the client's decision decides how many tasks can use pattern B.
Whatever the policy, every route a task uses gets a row in `build/audit/uncovered-routes.tsv`.

### 2. Choose the build machine
Building and trials need Docker and Harbor. Options: install both on the client VM (32 CPU, trials
in parallel; needs your approval) or use the Mac's shared Docker VM (8 CPU, one build at a time).

### 3. First build batch
Pick 6-8 hosts from the top of the table under the chosen policy: fix estimate 60 minutes or less,
no DoS flag, offline build, and a mix of languages. Each goes through the pipeline in
`builder/NEXT-STEPS.md`: build (`builder/TASK-BUILD-PROMPT-v1.md`), blind fix, fairness review,
strict gate, trials on DeepSeek and MiMo (up to 3 runs each, offline, 2 h), and an audit of every
graded run. Builder and auditor runs use Opus, so keep watching the weekly usage.

### 4. Learn from the outcomes
After the batch's trials, add the outcomes to the calibration set, refit `screen-weights.json`
(screen-w1), and re-rank. The ranking below is only as good as the unfitted weights.

## Ranking ({n} hosts)
Routes = uncovered routes still upstream / fixed upstream / unknown. Fix = the screener's estimate
for a careful engineer who knows where to look. Recall = how widely the advisory is written up.

| # | Score | A-only score | Repo | Advisory | Language | CVE | Pattern | Entry points | Out-of-scope site | Routes | Fix | Red flags | Recall | DoS |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
""" + "\n".join(table) + "\n"
    if unranked:
        md += "\nNot ranked (invalid record, re-screen): " + ", ".join(
            f"entry {e} ({json.load(open(os.path.join(R, e + '.json'))).get('repo', '?')})" for e in unranked) + ".\n"
    open(OUT, "w").write(md)
    print("wrote", OUT, n, "rows")


if __name__ == "__main__":
    main()
