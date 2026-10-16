#!/bin/bash
# Verifier entry point. Rebuilds the trigger.dev webapp from whatever is in
# /app, starts it against a fresh local Postgres + Redis (dummy ClickHouse),
# seeds a tenant + fixtures, then drives the security and functional test
# groups against the running server over its real HTTP API, writing JUnit XML
# into /logs/verifier/{security,functional}/ and scoring. The authoritative
# tests live under /tests; copies in /app are ignored.

# Stop the agent before grading (2026-10-16). On an agent timeout Harbor stops waiting for the
# agent but does not kill it inside this shared container, and it was seen editing /app while
# the tests ran (research/own-runs; build/postmortem.py). Kill every Claude Code process first.
for _p in /proc/[0-9]*; do
  case "$(tr '\0' ' ' < "$_p/cmdline" 2>/dev/null)" in
    claude\ *|*/claude\ *|*@anthropic-ai/claude-code*) kill -9 "${_p#/proc/}" 2>/dev/null || true ;;
  esac
done
sleep 1
set -uo pipefail
mkdir -p /logs/verifier/security /logs/verifier/functional
rm -f /logs/verifier/reward.* /logs/verifier/results.json

export DATABASE_URL="postgresql://postgres@127.0.0.1:5432/main?schema=public&sslmode=disable"
export DIRECT_URL="$DATABASE_URL"
export SESSION_SECRET=2818143646516f6fffd707b36f334bbb
export MAGIC_LINK_SECRET=44da78b7bbb0dfe709cf38931d25dcdd
export ENCRYPTION_KEY=f686147ab967943ebbe9ed3b496e465a
export MANAGED_WORKER_SECRET=447c29678f9eaf289e9c4b70d3dd8a7f
export CLICKHOUSE_URL="http://default:password@127.0.0.1:8123?secure=false"
export REDIS_HOST=127.0.0.1 REDIS_PORT=6379 REDIS_TLS_DISABLED=true
export APP_ORIGIN=http://localhost:3030 LOGIN_ORIGIN=http://localhost:3030 API_ORIGIN=http://localhost:3030
export NODE_ENV=development PORT=3030
export DEPLOY_REGISTRY_HOST=localhost:5000
export NODE_PATH=/app/node_modules/.pnpm/node_modules
export CI=1 HUSKY=0 TRIGGER_TELEMETRY_DISABLED=1

# --- Clean slate. The agent shares this container and often leaves its own dev
# server, Postgres, Redis or restart-loop scripts running; a held port or DB lock
# then hung setup until the verifier timed out (3 runs lost their grade, 2026-10-15).
# Kill them, sparing this script's own process chain.
keep=" 1 "; p=$$
while [ -n "$p" ] && [ "$p" -gt 1 ] 2>/dev/null; do
    keep="$keep$p "; p=$(awk '{print $4}' "/proc/$p/stat" 2>/dev/null)
done
for pid in $(pgrep -f 'node|pnpm|npm|npx|tsx|turbo|esbuild|remix|vite|postgres|redis|/tmp/|/app/'); do
    case "$keep" in *" $pid "*) ;; *) kill -9 "$pid" 2>/dev/null ;; esac
done
pkill -9 -u postgres 2>/dev/null
sleep 2

# --- Crash artifacts. A process that crashes in this container (e.g. a type-check that
# ran out of memory) can leave an ELF core dump in /app; the bundler then fills all memory
# on it (2026-10-15: a 4.5 GB dump broke grading at 6 and 8 GB). A core dump is not part of
# any fix: move it out of /app (kept under /tmp/core-dumps) and say so in the output.
python3 - <<'PY'
import os, shutil, sys
moved = []
for root, dirs, files in os.walk("/app"):
    dirs[:] = [d for d in dirs if d not in ("node_modules", ".git")]
    for f in files:
        p = os.path.join(root, f)
        try:
            if os.path.getsize(p) < 1_000_000:
                continue
            with open(p, "rb") as fh:
                head = fh.read(18)
        except OSError:
            continue
        if head[:4] == b"\x7fELF" and int.from_bytes(head[16:18], "little") == 4:
            os.makedirs("/tmp/core-dumps", exist_ok=True)
            shutil.move(p, os.path.join("/tmp/core-dumps", p.strip("/").replace("/", "__")))
            moved.append(p)
