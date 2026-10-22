FROM maven:3.9-eclipse-temurin-17

# Tools the task and verifier need. Everything is installed now so the trial
# itself needs NO network.
RUN apt-get update && apt-get install -y --no-install-recommends \
      ca-certificates curl git patch bash python3 \
    && rm -rf /var/lib/apt/lists/*

# Fetch the plugin at the VULNERABLE parent commit, apply the task's injected
# sibling methods into this copy only, then drop the history so neither the
# later fix nor the injection provenance is present in the image.
WORKDIR /app
COPY inject-siblings.patch /tmp/inject-siblings.patch
RUN git init -q . \
 && git remote add origin https://github.com/jenkinsci/ec2-fleet-plugin \
 && git fetch -q --depth 1 origin 8fedff2a81c3f91c14e7a1f5ea5191063f3d43b3 \
 && git checkout -q FETCH_HEAD \
 && patch -p1 < /tmp/inject-siblings.patch \
 && rm -f /tmp/inject-siblings.patch \
 && rm -rf /app/.git

# Common Maven options: skip the plugin parent-POM quality gates that are not
# relevant to the task and that would otherwise slow or fail an offline build.
ENV MVN_SKIPS="-Dspotbugs.skip=true -Dcheckstyle.skip=true -Denforcer.skip=true \
-Dspotless.check.skip=true -Dspotless.apply.skip=true -Dmaven.javadoc.skip=true \
-Dlicense.skip=true -Dforbiddenapis.skip=true -Daccess-modifier-checker.skip=true \
-Dmaven.test.failure.ignore=true"

# Warm the local Maven repository with every build/test dependency (the Jenkins
# test harness, HtmlUnit, Mockito, the AWS SDK, surefire, the hpi plugin, ...)
# by compiling the project and running one JenkinsRule-backed test online now.
# After this the verifier runs fully offline with `mvn -o`.
RUN mvn -B -q test-compile $MVN_SKIPS \
 && mvn -B -q surefire:test -Dtest=CloudNamesTest $MVN_SKIPS \
 ; mvn -B -q org.apache.maven.plugins:maven-dependency-plugin:3.6.1:go-offline $MVN_SKIPS || true

# --- agent layer: append to a task's environment/Dockerfile -----------------
# Pre-installs Claude Code so Harbor skips its own install step at trial start
# (that step otherwise apt-installs Node.js on every trial, which is slow and
# fails on network hiccups). Needs curl, bash and ca-certificates in the image.
RUN curl -fsSL https://downloads.claude.ai/claude-code-releases/bootstrap.sh | bash \
    && ln -sf /root/.local/bin/claude /usr/local/bin/claude \
    && claude --version
# -----------------------------------------------------------------------------
