"""Harbor task packaging (used by stages 4/5/6) and the Stage 6 runner.

`build_task()` turns one stage-3 environment folder into a Harbor task directory:

    <task>/
      task.toml
      instruction.md                 agent-visible bug report
      environment/Dockerfile         vulnerable repo baked into the image at /app
      environment/repo/              pre-patch checkout (single snapshot commit, fix unreachable)
      solution/solve.sh              oracle: applies the human fix (source files only)
      solution/oracle_solution.patch
      tests/test.sh, score.py        partial score -> /logs/verifier/reward.txt (1.0 only if everything passes)
      tests/existing_files.txt       repo test files for the affected code (stage 4 adds existing_expected.txt)
      tests/existing_node.py         runs those files with the project's own JS runner (vitest/jest/mocha/node --test)
      tests/test_outputs.py          = hidden_tests.py

Answer-key hygiene: tests/ and solution/ never enter the image (Harbor uploads tests/ only after the agent has finished),
the repo history is a single snapshot commit, the container has no network, and test.sh (a) records every file the agent
changed - in the repo and outside it - for the reward-hacking checks of stage 5, (b) runs the hidden tests with plugin
auto-loading off and no repo/root conftest or ini file in effect, and (c) restores the pristine existing tests before
running them.

Stage 4 builds it into `<env>/harbor_task`, stage 5 evaluates that directory and stage 6 copies it, so the
artifact that was validated is byte-for-byte the artifact that ships.
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import re
import shlex
import shutil
import stat
import subprocess
import sys
from pathlib import Path
from typing import Any, Optional

from src.common.classify import is_test_path
from src.common.config import Config
from src.common.harbor import HarborUnavailable, preflight, read_trials, run_harbor
from src.common.logging_setup import configure_logging
from src.common.state_manager import StateManager, Status

log = logging.getLogger(__name__)

STAGE = "stage6_packager"
TASK_DIRNAME = "harbor_task"
ORG = "cwe-bench"
DOCKERFILE_OVERRIDE = "Dockerfile.override"   # drop one next to repo/ to hand-fix a stubborn build

# A uv-managed project (uv.lock): install exactly what the lock declares, every extra and dependency group included
# (dev tools such as `rich` that the repo's own conftest plugins import). For a workspace monorepo (e.g. pydantic-ai)
# this is the only way: the root pins sibling packages at an unreleased version that only the workspace provides. Install the locked workspace (every member
# editable) into the system Python; --inexact keeps what is already installed (pytest, the ctrf plugin).
UV_WORKSPACE_INSTALL = (
    "if [ -f uv.lock ] && grep -qE '^\\[(tool\\.uv\\.workspace|project)\\]' pyproject.toml 2>/dev/null; then "
    "pip install --no-cache-dir uv && export UV_PROJECT_ENVIRONMENT=/usr/local UV_NO_CACHE=1 UV_PYTHON_DOWNLOADS=never "
    "UV_PYTHON=/usr/local/bin/python3 && "
    "(uv sync --frozen --inexact --all-packages --all-extras --all-groups "
    "|| uv sync --frozen --inexact --all-packages); else false; fi")

PY_BASE = "python:3.11-slim-bookworm"
PY_MIN, PY_MAX = (3, 11), (3, 13)


NODE_BASE = "node:22-bookworm"
NODE_MIN, NODE_MAX = 18, 24


def node_base_image(repo: Path) -> str:
    """node:<major>-bookworm from package.json `engines.node` (its lowest major, clamped to 18-24); default 22."""
    try:
        spec = str((json.loads((repo / "package.json").read_text()).get("engines") or {}).get("node") or "")
    except (OSError, ValueError):
        spec = ""
    majors = [int(m) for m in re.findall(r"(?<![\d.])(\d{2})(?=[.x*]|\b)", spec)]
    if not majors:
        return NODE_BASE
    return f"node:{min(max(min(majors), NODE_MIN), NODE_MAX)}-bookworm"


def python_base_image(repo: Path) -> str:
    """The python:<ver>-slim-bookworm image the repo can install on, from pyproject's `requires-python`: its lower
    bound (never below 3.11, so repos that build today keep their image) or the newest minor below an upper bound."""
    try:
        m = re.search(r"""requires-python\s*=\s*["']([^"']+)["']""", (repo / "pyproject.toml").read_text(errors="replace"))
    except OSError:
        m = None
    if not m:
        return PY_BASE
    ver = PY_MIN
    for op, a, b in re.findall(r"(>=|~=|==|>|<=|<)\s*(\d+)\.(\d+)", m.group(1)):
        v = (int(a), int(b))
        if op in (">=", "~=", "==") and v > ver:
            ver = v
        elif op == ">" and (v[0], v[1] + 1) > ver:
            ver = (v[0], v[1] + 1)
    ver = min(ver, PY_MAX)
    for op, a, b in re.findall(r"(<=|<)\s*(\d+)\.(\d+)", m.group(1)):
        hi = (int(a), int(b)) if op == "<=" else (int(a), int(b) - 1)
        ver = min(ver, hi)
    return f"python:{ver[0]}.{ver[1]}-slim-bookworm"


PY_DOCKERFILE = """\
FROM python:3.11-slim-bookworm
RUN apt-get update && apt-get install -y --no-install-recommends git build-essential curl tmux asciinema \\
    && rm -rf /var/lib/apt/lists/*
# The repo's git history is a single snapshot commit (answer-key hygiene), so version-from-git-tags tooling
# (setuptools_scm, hatch-vcs, pbr) would report 0.1.dev1 and break dependency resolution. Pin a high version.
ENV SETUPTOOLS_SCM_PRETEND_VERSION=999.0.0 PBR_VERSION=999.0.0
RUN pip install --no-cache-dir pytest==8.4.1 pytest-json-ctrf==0.3.5
WORKDIR /app
COPY repo/ /app/
# Config templates the project's CI copies before testing (environment.dist.yaml -> environment.yaml,
# phpunit.xml.dist -> phpunit.xml): without them a whole test suite can fail to load (sync-in).
RUN find /app -maxdepth 4 \\( -name node_modules -o -name .git \\) -prune -o -type f -name '*.dist*' -print | while read -r f; do t=$(printf '%s' "$f" | sed -E 's/\\.dist(\\.[^/.]+)?$/\\1/'); [ "$t" != "$f" ] && [ ! -e "$t" ] && cp "$f" "$t"; done; true
# The vulnerable path often needs an optional extra (e.g. protobuf support), and dev tools may live in a PEP 735
# dependency group (pip >= 25.1): install the project with everything it declares, falling back step by step.
RUN pip install --no-cache-dir --upgrade "pip>=25.1" || true
# A uv workspace's lock already holds its dev/test groups. Installing them again with pip would fetch the project's own
# packages (e.g. a group listing "httpx2[http2]") as RELEASED, already-fixed copies into site-packages: an answer key.
RUN if {uv}; then echo "uv workspace installed"; else \\
      (pip install --no-cache-dir -e ".[$(python3 -c 'import tomllib; print(",".join(tomllib.load(open("pyproject.toml","rb")).get("project",{}).get("optional-dependencies",{})))' 2>/dev/null)]" \\
       || pip install --no-cache-dir -e ".[all,test,tests,testing,dev]" \\
       || pip install --no-cache-dir -e ".[test,tests,testing,dev]" || pip install --no-cache-dir -e . || true) \\
      && for g in dev test tests testing; do pip install --no-cache-dir --group "$g" >/dev/null 2>&1 || true; done \\
      && for f in requirements.txt requirements-dev.txt requirements_dev.txt requirements-test.txt \\
                  requirements_test.txt requirements/test.txt requirements/dev.txt dev-requirements.txt \\
                  test-requirements.txt; do \\
           if [ -f "$f" ]; then pip install --no-cache-dir -r "$f" || true; fi; \\
         done; \\
    fi
""".replace("{uv}", UV_WORKSPACE_INSTALL)

# Last layer of every task image: files newer than this marker were written during the run (reward-hacking check).
IMAGE_MARKER = "/etc/.cwe_image_built"
IMAGE_COMMIT = "/etc/.cwe_image_commit"     # repo state right after the image build: the base of the agent's patch
_G = "git -c safe.directory=/app -c user.name=image -c user.email=image@localhost"
MARKER_LAYER = (f"RUN cd /app && {_G} add -A -- . ':!node_modules' ':!**/node_modules' >/dev/null 2>&1; "
                f"{_G} commit -q --allow-empty -m 'image build state' >/dev/null 2>&1; "
                f"{_G} rev-parse HEAD > {IMAGE_COMMIT} 2>/dev/null; touch {IMAGE_MARKER}\n")

# The grader runs in a SEPARATE, fresh container built from the same image ([verifier] environment_mode = "separate").
# Right after the agent stops, this collect hook runs in the AGENT's container and saves only its source changes as a
# patch (+ records of what else it touched) under /logs/artifacts, the one directory Harbor carries over. Nothing else
# the agent did - to Python, pytest, node_modules, /usr/bin - can reach the grader.
COLLECT_SH = f"""mkdir -p /logs/artifacts; cd /app || exit 0
G="git -c safe.directory=/app"
BASE=$(cat {IMAGE_COMMIT} 2>/dev/null || $G rev-parse HEAD 2>/dev/null)
$G add -A -- . ':!node_modules' ':!**/node_modules' >/dev/null 2>&1   # rc 1 only means "some paths are ignored"
if $G diff --cached --binary --no-renames "$BASE" > /logs/artifacts/agent.patch \\
   && $G diff --cached --name-status --no-renames "$BASE" > /logs/artifacts/agent_changes.txt; then :
else echo "could not diff /app against the image state (git missing or .git damaged)" > /logs/artifacts/collect_error.txt; fi
$G reset -q >/dev/null 2>&1
find / -xdev \\( -path /proc -o -path /sys -o -path /dev -o -path /app -o -path /logs -o -path /tests -o -path /tmp \\
    -o -path /var/tmp -o -path /root -o -path /home -o -path /run -o -path /var/log -o -path /var/cache \\
    -o -path /var/lib/apt -o -path /var/lib/dpkg -o -name __pycache__ \\) -prune \\
    -o -type f -newer {IMAGE_MARKER} ! -name '*.pyc' -print 2>/dev/null | head -500 > /logs/artifacts/outside_changes.txt
[ -d /app/node_modules ] && find /app/node_modules \\( -name .cache -o -name '.vite*' -o -name .vitest \\) -prune \\
    -o -type f -newer {IMAGE_MARKER} -print 2>/dev/null | head -200 > /logs/artifacts/dependency_changes.txt
exit 0"""

