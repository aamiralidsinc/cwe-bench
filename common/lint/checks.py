"""Static checks of a task's tests (warning-only). Each check returns a list of Finding.

The checks look for the test shapes that let a correct fix fail, or let a run be scored on less than it did:
stand-ins that differ from the real code, network stand-ins above the layer a fix may use, flaky timing, tests that
drive internal code directly without accepting a refusal, project tests read from the agent's workspace, and
report writers that may drop a test file that never loaded. See docs/TASK-QUALITY.md.
"""
import json
import re
from dataclasses import dataclass, asdict
from pathlib import Path

CODE_EXT = {".py", ".js", ".mjs", ".cjs", ".ts", ".mts", ".cts", ".go", ".java", ".php", ".rs", ".rb", ".kt"}
SKIP_DIRS = {"node_modules", "vendor", ".git", "__pycache__", "pristine", "project", "dist", "build", "target"}
MAX_FILE_BYTES = 2_000_000


@dataclass
class Finding:
    kind: str          # check id, e.g. "hypothesis-deadline"
    severity: str      # "warn" (likely to fail a correct fix or hide a failure) or "info" (review it)
    file: str          # path relative to the task folder
    line: int
    message: str

    def as_dict(self):
        return asdict(self)


def rel(path, task):
    try:
        return str(Path(path).relative_to(task))
    except ValueError:
        return str(path)


def code_files(tests_dir, skip_project=True):
    """Test source files, skipping vendored code and (unless skip_project is False) copies of the project's own
    suite. The flaky-pattern checks read the project's copies too: they run in the verifier like any test."""
    out = []
    skip = SKIP_DIRS if skip_project else SKIP_DIRS - {"pristine", "project"}
    for p in sorted(Path(tests_dir).rglob("*")):
        if not p.is_file() or p.suffix not in CODE_EXT:
            continue
        if any(part in skip for part in p.relative_to(tests_dir).parts[:-1]):
            continue
        try:
            if p.stat().st_size > MAX_FILE_BYTES:
                continue
        except OSError:
            continue
        out.append(p)
    return out


def read(p):
    try:
        return Path(p).read_text(errors="replace")
    except OSError:
        return ""


def lineno(text, pos):
    return text.count("\n", 0, pos) + 1


def group_of(path, tests_dir):
    parts = Path(path).relative_to(tests_dir).parts
    return parts[0] if len(parts) > 1 and parts[0] in ("security", "functional") else "support"


# ---------------------------------------------------------------- flaky patterns

GIVEN = re.compile(r"^\s*@(?:hypothesis\.)?given\(", re.M)
DEADLINE_OFF = re.compile(r"deadline\s*=\s*None")


def check_hypothesis(task, tests_dir, files, ctx):
    """Hypothesis' default 200 ms per-example deadline measures machine load, not correctness."""
    py = [f for f in ctx["all_files"] if f.suffix == ".py"]
    if any(DEADLINE_OFF.search(read(f)) and "load_profile" in read(f) for f in py):
        return []                                             # a project-wide profile turns it off
    out = []
    for f in py:
        t = read(f)
        for m in GIVEN.finditer(t):
            window = t[max(0, m.start() - 400):m.start() + 400]
            if not DEADLINE_OFF.search(window):
                out.append(Finding("hypothesis-deadline", "warn", rel(f, task), lineno(t, m.start()),
                                   "@given without deadline=None: the 200 ms default deadline fails under load "
                                   "(set a conftest profile with deadline=None)"))
    return out


TIMING = [
    re.compile(r"(?:assert|expect|assert(?:That|True|Less|LessThan)?)\b[^\n]{0,120}\b(?:elapsed|duration|took|"
               r"time_?taken|millis|ms|seconds|nanos)\b[^\n]{0,40}[<>]=?\s*\d", re.I),
    re.compile(r"(?:time\.(?:time|monotonic|perf_counter)\(\)|performance\.now\(\)|Date\.now\(\)|process\.hrtime|"
               r"System\.(?:nanoTime|currentTimeMillis)\(\)|time\.Since\(|microtime\()[^\n]{0,60}[<>]=?\s*[\d.]+"),
]


