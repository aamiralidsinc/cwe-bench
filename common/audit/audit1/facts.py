#!/usr/bin/env python3
"""Audit 1, step 1 (no LLM): the checkable facts of one failing run, for the DeepSeek dossier agent.

    python3 common/audit/audit1/facts.py <postmortem-folder> [--trial <trial-dir>] [--out <folder>]

<postmortem-folder> is a folder made by `postmortem.py prepare` (it holds evidence/ and PREPARED.json). The trial
folder defaults to its parent. Everything is written to --out (default: the postmortem folder):

    FACTS.json          failing tests (category, crash or assertion, message, test source file:line, frames through
                        helpers/stand-ins), the reward arithmetic and which tests decided it, infra signals (timeouts,
                        provider stops, content filter, 429 retries, API cuts, tool calls inside the grading window,
                        artifact transfer errors, verifier setup flags), evidence gaps (empty/truncated patch), and
                        contamination candidates (reads of hidden tests, WebFetch/WebSearch, upstream fetches, mtime
                        tricks, netguard lines), each with file:line and a short snippet.
    facts-input/        the raw verifier reports the facts cite (JUnit XML, *.log, score.log, capped in size) and the
                        error lines of trial.log, so the agent can open them: it is confined to this folder.

Paths in FACTS.json are relative to the --out folder ("evidence/transcript.md:212", "facts-input/verifier/...").
A hit found only in the full agent log (the digest cuts tool inputs at 400 characters) is cited as
"trial:agent/claude-code.txt:<line>" with its snippet; the agent cannot open that file and judges from the snippet.

Reads only; never writes under the trial folder unless --out points there (the default postmortem folder does).
"""
import argparse
import json
import re
import shutil
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))          # common/audit: review_flags, internet_use
try:
    import review_flags  # noqa: E402
except Exception:  # pragma: no cover - keep facts usable without the repo helpers
    review_flags = None
try:
    import internet_use  # noqa: E402
    URL_RE, SOURCE_DL_RE = internet_use.URL, internet_use.SOURCE_DL
except Exception:  # pragma: no cover
    URL_RE = re.compile(r"(?:https?|git|ssh|ftp)://(?!(?:localhost|127\.\d+\.\d+\.\d+|0\.0\.0\.0)[:/])"
                        r"[A-Za-z0-9.-]+\.[A-Za-z]{2,}", re.I)
    SOURCE_DL_RE = re.compile(r"\b(pip3?\s+download|npm\s+(view|pack|info)|go\s+mod\s+download|cargo\s+download)\b", re.I)

VERSION = "audit1-facts-v1"
MAX_HITS_PER_KIND = 40
MAX_COPY = 400_000          # bytes per copied verifier file
ASSERTION_TYPES = re.compile(r"assert|expectation|comparisonfailure|opentest4j|expected|testfailure|"
                             r"rspec::expectations|minitest::assertion", re.I)
HELPER_PATH = re.compile(r"(^|/)(support|harness|helpers?|fixtures?|stubs?|mocks?|fakes?|util|utils|common|lib)/|"
                         r"conftest\.py|_helper|helper\.|fixture|stand.?in|bootstrap\.", re.I)
FRAME_RES = [
    re.compile(r'File "(?P<path>[^"]+)", line (?P<line>\d+)'),                                  # Python
    re.compile(r"(?P<path>(?:\.{0,2}/)?[\w@.+-]*(?:/[\w@.+ -]+)*\.(?:py|php|rb|js|mjs|cjs|ts|tsx|go|java|kt|rs|cs|c|cc|cpp|sh)):(?P<line>\d+)"),
    re.compile(r"at [\w$.<>]+\((?P<path>[\w$-]+\.(?:java|kt|scala|groovy)):(?P<line>\d+)\)"),   # JVM
]
TRIAL_LOG_SIGNS = [
    (re.compile(r"Failed to (download|upload|copy) artifact"), "artifact transfer between agent and verifier failed"),
    (re.compile(r"\b(AbsoluteLinkError|LinkOutsideDestinationError|tarfile\.\w+Error)\b"), "workspace archive error"),
    (re.compile(r"No space left on device"), "disk full"),
    (re.compile(r"\b(OOMKilled|out of memory|Cannot allocate memory)\b", re.I), "out of memory"),
    (re.compile(r"\b(VerifierTimeoutError|EnvironmentStartTimeoutError|DockerException|docker: Error)\b"),
     "verifier/environment error"),
    (re.compile(r"(?i)\bverifier\b.*\btimed? ?out\b"), "verifier timeout"),
]
TRIAL_LOG_NOISE = re.compile(r"Cannot estimate Claude cost|litellm|Pass model as E\.g\.|keep_containers")
TESTS_READ = [
    (re.compile(r"\.htests\b"), "hidden-tests path (.htests)"),
    (re.compile(r"(?<![\w.~-])/tests(?=/|\b)"), "absolute /tests path"),
    (re.compile(r"/logs/verifier|/verifier/(results|reward)"), "verifier output path"),
    (re.compile(r"\bzz_(sec|func)_\w+"), "hidden test file name (zz_sec_/zz_func_)"),
    (re.compile(r"(?<![\w.-])/solution(?=/|\b)|fix\.patch\b"), "reference solution path"),
]
MTIME = re.compile(r"\bfind\b[^|;&\n]{0,200}\s-(newer\w*|mmin|mtime|cmin|ctime|amin|atime)\b|"
                   r"\bls\s+-[A-Za-z]*t[A-Za-z]*\b|\bstat\s+(-c|--format|-f)\b|"
                   r"\bgit\s+(log|reflog|fsck)\b[^|;&\n]{0,80}(--all|--lost-found|--unreachable|--reflog)")
