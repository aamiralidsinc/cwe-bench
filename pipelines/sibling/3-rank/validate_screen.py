"""Validate screener output records (screener-v1) against the prompt's own output schema.

The schema skeleton is read from the screener prompt of the record's version (common/screener/SCREENER-PROMPT-v2.md, or
common/archive/old-prompts/SCREENER-PROMPT-v1.md) (the ```json block under
"## Output", between the ---8<--- markers), so it cannot drift from what the screener was asked
to write. Enums come from the prompt's prose; load_schema() checks that each one is still there.

Checks: exact key set (no extra keys, no score), value types, enums, versions, optional match
against the candidate row, every file:line reference (resolves to an existing file and line when
--repo is given), and the prompt's rules for filling the j block (warnings).

Usage:
  python3 -I validate_screen.py RECORD.json [--repo DIR] [--candidate CAND.json] [--json]
Exit status 1 when any record has errors. Standard library only; reads files, runs nothing.
"""
import argparse, json, os, re, sys
from pathlib import Path
sys.path.insert(0, str(next(p for p in Path(__file__).resolve().parents if (p / ".cwe-bench-root").is_file()) / "common"))
import paths  # noqa: E402  (repo locations: common/paths.py)

# Screener prompts by version: the live one (v2) and the archived ones (v1 and older drafts).
PROMPT_DIRS = [str(paths.SCREENER_PROMPT.parent), str(paths.COMMON / "archive" / "old-prompts")]
PROMPT = str(paths.COMMON / "archive" / "old-prompts" / "SCREENER-PROMPT-v1.md")


def prompt_for(version):
    """SCREENER-PROMPT-vN.md for 'screener-vN', from common/screener/ or common/archive/old-prompts/
    (v1 when the version is missing or odd)."""
    m = re.fullmatch(r"screener-(v\d+)", str(version or ""))
    if m:
        for d in PROMPT_DIRS:
            p = os.path.join(d, f"SCREENER-PROMPT-{m.group(1)}.md")
            if os.path.exists(p):
                return p
    return PROMPT


_SCHEMAS = {}


def schema_for(version):
    p = prompt_for(version)
    if p not in _SCHEMAS:
        _SCHEMAS[p] = load_schema(p)[0]
    return _SCHEMAS[p]
MARK = "---8<---"

ENUMS = {
    "O2_out_of_scope_site.kind": ["second_implementation", "lower_level_api", "wrapper_or_composition",
                                  "save_reload_or_serialization", "defaults_or_merge_route",
                                  "legacy_path", "none"],
    "O7_producer.kind": ["schema", "serializer", "cache", "mapper", "config_loader", "handler", "none"],
    "O12_red_flags[]": ["regression_tests_in_pinned_commit", "needs_gpu_kernel_gui",
                        "needs_network_at_runtime", "many_fix_commits", "tiny_repo", "giant_repo",
                        "single_site", "protection_documented_without_exceptions"],
    "O13_recall_risk": ["low", "medium", "high"],
    "pattern_fit": ["A", "B", "A+B", "injection_only", "none"],
    "O8_uncovered_routes[].present_in_latest": ["yes", "no", "unknown"],
    "j.j_sibling_sites": ["yes", "no", "unknown"],
}
# "A value without file:line evidence must be `unknown`": allowed for these besides their enum
UNKNOWN_OK = {"O2_out_of_scope_site.kind", "O7_producer.kind", "O13_recall_risk"}
BINARY = {"j.j_multi_site", "j.j_cause_other_layer", "j.j_defence_ineffective",
          "j.j_overbroad_breaks_legit"}
# fields holding file:line evidence ("where"-like); lists are checked item by item
LOC_FIELDS = ["trust_decision.evidence[]", "landing_point.where", "fix_sites[].where",
              "O2_out_of_scope_site.where", "O5_coupled_behaviour.where", "O7_producer.where",
              "O8_uncovered_routes[].where", "O8b_injection_room[].where",
              "O8_uncovered_routes[].latest_where"]
REF_RX = re.compile(r"([A-Za-z0-9_.@+\-/\\$]+\.[A-Za-z0-9_+\-]+):(\d+)(?:\s*[-–]\s*(\d+))?")


def load_schema(path=PROMPT):
    text = open(path, encoding="utf-8").read()
    parts = text.split(MARK)
    if len(parts) < 3:
        raise SystemExit(f"{path}: prompt markers not found")
    prompt = parts[1]
    m = re.search(r"## Output.*?```json\n(.*?)\n```", prompt, re.S)
    if not m:
        raise SystemExit(f"{path}: no ```json block under '## Output'")
    skeleton = json.loads(m.group(1))
    for name, values in ENUMS.items():
        for v in values:
            if f"`{v}`" not in prompt and f'"{v}"' not in prompt:
                raise SystemExit(f"{path}: enum value {v!r} of {name} no longer in the prompt")
    return skeleton, prompt