# Files the grader never takes from the agent's patch: test-runner configuration, manifests and lockfiles (dependencies
# cannot be installed offline anyway). Changes to them are listed in agent_patch_dropped.txt.
GRADER_EXCLUDES = ("conftest.py", "pytest.ini", "tox.ini", "setup.cfg", "pyproject.toml", "package.json",
                   "package-lock.json", "yarn.lock", "pnpm-lock.yaml", "bun.lock", "bun.lockb", "sitecustomize.py",
                   "usercustomize.py", "*.pth", "vitest.config.*", "vite.config.*", "jest.config.*", "jest.setup.*",
                   "karma.conf.*", ".mocharc*", "go.mod", "go.sum", "go.work", "go.work.sum",
                   "composer.json", "composer.lock", "phpunit.xml", "phpunit.xml.dist", "phpunit.dist.xml", "Pest.php")
_EXCL = " ".join(f"--exclude='{x}' --exclude='*/{x}'" for x in GRADER_EXCLUDES)

# Package-manager detection shared by the stage-3 build check and the task image: bun / pnpm / yarn / npm. The exact
# lockfile is tried first; an out-of-date lockfile (common at a mid-history commit) falls back to a normal install.
NODE_INSTALL = """\
RUN if [ -f bun.lock ] || [ -f bun.lockb ]; then \\
      BV=$(node -p "((require('./package.json').packageManager||'').match(/^bun@([^+]+)/)||[])[1]||''") \\
      && npm install -g "bun${BV:+@$BV}" && (bun install --frozen-lockfile || bun install); \\
    elif [ -f pnpm-lock.yaml ]; then corepack enable \\
      && PV=$(node -p "require('./package.json').packageManager ? '' : (((require('./package.json').engines||{}).pnpm||'').match(/\\d+(\\.\\d+){0,2}/)||[''])[0]") \\
      && { [ -n "$PV" ] || PV=$(sed -n "s/^lockfileVersion: *'\\{0,1\\}\\([0-9]*\\).*/\\1/p" pnpm-lock.yaml | head -1 | awk '$1>=9{print $1}'); } \\
      && { [ -z "$PV" ] || corepack prepare "pnpm@$PV" --activate; } \\
      && (pnpm install --frozen-lockfile || pnpm install --no-frozen-lockfile); \\
    elif [ -f yarn.lock ]; then corepack enable && (yarn install --frozen-lockfile || yarn install); \\
    else npm ci || npm install; fi"""
# Answer-key hygiene: a project's own dev tooling often depends on the project itself (fast-uri <- ajv), so the install
# pulls the RELEASED package - which already contains the fix - into node_modules. Replace every installed real copy
# of any package defined in the repo with a link to its local source (the vulnerable code under test).
NODE_SELF_LINK_JS = r"""
const fs = require('fs'), path = require('path');
const local = {};
(function scan(d, depth) {
  if (depth > 4) return;
  let es; try { es = fs.readdirSync(d, {withFileTypes: true}); } catch (e) { return; }
  for (const e of es) {
    if (e.name === 'node_modules' || e.name === '.git' || e.isSymbolicLink()) continue;
    const p = path.join(d, e.name);
    if (e.isDirectory()) scan(p, depth + 1);
    else if (e.name === 'package.json') {
      try { const n = JSON.parse(fs.readFileSync(p, 'utf8')).name; if (n && !local[n]) local[n] = d; } catch (err) {}
    }
  }
})('/app', 0);
let linked = 0;
(function walk(d, depth) {
  if (depth > 14) return;
  let es; try { es = fs.readdirSync(d, {withFileTypes: true}); } catch (e) { return; }
  for (const e of es) {
    if (e.isSymbolicLink() || !e.isDirectory()) continue;
    const p = path.join(d, e.name);
    const m = p.match(/node_modules\/((?:@[^/]+\/)?[^/@][^/]*)$/);
    if (m && local[m[1]]) {
      fs.rmSync(p, {recursive: true, force: true});
      fs.symlinkSync(local[m[1]], p);
      linked++;
      continue;
    }
    walk(p, depth + 1);
  }
})('/app/node_modules', 0);
if (linked) console.log('self-link: replaced ' + linked + ' installed copies of repo packages with links to the source');
"""
import base64 as _b64
NODE_SELF_LINK = ("RUN echo " + _b64.b64encode(NODE_SELF_LINK_JS.encode()).decode()
                  + " | base64 -d > /tmp/self-link.js && node /tmp/self-link.js; rm -f /tmp/self-link.js")

# A test folder can be its own package outside the workspace (9router: tests/package.json declares vitest; the root
# install never installs it), so its runner is missing and no existing test can run. Install such a package's own
# dependencies when the runner it declares cannot be found from its folder.
NODE_TEST_PKGS_JS = r"""
const fs = require('fs'), path = require('path'), cp = require('child_process');
const RUNNERS = ['vitest', 'jest', 'mocha', 'tape', 'tap'];
const found = (d, r) => { for (;;) { if (fs.existsSync(path.join(d, 'node_modules', '.bin', r))) return true;
  if (d === '/app') return false; d = path.dirname(d); } };
const runnerOf = f => { let m = {}; try { m = JSON.parse(fs.readFileSync(f, 'utf8')); } catch (err) {}
  const deps = {...m.dependencies, ...m.devDependencies}; return RUNNERS.find(x => deps[x]); };
// The root install (or a workspace member's share of it) can fail half-way and the Dockerfile tolerates that, leaving
// no runner binary (sync-in: vitest without .bin/vitest). Re-run the ROOT install once in that case.
const root = (() => { let m = {}; try { m = JSON.parse(fs.readFileSync('/app/package.json', 'utf8')); } catch (err) {}
  const ws = Array.isArray(m.workspaces) ? m.workspaces : ((m.workspaces || {}).packages || []);
  return ws.map(w => path.join('/app', w.replace(/\/\*+$/, ''))); })();
const member = p => p === '/app' || root.some(w => p === w || p.startsWith(w + '/'));
const rootMissing = ['/app', ...root].some(d => { const r = runnerOf(path.join(d, 'package.json')); return r && !found(d, r); });
if (rootMissing) {
  const cmd = fs.existsSync('/app/pnpm-lock.yaml') ? 'pnpm install --frozen-lockfile || pnpm install'
    : fs.existsSync('/app/yarn.lock') ? 'yarn install --frozen-lockfile || yarn install'
    : 'npm ci --no-audit --no-fund || npm install --no-audit --no-fund';
  console.log('test runner missing after the root install - re-running it: ' + cmd);
  try { cp.execSync(cmd, {cwd: '/app', stdio: 'inherit', shell: '/bin/sh'}); } catch (err) {}
}
(function scan(d, depth) {
  if (depth > 3) return;
  let es; try { es = fs.readdirSync(d, {withFileTypes: true}); } catch (e) { return; }
  for (const e of es) {
    if (!e.isDirectory() || e.name === 'node_modules' || e.name.startsWith('.')) continue;
    const p = path.join(d, e.name), f = path.join(p, 'package.json');
    if (fs.existsSync(f)) {
      let m = {}; try { m = JSON.parse(fs.readFileSync(f, 'utf8')); } catch (err) {}
      const deps = {...m.dependencies, ...m.devDependencies};
      const r = RUNNERS.find(x => deps[x]);
      if (r && !found(p, r) && !member(p)) {        // workspace members are handled by the root install above
        console.log('installing test package ' + p + ' (' + r + ')');
        // --legacy-peer-deps: npm's peer-set resolver crashes on optional peers (jsdom -> canvas, "edgesOut")
        for (const flags of ['', ' --legacy-peer-deps']) {
          try { cp.execSync('npm install --no-audit --no-fund --no-package-lock' + flags, {cwd: p, stdio: 'inherit'}); break; }
          catch (err) {}
        }
      }
    }
    scan(p, depth + 1);
  }
})('/app', 0);
"""
NODE_TEST_PKGS = ("RUN echo " + _b64.b64encode(NODE_TEST_PKGS_JS.encode()).decode()
                  + " | base64 -d > /tmp/test-pkgs.js && node /tmp/test-pkgs.js; rm -f /tmp/test-pkgs.js")

# Browser tests (vitest browser mode, playwright test): the npm package carries no browser binary, so download the
# matching Chromium at BUILD time (the offline agent and grader cannot). Only when the project depends on playwright.
NODE_PLAYWRIGHT = ("RUN P=$(find /app -path '*/node_modules/.bin/playwright' -not -path '*/node_modules/*/node_modules/*' "
                   "2>/dev/null | head -1); if [ -n \"$P\" ]; then \"$P\" install --with-deps chromium || true; fi")

# Go: one base image; GOTOOLCHAIN=auto lets `go` fetch a newer toolchain at BUILD time when go.mod asks for one, so it
# is cached in the image and the offline agent/grader never needs the network. Test binaries are pre-compiled.
GO_DOCKERFILE = """\
FROM golang:1.24-bookworm
RUN apt-get update && apt-get install -y --no-install-recommends python3 python3-pip git tmux asciinema \\
    && rm -rf /var/lib/apt/lists/*
RUN pip3 install --no-cache-dir --break-system-packages pytest==8.4.1 pytest-json-ctrf==0.3.5
ENV GOTOOLCHAIN=auto
WORKDIR /app
COPY repo/ /app/
RUN (go mod download || true) && (go build ./... || true) \\
    && (go test -count=1 -run '^$' ./... > /dev/null 2>&1 || true)
"""

EXISTING_GO_PY = r'''"""Run the repo's own Go tests for the packages listed in /tests/existing_files.txt -> ctrf_existing.json.
One `go test -json` per package; names are "<package dir>::<TestName[/subtest]>"."""
import json
import subprocess
from pathlib import Path

APP, OUT = Path("/app"), Path("/logs/verifier/ctrf_existing.json")
tests = {}
pkgs = sorted({str(Path(l.strip()).parent) for l in open("/tests/existing_files.txt") if l.strip()})
for pkg in pkgs:
    target = "./" + pkg if pkg not in (".", "") else "."
    try:
        proc = subprocess.run(["go", "test", "-json", "-count=1", target], cwd=APP, timeout=300,
                              capture_output=True, text=True)
        out = proc.stdout
    except (OSError, subprocess.TimeoutExpired):
        tests[f"{pkg}::(go test timed out or failed to start)"] = "failed"
        continue
    found = 0
    for line in out.splitlines():
        try:
            ev = json.loads(line)
        except ValueError:
            continue
        if ev.get("Test") and ev.get("Action") in ("pass", "fail", "skip"):
            found += 1
            tests[f"{pkg}::{ev['Test']}"] = {"pass": "passed", "fail": "failed", "skip": "skipped"}[ev["Action"]]
    if not found:
        tests[f"{pkg}::(no results)"] = "failed"
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({"results": {"tests": [{"name": n, "status": s} for n, s in tests.items()]}}))
print(f"existing tests: {sum(s == 'passed' for s in tests.values())}/{len(tests)} passed")
'''

# PHP (Composer): the base image follows composer.json's "php" constraint (highest supported release that satisfies it);
# common extensions are compiled one by one so a single unavailable one cannot fail the image.
PHP_VERSIONS = ("8.4", "8.3", "8.2", "8.1", "8.0", "7.4")
PHP_BASE = "php:8.3-cli-bookworm"
PHP_EXTENSIONS = "zip intl gd bcmath pdo_mysql pdo_pgsql pcntl gmp exif sockets soap xsl"


