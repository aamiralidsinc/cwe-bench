FROM python:3.12-slim-bookworm

RUN apt-get update && apt-get install -y --no-install-recommends \
        patch curl ca-certificates bash git \
    && rm -rf /var/lib/apt/lists/*

# django CMS at the vulnerable commit (parent of the published fix)
WORKDIR /app
RUN git init -q . \
    && git remote add origin https://github.com/django-cms/django-cms.git \
    && git fetch -q --depth 1 origin 3edf89a0a8bb06cdd54d2d22cba33ee7b72b5b82 \
    && git checkout -q FETCH_HEAD \
    && rm -rf /app/.git

# Project + test dependencies (Django 5.2 line), installed for offline use.
RUN pip install --no-cache-dir \
        "Django>=5.2,<6.0" django-classy-tags django-formtools "django-sekizai>=0.7" \
        "django-treebeard>=4.3" "djangocms-admin-style>=1.5" djangocms-text-ckeditor \
        dj-database-url mock Pillow unittest-xml-reporting setuptools \
        pytest pytest-django \
    && pip install --no-cache-dir --no-deps -e /app \
    && python -c "import cms, django; print(cms.__version__, django.get_version())"

ENV PYTHONDONTWRITEBYTECODE=1

# --- agent layer: append to a task's environment/Dockerfile -----------------
# Pre-installs Claude Code so Harbor skips its own install step at trial start
# (that step otherwise apt-installs Node.js on every trial, which is slow and
# fails on network hiccups). Needs curl, bash and ca-certificates in the image.
RUN curl -fsSL https://downloads.claude.ai/claude-code-releases/bootstrap.sh | bash \
    && ln -sf /root/.local/bin/claude /usr/local/bin/claude \
    && claude --version
# -----------------------------------------------------------------------------