def walk(skel, val, path, out):
    """Compare shape and types against the skeleton; yields (path, value) leaves into out."""
    errs = []
    if isinstance(skel, dict):
        if not isinstance(val, dict):
            return [f"{path or '<root>'}: expected object, got {type(val).__name__}"]
        missing = [k for k in skel if k not in val]
        extra = [k for k in val if k not in skel]
        if missing:
            errs.append(f"{path or '<root>'}: missing keys {missing}")
        if extra:
            errs.append(f"{path or '<root>'}: unexpected keys {extra}")
        for k in skel:
            if k in val:
                errs += walk(skel[k], val[k], f"{path}.{k}" if path else k, out)
        return errs
    if isinstance(skel, list):
        if not isinstance(val, list):
            return [f"{path}: expected list, got {type(val).__name__}"]
        item = skel[0] if skel else None
        for i, v in enumerate(val):
            if item is None:
                out.append((path + "[]", v))
                if not isinstance(v, str):
                    errs.append(f"{path}[{i}]: expected string")
            else:
                errs += walk(item, v, path + "[]", out)
        return errs
    out.append((path, val))
    if path == "entry_id" and isinstance(val, int) and not isinstance(val, bool):
        return errs  # index entry_ids are integers; the prompt's skeleton shows a string
    if val == "unknown":
        return errs  # allowed for any scalar observation; enum check below may still apply
    if isinstance(skel, bool):
        ok = isinstance(val, bool)
    elif isinstance(skel, int):
        ok = isinstance(val, int) and not isinstance(val, bool)
    elif isinstance(skel, str):
        ok = isinstance(val, str)
    else:  # null in the skeleton: number, bool or null
        ok = val is None or isinstance(val, (int, float, bool))
    if not ok:
        errs.append(f"{path}: wrong type {type(val).__name__} ({val!r})")
    return errs


def enum_head(v, values):
    """'yes (latest x.py:3 unchanged)' -> 'yes': an enum value followed by a space or bracket."""
    for val in sorted(values, key=len, reverse=True):
        if v.startswith(val) and len(v) > len(val) and v[len(val)] in " (;,:-":
            return val
    return ""


def normalise(rec):
    """Copy of rec with 'value (note)' enums reduced to the value, for scoring and comparison."""
    import copy
    rec = copy.deepcopy(rec)
    for r in rec.get("O8_uncovered_routes") or []:
        if isinstance(r, dict) and isinstance(r.get("present_in_latest"), str):
            r["present_in_latest"] = enum_head(r["present_in_latest"], ["yes", "no", "unknown"]) \
                or r["present_in_latest"]
    for key, sub in (("O2_out_of_scope_site", "kind"), ("O7_producer", "kind")):
        o = rec.get(key)
        if isinstance(o, dict) and isinstance(o.get(sub), str):
            o[sub] = enum_head(o[sub], ENUMS[f"{key}.{sub}"] + ["unknown"]) or o[sub]
    for key in ("O13_recall_risk", "pattern_fit"):
        if isinstance(rec.get(key), str):
            rec[key] = enum_head(rec[key], ENUMS[key] + ["unknown"]) or rec[key]
    return rec


def refs_in(s):
    return [(m.group(1), int(m.group(2)), int(m.group(3) or m.group(2))) for m in REF_RX.finditer(s)]


def lines_of(p, cache):
    if p not in cache:
        try:
            with open(p, "rb") as fh:
                cache[p] = fh.read().count(b"\n") + 1
        except OSError:
            cache[p] = None
    return cache[p]


def suffix_matches(repo, f, cache):
    """Repo files whose path ends with /f (for references that give a bare or partial path)."""
    if "__files__" not in cache:
        allf = []
        for d, dirs, files in os.walk(repo):
            dirs[:] = [x for x in dirs if x not in (".git", "node_modules")]
            allf += [os.path.join(d, x) for x in files]
        cache["__files__"] = allf
    tail = "/" + f
    return [p for p in cache["__files__"] if p.replace(os.sep, "/").endswith(tail)]