def _php_ok(ver: str, constraint: str) -> bool:
    import re as _re
    v = tuple(int(x) for x in ver.split("."))
    def one(c: str) -> bool:
        ok = True
        for op, a, b, patch in _re.findall(r"(\^|~|>=|<=|>|<|=)?\s*v?(\d+)(?:\.(\d+|\*))?(?:\.(\d+|\*))?", c):
            t = (int(a), int(b) if b and b != "*" else 0)
            if op == "^":
                ok &= v >= t and v[0] == t[0]
            elif op == "~":       # ~8.1 -> >=8.1 <9; ~8.1.0 -> >=8.1 <8.2
                ok &= v >= t and v[0] == t[0] and (v[1] == t[1] if patch else True)
            elif op == ">=":
                ok &= v >= t
            elif op == ">":
                ok &= v > t
            elif op == "<=":
                ok &= v <= t
            elif op == "<":
                ok &= v < t
            else:
                ok &= v[0] == t[0] and (not b or b == "*" or v[1] == t[1])
        return ok
    return any(one(part) for part in _re.split(r"\|\|?", constraint) if part.strip())


def php_base_image(repo: Path) -> str:
    try:
        req = (json.loads((repo / "composer.json").read_text()).get("require") or {}).get("php", "")
    except (OSError, ValueError):
        req = ""
    if not req:
        return PHP_BASE
    for ver in PHP_VERSIONS:
        try:
            if _php_ok(ver, req):
                return f"php:{ver}-cli-bookworm"
        except ValueError:
            break
    return PHP_BASE


PHP_DOCKERFILE = f"""\
FROM {PHP_BASE}
RUN apt-get update && apt-get install -y --no-install-recommends git unzip python3 python3-pip tmux asciinema nodejs \\
        libzip-dev libicu-dev libpng-dev libjpeg-dev libfreetype6-dev libwebp-dev libxml2-dev libonig-dev libsqlite3-dev \\
        libpq-dev libgmp-dev libxslt1-dev \\
    && rm -rf /var/lib/apt/lists/*
# gd needs explicit JPEG/WebP/FreeType support, or apps that pick an image format find none (koel GHSA-rjg7)
RUN docker-php-ext-configure gd --with-jpeg --with-freetype --with-webp > /dev/null 2>&1 || echo "gd configure skipped"
RUN for e in {PHP_EXTENSIONS}; do docker-php-ext-install -j"$(nproc)" "$e" > /dev/null 2>&1 || echo "skip ext $e"; done
RUN pip3 install --no-cache-dir --break-system-packages pytest==8.4.1 pytest-json-ctrf==0.3.5
COPY --from=composer:2 /usr/bin/composer /usr/local/bin/composer
ENV COMPOSER_ALLOW_SUPERUSER=1 COMPOSER_NO_INTERACTION=1
WORKDIR /app
COPY repo/ /app/
RUN find /app -maxdepth 4 \\( -name node_modules -o -name .git \\) -prune -o -type f -name '*.dist*' -print | while read -r f; do t=$(printf '%s' "$f" | sed -E 's/\\.dist(\\.[^/.]+)?$/\\1/'); [ "$t" != "$f" ] && [ ! -e "$t" ] && cp "$f" "$t"; done; true
# the repo's own version (a snapshot has no tags, so Composer would call it dev-master and reject dev tools that
# require it, e.g. guzzle's test-server -> guzzle ^8): composer.json version, branch alias, newest changelog entry
RUN echo PD9waHAKJGogPSBqc29uX2RlY29kZShAZmlsZV9nZXRfY29udGVudHMoJ2NvbXBvc2VyLmpzb24nKSwgdHJ1ZSkgPzogW107CmlmICghZW1wdHkoJGpbJ3ZlcnNpb24nXSkpIHsgZWNobyAkalsndmVyc2lvbiddOyBleGl0OyB9CiRhID0gJGpbJ2V4dHJhJ11bJ2JyYW5jaC1hbGlhcyddID8/IFtdOwpmb3JlYWNoIChbJ2Rldi1tYXN0ZXInLCAnZGV2LW1haW4nLCAnZGV2LWRldmVsb3AnLCAnZGV2LXRydW5rJ10gYXMgJGIpIHsgaWYgKCFlbXB0eSgkYVskYl0pKSB7IGVjaG8gJGFbJGJdOyBleGl0OyB9IH0KZm9yZWFjaCAoYXJyYXlfbWVyZ2UoZ2xvYignQ0hBTkdFTE9HKicpID86IFtdLCBnbG9iKCdDSEFOR0VTKicpID86IFtdLCBnbG9iKCdVUEdSQURFKicpID86IFtdKSBhcyAkZikgewogIGlmIChwcmVnX21hdGNoKCcvXGIoXGQrXC5cZCtcLlxkKylcYi8nLCAoc3RyaW5nKSBAZmlsZV9nZXRfY29udGVudHMoJGYpLCAkbSkpIHsgZWNobyAkbVsxXTsgZXhpdDsgfQp9Cg== | base64 -d > /tmp/rootver.php && CRV=$(php /tmp/rootver.php); rm -f /tmp/rootver.php; \\
    if [ -n "$CRV" ]; then export COMPOSER_ROOT_VERSION="$CRV"; fi; \\
    # --no-scripts: the project's install hooks boot the whole app (artisan / Symfony console) at build time, and any
    # app-level startup problem killed the build (koel, pimcore 2026-10-20); the autoloader is still generated
    (composer install --no-progress --prefer-dist --ignore-platform-reqs --no-scripts \\
     || composer update --no-progress --prefer-dist --ignore-platform-reqs --no-scripts) || true
"""

EXISTING_PHP_PY = r'''"""Run the repo's own PHP test files (/tests/existing_files.txt) with PHPUnit or Pest -> ctrf_existing.json.
One runner call per file; names are "<file>::<class> > <test>"."""
import json
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

APP, OUT = Path("/app"), Path("/logs/verifier/ctrf_existing.json")
runner = next((str(APP / "vendor" / "bin" / r) for r in ("pest", "phpunit") if (APP / "vendor" / "bin" / r).exists()), None)
tests = {}
for rel in [l.strip() for l in open("/tests/existing_files.txt") if l.strip()]:
    xml = Path("/tmp/existing.xml")
    xml.unlink(missing_ok=True)
    if not runner:
        tests[f"{rel}::(no runnable test runner)"] = "failed"
        continue
    try:
        subprocess.run([runner, "--log-junit", str(xml), rel], cwd=APP, timeout=300, stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL)
    except (OSError, subprocess.TimeoutExpired):
        tests[f"{rel}::(runner timed out or failed to start)"] = "failed"
        continue
    found = 0
    try:
        for case in ET.parse(xml).getroot().iter("testcase"):
            found += 1
            status = "failed" if case.find("failure") is not None or case.find("error") is not None else (
                "skipped" if case.find("skipped") is not None else "passed")
            name = f"{rel}::{case.get('class') or case.get('classname', '')} > {case.get('name', '')}"
            while name in tests:
                name += "'"
            tests[name] = status
    except (OSError, ET.ParseError):
        pass
    if not found:
        tests[f"{rel}::(no results)"] = "failed"
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({"results": {"tests": [{"name": n, "status": s} for n, s in tests.items()]}}))
print(f"existing tests: {sum(s == 'passed' for s in tests.values())}/{len(tests)} passed")
'''

NODE_BUILD = ("if [ -f bun.lock ] || [ -f bun.lockb ]; then bun run --if-present build 2>/dev/null || bun run build; "
              # a pnpm monorepo's root `build` script is the curated build (e.g. turbo with filters); a recursive
              # build would also try every test fixture and stop at the first one that cannot build
              "elif [ -f pnpm-lock.yaml ]; then "
              "if node -e \"process.exit(require('./package.json').scripts?.build ? 0 : 1)\" 2>/dev/null; "
              "then pnpm run build || pnpm -r --if-present --no-bail run build; "
              "else pnpm -r --if-present --no-bail run build; fi; "
              "elif [ -f yarn.lock ]; then yarn run build; else npm run build --if-present; fi")

# The grader (2 CPUs, a 600 s build limit) only has to recompile what the agent's patch touched: the image already
# holds the build of the vulnerable tree. In a pnpm monorepo, rebuild just the packages changed since the image's
# commit (a full astro rebuild took >600 s on 2 CPUs); anything else, or a failed incremental build, does the full one.
NODE_REBUILD = ("git config --global --add safe.directory /app 2>/dev/null; BASE=$(cat " + IMAGE_COMMIT + " 2>/dev/null); "
                "if [ -f pnpm-lock.yaml ] && [ -n \"$BASE\" ] && "
                "git -c safe.directory=/app cat-file -e \"$BASE\" 2>/dev/null; then "
                "pnpm --filter \"[$BASE]\" --if-present --no-bail run build || { " + NODE_BUILD + "; }; "
                "else " + NODE_BUILD + "; fi")

NODE_DOCKERFILE = f"""\
FROM node:22-bookworm
RUN apt-get update && apt-get install -y --no-install-recommends python3 python3-pip git build-essential tmux asciinema \\
    && rm -rf /var/lib/apt/lists/*
RUN pip3 install --no-cache-dir --break-system-packages pytest==8.4.1 pytest-json-ctrf==0.3.5
WORKDIR /app
COPY repo/ /app/
# Config templates the project's CI copies before testing (environment.dist.yaml -> environment.yaml,
# phpunit.xml.dist -> phpunit.xml): without them a whole test suite can fail to load (sync-in).
RUN find /app -maxdepth 4 \\( -name node_modules -o -name .git \\) -prune -o -type f -name '*.dist*' -print | while read -r f; do t=$(printf '%s' "$f" | sed -E 's/\\.dist(\\.[^/.]+)?$/\\1/'); [ "$t" != "$f" ] && [ ! -e "$t" ] && cp "$f" "$t"; done; true
{NODE_INSTALL} || true
{NODE_TEST_PKGS}
{NODE_PLAYWRIGHT}
{NODE_SELF_LINK}
# Compile TypeScript/bundled packages so dist/ exists for the agent and for the pre-patch run.
RUN ({NODE_BUILD}) || true
"""

CLAUDE_CODE_LAYER = """\
# Agent harness baked into the image (same native installer Harbor uses on Debian; needs no Node.js, so the project's own
# Node version is untouched). Nothing is downloaded during the allowlisted agent phase.
# Downloaded to a file with retries: a piped `curl | bash` hides a failed download (bash runs an empty script and only
# the final `claude --version` fails, exit 127).
RUN curl -fsSL --retry 5 --retry-delay 3 --retry-all-errors -o /tmp/claude-bootstrap.sh \\
        https://downloads.claude.ai/claude-code-releases/bootstrap.sh \\
    && bash /tmp/claude-bootstrap.sh {version} && rm -f /tmp/claude-bootstrap.sh \\
    && ln -sf "$HOME/.local/bin/claude" /usr/local/bin/claude && claude --version
"""

