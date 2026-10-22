# OliveTin action executor — argument-allowlist / system-value command-injection task.
# Go project, offline after build.
FROM golang:1.25-bookworm

RUN apt-get update \
 && apt-get install -y --no-install-recommends patch curl ca-certificates bash git \
 && rm -rf /var/lib/apt/lists/*

ENV GOTOOLCHAIN=local \
    GOFLAGS=-mod=mod \
    CGO_ENABLED=0

# Pinned (vulnerable) commit.
RUN git clone https://github.com/OliveTin/OliveTin /app \
 && cd /app \
 && git checkout 41612c6bc6a8a6424e27e6a66fb0dae30524c768

WORKDIR /app

# Inject the sibling code into our copy only (not upstream).
COPY inject.patch /tmp/inject.patch
RUN patch -p1 < /tmp/inject.patch && rm -f /tmp/inject.patch

# Warm the module cache and the test-dependency graph so grading runs offline,
# and install the JUnit converter. Network is available only during this build.
RUN cd /app/service \
 && go build ./internal/... \
 && go test ./internal/executor/ ./internal/config/ -run '^$' -count=1 \
 && go install github.com/jstemmer/go-junit-report/v2@latest \
 && cp "$(go env GOPATH)/bin/go-junit-report" /usr/local/bin/go-junit-report

# Drop the repository history.
RUN rm -rf /app/.git

# --- agent layer: append to a task's environment/Dockerfile -----------------
RUN curl -fsSL https://downloads.claude.ai/claude-code-releases/bootstrap.sh | bash \
    && ln -sf /root/.local/bin/claude /usr/local/bin/claude \
    && claude --version
# -----------------------------------------------------------------------------
