"""Parse a GitHub '<commit>.patch' (git format-patch text) into diff metrics.

Reusable by any sourcer.  The text is untrusted data: it is only ever split and
counted here, never executed or written anywhere but the cache.

Standard library only.
"""
import re

LANG_BY_EXT = {
    ".py": "Python", ".pyx": "Python", ".pyi": "Python",
    ".js": "JavaScript", ".mjs": "JavaScript", ".cjs": "JavaScript", ".jsx": "JavaScript",
    ".ts": "TypeScript", ".tsx": "TypeScript", ".mts": "TypeScript", ".cts": "TypeScript",
    ".vue": "JavaScript", ".svelte": "JavaScript",
    ".go": "Go",
    ".java": "Java", ".kt": "Kotlin", ".kts": "Kotlin", ".scala": "Scala", ".groovy": "Groovy",
    ".rb": "Ruby", ".erb": "Ruby", ".rake": "Ruby", ".haml": "Ruby", ".slim": "Ruby",
    ".php": "PHP", ".phtml": "PHP", ".twig": "PHP", ".blade.php": "PHP",
    ".rs": "Rust",
    ".c": "C", ".h": "C", ".cc": "C++", ".cpp": "C++", ".cxx": "C++", ".hpp": "C++", ".hh": "C++",
    ".cs": "C#", ".fs": "F#",
    ".swift": "Swift", ".m": "Objective-C", ".mm": "Objective-C",
    ".ex": "Elixir", ".exs": "Elixir", ".erl": "Erlang",
    ".lua": "Lua", ".pl": "Perl", ".pm": "Perl", ".sh": "Shell", ".bash": "Shell",
    ".sql": "SQL", ".dart": "Dart", ".zig": "Zig", ".nim": "Nim", ".hs": "Haskell",
    ".html": "Template", ".htm": "Template", ".jinja": "Template", ".j2": "Template",
    ".jinja2": "Template", ".tmpl": "Template", ".tpl": "Template", ".ejs": "Template",
    ".hbs": "Template", ".mustache": "Template", ".pug": "Template", ".gohtml": "Template",
    ".liquid": "Template", ".jsp": "Java", ".ftl": "Template",
}

LOCKFILES = {
    "package-lock.json", "yarn.lock", "pnpm-lock.yaml", "npm-shrinkwrap.json", "bun.lockb",
    "bun.lock", "cargo.lock", "go.sum", "poetry.lock", "uv.lock", "pdm.lock", "pipfile.lock",
    "gemfile.lock", "composer.lock", "gradle.lockfile", "flake.lock", "deno.lock", "mix.lock",
    "packages.lock.json",
}
MANIFESTS = {
    "package.json", "pyproject.toml", "setup.py", "setup.cfg", "pipfile", "go.mod", "go.work",
    "cargo.toml", "pom.xml", "build.gradle", "build.gradle.kts", "settings.gradle",
    "gradle.properties", "gemfile", "composer.json", "mix.exs", "build.sbt", "deno.json",
    "version", "version.txt", "version.py", "_version.py", "__version__.py", "version.rb",
    "version.go", "version.ts", "version.js", "version.php", "manifest.in", "libs.versions.toml",
    "constraints.txt", "package.swift", "lerna.json", "nx.json", "turbo.json", "tsconfig.json",
}
DOC_EXT = {".md", ".mdx", ".rst", ".txt", ".adoc", ".asciidoc", ".po", ".pot"}
DOC_NAME = re.compile(r"^(changelog|changes|history|news|readme|license|licence|notice|authors|"
                      r"contributors|security|upgrade|upgrading|release[-_ ]?notes|copying|"
                      r"codeowners)(\.|$)", re.I)
DOC_DIR = {"docs", "doc", "documentation", "website", "changelog.d", "newsfragments",
           "releasenotes", ".changeset", "changes", "changelog", "news", "site", "man",
           ".changes", "upgrade-notes", "release-notes"}
CI_DIR = {".github", ".circleci", ".gitlab", ".buildkite", ".husky", ".devcontainer", ".vscode",
          ".idea", "ci", ".ci", ".azure-pipelines", ".teamcity"}
CI_NAME = re.compile(r"^(dockerfile.*|docker-compose.*|compose\.ya?ml|makefile|justfile|"
                     r"jenkinsfile|\.gitlab-ci\.yml|\.travis\.yml|tox\.ini|noxfile\.py|"
                     r"\.pre-commit-config\.yaml|\.gitignore|\.gitattributes|\.dockerignore|"
                     r"\.editorconfig|\.eslintrc.*|\.prettierrc.*|renovate\.json|"
                     r"dependabot\.yml|codecov\.yml|\.npmrc|\.nvmrc|taskfile\.ya?ml)$", re.I)