OFFLINE_COMPOSE = """\
# Task container is fully offline in every phase (agent + verifier). Enforced by Docker itself (network_mode: none):
# Harbor's own no-network/allowlist modes need an nftables kernel feature that Docker Desktop for Mac lacks.
services:
  main:
    network_mode: none
"""

# In-container agents (Claude Code): the task container is on an INTERNAL Docker network with no route out; the only way
# out is the egress proxy (docker/egress), which forwards HTTPS to the model-API hosts only. This is how the allowlist
# is enforced on Docker Desktop for Mac, where Harbor's own allowlist mode (nftables) is not available.
EGRESS_IMAGE = "cwe-egress:2"   # v2: TCP keepalive + per-connection close logging
EGRESS_DIR = Path(__file__).resolve().parents[2] / "docker" / "egress"
EGRESS_OUTSIDE_NET = "cwe-egress-outside"
PROXY_COMPOSE = """\
# Agent container: internal network only (no route to the internet). Its single way out is the egress proxy, which
# allows HTTPS to the model-API hosts below and nothing else (docker/egress/egress.py; decisions in its docker logs).
services:
  main:
    networks: [agent_isolated]
    environment:
      HTTPS_PROXY: http://egress:3128
      https_proxy: http://egress:3128
      HTTP_PROXY: http://egress:3128
      http_proxy: http://egress:3128
      NO_PROXY: localhost,127.0.0.1
      no_proxy: localhost,127.0.0.1
    depends_on: [egress]
  egress:
    image: {image}
    pull_policy: never
    environment:
      ALLOWED_HOSTS: {hosts}
    networks: [agent_isolated, egress_outside]
networks:
  agent_isolated:
    internal: true
  egress_outside:                # ONE shared outbound network for every task's proxy (Docker has few address pools)
    external: true
    name: {outside}
"""


def ensure_egress_image() -> None:
    """Build the egress proxy image once per machine (it is referenced by tag, never pulled)."""
    import subprocess as sp
    if sp.run(["docker", "image", "inspect", EGRESS_IMAGE], capture_output=True).returncode != 0:
        sp.run(["docker", "build", "-q", "-t", EGRESS_IMAGE, str(EGRESS_DIR)], check=True, capture_output=True)
    if sp.run(["docker", "network", "inspect", EGRESS_OUTSIDE_NET], capture_output=True).returncode != 0:
        sp.run(["docker", "network", "create", EGRESS_OUTSIDE_NET], check=True, capture_output=True)


TOOLS_LAYER = """\
RUN (apt-get update && apt-get install -y --no-install-recommends tmux asciinema && rm -rf /var/lib/apt/lists/*) || true
"""

# Verifier time budget: test.sh's own limits (build + hidden tests + existing tests) plus slack. task.toml uses the total,
# so a slow build or suite can never be cut off by Harbor before a reward is written.
BUILD_BUDGET_SEC, HIDDEN_BUDGET_SEC, EXISTING_BUDGET_SEC = 600, 900, 900
VERIFY_BUDGET_SEC = BUILD_BUDGET_SEC + HIDDEN_BUDGET_SEC + EXISTING_BUDGET_SEC + 300

TEST_SH = f"""\
#!/bin/bash
# Partial-score grading. Reward = mean of the fractions of passing (a) hidden security tests,
# (b) hidden functional tests, (c) the repo's existing tests that stage 4 proved pass before AND after the fix.
# Reward is exactly 1.0 only if everything passes. Written on every code path.
set -uo pipefail
mkdir -p /logs/verifier
cd /app || {{ echo 0 > /logs/verifier/reward.txt; exit 0; }}
export PYTHONPATH="/app:${{PYTHONPATH:-}}" REPO_ROOT=/app

# 1. This is a FRESH container from the task image (separate grader), so the agent's environment is gone. Apply only
#    its source patch, collected from its container when it stopped - never its test-runner config or manifests.
for f in agent_changes.txt outside_changes.txt dependency_changes.txt collect_error.txt; do
  [ -f /logs/artifacts/$f ] && cp /logs/artifacts/$f /logs/verifier/$f
done
if [ -s /logs/artifacts/agent.patch ]; then
  cp /logs/artifacts/agent.patch /logs/verifier/agent.diff
  grep -E '^diff --git ' /logs/artifacts/agent.patch | sed 's|^diff --git a/[^ ]* b/||' > /logs/verifier/agent_patch_files.txt
  git -c safe.directory=/app apply --binary --whitespace=nowarn {_EXCL} /logs/artifacts/agent.patch \\
      > /logs/verifier/agent_patch_apply.log 2>&1 || {{ echo "APPLY FAILED" >> /logs/verifier/agent_patch_apply.log;
    git -c safe.directory=/app apply --binary --whitespace=nowarn --reject {_EXCL} /logs/artifacts/agent.patch \\
      >> /logs/verifier/agent_patch_apply.log 2>&1; }}
  git -c safe.directory=/app diff --name-only > /logs/verifier/agent_patch_applied.txt 2>/dev/null
  git -c safe.directory=/app ls-files --others --exclude-standard >> /logs/verifier/agent_patch_applied.txt 2>/dev/null
  sort -u /logs/verifier/agent_patch_files.txt | comm -23 - <(sort -u /logs/verifier/agent_patch_applied.txt) \\
      > /logs/verifier/agent_patch_dropped.txt
else
  echo "no agent changes" > /logs/verifier/agent_patch_apply.log
fi

# 2. Compiled (TypeScript/bundled) projects: rebuild so the code under test is what is in /app/src right now
#    (the agent's or the oracle's edits), not what was compiled when the image was built.
if [ -f /tests/node_build.sh ]; then timeout {BUILD_BUDGET_SEC} bash /tests/node_build.sh > /logs/verifier/build.log 2>&1 || true; fi

# 3. Hidden tests. No plugin auto-loading (only the ctrf reporter) and no ini/conftest from the repo or / can take effect.
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 timeout {HIDDEN_BUDGET_SEC} python3 -m pytest /tests/test_outputs.py -p ctrf.main \\
    -p no:cacheprovider -q --rootdir=/app -c /dev/null --confcutdir=/tests --ctrf /logs/verifier/ctrf.json
HIDDEN_RC=$?

# 4. The repo's existing tests, from pristine copies (the agent cannot edit them, or their conftest/ini, to pass).
if [ -s /tests/existing_files.txt ]; then
  [ -d /tests/existing_snapshot ] && cp -a /tests/existing_snapshot/. /app/
  if [ -f /tests/existing_node.py ]; then
    timeout {EXISTING_BUDGET_SEC} python3 /tests/existing_node.py
  elif [ -f /tests/existing_go.py ]; then
    timeout {EXISTING_BUDGET_SEC} python3 /tests/existing_go.py
  elif [ -f /tests/existing_php.py ]; then
    timeout {EXISTING_BUDGET_SEC} python3 /tests/existing_php.py
  else
    mapfile -t EXISTING < /tests/existing_files.txt
    timeout {EXISTING_BUDGET_SEC} python3 -m pytest "${{EXISTING[@]}}" -p no:cacheprovider -q --rootdir=/app \\
        --continue-on-collection-errors --ctrf /logs/verifier/ctrf_existing.json
  fi
fi

python3 /tests/score.py "$HIDDEN_RC"
exit 0
"""

