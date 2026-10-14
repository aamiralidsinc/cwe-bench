FROM ruby:3.2-slim-bookworm

# Runtime + build/test tooling. nokogiri ships a precompiled native gem for this
# platform, so no compiler/toolchain is needed. python3 is used by the verifier's
# scorer. libxml2/libxslt are nokogiri's shared-library runtime deps.
RUN apt-get update && apt-get install -y --no-install-recommends \
        bash ca-certificates curl git patch python3 libxml2 libxslt1.1 \
    && rm -rf /var/lib/apt/lists/*

RUN gem install --no-document nokogiri -v 1.16.7

# Fetch ruby-saml at the vulnerable commit (v1.16.0) and drop later history.
WORKDIR /app
RUN git init -q \
    && git remote add origin https://github.com/saml-toolkits/ruby-saml.git \
    && git fetch -q --depth 1 origin 148a4c2de713a98c58c28bbc7785c05698216a4d \
    && git checkout -q FETCH_HEAD \
    && rm -rf /app/.git

# --- agent layer: append to a task's environment/Dockerfile -----------------
RUN curl -fsSL https://downloads.claude.ai/claude-code-releases/bootstrap.sh | bash \
    && ln -sf /root/.local/bin/claude /usr/local/bin/claude \
    && claude --version
# -----------------------------------------------------------------------------
