FROM maven:3.9-eclipse-temurin-17

# Everything the task and the verifier need is installed now; the trial itself
# runs without network.
RUN apt-get update && apt-get install -y --no-install-recommends \
      ca-certificates curl git patch bash python3 procps \
    && rm -rf /var/lib/apt/lists/*

# Fetch the project at the vulnerable parent commit, apply the task's injected
# sibling gaps to this copy only, then drop the history so neither a later fix
# nor the injection provenance is present in the image.
WORKDIR /app
COPY inject-siblings.patch /tmp/inject-siblings.patch
RUN git init -q . \
 && git remote add origin https://github.com/yamcs/yamcs \
 && git fetch -q --depth 1 origin b566beceba98cc35514b0e1519be126b8c5a0438 \
 && git checkout -q FETCH_HEAD \
 && patch -p1 < /tmp/inject-siblings.patch \
 && rm -f /tmp/inject-siblings.patch \
 && rm -rf /app/.git

# The product modules used by the grading harness. yamcs-web (Angular) is not
# needed and is never built.
ENV MVN_SKIPS="-Dmaven.javadoc.skip=true -Denforcer.skip=true -Dlicense.skip=true"

RUN mvn -B -q -Dmaven.test.skip=true $MVN_SKIPS \
      -pl yamcs-api,yamcs-xtce,yamcs-client,yamcs-core,tests -am install

# Warm every build/test dependency and the surefire provider by compiling the
# tests module and running one of the project's own integration tests online.
RUN mvn -B -q $MVN_SKIPS -pl tests test -Dtest=PermissionsTest -DfailIfNoTests=false \
 && mvn -B -q $MVN_SKIPS -pl tests -am test-compile -DskipTests || true
RUN mvn -B -q $MVN_SKIPS -pl yamcs-api,yamcs-xtce,yamcs-client,yamcs-core,tests \
      org.apache.maven.plugins:maven-dependency-plugin:3.6.1:go-offline || true

# --- agent layer: append to a task's environment/Dockerfile -----------------
# Pre-installs Claude Code so Harbor skips its own install step at trial start
# (that step otherwise apt-installs Node.js on every trial, which is slow and
# fails on network hiccups). Needs curl, bash and ca-certificates in the image.
RUN curl -fsSL https://downloads.claude.ai/claude-code-releases/bootstrap.sh | bash \
    && ln -sf /root/.local/bin/claude /usr/local/bin/claude \
    && claude --version
# -----------------------------------------------------------------------------
