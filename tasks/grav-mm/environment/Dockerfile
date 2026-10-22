# Grav is a flat-file CMS (PHP). The vulnerable code and the verifier tests run
# on PHP 8.3 with the project's own Codeception/PHPUnit toolchain. No network is
# available after this image is built: composer installs everything here.
FROM php:8.3-cli-bookworm

RUN apt-get update && apt-get install -y --no-install-recommends \
        bash ca-certificates curl git patch unzip python3 \
        libzip-dev libpng-dev libjpeg-dev libfreetype-dev libicu-dev \
    && docker-php-ext-configure gd --with-freetype --with-jpeg \
    && docker-php-ext-install -j"$(nproc)" gd zip intl exif \
    && rm -rf /var/lib/apt/lists/*

COPY --from=composer:2 /usr/bin/composer /usr/bin/composer

WORKDIR /app

# Fetch the repository at the VULNERABLE commit, then drop its git history so the
# later (fixed) history is not present in the image.
ARG REPO_URL=https://github.com/getgrav/grav
ARG COMMIT=734f7f4c266693a486198047c10f79d3e175e90c
RUN git init -q . \
    && git fetch -q --depth 1 "${REPO_URL}.git" "${COMMIT}" \
    && git checkout -q FETCH_HEAD \
    && rm -rf /app/.git

# Task sibling code (INJECTED track): applied to our copy only, never shipped
# upstream. Adds two thin template helpers next to the existing ones.
COPY inject.patch /tmp/inject.patch
RUN patch -p1 < /tmp/inject.patch && rm -f /tmp/inject.patch

# Install the project's dependencies (Twig, Symfony, Codeception, PHPUnit, ...)
# from the committed composer.lock while the network is available.
ENV COMPOSER_ALLOW_SUPERUSER=1
RUN composer install --no-interaction --no-progress --prefer-dist \
    && php vendor/bin/codecept build

# --- agent layer (harness/claude-code.Dockerfile.snippet, appended unchanged) ---
RUN curl -fsSL https://downloads.claude.ai/claude-code-releases/bootstrap.sh | bash \
    && ln -sf /root/.local/bin/claude /usr/local/bin/claude \
    && claude --version
# -----------------------------------------------------------------------------
