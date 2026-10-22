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
           build/<slug>/FAIRNESS.md (pre-trial fairness review), and 3 oracle runs.
  nop      untouched vulnerable code: every security test FAILS, every
           functional test PASSES
  oracle   reference fix, run twice (3x under strict_gate): reward 1.0 and identical results
  patches  every patch listed in manifest["patch_checks"] behaves as declared:
             security_fail    at least one security test fails, functional all pass
             functional_fail  at least one functional test fails
             pass             reward 1.0 (an independent correct fix)

The result is written to build/<slug>/gate_report.json. Exit code 0 = passed.
Decisions here are made by scripts only; no model judgement is involved.
"""
import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
import time
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

ROOT = Path(__file__).resolve().parent.parent
JOBS = Path.home() / ".tb-graders" / "cwe" / "gate-jobs"
REQUIRED = [
    "instruction.md",
    "task.toml",
    "environment/Dockerfile",
    "solution/solve.sh",
    "solution/fix.patch",
    "tests/test.sh",
    "tests/score.py",
]
META_KEYS = ["cwe_id", "language", "repo", "source", "entry_point"]
MIN_SECURITY, MIN_FUNCTIONAL = 4, 5
MODEL_HOSTS = {"api.deepseek.com", "api.xiaomimimo.com"}
AGENT_KILL_MARK = "@anthropic-ai/claude-code"   # the kill block from templates/test.sh
MIN_DOCKER_FREE_GB = 15   # the Colima disk (79 GB) filled twice on 2026-10-16 and broke 6+ gate runs
# Wrong fixes the round-1 audits found passing (or correct fixes failing) only AFTER trials
# (research/round1-analysis/B-failure-modes.md, C-pipeline-lessons.md). A strict task names, for each
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
# Infrastructure errors worth one retry (Docker name lookups are flaky here).
RETRYABLE = ("NetworkConnectionError", "Could not resolve", "ENOTFOUND", "TLS handshake")


class GateFailure(Exception):
    pass


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
    raise GateFailure(f"Docker disk below {MIN_DOCKER_FREE_GB} GB free for 30 min (infrastructure, not the task)")


def run_harbor(task_dir: Path, agent: str, label: str) -> dict:
    """Run one Harbor trial and return {'reward', 'security', 'functional'}."""
    wait_for_disk()
    # Kept trial containers leave networks behind and Docker's ~31 address pools run out
    # ("all predefined address pools have been fully subnetted"); prune unused ones first.
    subprocess.run(["docker", "network", "prune", "-f"], capture_output=True)
    for attempt in (1, 2):
        name = f"{task_dir.name}-{label}-{int(time.time())}"
        cmd = ["harbor", "run", "-p", str(task_dir), "-a", agent, "-o", str(JOBS),
               "--job-name", name, "-y", "-q"]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        trials = [p for p in (JOBS / name).glob("*/") if (p / "result.json").exists()]
        if not trials:
            raise GateFailure(f"{label}: Harbor produced no trial ({proc.stdout[-400:]}{proc.stderr[-400:]})")
        trial = trials[0]
        result = json.loads((trial / "result.json").read_text())
        exc = result.get("exception_info")
        if exc:
            text = json.dumps(exc)
            if attempt == 1 and any(r in text for r in RETRYABLE):
                continue
            raise GateFailure(f"{label}: trial raised {exc.get('exception_type')}: "
                              f"{str(exc.get('exception_message'))[:300]}")
        detail = trial / "verifier" / "results.json"
        if not detail.exists():
            raise GateFailure(f"{label}: tests wrote no results.json (see {trial}/verifier)")
        data = json.loads(detail.read_text())
        data["trial_dir"] = str(trial)
        return data
    raise GateFailure(f"{label}: infrastructure error twice")


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
    test_files = [p for p in (task / "tests").rglob("*") if p.is_file() and p.name not in RUNNER_FILES]
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
        if not txt:
            continue
        if e.name != "Dockerfile":
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
# argo 403; analysis 2026-10-16, research/own-runs/FINDINGS.md). A line may keep an exact
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
    r"""from\s+['"](@ss/[^'"]+|/app/[^'"]+)['"]""",             # js/ts aliases into the product
    r"""require\(\s*['"](@ss/[^'"]+|/app/[^'"]+)['"]\s*\)""",
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
        problems.append("Dockerfile lacks the agent layer (harness/claude-code.Dockerfile.snippet)")
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
        if not (build / "checks" / str(c.get("patch"))).is_file():
            problems.append(f"patch check file missing: checks/{c.get('patch')}")
    kinds = {c.get("expect") for c in manifest.get("patch_checks", [])}
    for need in ("security_fail", "functional_fail"):
        if need not in kinds:
            problems.append(f"manifest.patch_checks has no '{need}' patch")
    exact = exact_status_asserts(task)
    if exact:
        problems.append("security tests assert one exact refusal status (assert the attack is blocked, "
                        f"e.g. any 4xx; or mark a reviewed line '{EXACT_STATUS_OK}'): " + " | ".join(exact))
    agent = toml.get("agent", {})
    if agent.get("network_mode") != "allowlist" or set(agent.get("allowed_hosts", [])) != MODEL_HOSTS:
        problems.append("task.toml [agent] must be offline: network_mode = \"allowlist\" with allowed_hosts "
                        "= only the model APIs (see templates/task.toml)")
    if AGENT_KILL_MARK not in (task / "tests/test.sh").read_text():
        problems.append("tests/test.sh lacks the kill-the-agent-before-grading block from templates/test.sh")
    warnings = variant_patch_warnings(manifest)
    if strict(manifest):
        problems.extend(warnings)
        problems.extend(catalogue_problems(build, manifest))
        if not (build / "FAIRNESS.md").is_file():
            problems.append("build/<slug>/FAIRNESS.md missing: the pre-trial fairness review (BUILDER.md 3h)")
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
        raise GateFailure("nop: " + "; ".join(problems))
    return {"ok": True, "security": len(sec), "functional": len(fun), "trial": r["trial_dir"]}


def check_oracle(task: Path, n: int = 2) -> dict:
    runs = [run_harbor(task, "oracle", f"oracle{i}") for i in range(1, n + 1)]
    for i, r in enumerate(runs, 1):
        bad = failing(r["security"]) + failing(r["functional"])
        if r["reward"] != 1.0 or bad:
            raise GateFailure(f"oracle run {i}: reward {r['reward']}, failing {bad}")
    if any(r["security"] != runs[0]["security"] or r["functional"] != runs[0]["functional"] for r in runs[1:]):
        raise GateFailure("oracle: the runs disagree (flaky tests)")
    return {"ok": True, "trials": [r["trial_dir"] for r in runs]}


def check_patches(task: Path, build: Path, manifest: dict) -> dict:
    out = {}
    for check in manifest.get("patch_checks", []):
        patch, expect = check["patch"], check["expect"]
        with tempfile.TemporaryDirectory(prefix="gate-") as tmp:
            variant = Path(tmp) / task.name
            shutil.copytree(task, variant)
            shutil.copy(build / "checks" / patch, variant / "solution" / "fix.patch")
            r = run_harbor(variant, "oracle", "chk-" + re.sub(r"\W+", "-", Path(patch).stem))
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
                              f"security failing {sec_bad}, functional failing {fun_bad}")
    return {"ok": True, "checks": out}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("slug")
    ap.add_argument("--only", choices=["static", "nop", "oracle", "patches"])
    ap.add_argument("--keep-jobs", action="store_true", help="kept for compatibility; jobs are always kept")
    args = ap.parse_args()

    task, build = ROOT / "tasks" / args.slug, ROOT / "build" / args.slug
    report = {"slug": args.slug, "started": time.strftime("%Y-%m-%dT%H:%M:%S"), "passed": False, "stages": {}}
    stages = ["static", "nop", "oracle", "patches"]
    if args.only:
        stages = [args.only]
    try:
        if not task.is_dir():
            raise GateFailure(f"no task directory {task}")
        mpath = build / "manifest.json"
        if not mpath.is_file():
            raise GateFailure(f"no manifest at {mpath}")
        manifest = json.loads(mpath.read_text())
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
    except GateFailure as e:
        report["failure"] = str(e)
        print(f"[gate] FAIL: {e}", file=sys.stderr)
    report["finished"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    if build.is_dir():
        # A partial run (--only) must never overwrite the full report that a trial relies on.
        out = "gate_report.partial.json" if args.only else "gate_report.json"
        (build / out).write_text(json.dumps(report, indent=1))
    ok = "failure" not in report
    print(f"[gate] {args.slug}: {'PASSED' if ok else 'FAILED'}"
          f"{' (' + args.only + ' only)' if args.only and ok else ''}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
