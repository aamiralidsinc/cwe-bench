# Trivy plugin manager — path-traversal task. Go project, offline after build.
FROM golang:1.26.3-bookworm

RUN apt-get update \
 && apt-get install -y --no-install-recommends patch curl ca-certificates bash git \
 && rm -rf /var/lib/apt/lists/*

ENV GOTOOLCHAIN=local \
    GOEXPERIMENT=jsonv2 \
    GOFLAGS=-mod=mod \
    CGO_ENABLED=0

# Pinned (vulnerable) commit.
RUN git clone https://github.com/aquasecurity/trivy /app \
 && cd /app \
 && git checkout 246ee3ca56b666e3c6e6462bf7c0ecd6f059341a

WORKDIR /app

# Inject the sibling code into our copy only (not upstream).
COPY inject.patch /tmp/inject.patch
RUN patch -p1 < /tmp/inject.patch && rm -f /tmp/inject.patch

# Warm the module cache and the test-dependency graph so grading runs offline,
# and install the JUnit converter. Network is available only during this build.
RUN go build ./pkg/plugin/... ./pkg/x/os/... \
 && go test ./pkg/plugin/ -run '^$' -count=1 \
 && go install github.com/jstemmer/go-junit-report/v2@latest \
 && cp "$(go env GOPATH)/bin/go-junit-report" /usr/local/bin/go-junit-report

# Drop the repository history.
RUN rm -rf /app/.git

# --- agent layer: append to a task's environment/Dockerfile -----------------
# Pre-installs Claude Code so Harbor skips its own install step at trial start
# (that step otherwise apt-installs Node.js on every trial, which is slow and
# fails on network hiccups). Needs curl, bash and ca-certificates in the image.
RUN curl -fsSL https://downloads.claude.ai/claude-code-releases/bootstrap.sh | bash \
    && ln -sf /root/.local/bin/claude /usr/local/bin/claude \
    && claude --version
# -----------------------------------------------------------------------------
