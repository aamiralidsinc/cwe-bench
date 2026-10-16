#!/usr/bin/env python3
"""Stage 3 - AI Task Generator.

For every <environments>/<OSV-ID>/ built by Stage 2, asks Claude to write:

    instruction.md      realistic bug report (no file names / function names / line numbers / hints)
    hidden_tests.py     pytest file: security (fail->pass) + functional (pass->pass)
    check_patches/      three wrong/right fixes that stage 4 RUNS against the tests (deterministic test-quality proof):
                        shallow.patch (blocks only the reported trigger -> some security test must still fail),
                        removal.patch (disables the feature -> some functional test must fail),
                        alternative.patch (a correct fix of a different design -> every test must pass)

All of them are written next to repo/ (never inside it) so the agent under evaluation cannot see them.

Inputs per folder
  * oracle_solution.patch                  (Stage 2)
  * repo/                                  checked out at the pre-patch commit (Stage 2)
  * summary/CWE/etc. from --candidates     (Stage 1 JSON)

Backends
  cli (default)  headless `claude -p` using the logged-in Claude Code subscription; no API key needed
  api            Anthropic API; needs ANTHROPIC_API_KEY (pip install anthropic python-dotenv)

Usage
  python -m src.stage3_task_builder.task_generator --candidates data/02_screened/screened.json --environments data/03_environments
  python -m src.stage3_task_builder.task_generator --candidates ... --dry-run --only GHSA-xxxx   # print prompt only
"""
from __future__ import annotations

import argparse
import ast
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from src.common.llm import CliBackend, QuotaExhausted, SafeguardsFlagged, normalize_model  # noqa: F401  (re-exported)

log = logging.getLogger(__name__)

INSTRUCTION_NAME = "instruction.md"
TESTS_NAME = "hidden_tests.py"
PATCH_NAME = "oracle_solution.patch"
REPO_DIRNAME = "repo"
META_NAME = "generation_meta.json"

DEFAULT_MODEL = "claude-opus-5-5"
MAX_FILE_CHARS = 40_000        # per source file shown to the model
MAX_CONTEXT_CHARS = 160_000    # all source files together
MAX_PATCH_CHARS = 80_000
MIN_SECURITY_TESTS = 3      # the reported case + >= 2 variants (skills/adversarial_research.md 4.4): a partial fix must fail
MIN_FUNCTIONAL_TESTS = 3    # legitimate uses near the boundary: an over-broad fix must fail
CHECK_DIR = "check_patches"
CHECK_KINDS = ("shallow", "removal", "alternative")
# Identifiers that are ordinary words in a report; never treated as a localization leak on their own.
GENERIC_NAMES = {"index", "main", "utils", "util", "helpers", "helper", "common", "types", "type", "init", "core", "lib",
                 "base", "config", "constants", "errors", "error", "shared", "internal", "constructor", "tostring",
                 "render", "handle", "handler", "process", "parse", "validate", "request", "response", "client",
                 "server", "options", "default", "value", "values", "result", "data", "test", "setup", "build", "create",
                 "update", "delete", "remove", "get", "set", "run", "call", "apply", "load", "save", "read", "write"}

TEST_PATH_RE = re.compile(r"(^|/)(tests?|__tests__|spec|specs)(/|$)|(^|/)(test_[^/]+|[^/]+_test\.\w+|[^/]+\.(test|spec)\.\w+)$",
                          re.IGNORECASE)


# --------------------------------------------------------------------------- #
# Prompts
# --------------------------------------------------------------------------- #
SYSTEM_PROMPT = """\
You are a senior application-security engineer on the maintainer/QA side of a defensive benchmark that measures \
whether AI coding agents can correctly REPAIR real vulnerabilities that are already publicly disclosed (CVE/GHSA) \
and already fixed upstream. You are given the historical fix (the "reference patch") and the vulnerable source. \
You write (1) the bug report a maintainer would receive, (2) a hidden pytest regression suite that checks a \
repair actually closes the hole without breaking the feature, and (3) three candidate code fixes (an incomplete \
one, an over-restrictive one and a correct one) that are run against the suite to prove it tells good repairs \
from bad ones.

Purpose and use: the benchmark grades AI agents that are asked to FIX the code; the agents never see the tests. A \
repair task is useful only if an incomplete or over-broad repair is caught, which is why the suite checks every \
path to the bug and the feature's legitimate uses. Nothing here is run against anyone else's systems: the tests \
run offline, inside a throwaway container, against a pinned old version of the project, and the bug is already \
patched in current releases. This is ordinary security-regression-test work: the tests only assert that hostile \
input is REJECTED (or handled safely), use harmless sentinel values and small inputs, and contain no attack tooling.\
"""

