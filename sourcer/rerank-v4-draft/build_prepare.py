"""Fill builder/TASK-BUILD-PROMPT-v1.md for one host into build/<slug>/BUILD-PROMPT.md.

The prompt body is cut verbatim between the ---8<--- markers; FIX_SITES / UNCOVERED_ROUTES /
SCREEN_RECORD come from the screener record; DESIGN_PLAN and HOST_NOTES from a small spec file.

  python3 -I build_prepare.py SPEC.json
SPEC.json: {slug, entry_id, pattern, track, advisory, vuln_commit, fix_commits:[...],
            design_plan, host_notes, project_root}
Writes <project_root-on-this-machine>/build/<slug>/BUILD-PROMPT.md (locally, to ship to the VM).
"""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(HERE, "..", "..", "builder", "TASK-BUILD-PROMPT-v1.md")
RECORDS = os.path.join(HERE, "..", "review", "screener-v2")
MARK = "---8<---"


def main(spec_path):
    spec = json.load(open(spec_path))
    body = open(TEMPLATE, encoding="utf-8").read().split(MARK)[1].strip("\n") + "\n"
    rec = json.load(open(os.path.join(RECORDS, f"{spec['entry_id']}.json")))

    fix_sites = "\n".join(
        f"  - {s['where']} — entry point: {s.get('entry_point', '')} [{s.get('module_kind', '')}]"
        for s in rec.get("fix_sites", [])) or "  (see the screener record)"
    routes = [x for x in rec.get("O8_uncovered_routes") or []
              if isinstance(x, dict) and str(x.get("where") or "").strip() not in ("", "path:line")]
    if routes and spec["pattern"] in ("B", "A+B"):
        uncovered = "\n".join(
            f"  - {x['where']} — {str(x.get('route', ''))} (reason to dismiss: "
            f"{x.get('reason_to_dismiss', '')}; still in latest: {x.get('present_in_latest', 'unknown')})"
            for x in routes)
    else:
        uncovered = "none"

    out = (body
           .replace("{{SLUG}}", spec["slug"])
           .replace("{{PATTERN}}", spec["pattern"])
           .replace("{{TRACK}}", spec["track"])
           .replace("{{ADVISORY}}", spec["advisory"])
           .replace("{{VULN_COMMIT}}", spec["vuln_commit"])
           .replace("{{FIX_COMMITS}}", ", ".join(spec["fix_commits"]))
           .replace("{{SCREEN_RECORD}}", json.dumps(rec, indent=1))
           .replace("{{FIX_SITES}}", fix_sites)
           .replace("{{UNCOVERED_ROUTES}}", uncovered)
           .replace("{{DESIGN_PLAN}}", spec["design_plan"])
           .replace("{{HOST_NOTES}}", spec.get("host_notes", "none"))
           .replace("{{PROJECT_ROOT}}", spec["project_root"]))
    left = re.findall(r"\{\{[A-Z_]+\}\}", out)
    if left:
        raise SystemExit(f"unfilled slots: {left}")
    d = os.path.join(HERE, "..", "..", "build", spec["slug"])
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d, "BUILD-PROMPT.md")
    open(p, "w").write(out)
    print(f"wrote {p} ({len(out.split())} words); pattern {spec['pattern']}, {len(routes)} O8 routes")


if __name__ == "__main__":
    main(sys.argv[1])