# The trial agent runs with bypassPermissions: a denial means the sandbox or a settings file in the repository got in
# the way (logging-operator-s2 2026-10-28: the repo's own .claude deny rule blocked every read of the file to fix).
PERMISSION_DENIED = re.compile(r"Permission to use \w+ .{0,300}has been denied|denied by your permission settings|"
                               r"blocked by (a |your )?(permission|deny) (rule|setting)", re.S)
# Errors that say the ENVIRONMENT lacks something (a global, a module, a service), not that the code refused or checked.
ENV_ERROR = re.compile(r"\b(ReferenceError|is not defined\b|Cannot find (module|package)|ModuleNotFoundError|ImportError|"
                       r"No module named|ClassNotFoundException|NoClassDefFoundError|MissingAppKeyException|"
                       r"No application encryption key|ECONNREFUSED|Connection refused|command not found|"
                       r"UnsatisfiedLinkError|ERR_MODULE_NOT_FOUND|could not find driver|getaddrinfo)", re.I)
UPSTREAM_GIT = re.compile(r"\bgit\s+(clone|fetch|ls-remote|pull|remote\s+add)\b")
FETCH_TOOL = re.compile(r"\b(curl|wget|git|svn|hg|pip3?|python3? -m pip|npm|pnpm|yarn|npx|go\s+(get|mod)|cargo|gem|composer|"
                        r"mvn|gradle|bundle|apt(-get)?|urllib|requests\.get|httpx\.get|fetch\()", re.I)
CODE_HOST = re.compile(r"github\.com|githubusercontent|gitlab|bitbucket|googlesource|sourceforge|codeberg|pypi\.org/(project|pypi|packages)|"
                       r"files\.pythonhosted|registry\.npmjs|npmjs\.(com|org)|unpkg|jsdelivr|packagist|repo1?\.maven|"
                       r"search\.maven|crates\.io|proxy\.golang|pkg\.go\.dev|rubygems|nuget|osv\.dev|nvd\.nist|"
                       r"cve\.(org|mitre)|security\.snyk|advisories|ghsa", re.I)


# ----------------------------------------------------------------------------------------------- small helpers

def jload(p):
    try:
        return json.loads(Path(p).read_text())
    except (OSError, ValueError):
        return None


def clip(s, n=300):
    s = " ".join(str(s or "").split())
    return s if len(s) <= n else s[: n - 3] + "..."


def grading_dir(trial, name):
    if name and name != "original" and (trial / name / "verifier").is_dir():
        return trial / name
    return trial


# ----------------------------------------------------------------------------------------------- test locations

