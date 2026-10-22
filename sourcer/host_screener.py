#!/usr/bin/env python3
"""Host screener: rank candidate REPOSITORIES by properties of the host codebase,
not of the advisory.

Why: the advisory-level score (weights.json) did not predict which round-1 tasks were
hard. The one task both target models failed (build/jackson-databind-sib2) owed its
difficulty to the host:
  - a large, modular codebase;
  - a declarative field-level protection (view, read-only, allowlist, permission
    marker) applied across several modules;
  - at least one input route in a different module that does not use the
    protection's API;
  - values linked to protected ones through the same handler.
(builder/BRIEF-trap-stack.md "Lesson" sections: distance + a reason to dismiss.)

Read-only over sourcer/index/candidates.sqlite. Stdlib only. Run with -I.

    python3 -I sourcer/host_screener.py pass1            # offline, every candidate repo
    python3 -I sourcer/host_screener.py clone --top 150  # shallow, blob-less, sparse (source only)
    python3 -I sourcer/host_screener.py scan             # regex scan of the clones, offline
    python3 -I sourcer/host_screener.py rank             # sourcer/host-ranking.tsv / .md

Clones and intermediate files live outside the code directory, in
~/.tb-graders/cwe/host-screen/ (clones/ is untrusted data: it is only listed and read
as text; nothing in it is executed, and git hooks are not cloned).

The clone is of the default branch HEAD, not of each advisory's vulnerable commit:
host properties (size, modules, protection idioms) change slowly, and this ranks hosts,
not advisories. Every point value below is a HYPOTHESIS from one failed task; see
host-ranking.md for the calibration check.
"""
import argparse
import collections
import concurrent.futures
import gzip
import json
import math
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
INDEX = os.path.join(HERE, "index", "candidates.sqlite")
DATA = os.path.expanduser("~/.tb-graders/cwe/sourcer-data")
WORK = os.path.expanduser("~/.tb-graders/cwe/host-screen")
CLONES = os.path.join(WORK, "clones")
PASS1 = os.path.join(WORK, "pass1.tsv")
SCAN = os.path.join(WORK, "scan.json")
OUT_TSV = os.path.join(HERE, "host-ranking.tsv")
OUT_MD = os.path.join(HERE, "host-ranking.md")

DISK_CAP_BYTES = 28 * 1024 ** 3          # stay under the 30 GB budget with margin
MAX_CHECKOUT_SRC_BYTES = 900 * 1024 ** 2  # bigger source trees: tree metrics only

# Round-1 / round-2 bases with known outcomes. Cloned inside the cap (they replace the
# tail of the first-pass order) so the ranking can be checked against them.
CALIBRATION = {
    "fasterxml/jackson-databind": "HARD: sib DeepSeek 0/6; sib2 both models failed (class A)",
    "marshmallow-code/marshmallow": "EASY: marshmallow-readonly-sib solved by DeepSeek in 10 min (class A, small host)",
    "typestack/class-transformer": "PARKED: class-transformer-exclude-sib, named as a poor (small) class-A host",
    "asynchttpclient/async-http-client": "round-1 composite 0.66 (real defects, not class A)",
    "argoproj/argo-workflows": "round-1 composite 0.74 (defaults route, not class A)",
    "ronf/asyncssh": "round-1 composite 0.85 (adjacent adjustment, not class A)",
    "rclone/rclone": "round-1 composite 0.42",
    "eugeny/russh": "round-1 composite 0.36",
    "hickory-dns/hickory-dns": "round-1 composite 0.38",
    "pylons/webob": "round-1 composite 0.46",
    "cloudreve/cloudreve": "round-1 composite 0.37",
    "filamentphp/filament": "round-1 composite 0.58",
}

# --------------------------------------------------------------------------- files

SRC_EXT = {
    ".java": "Java", ".kt": "Kotlin", ".kts": "Kotlin", ".scala": "Scala", ".groovy": "Groovy",
    ".go": "Go", ".py": "Python", ".php": "PHP", ".rb": "Ruby",
    ".ts": "TypeScript", ".tsx": "TypeScript", ".mts": "TypeScript", ".cts": "TypeScript",
    ".js": "JavaScript", ".jsx": "JavaScript", ".mjs": "JavaScript", ".cjs": "JavaScript",
    ".vue": "JavaScript", ".svelte": "JavaScript",
    ".rs": "Rust", ".c": "C", ".h": "C", ".cc": "C++", ".cpp": "C++", ".hpp": "C++",
    ".cxx": "C++", ".cs": "C#", ".ex": "Elixir", ".exs": "Elixir",
}
EXCL_DIRS = {
    "vendor", "node_modules", "third_party", "thirdparty", "third-party", "external", "dist",
    "build", "target", "out", ".git", "testdata", "test-data", "fixtures", "__fixtures__",
    "test", "tests", "__tests__", "__mocks__", "spec", "specs", "e2e", "it", "examples",
    "example", "samples", "sample", "docs", "doc", "documentation", "benchmark", "benchmarks",
    "bench", "mocks", "mock", "testing", "testutil", "testutils", "test-utils", "cypress",
    "playwright", "storybook", ".storybook", "stories", "site-packages", "bower_components",
    "public", "static", "assets", "migrations",
}
TEST_FILE = re.compile(
    r"(_test\.go$|\.test\.[jt]sx?$|\.spec\.[jt]sx?$|(^|/)test_[^/]*\.py$|_test\.py$|"
    r"(^|/)conftest\.py$|Tests?\.(java|kt|scala|groovy)$|Spec\.(groovy|scala|kt)$|IT\.java$|"
    r"_spec\.rb$|_test\.rb$|Test\.php$|\.stories\.[jt]sx?$|\.d\.ts$|\.min\.js$|\.pb\.go$|"
    r"zz_generated|_generated\.|\.generated\.|\.gen\.go$|_mock\.go$|mock_[^/]*\.go$)")