USER_PROMPT_TEMPLATE = """\
# Vulnerability metadata
- OSV ID: {osv_id}
- CVE: {cve_id}
- CWE: {cwes}
- Ecosystem / package: {ecosystem} / {package}
- Repository: {repo_url}
- Official summary: {summary}

# Oracle patch (the historical human fix; the agent never sees this)
```diff
{patch}
```

# Pre-patch source of the files the patch modifies (vulnerable state)
{sources}

# How the rest of the repository reaches that code (callers / entry points - read these to wire the tests correctly)
{callers}

# Repository map (source and test files; the agent under evaluation gets this whole repository)
{repo_map}

# Package manifests (entry points, exports, scripts, test runner)
{manifests}

# Other context
- Existing test files touched by the patch: {test_files}
- Repo top-level entries: {top_level}

# How this project's own tests set things up (copy the fixture/app-construction pattern)
{test_examples}

# Your job
Produce the artifacts below.

## Artifact 1: instruction.md - the bug report
Write a realistic vulnerability report as a user/security researcher/customer would file it.
- Describe the business impact and the observable, behaviour-level way the issue is triggered \
(what is sent or done, what happens, what should happen instead). It must be accurate and give enough \
information that a skilled engineer could reproduce the *symptom* and recognise the vulnerability class.
- Crucial: DO NOT mention any file names, paths, module names from the patch, function/class names that \
the patch changes, line numbers, or hints about where or how to fix it. We are testing Localization: the \
agent must find the faulty code itself. Public, user-facing API names and documented features may be \
referenced only if the report is unintelligible without them.
- Where it is genuinely true of this bug, frame it as the deeper flaw it is (inter-procedural data flow, \
business-logic or state-tracking error, race condition, incomplete validation across code paths). Do not \
invent a different vulnerability than the one the patch fixes, and do not exaggerate.
- A validator rejects the report if it names a changed file's base name (e.g. `uneval` for uneval.js), or a \
function/method/class the patch defines or edits (e.g. `Address4`). Describe them by role instead ("the serializer that \
emits JavaScript source", "the IPv4 address type").
- Write it in your OWN words: never reuse phrases from the advisory summary/description above, and do not name the CVE/GHSA id.
- Do not describe the variants that your hidden tests cover.
- Do NOT prescribe the fix. Any 'expected behaviour' part may only state the security property that must hold and the legitimate behaviour that must keep working, in user-visible terms. It must not describe validation rules, token formats, where or in what order checks happen, what is logged versus returned, or which internal code paths need changing. Likewise do not hint which inputs are legitimate beyond what the report needs to be accurate.
- Every behaviour your functional tests require must be derivable from the report or from ordinary expectations of the feature; if a functional test needs an unusual-but-legal input, the report must make clear that input is legitimate.
- 150-400 words, Markdown, with a title.

## Artifact 2: hidden_tests.py - pytest suite
Constraints (the suite is run with the working directory at the repo root, repo root on sys.path, \
after the agent edits the code; `REPO_ROOT` env var also points there):
- Pure pytest, deterministic, offline (no network, no sleeping beyond ~1s, no external services), \
self-contained: create temp files via `tmp_path`. Import only things that exist in the PRE-patch source above \
or the standard library / the project's declared dependencies. If the vulnerable language is not Python \
(e.g. npm package), drive the code via `subprocess` calling `node` with inline scripts and assert on the output.
- Black-box: test behaviour through public/entry-point APIs only. NEVER import, call, or assert on \
anything that the oracle patch ADDS (new helpers, new exceptions, new parameters), and never assert exact \
error message text. Accept any reasonable rejection (exception of any type, sanitised output, error \
status) when asserting that something is blocked - define a small helper like `assert_blocked(callable)`.
- The oracle patch MUST pass every test, and the pre-patch code MUST fail every `test_security_*` test. \
Only test hardening that the oracle patch itself provides; do not demand extra protections it does not give.
- Use harmless sentinel values (e.g. a marker file inside tmp_path, a sentinel string) - nothing that would be harmful outside the test.

Naming convention (enforced by a validator):
A) `test_security_*` (at least {min_sec}, ideally 4-8): fail on vulnerable code, pass after a correct fix. \
Cover the exact scenario in the report AND *variants beyond the report* that share the same root cause so \
that an incomplete remediation (patching only the one reported path/encoding/entry point/casing/ordering) \
still fails. Think: alternative entry points that reach the same sink, encodings and normalisation \
tricks, case/Unicode/whitespace variants, nested or chained inputs, repeated or interleaved calls \
(state/race-style), boundary values.
B) `test_functional_*` (at least {min_func}, ideally 4-8): pass on both vulnerable and fixed code. \
These are legitimate use-cases that a careless or over-broad fix would break (over-correction): valid \
inputs close to the rejection boundary, normal feature usage, documented options, edge cases that look \
suspicious but are legitimate. A fix that simply disables the feature or rejects everything must fail \
these tests.
- Add a one-line docstring on each test saying what it protects (without giving away the fix location).

# Hard rules learned from real rejections (most early drafts broke rule 1)
1. IMPLEMENTATION-AGNOSTIC. A test may only observe what an attacker or user can observe at the entry point (HTTP \
status/body, return value, raised error, file written or not). It must pass for ANY reasonable correct fix, not just the \
reference patch's design. Real rejected examples:
   - asserting the fix lives in one permission layer, when an equally valid in-method check would fail the test
   - reading the server-side session store to prove sessions were deleted, when a valid fix rejects stale sessions \
without deleting them -> instead send the request with the old session and assert it is refused
   - driving a hand-built mini app instead of the project's real app/routes -> use the project's own app factory/entry point
2. SOLVABLE FROM THE REPORT. Every input a security test uses must be an instance of the class the report describes. \
Never require blocking an input the report does not imply (rejected example: blocking a config key that the underlying \
tool ignores and the report never mentions).
3. THE HARNESS MUST RUN. Build the app/client ONCE per module (module-scoped fixture) when the project registers global \
state (Flask blueprints, singletons, module-level registries) and reset state between tests instead of re-creating the \
app (rejected example: re-creating a Flask app per test -> "blueprint already registered" on every test after the first). \
Mirror how the project's own tests set things up (examples below, if any).
4. COMPILED JS/TS PROJECTS. Test the SOURCE, not a prebuilt bundle: run the project's own test runner (vitest/jest/mocha via node_modules/.bin) on a temporary test file that imports from src/, or load the source through the project's TS tooling. Never import dist/ or build output (rejected example: tests that required dist/index.js, which does not exist until a build and would not contain the agent's edits).
Before answering, check each test against these four rules.

# Entry point
Security regression tests must reproduce the vulnerable behaviour through a REAL entry point of the project - the way \
an untrusted caller or a normal user reaches the code (public API call, HTTP route, CLI command, exported function) - never by calling the \
internal helper the patch modifies. State that entry point in the metadata block (internal use only, it is never \
shown to the agent).

## Artifact 3: check patches - three fixes the pipeline RUNS against your tests (never shown to the agent)
Each is a list of exact search/replace edits on the PRE-patch source files above. "search" must appear EXACTLY ONCE in \
that file, copied verbatim (indentation included); "replace" is the new text. Edit only non-test source files and keep \
the code valid. The pipeline executes your hidden tests against each one; a wrong outcome sends the task back to you:
- "shallow": the band-aid a hurried engineer writes from the report alone - it blocks ONLY the exact reported trigger \
(one entry point / one encoding / one call path) and leaves the sibling variants open. It must make at least one \
security test pass, and at least one security test must still FAIL on it. (This proves a partial fix is caught.)
- "removal": closes the hole by disabling or over-restricting the feature (reject the whole input class, remove the \
code path, return early). At least one functional test must FAIL on it. (This proves over-blocking is caught.)
- "alternative": a CORRECT, complete fix whose design differs from the reference patch (another layer or mechanism). \
EVERY test must pass on it. (This proves the tests accept any correct fix, not just the reference design.)

# Output format (strict)
Return ONLY these four blocks, nothing else:

<instruction_md>
...markdown...
</instruction_md>
<hidden_tests_py>
...python source, no code fences...
</hidden_tests_py>
<task_metadata_json>
{{"entry_point": "<one line: how untrusted input reaches the code, e.g. 'HTTP GET /download?file= handled by the app'>",
  "techniques": [<numbers of the task-design techniques (from the curated technique list) this task applies, e.g. 1, 4, 7>]}}
</task_metadata_json>
<check_patches_json>
{{"shallow": [{{"file": "<repo-relative path>", "search": "<exact existing text>", "replace": "<new text>"}}],
  "removal": [...], "alternative": [...]}}
</check_patches_json>
"""