def check_ref(repo, f, a, b, cache, notes=None):
    """'' when path:a-b exists in repo. A bare or partial path counts when it names exactly one
    file whose line range fits (noted), or several of which exactly one fits (noted)."""
    f = f.replace("\\", "/")
    if re.search(r"(^|/)screen/runs/", f):
        return "self-citation: a file the screener wrote in its run dir, not the code"
    f = re.sub(r"^/?(home/[^/]+/)?screen/hosts/\d+/", "", f).lstrip("./")
    for prefix in ("/work/repo/", "work/repo/", "repo/"):
        if f.startswith(prefix):
            f = f[len(prefix):]
    host = os.path.dirname(os.path.normpath(repo))
    if f in ("fix.diff", "work/fix.diff") or f.startswith("latest/"):
        p = os.path.join(host, "fix.diff" if f.endswith("fix.diff") else f)
        n = lines_of(p, cache)
        if n is None:
            return "no such file"
        if not (1 <= a <= b <= n):
            return f"line out of range (file has {n})"
        if notes is not None and f.startswith("latest/"):
            notes.append(f"{f}:{a}: in the latest tree, not the pinned code")
        return ""
    p = os.path.normpath(os.path.join(repo, f))
    if not p.startswith(os.path.normpath(repo) + os.sep):
        return "outside repo"
    n = lines_of(p, cache)
    if n is None:
        cands = suffix_matches(repo, f, cache)
        fits = [c for c in cands if (lines_of(c, cache) or 0) >= b]
        if len(fits) == 1:
            if notes is not None:
                rel = os.path.relpath(fits[0], repo)
                notes.append(f"{f}:{a}: resolved to {rel}" + (f" (1 of {len(cands)} same-named files fits)"
                                                              if len(cands) > 1 else ""))
            return ""
        if not cands:
            return "no such file"
        return f"ambiguous: {len(cands)} files named {f}, {len(fits)} fit the lines"
    if not (1 <= a <= b <= n):
        return f"line out of range (file has {n})"
    return ""


def get(rec, dotted):
    cur = [rec]
    for part in dotted.split("."):
        nxt = []
        for c in cur:
            key, many = (part[:-2], True) if part.endswith("[]") else (part, False)
            v = c.get(key) if isinstance(c, dict) else None
            if v is None:
                continue
            nxt += (v if isinstance(v, list) else [v]) if many else [v]
        cur = nxt
    return cur