MANIFESTS = re.compile(
    r"(^|/)(pom\.xml|build\.gradle(\.kts)?|build\.sbt|go\.mod|package\.json|Cargo\.toml|"
    r"composer\.json|setup\.py|pyproject\.toml|[^/]+\.gemspec|mix\.exs|[^/]+\.csproj)$")


def source_lang(path):
    """Language of a non-test, non-vendored source file, else None."""
    ext = os.path.splitext(path)[1].lower()
    lang = SRC_EXT.get(ext)
    if not lang:
        return None
    parts = path.split("/")
    for p in parts[:-1]:
        if p.lower() in EXCL_DIRS:
            return None
    if TEST_FILE.search(path):
        return None
    return lang


def module_roots(paths):
    """The deepest directory holding >= 80% of the source files; a module is that root
    plus one more path segment (submodule: plus two). Collapses Java reverse-domain chains
    and single-package layouts, keeps monorepo packages/<x> apart."""
    n = len(paths)
    if not n:
        return ""
    root = []
    while True:
        cnt = collections.Counter()
        for p in paths:
            segs = p.split("/")[:-1]
            if len(segs) > len(root) and segs[:len(root)] == root:
                cnt[segs[len(root)]] += 1
        if not cnt:
            break
        seg, c = cnt.most_common(1)[0]
        if c < 0.8 * n:
            break
        root = root + [seg]
    return "/".join(root)


def module_of(path, root, depth=1):
    segs = path.split("/")[:-1]
    rsegs = root.split("/") if root else []
    if segs[:len(rsegs)] != rsegs:          # outside the root: its own top segments
        return "/".join(segs[:depth]) or "."
    rest = segs[len(rsegs):]
    if not rest:
        return (root or ".") + "/."
    return (root + "/" if root else "") + "/".join(rest[:depth])


# --------------------------------------------------------------------------- markers
# FIELD: declarative field-level protections. PERM: declarative permission markers
# (method / handler level). The lesson names both; FIELD carries more points.

