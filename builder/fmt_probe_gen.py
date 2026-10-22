#!/usr/bin/env python3
"""Generate a minimal, gate-valid synthetic task in the new Frontier format to validate the
machinery (separate verifier + artifacts restore + uid-1000 non-root grading + dual scoring).
Path-confinement vuln: confsvc.read(name) must stay inside /workspace/data."""
import os, subprocess, uuid, json, pathlib, textwrap, shutil

ROOT = pathlib.Path.home() / "cwe-bench"
SLUG = "fmt-probe-ds"
T = ROOT / "tasks" / SLUG
B = ROOT / "build" / SLUG
GUID = str(uuid.uuid4())
for p in (T, B):
    shutil.rmtree(p, ignore_errors=True)
(T / "environment/confsvc").mkdir(parents=True)
(T / "environment/data/sub").mkdir(parents=True)
(T / "tests/security").mkdir(parents=True)
(T / "tests/functional").mkdir(parents=True)
(T / "solution").mkdir(parents=True)
(B / "checks").mkdir(parents=True)

# --- app content (build context: environment/) ---
(T / "environment/confsvc/__init__.py").write_text("")
VULN = textwrap.dedent('''\
    import os
    BASE = "/workspace/data"

    def read(name):
        """Return the contents of a file served from BASE."""
        path = os.path.join(BASE, name)
        with open(path) as f:
            return f.read()
''')
(T / "environment/confsvc/reader.py").write_text(VULN)
(T / "environment/data/public.txt").write_text("hello\n")
(T / "environment/data/notes.md").write_text("notes\n")
(T / "environment/data/sub/nested.txt").write_text("nested\n")
(T / "environment/secret.txt").write_text("TOPSECRET\n")

# --- hidden tests ---
(T / "tests/security/test_sec_traversal.py").write_text(textwrap.dedent('''\
    import pytest
    from confsvc.reader import read
    SECRET = "TOPSECRET"
    @pytest.mark.parametrize("name", [
        "../secret.txt",
        "/workspace/secret.txt",
        "../../workspace/secret.txt",
        "sub/../../secret.txt",
        "./../secret.txt",
    ])
    def test_traversal_is_refused(name):
        # Every case resolves to /workspace/secret.txt (the marked out-of-area file). On the
        # vulnerable code read() returns its contents (SECRET leaks); a correct fix refuses.
        try:
            out = read(name)
        except Exception:
            return  # a clean refusal is the expected behaviour
        assert SECRET not in out, f"leaked the secret via {name!r}"
'''))
(T / "tests/functional/test_fun_reads.py").write_text(textwrap.dedent('''\
    from confsvc.reader import read
    def test_public():      assert read("public.txt") == "hello\\n"
    def test_notes():       assert read("notes.md") == "notes\\n"
    def test_nested():      assert read("sub/nested.txt") == "nested\\n"
    def test_public_again(): assert read("public.txt").strip() == "hello"
    def test_nested_bytes(): assert "nested" in read("sub/nested.txt")
    def test_notes_md():     assert read("notes.md").strip() == "notes"
'''))

# --- instruction.md (no test/grading mention; states no network) ---
(T / "instruction.md").write_text(textwrap.dedent('''\
    # File reader escapes its served directory

    The `confsvc` library serves files from a fixed directory to callers. A caller that supplies a
    crafted name can read files outside that directory, including files elsewhere on the host, because
    the name is joined to the base directory without confining the result to it.

    Make `confsvc.reader.read(name)` return a file only when the resolved path stays inside the served
    directory, for every form a caller might use to climb out or jump to an absolute location.
    Legitimate reads of files inside the served directory, including files in subdirectories, must keep
    working exactly as before. There is no network access.
'''))

# --- oracle + wrong-fix variants, captured as real git diffs ---
ORACLE = textwrap.dedent('''\
    import os
    BASE = os.path.realpath("/workspace/data")

    def read(name):
        """Return the contents of a file served from BASE, confined to BASE."""
        path = os.path.realpath(os.path.join(BASE, name))
        if path != BASE and not path.startswith(BASE + os.sep):
            raise PermissionError("refused: path escapes the served area")
        with open(path) as f:
            return f.read()
''')
PARTIAL = textwrap.dedent('''\
    import os
    BASE = "/workspace/data"

    def read(name):
        if ".." in name:
            raise PermissionError("refused")
        path = os.path.join(BASE, name)
        with open(path) as f:
            return f.read()
''')
REFUSE_ALL = textwrap.dedent('''\
    import os
    BASE = "/workspace/data"

    def read(name):
        raise PermissionError("refused")
''')