class TestIndex:
    """Maps hidden-test paths and names onto evidence/tests (the copy the agent can read)."""

    def __init__(self, tests_dir, rel_base):
        self.dir, self.base = tests_dir, rel_base
        self.files = [p for p in tests_dir.rglob("*") if p.is_file()] if tests_dir.is_dir() else []
        self.by_name = {}
        for p in self.files:
            self.by_name.setdefault(p.name, []).append(p)
        self._text = {}

    def rel(self, p):
        return str(p.relative_to(self.base))

    def text(self, p):
        if p not in self._text:
            try:
                self._text[p] = p.read_text(errors="replace").splitlines() if p.stat().st_size < 3_000_000 else []
            except OSError:
                self._text[p] = []
        return self._text[p]

    def map_path(self, path):
        """A path as the verifier saw it (/workspace/.htests/security/x.py, ./.htests/..., tests/...) -> evidence path."""
        path = path.replace("\\", "/")
        direct = self.dir / path.lstrip("./")
        if not path.startswith("/") and direct.is_file():
            return direct
        for marker in ("/.htests/", ".htests/", "/tests/", "tests/", "/htests/", "htests/"):
            i = path.find(marker)
            if i >= 0:
                cand = self.dir / path[i + len(marker):]
                if cand.is_file():
                    return cand
        name = path.rsplit("/", 1)[-1]
        c = self.by_name.get(name) or []
        if len(c) == 1:
            return c[0]
        # same tail of two components
        tail = "/".join(path.split("/")[-2:])
        c = [p for p in c if str(p).endswith(tail)]
        return c[0] if len(c) == 1 else None

    def find_test(self, name, hint_file=None):
        """file:line of a test's definition, by its name (function/method name or a spec description)."""
        cands = []
        base = re.sub(r"\(.*\)$", "", name.split("::")[-1].split(" > ")[-1]).strip()
        words = [base]
        if " " in base:      # spec style: search a distinctive slice of the description
            words = [base[:60], base[-60:]]
        files = [hint_file] if hint_file else [p for p in self.files if p.suffix in
                                                (".py", ".php", ".rb", ".js", ".mjs", ".ts", ".tsx", ".go", ".java",
                                                 ".kt", ".rs", ".cs", ".scala", ".groovy")]
        for p in files:
            for i, line in enumerate(self.text(p), 1):
                for w in words:
                    if w and w in line and (" " in w or re.search(rf"\b{re.escape(w)}\b", line)):
                        cands.append((p, i))
                        break
        if not cands:
            return None
        # prefer a definition line
        for p, i in cands:
            line = self.text(p)[i - 1]
            if re.search(r"\b(def|func|function|void|public|it|test|describe|context|specify|fn)\b", line):
                return p, i
        return cands[0]


# ----------------------------------------------------------------------------------------------- JUnit parsing

def parse_xml_reports(verifier, copy_root, out_dir):
    """[{key candidates..., tag, type, message, text, file, line, xml_ref}] from every JUnit XML under verifier/."""
    cases = []
    if not verifier.is_dir():
        return cases
    for x in sorted(verifier.rglob("*.xml")):
        rel = x.relative_to(verifier)
        dest = copy_root / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        try:
            raw = x.read_bytes()
        except OSError:
            continue
        dest.write_bytes(raw[:MAX_COPY])
        text = raw.decode("utf-8", "replace")
        try:
            root = ET.fromstring(raw)
        except ET.ParseError:
            continue
        lines = text.splitlines()
        # line of each <testcase name="..."> in the file, for citations
        line_of = {}
        for i, l in enumerate(lines, 1):
            m = re.search(r'<testcase\b[^>]*\bname="([^"]*)"', l)
            if m:
                line_of.setdefault(m.group(1), i)
        for tc in root.iter("testcase"):
            name = tc.get("name") or ""
            cls = tc.get("classname") or tc.get("class") or ""
            bad = next((c for c in tc if c.tag in ("failure", "error")), None)
            skipped = next((c for c in tc if c.tag == "skipped"), None)
            cases.append({
                "name": name, "classname": cls, "file": tc.get("file"), "line": tc.get("line"),
                "status": bad.tag if bad is not None else ("skipped" if skipped is not None else "pass"),
                "type": (bad.get("type") or "") if bad is not None else "",
                "message": (bad.get("message") or "") if bad is not None else "",
                "text": (bad.text or "") if bad is not None else "",
                "system_out": "".join((c.text or "") for c in tc if c.tag in ("system-out", "system-err"))[:4000],
                "xml_ref": f"{dest.relative_to(out_dir)}:{line_of.get(_xml_escape(name), line_of.get(name, 1))}",
            })
    return cases