EXISTING_NODE_PY = r'''"""Run the repo's own JS/TS test files (/tests/existing_files.txt) with the project's runner -> ctrf_existing.json.
One runner call per file (so every result maps to its file); names are "<file>::<suite / test title>"."""
import json
import os
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

APP, OUT = Path("/app"), Path("/logs/verifier/ctrf_existing.json")
RUNNERS = ("vitest", "jest", "mocha", "tape", "tap")   # "tape" before "tap": a script naming tape also contains "tap"


def manifest(d):
    try:
        return json.loads((d / "package.json").read_text())
    except (OSError, ValueError):
        return {}


def runner_for(test_file):
    """Nearest package.json (up to /app) that names a runner in its deps or test script -> (runner, package dir)."""
    d = (APP / test_file).parent
    while True:
        # a monorepo package with its OWN runner config (packages/x/jest.config.js) must run from that folder,
        # even when only the root package.json names the runner
        if any(d.glob("jest.config.*")):
            return "jest", d
        if any(d.glob("vitest.config.*")) or any(d.glob("vitest.workspace.*")):
            return "vitest", d
        m = manifest(d)
        deps = {**m.get("dependencies", {}), **m.get("devDependencies", {})}
        script = (m.get("scripts") or {}).get("test", "")
        for r in RUNNERS:
            if r in deps or r in script:
                return r, d
        if "node --test" in script:
            return "node", d
        if d == APP:
            return None, APP
        d = d.parent


def script_setup(pkg, runner):
    """Follow the package's `test` script chain (test -> test:playwright -> test:unit ...) and collect what it sets for
    the runner: VAR=value prefixes and --config <file> (test/browser in vitest: PROVIDER=playwright,
    --config=vitest.config.unit.mts). Returns (env, config path or None)."""
    import re, shlex
    scripts = (manifest(pkg).get("scripts") or {})
    env, config, name, seen = {}, None, "test", set()
    while name in scripts and name not in seen:
        seen.add(name)
        cmd = scripts[name]
        for k, v in re.findall(r"(?:^|&&|;|\s)([A-Z][A-Z0-9_]*)=(\S+)", cmd):
            env.setdefault(k, v.strip("'\""))
        if runner in cmd:
            try:
                words = shlex.split(cmd)
            except ValueError:
                words = cmd.split()
            for i, w in enumerate(words):
                if w.startswith("--config="):
                    config = w.split("=", 1)[1]
                elif w in ("--config", "-c") and i + 1 < len(words):
                    config = words[i + 1]
            break
        nxt = re.search(r"(?:pnpm|npm|yarn)(?:\s+-\S+)*\s+(?:run\s+)?([\w:.-]+)", cmd)
        name = nxt.group(1) if nxt else ""
    if config and not (pkg / config).is_file():
        config = None
    return env, config


def binary(name, start):
    d = start
    while True:
        b = d / "node_modules" / ".bin" / name
        if b.exists():
            return str(b)
        if d == APP:
            return None
        d = d.parent


def junit(path, prefix):
    out = {}
    try:
        root = ET.parse(path).getroot()
    except (OSError, ET.ParseError):
        return out
    for case in root.iter("testcase"):
        status = "failed" if case.find("failure") is not None or case.find("error") is not None else (
            "skipped" if case.find("skipped") is not None else "passed")
        name = f"{prefix}::{case.get('classname', '')} > {case.get('name', '')}"
        while name in out:
            name += "'"
        out[name] = status
    return out


def tap(text, prefix):
    """TAP -> {"<file>::<test> #<k> <assertion>": status}; k numbers the assertions inside each `# test` header, so
    names stay stable however many tests ran before."""
    import re
    out, current, k = {}, "", 0
    for line in text.splitlines():
        s = line.strip()
        h = re.match(r"^# (?!tests\b|pass\b|fail\b|ok\b|todo\b|skip\b)(.+)$", s)
        if h:
            current, k = h.group(1).strip(), 0
            continue
        m = re.match(r"^(not )?ok\s+\d+\s*-?\s*(.*?)(\s+#\s*(SKIP|TODO)\b.*)?$", s, re.I)
        if m:
            k += 1
            status = "skipped" if m.group(4) else ("failed" if m.group(1) else "passed")
            out[f"{prefix}::{current} #{k} {m.group(2).strip()}"] = status
    return out


def uses_node_test(rel):
    """A file written for Node's built-in runner (import from 'node:test') runs with `node --test`, whatever the
    package's test script wraps it in (astro: astro-scripts test --strip-types)."""
    try:
        head = (APP / rel).read_text(errors="replace")[:4000]
    except OSError:
        return False
    return "'node:test'" in head or '"node:test"' in head


def run_file(rel):
    runner, pkg = runner_for(rel)
    if uses_node_test(rel):
        runner = "node"
    target = str((APP / rel).relative_to(pkg)) if pkg != APP else rel
    xml, js = Path("/tmp/existing.xml"), Path("/tmp/existing.json")
    for p in (xml, js):
        p.unlink(missing_ok=True)
    exe = binary(runner, pkg) if runner in RUNNERS else None
    extra_env, config = script_setup(pkg, runner) if runner in ("vitest", "jest") else ({}, None)
    cfg_args = ["--config", config] if config else []
    if runner == "vitest" and exe:
        cmd = [exe, "run", target, "--reporter=junit", f"--outputFile={xml}", *cfg_args]
    elif runner == "jest" and exe:
        cmd = [exe, "--ci", "--watchAll=false", "--runTestsByPath", target, "--json", f"--outputFile={js}", *cfg_args]
    elif runner == "mocha" and exe:
        cmd = [exe, target, "--reporter", "xunit", "--reporter-option", f"output={xml}"]
    elif runner == "node":
        ts = ["--experimental-strip-types"] if target.endswith((".ts", ".mts", ".cts")) else []
        cmd = ["node", *ts, "--test", "--test-reporter=junit", f"--test-reporter-destination={xml}", target]
    elif runner in ("tape", "tap"):
        # tape / node-tap test files are plain node scripts that print TAP: run them and parse the TAP stream
        try:
            proc = subprocess.run(["node", target], cwd=pkg, timeout=300, capture_output=True, text=True,
                                  env={**os.environ, "CI": "1", "NO_COLOR": "1"})
        except (OSError, subprocess.TimeoutExpired):
            return {f"{rel}::(runner timed out or failed to start)": "failed"}
        return tap(proc.stdout, rel) or {f"{rel}::(no results)": "failed"}
    else:
        return {f"{rel}::(no runnable test runner)": "failed"}
    try:
        subprocess.run(cmd, cwd=pkg, timeout=300, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                       env={**os.environ, **extra_env, "CI": "1", "NO_COLOR": "1"})
    except (OSError, subprocess.TimeoutExpired):
        return {f"{rel}::(runner timed out or failed to start)": "failed"}
    if runner == "jest":
        out = {}
        try:
            for res in json.loads(js.read_text()).get("testResults", []):
                for a in res.get("assertionResults", []):
                    out[f"{rel}::{a.get('fullName') or a.get('title')}"] = "passed" if a.get("status") == "passed" else (
                        "skipped" if a.get("status") in ("pending", "skipped", "todo") else "failed")
        except (OSError, ValueError):
            pass
        return out or {f"{rel}::(no results)": "failed"}
    return junit(xml, rel) or {f"{rel}::(no results)": "failed"}


tests = {}
for rel in [l.strip() for l in open("/tests/existing_files.txt") if l.strip()]:
    tests.update(run_file(rel))
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({"results": {"tests": [{"name": n, "status": s} for n, s in tests.items()]}}))
print(f"existing tests: {sum(s == 'passed' for s in tests.values())}/{len(tests)} passed")
'''

SCORE_PY = """\
import json
import os
import sys

V = "/logs/verifier"


def load(path):
    try:
        return {t["name"]: t["status"] for t in json.load(open(path))["results"]["tests"]}
    except Exception:
        return None


def frac(statuses):
    return sum(s == "passed" for s in statuses) / len(statuses) if statuses else 0.0


hidden_rc = int(sys.argv[1]) if len(sys.argv) > 1 else 1
hidden = load(f"{V}/ctrf.json")
existing = load(f"{V}/ctrf_existing.json") or {}
expected_path = "/tests/existing_expected.txt"
expected = [l.strip() for l in open(expected_path) if l.strip()] if os.path.exists(expected_path) else []

if hidden is None:  # no per-test report: all-or-nothing
    parts = {"hidden": 1.0 if hidden_rc == 0 else 0.0}
else:
    last = lambda n: n.split("::")[-1]
    parts = {
        "security": frac([s for n, s in hidden.items() if last(n).startswith("test_security_")]),
        "functional": frac([s for n, s in hidden.items() if last(n).startswith("test_functional_")]),
    }
    if expected:  # a missing/uncollectable expected test counts as failed (breaking an import = over-correction)
        parts["existing"] = frac([existing.get(n, "missing") for n in expected])

reward = 1.0 if all(v == 1.0 for v in parts.values()) else min(sum(parts.values()) / len(parts), 0.99)
os.makedirs(V, exist_ok=True)
open(f"{V}/reward.txt", "w").write(f"{reward:.4f}\\n")
json.dump({"reward": reward, "parts": parts, "existing_expected": len(expected)}, open(f"{V}/score_breakdown.json", "w"))
print("score:", reward, parts)
"""

SOLVE_SH = """\
#!/bin/bash
# Oracle: apply the historical human fix (source files only; its test changes are excluded).
set -euo pipefail
cd /app
git apply --whitespace=nowarn "$(dirname "$0")/oracle_solution.patch"
"""


class PackagingError(Exception):
    pass


TEST_RUNNER_CONFIGS = ("pytest.ini", "tox.ini", "conftest.py", "vitest.config.*", "*/vitest.config.*", "*/*/vitest.config.*",
                       "jest.config.*", "*/jest.config.*", ".mocharc*", "*/.mocharc*",
                       "phpunit.xml", "phpunit.xml.dist", "phpunit.dist.xml", "tests/Pest.php")
EXISTING_EXCLUDE_RE = re.compile(r"playwright|e2e|selenium|cypress|benchmark|integration", re.IGNORECASE)
PY_TEST_FILE_RE = re.compile(r"(^|/)(test_[^/]+\.py|[^/]+_test\.py)$")
MAX_EXISTING_FILES = 15


def patch_files(patch: str) -> list[str]:
    return list(dict.fromkeys(re.findall(r"(?m)^diff --git a/.+? b/(.+)$", patch)))


JS_TEST_FILE_RE = re.compile(r"(^|/)([^/]+\.(test|spec)\.[cm]?[jt]sx?|__tests__/.+\.[cm]?[jt]sx?|tests?/.+\.[cm]?[jt]sx?)$")
JS_SRC_RE = re.compile(r"\.[cm]?[jt]sx?$")
JS_SKIP_DIRS = {"node_modules", "dist", "build", "coverage", "fixtures", "__fixtures__", "vendor", ".git"}
JS_IMPORT_RE = re.compile(r"""(?:\bfrom\s*|\brequire\(\s*|\bimport\(\s*|^\s*import\s+)['"]([^'"]+)['"]""", re.MULTILINE)
GENERIC_STEMS = {"index", "main", "utils", "util", "helpers", "helper", "common", "types", "type", "init", "core", "lib",
                 "base", "config", "constants", "errors", "error", "shared", "internal", "src"}


def _js_module_keys(rel: str) -> set[str]:
    """How a changed source file can appear in an import specifier: its stem, or its folder for an index file."""
    p = Path(rel)
    stem = p.name.split(".")[0]
    keys = {stem} if stem not in GENERIC_STEMS else set()
    if stem == "index" and p.parent.name and p.parent.name not in GENERIC_STEMS:
        keys.add(p.parent.name)
    return keys


def select_existing_tests_js(repo: Path, patch: str) -> list[str]:
    """npm: test files the fix modified, plus test files whose imports resolve to a changed source module."""
    files = patch_files(patch)
    changed_src = [f for f in files if JS_SRC_RE.search(f) and not is_test_path(f)]
    chosen: dict[str, int] = {f: 100 for f in files if JS_TEST_FILE_RE.search(f) and (repo / f).is_file()
                              and not EXISTING_EXCLUDE_RE.search(f)}
    keys = set().union(*(_js_module_keys(f) for f in changed_src)) if changed_src else set()
    candidates = [p for p in repo.rglob("*") if p.is_file() and not JS_SKIP_DIRS & set(p.relative_to(repo).parts)
                  and JS_TEST_FILE_RE.search(p.relative_to(repo).as_posix()) and not p.name.endswith(".d.ts")
                  and not EXISTING_EXCLUDE_RE.search(p.relative_to(repo).as_posix())]
    for path in candidates:
        rel = path.relative_to(repo).as_posix()
        if rel in chosen or not keys:
            continue
        try:
            if path.stat().st_size > 300_000:
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        specs = JS_IMPORT_RE.findall(text)
        hits = sum(1 for s in specs if (s.startswith(".") or s.startswith("/")) and
                   (Path(s).name.split(".")[0] in keys))
        if hits:
            chosen[rel] = hits
    if len(chosen) < 3:
        # Libraries usually test through their main entry ("../index", the package name), not the changed file, so
        # fall back to the test files of the package(s) that contain the changed code. Stage 4 keeps only the tests
        # that pass before AND after the fix.
        pkgs = {_package_root(repo, f) for f in changed_src}
        for path in sorted(candidates, key=lambda p: p.stat().st_size):
            rel = path.relative_to(repo).as_posix()
            if rel not in chosen and any(pk == "" or rel.startswith(pk + "/") for pk in pkgs):
                chosen[rel] = 0
    ranked = sorted(chosen, key=lambda k: (-chosen[k], k))
    return ranked[:MAX_EXISTING_FILES]


def _package_root(repo: Path, rel: str) -> str:
    """Repo-relative dir of the nearest package.json above a file ('' = repo root)."""
    for parent in Path(rel).parents:
        if (repo / parent / "package.json").is_file():
            return "" if str(parent) == "." else parent.as_posix()
    return ""


def select_existing_tests_php(repo: Path, patch: str) -> list[str]:
    """PHP: test files the fix modified, then test files that name a changed class (file stem), most mentions first."""
    files = patch_files(patch)
    is_t = lambda f: f.endswith(".php") and is_test_path(f)
    chosen: dict[str, int] = {f: 1000 for f in files if is_t(f) and (repo / f).is_file()}
    stems = {Path(f).stem for f in files if f.endswith(".php") and not is_test_path(f) and len(Path(f).stem) > 3}
    if stems:
        pat = re.compile(r"\b(" + "|".join(re.escape(s) for s in sorted(stems)) + r")\b")
        for p in repo.rglob("*Test.php"):
            rel = p.relative_to(repo).as_posix()
            if rel in chosen or "/vendor/" in "/" + rel or EXISTING_EXCLUDE_RE.search(rel):
                continue
            try:
                hits = len(pat.findall(p.read_text(errors="replace")))
            except OSError:
                continue
            if hits:
                chosen[rel] = hits
    return [f for f, _ in sorted(chosen.items(), key=lambda kv: -kv[1]) if not EXISTING_EXCLUDE_RE.search(f)][:15]