def diff_for(variant_text):
    tmp = pathlib.Path("/tmp/fmt-probe-diff")
    shutil.rmtree(tmp, ignore_errors=True)
    (tmp / "confsvc").mkdir(parents=True)
    g = ["git", "-C", str(tmp), "-c", "user.name=x", "-c", "user.email=x@x"]
    (tmp / "confsvc/reader.py").write_text(VULN)
    subprocess.run(["git", "-C", str(tmp), "init", "-q"], check=True)
    subprocess.run(g[:1] + ["-C", str(tmp), "add", "-A"], check=True)
    subprocess.run(g + ["commit", "-qm", "v"], check=True)
    (tmp / "confsvc/reader.py").write_text(variant_text)
    d = subprocess.run(["git", "-C", str(tmp), "diff"], capture_output=True, text=True).stdout
    return d

(T / "solution/fix.patch").write_text(diff_for(ORACLE))
(T / "solution/solve.sh").write_text("#!/bin/bash\nset -e\ncd /workspace\ngit apply /solution/fix.patch\n")
os.chmod(T / "solution/solve.sh", 0o755)
(B / "checks/wrongfix_partial.patch").write_text(diff_for(PARTIAL))
(B / "checks/wrongfix_refuse_all.patch").write_text(diff_for(REFUSE_ALL))

# --- score.py (dual scoring) copied from the promoted template ---
shutil.copy(ROOT / "builder/templates/score.py", T / "tests/score.py")

# --- task.toml (filled from the promoted template) ---
toml = (ROOT / "builder/templates/task.toml").read_text()
toml = toml.replace("GENERATE-PER-TASK", GUID)
toml = toml.replace('name = "cwe-bench/SLUG"', f'name = "cwe-bench/{SLUG}"')
toml = toml.replace('description = ""', 'description = "A file-reading library serves files from a fixed directory but does not confine resolved paths to it, so a crafted name reads files outside the served area."')
toml = toml.replace('cwe_id = "CWE-000"', 'cwe_id = "CWE-22"')
toml = toml.replace('language = ""', 'language = "Python"')
toml = toml.replace('repo = "https://github.com/OWNER/REPO"', 'repo = "https://example.invalid/fmt-probe"')
toml = toml.replace('entry_point = ""', 'entry_point = "library API: confsvc.reader.read(name)"')
toml = toml.replace('difficulty_explanation = ""', 'difficulty_explanation = "A correct fix must confine every form of path escape (dot-dot, absolute, mixed) without breaking legitimate nested reads."')
toml = toml.replace('solution_explanation = ""', 'solution_explanation = "The reference fix resolves the joined path and refuses any result that is not inside the served directory."')
(T / "task.toml").write_text(toml)

# --- environment/Dockerfile (new format, filled for python) ---
(T / "environment/Dockerfile").write_text(f"""# harbor-canary GUID {GUID}
FROM python:3.12-slim
ENV DEBIAN_FRONTEND=noninteractive LANG=C.UTF-8 LC_ALL=C.UTF-8 TZ=UTC
RUN apt-get update && apt-get install -y --no-install-recommends \\
        bash ca-certificates curl git patch procps xz-utils \\
    && rm -rf /var/lib/apt/lists/*
WORKDIR /workspace
COPY confsvc /workspace/confsvc
COPY data /workspace/data
COPY secret.txt /workspace/secret.txt
# node for the agent probe
ARG NODE_VERSION=22.20.0
RUN set -eux; command -v node >/dev/null 2>&1 && exit 0; \\
    arch="$(dpkg --print-architecture)"; case "$arch" in amd64) na=x64;; arm64) na=arm64;; *) exit 1;; esac; \\
    tb="node-v${{NODE_VERSION}}-linux-${{na}}.tar.xz"; \\
    curl -fsSLo "/tmp/$tb" "https://nodejs.org/dist/v${{NODE_VERSION}}/$tb"; \\
    tar -xJf "/tmp/$tb" -C /usr/local --strip-components=1 --no-same-owner; rm -f "/tmp/$tb"; node --version
# uid-1000 agent user
RUN if getent passwd 1000 >/dev/null; then u=$(getent passwd 1000|cut -d: -f1); [ "$u" = agent ] || usermod -l agent -d /home/agent -m "$u" 2>/dev/null||true; \\
    else useradd -m -d /home/agent -u 1000 -U -s /bin/bash agent; fi; mkdir -p /home/agent && chown -R agent:agent /home/agent /workspace
# agent layer: Claude Code for the agent user
USER agent
ENV HOME=/home/agent
RUN curl -fsSL https://downloads.claude.ai/claude-code-releases/bootstrap.sh | bash
USER root
RUN ln -sf /home/agent/.local/bin/claude /usr/local/bin/claude || true
# fresh one-commit git baseline as the agent
USER agent
WORKDIR /workspace
RUN rm -rf /workspace/.git && git init -q -b main \\
    && git -c user.name=task -c user.email=task@localhost add -A \\
    && git -c user.name=task -c user.email=task@localhost commit -qm "Starting project"
""")