def check_timing(task, tests_dir, files, ctx):
    """Wall-clock limits in assertions. A complexity (DoS) test legitimately times, but needs a wide margin."""
    out = []
    for f in ctx["all_files"]:
        t = read(f)
        for rx in TIMING:
            for m in rx.finditer(t):
                out.append(Finding("timing-assertion", "info", rel(f, task), lineno(t, m.start()),
                                   "wall-clock limit in an assertion: keep it far above the reference fix's time "
                                   "under full machine load, or compare growth instead of absolute time"))
                break
    return out


# ---------------------------------------------------------------- network stand-ins and their layer

FETCH_ONLY = re.compile(r"(?:globalThis|global|window)\.fetch\s*=|spyOn\(\s*(?:globalThis|global)\s*,\s*['\"]fetch|"
                        r"\bnock\(|from ['\"]msw|require\(['\"]msw|fetchMock|undici\W+MockAgent")
LOW_NET_JS = re.compile(r"dns(?:\.promises)?\.(?:lookup|resolve\w*)\s*=|\bnet\.(?:connect|createConnection)\s*=|"
                        r"Socket\.prototype\.connect\s*=|(?:internalBinding|process\.binding)\(\s*['\"](?:cares_wrap|tcp_wrap)|"
                        r"\.getaddrinfo\s*=|setGlobalDispatcher|"
                        r"\bhttps?\.(?:request|get)\s*=|(?:vi|jest)\.mock\(\s*['\"](?:node:)?(?:dns|net|http|https)['\"]")
PY_HIGH_NET = re.compile(r"\brequests_mock\b|\bimport responses\b|@responses\.activate|respx|"
                         r"(?:mock\.)?patch\(\s*['\"](?:requests|httpx|urllib3?|aiohttp)\.")
PY_LOW_NET = re.compile(r"socket\.(?:getaddrinfo|create_connection|socket)\s*=|patch\(\s*['\"]socket\.|"
                        r"setattr\(\s*socket\b|getaddrinfo\s*=")


def strip_js_comments(text):
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    return re.sub(r"(?m)(^|[^:\\'\"])//.*$", r"\1", text)


def check_network(task, tests_dir, files, ctx):
    out = []
    js = [f for f in files if f.suffix in {".js", ".mjs", ".cjs", ".ts", ".mts", ".cts"}]
    js_text = {f: strip_js_comments(read(f)) for f in js}
    if any(FETCH_ONLY.search(t) for t in js_text.values()) and not any(LOW_NET_JS.search(t)
                                                                       for t in js_text.values()):
        f, t = next((f, t) for f, t in js_text.items() if FETCH_ONLY.search(t))
        out.append(Finding("network-layer", "warn", rel(f, task), lineno(t, FETCH_ONLY.search(t).start()),
                           "the network stand-in replaces fetch only: a fix that connects through node:http, "
                           "undici or its own dns lookup (the usual rebinding defence) bypasses it"))
    py = [f for f in files if f.suffix == ".py"]
    py_text = {f: re.sub(r"(?m)#.*$", "", read(f)) for f in py}
    if any(PY_HIGH_NET.search(t) for t in py_text.values()) and not any(PY_LOW_NET.search(t)
                                                                        for t in py_text.values()):
        f, t = next((f, t) for f, t in py_text.items() if PY_HIGH_NET.search(t))
        out.append(Finding("network-layer", "warn", rel(f, task), lineno(t, PY_HIGH_NET.search(t).start()),
                           "the network stand-in patches one HTTP client: a fix that resolves or connects "
                           "through another client or the socket layer bypasses it"))
    sh = Path(tests_dir) / "test.sh"
    t = read(sh)
    functional = "\n".join(read(f) for f in files if group_of(f, tests_dir) == "functional")
    for line_no, line in enumerate(t.splitlines(), 1):
        if "/etc/hosts" in line and re.search(r"127\.\d+\.\d+\.\d+|::1|localhost", line):
            names = [n for n in re.findall(r"\b([a-z0-9-]+(?:\.[a-z0-9-]+)+)\b", line, re.I)
                     if not re.match(r"^\d+(\.\d+)+$", n) and n not in ("etc.hosts",)]
            used = [n for n in names if n in functional]
            out.append(Finding("hosts-loopback", "warn" if used else "info", rel(sh, task), line_no,
                               "test.sh maps a name to a loopback address in /etc/hosts"
                               + (f" and functional tests treat {used[0]} as an ordinary host: a fix that resolves "
                                  "names the way clients do sees an internal address" if used else
                                  ": confirm the name is meant to be internal")))
    return out


