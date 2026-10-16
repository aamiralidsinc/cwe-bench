# Base image ships JDK 11 + Maven, matching the project's build requirements.
FROM maven:3.9-eclipse-temurin-11

# Tools the task and the verifier need. bash is already present in this image.
RUN apt-get update \
    && apt-get install -y --no-install-recommends patch curl ca-certificates git python3 \
    && rm -rf /var/lib/apt/lists/*

# Fetch the repository at the VULNERABLE parent commit into /app.
WORKDIR /app
RUN git init -q \
    && git remote add origin https://github.com/asynchttpclient/async-http-client.git \
    && git fetch -q --depth 1 origin 7dc5bbc2d0a48aa2a9caf089a626dcfd333168e9 \
    && git checkout -q FETCH_HEAD

# Resolver retry/timeout settings: Maven Central is fetched once here, during the
# image build, under shared-network contention, so make transient read failures
# retry rather than abort the whole build.
ENV MVN_NET="-Daether.connector.http.retryHandler.count=12 \
-Daether.connector.connectTimeout=60000 \
-Daether.connector.requestTimeout=300000 \
-Dmaven.wagon.http.retryHandler.count=12 \
-Dmaven.wagon.rto=300000"

# Warm the Maven cache and produce the initial build, with network available at
# BUILD time only. After this, `mvn -o` (offline) builds the client without any
# network, which is what the verifier relies on at run time. A second offline
# pass then proves the cache is complete before the image is sealed.
RUN mvn -q -pl client -am package $MVN_NET \
      -Dmaven.test.skip=true -Dgpg.skip=true -Dspotbugs.skip=true \
      -Dcheckstyle.skip=true -Dlicense.skip=true -Denforcer.skip=true \
      -Dmaven.javadoc.skip=true -Dsource.skip=true

# Stage the client's runtime dependencies and a JUnit 5 console launcher in a
# stable location, so the verifier can compile and run its own tests offline
# regardless of what the agent does to the build tree.
RUN mvn -q -pl client org.apache.maven.plugins:maven-dependency-plugin:3.6.1:copy-dependencies $MVN_NET \
      -DincludeScope=runtime -DoutputDirectory=/opt/ahc-deps -Dgpg.skip=true \
    && curl -fsSL --retry 8 --retry-all-errors -o /opt/junit-console.jar \
      https://repo1.maven.org/maven2/org/junit/platform/junit-platform-console-standalone/1.11.4/junit-platform-console-standalone-1.11.4.jar \
    && mvn -q -o -pl client -am package \
      -Dmaven.test.skip=true -Dgpg.skip=true -Dspotbugs.skip=true \
      -Dcheckstyle.skip=true -Dlicense.skip=true -Denforcer.skip=true \
      -Dmaven.javadoc.skip=true -Dsource.skip=true

# Drop the repository history so later commits are not present in the image.
RUN rm -rf /app/.git

# --- agent layer: append to a task's environment/Dockerfile -----------------
# Pre-installs Claude Code so Harbor skips its own install step at trial start
# (that step otherwise apt-installs Node.js on every trial, which is slow and
# fails on network hiccups). Needs curl, bash and ca-certificates in the image.
RUN curl -fsSL https://downloads.claude.ai/claude-code-releases/bootstrap.sh | bash \
    && ln -sf /root/.local/bin/claude /usr/local/bin/claude \
    && claude --version
# -----------------------------------------------------------------------------