def _xml_escape(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def match_case(test_id, cases):
    """The XML testcase for a results.json key such as 'Class::method' or '.htests/x.test.ts::a > b'."""
    tail = test_id.split("::")[-1]
    for c in cases:
        if f"{c['classname']}::{c['name']}" == test_id or c["name"] == test_id:
            return c
    exact = [c for c in cases if c["name"] == tail]
    if len(exact) == 1:
        return exact[0]
    if exact:
        head = test_id.rsplit("::", 1)[0]
        for c in exact:
            if c["classname"] and (c["classname"] in head or head.endswith(c["classname"].split(".")[-1])):
                return c
        bad = [c for c in exact if c["status"] in ("failure", "error")]
        return bad[0] if bad else exact[0]
    loose = [c for c in cases if c["name"] and (c["name"] in test_id or tail in c["name"])]
    bad = [c for c in loose if c["status"] in ("failure", "error")]
    return (bad or loose or [None])[0]


def frames(text, index, out_dir):
    """Test-side frames (mapped to evidence/tests) and product-side frames found in a failure text."""
    test_frames, product_frames, seen = [], [], set()
    for rx in FRAME_RES:
        for m in rx.finditer(text or ""):
            path, line = m.group("path"), int(m.group("line"))
            key = (path, line)
            if key in seen:
                continue
            seen.add(key)
            mapped = index.map_path(path)
            if mapped is not None:
                rel = str(mapped.relative_to(out_dir))
                test_frames.append({"where": f"{rel}:{line}", "helper": bool(HELPER_PATH.search(rel.split("evidence/tests/", 1)[-1])),
                                    "raw": path})
            elif len(product_frames) < 12 and not re.search(r"site-packages|node_modules|/usr/lib|vendor/phpunit|"
                                                            r"junit|java\.base|reflect|_pytest|pluggy", path):
                product_frames.append(f"{path}:{line}")
    return test_frames, product_frames


def classify(case):
    """'assertion' (the test checked and the check failed), 'crash' (an exception the test did not expect),
    'setup-error' (failed before the test body: fixture/setup), 'missing' (no testcase found), 'skipped'."""
    if case is None:
        return "missing"
    if case["status"] == "skipped":
        return "skipped"
    blob = f"{case['type']} {case['message']} {case['text'][:600]}"
    if re.search(r"failed on setup|error at setup|in setup|fixture|setUp\b|before(Each|All)? hook|BeforeEach|"
                 r"@Before|setUpBeforeClass|setup_method", blob, re.I) and case["status"] == "error":
        return "setup-error"
    if ASSERTION_TYPES.search(case["type"] or "") or re.search(r"^\s*(AssertionError|assert\b|Expected\b)|"
                                                                r"Failed asserting|expected:?\s*<|to (equal|be|eq|include|match)|"
                                                                r"\bexpected\b.*\b(got|but|received|actual)\b",
                                                                blob, re.I | re.M):
        return "assertion"
    if case["status"] == "error" or case["type"]:
        return "crash"
    # Go and some runners report only a message; a panic or an error value from a call is a crash
    if re.search(r"\bpanic:|Traceback|Exception\b|Error:|undefined|cannot find|not found|NoSuchMethod|"
                 r"ClassNotFound|ModuleNotFound|ImportError|Fatal error|Uncaught", blob):
        return "crash"
    return "assertion"


# ----------------------------------------------------------------------------------------------- reward arithmetic

def reward_facts(results, reward_json, failing):
    sec = results.get("security") or {}
    fun = results.get("functional") or {}
    rw = (reward_json or {}).get("reward", results.get("reward"))
    s_pass, s_tot = sum(v == "pass" for v in sec.values()), len(sec)
    f_fail = [k for k, v in fun.items() if v != "pass"]
    expected = 1.0 if not failing else (0.0 if f_fail else (round(s_pass / s_tot, 4) if s_tot else None))
    consistent = (rw is not None and expected is not None and abs(float(rw) - expected) < 0.02) or \
                 (rw is not None and f_fail and float(rw) == 0.0)
    return {
        "reward": rw, "security": f"{s_pass}/{s_tot}", "functional": f"{len(fun) - len(f_fail)}/{len(fun)}",
        "setup_errors": results.get("setup_errors") or [],
        "rule": "reward is 1.0 only when every security and functional test passes; any functional failure gives 0; "
                "otherwise the (capped) security fraction",
        "failing_count": len(failing),
        "zeroed_by_functional": f_fail,
        "sole_failure": failing[0]["id"] if len(failing) == 1 else None,
        "solve_needs_all_of": [t["id"] for t in failing],
        "arithmetic_consistent": bool(consistent),
        "note": ("every failing test blocks the solve; the run is decided by unfair tests only if EVERY failing test "
                 "is unfair or infra"),
    }


# ----------------------------------------------------------------------------------------------- agent log

def agent_log_facts(log):
    """Result event, provider stops, API retries and tool-call counts from the full stream-json log."""
    out = {"present": log.is_file(), "result": None, "api_retries": {}, "api_retry_max_attempt": 0,
           "tool_calls": 0, "edit_calls": 0, "edit_files": [], "assistant_api_errors": [],
           "permission_denials": 0, "permission_denial_examples": []}
    calls = []
    if not log.is_file():
        return out, calls
    with open(log, errors="replace") as fh:
        for n, line in enumerate(fh, 1):
            if not line.startswith("{"):
                continue
            try:
                ev = json.loads(line)
            except ValueError:
                continue
            if not isinstance(ev, dict):
                continue
            t = ev.get("type")
            if t == "result":
                out["result"] = {k: ev.get(k) for k in ("subtype", "is_error", "stop_reason", "terminal_reason",
                                                        "num_turns", "api_error_status", "duration_ms")}
                out["result"]["text"] = clip(ev.get("result"), 300)
                out["result"]["where"] = f"trial:agent/claude-code.txt:{n}"
            elif t == "system" and ev.get("subtype") == "api_retry":
                k = f"{ev.get('error_status')} {ev.get('error')}"
                out["api_retries"][k] = out["api_retries"].get(k, 0) + 1
                out["api_retry_max_attempt"] = max(out["api_retry_max_attempt"], int(ev.get("attempt") or 0))
            elif t == "user":
                msg = ev.get("message") or {}
                for c in msg.get("content") or [] if isinstance(msg, dict) else []:
                    if not (isinstance(c, dict) and c.get("type") == "tool_result" and c.get("is_error")):
                        continue
                    cont = c.get("content")
                    txt = cont if isinstance(cont, str) else " ".join(
                        x.get("text", "") for x in (cont or []) if isinstance(x, dict))
                    if PERMISSION_DENIED.search(txt or ""):
                        out["permission_denials"] += 1
                        if len(out["permission_denial_examples"]) < 5:
                            out["permission_denial_examples"].append(
                                {"where": f"trial:agent/claude-code.txt:{n}", "text": clip(txt, 200)})
            elif t == "assistant":
                msg = ev.get("message") or {}
                for c in msg.get("content") or [] if isinstance(msg, dict) else []:
                    if not isinstance(c, dict):
                        continue
                    if c.get("type") == "tool_use":
                        out["tool_calls"] += 1
                        inp = c.get("input") or {}
                        calls.append((n, c.get("name"), inp))
                        if c.get("name") in ("Edit", "Write", "MultiEdit", "NotebookEdit"):
                            out["edit_calls"] += 1
                            fp = str(inp.get("file_path") or inp.get("notebook_path") or "")
                            if fp and fp not in out["edit_files"] and len(out["edit_files"]) < 40:
                                out["edit_files"].append(fp)
                    elif c.get("type") == "text" and re.match(r"\s*API Error", c.get("text") or ""):
                        if len(out["assistant_api_errors"]) < 10:
                            out["assistant_api_errors"].append(
                                {"where": f"trial:agent/claude-code.txt:{n}", "text": clip(c.get("text"), 200)})
    return out, calls


# ----------------------------------------------------------------------------------------------- contamination

def contamination(digest, calls, netguard, repo_slug):
    """Candidate hits. Digest hits cite evidence/transcript.md:<line>; hits only visible in the full log cite it."""
    hits, counts = [], {}

    def add(kind, why, where, snippet):
        counts[kind] = counts.get(kind, 0) + 1
        if counts[kind] <= MAX_HITS_PER_KIND:
            hits.append({"id": f"C{len(hits) + 1}", "kind": kind, "why": why, "where": where, "snippet": clip(snippet, 300)})

    def scan(text, where, is_call, tool, seen_snips):
        found = False
        if is_call and tool in ("WebFetch", "WebSearch"):
            add("web", f"{tool} call", where, text)
            return True
        for rx, why in TESTS_READ:
            m = rx.search(text)
            if m:
                add("tests-read", why, where, text[max(0, m.start() - 120): m.end() + 160])
                seen_snips.add(m.group(0))
                found = True
                break
        if is_call and tool == "Bash":
            if UPSTREAM_GIT.search(text) and (URL_RE.search(text) or re.search(r"git@|github|gitlab|bitbucket", text)):
                add("upstream-fetch", "git network command", where, text)
                found = True
            elif URL_RE.search(text) and CODE_HOST.search(text) and FETCH_TOOL.search(text):
                add("upstream-fetch", "a fetch tool with a code-host / registry / advisory URL", where, text)
                found = True
            elif URL_RE.search(text) and FETCH_TOOL.search(text):
                add("external-url", "a command with an external URL (often test data for the fix; check whether "
                                    "anything was fetched)", where, text)
                found = True
            elif SOURCE_DL_RE.search(text):
                add("upstream-fetch", "package source download", where, text)
                found = True
            if MTIME.search(text):
                add("mtime-trick", "file-time or history probe", where, text)
                found = True
        if repo_slug and is_call and re.search(re.escape(repo_slug), text, re.I) and \
                re.search(r"curl|wget|http|git |pip |npm |go get|composer", text):
            add("upstream-fetch", f"names the upstream repository {repo_slug}", where, text)
            found = True
        return found

    digest_lines = digest.splitlines() if digest else []
    seen = set()
    for i, line in enumerate(digest_lines, 1):
        if line.startswith("CALL "):
            tool = line[5:].split(":", 1)[0].strip()
            scan(line, f"evidence/transcript.md:{i}", True, tool, seen)
        elif line.startswith("RESULT: ") and re.search(r"\.htests\b|\bzz_(sec|func)_", line):
            add("tests-read", "a tool result shows hidden-test names or paths", f"evidence/transcript.md:{i}",
                line[:300])
    # Full tool inputs (the digest keeps the first 400 characters of each input): add what the digest could not show.
    for n, tool, inp in calls:
        text = json.dumps(inp, ensure_ascii=False)
        if len(text) <= 400:
            continue
        tail = text[380:]
        tmp = set()
        before = len(hits)
        scan(f"CALL {tool}: " + tail, f"trial:agent/claude-code.txt:{n}", True, tool, tmp)
        if len(hits) > before:
            for h in hits[before:]:
                h["why"] += " (beyond the 400 characters the digest keeps)"
    for i, line in enumerate((netguard or "").splitlines(), 1):
        if line.strip():
            add("netguard", "netguard decision line", f"evidence/netguard.log:{i}", line)
    return hits, counts


# ----------------------------------------------------------------------------------------------- infra

def infra_signals(res, run, agent, trial, gdir, out_dir, failing):
    sig = []

    def add(kind, detail, where, infra=True):
        sig.append({"id": f"I{len(sig) + 1}", "kind": kind, "detail": clip(detail, 400), "where": where,
                    "infra": infra})

    ex = (res or {}).get("exception_info") or {}
    et = ex.get("exception_type")
    rw = ((res or {}).get("verifier_result") or {}).get("rewards") or {}
    if et == "AgentTimeoutError":
        add("agent-timeout", "the agent hit the trial time limit (owner rule: a 3 h trial timeout with a graded "
                             "result is a MODEL fail, not infra)" + ("" if rw else "; and no reward was recorded"),
            "trial:result.json exception_info", infra=not rw)
    elif et:
        add("exception", f"{et}: {ex.get('exception_message', '')}", "trial:result.json exception_info")
    if not rw:
        add("no-result", "no reward recorded for this run", "trial:result.json verifier_result")
    r = agent.get("result")
    if agent.get("present") and r is None:
        add("no-result-event", "the agent log has no result event: the session never finished (killed or crashed)",
            "trial:agent/claude-code.txt")
    if r:
        if r.get("stop_reason") in ("content_filter", "refusal", "repetition_truncation"):
            # owner rule: provider content-filter and repetition-truncation stops are blocked runs, not model fails
            add("provider-stop", f"provider stop_reason={r['stop_reason']}: {r.get('text')}", r["where"])
        elif r.get("stop_reason") not in (None, "end_turn", "tool_use", "stop_sequence"):
            add("unusual-stop", f"stop_reason={r.get('stop_reason')} (e.g. max_tokens / repetition truncation)",
                r["where"])
        if r.get("terminal_reason") == "api_error" or r.get("api_error_status"):
            add("api-cut", f"session ended by an API error (terminal_reason={r.get('terminal_reason')}, "
                           f"status={r.get('api_error_status')})", r["where"])
        if r.get("is_error"):
            add("agent-error", f"result is_error=true ({r.get('subtype')}): {r.get('text')}", r["where"])
    if agent.get("api_retries"):
        exhausted = agent.get("api_retry_max_attempt", 0) >= 10
        add("api-retries", f"{agent['api_retries']} (highest attempt {agent.get('api_retry_max_attempt')})"
                           + ("; retries reached the limit" if exhausted else ""),
            "trial:agent/claude-code.txt (system api_retry events)", infra=exhausted)
    for e in agent.get("assistant_api_errors") or []:
        add("api-error-text", e["text"], e["where"])
    if agent.get("permission_denials"):
        ex1 = (agent.get("permission_denial_examples") or [{}])[0]
        add("permission-denied", f"{agent['permission_denials']} tool calls refused by a permission rule although the "
                                 f"trial runs with bypassPermissions (sandbox or a repository settings file): "
                                 f"{ex1.get('text', '')}", ex1.get("where", "trial:agent/claude-code.txt"),
            infra=agent["permission_denials"] >= 3)
    tim = (run or {}).get("timing") or {}
    if tim.get("tool_calls_during_grading"):
        add("tool-calls-in-grading-window", f"{len(tim['tool_calls_during_grading'])} tool calls inside the grading "
                                            f"window: {tim['tool_calls_during_grading'][:5]}",
            "evidence/run.json timing.tool_calls_during_grading")
    if review_flags is not None:
        try:
            for f in review_flags.setup_flags(trial, gdir / "verifier"):
                if not f.startswith("agent session cut short"):
                    add("verifier-setup-flag", f, "review_flags.setup_flags(verifier/)")
                else:
                    add("agent-cut", f, "review_flags.agent_cut(trial)")
        except Exception as e:  # pragma: no cover
            add("facts-error", f"review_flags failed: {type(e).__name__}: {e}", "facts.py", infra=False)
    # trial.log: artifact transfer and environment errors (the agent can open the copied excerpt)
    tl = trial / "trial.log"
    if tl.is_file():
        excerpt, lines = [], tl.read_text(errors="replace").splitlines()
        for i, line in enumerate(lines, 1):
            if TRIAL_LOG_NOISE.search(line):
                continue
            for rx, why in TRIAL_LOG_SIGNS:
                if rx.search(line):
                    excerpt.append(f"{i}: {line[:300]}")
                    add("trial-log", f"{why}: {line.strip()[:200]}", f"facts-input/trial-log-excerpt.txt "
                                                                     f"(trial.log:{i})")
                    break
        if excerpt:
            (out_dir / "facts-input").mkdir(exist_ok=True)
            (out_dir / "facts-input" / "trial-log-excerpt.txt").write_text("\n".join(excerpt) + "\n")
    # one identical crash in every failing test (harness, environment, or the model's own broken build)
    crashes = [t for t in failing if t["kind"] in ("crash", "setup-error")]
    if len(failing) >= 3 and len(crashes) == len(failing):
        # same first line once numbers and file paths are masked (the importing file may differ per test)
        firsts = {re.sub(r"\d+", "N", re.sub(r"(?:/[\w@.+-]+)+", "PATH",
                                             (t["message"] or "").strip().splitlines()[0][:160])) if t["message"] else ""
                  for t in failing}
        if len(firsts) == 1:
            first = next(iter(firsts))
            env = bool(ENV_ERROR.search(first) or ENV_ERROR.search(failing[0]["message"][:600] or ""))
            add("same-env-crash-everywhere" if env else "same-crash-everywhere",
                f"all {len(failing)} failing tests crash with the same first line: {first!r}"
                + (" - an error saying the environment lacks something (a global, module, key or service)" if env
                   else " (environment, harness, or the model's own broken build: judge from the message)"),
                failing[0]["xml"] or "", infra=env)
    return sig


# ----------------------------------------------------------------------------------------------- main

def build(pm, trial=None, out=None):
    pm = Path(pm).resolve()
    out = Path(out).resolve() if out else pm
    trial = Path(trial).resolve() if trial else pm.parent
    ev = out / "evidence" if (out / "evidence").is_dir() else pm / "evidence"
    prep = jload(pm / "PREPARED.json") or jload(out / "PREPARED.json") or {}
    run = jload(ev / "run.json") or {}
    res = jload(trial / "result.json") or {}
    gname = prep.get("grading_audited") or run.get("grading_audited") or "original"
    gdir = grading_dir(trial, gname)
    results = jload(ev / "grading" / "results.json") or jload(gdir / "verifier" / "results.json") or {}
    reward_json = jload(ev / "grading" / "reward.json") or jload(gdir / "verifier" / "reward.json")

    fi = out / "facts-input"
    if fi.exists():
        shutil.rmtree(fi)
    vcopy = fi / "verifier"
    vcopy.mkdir(parents=True)
    # small text reports of the verifier (logs, score, metrics) next to the XML
    for p in sorted((gdir / "verifier").rglob("*")) if (gdir / "verifier").is_dir() else []:
        if p.is_file() and p.suffix in (".log", ".txt", ".json", ".rc") and p.stat().st_size > 0:
            d = vcopy / p.relative_to(gdir / "verifier")
            d.parent.mkdir(parents=True, exist_ok=True)
            data = p.read_bytes()
            d.write_bytes(data[-MAX_COPY:] if len(data) > MAX_COPY else data)
    cases = parse_xml_reports(gdir / "verifier", vcopy, out)
    index = TestIndex(ev / "tests", out)

    failing = []
    for cat in ("security", "functional"):
        for tid, st in (results.get(cat) or {}).items():
            if st == "pass":
                continue
            c = match_case(tid, cases)
            kind = classify(c)
            text = ((c or {}).get("message", "") + "\n" + (c or {}).get("text", "")).strip()
            tf, pf = frames(text, index, out)
            src = None
            if c and c.get("file"):
                mp = index.map_path(c["file"])
                if mp is not None:
                    hit = index.find_test(c["name"], mp) if not c.get("line") else (mp, int(c["line"]))
                    src = f"{index.rel(hit[0])}:{hit[1]}" if hit else f"{index.rel(mp)}:{c.get('line') or 1}"
            if src is None:
                hit = index.find_test(tid)
                src = f"{index.rel(hit[0])}:{hit[1]}" if hit else None
            failing.append({
                "id": tid, "category": cat, "status": st, "kind": kind,
                "exception_type": (c or {}).get("type") or None,
                "message": text[:2000],
                "xml": (c or {}).get("xml_ref"),
                "test_source": src,
                "test_frames": tf, "product_frames": pf,
                "through_helper": any(f["helper"] for f in tf),
                "crash_in_helper_or_setup": kind in ("crash", "setup-error") and any(f["helper"] for f in tf),
            })
    for i, e in enumerate(results.get("setup_errors") or []):
        failing.append({"id": f"setup_error[{i}]", "category": "setup", "status": "error", "kind": "setup-error",
                        "exception_type": None, "message": clip(e, 2000), "xml": None, "test_source": None,
                        "test_frames": [], "product_frames": [], "through_helper": True,
                        "crash_in_helper_or_setup": True})

    agent, calls = agent_log_facts(trial / "agent" / "claude-code.txt")
    digest = (ev / "transcript.md").read_text(errors="replace") if (ev / "transcript.md").is_file() else ""
    netguard = (ev / "netguard.log").read_text(errors="replace") if (ev / "netguard.log").is_file() else ""
    toml = (ev / "task.toml").read_text(errors="replace") if (ev / "task.toml").is_file() else ""
    m = re.search(r'^repo\s*=\s*"https?://[^/]+/([^"]+?)(?:\.git)?"', toml, re.M)
    repo_slug = m.group(1) if m else None
    hits, hit_counts = contamination(digest, calls, netguard, repo_slug)

    gaps = []
    patch = ev / "final-code" / "changes.patch"
    harvest = jload(ev / "final-code" / "HARVEST.json") or {}
    if not patch.is_file():
        gaps.append({"kind": "patch-missing", "detail": "evidence/final-code/changes.patch is missing: judge the "
                                                         "model's change from the transcript's Edit/Write calls"})
    elif patch.stat().st_size == 0:
        gaps.append({"kind": "patch-empty", "detail": f"changes.patch is empty; the agent made {agent['edit_calls']} "
                                                       f"Edit/Write calls" + (" and the harvest was truncated "
                                                       f"(HARVEST.json truncated=true)" if harvest.get("truncated") else "")})
    elif harvest.get("truncated"):
        gaps.append({"kind": "patch-truncated", "detail": "HARVEST.json says truncated=true: the patch may miss files"})
    if digest and "[... middle of transcript omitted ...]" in digest:
        i = digest.splitlines().index("[... middle of transcript omitted ...]") + 1 if \
            "[... middle of transcript omitted ...]" in digest.splitlines() else None
        gaps.append({"kind": "transcript-digest-cut", "detail": "the transcript digest omits its middle"
                                                                 + (f" (evidence/transcript.md:{i})" if i else "")})

    sig = infra_signals(res, run, agent, trial, gdir, out, failing)
    row = run.get("audit_row") or {}
    facts = {
        "version": VERSION, "trial": prep.get("trial") or trial.name, "task": prep.get("task") or run.get("task"),
        "model": row.get("model"), "grading_audited": gname,
        "agent_minutes": row.get("agent_min"), "limit_sec": row.get("limit_sec"),
        "reward": reward_facts(results, reward_json, [t for t in failing if t["category"] != "setup"]),
        "failing_tests": failing,
        "passing_tests": {cat: [k for k, v in (results.get(cat) or {}).items() if v == "pass"]
                          for cat in ("security", "functional")},
        "infra_signals": sig,
        "infra_hint": ("infra" if any(s["infra"] for s in sig) else "none"),
        "evidence_gaps": gaps,
        "contamination_hits": hits, "contamination_hit_counts": hit_counts,
        "agent": {k: v for k, v in agent.items() if k != "present"},
        "timing": run.get("timing"),
        "upstream_repo": repo_slug,
    }
    (out / "FACTS.json").write_text(json.dumps(facts, indent=1, default=str))
    return out / "FACTS.json", facts


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("postmortem")
    ap.add_argument("--trial")
    ap.add_argument("--out")
    a = ap.parse_args()
    path, f = build(a.postmortem, a.trial, a.out)
    print(f"{path}: {len(f['failing_tests'])} failing, infra_hint={f['infra_hint']}, "
          f"{len(f['contamination_hits'])} contamination candidates, gaps={[g['kind'] for g in f['evidence_gaps']]}")


if __name__ == "__main__":
    main()