# ---------------------------------------------------------------- stand-ins for real code

JS_MOCK = re.compile(r"\b(?:vi|jest)\.mock\(\s*['\"]([^'\"]+)['\"]")
PY_PATCH = re.compile(r"(?:mock\.)?patch(?:\.object)?\(\s*['\"]([A-Za-z_][\w.]*)['\"]")
PY_SYSMOD = re.compile(r"sys\.modules\[\s*['\"]([\w.]+)['\"]\s*\]\s*=")
JAVA_PKG = re.compile(r"^\s*package\s+([\w.]+)\s*;", re.M)
JAVA_TYPE = re.compile(r"^\s*(?:public\s+)?(?:final\s+|abstract\s+)*(?:class|interface|enum)\s+(\w+)", re.M)
PHP_NS = re.compile(r"^\s*namespace\s+([\w\\]+)\s*;", re.M)
PHP_TYPE = re.compile(r"^\s*(?:final\s+|abstract\s+)*(?:class|interface|trait)\s+(\w+)", re.M)
JAVA_MEMBER = re.compile(r"^\s*(?:public|protected)\s+(?:static\s+)?(?:final\s+)?[\w<>\[\], .?]+?\s+(\w+)\s*(?:[=;(])",
                         re.M)
PHP_MEMBER = re.compile(r"^\s*(?:public|protected)\s+(?:static\s+)?(?:function\s+(\w+)|const\s+(\w+)|"
                        r"(?:\??\w+\s+)?\$(\w+))", re.M)
HARNESS_PKG = {"bench", "wsbench", "htests", "hidden", "harness", "support", "test", "tests", "testing", "fixture",
               "fixtures", "functional", "security", "cwebench", "stubs", "fakes"}
TEST_CLASS = re.compile(r"(?:Test|Tests|IT|TestCase|Spec|Harness|Fixture)$")
SUPPORT_DIRS = {"support", "harness", "stubs", "stub", "fakes", "fake", "mocks", "shims", "shim", "standins"}
JAVA_PROXY = re.compile(r"Proxy\.newProxyInstance\(|Mockito\.(?:mock|spy)\(|@Mock\b")


def members(text, lang):
    if lang == "java":
        return {m.group(1) for m in JAVA_MEMBER.finditer(text)}
    return {next(g for g in m.groups() if g) for m in PHP_MEMBER.finditer(text)}


