# Python 3.12: a version the project's own toolchain supports. The flaw is not
# Python-version dependent.
FROM python:3.12-slim

# Tools the task and verifier need. No network is available after build.
# ripgrep is the content-search backend the project uses when present.
RUN apt-get update && apt-get install -y --no-install-recommends \
        bash ca-certificates curl git patch ripgrep \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Fetch the monorepo at the pinned (vulnerable) commit.
ARG REPO_URL=https://github.com/langchain-ai/langchain
ARG COMMIT=0392b6bae4bdfc0b7ed5aeb2e9e414bbb7ea643b
RUN git init -q . \
    && git fetch -q --depth 1 "${REPO_URL}.git" "${COMMIT}" \
    && git checkout -q FETCH_HEAD

# Inject the same-class, model-supplied path-handling siblings into other
# command handlers of the file-tool middleware, then drop the git history so no
# later (fixed) commit, tag or branch is present in the image.
COPY injection.patch /tmp/injection.patch
RUN patch -p1 < /tmp/injection.patch \
    && rm -f /tmp/injection.patch \
    && rm -rf /app/.git

# Install the runtime packages (editable, so a fix to /app takes effect) plus
# the project's test toolchain, while the network is still available.
RUN pip install --no-cache-dir -e libs/core \
    && pip install --no-cache-dir -e libs/langchain_v1 \
    && pip install --no-cache-dir -e libs/partners/anthropic \
    && pip install --no-cache-dir -e libs/standard-tests \
    && pip install --no-cache-dir \
        "pytest>=8,<9" "pytest-asyncio>=0.23" "pytest-mock>=3" \
        "blockbuster>=1.5" "pytest-socket>=0.7" "syrupy>=4" \
    && python -c "import langchain.agents.middleware.file_search; import langchain_anthropic.middleware.anthropic_tools"

# Defensive guard: drop any text file naming the advisory. The checkout predates
# the fix, so this finds nothing today.
RUN find /app -type f \( -name '*.md' -o -name '*.txt' -o -name '*.rst' \) -print0 \
      | xargs -0 -r grep -ilE 'GHSA-GR75-JV2W-4656|CVE-2026-55443|PYSEC-2026-2192|PYSEC-2026-2556' 2>/dev/null \
      | xargs -r rm -f || true

# --- agent layer: append to a task's environment/Dockerfile -----------------
# Pre-installs Claude Code so Harbor skips its own install step at trial start
# (that step otherwise apt-installs Node.js on every trial, which is slow and
# fails on network hiccups). Needs curl, bash and ca-certificates in the image.
RUN curl -fsSL https://downloads.claude.ai/claude-code-releases/bootstrap.sh | bash \
    && ln -sf /root/.local/bin/claude /usr/local/bin/claude \
    && claude --version
# -----------------------------------------------------------------------------
