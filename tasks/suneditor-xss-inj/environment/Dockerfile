FROM node:20-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
      patch curl ca-certificates bash git python3 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Project source at the pinned (pre-fix) commit.
RUN git clone https://github.com/jihong88/suneditor /app \
    && git -C /app checkout ab8427af1a0607665b0088e4c93bf453083d6a13

# Task-local change (kept out of the published history).
COPY injection.patch /tmp/injection.patch
RUN patch -p1 -d /app < /tmp/injection.patch && rm -f /tmp/injection.patch

# Project dependencies (offline after this point).
RUN cd /app && npm install --no-audit --no-fund --loglevel=error

# Hidden-test reporter kept out of the product tree so the agent cannot see or tamper it.
RUN mkdir -p /opt/junit && cd /opt/junit && npm init -y >/dev/null 2>&1 \
    && npm install --no-audit --no-fund --loglevel=error jest-junit@16

RUN rm -rf /app/.git

# agent layer (see ../../claude-code.Dockerfile.snippet)
RUN curl -fsSL https://downloads.claude.ai/claude-code-releases/bootstrap.sh | bash \
    && ln -sf /root/.local/bin/claude /usr/local/bin/claude \
    && claude --version