def check_standins(task, tests_dir, files, ctx):
    """A test file that declares a product class, or mocks a module, replaces real code: the stand-in must offer
    every member a correct fix may use. With the repository at hand, members are compared."""
    out, repo = [], ctx.get("repo")
    for f in files:
        t = read(f)
        supportish = any(part in SUPPORT_DIRS for part in f.relative_to(tests_dir).parts[:-1])
        if f.suffix in (".java", ".kt") and JAVA_PKG.search(t):
            pkg = JAVA_PKG.search(t).group(1)
            if HARNESS_PKG & set(pkg.lower().split(".")) or pkg.lower().endswith("bench"):
                pass
            else:
                for m in JAVA_TYPE.finditer(t):
                    if TEST_CLASS.search(m.group(1)):
                        continue
                    out += standin_finding(task, f, t, m, f"{pkg}.{m.group(1)}", pkg.replace(".", "/") + "/" +
                                           m.group(1) + ".java", "java", repo, supportish)
        elif f.suffix == ".php" and PHP_NS.search(t):
            ns = PHP_NS.search(t).group(1)
            if not HARNESS_PKG & set(ns.lower().split("\\")):
                for m in PHP_TYPE.finditer(t):
                    if TEST_CLASS.search(m.group(1)):
                        continue
                    out += standin_finding(task, f, t, m, f"{ns}\\{m.group(1)}",
                                           m.group(1) + ".php", "php", repo, supportish)
        for rx, what in ((JS_MOCK, "module"), (PY_PATCH, "patch"), (PY_SYSMOD, "sys.modules")):
            for m in rx.finditer(t):
                target = m.group(1)
                product = target.startswith((".", "/")) or (repo and is_product_module(repo, target))
                if product:
                    out.append(Finding("layer-replaced", "warn", rel(f, task), lineno(t, m.start()),
                                       f"the harness replaces product code ({what} {target}): a correct fix placed "
                                       "inside the replaced component is not observed; confirm the fix cannot "
                                       "live there, or drive the real component"))
                else:
                    out.append(Finding("dependency-mock", "info", rel(f, task), lineno(t, m.start()),
                                       f"{what} stand-in for {target}: it must offer every export and behaviour "
                                       "of the real library a correct fix may use (transactions, extra "
                                       "constants, error types)"))
        if f.suffix == ".java":
            for m in JAVA_PROXY.finditer(t):
                out.append(Finding("layer-replaced", "info", rel(f, task), lineno(t, m.start()),
                                   "a proxy or mock stands in for a product type: confirm a correct fix inside "
                                   "the replaced chain is still observed"))
                break
    return out


def standin_finding(task, f, t, m, fqname, relpath, lang, repo, supportish):
    pos = lineno(t, m.start())
    if not repo:
        if not supportish:
            return []
        return [Finding("stand-in-class", "info", rel(f, task), pos,
                        f"declares {fqname}, a product name: a stand-in compiled ahead of the real class must "
                        "declare every public member a correct fix may use")]
    real = find_in_repo(repo, relpath)
    if not real:
        return []
    missing = sorted(members(read(real), lang) - members(t, lang))
    if not missing:
        return []
    return [Finding("stand-in-class", "warn", rel(f, task), pos,
                    f"stand-in {fqname} lacks public members of the real class ({real}): "
                    + ", ".join(missing[:12]) + (" ..." if len(missing) > 12 else ""))]


_repo_index = {}


def find_in_repo(repo, relpath):
    """The real file for a stand-in: same file name and, for Java, the same package path. PHP files are matched by
    name and must be unique in the repository."""
    key = str(repo)
    if key not in _repo_index:
        idx = {}
        for p in Path(repo).rglob("*"):
            if p.suffix in (".java", ".php", ".kt") and not ({".git", "node_modules", "test", "tests"} & set(p.parts)):
                idx.setdefault(p.name, []).append(p)
        _repo_index[key] = idx
    cands = _repo_index[key].get(Path(relpath).name, [])
    want = str(Path(relpath).parent)
    if want not in ("", "."):
        cands = [c for c in cands if str(c.parent).endswith("/" + want)]
    return cands[0] if len(cands) == 1 else None


def is_product_module(repo, target):
    root = target.split(".")[0].split("/")[0]
    r = Path(repo)
    return (r / root).is_dir() or (r / f"{root}.py").is_file() or (r / "src" / root).is_dir()


# ---------------------------------------------------------------- driving internal code, refusal handling

