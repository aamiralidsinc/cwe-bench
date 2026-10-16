# Python 3.11: matches the interpreter the project supports (>=3.10) and keeps
# the image lean. The flaw is not Python-version dependent.
FROM python:3.11-slim

# Tools the task and verifier need. No network is available after build.
RUN apt-get update && apt-get install -y --no-install-recommends \
        bash ca-certificates curl git patch \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Fetch the repository at the vulnerable commit, then drop its git history so
# the later (fixed) history, tags and branches are not present in the image.
ARG REPO_URL=https://github.com/posit-dev/py-shiny
ARG COMMIT=48b4faa0d651476afa84d6423d57503b60716902
RUN git init -q . \
    && git fetch -q --depth 1 "${REPO_URL}.git" "${COMMIT}" \
    && git checkout -q FETCH_HEAD \
    && rm -rf /app/.git

# Install the project (editable, so a fix to /app/shiny takes effect) plus the
# runtime pieces the tests drive it through (an in-process ASGI HTTP client)
# and the test runner. Done now while the network is available.
# The project derives its version from git via setuptools-scm, but we removed
# /app/.git above; supply the version explicitly (this checkout is the 1.6.3
# release) so the editable build does not need the repository history.
ENV SETUPTOOLS_SCM_PRETEND_VERSION_FOR_SHINY=1.6.3
RUN pip install --no-cache-dir -e . \
    && pip install --no-cache-dir "httpx>=0.27,<0.29" "pytest>=7,<9"

# Scrub any mention of the advisory / the fix from text the solver can read.
# The checkout predates the fix, so this finds nothing today; it is kept as a
# defensive guard so no release note, changelog entry or doc can name the
# vulnerability or its remedy. It deliberately does NOT touch the ordinary
# bookmark-feature documentation (a public feature the solver may rely on).
RUN find /app -type f \( -name '*.md' -o -name '*.txt' -o -name '*.rst' \) -print0 \
      | xargs -0 -r grep -ilE 'path.?traversal|GHSA-47c3|CVE-2026-108258' 2>/dev/null \
      | xargs -r rm -f || true

# --- agent layer (harness/claude-code.Dockerfile.snippet, appended unchanged) ---
RUN curl -fsSL https://downloads.claude.ai/claude-code-releases/bootstrap.sh | bash \
    && ln -sf /root/.local/bin/claude /usr/local/bin/claude \
    && claude --version
# -----------------------------------------------------------------------------
