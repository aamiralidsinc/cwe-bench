#!/usr/bin/env python3
"""Merge the public per-task, per-model repair results into one long table (research item 4).

    python3 research/raw/item4-severity/build_outcomes.py

Input: ~/.tb-graders/cwe/research-raw/item4-severity/benchmarks/ (see its SOURCES.txt)
Output (this folder):
    outcomes_long.tsv   benchmark, run, model, cve, solved (0/1), excluded_run (reason or empty)
    outcome_cves.txt    every CVE in the table (input for fetch_severity.py)

Success definitions (each benchmark's own):
    LiveCVEBench  leaderboard.json user_report[].cve_results[CVE].success     run = model | agent
    PatchEval     any epoch with status == "success" (reproduces DeepSeek V3's leaderboard score)
    SEC-bench     report success, CVE instances only (the 100 OSS-Fuzz tasks have no CVE)
    BountyBench   patch solved within 3 attempts (paper Tables 25/26)
    Gatti         solved_author_rule                                            run = model | prompt type
A run whose solve rate is under 5% is kept but marked excluded_run (likely a harness failure,
e.g. LiveCVEBench OpenHands + DeepSeek V3.2 at 4/190).
"""
import csv
import json
import re
from collections import defaultdict
from pathlib import Path

B = Path.home() / ".tb-graders/cwe/research-raw/item4-severity/benchmarks"
HERE = Path(__file__).resolve().parent


def livecve():
    d = json.loads((B / "livecvebench/site-data/leaderboard.json").read_text())
    for r in d["results"]["user_report"]:
        for cve, v in r["cve_results"].items():
            yield "LiveCVEBench", f"{r['model']} | {r['agent']}", r["model"], cve, int(bool(v.get("success")))


def patcheval():
    for f in sorted((B / "patcheval/compact_llm").glob("fixed_*_Default.jsonl")):
        model = f.name[len("fixed_"):-len("_Default.jsonl")]
        solved = defaultdict(int)
        for line in f.open():
            r = json.loads(line)
            solved[r["cve"]] |= int(r.get("status") == "success")
        for cve, s in solved.items():
            yield "PatchEval", model, model, cve, s


def secbench():
    for f in sorted((B / "sec-bench/compact").glob("Patch_*.jsonl")):
        run = f.name[len("Patch_"):-len(".jsonl")]
        for line in f.open():
            r = json.loads(line)
            m = re.search(r"cve-(\d{4}-\d+)", r["instance_id"], re.I)
            if m:
                yield "SEC-bench", run, run, "CVE-" + m.group(1), int(bool(r["success"]))


def bountybench():
    for r in csv.DictReader(open(B / "bountybench/bountybench_patch_long.tsv"), delimiter="\t"):
        if r["cve"].startswith("CVE-"):
            yield "BountyBench", r["agent"], r["agent"], r["cve"], int(r["success_any_of_3"])


def gatti():
    for line in open(B / "gatti-cve-bench/runs.jsonl"):
        r = json.loads(line)
        if r["cve_id"].startswith("CVE-"):
            yield ("Gatti", f"{r['model_id']} | {r['prompt_type']}", r["model_id"], r["cve_id"],
                   int(bool(r["solved_author_rule"])))


STUDIES = Path.home() / ".tb-graders/cwe/research-raw/item4-severity/studies"


def wide(bench, rel, models, row_ok=lambda r: True):
    """A study table with one row per CVE and one 0/1 column per model (each study's own
    success rule, stated in the file's header comment). NA / empty cells are skipped."""
    lines = [l for l in open(STUDIES / rel, errors="replace") if not l.startswith("#")]
    for r in csv.DictReader(lines, delimiter="\t"):
        cve = (r.get("cve") or "").strip()
        if not cve.startswith("CVE-") or not row_ok(r):
            continue
        for col in (models(r.keys()) if callable(models) else models):
            v = (r.get(col) or "").strip()
            if v in ("0", "1"):
                yield bench, col, col, cve, int(v)


def studies():
    yield from wide("VulnRepairEval", "vulnrepaireval/table2_12models_repair_format.tsv",
                    lambda ks: [k for k in ks if k.endswith("_R")])
    yield from wide("APPATCH", "appatch/zeroday_per_sample_per_model.tsv",
                    ["gpt-4", "claude-3.5-sonnet", "gemini-1.5-pro", "llama-3.1",
                     "deepseek-coder-v2", "codeqwen-1.5", "codellama"])
    yield from wide("CWEFT", "cweft-esem2026/per_cve_L3_pivot.tsv",
                    lambda ks: [k for k in ks if k.split("_")[0] in ("claude", "gemini", "gpt")])
    yield from wide("SAN2PATCH", "san2patch/table3_per_model.tsv",
                    ["gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo", "claude-3.5-sonnet",
                     "gemini-1.5-pro", "gemini-1.5-flash"])
    yield from wide("Pearce2023", "pearce-sp2023/realworld_per_cve_per_engine.tsv",
                    ["code-davinci-002", "cushman-codex", "davinci-codex", "gpt2_csrc", "j1-large", "polycoder"])
    yield from wide("Wu-ISSTA2023", "wu-issta2023-llm-vul/table5_per_vuln_per_model.tsv",
                    lambda ks: [k for k in ks if k not in ("vuln_id", "cve")])
    yield from wide("Garg2025", "garg-oneshot-2511.23408/table2_per_vuln_per_model.tsv",
                    lambda ks: [k for k in ks if k not in ("vuln", "cve", "variant")],
                    row_ok=lambda r: r.get("variant") == "real")
    yield from wide("WhyLLMsFail", "why-llms-fail-2603.10072/per_vuln_gemini3flash.tsv", ["full_any"])


def main():
    rows = [r for src in (livecve, patcheval, secbench, bountybench, gatti, studies) for r in src()]
    rate = defaultdict(list)
    for bench, run, _m, _c, s in rows:
        rate[(bench, run)].append(s)
    excluded = {k: f"solve rate {sum(v)}/{len(v)} < 5% (no signal; harness failure or genuinely weak)"
                for k, v in rate.items() if sum(v) < 0.05 * len(v)}
    with open(HERE / "outcomes_long.tsv", "w") as f:
        f.write("benchmark\trun\tmodel\tcve\tsolved\texcluded_run\n")
        for bench, run, model, cve, s in rows:
            f.write(f"{bench}\t{run}\t{model}\t{cve}\t{s}\t{excluded.get((bench, run), '')}\n")
    cves = sorted({r[3] for r in rows})
    (HERE / "outcome_cves.txt").write_text("\n".join(cves) + "\n")
    print(f"{len(rows)} outcomes, {len(cves)} distinct CVEs")
    for bench in sorted({r[0] for r in rows}):
        runs = [k for k in rate if k[0] == bench]
        n_cve = len({r[3] for r in rows if r[0] == bench})
        ds = [k[1] for k in runs if "deepseek" in k[1].lower()]
        print(f"  {bench:13} runs={len(runs):>2} cves={n_cve:>3} excluded={sum(1 for k in runs if k in excluded)} "
              f"deepseek_runs={ds}")
    for k, why in sorted(excluded.items()):
        print(f"  excluded: {k[0]} / {k[1]}: {why}")


if __name__ == "__main__":
    main()