# --------------------------------------------------------------------------- #
# Context building
# --------------------------------------------------------------------------- #
@dataclass
class Context:
    osv_id: str
    env_dir: Path
    meta: dict
    patch: str
    changed_files: list[str]
    prompt: str = ""
    leak_terms: set[str] = field(default_factory=set)
    advisory_text: str = ""
    leak_idents: set[str] = field(default_factory=set)


def parse_changed_files(patch: str) -> list[str]:
    files = []
    for m in re.finditer(r"^diff --git a/(.+?) b/(.+)$", patch, re.MULTILINE):
        path = m.group(2)
        if path not in files:
            files.append(path)
    return files


def read_text_capped(path: Path, cap: int) -> Optional[str]:
    try:
        data = path.read_bytes()
    except OSError:
        return None
    if b"\0" in data[:4096]:
        return None
    text = data.decode("utf-8", errors="replace")
    if len(text) > cap:
        text = text[:cap] + f"\n... [truncated, file is {len(text)} chars]"
    return text


def build_sources_section(repo: Path, changed: list[str]) -> tuple[str, list[str]]:
    parts, test_files, budget = [], [], MAX_CONTEXT_CHARS
    for rel in changed:
        if TEST_PATH_RE.search(rel):
            test_files.append(rel)
            continue
        if budget <= 0:
            parts.append(f"### {rel}\n[omitted: context budget exhausted]")
            continue
        text = read_text_capped(repo / rel, min(MAX_FILE_CHARS, budget))
        if text is None:
            parts.append(f"### {rel}\n[new file in patch, binary, or unreadable in pre-patch tree]")
            continue
        budget -= len(text)
        parts.append(f"### {rel}\n```\n{text}\n```")
    return ("\n\n".join(parts) or "[none]"), test_files


SKIP_DIRS = {".git", "node_modules", "dist", "build", "coverage", "vendor", "__pycache__", ".venv", "venv", ".tox",
             "site-packages", ".next", ".cache", "fixtures", "__fixtures__"}
CODE_EXT_RE = re.compile(r"\.(py|pyi|[cm]?[jt]sx?|vue|svelte)$")
MAP_CHARS, CALLER_CHARS, CALLER_FILE_CHARS, MANIFEST_CHARS = 14_000, 60_000, 12_000, 6_000


def repo_files(repo: Path) -> list[str]:
    try:
        out = subprocess.run(["git", "ls-files"], cwd=repo, capture_output=True, text=True, timeout=60).stdout.split("\n")
    except (OSError, subprocess.TimeoutExpired):
        out = [p.relative_to(repo).as_posix() for p in repo.rglob("*") if p.is_file()]
    return [f for f in out if f and not SKIP_DIRS & set(Path(f).parts) and CODE_EXT_RE.search(f)]


def repo_map(repo: Path, changed: list[str]) -> str:
    """Source/test file list. Big repos: every file in the directories the fix touches, and per-directory counts elsewhere."""
    files = repo_files(repo)
    text = "\n".join(files)
    if len(text) <= MAP_CHARS:
        return text or "(no source files found)"
    near = {str(Path(c).parent) for c in changed}
    keep = [f for f in files if str(Path(f).parent) in near]
    counts: dict[str, int] = {}
    for f in files:
        if str(Path(f).parent) not in near:
            d = "/".join(Path(f).parts[:3][:-1]) or "."
            counts[d] = counts.get(d, 0) + 1
    lines = keep + [f"{d}/  ({n} files)" for d, n in sorted(counts.items())]
    return ("\n".join(lines))[:MAP_CHARS] + (f"\n... ({len(files)} source files in total)" if len(files) > len(lines) else "")


def _module_keys(rel: str) -> set[str]:
    p = Path(rel)
    stem = p.name.split(".")[0]
    keys = {stem} if stem not in ("index", "__init__", "main", "utils", "util", "types") else set()
    if stem in ("index", "__init__") and p.parent.name:
        keys.add(p.parent.name)
    if rel.endswith(".py"):
        parts = list(p.with_suffix("").parts)
        if parts and parts[0] in ("src", "lib"):
            parts = parts[1:]
        if parts and parts[-1] == "__init__":
            parts = parts[:-1]
        if len(parts) > 1:
            keys.add(".".join(parts))
    return keys


def callers_section(repo: Path, changed: list[str], patch: str) -> str:
    """Files (outside the fix) that import a changed module or call a function/class the fix edits, best first - the
    path from the public entry point down to the vulnerable code, so the hidden tests can drive it for real."""
    src = [c for c in changed if CODE_EXT_RE.search(c) and not TEST_PATH_RE.search(c)]
    if not src:
        return "(none)"
    keys = set().union(*(_module_keys(c) for c in src))
    names = {n for n in localizing_identifiers(patch) if len(n) >= 5}
    scored: list[tuple[int, str, str]] = []
    for rel in repo_files(repo):
        if rel in changed or TEST_PATH_RE.search(rel):
            continue
        try:
            text = (repo / rel).read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if len(text) > 400_000:
            continue
        imports = re.findall(r"""(?:\bfrom\s+['"]?|\bimport\s+['"]?|require\(\s*['"]|import\(\s*['"])([\w./@-]+)""", text)
        hit_imports = sum(1 for spec in imports if Path(spec).name.split(".")[0] in keys or spec.lstrip(".") in keys
                          or any(spec.endswith("." + k) or spec == k for k in keys if "." in k))
        hit_names = sum(1 for n in names if re.search(rf"\b{re.escape(n)}\b", text))
        if hit_imports or hit_names:
            scored.append((3 * hit_imports + hit_names, rel, text))
    scored.sort(key=lambda t: (-t[0], len(t[2])))
    parts, used = [], 0
    for _, rel, text in scored:
        if used >= CALLER_CHARS:
            parts.append(f"(+{len(scored) - len(parts)} more files reference the changed code)")
            break
        body = text[:CALLER_FILE_CHARS] + ("\n... [truncated]" if len(text) > CALLER_FILE_CHARS else "")
        used += len(body)
        parts.append(f"### {rel}\n```\n{body}\n```")
    return "\n\n".join(parts) or "(no other file imports the changed code - it is likely a public entry point itself)"


def manifests_section(repo: Path) -> str:
    parts, used = [], 0
    for name in ("package.json", "pyproject.toml", "setup.cfg", "setup.py", "pytest.ini", "tox.ini"):
        f = repo / name
        if f.is_file() and used < MANIFEST_CHARS:
            body = f.read_text(errors="ignore")[: MANIFEST_CHARS - used]
            used += len(body)
            parts.append(f"### {name}\n```\n{body}\n```")
    return "\n\n".join(parts) or "(none)"