ENTRY_POINT = re.compile(
    r"\b(?:client|session|agent|app|server|http|api|browser|page|mcp)\s*\.\s*\w+\s*\(|"
    r"\brequest\s*\.\s*(?:get|post|put|patch|delete|request|fetch|send)\b|supertest|httptest\.New(?:Request|Recorder|"
    r"Server)|MockMvc|TestClient|\bfetch\(|subprocess\.|child_process|spawn(?:Sync)?\(|exec(?:File)?(?:Sync)?\(|"
    r"\$this->(?:get|post|put|delete|call|request)\(|->handleRequest\(|Actions::invoke|curl\b|"
    r"\brun_?cli\(|\bcli\.|ServeHTTP\(|WebTestClient|RestAssured|HttpClient|HttpRequest|\.service\(|doGet\(|doPost\(",
    re.I)
REFUSAL_HANDLED = re.compile(
    r"pytest\.raises|assertRaises|refused_or|must_refuse|attempt\(|\btry\s*[:{]|\bexcept\b|\bcatch\s*\(|"
    r"toThrow|rejects|assert\.throws|assert\.rejects|refusedOr|mustRefuse|expectException|assertThrows|"
    r"Refusal::|Refusal\.|refusal\.Do|\berr\s*!=\s*nil|errors\.Is\(|status(?:_code|Code)?\s*(?:>=|in)\s*",
    re.I)
INSTRUCTION_REFUSES = re.compile(r"\brefus|\breject|client error|\b4\d\d\b|\bdenied\b|\bforbidden\b", re.I)


def check_direct_drive(task, tests_dir, files, ctx):
    """Security tests that never go through an entry point drive internal code directly. Where the instruction
    allows refusing and other security files of the task accept a refusal, a file that does not is inconsistent:
    a fix that refuses by raising passes the others and fails this one (the pattern of the 2026-10-27 store()
    repair). Without that contrast it is a note for the fairness review."""
    refuses = bool(INSTRUCTION_REFUSES.search(ctx.get("instruction", "")))
    sec = [f for f in files if group_of(f, tests_dir) == "security" and len(read(f)) >= 80]
    handled = {f: bool(REFUSAL_HANDLED.search(read(f))) for f in sec}
    direct = [f for f in sec if not ENTRY_POINT.search(read(f))]
    some_handle = any(handled.values())
    out = []
    for f in direct:
        if refuses and some_handle and not handled[f]:
            out.append(Finding("refusal-not-accepted", "warn", rel(f, task), 1,
                               "drives internal code directly with no refusal handling, while other security tests "
                               "of this task accept a refusal and the instruction allows refusing: a fix that "
                               "refuses by raising fails only here (use the shared refusal helper)"))
        else:
            out.append(Finding("direct-drive", "info", rel(f, task), 1,
                               "no entry point in this security test: confirm the instruction names the layer it "
                               "drives, and that a refusal would also pass"))
    return out


# ---------------------------------------------------------------- the grading run itself

WS_TEST_PATH = re.compile(r"/workspace/(?:[\w.$-]+/)*?(?:src/)?tests?(?:/[\w./$-]*)?")
RUNNER = re.compile(r"\b(?:pytest|phpunit|codecept|go\s+test|mvn|gradlew?|jest|vitest|mocha|node\s+--test|npx|"
                    r"cargo\s+test|javac|java\s|rspec|bundle\s+exec|unittest|tox|nox)\b")
REL_TEST_PATH = re.compile(r"(?<![\w/.$-])(?:[\w-]+/)?(?:src/)?tests?/[\w./-]+")
RESTORE = re.compile(r"\b(?:cp|rsync|install|tar|git)\b")


def logical_lines(text):
    """test.sh lines with backslash continuations joined: (first line number, text)."""
    out, buf, start = [], "", 0
    for i, line in enumerate(text.splitlines(), 1):
        if not buf:
            start = i
        if line.rstrip().endswith("\\"):
            buf += line.rstrip()[:-1] + " "
            continue
        out.append((start, buf + line))
        buf = ""
    if buf:
        out.append((start, buf))
    return out