FIELD = [
    ("java_jsonview", r"@JsonView\b"),
    ("java_jsonignore", r"@JsonIgnore(?:Properties|Type)?\b"),
    ("jackson_access", r"Access\.(?:READ_ONLY|WRITE_ONLY)\b"),
    ("jpa_not_updatable", r"\b(?:updatable|insertable)\s*=\s*false"),
    ("spring_binder_allow", r"\bset(?:Allowed|Disallowed)Fields\b"),
    ("jackson_filter", r"@JsonFilter\b|SimpleBeanPropertyFilter"),
    ("xml_transient", r"@XmlTransient\b"),
    ("schema_readonly", r"\breadOnly\s*[:=]\s*true\b|accessMode\s*=\s*\w*\.?READ_ONLY"),
    ("schema_writeonly", r"\bwriteOnly\s*[:=]\s*true\b"),
    ("go_json_dash", r"json:\"-\""),
    ("go_orm_perm", r"gorm:\"[^\"]*(?:<-|->|-:)|gorm:\"-\"|bun:\"-\""),
    ("go_bind_dash", r"\b(?:binding|mapstructure|form|query|param|yaml|toml):\"-\"|readonly:\"true\""),
    ("proto_field_behavior", r"field_behavior\)\s*=\s*(?:OUTPUT_ONLY|IMMUTABLE)|FieldBehavior_(?:OUTPUT_ONLY|IMMUTABLE)"),
    ("k8s_immutable", r"self\s*==\s*oldSelf|\+immutable\b"),
    ("drf_read_only", r"\bread_only_fields\b|\bread_only\s*=\s*True|\bwrite_only\s*=\s*True|\bextra_kwargs\b"),
    ("django_readonly", r"\beditable\s*=\s*False|\breadonly_fields\b|\bget_readonly_fields\b"),
    ("marshmallow_only", r"\bdump_only\b|\bload_only\b"),
    ("pydantic_exclude", r"\bexclude\s*=\s*True|\bfrozen\s*=\s*True|\bPrivateAttr\b"),
    ("laravel_mass", r"\$(?:fillable|guarded|hidden|visible)\s*="),
    ("symfony_groups", r"[#@]\[?(?:Groups|Ignore|SerializedName)\b"),
    ("api_platform_rw", r"ApiProperty\([^)]*\b(?:readable|writable)\s*[:=]"),
    ("yii_safe", r"'safe'\s*\]"),
    ("drupal_access", r"'#access'"),
    ("filament_dehydrated", r"->dehydrated\("),
    ("rails_attr", r"\battr_(?:readonly|accessible|protected)\b|\bpermitted_attributes\b"),
    ("rails_permit", r"\.permit\("),
    ("class_transformer", r"@(?:Exclude|Expose)\("),
    ("nest_hide", r"@(?:ApiHideProperty|HideField)\b"),
    ("orm_select_false", r"\bselect:\s*false\b"),
    ("field_access_fn", r"\baccess:\s*\{\s*(?:read|create|update)\b"),
    ("serde_skip", r"#\[serde\([^\]]*\bskip(?:_deserializing|_serializing)?\b"),
    ("serde_deny_unknown", r"\bdeny_unknown_fields\b"),
    ("protection_vocab", r"(?i)\b(?:read_?only_?(?:fields|props|properties|attrs|attributes|columns)|"
                         r"writable_?(?:fields|attributes|properties)|allowed_?(?:fields|attributes|properties|keys|params)|"
                         r"permitted_?(?:params|attributes|fields|keys)|protected_?(?:fields|attributes)|"
                         r"hidden_?(?:fields|attributes|properties)|sensitive_?(?:fields|keys|attributes)|"
                         r"field_?(?:permissions?|visibility|level_?access)|active_?view|visible_?in_?view|"
                         r"view_?inclusion|redact(?:ed)?_?(?:fields|keys))\b"),
]
PERM = [
    ("java_method_sec", r"@(?:PreAuthorize|PostAuthorize|Secured|RolesAllowed|PermitAll|DenyAll|RequiresPermissions|RequiresRoles)\b"),
    ("jenkins_restricted", r"@Restricted\(|\bcheckPermission\("),
    ("py_perm", r"\bpermission_classes\b|\bhas_object_permission\b|@permission_required\b|@requires?_permissions?\b"),
    ("php_perm", r"#\[IsGranted\b|@IsGranted\b|@Security\(|->authorize\(|Gate::(?:allows|denies|authorize)\("),
    ("nest_roles", r"@(?:Roles|UseGuards|RequirePermissions?)\("),
    ("rails_authz", r"\bauthorize!\s|\bauthorize\s+@\w+|\bpolicy_scope\(|\bbefore_action\s+:(?:authorize|require_)\w*"),
    ("go_perm", r"\b(?:RequirePermission|CheckPermission|HasPermission|Authorize[A-Z]\w*)\("),
]
ROUTE = [
    ("java_bind", r"@RequestBody\b|@ModelAttribute\b|\breaderForUpdating\(|\.readValue\(|\bconvertValue\(|"
                  r"\bcopyProperties\(|\bbindJSON\(|@DataBoundSetter\b|@BeanParam\b|@FormParam\b|\bDataBinder\b|"
                  r"\btreeToValue\(|\bfromJson\("),
    ("lib_decoder", r"\b(?:extends|implements)\s+\w*(?:Deserializer|Decoder|Unmarshaller|Unmarshaler|Binder)\b|"
                    r"\bimpl(?:<[^>]*>)?\s+(?:\w+::)*(?:Deserialize|Decode)\w*(?:<[^>]*>)?\s+for\b|"
                    r"\bfunc\s+\([^)]*\)\s+Unmarshal(?:JSON|YAML|Text)\("),
    ("go_bind", r"\bjson\.Unmarshal\(|\bjson\.NewDecoder\(|\bShouldBind\w*\(|\.Bind(?:JSON|Query|Body|Uri)?\(|"
                r"\bmapstructure\.Decode|\byaml\.Unmarshal\(|\bprotojson\.Unmarshal\(|\bDecodeJSON\w*\("),
    ("py_bind", r"\brequest\.(?:json|data|POST|form|get_json)\b|\.is_valid\(|\bmodel_validate\w*\(|\bparse_obj\(|"
                r"\bsetattr\(\s*\w+\s*,\s*\w+\s*,"),
    ("php_bind", r"\$request->(?:all|input|validated|only|post|getContent|toArray)\(|->fill\(|->forceFill\(|"
                 r"\bjson_decode\(|->handleRequest\(|->denormalize\(|->setAttributes\(|->load\(\s*\$"),
    ("rb_bind", r"\bparams\[|\bparams\.require\b|\bassign_attributes\b|\bupdate_attributes\b|\.update\(\s*params"),
    ("js_bind", r"\breq\.body\b|\brequest\.body\b|\bctx\.request\.body\b|\bplainTo(?:Class|Instance)\(|"
                r"\bObject\.assign\(|\.\.\.\s*(?:req|request|ctx\.request)\.body|@Body\("),
    ("rs_bind", r"\bserde_json::from_\w+|\bfrom_slice\(|\bJson<|\bForm<|\bweb::Json\b|\bQuery<"),
]
# Routes known to skip model-level protections (raw / mass writes).
BYPASS = [
    ("bypass", r"\bforceFill\(|\bforceCreate\(|\bunguard(?:ed)?\(|\bupdate_columns?\(|\bupdate_all\(|"
               r"\.to_unsafe_h\b|\bpermit!|\breaderForUpdating\(|@JsonMerge\b|\.objects\.filter\([^)]*\)\.update\(|"
               r"DB::table\([^)]*\)->update\(|\bBeanUtils\.copyProperties\(|\.UpdateColumns?\(|"
               r"\.Updates\(\s*map\[|\bUnscoped\(\)|\.save\(\s*update_fields|\bupsert\(|\bbulk_update\(|"
               r"\binsertGetId\(|\.\.\.\s*(?:req|request)\.body\b"),
]
LINK = [
    ("java_link", r"@(?:JsonIdentityInfo|JsonManagedReference|JsonBackReference|JsonIdentityReference|ManyToOne|"
                  r"OneToMany|ManyToMany|OneToOne|JoinColumn|DBRef|JsonUnwrapped)\b|\bObjectId(?:Generator|Resolver|Reader)\b"),
    ("py_link", r"\b(?:ForeignKey|ManyToManyField|OneToOneField|PrimaryKeyRelatedField|SlugRelatedField|"
                r"HyperlinkedRelatedField|relationship)\(|\bfields\.Nested\(|\bmany\s*=\s*True"),
    ("php_link", r"->(?:belongsTo|hasMany|hasOne|belongsToMany|morphTo|morphMany|sync|associate|relationship)\(|"
                 r"[#@]\[?(?:ManyToOne|OneToMany|ManyToMany|OneToOne)\b"),
    ("rb_link", r"\baccepts_nested_attributes_for\b|\bbelongs_to\b|\bhas_many\b|\bhas_one\b|\bhas_and_belongs_to_many\b"),
    ("go_link", r"\b(?:foreignKey|references|many2many):|\.Association\(|\b(?:Parent|Owner|Ref|Target)ID\b"),
    ("ts_link", r"@(?:ManyToOne|OneToMany|ManyToMany|OneToOne|JoinColumn)\(|\bconnect:\s*\{|\brelationTo:|\.populate\("),
    ("rs_link", r"\bbelongs_to\b|#\[sea_orm\([^\]]*\brelation\b|\bforeign_key\b"),
]


