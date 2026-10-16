# Filament is a Laravel admin-panel framework (PHP). The vulnerable code and the
# verifier tests run on PHP 8.4 (the committed composer.lock pins packages that
# require PHP >= 8.4) with an in-memory SQLite database. No network is available
# after this image is built: composer installs everything here.
FROM php:8.4-cli-bookworm

RUN apt-get update && apt-get install -y --no-install-recommends \
        bash ca-certificates curl git patch unzip python3 \
        libicu-dev libzip-dev libonig-dev libsqlite3-dev libpng-dev libjpeg-dev libfreetype-dev \
    && docker-php-ext-configure gd --with-freetype --with-jpeg \
    && docker-php-ext-install -j"$(nproc)" intl pdo_sqlite zip bcmath sockets exif gd \
    && rm -rf /var/lib/apt/lists/*

COPY --from=composer:2 /usr/bin/composer /usr/bin/composer

WORKDIR /app

# Fetch the repository at the VULNERABLE commit, then drop its git history so the
# later (fixed) history is not present in the image.
ARG REPO_URL=https://github.com/filamentphp/filament
ARG COMMIT=e1f36a7316d75476f3301e044cc360d7cb746c56
RUN git init -q . \
    && git fetch -q --depth 1 "${REPO_URL}.git" "${COMMIT}" \
    && git checkout -q FETCH_HEAD \
    && rm -rf /app/.git

# Install the project's dependencies (framework, Livewire, Testbench, PHPUnit,
# google2fa, ...) while the network is available. `composer install` uses the
# committed composer.lock, so the dependency set is deterministic.
ENV COMPOSER_ALLOW_SUPERUSER=1
RUN composer install --no-interaction --no-progress --prefer-dist

# --- agent layer (harness/claude-code.Dockerfile.snippet, appended unchanged) ---
RUN curl -fsSL https://downloads.claude.ai/claude-code-releases/bootstrap.sh | bash \
    && ln -sf /root/.local/bin/claude /usr/local/bin/claude \
    && claude --version
# -----------------------------------------------------------------------------
