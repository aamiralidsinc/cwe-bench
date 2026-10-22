# PHP 8.3: a version the project's own toolchain supports (composer.json requires
# php ^7.2.5 || ^8.0). The flaw is not PHP-version dependent.
FROM php:8.3-cli

# Tools the task and verifier need. No network is available after build.
RUN apt-get update && apt-get install -y --no-install-recommends \
        bash ca-certificates curl git patch unzip libzip-dev python3 \
    && docker-php-ext-install zip >/dev/null \
    && rm -rf /var/lib/apt/lists/*

# Composer itself, used only at build time to install the project's dependencies.
RUN curl -fsSL https://getcomposer.org/installer -o /tmp/composer-setup.php \
    && php /tmp/composer-setup.php --install-dir=/usr/local/bin --filename=composer \
    && rm -f /tmp/composer-setup.php && composer --version

WORKDIR /app

# Fetch the monorepo at the pinned (vulnerable) commit.
ARG REPO_URL=https://github.com/composer/composer
ARG COMMIT=24e396b5279a92fadf4897dd701d2cb97942cda3
RUN git init -q . \
    && git fetch -q --depth 1 "${REPO_URL}.git" "${COMMIT}" \
    && git checkout -q FETCH_HEAD

# Inject the same-class bin-permission siblings into other install/download
# code paths, then drop the git history so no later (fixed) commit is present.
COPY injection.patch /tmp/injection.patch
RUN patch -p1 < /tmp/injection.patch \
    && rm -f /tmp/injection.patch \
    && rm -rf /app/.git

# Install the project's dependencies and test toolchain while the network is up.
RUN composer install --no-interaction --no-progress --no-scripts \
    && php -r "require 'vendor/autoload.php'; new Composer\Installer\BinaryInstaller(new Composer\IO\NullIO, '/tmp/b', 'auto');"

# Warm the symfony/phpunit-bridge PHPUnit install now, while the network is up:
# simple-phpunit downloads PHPUnit on first use, and grading happens offline.
RUN cd /app && vendor/bin/simple-phpunit tests/Composer/Test/Installer/BinaryInstallerTest.php >/dev/null 2>&1 || true \
    && test -f vendor/bin/.phpunit/phpunit-9.6-0/phpunit

# Defensive guard: drop any text file naming the advisory. The checkout predates
# the fix, so this finds nothing today.
RUN find /app -type f \( -name '*.md' -o -name '*.txt' -o -name '*.rst' \) -print0 \
      | xargs -0 -r grep -ilE 'GHSA-96h3-5x6v-m776|CVE-2026-59944|BIT-COMPOSER-2026-59944' 2>/dev/null \
      | xargs -r rm -f || true

# --- agent layer: append to a task's environment/Dockerfile -----------------
# Pre-installs Claude Code so Harbor skips its own install step at trial start
# (that step otherwise apt-installs Node.js on every trial, which is slow and
# fails on network hiccups). Needs curl, bash and ca-certificates in the image.
RUN curl -fsSL https://downloads.claude.ai/claude-code-releases/bootstrap.sh | bash \
    && ln -sf /root/.local/bin/claude /usr/local/bin/claude \
    && claude --version
# -----------------------------------------------------------------------------