CONFIG_EXT = {".yml", ".yaml", ".json", ".toml", ".ini", ".cfg", ".conf", ".properties",
              ".xml", ".env", ".lock", ".json5", ".jsonc", ".plist", ".editorconfig",
              ".csproj", ".props", ".gradle", ".bazel", ".bzl", ".nix", ".tf", ".hcl"}
GENERATED_DIR = {"vendor", "node_modules", "dist", "build", "third_party", "thirdparty",
                 "generated", "gen", "__generated__", "bower_components", "public", "static",
                 "assets", "out", "target", ".yarn"}
GENERATED_NAME = re.compile(r"(\.min\.(js|css)$|\.map$|\.pb\.go$|_pb2(_grpc)?\.py$|"
                            r"\.generated\.|\.gen\.go$|_generated\.go$|\.snap$|\.bundle\.js$|"
                            r"^zz_generated|openapi.*\.(json|ya?ml)$|swagger.*\.(json|ya?ml)$)", re.I)
TEST_DIR = {"test", "tests", "__tests__", "spec", "specs", "testing", "e2e", "testdata",
            "fixtures", "__fixtures__", "__snapshots__", "__mocks__", "cypress", "playwright",
            "integration-tests", "integration_tests", "unittests", "unit_tests",
            "functional_tests", "test-fixtures", "testutil", "testutils", "test_data",
            "testsuite", "smoke", "acceptance", "regression", "fuzz", "benches",
            "benchmarks", "bench", "androidtest", "mocks"}
TEST_NAME = re.compile(
    r"(^test_.*\.py$|_tests?\.py$|^tests?\.py$|^conftest\.py$|_test\.go$|"
    r"\.(test|spec|e2e|cy)\.[cm]?[jt]sx?$|\.test-d\.ts$|"
    r"(Test|Tests|TestCase|IT|ITCase|Spec|TestSuite)\.(java|kt|scala|groovy)$|^Test[A-Z].*\.(java|kt)$|"
    r"_spec\.rb$|_test\.rb$|^test_.*\.rb$|Test\.php$|_test\.php$|Cest\.php$|"
    r"^tests?\.rs$|_tests?\.rs$|_test\.(c|cc|cpp)$|\.t$|_test\.exs$|Tests?\.cs$|\.bats$)")

IMAGE_EXT = {".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".webp", ".pdf", ".woff", ".woff2",
             ".ttf", ".eot", ".zip", ".gz", ".tar", ".jar", ".bin", ".css", ".scss", ".less",
             ".csv", ".tsv", ".ipynb"}

NONSOURCE = ("test", "doc", "lockfile", "manifest", "ci", "config", "generated", "other")


def _ext(name):
    low = name.lower()
    if low.endswith(".blade.php"):
        return ".blade.php"
    i = low.rfind(".")
    return low[i:] if i > 0 else ""


def classify_path(path):
    """-> (category, language).  category is 'source' or one of NONSOURCE."""
    p = path.strip().strip('"')
    parts = p.split("/")
    name = parts[-1]
    low = name.lower()
    dirs = [d.lower() for d in parts[:-1]]
    ext = _ext(name)
    lang = LANG_BY_EXT.get(ext, "")

    if low in LOCKFILES:
        return "lockfile", ""
    if any(d in GENERATED_DIR for d in dirs) and not lang:
        return "generated", ""
    if any(d in ("vendor", "node_modules", "third_party", "thirdparty", "bower_components",
                 "__generated__", ".yarn") for d in dirs) or GENERATED_NAME.search(name):
        return "generated", ""
    # tests before docs/config: fixtures are often .json/.yml/.md under tests/
    if (any(d in TEST_DIR for d in dirs) or TEST_NAME.search(name)
            or "/src/test/" in "/" + p.lower() or any(d.endswith(("_test", "-tests", "_tests",
                                                                  "-test")) for d in dirs)):
        return "test", lang
    if any(d in CI_DIR for d in dirs) or CI_NAME.match(name):
        return "ci", ""
    if low in MANIFESTS or re.match(r"^requirements.*\.(txt|in)$", low) or low.endswith(".gemspec") \
            or low.endswith(".csproj") or low.endswith(".cabal"):
        return "manifest", ""
    if ext in DOC_EXT or DOC_NAME.match(name) or (dirs and dirs[0] in DOC_DIR) \
            or any(d in ("docs", "doc", ".changeset", "changelog.d", "newsfragments",
                         "releasenotes") for d in dirs):
        return "doc", ""
    if any(d in ("examples", "example", "samples", "sample", "demo", "demos") for d in dirs):
        return "other", lang
    if lang:
        return "source", lang
    if ext in CONFIG_EXT:
        return "config", ""
    return "other", ""


_DIFF_HEAD = re.compile(r"^diff --git a/(.+?) b/(.+)$")
_FROM = re.compile(r"^From ([0-9a-f]{40}) Mon Sep 17 00:00:00 2001$")
_HUNK = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@(.*)$")