def _compile(group):
    return [(k, re.compile(r)) for k, r in group]


GROUPS = {"field": _compile(FIELD), "perm": _compile(PERM), "route": _compile(ROUTE),
          "bypass": _compile(BYPASS), "link": _compile(LINK)}


def scan_text(text):
    """{group: {kind: hits}} for one file's text."""
    out = {}
    for g, pats in GROUPS.items():
        d = {}
        for k, rx in pats:
            n = len(rx.findall(text))
            if n:
                d[k] = n
        if d:
            out[g] = d
    return out


# --------------------------------------------------------------------------- pass 1

PROT_CWES = {"915": 3, "200": 1, "212": 1, "213": 1, "359": 1, "863": 1, "862": 1, "639": 1,
             "284": 1, "285": 1, "269": 1, "732": 1, "668": 1, "1321": 0}
PROT_TEXT = re.compile(
    r"(?i)\b(?:mass[- ]assignment|read[- ]?only|write[- ]only|allow[- ]?list|whitelist|deny[- ]?list|"
    r"blacklist|fillable|guarded|json ?view|"
    r"(?:hidden|private|protected|restricted|sensitive|internal|privileged|immutable) (?:fields?|attributes?|propert(?:y|ies)|columns?)|"
    r"(?:fields?|attributes?|propert(?:y|ies)|columns?) (?:that|which) (?:should|must) (?:not|only)|"
    r"(?:modify|change|set|overwrite|update|edit|alter) (?:arbitrary|protected|restricted|privileged|read-only|other) "
    r"(?:fields?|attributes?|propert(?:y|ies)|columns?|settings)|"
    r"arbitrary (?:fields?|attributes?|propert(?:y|ies))|field[- ]level|attribute[- ]level|per[- ]field|"
    r"exposes? (?:sensitive|private|hidden|internal|secret)|serializ\w* (?:sensitive|secret|private|password))")
LANG_POINTS = {"Java": 1, "Kotlin": 1, "Scala": 1, "PHP": 1, "Ruby": 1, "C": -2, "C++": -2}


def ro_index():
    return sqlite3.connect("file:%s?mode=ro" % INDEX, uri=True)


def patch_markers(repo, shas):
    """Protection / link marker kinds seen in the cached fix patches (any line)."""
    kinds = collections.Counter()
    d = os.path.join(DATA, "patches", *repo.split("/"))
    for sha in shas:
        f = os.path.join(d, sha + ".patch.gz")
        if not os.path.isfile(f):
            continue
        try:
            with gzip.open(f, "rt", encoding="utf-8", errors="replace") as fh:
                text = fh.read()
        except OSError:
            continue
        for g, d2 in scan_text(text).items():
            if g in ("field", "perm", "link"):
                for k in d2:
                    kinds[g + ":" + k] += 1
    return kinds


