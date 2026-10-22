# OpenBao identity-template authorization task. Go project, offline after build.
FROM golang:1.25.8-bookworm

RUN apt-get update \
 && apt-get install -y --no-install-recommends patch curl ca-certificates bash git \
 && rm -rf /var/lib/apt/lists/*

ENV GOTOOLCHAIN=local \
    GOFLAGS=-mod=mod \
    CGO_ENABLED=0

# Pinned (vulnerable) commit. Depth-1 fetch of the exact tree; no later history.
WORKDIR /app
COPY inject.patch /tmp/inject.patch
RUN git init -q . \
 && git remote add origin https://github.com/openbao/openbao \
 && git fetch -q --depth 1 origin 681f6e2730f03f9cd2a5ce7d056fc957622cfe81 \
 && git checkout -q FETCH_HEAD \
 && patch -p1 < /tmp/inject.patch \
 && rm -f /tmp/inject.patch

WORKDIR /app

# Warm the module cache (root module plus the sdk module) and the test-dependency
# graph so grading runs offline, and install the JUnit converter. Network is
# available only during this build.
RUN go build ./vault/ ./builtin/logical/pki/ ./builtin/logical/ssh/ \
 && go test ./vault/policy/ ./vault/external_tests/policy/ ./builtin/logical/pki/ ./builtin/logical/ssh/ -run '^$' -count=1 \
 && ( cd sdk && go test ./helper/identitytpl/ -run '^$' -count=1 ) \
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