# ---- fix-shape helpers ----------------------------------------------------
_COMMENT = re.compile(r"^\s*(//|#|\*|/\*|\*/|--\s|<!--|\"\"\"|\'\'\')")
_IMPORT = re.compile(r"^\s*(import\b|from\s+\S+\s+import\b|use\s|require\b|require_once\b|"
                     r"#include\b|using\s|package\s|\"[\w./-]+\",?\s*$|[\w.]+\s+\"[\w./-]+\"\s*$|"
                     r"(const|let|var)\s+[\w{}\s,]+=\s*require\(|\}\s*from\s+['\"]|[\w$]+,\s*$|[)}\]];?\s*$)")
_CALL = re.compile(r"([A-Za-z_][A-Za-z0-9_]*)\s*\(")
_DEFINITION = re.compile(r"\b(def|function|func|fn|class|public|private|protected|static|"
                         r"async|export|interface|type|struct|impl|fun|sub)\b")
_CHECK_LINE = re.compile(
    r"^\s*(\}?\s*(else\s+)?if|elif|unless|assert|while|guard|when|case)\b|&&|\|\||\band\b|\bor\b|"
    r"(valid|verif|check|sanitiz|sanitis|escape|allow|deny|block|permit|authori[sz]|authenticat|"
    r"startswith|endswith|hasprefix|hassuffix|regex|regexp|pattern|match|is_safe|issafe|"
    r"contains|includes|whitelist|blacklist|filter|guard|protect|restrict|forbid|permission)", re.I)
_CHECKISH_NAME = re.compile(r"valid|check|safe|verif|assert|ensure|authori|sanitiz|sanitis|escape|"
                            r"allowed|permission|guard|require|restrict|reject|deny|protect|"
                            r"contain|scope|owner|access|can[A-Z_]|is[A-Z_]", re.I)
_STOP_CALLS = set("""
if for while switch catch return function def class new print println printf len str int bool
list dict set map string isinstance range super require import typeof sizeof assert raise throw
error exception valueerror typeerror runtimeerror keyerror errorf sprintf format join append
push get add put test expect describe it log debug info warn warning some ok err unwrap clone
to_string into number boolean array object promise async await func fn elif else with and or
not in is lambda self this isset empty count sprintf_s make min max abs any all tuple float
open close read write keys values items then filter foreach reduce slice split trim strip
replace lower upper tolowercase touppercase startswith endswith hasprefix hassuffix contains
includes equals hasownproperty call apply bind is_some is_none is_ok is_err expect_err
as_str as_ref to_owned iter collect next from vec box arc rc string_view defer go select
getattr setattr hasattr type id repr sorted enumerate zip bytes encode decode stringify parse
tostring valueof getclass hashcode length size isempty optional of asserttrue assertequals
sprintf fprintf wrap wrapf new_error errors errorsnew nil null none true false echo unset
""".split())


def _substantive(lines):
    return [ln for ln in lines if ln.strip() and not _COMMENT.match(ln) and not _IMPORT.match(ln)]


def shape_metrics(source_files):
    """Fix-shape numbers for the non-test source part of a patch.

    source_files: {path: {"hunk_list": [{"start", "context", "added", "removed"}, ...]}}

    fix_sites           hunks that change real code (not only imports/comments)
    site_files          source files containing such a hunk
    same_check_sites    the largest number of fix sites that all gained a call to the SAME
                        function which no removed line called (proxy for "one check or invariant
                        enforced at several call sites"); the definition site is not counted
    same_check_name     that function's name
    removed_check_lines removed lines that look like a condition, validator or sanitiser
                        (proxy for "a defence was already there and had to be corrected")
    hunk_span           largest distance in lines between hunks of one file
    """
    sites = []                               # (path, hunk index, added, removed)
    removed_check = 0
    max_span = 0
    for path, st in source_files.items():
        starts = []
        for i, h in enumerate(st.get("hunk_list") or []):
            a, r = _substantive(h["added"]), _substantive(h["removed"])
            if not a and not r:
                continue
            sites.append((path, i, a, r))
            starts.append(h["start"])
            removed_check += sum(1 for ln in r if _CHECK_LINE.search(ln))
        if len(starts) > 1:
            max_span = max(max_span, max(starts) - min(starts))
    removed_calls = set()
    for _p, _i, _a, r in sites:
        for ln in r:
            removed_calls.update(m.group(1).lower() for m in _CALL.finditer(ln))
    where = {}
    for path, i, a, _r in sites:
        for ln in a:
            is_def = bool(_DEFINITION.search(ln.split("(")[0]))
            for m in _CALL.finditer(ln):
                name = m.group(1)
                low = name.lower()
                if low in _STOP_CALLS or low in removed_calls or len(name) < 4:
                    continue
                if is_def and ln.find(name + "(") == ln.find("("):       # defining, not calling
                    continue
                if is_def and re.search(r"\b(def|function|func|fn)\s+" + re.escape(name) + r"\s*\(", ln):
                    continue
                where.setdefault(name, set()).add((path, i))
    best_name, best_n = "", 0
    for name, locs in where.items():
        key = (len(locs), 1 if _CHECKISH_NAME.search(name) else 0)
        if key > (best_n, 1 if (best_name and _CHECKISH_NAME.search(best_name)) else 0):
            best_name, best_n = name, len(locs)
    site_files = len(set(p for p, _i, _a, _r in sites))
    n_added = sum(len(a) for _p, _i, a, _r in sites)
    n_removed = sum(len(r) for _p, _i, _a, r in sites)
    return {
        "fix_sites": len(sites),
        "site_files": site_files,
        "same_check_sites": best_n if best_n >= 2 else (1 if sites else 0),
        "same_check_name": best_name if best_n >= 2 else "",
        "removed_check_lines": removed_check,
        "hunk_span": max_span,
        "code_added": n_added,
        "code_removed": n_removed,
    }


