# Python 3.12: within the project's supported range (>=3.11). The flaw is not
# Python-version dependent.
FROM python:3.12-slim

# Tools the task and verifier need. No network is available after build.
RUN apt-get update && apt-get install -y --no-install-recommends \
        bash ca-certificates curl git patch \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Fetch the repository at the pinned (vulnerable) commit.
ARG REPO_URL=https://github.com/nousresearch/hermes-agent
ARG COMMIT=b6ce7a451f72a185ceafc4a3d13a599ee00a62d5
RUN git init -q . \
    && git fetch -q --depth 1 "${REPO_URL}.git" "${COMMIT}" \
    && git checkout -q FETCH_HEAD

# Apply the task's additions, then drop the git history so no later (fixed)
# commit, tag or branch is present in the image.
COPY injection.patch /tmp/injection.patch
RUN patch -p1 < /tmp/injection.patch \
    && rm -f /tmp/injection.patch \
    && rm -rf /app/.git

# Install the project's runtime dependencies and the test toolchain while the
# network is still available. The package itself is editable so a fix in /app
# takes effect without reinstalling.
RUN pip install --no-cache-dir \
        openai==2.24.0 python-dotenv==1.2.2 fire==0.7.1 "httpx[socks]==0.28.1" \
        rich==14.3.3 tenacity==9.1.4 pyyaml==6.0.3 "ruamel.yaml==0.18.17" \
        requests==2.33.0 jinja2==3.1.6 pydantic==2.13.4 prompt_toolkit==3.0.52 \
        croniter==6.0.0 "PyJWT[crypto]==2.12.1" psutil==7.2.2 \
        pytest==9.0.2 pytest-asyncio==1.3.0 pytest-timeout==2.4.0 \
    && pip install --no-cache-dir --no-deps -e .

# Smoke-import the modules the hidden tests drive.
RUN python -c "import agent.prompt_builder, agent.tool_dispatch_helpers, tools.memory_tool, agent.memory_manager, agent.subdirectory_hints, agent.transports.codex_event_projector"

# Warm the project's test collection once (offline afterwards).
RUN cd /app \
    && python -m pytest -q -p no:cacheprovider \
        tests/tools/test_memory_tool.py \
        tests/tools/test_memory_tool_schema.py \
        tests/agent/test_prompt_builder.py \
        tests/agent/test_subdirectory_hints.py \
        tests/agent/transports/test_codex_event_projector.py >/dev/null 2>&1; \
    find /app -name __pycache__ -type d -prune -exec rm -rf {} + ; true

# Defensive guard: drop any text file naming the advisory. The checkout
# predates the fix, so this normally finds nothing.
RUN find /app -type f \( -name '*.md' -o -name '*.txt' -o -name '*.rst' \) -print0 \
      | xargs -0 -r grep -ilE 'GHSA-33QV-C5QM-799V|CVE-2026-10223|PYSEC-2026-3575' 2>/dev/null \
      | xargs -r rm -f || true

# --- agent layer: append to a task's environment/Dockerfile -----------------
# Pre-installs Claude Code so Harbor skips its own install step at trial start
# (that step otherwise apt-installs Node.js on every trial, which is slow and
# fails on network hiccups). Needs curl, bash and ca-certificates in the image.
RUN curl -fsSL https://downloads.claude.ai/claude-code-releases/bootstrap.sh | bash \
    && ln -sf /root/.local/bin/claude /usr/local/bin/claude \
    && claude --version
# -----------------------------------------------------------------------------