def check_test_sh(task, tests_dir, files, ctx):
    out = []
    sh = Path(tests_dir) / "test.sh"
    t = read(sh)
    if not t:
        return [Finding("no-test-sh", "info", rel(sh, task), 1, "no tests/test.sh")]
    scripts = [(sh, t)] + [(p, read(p)) for p in sorted(Path(tests_dir).rglob("*.sh")) if p != sh
                           and "pristine" not in p.parts]
    restored = set()
    for _p, text in scripts:
        for _n, line in logical_lines(text):
            s = line.strip()
            if s.startswith("#") or not RESTORE.search(s):
                continue
            if re.search(r"/tests/|/opt/|pristine|\.tgz|\.tar", s) or re.search(r"-C\s+/workspace\b", s):
                if re.search(r"-C\s+/workspace/?(\s|$)", s):
                    restored.add("/workspace/")
                restored.update(m.group(0) for m in WS_TEST_PATH.finditer(s))
    for p, text in scripts:
        for n, line in logical_lines(text):
            s = line.strip()
            if s.startswith("#") or not RUNNER.search(s):
                continue
            paths = [m.group(0) for m in WS_TEST_PATH.finditer(s)]
            if re.search(r"cd\s+['\"]?/workspace['\"]?\s*(?:&&|;)", s):
                paths += ["/workspace/" + m.group(0) for m in REL_TEST_PATH.finditer(s)]
            for path in paths:
                if ".htests" in path or any(path.startswith(r) or r.startswith(path.rstrip("/") + "/") or
                                            path.split("/test")[0] == r.split("/test")[0] for r in restored):
                    continue
                out.append(Finding("workspace-tests", "warn", rel(p, task), n,
                                   f"runs the project's own tests from {path}, which the agent can edit, without "
                                   "restoring them from /tests: copy them from tests/pristine/ at the pinned "
                                   "commit"))
                break
            else:
                continue
            break
    if "run_group" in t and ".rc" not in t:
        out.append(Finding("runner-exit-ignored", "info", rel(sh, task), 1,
                           "the runner's exit code is not recorded (<group>.rc): a test file that never loads "
                           "leaves no failing test case, so score.py cannot see it"))
    return out


REPORT_WRITER = re.compile(r"<testcase\b|testcase\s*\(|['\"]testcase['\"]")


def check_report_writer(task, tests_dir, files, ctx):
    out = []
    for f in list(files) + sorted(Path(tests_dir).rglob("*.sh")):
        if f.name in ("score.py",):
            continue
        t = read(f)
        if REPORT_WRITER.search(t):
            out.append(Finding("custom-report", "info", rel(f, task), lineno(t, REPORT_WRITER.search(t).start()),
                               "custom JUnit writer: confirm a test file that fails to load or a hook that "
                               "throws is written as an <error> test case"))
    return out


ALL_CHECKS = [check_hypothesis, check_timing, check_network, check_standins, check_direct_drive, check_test_sh,
              check_report_writer]


def run(task_dir, repo=None):
    """All static findings for one task folder (tasks/<slug>)."""
    task = Path(task_dir)
    tests = task / "tests"
    if not tests.is_dir():
        return [Finding("no-tests", "info", "tests", 0, "no tests/ folder")]
    ctx = {"repo": Path(repo) if repo else None, "instruction": read(task / "instruction.md")}
    files = code_files(tests)
    ctx["all_files"] = code_files(tests, skip_project=False)
    out = []
    for check in ALL_CHECKS:
        try:
            out += check(task, tests, files, ctx)
        except Exception as e:  # a lint bug must never hide the other checks
            out.append(Finding("lint-error", "info", "tests", 0, f"{check.__name__}: {type(e).__name__}: {e}"))
    return out


def to_json(findings):
    return json.dumps([f.as_dict() for f in findings], indent=1)