def parse_patch(text):
    """Return a dict of metrics for one .patch text (may hold several commits)."""
    files = {}          # path -> dict(added, removed, hunks, binary)
    shas, subject, date = [], "", ""
    cur = None
    in_hunk = False
    in_header = False
    for line in text.split("\n"):
        m = _FROM.match(line)
        if m:                       # never a diff line: those start with ' ', '+', '-' or '\\'
            in_hunk = False
            shas.append(m.group(1))
            in_header = True
            cur = None
            continue
        if in_header:
            if line.startswith("Subject: ") and not subject:
                subject = re.sub(r"^\[PATCH[^\]]*\]\s*", "", line[9:]).strip()
            elif line.startswith("Date: ") and not date:
                date = line[6:].strip()
        m = _DIFF_HEAD.match(line)
        if m:
            in_header = False
            in_hunk = False
            path = m.group(2)
            cur = files.setdefault(path, {"added": 0, "removed": 0, "hunks": 0, "binary": 0,
                                          "hunk_list": []})
            continue
        if cur is None:
            continue
        if line.startswith("@@"):
            cur["hunks"] += 1
            in_hunk = True
            hm = _HUNK.match(line)
            cur["hunk_list"].append({"start": int(hm.group(1)) if hm else 0,
                                     "context": (hm.group(2).strip() if hm else "")[:120],
                                     "added": [], "removed": []})
            continue
        if not in_hunk:
            if line.startswith("Binary files") or line.startswith("GIT binary patch"):
                cur["binary"] = 1
            continue
        if line.startswith("+"):
            if line[1:].strip():
                cur["added"] += 1
                cur["hunk_list"][-1]["added"].append(line[1:])
        elif line.startswith("-"):
            if line == "-- ":            # format-patch signature separator ends the commit
                in_hunk = False
                cur = None
                continue
            if line[1:].strip():
                cur["removed"] += 1
                cur["hunk_list"][-1]["removed"].append(line[1:])
        elif line.startswith(" ") or line == "" or line.startswith("\\"):
            pass
        else:
            in_hunk = False

    breakdown = {}
    src_added = src_removed = src_hunks = 0
    lang_lines = {}
    src_paths, test_paths = [], []
    source_files = {}
    for path, st in files.items():
        cat, lang = classify_path(path)
        if st["binary"] and cat == "source":
            cat = "other"
        breakdown[cat] = breakdown.get(cat, 0) + 1
        if cat == "source":
            source_files[path] = st
            src_added += st["added"]
            src_removed += st["removed"]
            src_hunks += st["hunks"]
            lang_lines[lang] = lang_lines.get(lang, 0) + st["added"] + st["removed"] + 1
            src_paths.append(path)
        elif cat == "test":
            test_paths.append(path)
    # 'Template' only wins when nothing else changed
    real = dict((k, v) for k, v in lang_lines.items() if k != "Template")
    pick = real or lang_lines
    language = max(pick.items(), key=lambda kv: kv[1])[0] if pick else ""
    src_files = breakdown.get("source", 0)
    test_files = breakdown.get("test", 0)
    return {
        "shas": shas,
        "n_patches": len(shas),
        "subject": subject[:300],
        "commit_date": date,
        "n_files": len(files),
        "src_files": src_files,
        "src_added": src_added,
        "src_removed": src_removed,
        "src_hunks": src_hunks,
        "test_files": test_files,
        "other_files": len(files) - src_files - test_files,
        "language": language,
        "breakdown": breakdown,
        "shape": shape_metrics(source_files),
        "src_paths": src_paths[:40],
        "test_paths": test_paths[:20],
    }
