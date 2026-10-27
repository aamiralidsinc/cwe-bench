#!/usr/bin/env python3
"""Provenance of every delivered task: where it came from and the evidence behind it (internal; never delivered).

    python3 common/util/provenance.py <out_dir>

Reads build/audit/delivered.tsv (the delivery register), the ledger, the batch files, tasks/<slug>/task.toml and
build/<slug>/ records, and writes <out_dir>/PROVENANCE.tsv plus <out_dir>/<delivered_as>.md per task. Read-only on
the sources.
"""
import csv
import re
import sys
import tomllib
from pathlib import Path

sys.path.insert(0, str(next(p for p in Path(__file__).resolve().parents if (p / ".cwe-bench-root").is_file()) / "common"))
import paths  # noqa: E402
sys.path.insert(0, str(paths.AUDIT_TOOLS))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import export_delivery  # noqa: E402  (the same counted runs the delivery exported)

FIELDS = ["slug", "delivered_as", "client_commit", "delivered_date", "track", "round", "built_date", "repo", "cwe_id",
          "advisory", "vulnerable_commit", "fix_commit", "deepseek", "mimo", "fairness", "decision", "runs"]


def read(p):
    try:
        return Path(p).read_text(errors="replace")
    except OSError:
        return ""


def main():
    out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
    batches = {}
    for f in sorted((paths.PIPELINES / "router" / "out" / "batches").glob("*.txt")):
        for line in read(f).splitlines():
            s = line.split("#")[0].strip()
            if s:
                batches.setdefault(s, f.stem)
    ledger = {}
    for line in read(paths.AUDIT_DIR / "ledger.md").splitlines():
        c = [x.strip() for x in line.split("|")]
        if len(c) >= 7 and c[2] not in ("Task", "---"):
            ledger[c[2]] = c
    trials = list(csv.DictReader(open(paths.AUDIT_DIR / "trials.tsv"), delimiter="\t"))
    rows = []
    for line in read(paths.AUDIT_DIR / "delivered.tsv").splitlines():
        if line.startswith("#") or not line.strip():
            continue
        slug, name, commit, date = (line.split("\t") + ["", "", "", ""])[:4]
        if slug.endswith("-control"):
            continue
        b = paths.BUILD / slug
        try:
            meta = tomllib.loads(read(paths.TASKS / slug / "task.toml")).get("metadata", {})
        except tomllib.TOMLDecodeError:
            meta = {}
        led = ledger.get(slug, [""] * 7)
        dec = read(b / "HUMAN-DECISION.md")
        d = re.search(r"(?m)^DECISION:\s*(\w+)", dec); dt = re.search(r"(?m)^DATE:\s*(\S+)", dec)
        fair = re.findall(r"(?mi)^\W*GATE_A\W*[:=]\W*(NOT[ _-]?READY|READY)", read(b / "FAIRNESS.md"))
        runs = [f"{t['model']}:{t['job']}/{t['trial']}={t['reward']}" for t in export_delivery.counted_runs(slug, trials)]
        rnd = batches.get(slug) or ("precision-validation (GitHub Actions)" if slug.startswith("pv-") else
                                    f"pre-scale round, built {read(b / 'start_utc.txt')[:10] or '?'}")
        r = {"slug": slug, "delivered_as": name, "client_commit": commit, "delivered_date": date,
             "track": led[1], "round": rnd, "built_date": read(b / "start_utc.txt")[:10],
             "repo": meta.get("repo", ""), "cwe_id": meta.get("cwe_id", ""), "advisory": meta.get("advisory", ""),
             "vulnerable_commit": meta.get("vulnerable_commit", ""), "fix_commit": meta.get("fix_commit", ""),
             "deepseek": led[3], "mimo": led[4], "fairness": fair[-1] if fair else "",
             "decision": f"{d.group(1)} {dt.group(1)}" if d and dt else "", "runs": " ".join(runs)}
        rows.append(r)
        md = [f"# {name}", "", f"Build ID `{slug}`; delivered {date} in client commit {commit}.", "",
              "| Field | Value |", "|---|---|"] + [f"| {k} | {r[k]} |" for k in FIELDS if k not in ("runs",)]
        md += ["", "## Counted runs (job/trial = reward)", ""] + [f"- {x}" for x in runs]
        md += ["", "## Records", "", f"- VM build records: ~/cwe-bench/build/{slug}/ (FAIRNESS.md, HUMAN-DECISION.md,"
               " AUDIT-NOTES.md, build notes, gate reports)", f"- VM task package: ~/cwe-bench/tasks/{slug}/",
               "- VM trial folders: ~/.tb-graders/cwe/jobs/<job>/<trial>/ (postmortem-*/verdict.json = audit)",
               "- Locked run archive: ~/.tb-graders/cwe/archive/"]
        (out / f"{name}.md").write_text("\n".join(md) + "\n")
    with open(out / "PROVENANCE.tsv", "w", newline="") as f:
        w = csv.DictWriter(f, FIELDS, delimiter="\t"); w.writeheader(); w.writerows(rows)
    print(f"{len(rows)} delivered tasks -> {out}")


if __name__ == "__main__":
    main()