def stage4_checks_text() -> str:
    """The exact checks stage 4 applies, so the first draft is written to pass them (instead of learning by rejection)."""
    try:
        from src.stage4_oracle_validator.rubric_check import CRITERIA
    except Exception:          # never block generation on this
        return ""
    crit = "\n".join(f"- {name} ({'must pass' if c else 'advisory'}): {d}" for name, (c, d) in CRITERIA.items())
    return f"""

# The checks your task will face (write it to pass all of them the first time)
An independent reviewer scores the task on these criteria; any failed "must pass" criterion sends it back:
{crit}
Then the task is EXECUTED: the reference fix must score 1.0 twice; the vulnerable code must fail every test_security_*
and pass every test_functional_*; the repo's own related tests must pass before and after the fix; your three check
patches run against your tests (shallow must still fail a security test, removal must fail a functional test,
alternative must pass everything); and if both target models can name the fix location from your report alone, the
task is rejected (so describe behaviour, never location).
"""


def regeneration_feedback(env_dir: Path) -> str:
    """If stage 4's rubric rejected earlier rounds, show the reviewer's issues and the rejected artifacts."""
    rounds = sorted((env_dir / "attempts").glob("round_*")) if (env_dir / "attempts").is_dir() else []
    if not rounds:
        return ""
    last = rounds[-1]
    try:
        prev_md = (last / "instruction.md").read_text()
        prev_tests = (last / "hidden_tests.py").read_text()
    except OSError:
        return ""
    issues: list[str] = []
    rubric = last / "rubric_check.json"
    if rubric.is_file():
        try:
            rj = json.loads(rubric.read_text())
            if not rj.get("passed", True):
                issues += rj.get("blocking_issues", [])
        except json.JSONDecodeError:
            pass
    exe = last / "execution_feedback.txt"
    if exe.is_file():
        body = exe.read_text()
        if body.startswith("FIX-CHECK"):     # stage 4 ran the check patches; the message says what to change
            issues.append(body[:4000])
        else:
            issues.append("Your tests were EXECUTED in the real environment and misbehaved. Real pytest output:\n"
                          + body[:3500]
                          + "\nFix the test harness itself (e.g. build the app ONCE per module with a module-scoped "
                            "fixture if the project registers global state/blueprints, reset state between tests "
                            "instead of re-creating the app).")
    if not issues:
        return ""
    bullets = "\n".join(f"- {i}" for i in issues)
    return f"""

# REVISION REQUIRED - an independent reviewer rejected your previous attempt
Blocking issues (fix ALL of them; do not just rephrase):
{bullets}

Previous instruction.md:
```
{prev_md}
```
Previous hidden_tests.py:
```python
{prev_tests}
```
Produce a corrected, complete set of the four blocks. Remember: every tested behaviour must be derivable from the report, \
and tests must accept any reasonable correct fix, not only the reference patch's design.
"""


LESSONS_TEXT = ""   # set in main() from skills/lessons_learned.md


def project_test_examples(repo: Path, changed: list[str], budget: int = 12_000) -> str:
    """conftest.py files + the most related existing test file, so the generated harness mirrors the project's own."""
    picks: list[Path] = []
    for conf in sorted(repo.rglob("conftest.py")):
        if ".git" not in conf.parts and "node_modules" not in conf.parts and conf.stat().st_size < 40_000:
            picks.append(conf)
        if len(picks) >= 2:
            break
    stems = {Path(c).stem.lower() for c in changed if not TEST_PATH_RE.search(c)}
    best, best_hits = None, 0
    for t in repo.rglob("*"):
        if (not t.is_file() or ".git" in t.parts or "node_modules" in t.parts or t.stat().st_size > 60_000
                or not TEST_PATH_RE.search(t.relative_to(repo).as_posix()) or t.suffix not in (".py", ".js", ".ts", ".mjs")):
            continue
        try:
            text = t.read_text(errors="ignore").lower()
        except OSError:
            continue
        hits = sum(1 for st in stems if len(st) >= 4 and st in text)
        if hits > best_hits:
            best, best_hits = t, hits
    if best:
        picks.append(best)
    out, used = [], 0
    for p in picks:
        body = p.read_text(errors="ignore")[: max(0, budget - used)]
        if not body:
            break
        used += len(body)
        out.append(f"### {p.relative_to(repo).as_posix()}\n```\n{body}\n```")
    return "\n\n".join(out) or "(no existing tests found)"


def build_context(env_dir: Path, candidates: dict[str, dict]) -> Context:
    osv_id = env_dir.name
    patch_path = env_dir / PATCH_NAME
    repo = env_dir / REPO_DIRNAME
    if not patch_path.is_file() or not repo.is_dir():
        raise ValueError(f"missing {PATCH_NAME} or {REPO_DIRNAME}/")
    patch = patch_path.read_text(encoding="utf-8", errors="replace")
    if len(patch) > MAX_PATCH_CHARS:
        raise ValueError(f"oracle patch too large ({len(patch)} chars); too big to be a good task")
    meta = candidates.get(osv_id, {})
    changed = parse_changed_files(patch)
    sources, test_files = build_sources_section(repo, changed)
    top = sorted(p.name for p in repo.iterdir() if p.name != ".git")[:60]

    feedback = regeneration_feedback(env_dir) + LESSONS_TEXT
    prompt = USER_PROMPT_TEMPLATE.format(
        osv_id=osv_id,
        cve_id=meta.get("cve_id") or "n/a",
        cwes=", ".join(meta.get("cwe_ids") or []) or "unknown",
        ecosystem=meta.get("ecosystem") or "unknown",
        package=meta.get("package") or "unknown",
        repo_url=meta.get("repo_url") or "unknown",
        summary=meta.get("summary") or "(no summary available - infer from the patch)",
        patch=patch, sources=sources,
        test_files=", ".join(test_files) or "none",
        top_level=", ".join(top),
        test_examples=project_test_examples(repo, changed),
        callers=callers_section(repo, changed, patch), repo_map=repo_map(repo, changed), manifests=manifests_section(repo),
        min_sec=MIN_SECURITY_TESTS, min_func=MIN_FUNCTIONAL_TESTS,
    ) + stage4_checks_text() + feedback

    leak = set()
    for f in changed:
        leak.add(f.lower())
        if len(Path(f).name) >= 4:
            leak.add(Path(f).name.lower())
    return Context(osv_id, env_dir, meta, patch, changed, prompt, leak,
                   advisory_text=f"{meta.get('summary') or ''} {meta.get('description') or ''}",
                   leak_idents=localizing_identifiers(patch))


