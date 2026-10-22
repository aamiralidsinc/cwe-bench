# protobuf.js is a CommonJS Node.js library. The pinned sources and the hidden
# verifier tests run on Node 20 with the project's own dependencies. Nothing is
# downloaded after this image is built.
FROM node:20-bookworm-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
        bash ca-certificates curl git patch python3 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Fetch the repository at the VULNERABLE commit and drop its git history so the
# later (fixed) history is not present in the image.
ARG REPO_URL=https://github.com/protobufjs/protobuf.js
ARG COMMIT=1aca107aa7938d1e49a25f9653186db2f40a0253
RUN git init -q . \
    && git fetch -q --depth 1 "${REPO_URL}.git" "${COMMIT}" \
    && git checkout -q FETCH_HEAD \
    && rm -rf /app/.git

# Task sibling code (INJECTED track): applied to our copy only, never shipped
# upstream. Two omitted own-property checks next to the existing option paths.
COPY injection.patch /tmp/injection.patch
RUN patch -p1 < /tmp/injection.patch && rm -f /tmp/injection.patch

# Install the runtime and development dependencies from the committed lockfile.
# The CLI package ships its own lockfile that predates a dependency bump, so it
# is installed from its manifest; its bundled copy of the library is then
# replaced with a link to the working tree so the generator always sees /app.
RUN npm ci --ignore-scripts --no-audit --no-fund \
    && cd cli && npm install --ignore-scripts --no-audit --no-fund \
    && rm -rf /app/cli/node_modules/protobufjs \
    && ln -s /app /app/cli/node_modules/protobufjs

# Pristine copy of the project's own tests for the affected area, kept outside
# the working tree so a later edit of /app/tests cannot affect grading. The
# links make the copies resolve the library and its dependencies in /app.
RUN mkdir -p /opt/pristine-tests/tests \
    && cp /app/tests/api_textformat.js /app/tests/api_enum.js /app/tests/api_object.js \
          /app/tests/api_descriptor.js /app/tests/api_util.js /opt/pristine-tests/tests/ \
    && cp -a /app/tests/data /opt/pristine-tests/tests/data \
    && ln -s /app/index.js /opt/pristine-tests/index.js \
    && ln -s /app/light.js /opt/pristine-tests/light.js \
    && ln -s /app/minimal.js /opt/pristine-tests/minimal.js \
    && ln -s /app/ext /opt/pristine-tests/ext \
    && ln -s /app/src /opt/pristine-tests/src \
    && ln -s /app/google /opt/pristine-tests/google \
    && ln -s /app/node_modules /opt/pristine-tests/node_modules

# --- agent layer: append to a task's environment/Dockerfile -----------------
# Pre-installs Claude Code so Harbor skips its own install step at trial start
# (that step otherwise apt-installs Node.js on every trial, which is slow and
# fails on network hiccups). Needs curl, bash and ca-certificates in the image.
RUN curl -fsSL https://downloads.claude.ai/claude-code-releases/bootstrap.sh | bash \
    && ln -sf /root/.local/bin/claude /usr/local/bin/claude \
    && claude --version
# -----------------------------------------------------------------------------
