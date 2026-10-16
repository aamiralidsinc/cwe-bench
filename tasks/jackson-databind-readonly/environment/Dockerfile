FROM eclipse-temurin:17-jdk-jammy

# Tools the task and verifier need. Everything is installed now so the trial
# itself needs NO network.
RUN apt-get update && apt-get install -y --no-install-recommends \
      ca-certificates curl git patch bash python3 \
    && rm -rf /var/lib/apt/lists/*

# Fetch the library at the VULNERABLE parent commit, then drop the history so
# the later fix is not present in the image.
WORKDIR /app
RUN git init -q . \
 && git remote add origin https://github.com/fasterxml/jackson-databind \
 && git fetch -q --depth 1 origin d627a8a86fcb062429282f79f3f256f181ed2c7b \
 && git checkout -q FETCH_HEAD \
 && rm -rf /app/.git

# Offline build/test dependencies: the published release artifacts of the two
# sibling modules this library compiles against, plus a self-contained JUnit 5
# runner. Vendored into the image so the verifier runs without network.
RUN mkdir -p /opt/libs \
 && curl -fsSL --retry 5 -o /opt/libs/jackson-core-2.18.4.jar \
      https://repo1.maven.org/maven2/com/fasterxml/jackson/core/jackson-core/2.18.4/jackson-core-2.18.4.jar \
 && curl -fsSL --retry 5 -o /opt/libs/jackson-annotations-2.18.4.jar \
      https://repo1.maven.org/maven2/com/fasterxml/jackson/core/jackson-annotations/2.18.4/jackson-annotations-2.18.4.jar \
 && curl -fsSL --retry 5 -o /opt/libs/junit-platform-console-standalone-1.11.4.jar \
      https://repo1.maven.org/maven2/org/junit/platform/junit-platform-console-standalone/1.11.4/junit-platform-console-standalone-1.11.4.jar

# Convenience helper: compiles the library offline so a solver can confirm its
# change still builds. It does not run any tests and reveals nothing about the flaw.
COPY compile-lib.sh /opt/verify/compile-lib.sh
RUN chmod +x /opt/verify/compile-lib.sh

# --- agent layer: append to a task's environment/Dockerfile -----------------
# Pre-installs Claude Code so Harbor skips its own install step at trial start
# (that step otherwise apt-installs Node.js on every trial, which is slow and
# fails on network hiccups). Needs curl, bash and ca-certificates in the image.
RUN curl -fsSL https://downloads.claude.ai/claude-code-releases/bootstrap.sh | bash \
    && ln -sf /root/.local/bin/claude /usr/local/bin/claude \
    && claude --version
# -----------------------------------------------------------------------------