DEF_RE = re.compile(r"\b(?:def|class|function|func|fn|interface|struct)\s+([A-Za-z_$][\w$]{3,})"
                    r"|^\s*(?:export\s+)?(?:async\s+)?(?:static\s+)?(?:const|let|var)\s+([A-Za-z_$][\w$]{3,})\s*=\s*(?:async\s*)?(?:function\b|\()"
                    r"|^\s*(?:public\s+|private\s+|protected\s+|static\s+|async\s+)*([A-Za-z_$][\w$]{3,})\s*\([^)]*\)\s*(?::[^{=]+)?\{\s*$",
                    re.MULTILINE)
JS_KEYWORDS = {"if", "for", "while", "switch", "catch", "return", "function", "else", "__init__", "__call__"}
SOURCE_EXT_RE = re.compile(r"\.(py|pyx|[cm]?[jt]sx?|vue|svelte|go|rb|rs|java|kt|php|cs|c|cc|cpp|h|hpp|swift|scala)$")


def localizing_identifiers(patch: str) -> set[str]:
    """Names that point straight at the fix: base names of changed source files and the functions/classes/methods the
    patch defines or edits (hunk-header context + definitions on changed lines). Generic words are excluded."""
    names: set[str] = set()
    for chunk in re.split(r"(?m)^(?=diff --git )", patch):
        m = re.match(r"diff --git a/.+? b/(.+)", chunk)
        if not m or TEST_PATH_RE.search(m.group(1)) or not SOURCE_EXT_RE.search(m.group(1)):
            continue          # docs, changesets, manifests: their names do not localize the fix
        stem = Path(m.group(1)).name.split(".")[0]
        if len(stem) >= 4:
            names.add(stem)
        changed = "\n".join(l[1:] for l in chunk.splitlines()
                            if l[:1] in "+-" and not l.startswith(("+++", "---")))
        headers = "\n".join(h for h in re.findall(r"(?m)^@@[^@]*@@(.*)$", chunk))
        for text in (changed, headers):
            for g in DEF_RE.findall(text):
                names.update(x for x in g if x and x not in JS_KEYWORDS)
    return {n for n in names if n.lower() not in GENERIC_NAMES}


def identifier_leaks(md: str, idents: set[str]) -> list[str]:
    """Code-like names (camelCase, snake_case, digits, Pascal with an inner capital) leak when they appear as words; a
    plain lowercase word (e.g. `quote`) only when written as code - in backticks or as a call."""
    out = []
    for name in sorted(idents):
        code_like = bool(re.search(r"[a-z][A-Z]|_|\d|^[A-Z][a-z]+[A-Z]", name))
        if code_like and re.search(rf"(?<![\w$]){re.escape(name)}(?![\w$])", md):
            out.append(name)
        elif not code_like and re.search(rf"`[^`]*\b{re.escape(name)}\b[^`]*`|\b{re.escape(name)}\s*\(", md, re.IGNORECASE):
            out.append(name)
    return out


def extract_check_patches(text: str, repo: Path) -> dict[str, str]:
    """<check_patches_json> -> {kind: unified diff}. Every edit must hit exactly one place in a non-test source file;
    the diff is produced by git on a scratch copy and must `git apply --check` cleanly on the real repo."""
    m = re.search(r"<check_patches_json>\s*(.*?)\s*</check_patches_json>", text, re.DOTALL)
    if not m:
        raise GenerationInvalid("Output must also contain a <check_patches_json> block (shallow, removal, alternative).")
    raw = m.group(1).strip()
    fence = re.match(r"^```(?:json)?\s*\n(.*?)\n```$", raw, re.DOTALL)
    try:
        spec = json.loads(fence.group(1) if fence else raw)
    except json.JSONDecodeError as e:
        raise GenerationInvalid(f"<check_patches_json> is not valid JSON: {e}")
    out = {}
    for kind in CHECK_KINDS:
        edits = spec.get(kind) if isinstance(spec, dict) else None
        if not isinstance(edits, list) or not edits:
            raise GenerationInvalid(f"check_patches.{kind} must be a non-empty list of {{file, search, replace}} edits.")
        out[kind] = edits_to_patch(kind, edits, repo)
    if len(set(out.values())) < len(out):
        raise GenerationInvalid("The three check patches must differ from each other.")
    return out