def cmd_pass1(args):
    os.makedirs(WORK, exist_ok=True)
    con = ro_index()
    con.row_factory = sqlite3.Row
    cand_repos = [r[0] for r in con.execute(
        "select distinct repo from entries where status in ('candidate','shortlisted') and repo is not null")]
    rows = []
    for repo in cand_repos:
        ents = con.execute("select * from entries where repo=?", (repo,)).fetchall()
        cands = [e for e in ents if e["status"] in ("candidate", "shortlisted")]
        langs = collections.Counter(e["language"] for e in cands if e["language"])
        lang = langs.most_common(1)[0][0] if langs else ""
        size_kb = max([e["repo_size_kb"] or 0 for e in ents]) or None
        stars = max([e["repo_stars"] or 0 for e in ents]) or None
        pkgs = set()
        for e in ents:
            for p in (e["packages"] or "").split(" | "):
                if p.strip():
                    pkgs.add(p.strip())
        prot_cwe = 0
        prot_cwe_915 = 0
        prot_text = 0
        for e in ents:
            cw = [c.split("-")[-1] for c in (e["cwe_ids"] or "").split()]
            prot_cwe += max([PROT_CWES.get(c, 0) for c in cw] or [0])
            prot_cwe_915 += "915" in cw
            if PROT_TEXT.search(e["summary"] or ""):
                prot_text += 1
        shas, paths = [], set()
        for c in con.execute("select sha, full_sha, src_paths from commits where repo=?", (repo,)):
            shas.extend([s for s in (c[0], c[1]) if s])
            try:
                paths.update(json.loads(c[2] or "[]"))
            except ValueError:
                pass
        top2 = {"/".join(p.split("/")[:2]) for p in paths if "/" in p}
        mk = patch_markers(repo, sorted(set(shas)))
        mk_field = len([k for k in mk if k.startswith("field:")])
        mk_link = len([k for k in mk if k.startswith("link:")])
        # cheap score: only orders the clone queue
        s = 0
        if size_kb:
            mb = size_kb / 1024
            s += -2 if mb < 5 else -1 if mb < 20 else 1 if mb < 100 else 2 if mb < 1500 else 0
        elif len(ents) >= 10:
            s += 1
        s += LANG_POINTS.get(lang, 0)
        s += min(3, prot_cwe_915 * 2 + (1 if prot_cwe >= 3 else 0) + (1 if prot_cwe >= 8 else 0))
        s += min(3, prot_text)
        s += (1 if mk_field >= 1 else 0) + (1 if mk_field >= 3 else 0) + (1 if mk_link >= 1 else 0)
        s += (1 if len(pkgs) >= 3 else 0) + (1 if len(top2) >= 4 else 0)
        rows.append({
            "repo": repo, "lang": lang, "n_cand": len(cands), "n_adv_all": len(ents),
            "size_mb": round(size_kb / 1024, 1) if size_kb else "", "stars": stars or "",
            "n_packages": len(pkgs), "fix_top2_dirs": len(top2), "prot_cwe_pts": prot_cwe,
            "cwe915": prot_cwe_915, "prot_text_adv": prot_text, "patch_field_kinds": mk_field,
            "patch_link_kinds": mk_link, "patch_markers": " ".join(sorted(mk)), "cheap_score": s,
        })
    rows.sort(key=lambda r: (-r["cheap_score"], -r["n_adv_all"], r["repo"]))
    cols = list(rows[0].keys())
    with open(PASS1, "w") as fh:
        fh.write("\t".join(["rank"] + cols) + "\n")
        for i, r in enumerate(rows, 1):
            fh.write("\t".join([str(i)] + [str(r[c]) for c in cols]) + "\n")
    print("pass1: %d repos -> %s" % (len(rows), PASS1))
    dist = collections.Counter(r["cheap_score"] for r in rows)
    print("cheap score distribution:", sorted(dist.items()))


def read_pass1():
    with open(PASS1) as fh:
        hdr = fh.readline().rstrip("\n").split("\t")
        return [dict(zip(hdr, l.rstrip("\n").split("\t"))) for l in fh]


# --------------------------------------------------------------------------- clone

def du_bytes(path):
    tot = 0
    for dp, dn, fn in os.walk(path):
        for f in fn:
            try:
                tot += os.lstat(os.path.join(dp, f)).st_size
            except OSError:
                pass
    return tot


def git(args, cwd=None, timeout=900):
    env = dict(os.environ, GIT_TERMINAL_PROMPT="0", GIT_LFS_SKIP_SMUDGE="1")
    return subprocess.run(["git", "-c", "core.hooksPath=/dev/null", "-c", "advice.detachedHead=false"] + args,
                          cwd=cwd, env=env, capture_output=True, text=True, timeout=timeout)


