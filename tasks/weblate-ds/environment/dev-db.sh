#!/bin/bash
# Development database: initialise a private cluster on first use, then start it.
# The unprivileged account owns both the data directory and the socket.
set -u
PGBIN=/usr/lib/postgresql/17/bin
DATA="${HOME}/.weblate-dev-pg"
SOCK="${HOME}/.weblate-dev-pg-sock"
mkdir -p "${SOCK}"
if [ ! -f "${DATA}/PG_VERSION" ]; then
    "${PGBIN}/initdb" -D "${DATA}" -U postgres --auth=trust --no-locale --encoding=UTF8 >/dev/null || exit 1
fi
if ! "${PGBIN}/pg_ctl" -D "${DATA}" status >/dev/null 2>&1; then
    "${PGBIN}/pg_ctl" -D "${DATA}" -l "${DATA}/server.log" \
        -o "-k ${SOCK} -p 5433 -c listen_addresses=''" -w -t 120 start >/dev/null || exit 1
fi
echo "PostgreSQL ready: CI_DB_HOST=${SOCK} CI_DB_PORT=5433 CI_DB_USER=postgres"