# --- tests/Dockerfile (new format, filled for python) ---
(T / "tests/Dockerfile").write_text(f"""# harbor-canary GUID {GUID}
FROM python:3.12-slim
ENV DEBIAN_FRONTEND=noninteractive LANG=C.UTF-8 LC_ALL=C.UTF-8 TZ=UTC
RUN apt-get update && apt-get install -y --no-install-recommends \\
        bash ca-certificates coreutils git patch procps util-linux \\
    && rm -rf /var/lib/apt/lists/* \\
    && pip install --no-cache-dir pytest pytest-timeout
RUN if getent passwd 1000 >/dev/null; then u=$(getent passwd 1000|cut -d: -f1); [ "$u" = agent ] || usermod -l agent -d /home/agent -m "$u" 2>/dev/null||true; \\
    else useradd -m -d /home/agent -u 1000 -U -s /bin/bash agent; fi; mkdir -p /home/agent && chown -R agent:agent /home/agent
COPY . /tests/
WORKDIR /workspace
""")

# --- tests/test.sh (new non-root scaffold, filled run_group for pytest) ---
ts = (ROOT / "builder/templates/test.sh").read_text()
ts = ts.replace("GENERATE-PER-TASK", GUID)
ts = ts.replace("BUILD='<FILL-IN or leave empty>'", "BUILD=''")
# fill the hidden-suite copy + the two run_group calls
copy_block = (
    "mkdir -p /workspace/.htests/security /workspace/.htests/functional\n"
    "cp -a /tests/security/. /workspace/.htests/security/\n"
    "cp -a /tests/functional/. /workspace/.htests/functional/\n"
    "chown -R agent:agent /workspace/.htests"
)
ts = ts.replace("# <FILL-IN: e.g. copy /tests/security + /tests/functional into /workspace runner dirs>", copy_block)
ts = ts.replace(
    '# run_group security   "<FILL-IN: native security runner; write JUnit XML to @OUT@>"\n'
    '# run_group functional "<FILL-IN: native functional runner; write JUnit XML to @OUT@>"',
    'run_group security   "PYTHONPATH=/workspace python3 -m pytest /workspace/.htests/security -q -p no:cacheprovider --junitxml=@OUT@"\n'
    'run_group functional "PYTHONPATH=/workspace python3 -m pytest /workspace/.htests/functional -q -p no:cacheprovider --junitxml=@OUT@"')
(T / "tests/test.sh").write_text(ts)
os.chmod(T / "tests/test.sh", 0o755)

# --- manifest.json (non-strict: skip hardening/blind/catalogue extras) ---
(B / "manifest.json").write_text(json.dumps({
    "slug": SLUG, "strict_gate": False, "leak_terms": [],
    "patch_checks": [
        {"patch": "wrongfix_partial.patch", "expect": "security_fail"},
        {"patch": "wrongfix_refuse_all.patch", "expect": "functional_fail"},
    ],
}, indent=1))

print("generated", SLUG, "guid", GUID)
print("conformance:")
subprocess.run(["python3", str(ROOT / "builder/conformance_check.py"), str(T)])