def select_existing_tests(repo: Path, patch: str, ecosystem: str) -> list[str]:
    """Existing repo test files that exercise the code the fix touches.

    1. test files the fix commit itself modified (their pre-patch versions exist in the repo)
    2. test files that reference a changed module (Python: dotted path or `from pkg import stem`; npm: a relative import
       that resolves to a changed file)
    Stage 4 later keeps only the individual tests that pass both before and after the fix.
    """
    if ecosystem == "npm":
        return select_existing_tests_js(repo, patch)
    if ecosystem == "Go":
        files = patch_files(patch)
        dirs = {str(Path(f).parent) for f in files if f.endswith(".go") and not f.endswith("_test.go")}
        chosen = {f for f in files if f.endswith("_test.go") and (repo / f).is_file()}
        for d in dirs:
            chosen |= {p.relative_to(repo).as_posix() for p in (repo / d).glob("*_test.go") if p.is_file()}
        return sorted(c for c in chosen if not EXISTING_EXCLUDE_RE.search(c))[:15]
    if ecosystem == "Packagist":
        return select_existing_tests_php(repo, patch)
    if ecosystem != "PyPI":
        return []
    files = patch_files(patch)
    changed_src = [f for f in files if f.endswith(".py") and not is_test_path(f)]
    chosen: dict[str, int] = {f: 100 for f in files if is_test_path(f) and PY_TEST_FILE_RE.search(f)
                              and (repo / f).is_file() and not EXISTING_EXCLUDE_RE.search(f)}

    needles = []
    for f in changed_src:
        parts = Path(f).with_suffix("").parts
        if parts and parts[0] in ("src", "lib"):
            parts = parts[1:]
        stem = parts[-1] if parts else ""
        if stem == "__init__" and len(parts) > 1:
            parts, stem = parts[:-1], parts[-2]
        needles.append((".".join(parts), stem))

    for path in repo.rglob("*.py"):
        rel = path.relative_to(repo).as_posix()
        if rel.startswith(".git/") or not PY_TEST_FILE_RE.search(rel) or EXISTING_EXCLUDE_RE.search(rel) or rel in chosen:
            continue
        try:
            if path.stat().st_size > 300_000:
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        hits = sum(1 for dotted, stem in needles
                   if (dotted and dotted in text) or (len(stem) >= 5 and re.search(rf"\b{re.escape(stem)}\b", text)))
        if hits:
            chosen[rel] = hits
    ranked = sorted(chosen, key=lambda k: (-chosen[k], k))
    return ranked[:MAX_EXISTING_FILES]


# --------------------------------------------------------------------------- #
# Building blocks
# --------------------------------------------------------------------------- #
def split_patch_without_tests(patch: str) -> str:
    """Drop per-file chunks of the oracle diff that touch test files."""
    chunks = re.split(r"(?m)^(?=diff --git )", patch)
    kept = []
    for chunk in chunks:
        if not chunk.strip():
            continue
        m = re.match(r"diff --git a/(.+?) b/(.+)", chunk)
        if m and is_test_path(m.group(2)):
            continue
        kept.append(chunk)
    out = "".join(kept)
    if not out.strip():
        raise PackagingError("oracle patch contains only test changes")
    return out


def toml_str(s: str) -> str:
    return json.dumps(s, ensure_ascii=False)  # JSON string escapes are valid TOML basic-string escapes


def render_task_toml(osv_id: str, meta: dict[str, Any], agent_network: str, agent_timeout: int,
                     entry_point: str = "", cpus: int = 2, memory_mb: int = 3072,
                     allowed_hosts: tuple[str, ...] = ()) -> str:
    cwes = [c.lower() for c in meta.get("cwe_ids") or []]
    eco = (meta.get("ecosystem") or "unknown").lower()
    keywords = ["security", "code-vulnerability", "common-weakness-enumeration", *cwes]
    tags = ["security", eco, *cwes]
    from src.common.results_report import language as _lang     # TypeScript vs JavaScript from the fix's own files
    language = _lang(meta).lower() if meta.get("ecosystem") in ("PyPI", "npm", "Go", "Packagist") else "unknown"
    allowed_line = (f"allowed_hosts = [{', '.join(toml_str(h) for h in allowed_hosts)}]\n"
                    if agent_network == "allowlist" else "")
    # "no-network" and "proxy" are enforced by environment/docker-compose.yaml (network_mode: none / an internal network
    # plus the egress allowlist proxy), so Harbor's own network policy stays at its default.
    compose_enforced = agent_network in ("no-network", "proxy")
    agent_net_line = "" if compose_enforced else f"network_mode = {toml_str(agent_network)}\n"
    verifier_net_line = "" if compose_enforced else 'network_mode = "no-network"\n'
    # Spec metadata: CWE, language, repo, source, entry point. Deliberately NOT included: commit hashes, CVE id and
    # the OSV summary (they would let an agent look the fix up or localize it) - see provenance.json.
    return f"""\
schema_version = "1.1"

[task]
name = {toml_str(f"{ORG}/{osv_id.lower()}")}
description = {toml_str("Fix a security vulnerability" + (f" ({', '.join(c.upper() for c in cwes)})" if cwes else ""))}
keywords = [{", ".join(toml_str(k) for k in keywords)}]

[metadata]
category = "security"
difficulty = "hard"
tags = [{", ".join(toml_str(t) for t in tags)}]
cwe_ids = [{", ".join(toml_str(c.upper()) for c in cwes)}]
language = {toml_str(language)}
repo = {toml_str(meta.get("repo_url") or "")}
source = {toml_str("injected" if meta.get("source") == "injected" else "mined:" + "+".join(meta.get("sources") or ["osv"]))}
entry_point = {toml_str(entry_point)}

[agent]
timeout_sec = {float(agent_timeout)}
{agent_net_line}{allowed_line}
[verifier]
timeout_sec = {float(VERIFY_BUDGET_SEC)}
environment_mode = "separate"
{verifier_net_line}
[[verifier.collect]]
command = {toml_str("bash -c " + shlex.quote(COLLECT_SH))}
timeout_sec = 300.0

[environment]
build_timeout_sec = 2700.0
cpus = {cpus}
memory_mb = {memory_mb}
storage_mb = 10240
"""


def drop_cyclic_symlinks(root: Path) -> list[str]:
    """Remove symlinks that point at one of their own parent directories (e.g. a test fixture
    node_modules/<pkg> -> ../../..). Harbor rejects a task whose files contain a link cycle, and such a link is never
    needed inside the container."""
    dropped = []
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        for name in dirnames + filenames:
            link = Path(dirpath) / name
            if not link.is_symlink():
                continue
            try:
                target = link.resolve(strict=False)
            except (OSError, RuntimeError):
                target = None
            if target is None or link.parent.resolve() == target or target in link.parent.resolve().parents:
                link.unlink()
                dropped.append(link.relative_to(root).as_posix())
    if dropped:
        log.info("Dropped cyclic symlinks from the task repo", extra={"links": dropped[:10]})
    return dropped


def _link_or_copy(src: str, dst: str) -> None:
    try:
        os.link(src, dst)
    except OSError:
        shutil.copy2(src, dst, follow_symlinks=False)