def clone_one(repo):
    dest = os.path.join(CLONES, repo.replace("/", "__"))
    meta_f = dest + ".meta.json"
    if os.path.isfile(meta_f):
        return json.load(open(meta_f))
    if os.path.isdir(dest):
        shutil.rmtree(dest)
    t0 = time.time()
    meta = {"repo": repo, "ok": False}
    r = git(["clone", "--depth", "1", "--filter=blob:none", "--no-checkout", "--quiet",
             "https://github.com/%s.git" % repo, dest])
    if r.returncode != 0:
        meta["error"] = (r.stderr or "")[-300:]
        json.dump(meta, open(meta_f, "w"))
        return meta
    head = git(["rev-parse", "HEAD"], cwd=dest).stdout.strip()
    lt = git(["ls-tree", "-r", "-l", "--full-tree", "HEAD"], cwd=dest, timeout=300)
    files = []          # (path, size)
    for line in lt.stdout.splitlines():
        try:
            info, path = line.split("\t", 1)
            parts = info.split()
            if parts[1] != "blob":
                continue
            size = int(parts[3]) if parts[3] != "-" else 0
        except (ValueError, IndexError):
            continue
        files.append((path, size))
    src = [(p, s) for p, s in files if source_lang(p)]
    manifests = [p for p, _ in files if MANIFESTS.search(p) and not any(
        x.lower() in EXCL_DIRS for x in p.split("/")[:-1])]
    src_bytes = sum(s for _, s in src)
    meta.update({"ok": True, "head": head, "n_files": len(files), "n_src": len(src),
                 "src_bytes": src_bytes, "n_manifests": len(manifests)})
    with open(dest + ".tree.json", "w") as fh:
        json.dump({"src": src, "manifests": manifests}, fh)
    if src_bytes > MAX_CHECKOUT_SRC_BYTES or not src:
        meta["checkout"] = "skipped_too_big" if src else "no_source"
    else:
        # sparse checkout of exactly the selected source files (blobs fetched in one batch)
        listf = dest + ".sparse.txt"
        with open(listf, "w") as fh:
            for p, _ in src:
                fh.write("/" + p.replace("\\", "\\\\").replace("*", "\\*").replace("?", "\\?")
                         .replace("[", "\\[").replace("!", "\\!").replace("#", "\\#") + "\n")
        git(["sparse-checkout", "init", "--no-cone"], cwd=dest)
        info_sparse = os.path.join(dest, ".git", "info", "sparse-checkout")
        shutil.copyfile(listf, info_sparse)
        r = git(["checkout", "--quiet", "HEAD"], cwd=dest, timeout=1800)
        meta["checkout"] = "ok" if r.returncode == 0 else "error: " + (r.stderr or "")[-300:]
    meta["seconds"] = round(time.time() - t0, 1)
    meta["disk_bytes"] = du_bytes(dest)
    json.dump(meta, open(meta_f, "w"))
    return meta


def clone_order(top):
    p1 = read_pass1()
    order = [r["repo"] for r in p1]
    cal = [c for c in CALIBRATION if c not in order[:top]]
    chosen = order[:top - len(cal)] + cal
    return chosen


def cmd_clone(args):
    os.makedirs(CLONES, exist_ok=True)
    chosen = clone_order(args.top)
    print("cloning %d repos (%d workers)" % (len(chosen), args.jobs))
    done = 0

    def used():
        return du_bytes(CLONES)

    with concurrent.futures.ThreadPoolExecutor(args.jobs) as ex:
        futs = {}
        it = iter(chosen)
        for _ in range(args.jobs):
            repo = next(it, None)
            if repo:
                futs[ex.submit(clone_one, repo)] = repo
        while futs:
            fin, _ = concurrent.futures.wait(futs, return_when=concurrent.futures.FIRST_COMPLETED)
            for f in fin:
                repo = futs.pop(f)
                done += 1
                try:
                    m = f.result()
                    print("[%d/%d] %s %s src=%s files=%s disk=%.0fMB %ss" % (
                        done, len(chosen), repo, m.get("checkout", m.get("error", "?"))[:40],
                        m.get("n_src"), m.get("n_files"), (m.get("disk_bytes") or 0) / 1e6, m.get("seconds")),
                        flush=True)
                except Exception as e:  # noqa
                    print("[%d/%d] %s FAILED %r" % (done, len(chosen), repo, e), flush=True)
                if done % 10 == 0:
                    u = used()
                    print("  disk used by clones: %.2f GB" % (u / 1024 ** 3), flush=True)
                    if u > DISK_CAP_BYTES:
                        print("DISK CAP reached; stopping new clones", flush=True)
                        it = iter(())
                nxt = next(it, None)
                if nxt:
                    futs[ex.submit(clone_one, nxt)] = nxt
    print("clone: done; disk used %.2f GB" % (used() / 1024 ** 3))


# --------------------------------------------------------------------------- scan

