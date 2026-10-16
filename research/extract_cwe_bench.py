#!/usr/bin/env python3
"""Turn CWE-bench's published data files into tables the screener can read.

    python3 research/extract_cwe_bench.py

Input (verbatim copies, see sources/cwe-bench-site/SOURCE.md):
    sources/cwe-bench-site/data-v1.js          per OWASP category x model pass@1
    sources/cwe-bench-site/cwe-map-data-v1.js  per CWE x model pass@1 (73 CWEs)
Output:
    cwe_bench_v1_category.tsv   category, name, tasks, one column per model, mean, min, max
    cwe_bench_v1_cwe.tsv        cwe, name, owasp, tasks, langs, one column per model,
                                mean, max, models_at_0, deepseek
Pass@1 is CWE-bench's deterministic metric (4 rollouts per task, rounded half-up). A CWE
with 1 task has pass@1 in steps of 25; small task counts are noisy, so the tasks column
stays next to every number.
"""
import json
import re
import statistics
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE / "sources" / "cwe-bench-site"
DS = "DeepSeek V4.1 Flash"


def load(name):
    text = re.sub(r"/\*.*?\*/", "", (SRC / name).read_text(), flags=re.S)
    return json.loads(text[text.index("=") + 1:].strip().rstrip(";"))


def main():
    d, c = load("data-v1.js"), load("cwe-map-data-v1.js")
    models = d["owasp"]["models"]
    tasks_per_cat = {}
    for row in c["cwes"]:
        tasks_per_cat[row["owasp"]] = tasks_per_cat.get(row["owasp"], 0) + row["tasks"]

    with open(HERE / "cwe_bench_v1_category.tsv", "w") as f:
        f.write("\t".join(["category", "name", "tasks", *models, "mean", "min", "max"]) + "\n")
        for i, cat in enumerate(d["owasp"]["categories"]):
            vals = [d["owasp"]["values"][m][i] for m in models]
            f.write("\t".join([cat, d["owasp"]["names"][cat], str(tasks_per_cat.get(cat, "")),
                               *map(str, vals), f"{statistics.mean(vals):.1f}",
                               str(min(vals)), str(max(vals))]) + "\n")

    with open(HERE / "cwe_bench_v1_cwe.tsv", "w") as f:
        f.write("\t".join(["cwe", "name", "owasp", "tasks", "langs", *models,
                           "mean", "max", "models_at_0", "deepseek"]) + "\n")
        for row in sorted(c["cwes"], key=lambda r: (r["owasp"], int(r["id"].split("-")[1]))):
            vals = [row["pass"][m] for m in models]
            langs = ",".join(f"{l}:{n}" for l, n in row.get("langs", []))
            f.write("\t".join([row["id"], row["name"], row["owasp"], str(row["tasks"]), langs,
                               *map(str, vals), f"{statistics.mean(vals):.1f}", str(max(vals)),
                               str(sum(v == 0 for v in vals)), str(row["pass"][DS])]) + "\n")
    print(f"wrote {len(d['owasp']['categories'])} categories and {len(c['cwes'])} CWEs for {len(models)} models")


if __name__ == "__main__":
    main()