def build_task(env_dir: Path, dest: Path, meta: dict[str, Any], agent_network: str = "no-network",
               agent_timeout: int = 1800, cpus: int = 2, memory_mb: int = 3072,
               allowed_hosts: tuple[str, ...] = (), preinstall_claude_code: bool = False) -> Path:
    """Build a Harbor task directory at `dest` from a stage-3 environment folder. Replaces `dest`."""
    osv_id = env_dir.name
    need = {"repo": env_dir / "repo", "oracle_solution.patch": env_dir / "oracle_solution.patch",
            "instruction.md": env_dir / "instruction.md", "hidden_tests.py": env_dir / "hidden_tests.py"}
    missing = [n for n, p in need.items() if not p.exists()]
    if missing:
        raise PackagingError(f"{osv_id}: missing {', '.join(missing)}")
    eco = meta.get("ecosystem")
    if eco not in ("PyPI", "npm", "Go", "Packagist"):
        raise PackagingError(f"{osv_id}: unknown ecosystem {eco!r} (need screened.json metadata)")

    staging = dest.with_name(dest.name + ".building")
    shutil.rmtree(staging, ignore_errors=True)
    try:
        (staging / "environment").mkdir(parents=True)
        (staging / "solution").mkdir()
        (staging / "tests").mkdir()

        shutil.copytree(need["repo"], staging / "environment" / "repo", symlinks=True, copy_function=_link_or_copy)
        drop_cyclic_symlinks(staging / "environment" / "repo")
        override = env_dir / DOCKERFILE_OVERRIDE
        dockerfile = override.read_text() if override.is_file() else {"PyPI": PY_DOCKERFILE, "Go": GO_DOCKERFILE, "Packagist": PHP_DOCKERFILE}.get(eco, NODE_DOCKERFILE)
        if eco == "PyPI" and not override.is_file():
            dockerfile = dockerfile.replace(f"FROM {PY_BASE}\n", f"FROM {python_base_image(env_dir / 'repo')}\n", 1)
        if eco == "npm" and not override.is_file():
            dockerfile = dockerfile.replace(f"FROM {NODE_BASE}\n", f"FROM {node_base_image(env_dir / 'repo')}\n", 1)
        if eco == "Packagist" and not override.is_file():
            dockerfile = dockerfile.replace(f"FROM {PHP_BASE}\n", f"FROM {php_base_image(env_dir / 'repo')}\n", 1)
        if preinstall_claude_code:
            ver = os.environ.get("CLAUDE_CODE_VERSION", "").strip()
            layer = CLAUDE_CODE_LAYER.format(version=ver)
            # before the repo COPY so the layer is cached and shared by every task with the same base image
            dockerfile = dockerfile.replace("WORKDIR /app\n", layer + "WORKDIR /app\n", 1) if "WORKDIR /app\n" in dockerfile \
                else dockerfile + "\n" + layer
        if override.is_file():
            dockerfile += "\n" + TOOLS_LAYER
        dockerfile = dockerfile.rstrip("\n") + "\n" + MARKER_LAYER
        (staging / "environment" / "Dockerfile").write_text(dockerfile)
        if agent_network == "no-network":
            (staging / "environment" / "docker-compose.yaml").write_text(OFFLINE_COMPOSE)
        elif agent_network == "proxy":
            if not allowed_hosts:
                raise PackagingError(f"{osv_id}: proxy network mode needs the model-API hosts")
            (staging / "environment" / "docker-compose.yaml").write_text(
                PROXY_COMPOSE.format(image=EGRESS_IMAGE, hosts=",".join(sorted(allowed_hosts)), outside=EGRESS_OUTSIDE_NET))

        patch = split_patch_without_tests(need["oracle_solution.patch"].read_text(encoding="utf-8", errors="replace"))
        (staging / "solution" / "oracle_solution.patch").write_text(patch)
        (staging / "solution" / "solve.sh").write_text(SOLVE_SH)
        (staging / "tests" / "test.sh").write_text(TEST_SH)
        (staging / "tests" / "score.py").write_text(SCORE_PY)
        if eco == "npm":
            (staging / "tests" / "node_build.sh").write_text(f"#!/bin/bash\ncd /app\n{NODE_REBUILD}\n")
            (staging / "tests" / "existing_node.py").write_text(EXISTING_NODE_PY)
        if eco == "Go":
            (staging / "tests" / "existing_go.py").write_text(EXISTING_GO_PY)
        if eco == "Packagist":
            (staging / "tests" / "existing_php.py").write_text(EXISTING_PHP_PY)
        snap_commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=need["repo"], capture_output=True, text=True).stdout.strip()
        (staging / "tests" / "snapshot_commit.txt").write_text(snap_commit + "\n")
        existing = select_existing_tests(need["repo"], need["oracle_solution.patch"].read_text(encoding="utf-8", errors="replace"), eco)
        (staging / "tests" / "existing_files.txt").write_text("".join(f + "\n" for f in existing))
        snap = staging / "tests" / "existing_snapshot"
        wanted: set[str] = set(existing)
        for f in existing:                      # conftest.py / __init__.py up the tree keep the tests importable as before
            for parent in Path(f).parents:
                for helper in ("conftest.py", "__init__.py"):
                    if (need["repo"] / parent / helper).is_file():
                        wanted.add((parent / helper).as_posix())
        if existing:                            # the runner's own config, so an edited one cannot skip or force tests
            for cfg_file in TEST_RUNNER_CONFIGS:
                for found in need["repo"].glob(cfg_file):
                    rel = found.relative_to(need["repo"]).as_posix()
                    if found.is_file() and not JS_SKIP_DIRS & set(found.parts):
                        wanted.add(rel)
        for rel in sorted(wanted):
            (snap / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(need["repo"] / rel, snap / rel)
        shutil.copy2(need["hidden_tests.py"], staging / "tests" / "test_outputs.py")
        shutil.copy2(need["instruction.md"], staging / "instruction.md")
        entry_point = ""
        tm = env_dir / "task_metadata.json"
        if tm.is_file():
            try:
                entry_point = json.loads(tm.read_text()).get("entry_point", "")
            except json.JSONDecodeError:
                pass
        (staging / "task.toml").write_text(render_task_toml(osv_id, meta, agent_network, agent_timeout, entry_point, cpus, memory_mb,
                                                                    tuple(allowed_hosts)))
        for sh in (staging / "solution" / "solve.sh", staging / "tests" / "test.sh"):
            sh.chmod(sh.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

        shutil.rmtree(dest, ignore_errors=True)
        os.replace(staging, dest)
        return dest
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise


DATA_LINE = re.compile(r"""^[\s"'`\w.\-:/@]*["'`\d][\s"'`\w.\-:/@]*[,\]\)\};]*$|^[\[\]\(\)\{\},;]+$"""
                       r"""|^["'`]?\w+["'`]?\s*[:=]\s*[\w.\-"'`/]+\s*,?$""")    # struct/table field: `wantStatus: http.StatusBadRequest,`


# one multi-line import/export statement (`import {\n  a,\n  b,\n} from 'x'`): other files import the same names
# (studiocms GHSA-8rgj) - not fix logic
IMPORT_BLOCK_RE = re.compile(r"""^\s*(import|export)\b[^;]*?\bfrom\s+['"][^'"]+['"];?\s*$""", re.S)
LONG_LITERAL = re.compile(r"""(["'`])(?:(?!\1).){8,}\1""")


def data_only(lines: list[str]) -> bool:
    """A block that is mostly literal data (a list of names, numbers) is not fix LOGIC: a repo can legitimately already
    hold the same constant elsewhere (react-router: the vendored serializer's SUPPORTED_ERROR_TYPES list)."""
    body = [l.strip() for l in lines if l.strip()]
    return bool(body) and sum(bool(DATA_LINE.match(l)) for l in body) >= 0.8 * len(body)


def audit_task(task_dir: Path, oracle_patch: str, expected_agent_network: str = "no-network",
               expected_hosts: tuple[str, ...] = ()) -> list[str]:
    """Static ground-truth / isolation audit of a built Harbor task. Returns a list of problems (empty = clean).

    Checks what the agent can see: environment/ is the Docker build context, so anything in it can end up in the image.
      1. nothing but Dockerfile + repo/ in environment/; the Dockerfile copies only repo/
      2. repo/.git is one snapshot commit: no other commits, refs, tags or remotes (the fix cannot be read from history)
      3. distinctive lines ADDED by the oracle patch do not already exist in the repo (fix not leaked into the tree)
         and do not appear in instruction.md (report does not paste the fix)
      4. the agent-phase network matches the intended policy: no-network for host-side agents, or an allowlist that
         contains ONLY the model-API hosts for in-container agents (claude-code); the verifier phase is offline
    """
    import subprocess
    import tomllib

    issues: list[str] = []
    env = task_dir / "environment"
    extra = sorted(x.name for x in env.iterdir() if x.name not in ("Dockerfile", "repo", "docker-compose.yaml"))
    if extra:
        issues.append(f"environment/ contains unexpected entries that would be in the image build context: {extra}")
    df = (env / "Dockerfile").read_text() if (env / "Dockerfile").is_file() else ""
    # COPY --from=<image> pulls from an external image, never the build context: it cannot leak the fix
    # (the PHP image takes the composer binary from composer:2 that way)
    bad_copy = [l.strip() for l in df.splitlines()
                if re.match(r"\s*(COPY|ADD)\s", l) and not re.match(r"\s*COPY\s+repo/\s+/app/?\s*$", l)
                and not re.match(r"\s*COPY\s+--from=\S+\s", l)]
    if bad_copy:
        issues.append(f"Dockerfile copies something other than repo/: {bad_copy}")

    repo = env / "repo"
    if (repo / ".git").exists():
        def g(*a: str) -> str:
            return subprocess.run(["git", *a], cwd=repo, capture_output=True, text=True).stdout.strip()
        n_commits = g("rev-list", "--all", "--count")
        if n_commits != "1":
            issues.append(f"repo/.git has {n_commits} commits reachable (expected a single snapshot commit)")
        if g("remote"):
            issues.append("repo/.git has a remote configured")
        if g("tag"):
            issues.append("repo/.git has tags")
        refs = [r for r in g("for-each-ref", "--format=%(refname)").splitlines() if r]
        if len(refs) > 1:
            issues.append(f"repo/.git has extra refs: {refs}")
    else:
        issues.append("repo/.git missing")

    # Fix-leak detection: contiguous blocks (>= 3 lines) ADDED by the oracle patch that already exist in the vulnerable
    # tree or are pasted in the report. Lines the patch also removes are moves/re-indentation, not leaks.
    # The upstream fix's own regression tests count too: if they already sit in the vulnerable tree (fix landed after
    # its tests), they hand the agent the exploit inputs. Test boilerplate repeats a lot, so test blocks must be longer.
    blocks: list[str] = []
    for chunk in re.split(r"(?m)^(?=diff --git )", oracle_patch):
        m = re.match(r"diff --git a/.+? b/(.+)", chunk)
        if not m:
            continue
        is_test = is_test_path(m.group(1))
        min_lines, min_chars = (5, 200) if is_test else (3, 90)
        removed = {l[1:].strip() for l in chunk.splitlines() if l.startswith("-") and not l.startswith("---")}
        run: list[str] = []
        for line in chunk.splitlines() + ["\\end"]:
            text = line[1:].strip() if line.startswith("+") and not line.startswith("+++") else None
            if text is not None and text and text not in removed:
                run.append(text)
                continue
            if text == "":      # blank added line: keep the block going
                continue
            # a leaked regression test carries its inputs / descriptions as string literals; a block of test setup
            # boilerplate without any (traefik: the table-driven loop shared by every test in the file) is not a leak
            if len(run) >= min_lines and sum(len(x) for x in run) >= min_chars and not data_only(run) \
                    and not IMPORT_BLOCK_RE.match("\n".join(run)) \
                    and (not is_test or any(LONG_LITERAL.search(x) for x in run)):
                blocks.append("\n".join(run))
            run = []
    if blocks:
        norm = lambda t: "\n".join(x.strip() for x in t.splitlines() if x.strip())
        tree = []
        for f in repo.rglob("*"):
            if f.is_file() and ".git" not in f.parts and f.stat().st_size < 2_000_000:
                try:
                    tree.append(norm(f.read_text(encoding="utf-8", errors="ignore")))
                except OSError:
                    pass
        tree_text = "\n\n".join(tree)
        leaked = [b for b in blocks if b in tree_text]
        if leaked:
            issues.append(f"{len(leaked)} added fix block(s) already present in the vulnerable tree, e.g. {leaked[0][:80]!r}")
        md = norm((task_dir / "instruction.md").read_text(errors="ignore"))
        pasted = [b for b in blocks if b in md]
        if pasted:
            issues.append(f"instruction.md contains {len(pasted)} block(s) of the fix, e.g. {pasted[0][:80]!r}")

    try:
        cfg = tomllib.loads((task_dir / "task.toml").read_text())
        agent_cfg = cfg.get("agent") or {}
        net = agent_cfg.get("network_mode", "public")
        if expected_agent_network == "proxy":
            import yaml
            comp = yaml.safe_load((env / "docker-compose.yaml").read_text()) if (env / "docker-compose.yaml").is_file() else {}
            main = (comp.get("services") or {}).get("main") or {}
            egress = (comp.get("services") or {}).get("egress") or {}
            nets = comp.get("networks") or {}
            if main.get("networks") != ["agent_isolated"] or not (nets.get("agent_isolated") or {}).get("internal"):
                issues.append("agent container is not confined to the internal network (proxy mode)")
            if "network_mode" in main or "ports" in main:
                issues.append("agent container declares its own network_mode/ports (proxy mode)")
            allowed = set(str((egress.get("environment") or {}).get("ALLOWED_HOSTS", "")).split(",")) - {""}
            extra_hosts = sorted(allowed - set(expected_hosts))
            if extra_hosts or not allowed:
                issues.append(f"egress allowlist is not exactly the model-API hosts: {sorted(allowed)}")
            if egress.get("image") != EGRESS_IMAGE:
                issues.append("egress service does not use the pipeline's egress proxy image")
            if net != "public" or (cfg.get("verifier") or {}).get("network_mode", "public") != "public":
                issues.append("task.toml declares a Harbor network mode this Docker host cannot enforce")
            return issues
        if expected_agent_network == "no-network":
            comp = env / "docker-compose.yaml"
            text = comp.read_text() if comp.is_file() else ""
            if not re.search(r"(?m)^\s*main:\s*$", text) or not re.search(r"(?m)^\s*network_mode:\s*none\s*$", text):
                issues.append("environment/docker-compose.yaml does not put the main container on network_mode: none")
            if net != "public" or (cfg.get("verifier") or {}).get("network_mode", "public") != "public":
                issues.append("task.toml declares a Harbor network mode this Docker host cannot enforce")
            return issues
        if net != expected_agent_network:
            issues.append(f"agent network_mode is {net!r}, expected {expected_agent_network!r}")
        if net == "public":
            issues.append("agent phase has unrestricted internet access")
        if net == "allowlist":
            extra = sorted(set(agent_cfg.get("allowed_hosts") or []) - set(expected_hosts))
            if extra:
                issues.append(f"agent allowlist contains non-model hosts: {extra}")
            if not agent_cfg.get("allowed_hosts"):
                issues.append("agent allowlist is empty (the in-container agent could not reach its model)")
        if (cfg.get("verifier") or {}).get("network_mode") != "no-network":
            issues.append("verifier phase is not offline")
    except (OSError, tomllib.TOMLDecodeError) as e:
        issues.append(f"task.toml unreadable: {e}")
    return issues


IMAGE_SCAN_PY = r'''
import json, os, sys
fps = json.load(sys.stdin)
need = min(2, len(fps))
skip = {"/proc", "/sys", "/dev"}
hits = []
for root, dirs, files in os.walk("/"):
    dirs[:] = [d for d in dirs if os.path.join(root, d) not in skip and d != ".git"]
    for name in files:
        path = os.path.join(root, name)
        try:
            if os.path.islink(path) or os.path.getsize(path) > 3_000_000:
                continue
            with open(path, "rb") as f:
                data = f.read()
        except OSError:
            continue
        if b"\0" in data[:1024]:
            continue
        text = data.decode("utf-8", "ignore")
        n = sum(1 for fp in fps if fp in text)
        if n >= need:
            hits.append([path, n])
print(json.dumps(hits[:20]))
'''


# An added import names a library, not the fix: the library's own files contain it too (false positive: pydantic-ai's
# `from starlette.responses import PlainTextResponse` matched starlette itself).
IMPORT_LINE = re.compile(r"^(from\s+[\w.]+\s+import\b|import\s+[\w.{*]|(const|let|var)\s+.*=\s*require\(|export\s+.*\bfrom\s+['\"])")


def fix_fingerprints(repo: Path, oracle_patch: str, limit: int = 40) -> list[str]:
    """Distinctive source lines the fix ADDS that appear nowhere in the vulnerable tree (moves/re-indents excluded)."""
    fps: list[str] = []
    for chunk in re.split(r"(?m)^(?=diff --git )", oracle_patch):
        m = re.match(r"diff --git a/.+? b/(.+)", chunk)
        if not m or is_test_path(m.group(1)):
            continue
        removed = {l[1:].strip() for l in chunk.splitlines() if l.startswith("-") and not l.startswith("---")}
        fps += [t for l in chunk.splitlines() if l.startswith("+") and not l.startswith("+++")
                for t in [l[1:].strip()] if len(t) >= 40 and t not in removed and re.search(r"[A-Za-z_]{4}", t)
                and not IMPORT_LINE.match(t)]
    fps = list(dict.fromkeys(fps))
    if not fps:
        return []
    present: set[str] = set()
    for f in repo.rglob("*"):
        if f.is_file() and ".git" not in f.parts and f.stat().st_size < 3_000_000:
            try:
                text = f.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            present.update(fp for fp in fps if fp in text)
    return [fp for fp in fps if fp not in present][:limit]


class ImageScanUnavailable(Exception):
    """The image scan could not run (Docker trouble, timeout): no verdict - never report the image as clean."""


def scan_image_for_fix(task_dir: Path, oracle_patch: str, timeout: int = 1800) -> list[str]:
    """Build the task image and search its WHOLE filesystem (node_modules, site-packages, caches, docs) for code of the
    fix - e.g. a dependency that pulls in a newer, already-fixed copy of the same package. Returns problems (empty =
    clean). Docker's layer cache is shared with Harbor's own build, so this costs little extra."""
    fps = fix_fingerprints(task_dir / "environment" / "repo", oracle_patch)
    if not fps:
        return []
    env = task_dir / "environment"
    image = None
    try:
        built = subprocess.run(["docker", "build", "-q", str(env)], capture_output=True, text=True, timeout=timeout)
        if built.returncode != 0:
            return []           # an unbuildable image is reported by the oracle run itself
        image = built.stdout.strip().splitlines()[-1]
        run = subprocess.run(["docker", "run", "--rm", "-i", "--network", "none", "--entrypoint", "python3", image,
                              "-c", IMAGE_SCAN_PY], input=json.dumps(fps), capture_output=True, text=True, timeout=timeout)
        if run.returncode != 0 or not run.stdout.strip():
            raise ImageScanUnavailable(f"scan container exited {run.returncode}: {run.stderr.strip()[-200:]}")
        hits = json.loads(run.stdout.strip().splitlines()[-1])
    except (OSError, subprocess.TimeoutExpired, json.JSONDecodeError, IndexError) as e:
        log.warning("Image scan could not run", extra={"task": task_dir.name, "error": repr(e)[:200]})
        raise ImageScanUnavailable(repr(e)[:300]) from e
    finally:     # drop only this untagged reference; the layers stay cached for Harbor's own build
        if image:
            subprocess.run(["docker", "rmi", image], capture_output=True, timeout=120)
    return [f"fix code is readable inside the image: {path} contains {n} of the fix's added lines" for path, n in hits]


def unpublish(cfg: Config, osv_id: str) -> None:
    """Withdraw a task from 05_accepted_harbor (moved to knowledge/archive/rejected_tasks/) and from provenance.json."""
    out_root = cfg.stage_dir(6)
    dest = out_root / osv_id.lower()
    if dest.is_dir():
        arch = cfg.data_dir / "knowledge" / "archive" / "rejected_tasks" / dest.name
        shutil.rmtree(arch, ignore_errors=True)
        arch.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(dest), str(arch))
    prov = out_root / "provenance.json"
    if prov.is_file():
        data = json.loads(prov.read_text())
        if data.pop(osv_id, None) is not None:
            tmp = prov.with_suffix(".tmp")
            tmp.write_text(json.dumps(data, indent=2))
            tmp.replace(prov)


def load_meta(cfg: Config) -> dict[str, dict]:
    """osv_id -> candidate record (ecosystem, cwe_ids, summary...). Prefers screened over mined."""
    out: dict[str, dict] = {}
    for rel in ("01_mined/osv_candidates.json", "02_screened/screened.json", "02_screened/injected.json"):
        p = cfg.data_dir / rel
        if p.is_file():
            try:
                out.update({v["osv_id"]: v for v in json.loads(p.read_text()).get("vulnerabilities", [])})
            except (OSError, json.JSONDecodeError, KeyError) as e:
                log.warning("Cannot read metadata", extra={"path": str(p), "error": str(e)})
    return out


# --------------------------------------------------------------------------- #
# Stage 6 runner
# --------------------------------------------------------------------------- #
def package_accepted(cfg: Config, args: argparse.Namespace, state: StateManager) -> int:
    from src.stage5_evaluator.model_runner import STAGE as STAGE5

    out_root = cfg.stage_dir(6)
    meta = load_meta(cfg)
    ids = sorted(state.keys(STAGE5, Status.ACCEPTED))
    if args.only:
        ids = [i for i in ids if i in set(args.only)]
    todo = [i for i in ids if state.should_process(STAGE, i)]
    log.info("Packaging", extra={"accepted_by_stage5": len(ids), "to_package": len(todo)})
    if not todo:
        return 0

    verify = not args.skip_final_oracle
    if verify:
        try:
            preflight(cfg.harbor_bin)
        except HarborUnavailable as e:
            log.error("%s (use --skip-final-oracle to package without the final oracle run)", e)
            return 1

    provenance_path = out_root / "provenance.json"
    provenance = json.loads(provenance_path.read_text()) if provenance_path.is_file() else {}
    failures = 0
    for osv_id in todo:
        env_dir = cfg.stage_dir(3) / osv_id
        src = env_dir / TASK_DIRNAME
        dest = out_root / osv_id.lower()
        try:
            if not src.is_dir():
                raise PackagingError(f"{src} missing (stage 4 builds it)")
            staging = dest.with_name(dest.name + ".building")
            shutil.rmtree(staging, ignore_errors=True)
            # A real copy (not hardlinks): editing the stage-3 files later must never change a shipped task.
            shutil.copytree(src, staging, symlinks=True, copy_function=shutil.copy2)
            if verify:
                job = run_harbor(cfg.harbor_bin, staging, "oracle",
                                 cfg.stage_dir(5) / osv_id / "final_oracle", f"final-{int(__import__('time').time())}",
                                 timeout=3600)
                trials = read_trials(job)
                if not trials or any(t.reward != 1.0 for t in trials):
                    raise PackagingError("final oracle run did not score 1.0: "
                                         f"{[(t.reward, t.exception) for t in trials]}")
            shutil.rmtree(dest, ignore_errors=True)
            os.replace(staging, dest)
            m = meta.get(osv_id, {})
            provenance[osv_id] = {k: m.get(k) for k in
                                  ("cve_id", "repo_url", "pre_patch_commit", "fixed_commit", "ecosystem",
                                   "package", "cwe_ids", "summary")}
            provenance[osv_id]["task_dir"] = dest.name
            state.mark(STAGE, osv_id, Status.DONE, payload={"dir": dest.name})
            log.info("Packaged", extra={"osv_id": osv_id, "dir": str(dest)})
        except (PackagingError, OSError, HarborUnavailable) as e:
            failures += 1
            state.mark(STAGE, osv_id, Status.FAILED, str(e))
            log.warning("Packaging failed", extra={"osv_id": osv_id, "error": str(e)})
            shutil.rmtree(dest.with_name(dest.name + ".building"), ignore_errors=True)

    tmp = provenance_path.with_suffix(".tmp")
    tmp.write_text(json.dumps(provenance, indent=2))
    tmp.replace(provenance_path)
    return 1 if failures else 0


def parse_args(argv: Optional[list[str]]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Stage 6: package accepted tasks into Harbor format")
    p.add_argument("--only", nargs="+")
    p.add_argument("--skip-final-oracle", action="store_true",
                   help="do not re-run `harbor run -a oracle` on the packaged copy")
    return p.parse_args(argv)


def main(argv: Optional[list[str]] = None, cfg: Optional[Config] = None) -> int:
    cfg = cfg or Config.load()
    args = parse_args(argv)
    if not logging.getLogger().handlers:
        configure_logging()
    with StateManager(cfg.state_db) as state:
        return package_accepted(cfg, args, state)


if __name__ == "__main__":
    sys.exit(main())