def scan_repo(repo):
    dest = os.path.join(CLONES, repo.replace("/", "__"))
    meta = json.load(open(dest + ".meta.json"))
    if not meta.get("ok"):
        return {"repo": repo, "ok": False, "error": meta.get("error", "")}
    tree = json.load(open(dest + ".tree.json"))
    src = tree["src"]
    paths = [p for p, _ in src]
    root = module_roots(paths)
    langs = collections.Counter()
    for p, s in src:
        langs[source_lang(p)] += s
    mod_files = collections.Counter(module_of(p, root) for p in paths)
    sub_files = collections.Counter(module_of(p, root, 2) for p in paths)
    res = {
        "repo": repo, "ok": True, "head": meta.get("head"), "checkout": meta.get("checkout"),
        "n_src": len(src), "src_bytes": sum(s for _, s in src), "n_manifests": meta.get("n_manifests", 0),
        "langs": {k: round(v / max(1, sum(langs.values())), 3) for k, v in langs.most_common(4)},
        "module_root": root,
        "n_modules": sum(1 for v in mod_files.values() if v >= 5),
        "n_submodules": sum(1 for v in sub_files.values() if v >= 5),
        "n_dirs": len({os.path.dirname(p) for p in paths}),
    }
    if meta.get("checkout") != "ok":
        return res
    loc = 0
    per_file = {}
    for p in paths:
        fp = os.path.join(dest, p)
        try:
            with open(fp, "rb") as fh:
                b = fh.read(2_000_000)
        except OSError:
            continue
        loc += b.count(b"\n")
        t = b.decode("utf-8", "replace")
        hits = scan_text(t)
        if hits:
            per_file[p] = hits
    res["loc"] = loc
    # aggregate per module (depth 1) and per directory (package)
    agg = {g: collections.Counter() for g in GROUPS}
    mods = {g: collections.defaultdict(set) for g in GROUPS}   # group -> module -> kinds
    dirs = {g: set() for g in GROUPS}
    files_g = collections.Counter()
    co_field_link = co_route_link = 0
    for p, hits in per_file.items():
        m = module_of(p, root, 2)
        for g, d in hits.items():
            files_g[g] += 1
            dirs[g].add(os.path.dirname(p))
            for k, n in d.items():
                agg[g][k] += n
                mods[g][m].add(k)
        if "link" in hits and "field" in hits:
            co_field_link += 1
        if "link" in hits and ("route" in hits or "bypass" in hits):
            co_route_link += 1
    field_mods = set(mods["field"])
    perm_mods = set(mods["perm"])
    route_mods = set(mods["route"])
    bypass_mods = set(mods["bypass"])
    # the dominant protection kind (excluding the weak generic vocabulary) and its spread
    strong = collections.Counter()
    for m, ks in mods["field"].items():
        for k in ks:
            if k != "protection_vocab":
                strong[k] += 1
    top_kind, top_kind_mods = (strong.most_common(1)[0] if strong else ("", 0))
    res.update({
        "field_hits": sum(agg["field"].values()), "field_files": files_g["field"],
        "field_dirs": len(dirs["field"]), "field_modules": len(field_mods),
        "field_kinds": dict(agg["field"].most_common(8)),
        "top_field_kind": top_kind, "top_field_kind_modules": top_kind_mods,
        "perm_files": files_g["perm"], "perm_modules": len(perm_mods),
        "route_files": files_g["route"], "route_modules": len(route_mods),
        "route_kinds": dict(agg["route"].most_common(5)),
        "route_modules_unprotected": len(route_mods - field_mods - perm_mods),
        "route_modules_no_field": len(route_mods - field_mods),
        "bypass_files": files_g["bypass"], "bypass_modules": len(bypass_mods),
        "bypass_modules_no_field": len(bypass_mods - field_mods),
        "bypass_kinds": dict(agg["bypass"].most_common(5)),
        "link_files": files_g["link"], "link_modules": len(mods["link"]),
        "cooccur_field_link_files": co_field_link, "cooccur_route_link_files": co_route_link,
    })
    return res


def cmd_scan(args):
    out = {}
    if os.path.isfile(SCAN) and not args.force:
        out = json.load(open(SCAN))
    repos = sorted(f[:-10].replace("__", "/", 1) for f in os.listdir(CLONES) if f.endswith(".meta.json"))
    for i, repo in enumerate(repos, 1):
        if repo in out and out[repo].get("ok") is not None and not args.force:
            continue
        t0 = time.time()
        try:
            out[repo] = scan_repo(repo)
        except Exception as e:  # noqa
            out[repo] = {"repo": repo, "ok": False, "error": repr(e)}
        print("[%d/%d] %s %.1fs" % (i, len(repos), repo, time.time() - t0), flush=True)
        if i % 10 == 0:
            json.dump(out, open(SCAN, "w"))
    json.dump(out, open(SCAN, "w"), indent=0)
    print("scan: %d repos -> %s" % (len(out), SCAN))


# --------------------------------------------------------------------------- rank

def host_score(s):
    """Additive host points; every term reported. Hypothesis weights (see module doc)."""
    d = {}
    loc = s.get("loc")
    if loc is None:   # not checked out: estimate from bytes (~33 bytes per line)
        loc = s.get("src_bytes", 0) / 33
    k = loc / 1000
    d["H1_size"] = -3 if k < 10 else 0 if k < 30 else 2 if k < 100 else 3 if k < 800 else 1
    if k >= 1500:
        d["H1_size"] = -1           # giant: build/offline risk
    nm = max(s.get("n_modules", 0), min(s.get("n_submodules", 0), s.get("n_modules", 0) * 3))
    d["H2_modular"] = 2 if nm >= 8 else 1 if nm >= 4 else 0
    if "field_modules" not in s:
        d["unscanned"] = 0
        return sum(d.values()), d
    fm = s["field_modules"]
    tk = s["top_field_kind_modules"]
    d["H3_protection_spread"] = (3 if fm >= 6 else 2 if fm >= 3 else 1 if fm >= 2 else 0 if fm == 1 else -4)
    d["H3b_one_kind_spread"] = 1 if tk >= 3 else 0
    d["H3c_perm_markers"] = 1 if s["perm_modules"] >= 2 else 0
    ru = s["route_modules_no_field"]
    if fm >= 1:
        d["H4_route_elsewhere"] = 3 if ru >= 4 else 2 if ru >= 2 else 1 if ru >= 1 else 0
        d["H4b_bypass_elsewhere"] = 1 if s["bypass_modules_no_field"] >= 1 else 0
    else:
        d["H4_route_elsewhere"] = 0
    c = s["cooccur_field_link_files"]
    d["H5_linked_values"] = 2 if c >= 5 else 1 if c >= 1 else 0
    return sum(d.values()), d


