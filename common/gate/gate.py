#!/usr/bin/env python3
"""Deterministic acceptance gate for one built task.

    gate.py <slug> [--only static|nop|oracle|patches] [--keep-jobs]

Layout it expects (paths relative to cwe-bench/):
    tasks/<slug>/   instruction.md task.toml environment/ solution/ tests/
    build/<slug>/   manifest.json  checks/*.patch

Checks, in order (it stops at the first failing group):
  static   required files, metadata, agent layer, no leaks in instruction.md,
           no hidden test content in environment/ (the image), no security test
           asserting one exact refusal status, and (warning, or failure when
           manifest["strict_gate"]) pass patches of kind 'hardening' and 'blind';
           reports each security test's product imports.
           Since 2026-10-16 every task must be offline ([agent] allowlist of the
           model APIs only) and its test.sh must kill the agent before grading.
           strict_gate is ON unless the manifest sets "strict_gate": false (only
           the 19 round-1 tasks do). Strict adds: hardening + blind pass patches,
           a wrong-fix catalogue entry for every class in WRONG_FIX_CLASSES,
           and 3 oracle runs. (FAIRNESS.md is written after the trial, not gated.)
  nop      untouched vulnerable code: every security test FAILS, every
           functional test PASSES
  oracle   reference fix, run twice (3x under strict_gate): reward 1.0 and identical results
  patches  every patch listed in manifest["patch_checks"] behaves as declared:
             security_fail    at least one security test fails, functional all pass
             functional_fail  at least one functional test fails
             pass             reward 1.0 (an independent correct fix)

The result is written to build/<slug>/gate_report.json (gate_report.partial.json with --only).
Decisions here are made by scripts only; no model judgement is involved.

Every failure is classified, because confusing the kinds is what kept marking sound tasks
unsound (and retrying real failures as "flakes") until 2026-10-20:
  task      the task itself is wrong; deterministic, retrying cannot help      exit 1
  infra     Docker / Harbor / host trouble; says nothing about the task; retry exit 2
  internal  the gate itself crashed (a bug here); neither of the above         exit 3
The report's top-level "verdict" is pass / task / infra / internal, and the failing stage is
always written into "stages" with ok=false, its "kind" and its "error", so a caller never has
to guess from a missing key. Failures that name failing tests carry "evidence": the first
error messages from the tests' JUnit XML (a compile error reads very differently from an
assertion).

Every failure also writes a FULL evidence file, build/<slug>/evidence/<UTC>-gate-<stage>.txt
(+ .json; common/util/evidence.py): the exception's class, complete message and traceback (Harbor's
exception_traceback included), every failing test's complete output, the verifier stdout, Harbor's
stdout/stderr and the raw artifact paths. The stage record names it in "evidence_file".
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import traceback
import xml.etree.ElementTree as ET
from pathlib import Path

try:
    import tomllib  # Python 3.11+
    def load_toml(text: str) -> dict:
        return tomllib.loads(text)
except ModuleNotFoundError:  # 3.9/3.10 host without tomllib
    def load_toml(text: str) -> dict:
        """Minimal reader for our own task.toml: flat tables of key = scalar.
        Enough for the metadata/verifier fields the gate inspects; not a full
        TOML parser."""
        import ast
        data = {}
        cur = data
        for raw in text.splitlines():
            line = raw.split("#", 1)[0].strip()
            if not line:
                continue
            if line.startswith("[") and line.endswith("]"):
                cur = data
                for part in line[1:-1].split("."):
                    cur = cur.setdefault(part.strip(), {})
                continue
            if "=" not in line:
                continue
            key, _, val = line.partition("=")
            key, val = key.strip(), val.strip()
            try:
                cur[key] = ast.literal_eval(val)
            except (ValueError, SyntaxError):
                cur[key] = val.strip('"').strip("'")
        return data

sys.path.insert(0, str(next(p for p in Path(__file__).resolve().parents if (p / ".cwe-bench-root").is_file()) / "common"))
import paths  # noqa: E402  (repo locations: common/paths.py)

ROOT = paths.ROOT
JOBS = Path.home() / ".tb-graders" / "cwe" / "gate-jobs"
sys.path.insert(0, str(paths.UTIL))
sys.path.insert(0, str(paths.BUILDER_DIR))  # so sibling imports resolve under `python3 -I`
import evidence as ev  # noqa: E402  (full error evidence: common/util/evidence.py)
import conformance_check  # noqa: E402  (Frontier-SWE delivery-format enforcement; common/builder/ on path for -I)
REQUIRED = [
    "instruction.md",
    "task.toml",
    "environment/Dockerfile",
    "solution/solve.sh",
    "solution/fix.patch",
    "tests/Dockerfile",
    "tests/test.sh",
    "tests/score.py",
]
META_KEYS = ["cwe_id", "language", "repo", "source", "entry_point"]
MIN_SECURITY, MIN_FUNCTIONAL = 4, 5
MODEL_HOSTS = {"api.deepseek.com", "api.xiaomimimo.com"}
AGENT_KILL_MARK = "@anthropic-ai/claude-code"   # the kill block from templates/test.sh
MIN_DOCKER_FREE_GB = 15   # the Colima disk (79 GB) filled twice on 2026-10-16 and broke 6+ gate runs
# Wrong fixes the round-1 audits found passing (or correct fixes failing) only AFTER trials
# (docs/research/round1-analysis/B-failure-modes.md, C-pipeline-lessons.md). A strict task names, for each
# class, the checks/ patch that proves the tests catch it, or "n/a: <why the class cannot apply>".
WRONG_FIX_CLASSES = {
    "refuse_all": "deny/refuse everything on the protected path (needs a positive control test)",
    "crash_as_refusal": "crash, panic or HTTP 500 instead of a clean refusal",
    "wrong_resource": "authorises a neighbouring/proxy resource instead of the object touched",
    "one_role_or_direction": "fixes only one role, peer or direction",
    "reads_only": "guards reads but not writes (or one verb only)",
    "check_after_adjustment": "guard placed after a normalising/adjusting step on the attacker value",
    "unlisted_route": "blocks the reported route/fields, not a merged/default/other route to the same sink",
    "malformed_identity": "parser mismatch: a malformed spelling makes the guard see nothing",
    "missing_authority": "fail-open when the authority returns no secret/role",
    "adjacent_api": "a shared-helper fix that changes a sibling API's stated behaviour",
}
# Infrastructure errors worth one immediate in-place retry (Docker name lookups are flaky here).
RETRYABLE = ("NetworkConnectionError", "Could not resolve", "ENOTFOUND", "TLS handshake")
# Known infrastructure signatures, seen on the VM, and the label the report gives them. Any
# exception Harbor records for a trial is infrastructure (the trial did not run to a result);
# the label only says which kind, so a person can tell a load flake from a broken Dockerfile.
INFRA_SIGNATURES = [
    (r"network \S+ not found", "docker network vanished between create and attach"),
    (r"context deadline exceeded|Client\.Timeout|i/o timeout", "docker/compose timeout under load"),
    (r"only one connection allowed", "buildkit session collision"),
    (r"Cannot connect to the Docker daemon|error during connect", "docker daemon unreachable"),
    (r"no space left on device", "disk full"),
    (r"NetworkConnectionError|Could not resolve|ENOTFOUND|TLS handshake|connection reset"
     r"|Temporary failure in name resolution", "network / DNS"),
    (r"toomanyrequests|rate limit", "registry rate limit"),
    (r"is already in use by container|Conflict\. The container name", "container name conflict"),
    (r"returned a non-zero code|failed to solve|executor failed running",
     "environment image build step failed (a broken Dockerfile repeats every retry)"),
    (r"TimeoutError|timed out", "a trial phase timed out (load, or a hang in the task if it repeats)"),
]
# Lines that make a failing test a build/collection problem rather than an assertion.
BUILD_ERROR = re.compile(r"\[build failed\]|build failed|cannot find|undefined|ImportError|"
                         r"ModuleNotFoundError|SyntaxError|error TS\d+|compil|cannot resolve symbol",
                         re.I)
# The VM gates and trials with DOCKER_BUILDKIT=0 (common/gate/docker-tuning.env). The classic builder
# does not feed a heredoc body to its command, so the build "succeeds" with an empty file: fission-ds
# lost its whole injection this way on 2026-10-19/20 and every stage then failed to compile.
HEREDOC = re.compile(r"""(?m)^[^#\n]*<<-?\s*['"]?[A-Za-z_]+""")


class GateFailure(Exception):
    """The task itself is wrong: a deterministic result contradicts what the gate requires."""
    kind = "task"

    def __init__(self, message: str, evidence=None, details=None):
        super().__init__(message)
        self.evidence = evidence or []    # short lines for the report and the log
        self.details = details or {}      # everything, for the evidence file (common/util/evidence.py)


class InfraError(GateFailure):
    """Docker, Harbor or the host failed: the trial produced no result about the task."""
    kind = "infra"


def infra_label(text: str) -> str:
    for pattern, label in INFRA_SIGNATURES:
        if re.search(pattern, text):
            return label
    return "unclassified infrastructure error"


def failure_evidence(trial_dir, limit: int = 3) -> list:
    """First error messages of failing tests from the trial's JUnit XML, build errors first."""
    found = []
    for xml in sorted(Path(trial_dir, "verifier").rglob("*.xml")):
        try:
            root = ET.parse(xml).getroot()
        except (ET.ParseError, OSError):
            continue
        for case in root.iter("testcase"):
            for bad in list(case.findall("failure")) + list(case.findall("error")):
                text = ((bad.get("message") or "") + "\n" + (bad.text or "")).strip()
                name = f"{case.get('classname', '')}::{case.get('name', '')}"
                if text:
                    found.append((0 if BUILD_ERROR.search(name + text) else 1, name, text[:600]))
    found.sort(key=lambda f: f[0])
    out, seen = [], set()
    for _, name, text in found:
        head = text.splitlines()[0]
        if head in seen:
            continue
        seen.add(head)
        out.append(f"{name}: {text}")
        if len(out) == limit:
            break
    return out


def dockerfile_problems(task_dir: Path) -> list:
    text = _text(task_dir / "environment" / "Dockerfile") or ""
    hits = [m.group(0).strip() for m in HEREDOC.finditer(text)]
    if hits:
        return [f"environment/Dockerfile uses a heredoc ({hits[0][:80]}); the classic builder "
                f"(DOCKER_BUILDKIT=0) drops its body, so the image silently lacks it. "
                f"Move the body into a file under environment/ and COPY it"]
    return []


def docker_free_gb():
    """Free GB on the Docker disk (the Colima VM's on the Mac, the local one on Linux), or None."""
    try:
        out = subprocess.run(["colima", "ssh", "--", "df", "-BG", "/var/lib/docker"],
                             capture_output=True, text=True, timeout=60).stdout.split()
        return int(out[-3].rstrip("G"))
    except Exception:
        pass
    try:  # Linux host (client VM): Docker's data lives under /var/lib on the root disk
        import shutil
        return shutil.disk_usage("/var/lib").free // 2**30
    except Exception:
        return None


def wait_for_disk():
    """Wait (up to 30 min) until the Docker disk has MIN_DOCKER_FREE_GB free; a full disk
    otherwise surfaces as a confusing build or test failure."""
    for _ in range(30):
        free = docker_free_gb()
        if free is None or free >= MIN_DOCKER_FREE_GB:
            return
        print(f"[gate] Docker disk has {free} GB free (< {MIN_DOCKER_FREE_GB}); waiting", flush=True)
        time.sleep(60)
    raise InfraError(f"Docker disk below {MIN_DOCKER_FREE_GB} GB free for 30 min")


def run_harbor(task_dir: Path, agent: str, label: str) -> dict:
    """Run one Harbor trial and return {'reward', 'security', 'functional', 'trial_dir'}.
    Raises InfraError when the trial produced no result about the task, GateFailure when the
    task's own files make the result meaningless."""
    problems = dockerfile_problems(task_dir)
    if problems:
        raise GateFailure(f"{label}: " + "; ".join(problems))
    wait_for_disk()
    # No network prune here (removed 2026-10-20): pruning raced concurrent compose runs
    # ("network ... not found"), and daemon.json now gives 172.16.0.0/12 in /24 pools
    # (~4096 networks), so address-pool exhaustion is no longer a risk.
    for attempt in (1, 2):
        name = f"{task_dir.name}-{label}-{int(time.time())}"
        cmd = ["harbor", "run", "-p", str(task_dir), "-a", agent, "-o", str(JOBS),
               "--job-name", name, "-y", "-q", "--allow-agent-host", "api.deepseek.com"]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        trials = [p for p in (JOBS / name).glob("*/") if (p / "result.json").exists()]
        if not trials:
            out = f"{proc.stdout}\n{proc.stderr}"
            if attempt == 1:
                time.sleep(30)  # transient harbor launch collision under load; retry once
                continue
            raise InfraError(f"{label}: Harbor produced no trial (exit {proc.returncode}; {infra_label(out)}): "
                             f"{ev.one_line(proc.stderr or proc.stdout, 600)}",
                             details={**ev.collect(None, proc), "job_dir": str(JOBS / name)})
        trial = trials[0]
        try:
            result = json.loads((trial / "result.json").read_text())
        except (json.JSONDecodeError, OSError) as e:
            raise InfraError(f"{label}: unreadable {trial}/result.json ({type(e).__name__}: {e})",
                             details=ev.collect(trial, proc))
        exc = result.get("exception_info")
        if exc:
            text = json.dumps(exc)
            if attempt == 1 and any(r in text for r in RETRYABLE):
                continue
            # Full message and Harbor's traceback go to the evidence file; the line names the class,
            # the infra signature and the start of the message.
            raise InfraError(f"{label}: trial raised {exc.get('exception_type')} [{infra_label(text)}]: "
                             f"{ev.one_line(exc.get('exception_message'), 1500)}",
                             details=ev.collect(trial, proc))
        detail = trial / "verifier" / "results.json"
        if not detail.exists():
            stdout = _text(trial / "verifier" / "test-stdout.txt") or ""
            if stdout.strip():
                # test.sh ran and crashed before scoring: the task's verifier is broken.
                raise GateFailure(f"{label}: tests ran but wrote no results.json; test-stdout ends: "
                                  f"{ev.one_line(stdout[-1500:], 1500)}", failure_evidence(trial),
                                  details=ev.collect(trial, proc))
            raise InfraError(f"{label}: the verifier produced no output at all (container died?); "
                             f"see {trial}/verifier", details=ev.collect(trial, proc))
        try:
            data = json.loads(detail.read_text())
        except (json.JSONDecodeError, OSError) as e:
            raise GateFailure(f"{label}: score.py wrote an unreadable results.json ({type(e).__name__}: {e})",
                              details=ev.collect(trial, proc))
        missing = [k for k in ("reward", "security", "functional") if k not in data]
        if missing:
            raise GateFailure(f"{label}: results.json lacks {missing} (score.py is broken)",
                              details=ev.collect(trial, proc))
        data["trial_dir"] = str(trial)
        return data
    raise InfraError(f"{label}: infrastructure error twice ({infra_label(text)})")


def failing(group: dict) -> list:
    return sorted(k for k, v in group.items() if v != "pass")


# Names of security tests, per language. A name found in environment/ means the hidden
# tests (or a copy of them) would be inside the image the agent works in.
TEST_NAME_PATTERNS = [
    r"\bfn\s+(\w{6,})\s*\(",                          # Rust
    r"\bfunc\s+(Test\w+)\s*\(",                       # Go
    r"\bdef\s+(test_\w+)\s*\(",                       # Python, Ruby
    r"@Test[^\n]*\n\s*(?:public\s+|private\s+)?void\s+(\w+)\s*\(",  # Java
    r"\bfunction\s+(test\w+)\s*\(",                   # PHP
    r"\b(?:it|test)\(\s*['\"`]([^'\"`\n]{12,})['\"`]",  # JS / TS / Pest
    r"\bit\s+['\"]([^'\"\n]{12,})['\"]",              # Ruby rspec
]
RUNNER_FILES = {"test.sh", "score.py"}
# Test definitions of any kind. environment/ may hold build-cache stubs, never tests:
# this also catches tests that live ONLY in the image (russh did, with nothing in tests/).
TEST_DEF_PATTERNS = [r"#\[(?:tokio::)?test\b", r"\bfunc\s+Test\w*\s*\(\s*\w+\s+\*testing\.T\)",
                     r"(?m)^\s*def\s+test_\w+", r"@Test\b", r"(?m)^\s*(?:it|test|describe)\s*\(",
                     r"\bfunction\s+test\w+\s*\(", r"(?m)^\s*it\s+['\"]"]


def _text(path: Path):
    try:
        return path.read_text()
    except (UnicodeDecodeError, OSError):
        return None


def hidden_test_leaks(task: Path) -> list:
    """Hidden tests must reach the container only at grading time (from /tests).
    Everything the image contains comes from environment/ (the build context), so it
    is enough to check that folder for copies of, or pieces of, the hidden tests."""
    env_files = [p for p in (task / "environment").rglob("*") if p.is_file()]
    test_files = [p for p in (task / "tests").rglob("*") if p.is_file() and p.name not in RUNNER_FILES and p.name != "Dockerfile"]
    env_text = {p: _text(p) for p in env_files}
    leaks = []
    by_hash = {}
    for t in test_files:
        by_hash.setdefault(t.read_bytes(), []).append(t)
    for e in env_files:
        if e.name != "Dockerfile" and e.read_bytes() in by_hash:
            leaks.append(f"{e.relative_to(task)} is a copy of {by_hash[e.read_bytes()][0].relative_to(task)}")
    names, lines = set(), set()
    for t in test_files:
        src = _text(t)
        if src is None:
            continue
        rel = str(t.relative_to(task / "tests"))
        if rel.startswith(("security", "harness")):
            for pat in TEST_NAME_PATTERNS:
                names.update(re.findall(pat, src))
        for line in src.splitlines():
            s = line.strip()
            if len(s) >= 30 and not re.match(r"(import |use |package |from |#include|require|//|#|\*|/\*)", s):
                lines.add(s)
    names = {n for n in names if n not in ("main", "setup", "teardown", "TestMain")}
    for e, txt in env_text.items():
        # Skip the agent Dockerfile: in separate mode it is the agent image (no tests inside), and it
        # legitimately shares base-image/apt/user boilerplate with the verifier image (tests/Dockerfile).
        if not txt or e.name == "Dockerfile":
            continue
        defs = [p for p in TEST_DEF_PATTERNS if re.search(p, txt)]
        if defs:
            leaks.append(f"{e.relative_to(task)} defines tests (matched {defs[0]}); "
                         "only build-cache stubs may be in environment/")
        found = sorted(n for n in names if re.search(rf"(?<![\w]){re.escape(n)}(?![\w])", txt))
        if found:
            leaks.append(f"{e.relative_to(task)} contains security test names: {', '.join(found[:5])}")
        shared = sum(1 for s in lines if s in txt)
        if shared >= 3:
            leaks.append(f"{e.relative_to(task)} shares {shared} distinctive lines with tests/")
    return sorted(set(leaks))


# A security test must assert that the attack is BLOCKED, not how: an exact refusal status
# (only 405, only 403, ...) fails correct fixes that refuse differently (trigger-dev 405,
# argo 403; analysis 2026-10-16, docs/research/own-runs/FINDINGS.md). A line may keep an exact
# status after review by carrying the marker below.
EXACT_STATUS_OK = "gate: exact-status-ok"
EXACT_STATUS_PATTERNS = [
    r"==\s*4\d\d\b",                                       # py/js/java: code == 405 (not Go, see below)
    r"\b4\d\d\s*==",                                        # 405 == code
    r"\.toBe\(\s*4\d\d\s*\)|\.toEqual\(\s*4\d\d\s*\)|\.toStrictEqual\(\s*4\d\d\s*\)",
    r"assertEquals\(\s*4\d\d\s*,",
    # Go: `if code != http.StatusForbidden { t.Fatal }` demands one status; `==` forbids one (fine)
    r"!=\s*(?:http\.Status(?:BadRequest|Unauthorized|Forbidden|NotFound|MethodNotAllowed|"
    r"RequestEntityTooLarge|Conflict|UnprocessableEntity|TooManyRequests)\b|4\d\d\b)",
    r"\.status\(\)\.is(?:Forbidden|Unauthorized|NotFound|MethodNotAllowed)\(\)",
    # Laravel / Livewire (filament demanded assertForbidden(); a correct fix threw instead)
    r"->assert(?:Forbidden|Unauthorized|NotFound|MethodNotAllowed)\(\)|->assertStatus\(\s*4\d\d\s*\)",
]
TEST_EXTS = (".py", ".js", ".ts", ".mjs", ".go", ".java", ".kt", ".rb", ".php", ".rs")


def security_test_files(task: Path) -> list:
    """Security test sources: tests/security/** plus security tests placed under tests/harness/
    (Go/Rust/Java tasks put them inside the product tree at grading time)."""
    out = []
    for p in (task / "tests").rglob("*"):
        if not p.is_file() or p.suffix not in TEST_EXTS:
            continue
        rel = str(p.relative_to(task / "tests"))
        if rel.startswith("security/") or (rel.startswith("harness/") and re.search(r"sec", p.name, re.I)):
            out.append(p)
    return sorted(out)


def exact_status_asserts(task: Path) -> list:
    found = []
    for p in security_test_files(task):
        src = _text(p) or ""
        for n, line in enumerate(src.splitlines(), 1):
            if EXACT_STATUS_OK in line or re.match(r"\s*(#|//|\*)", line):
                continue
            pats = EXACT_STATUS_PATTERNS[-2:-1] if p.suffix == ".go" else EXACT_STATUS_PATTERNS
            if any(re.search(pat, line) for pat in pats):
                found.append(f"{p.relative_to(task)}:{n}: {line.strip()[:100]}")
    return found


PRODUCT_IMPORT_PATTERNS = [
    r"""from\s+['"](@ss/[^'"]+|/app/[^'"]+|/workspace/[^'"]+)['"]""",             # js/ts aliases into the product
    r"""require\(\s*['"](@ss/[^'"]+|/app/[^'"]+|/workspace/[^'"]+)['"]\s*\)""",
    r"^\s*from\s+([A-Za-z_][\w.]*)\s+import",                     # python
    r"^\s*import\s+([A-Za-z_][\w.]*)",
    r"^\s*import\s+(?:static\s+)?([a-z][\w.]*\.[A-Z]\w*)\s*;",    # java
]
PY_STDLIB_OR_TEST = {"__future__", "pytest", "os", "sys", "re", "json", "time", "uuid", "base64", "typing",
                     "contextlib", "importlib", "sqlite3", "pathlib", "subprocess", "socket", "http",
                     "urllib", "tempfile", "shutil", "hashlib", "hmac", "datetime", "random", "string",
                     "conftest", "tr", "fastapi", "httpx", "requests", "cryptography", "unittest"}


def product_imports(task: Path) -> dict:
    """What product code each security test imports. Reported (not judged): a test that uses
    product code to compute its expected value or to clean up breaks when a fix hardens that
    code (actualbudget getPathForUserFile). The hardening patch check must cover these."""
    out = {}
    for p in security_test_files(task):
        if p.suffix == ".go":
            continue                     # Go security tests live inside the product package
        src = _text(p) or ""
        mods = set()
        for pat in PRODUCT_IMPORT_PATTERNS:
            for m in re.finditer(pat, src, flags=re.M):
                mod = m.group(1)
                if p.suffix == ".py" and mod.split(".")[0] in PY_STDLIB_OR_TEST:
                    continue
                if p.suffix == ".java" and mod.startswith(("java.", "javax.", "org.junit")):
                    continue
                mods.add(mod)
        if mods:
            out[str(p.relative_to(task))] = sorted(mods)
    return out


def variant_patch_warnings(manifest: dict) -> list:
    """Every task needs two extra independent 'pass' patches besides the alternative fix:
      kind=hardening  the reference fix plus defensive hardening of the product code the tests
                      import (a correct, stricter fix must still score 1.0)
      kind=blind      a fix written by a fresh agent that saw ONLY instruction.md and the repo
                      (the existing alternative fixes were written knowing the reference). The
                      same agent is asked to name the injected mechanisms; if it can, the
                      instruction leaks them (jackson-sib7) and must be rewritten.
    Warnings for tasks built before 2026-10-16; failures when manifest["strict_gate"] is true."""
    kinds = {c.get("kind") for c in manifest.get("patch_checks", []) if c.get("expect") == "pass"}
    return [f"manifest.patch_checks has no expect=pass patch with kind='{k}'"
            for k in ("hardening", "blind") if k not in kinds]


def strict(manifest: dict) -> bool:
    """strict_gate is the default; only the 19 round-1 tasks opt out (their gates predate it)."""
    return manifest.get("strict_gate", True) is not False


def catalogue_problems(build: Path, manifest: dict) -> list:
    cat = manifest.get("wrong_fix_catalogue", {})
    declared = {c.get("patch"): c.get("expect") for c in manifest.get("patch_checks", [])}
    out = []
    for cls in WRONG_FIX_CLASSES:
        v = str(cat.get(cls, "")).strip()
        if not v:
            out.append(f"wrong_fix_catalogue.{cls} missing (a checks/ patch or 'n/a: <reason>')")
        elif v.lower().startswith("n/a"):
            if len(v) < 12:
                out.append(f"wrong_fix_catalogue.{cls}: 'n/a' needs a reason")
        elif v not in declared:
            out.append(f"wrong_fix_catalogue.{cls}: patch {v} is not listed in patch_checks")
        elif declared[v] == "pass":
            out.append(f"wrong_fix_catalogue.{cls}: {v} is a wrong fix, so it must expect a failure")
    return out


def check_static(task: Path, build: Path, manifest: dict) -> dict:
    problems = []
    for rel in REQUIRED:
        if not (task / rel).is_file():
            problems.append(f"missing {rel}")
    if problems:
        raise GateFailure("; ".join(problems))

    toml = load_toml((task / "task.toml").read_text())
    meta = toml.get("metadata", {})
    for key in META_KEYS:
        if not str(meta.get(key, "")).strip():
            problems.append(f"task.toml [metadata].{key} is empty")
    if meta.get("source") not in ("mined", "mined+injected", "injected", "stacking", "mined+stacking"):
        problems.append("task.toml [metadata].source must be mined, mined+injected, injected, stacking or mined+stacking")

    docker = (task / "environment/Dockerfile").read_text()
    if "claude-code-releases/bootstrap.sh" not in docker:
        problems.append("Dockerfile lacks the agent layer (common/trial/claude-code.Dockerfile.snippet)")
    if ".git" not in docker:
        problems.append("Dockerfile does not remove the repository's .git history")
    # The agent and the verifier share one container: hidden tests baked into the image
    # can be read and run by the agent (it happened: hickory-dns, rclone*, russh*).
    for leak in hidden_test_leaks(task):
        problems.append("hidden tests leak into the image: " + leak)

    # Leaks: the report must not name the advisory, the fix, or where the fix goes.
    instr = (task / "instruction.md").read_text()
    low = instr.lower()
    leaks = [m for m in re.findall(r"CVE-\d{4}-\d+|GHSA-[0-9a-z-]{10,}", instr, flags=re.I)]
    for sha_key in ("fix_commit", "vulnerable_commit"):
        sha = str(meta.get(sha_key, ""))
        if len(sha) >= 7 and sha[:7].lower() in low:
            leaks.append(f"{sha_key} sha")
    fix = (task / "solution/fix.patch").read_text()
    for path in sorted(set(re.findall(r"^\+\+\+ b/(\S+)", fix, flags=re.M))):
        base = path.rsplit("/", 1)[-1]
        if path.lower() in low or re.search(rf"(?<![\w.]){re.escape(base.lower())}(?![\w])", low):
            leaks.append(f"file named in the fix: {base}")
    for term in manifest.get("leak_terms", []):
        if term and re.search(rf"(?<![\w]){re.escape(term.lower())}(?![\w])", low):
            leaks.append(f"leak term: {term}")
    if leaks:
        problems.append("instruction.md leaks: " + ", ".join(sorted(set(leaks))))
    if len(instr.split()) < 60:
        problems.append("instruction.md is under 60 words; a real report states impact and trigger")

    declared = {c.get("patch") for c in manifest.get("patch_checks", [])}
    for c in manifest.get("patch_checks", []):
        if c.get("kind") != "blind" and not (build / "checks" / str(c.get("patch"))).is_file():
            problems.append(f"patch check file missing: checks/{c.get('patch')}")
    kinds = {c.get("expect") for c in manifest.get("patch_checks", [])}
    for need in ("security_fail", "functional_fail"):
        if need not in kinds:
            problems.append(f"manifest.patch_checks has no '{need}' patch")
    exact = exact_status_asserts(task)
    if exact:
        problems.append("security tests assert one exact refusal status (assert the attack is blocked, "
                        f"e.g. any 4xx; or mark a reviewed line '{EXACT_STATUS_OK}'): " + " | ".join(exact))
    # Frontier-SWE delivery format (separate verifier, offline/no-allowlist, /workspace, uid-1000,
    # canary GUID, metadata, no test-mention): enforced by the machinery, not a build prompt.
    problems.extend(conformance_check.problems(task))
    warnings = variant_patch_warnings(manifest)
    if strict(manifest):
        problems.extend(warnings)
        problems.extend(catalogue_problems(build, manifest))
    if problems:
        raise GateFailure("; ".join(problems))
    return {"ok": True, "patch_checks": sorted(declared), "warnings": warnings,
            "security_test_product_imports": product_imports(task)}


def check_nop(task: Path) -> dict:
    r = run_harbor(task, "nop", "nop")
    sec, fun = r["security"], r["functional"]
    problems = []
    if len(sec) < MIN_SECURITY:
        problems.append(f"only {len(sec)} security tests (need {MIN_SECURITY}+)")
    if len(fun) < MIN_FUNCTIONAL:
        problems.append(f"only {len(fun)} functional tests (need {MIN_FUNCTIONAL}+)")
    passing_sec = sorted(k for k, v in sec.items() if v == "pass")
    if passing_sec:
        problems.append(f"security tests that PASS on vulnerable code (not exploits): {passing_sec}")
    if failing(fun):
        problems.append(f"functional tests that fail on vulnerable code: {failing(fun)}")
    if problems:
        raise GateFailure("nop: " + "; ".join(problems), failure_evidence(r["trial_dir"]),
                              details=ev.collect(r["trial_dir"]))
    return {"ok": True, "security": len(sec), "functional": len(fun), "trial": r["trial_dir"]}


def run_parallel(jobs: list, raise_errors: bool = True) -> list:
    """Run independent Harbor trials at the same time (2026-10-24: the runs inside one stage are
    independent; sequential runs made a gate ~45 min). Returns results in input order and raises
    the first error in input order, so the verdict is the one the sequential loop would reach.
    GATE_PARALLEL caps how many run at once (default: all)."""
    import concurrent.futures as cf
    if not jobs:
        return []
    width = max(1, min(len(jobs), int(os.environ.get("GATE_PARALLEL", "0") or 0) or len(jobs)))
    with cf.ThreadPoolExecutor(max_workers=width) as pool:
        futs = []
        for i, job in enumerate(jobs):
            futs.append(pool.submit(job))
            if i < len(jobs) - 1:
                time.sleep(2)  # small stagger: distinct --job-name timestamps, gentler compose fill
        outcomes = []
        for f in futs:
            try:
                outcomes.append((f.result(), None))
            except Exception as e:  # keep order: report the first failing job, as sequential did
                outcomes.append((None, e))
    if not raise_errors:
        return [err if err is not None else r for r, err in outcomes]
    for _, err in outcomes:
        if err is not None:
            raise err
    return [r for r, _ in outcomes]


def check_oracle(task: Path, n: int = 2) -> dict:
    runs = run_parallel([lambda i=i: run_harbor(task, "oracle", f"oracle{i}") for i in range(1, n + 1)])
    for i, r in enumerate(runs, 1):
        bad = failing(r["security"]) + failing(r["functional"])
        if r["reward"] != 1.0 or bad:
            raise GateFailure(f"oracle run {i}: reward {r['reward']}, failing {bad}",
                              failure_evidence(r["trial_dir"]),
                              details=ev.collect(r["trial_dir"]))
    if any(r["security"] != runs[0]["security"] or r["functional"] != runs[0]["functional"] for r in runs[1:]):
        diff = sorted(k for g in ("security", "functional") for r in runs[1:]
                      for k in set(r[g]) | set(runs[0][g]) if r[g].get(k) != runs[0][g].get(k))
        raise GateFailure(f"oracle: the runs disagree (flaky tests): {diff}",
                          details={"runs": [{"trial_dir": r["trial_dir"], "security": r["security"],
                                             "functional": r["functional"]} for r in runs],
                                   "failing_tests": [t for r in runs for t in ev.junit_failures(r["trial_dir"])]})
    return {"ok": True, "trials": [r["trial_dir"] for r in runs]}


def check_patches(task: Path, build: Path, manifest: dict) -> dict:
    out = {}
    checks = [c for c in manifest.get("patch_checks", [])
              # blind fix produced later by run_blindfix; validated in the --only patches re-gate
              if not (c.get("kind") == "blind" and not (build / "checks" / c["patch"]).is_file())]

    def one(patch):
        with tempfile.TemporaryDirectory(prefix="gate-") as tmp:
            variant = Path(tmp) / task.name
            shutil.copytree(task, variant)
            shutil.copy(build / "checks" / patch, variant / "solution" / "fix.patch")
            return run_harbor(variant, "oracle", "chk-" + re.sub(r"\W+", "-", Path(patch).stem))

    # Errors are returned, not raised, so they surface in manifest order exactly as the old
    # one-at-a-time loop met them (an earlier failing patch still wins over a later infra error).
    results = run_parallel([lambda p=c["patch"]: one(p) for c in checks], raise_errors=False)
    for check, r in zip(checks, results):
        if isinstance(r, BaseException):
            raise r
        patch, expect = check["patch"], check["expect"]
        sec_bad, fun_bad = failing(r["security"]), failing(r["functional"])
        if expect == "security_fail":
            ok = bool(sec_bad) and not fun_bad
            why = "must leave a security test failing while all functional tests pass"
        elif expect == "functional_fail":
            ok = bool(fun_bad)
            why = "must break at least one functional test"
        elif expect == "pass":
            ok = r["reward"] == 1.0
            why = "is a correct fix and must score 1.0"
        else:
            raise GateFailure(f"patches: unknown expect '{expect}' for {patch}")
        out[patch] = {"expect": expect, "ok": ok, "reward": r["reward"],
                      "security_failing": sec_bad, "functional_failing": fun_bad}
        if not ok:
            raise GateFailure(f"patches: {patch} {why}; got reward {r['reward']}, "
                              f"security failing {sec_bad}, functional failing {fun_bad}",
                              failure_evidence(r["trial_dir"]),
                              details=ev.collect(r["trial_dir"]))
    return {"ok": True, "checks": out}


def write_evidence(build: Path, slug: str, stage: str, kind: str, summary: str, details: dict):
    """The full evidence file of a failed stage; never lets an evidence problem hide the failure."""
    where = build / "evidence" if build.is_dir() else JOBS.parent / "gate-evidence" / slug
    try:
        return ev.write(where, f"gate-{stage}", f"gate {slug} stage {stage}", kind, summary, details)
    except Exception as e:
        print(f"[gate] could not write the evidence file ({type(e).__name__}: {e})", file=sys.stderr)
        return None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("slug")
    ap.add_argument("--only", choices=["static", "nop", "oracle", "patches"])
    ap.add_argument("--keep-jobs", action="store_true", help="kept for compatibility; jobs are always kept")
    args = ap.parse_args()

    task, build = ROOT / "tasks" / args.slug, ROOT / "build" / args.slug
    report = {"slug": args.slug, "only": args.only, "started": time.strftime("%Y-%m-%dT%H:%M:%S"),
              "passed": False, "verdict": None, "stages": {}}
    stages = ["static", "nop", "oracle", "patches"]
    if args.only:
        stages = [args.only]
    stage = "setup"
    try:
        if not task.is_dir():
            raise GateFailure(f"no task directory {task}")
        mpath = build / "manifest.json"
        if not mpath.is_file():
            raise GateFailure(f"no manifest at {mpath}")
        try:
            manifest = json.loads(mpath.read_text())
        except json.JSONDecodeError as e:
            raise GateFailure(f"build/{args.slug}/manifest.json is not valid JSON ({e})")
        JOBS.mkdir(parents=True, exist_ok=True)
        for stage in stages:
            print(f"[gate] {args.slug}: {stage} ...", flush=True)
            if stage == "static":
                report["stages"][stage] = check_static(task, build, manifest)
            elif stage == "nop":
                report["stages"][stage] = check_nop(task)
            elif stage == "oracle":
                report["stages"][stage] = check_oracle(task, 3 if strict(manifest) else 2)
            else:
                report["stages"][stage] = check_patches(task, build, manifest)
        report["passed"] = not args.only
        report["partial"] = bool(args.only)
        report["verdict"] = "pass"
    except GateFailure as e:  # includes InfraError
        report.update(failure=str(e), verdict=e.kind, failed_stage=stage)
        efile = write_evidence(build, args.slug, stage, e.kind, str(e),
                               {**e.details, "evidence_lines": e.evidence})
        report["stages"][stage] = {"ok": False, "kind": e.kind, "error": str(e),
                                   "evidence": e.evidence, "evidence_file": efile}
        print(f"[gate] FAIL ({e.kind}): {e}", file=sys.stderr)
        for line in e.evidence:
            print(f"[gate]   evidence: {line}", file=sys.stderr)
        print(f"[gate]   full evidence (message, traceback, every failing test): {efile}", file=sys.stderr)
    except Exception as e:  # a bug in the gate: never let it pass for a task verdict
        tb = traceback.format_exc()
        report.update(failure=f"gate.py crashed: {type(e).__name__}: {e}", verdict="internal", failed_stage=stage)
        efile = write_evidence(build, args.slug, stage, "internal", f"gate.py crashed: {type(e).__name__}: {e}",
                               {"traceback": tb})
        report["stages"][stage] = {"ok": False, "kind": "internal", "error": tb, "evidence_file": efile}
        print(f"[gate] INTERNAL ERROR in stage {stage}:\n{tb}\n[gate]   full evidence: {efile}", file=sys.stderr)
    report["finished"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    if build.is_dir():
        # A partial run (--only) must never overwrite the full report that a trial relies on.
        out = "gate_report.partial.json" if args.only else "gate_report.json"
        tmp = build / (out + ".tmp")
        tmp.write_text(json.dumps(report, indent=1))
        tmp.replace(build / out)
    verdict = report["verdict"]
    print(f"[gate] {args.slug}: {'PASSED' if verdict == 'pass' else 'FAILED (' + verdict + ')'}"
          f"{' (' + args.only + ' only)' if args.only and verdict == 'pass' else ''}")
    return {"pass": 0, "task": 1, "infra": 2, "internal": 3}[verdict]


if __name__ == "__main__":
    sys.exit(main())