def validate(rec, skeleton, repo=None, candidate=None):
    res = {"errors": [], "warnings": [], "refs_total": 0, "refs_ok": 0, "refs_bad": [],
           "ref_notes": [], "fields_unknown": 0}
    leaves = []
    res["errors"] += walk(skeleton, rec, "", leaves)
    if not isinstance(rec, dict):
        return res
    def keys(o):
        if isinstance(o, dict):
            for k, v in o.items():
                yield k
                yield from keys(v)
        elif isinstance(o, list):
            for v in o:
                yield from keys(v)
    if any("score" in str(k).lower() for k in keys(rec)):
        res["errors"].append("record carries a score field; the script scores, not the screener")
    leafmap = {}
    for p, v in leaves:
        leafmap.setdefault(p, []).append(v)
        if v == "unknown":
            res["fields_unknown"] += 1
    for name, values in ENUMS.items():
        key = name[:-2] if name.endswith("[]") else name
        for v in leafmap.get(name, []) + (leafmap.get(key, []) if name.endswith("[]") else []):
            if not isinstance(v, str):
                continue
            if v not in values and not (v == "unknown" and name in UNKNOWN_OK):
                head = enum_head(v, values + (["unknown"] if name in UNKNOWN_OK else []))
                if head:
                    res["warnings"].append(f"{name}: {v[:60]!r} read as {head!r} (note after the value)")
                else:
                    res["errors"].append(f"{name}: {v!r} not in {values}")
    for name in BINARY:
        for v in leafmap.get(name, []):
            if v not in (0, 1):
                res["errors"].append(f"{name}: must be 0 or 1, got {v!r}")
    want = skeleton.get("screener_version")
    if rec.get("screener_version") != want:
        res["errors"].append(f"screener_version {rec.get('screener_version')!r} != {want!r}")
    if not re.fullmatch(r"lessons-v\d+", str(rec.get("lessons_version", ""))):
        res["errors"].append(f"lessons_version {rec.get('lessons_version')!r} is not lessons-vN")
    if not rec.get("model"):
        res["errors"].append("model is empty")
    if candidate:
        if str(rec.get("entry_id")) != str(candidate.get("entry_id")):
            res["errors"].append(f"entry_id {rec.get('entry_id')!r} != candidate {candidate.get('entry_id')!r}")
        if (rec.get("repo") or "").lower() != (candidate.get("repo") or "").lower():
            res["errors"].append(f"repo {rec.get('repo')!r} != candidate {candidate.get('repo')!r}")
        pin = (candidate.get("parent_commit") or "")
        if pin and not (rec.get("pinned_commit") or "x").startswith(pin[:7]) \
                and not pin.startswith(rec.get("pinned_commit") or "x"):
            res["errors"].append(f"pinned_commit {rec.get('pinned_commit')!r} != candidate {pin[:12]}")

    # file:line evidence
    cache = {}
    for field in LOC_FIELDS:
        for v in get(rec, field):
            if not isinstance(v, str) or v.strip() in ("", "unknown"):
                continue
            found = refs_in(v)
            if not found:
                res["refs_total"] += 1
                res["refs_bad"].append(f"{field}: {v!r}: not a path:line reference")
                continue
            for f, a, b in found:
                res["refs_total"] += 1
                why = check_ref(repo, f, a, b, cache, res["ref_notes"]) if repo else ""
                if why:
                    res["refs_bad"].append(f"{field}: {f}:{a}{'-%d' % b if b != a else ''}: {why}")
                else:
                    res["refs_ok"] += 1
    if not repo:
        res["warnings"].append("no --repo given: references checked for form only")

    # a filled kind needs evidence
    for kfield, wfield in (("O2_out_of_scope_site", "where"), ("O7_producer", "where")):
        o = rec.get(kfield) or {}
        if isinstance(o, dict) and o.get("kind") not in (None, "none", "unknown") \
                and not str(o.get(wfield) or "").strip():
            res["errors"].append(f"{kfield}: kind {o.get('kind')!r} without file:line evidence (use 'unknown')")
    for r in rec.get("O8_uncovered_routes") or []:
        if isinstance(r, dict) and not str(r.get("where") or "").strip():
            res["errors"].append(f"O8 route {r.get('route')!r} without file:line evidence")

    # rules for filling the j block, and pattern_fit consistency (warnings: judgement calls)
    j = rec.get("j") if isinstance(rec.get("j"), dict) else {}
    o1 = rec.get("O1_entry_points")
    o8 = [r for r in rec.get("O8_uncovered_routes") or [] if isinstance(r, dict) and r.get("where")]
    multi = (isinstance(o1, int) and o1 >= 2) or bool(o8)
    if j.get("j_multi_site") in (0, 1) and j["j_multi_site"] != int(multi):
        res["warnings"].append(f"j_multi_site={j['j_multi_site']} but O1={o1!r}, O8 routes={len(o8)}")
    o5 = rec.get("O5_coupled_behaviour") or {}
    filled5 = isinstance(o5, dict) and str(o5.get("what") or "").strip() not in ("", "unknown")
    if j.get("j_overbroad_breaks_legit") in (0, 1) and j["j_overbroad_breaks_legit"] != int(filled5):
        res["warnings"].append(f"j_overbroad_breaks_legit={j['j_overbroad_breaks_legit']} but O5 filled={filled5}")
    if j.get("j_sibling_sites") == "yes" and not o8:
        res["warnings"].append("j_sibling_sites='yes' but O8 is empty")
    if j.get("j_sibling_sites") == "no" and o8:
        res["warnings"].append("j_sibling_sites='no' but O8 lists routes")
    pf = rec.get("pattern_fit")
    if pf in ("B", "A+B") and not o8:
        res["warnings"].append(f"pattern_fit={pf} but O8 is empty")
    if pf in ("A", "A+B") and not multi and (rec.get("O2_out_of_scope_site") or {}).get("kind") in ("none", None):
        res["warnings"].append(f"pattern_fit={pf} with O1={o1!r} and no out-of-scope site")
    if isinstance(o1, int) and o1 == 0 and rec.get("fix_sites"):
        res["warnings"].append("O1_entry_points=0 while fix_sites is filled")
    return res


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("records", nargs="+")
    ap.add_argument("--repo", help="code at the pinned commit, for resolving file:line")
    ap.add_argument("--candidate", help="the {{CANDIDATE}} JSON the run was given")
    ap.add_argument("--prompt", default=PROMPT)
    ap.add_argument("--json", action="store_true", help="print one JSON summary per record")
    a = ap.parse_args(argv)
    cand = json.load(open(a.candidate)) if a.candidate else None
    bad = 0
    for path in a.records:
        try:
            rec = json.load(open(path, encoding="utf-8"))
        except (OSError, ValueError) as e:
            res = {"errors": [f"unreadable JSON: {e}"], "warnings": [], "refs_total": 0,
                   "refs_ok": 0, "refs_bad": [], "fields_unknown": 0}
        else:
            skeleton = load_schema(a.prompt)[0] if a.prompt != PROMPT else \
                schema_for(rec.get("screener_version") if isinstance(rec, dict) else None)
            res = validate(rec, skeleton, a.repo, cand)
        res["record"] = path
        bad += bool(res["errors"])
        if a.json:
            print(json.dumps(res))
            continue
        tot = res["refs_total"]
        print(f"{path}: {'FAIL' if res['errors'] else 'ok'}; refs {res['refs_ok']}/{tot} hold"
              f"{' (%.0f%% wrong)' % (100 * (tot - res['refs_ok']) / tot) if tot else ''};"
              f" {res['fields_unknown']} unknown")
        for e in res["errors"]:
            print("  ERROR", e)
        for w in res["warnings"]:
            print("  warn ", w)
        for r in res["refs_bad"]:
            print("  ref  ", r)
        for r in res.get("ref_notes", []):
            print("  note ", r)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