def spearman(xs, ys):
    def rk(v):
        o = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        i = 0
        while i < len(o):
            j = i
            while j + 1 < len(o) and v[o[j + 1]] == v[o[i]]:
                j += 1
            for t in range(i, j + 1):
                r[o[t]] = (i + j) / 2.0
            i = j + 1
        return r
    a, b = rk(xs), rk(ys)
    n = len(a)
    ma, mb = sum(a) / n, sum(b) / n
    cov = sum((a[i] - ma) * (b[i] - mb) for i in range(n))
    va = math.sqrt(sum((x - ma) ** 2 for x in a))
    vb = math.sqrt(sum((x - mb) ** 2 for x in b))
    return cov / (va * vb) if va and vb else float("nan")


def cmd_rank(args):
    p1 = {r["repo"]: r for r in read_pass1()}
    scan = json.load(open(SCAN))
    con = ro_index()
    adv_score = {r[0]: (r[1], r[2]) for r in con.execute(
        "select repo, max(score), count(*) from entries where status in ('candidate','shortlisted') group by repo")}
    rows = []
    for repo, s in scan.items():
        if not s.get("ok"):
            continue
        hs, det = host_score(s)
        p = p1.get(repo, {})
        rows.append({
            "repo": repo, "host_score": hs,
            "lang": p.get("lang") or (list(s.get("langs", {}))[:1] or [""])[0],
            "kloc": round((s.get("loc") or s.get("src_bytes", 0) / 33) / 1000, 1),
            "n_modules": s.get("n_modules"), "n_submodules": s.get("n_submodules"),
            "field_modules": s.get("field_modules", ""), "top_field_kind": s.get("top_field_kind", ""),
            "top_kind_modules": s.get("top_field_kind_modules", ""),
            "perm_modules": s.get("perm_modules", ""), "route_modules": s.get("route_modules", ""),
            "route_mod_no_field": s.get("route_modules_no_field", ""),
            "bypass_mod_no_field": s.get("bypass_modules_no_field", ""),
            "field_link_files": s.get("cooccur_field_link_files", ""),
            "n_candidates": adv_score.get(repo, ("", ""))[1], "best_adv_score": adv_score.get(repo, ("", ""))[0],
            "cheap_rank": p.get("rank", ""), "calibration": CALIBRATION.get(repo, ""),
            "detail": json.dumps(det, separators=(",", ":")),
            "field_kinds": json.dumps(s.get("field_kinds", {}), separators=(",", ":")),
            "head": (s.get("head") or "")[:12], "checkout": s.get("checkout"),
        })
    rows.sort(key=lambda r: (-r["host_score"], -(r["kloc"] or 0)))
    cols = list(rows[0].keys())
    with open(OUT_TSV, "w") as fh:
        fh.write("\t".join(["rank"] + cols) + "\n")
        for i, r in enumerate(rows, 1):
            r["rank"] = i
            fh.write("\t".join([str(i)] + [str(r[c]).replace("\t", " ") for c in cols]) + "\n")
    # rank correlation with the advisory score among candidate repos
    both = [r for r in rows if r["best_adv_score"] not in ("", None)]
    rho = spearman([r["host_score"] for r in both], [r["best_adv_score"] for r in both]) if len(both) > 3 else float("nan")
    print("rank: %d repos -> %s ; spearman(host, best advisory score) = %.2f (n=%d)" % (
        len(rows), OUT_TSV, rho, len(both)))
    for r in rows[:40]:
        print("%3d %-45s %3d  %7.1fk mod=%s fm=%s %s ru=%s link=%s %s" % (
            r["rank"], r["repo"], r["host_score"], r["kloc"], r["n_modules"], r["field_modules"],
            r["top_field_kind"], r["route_mod_no_field"], r["field_link_files"], r["calibration"][:30]))
    print("calibration:")
    for r in rows:
        if r["calibration"]:
            print("%3d %-40s %3d %s" % (r["rank"], r["repo"], r["host_score"], r["calibration"]))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    sp.add_parser("pass1")
    c = sp.add_parser("clone")
    c.add_argument("--top", type=int, default=150)
    c.add_argument("--jobs", type=int, default=4)
    s = sp.add_parser("scan")
    s.add_argument("--force", action="store_true")
    sp.add_parser("rank")
    a = ap.parse_args()
    {"pass1": cmd_pass1, "clone": cmd_clone, "scan": cmd_scan, "rank": cmd_rank}[a.cmd](a)


if __name__ == "__main__":
    main()