if moved:
    print("NOTE: moved core dump(s) out of /app (a process crashed during the run): "
          + ", ".join(moved), file=sys.stderr)
PY

# --- EDIT: rebuild the webapp from /app so the agent's fix takes effect
# (offline, incremental against the baked turbo/module caches).
# Every setup step is time-limited: a broken state must be GRADED (as a fail), not hang.
( cd /app && timeout -k 10 600 pnpm run build --filter webapp ) >/tmp/webapp-build.log 2>&1 \
    || echo "WARNING: webapp build from /app failed (see /tmp/webapp-build.log)" >&2

# Fresh Postgres cluster + Redis, both local; no external services.
PGBIN=$(ls -d /usr/lib/postgresql/*/bin | head -1)
export PGDATA=/var/lib/postgresql/data
pkill -9 -f 'build/server.js' 2>/dev/null; sleep 1
su postgres -c "$PGBIN/pg_ctl -D $PGDATA stop -m immediate" 2>/dev/null
rm -rf "$PGDATA"; mkdir -p "$PGDATA"; chown -R postgres:postgres "$PGDATA"
su postgres -c "$PGBIN/initdb -A trust -D $PGDATA" >/tmp/pg-init.log 2>&1
su postgres -c "$PGBIN/pg_ctl -D $PGDATA -o '-c listen_addresses=127.0.0.1 -p 5432' -l /tmp/pg.log -w start" >/dev/null 2>&1
su postgres -c "$PGBIN/createdb -h 127.0.0.1 main" 2>/dev/null
redis-server --daemonize yes >/tmp/redis.log 2>&1
sleep 1

# Apply DB migrations, seed a tenant (org/projects/environments + keys), then
# add the task fixtures (a known PAT + one TaskRun).
( cd /app/internal-packages/database && timeout -k 10 180 pnpm exec prisma migrate deploy ) >/tmp/migrate.log 2>&1 \
    || echo "WARNING: migrate failed or timed out" >&2
( cd /app/apps/webapp && timeout -k 10 180 pnpm run db:seed ) >/tmp/seed.log 2>&1 \
    || echo "WARNING: seed failed or timed out" >&2
cp /tests/lib/fixtures.ts /app/apps/webapp/.tbfixtures.ts
( cd /app/apps/webapp && timeout -k 10 180 pnpm exec tsx .tbfixtures.ts ) >/tmp/fixtures.log 2>&1 \
    || echo "WARNING: fixtures failed or timed out" >&2
echo "---- fixtures.log ----" >&2; tail -20 /tmp/fixtures.log >&2

# Credentials/refs the tests need: fixtures.ts (which has reliable Prisma
# access) prints them as TR_*=... lines; take only those lines.
export TR_BASE=http://127.0.0.1:3030
export TR_EMAIL=local@trigger.dev
eval "$(grep -E '^TR_(PAT|RUN|BATCH|BATCH_ANON|BATCH_XORG|OUTSIDER_EMAIL|PROJREF|PROD_KEY|DEV_KEY|STAGING_KEY)=' /tmp/fixtures.log | sed 's/^/export /')"
echo "fixtures -> PAT=${TR_PAT:-MISSING} PROJREF=${TR_PROJREF:-MISSING} PROD=${TR_PROD_KEY:-MISSING} DEV=${TR_DEV_KEY:-MISSING}" >&2

# Boot the webapp (detached so it survives this shell).
( cd /app/apps/webapp && setsid node build/server.js >/tmp/webapp.log 2>&1 </dev/null & )
up=0
for _ in $(seq 1 90); do
    if curl -sf -o /dev/null http://127.0.0.1:3030/login 2>/dev/null; then up=1; break; fi
    sleep 1
done
[ "$up" = 1 ] || { echo "server did not come up" >&2; tail -40 /tmp/webapp.log >&2; }

# --- EDIT: run the two groups; a failure in one must not stop the other.
# SIGINT on timeout lets pytest stop cleanly and still write its JUnit file.
timeout -s INT -k 30 300 python3 -m pytest /tests/security   -q -p no:cacheprovider -o cache_dir=/tmp/pc_s \
    --junitxml=/logs/verifier/security/results.xml
timeout -s INT -k 30 300 python3 -m pytest /tests/functional -q -p no:cacheprovider -o cache_dir=/tmp/pc_f \
    --junitxml=/logs/verifier/functional/results.xml

pkill -f 'build/server.js' 2>/dev/null

python3 /tests/score.py