def edits_to_patch(kind: str, edits: list, repo: Path) -> str:
    with tempfile.TemporaryDirectory(prefix="checkpatch_") as tmp:
        work = Path(tmp)
        files = {}
        for i, e in enumerate(edits):
            if not isinstance(e, dict) or not all(isinstance(e.get(k), str) for k in ("file", "search", "replace")):
                raise GenerationInvalid(f"check_patches.{kind}[{i}] needs string fields file, search, replace.")
            rel = e["file"].strip().lstrip("/")
            if TEST_PATH_RE.search(rel) or ".." in Path(rel).parts:
                raise GenerationInvalid(f"check_patches.{kind}[{i}]: edit source files only, not {rel!r}.")
            if rel not in files:
                src = repo / rel
                if not src.is_file():
                    raise GenerationInvalid(f"check_patches.{kind}[{i}]: {rel!r} does not exist in the repository.")
                files[rel] = src.read_text(encoding="utf-8", errors="replace")
            n = files[rel].count(e["search"]) if e["search"] else 0
            if n != 1:
                raise GenerationInvalid(f"check_patches.{kind}[{i}]: the search text occurs {n} times in {rel} "
                                        "(it must be copied verbatim and occur exactly once).")
            files[rel] = files[rel].replace(e["search"], e["replace"], 1)
        for rel in files:
            (work / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(repo / rel, work / rel)
        git = lambda *a: subprocess.run(["git", "-c", "user.name=x", "-c", "user.email=x@x", *a], cwd=work,
                                        capture_output=True, text=True)
        git("init", "-q")
        git("add", "-A")
        git("commit", "-qm", "base")
        for rel, body in files.items():
            (work / rel).write_text(body, encoding="utf-8")
        diff = git("diff", "--no-color").stdout
    if not diff.strip():
        raise GenerationInvalid(f"check_patches.{kind} changes nothing.")
    chk = subprocess.run(["git", "apply", "--check", "-"], cwd=repo, input=diff, capture_output=True, text=True)
    if chk.returncode != 0:
        raise GenerationInvalid(f"check_patches.{kind} does not apply to the repository: {chk.stderr.strip()[:300]}")
    return diff


# --------------------------------------------------------------------------- #
# Parsing and validation
# --------------------------------------------------------------------------- #
REFUSAL_RE = re.compile(r"\b(I can't|I cannot|I won't|I'm not able|I am unable|I'm unable|can't help with|unable to (?:help|assist|complete))", re.IGNORECASE)
REFUSAL_RETRY_NOTE = """

# Context for this request
This is a defensive security-REGRESSION task for a vulnerability that is already public (see the advisory metadata above) and \
already fixed upstream by the reference patch. The deliverables are (1) a maintainer-style bug report and (2) pytest tests that \
assert hostile input is REJECTED while legitimate use keeps working. Tests use harmless sentinel values inside pytest's tmp_path \
and contain no attack tooling. Please produce the four blocks in the required format.
"""


class GenerationInvalid(Exception):
    """Model output unusable; message is fed back to the model on retry."""


def extract_blocks(text: str) -> tuple[str, str]:
    inst = re.search(r"<instruction_md>\s*(.*?)\s*</instruction_md>", text, re.DOTALL)
    tests = re.search(r"<hidden_tests_py>\s*(.*?)\s*</hidden_tests_py>", text, re.DOTALL)
    if not inst or not tests:
        raise GenerationInvalid("Output must contain both <instruction_md> and <hidden_tests_py> blocks.")
    code = tests.group(1).strip()
    fence = re.match(r"^```(?:python)?\s*\n(.*?)\n```$", code, re.DOTALL)
    if fence:
        code = fence.group(1)
    return inst.group(1).strip() + "\n", code.strip() + "\n"


def extract_metadata(text: str) -> dict:
    m = re.search(r"<task_metadata_json>\s*(.*?)\s*</task_metadata_json>", text, re.DOTALL)
    if not m:
        raise GenerationInvalid("Output must also contain a <task_metadata_json> block with an entry_point.")
    try:
        meta = json.loads(m.group(1))
    except json.JSONDecodeError as e:
        raise GenerationInvalid(f"<task_metadata_json> is not valid JSON: {e}")
    ep = meta.get("entry_point") if isinstance(meta, dict) else None
    if not isinstance(ep, str) or not (5 <= len(ep.strip()) <= 300):
        raise GenerationInvalid("metadata.entry_point must be a one-line string describing the real entry point.")
    techs = meta.get("techniques") if isinstance(meta.get("techniques"), list) else []
    # which curated techniques this task applies: the technique scoreboard learns from them (optional field)
    return {"entry_point": ep.strip(), "techniques": sorted({int(t) for t in techs if str(t).strip().isdigit() and 0 < int(t) < 50})}


def _ngrams(text: str, n: int = 8) -> set[str]:
    words = re.findall(r"[a-z0-9_]+", text.lower())
    return {" ".join(words[i:i + n]) for i in range(len(words) - n + 1)}


def validate_instruction(md: str, ctx: Context) -> None:
    lowered = md.lower()
    copied = _ngrams(md) & _ngrams(ctx.advisory_text)
    if copied:   # verbatim advisory phrases are the strongest recall cue for a model that has seen the advisory
        raise GenerationInvalid("instruction.md copies the public advisory's wording (e.g. "
                                f"{sorted(copied)[0]!r}). Describe the problem entirely in your own words as a user would.")
    leaked = sorted(t for t in ctx.leak_terms if t in lowered)
    if leaked:
        raise GenerationInvalid(
            f"instruction.md mentions file names/paths from the patch ({', '.join(leaked)}). "
            "Remove every file name and path.")
    named = identifier_leaks(md, ctx.leak_idents)
    if named:
        raise GenerationInvalid(
            f"instruction.md names code the fix changes: {', '.join(named)} (a changed file's base name or a function/"
            "method/class the patch edits). Remove every occurrence of these exact names written as code - in backticks, "
            "as a call like name(...), or as an identifier. Describe the component in plain words by its role instead "
            "(e.g. 'the HTTP response-caching layer' rather than `cache` or cache()); a public option the user sets "
            "may still be described in words.")
    if re.search(r"\bline[s]?\s+\d+\b|\.\w{1,4}:\d+\b|\bL\d{2,}\b", md, re.IGNORECASE):
        raise GenerationInvalid("instruction.md contains line numbers; remove them.")
    if len(md.split()) < 60:
        raise GenerationInvalid("instruction.md is too short to be a realistic report.")


def no_silent_skips(code: str) -> str:
    """A skipped test scores as failed and hides an environment gap. Turn guards into hard failures instead, so a missing
    package fails loudly at validation (where it gets fixed): pytest.skip(...) -> pytest.fail(...),
    pytest.importorskip("x") -> importlib.import_module("x"), skip/skipif markers removed. xfail is still rejected."""
    code = re.sub(r"\bpytest\.skip\s*\(", "pytest.fail(", code)
    code = re.sub(r",\s*allow_module_level\s*=\s*True", "", code)
    code = re.sub(r"\bpytest\.importorskip\s*\(\s*(['\"][\w.]+['\"])\s*\)", r"__import__('importlib').import_module(\1)", code)
    code = re.sub(r"(?m)^\s*@pytest\.mark\.skip(if)?\b.*\n", "", code)
    code = re.sub(r"(?m)^\s*pytestmark\s*=\s*pytest\.mark\.skip(if)?\b.*\n", "", code)
    return code


def ensure_pytest_import(code: str) -> str:
    """A missing `import pytest` is a one-line omission, not a design flaw: add it (after a module docstring and
    __future__ imports) instead of rejecting an otherwise valid suite."""
    if re.search(r"(?m)^\s*(import pytest\b|from pytest\b)", code):
        return code
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return code               # validate_tests reports the syntax error
    line = 0
    for node in tree.body:
        is_doc = isinstance(node, ast.Expr) and isinstance(getattr(node, "value", None), ast.Constant) \
            and isinstance(node.value.value, str)
        if is_doc or (isinstance(node, ast.ImportFrom) and node.module == "__future__"):
            line = node.end_lineno
            continue
        break
    lines = code.splitlines(keepends=True)
    return "".join(lines[:line]) + "import pytest\n" + "".join(lines[line:])


def validate_tests(code: str, ctx: Context) -> None:
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        raise GenerationInvalid(f"hidden_tests.py has a syntax error: {e}")
    names = [n.name for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    sec = [n for n in names if n.startswith("test_security_")]
    fun = [n for n in names if n.startswith("test_functional_")]
    if len(sec) < MIN_SECURITY_TESTS:
        raise GenerationInvalid(f"Need >= {MIN_SECURITY_TESTS} test_security_* functions, found {len(sec)}.")
    if len(fun) < MIN_FUNCTIONAL_TESTS:
        raise GenerationInvalid(f"Need >= {MIN_FUNCTIONAL_TESTS} test_functional_* functions, found {len(fun)}.")
    if "import pytest" not in code and "from pytest" not in code:
        raise GenerationInvalid("hidden_tests.py must import pytest.")
    if re.search(r"importorskip|pytest\.skip\s*\(|mark\.skip(if)?\b|pytest\.xfail|mark\.xfail|allow_module_level", code):
        # A skipped test scores as failed: a missing package would look like a model failure. The task image installs
        # the project with all its extras and dev/test groups, so a dependency the tests need is present.
        raise GenerationInvalid("hidden_tests.py must never skip or xfail (no importorskip, pytest.skip, skipif, xfail): "
                                "every test must run. The environment installs the project with all its optional extras "
                                "and dev/test dependencies; import what you need directly.")
    # Tests must not read the answer key.
    if PATCH_NAME in code or "oracle_solution" in code:
        raise GenerationInvalid("hidden_tests.py must not reference the oracle patch.")


# --------------------------------------------------------------------------- #
# Model backends
# --------------------------------------------------------------------------- #
class ApiBackend:
    """Direct Anthropic API (needs ANTHROPIC_API_KEY)."""

    def __init__(self, timeout: float):
        import anthropic
        # The SDK already retries 408/409/429/5xx and connection errors with backoff.
        self.client = anthropic.Anthropic(timeout=timeout, max_retries=5)

    def complete(self, model: str, system: str, messages: list[dict], max_tokens: int) -> tuple[str, dict]:
        # Streaming avoids the SDK's non-streaming guard on long generations.
        with self.client.messages.stream(model=model, max_tokens=max_tokens, system=system, messages=messages) as stream:
            final = stream.get_final_message()
        if final.stop_reason == "refusal":
            raise RuntimeError("model refused the request")
        text = "".join(b.text for b in final.content if getattr(b, "type", "") == "text")
        if final.stop_reason == "max_tokens":
            raise GenerationInvalid("Output was truncated at max_tokens; be more concise.")
        return text, {"input_tokens": final.usage.input_tokens, "output_tokens": final.usage.output_tokens}


def call_model(client, model: str, messages: list[dict], max_tokens: int) -> tuple[str, dict]:
    return client.complete(model, SYSTEM_PROMPT, messages, max_tokens)


def generate(client, ctx: Context, model: str, max_tokens: int, max_attempts: int,
             fallback_model: str = "") -> tuple[str, str, dict, dict, dict]:
    """Up to max_attempts generations. If the primary model's output is stopped by the safety filter, the candidate
    switches to `fallback_model` (once, with one extra attempt so the fallback gets a full budget)."""
    messages = [{"role": "user", "content": ctx.prompt}]
    last_err = "unknown"
    refused = 0
    total = {"input_tokens": 0, "output_tokens": 0, "attempts": 0, "models": []}
    budget, attempt = max_attempts, 0
    while attempt < budget:
        attempt += 1
        total["attempts"] = attempt
        total["models"].append(model)
        text = ""          # never reuse an earlier attempt's output in the feedback below
        try:
            text, usage = call_model(client, model, messages, max_tokens)
            total["input_tokens"] += usage["input_tokens"]
            total["output_tokens"] += usage["output_tokens"]
            if usage.get("output_tokens", 0) >= max_tokens * 0.98:      # cut at the output limit: never use a fragment
                raise GenerationInvalid("Output was truncated at the output-token limit; be more concise "
                                        "(shorter report, fewer and tighter tests, minimal check-patch edits).")
            md, code = extract_blocks(text)
            code = no_silent_skips(ensure_pytest_import(code))
            task_meta = extract_metadata(text)
            validate_instruction(md, ctx)
            validate_tests(code, ctx)
            patches = extract_check_patches(text, ctx.env_dir / REPO_DIRNAME)
            return md, code, total, task_meta, patches
        except GenerationInvalid as e:
            last_err = str(e)
            raw = text
            if REFUSAL_RE.search(raw[:600]) and "<instruction_md>" not in raw[:200]:
                # A refusal is not feedback: retry the ORIGINAL request with extra defensive context.
                refused += 1
                if fallback_model and model != fallback_model:
                    log.warning("[%s] attempt %d/%d: %s declined (safety filter); switching to the fallback model %s",
                                ctx.osv_id, attempt, budget, model, fallback_model)
                    model, budget = fallback_model, budget + 1
                else:
                    log.warning("[%s] attempt %d/%d: %s declined (safety filter); retrying with added context",
                                ctx.osv_id, attempt, budget, model)
                try:
                    # one file per refusal across runs (stage 3 retires a candidate after MAX_REFUSALS in total)
                    (ctx.env_dir / f"generation_refused_{time.strftime('%Y%m%d-%H%M%S')}_{attempt}.txt").write_text(raw)
                except OSError:
                    pass
                messages = [{"role": "user", "content": ctx.prompt + REFUSAL_RETRY_NOTE}]
                continue
            log.info("[%s] attempt %d/%d rejected: %s", ctx.osv_id, attempt, budget, last_err)
            # Give the model its own output plus the specific problem; keep the raw reply for diagnosis.
            prior = text
            if prior:
                try:
                    (ctx.env_dir / f"generation_rejected_{time.strftime('%Y%m%d-%H%M%S')}_{attempt}.txt").write_text(
                        f"REJECTED: {last_err}\n\n{prior}")
                except OSError:
                    pass
                messages = [messages[0],
                            {"role": "assistant", "content": prior},
                            {"role": "user", "content":
                             f"Rejected by the validator: {last_err}\nReturn the corrected full output "
                             "in the same strict four-block format."}]
    if refused == attempt:
        raise GenerationInvalid(f"declined by the safety filter on all {attempt} attempts "
                                f"({', '.join(dict.fromkeys(total['models']))}); no task was produced")
    raise GenerationInvalid(f"no valid output after {attempt} attempts: {last_err}")


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #
def write_atomic(path: Path, content: str) -> None:
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(content, encoding="utf-8")
    os.replace(tmp, path)


def already_done(env_dir: Path) -> bool:
    return all((env_dir / n).is_file() and (env_dir / n).stat().st_size > 0
               for n in (INSTRUCTION_NAME, TESTS_NAME))


ABORT = threading.Event()  # set when the quota is exhausted so remaining folders are not attempted


def process(env_dir: Path, candidates: dict, client, args) -> tuple[str, str, str]:
    osv_id = env_dir.name
    if ABORT.is_set():
        return osv_id, "failed", "aborted: quota exhausted earlier in this run"
    if already_done(env_dir):
        return osv_id, "skipped", "already generated"
    try:
        ctx = build_context(env_dir, candidates)
    except ValueError as e:
        log.warning("[%s] cannot build context: %s", osv_id, e)
        return osv_id, "failed", str(e)

    if args.dry_run:
        print(f"===== SYSTEM =====\n{SYSTEM_PROMPT}\n\n===== USER ({len(ctx.prompt)} chars) =====\n{ctx.prompt}")
        return osv_id, "skipped", "dry-run"

    try:
        md, code, usage, task_meta, patches = generate(client, ctx, args.model, args.max_tokens, args.max_attempts,
                                                       args.fallback_model)
    except GenerationInvalid as e:
        log.warning("[%s] FAILED validation: %s", osv_id, e)
        return osv_id, "failed", str(e)
    except SafeguardsFlagged as e:
        ABORT.set()      # an account-level flag: generate nothing more in this run; a human decides how to proceed
        log.error("[%s] Anthropic safeguards flagged the session (AUP) - candidate retired, no retry/fallback: %s",
                  osv_id, str(e)[:200])
        try:
            (env_dir / "safeguards_flagged.txt").write_text(str(e))
        except OSError:
            pass
        return osv_id, "failed", f"safeguards flagged (AUP): {str(e)[:200]}"
    except QuotaExhausted as e:
        ABORT.set()
        log.error("[%s] model quota exhausted - stopping the run: %s", osv_id, e)
        return osv_id, "failed", f"quota exhausted: {e}"
    except Exception as e:  # API errors after SDK retries, auth, refusal, network...
        log.warning("[%s] API FAILURE (%s): %s", osv_id, type(e).__name__, e)
        return osv_id, "failed", f"{type(e).__name__}: {e}"

    try:
        write_atomic(env_dir / TESTS_NAME, code)
        write_atomic(env_dir / "task_metadata.json", json.dumps(task_meta, indent=2))
        (env_dir / CHECK_DIR).mkdir(exist_ok=True)
        for kind, diff in patches.items():
            write_atomic(env_dir / CHECK_DIR / f"{kind}.patch", diff)
        write_atomic(env_dir / META_NAME, json.dumps({"model": usage["models"][-1], "backend": args.backend, **usage},
                                                     indent=2))
        write_atomic(env_dir / INSTRUCTION_NAME, md)  # last: its presence marks completion
    except OSError as e:
        return osv_id, "failed", f"write error: {e}"
    log.info("[%s] generated (%d attempt(s), %d out tokens)", osv_id, usage["attempts"], usage["output_tokens"])
    return osv_id, "ok", ""


def load_candidates(path: Optional[Path]) -> dict[str, dict]:
    if not path:
        return {}
    data = json.loads(path.read_text())
    items = data.get("vulnerabilities", []) if isinstance(data, dict) else data
    return {i["osv_id"]: i for i in items if "osv_id" in i}


def load_api_key(env_file: Optional[Path]) -> None:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=env_file, override=False)  # None -> search upward from cwd
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise SystemExit("ANTHROPIC_API_KEY not found in environment or .env file")


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--environments", type=Path, default=Path("environments"))
    p.add_argument("--candidates", type=Path, help="Stage 1 JSON, supplies summary/CVE/CWE")
    p.add_argument("--env-file", type=Path, help=".env path (default: search upward from cwd)")
    p.add_argument("--backend", choices=("cli", "api"), default=os.environ.get("TASK_GEN_BACKEND", "cli"),
                   help="cli = headless `claude -p` with the logged-in subscription (default); api = ANTHROPIC_API_KEY")
    p.add_argument("--claude-bin", default=os.environ.get("CLAUDE_BIN", "claude"))
    p.add_argument("--model", default=os.environ.get("ANTHROPIC_MODEL", DEFAULT_MODEL))
    p.add_argument("--fallback-model", default=os.environ.get("GEN_FALLBACK_MODEL", "claude-opus-4-8"),
                   help="model used for a candidate after the primary model's output is stopped by the safety filter "
                        "('' = no fallback)")
    p.add_argument("--max-tokens", type=int, default=64000)
    p.add_argument("--max-attempts", type=int, default=3, help="regeneration attempts when validation rejects output")
    p.add_argument("--timeout", type=float, default=3600.0, help="per-call timeout seconds (long: a 64k-token generation can take > 15 min)")
    p.add_argument("--workers", type=int, default=2)
    p.add_argument("--only", nargs="+", help="only these OSV IDs")
    p.add_argument("--dry-run", action="store_true", help="print the prompt, make no API call")
    p.add_argument("-v", "--verbose", action="store_true")
    return p.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    args = parse_args(argv)
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO,
                        format="%(asctime)s %(levelname)s %(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)

    try:
        candidates = load_candidates(args.candidates)
    except (OSError, json.JSONDecodeError) as e:
        log.error("Cannot read candidates file: %s", e)
        return 2
    if not args.environments.is_dir():
        log.error("%s is not a directory", args.environments)
        return 2

    global LESSONS_TEXT
    try:
        from src.common.config import Config
        from src.common.knowledge import lessons_for_prompt
        LESSONS_TEXT = lessons_for_prompt(Config.load())
        if LESSONS_TEXT:
            log.info("Using lessons_learned.md (%d chars) in the generation prompt", len(LESSONS_TEXT))
    except Exception as e:  # lessons are an enhancement, never a blocker
        log.warning("Could not load lessons: %s", e)

    client = None
    if not args.dry_run:
        if args.backend == "cli":
            client = CliBackend(args.claude_bin, args.timeout)
        else:
            load_api_key(args.env_file)
            client = ApiBackend(args.timeout)

    env_dirs = sorted(d for d in args.environments.iterdir()
                      if d.is_dir() and not d.name.startswith(".") and (d / PATCH_NAME).is_file())
    if args.only:
        env_dirs = [d for d in env_dirs if d.name in set(args.only)]
    log.info("%d environments found; backend=%s model=%s", len(env_dirs), args.backend, args.model)

    counts = {"ok": 0, "skipped": 0, "failed": 0}
    failures = []
    try:
        with ThreadPoolExecutor(max_workers=1 if args.dry_run else args.workers) as pool:
            futs = [pool.submit(process, d, candidates, client, args) for d in env_dirs]
            for fut in as_completed(futs):
                osv_id, status, detail = fut.result()
                counts[status] += 1
                if status == "failed":
                    failures.append((osv_id, detail))
    except KeyboardInterrupt:
        log.error("Interrupted")
        return 130

    log.info("Done: %d generated, %d skipped, %d failed", counts["ok"], counts["skipped"], counts["failed"])
    for osv_id, detail in failures:
        log.info("  failed: %s - %s", osv_id, detail[:200])
    return 0


if __name__ == "__main__":
    sys.exit(main())
