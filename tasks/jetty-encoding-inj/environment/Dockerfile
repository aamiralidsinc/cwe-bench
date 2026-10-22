FROM maven:3.9-eclipse-temurin-17

# Tools the task and verifier need. Everything is installed now so the trial
# itself needs NO network.
RUN apt-get update && apt-get install -y --no-install-recommends \
      ca-certificates curl git patch bash python3 \
    && rm -rf /var/lib/apt/lists/*

# Fetch the project at the VULNERABLE parent commit, apply the task's injected
# sibling code into this copy only, then drop the history so neither the later
# fix nor the injection provenance is present in the image.
WORKDIR /app
COPY inject.patch /tmp/inject.patch
RUN git init -q . \
 && git remote add origin https://github.com/jetty/jetty.project \
 && git fetch -q --depth 1 origin 341a3175c4344a5122fcf5c302074309f8f284c6 \
 && git checkout -q FETCH_HEAD \
 && patch -p1 < /tmp/inject.patch \
 && rm -f /tmp/inject.patch \
 && rm -rf /app/.git

# Common Maven options: disable the module build cache (so source edits always
# rebuild) and skip the parent-POM quality gates that are irrelevant here and
# would otherwise slow or fail an offline build.
ENV MVN_SKIPS="-Dmaven.build.cache.enabled=false -Dspotbugs.skip=true -Dcheckstyle.skip=true \
-Denforcer.skip=true -Dspotless.check.skip=true -Dspotless.apply.skip=true -Dmaven.javadoc.skip=true \
-Dlicense.skip=true -Dforbiddenapis.skip=true -Daccess-modifier-checker.skip=true \
-Dmaven.buildNumber.skip=true -Dmaven.test.failure.ignore=true"

# Warm the local Maven repository with every build/test dependency (the Jetty
# core modules, JUnit 5, Hamcrest, the test helpers, ...) by compiling the
# affected modules and running one JUnit-backed test online now. After this the
# verifier runs fully offline with `mvn -o`.
RUN mvn -B -q -pl jetty-core/jetty-security -am install -DskipTests $MVN_SKIPS \
 && mvn -B -q -pl jetty-core/jetty-security test -Dtest=BasicAuthenticatorTest -DfailIfNoTests=false $MVN_SKIPS

# --- agent layer: append to a task's environment/Dockerfile -----------------
# Pre-installs Claude Code so Harbor skips its own install step at trial start
# (that step otherwise apt-installs Node.js on every trial, which is slow and
# fails on network hiccups). Needs curl, bash and ca-certificates in the image.
RUN curl -fsSL https://downloads.claude.ai/claude-code-releases/bootstrap.sh | bash \
    && ln -sf /root/.local/bin/claude /usr/local/bin/claude \
    && claude --version
# -----------------------------------------------------------------------------
