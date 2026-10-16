#!/bin/bash
# Boot the webapp offline (postgres + redis + dummy clickhouse) and reproduce
# the SSRF alert-channel exploit through the real HTTP API.
set -uo pipefail
PGBIN=$(ls -d /usr/lib/postgresql/*/bin | head -1)
export PGDATA=/var/lib/postgresql/data
mkdir -p "$PGDATA" && chown -R postgres:postgres "$PGDATA"
su postgres -c "$PGBIN/initdb -A trust -D $PGDATA" >/tmp/pg-init.log 2>&1
su postgres -c "$PGBIN/pg_ctl -D $PGDATA -o '-c listen_addresses=127.0.0.1 -p 5432' -l /tmp/pg.log start"
sleep 3
su postgres -c "$PGBIN/createdb -h 127.0.0.1 main" 2>/dev/null
redis-server --daemonize yes >/tmp/redis.log 2>&1
sleep 1

export DATABASE_URL="postgresql://postgres@127.0.0.1:5432/main?schema=public&sslmode=disable"
export DIRECT_URL="$DATABASE_URL"
export SESSION_SECRET=2818143646516f6fffd707b36f334bbb
export MAGIC_LINK_SECRET=44da78b7bbb0dfe709cf38931d25dcdd
export ENCRYPTION_KEY=f686147ab967943ebbe9ed3b496e465a
export MANAGED_WORKER_SECRET=447c29678f9eaf289e9c4b70d3dd8a7f
export CLICKHOUSE_URL="http://default:password@127.0.0.1:8123?secure=false"
export REDIS_HOST=127.0.0.1 REDIS_PORT=6379 REDIS_TLS_DISABLED=true
export APP_ORIGIN=http://localhost:3030 LOGIN_ORIGIN=http://localhost:3030 API_ORIGIN=http://localhost:3030
export NODE_ENV=production PORT=3030 REMIX_APP_PORT=3030
# pnpm isolates transitive deps of the bundled @trigger.dev/* packages in its
# virtual-store hoist dir; expose it so the bundled server can require them.
export NODE_PATH=/app/node_modules/.pnpm/node_modules
export DEPLOY_REGISTRY_HOST=localhost:5000
export TRIGGER_TELEMETRY_DISABLED=1 INTERNAL_OTEL_TRACE_DISABLED=1

echo "=== migrate (main db) ==="
cd /app/internal-packages/database && pnpm exec prisma migrate deploy 2>&1 | tail -15

echo "=== seed ==="
cd /app/apps/webapp && SEED_LOCAL=1 pnpm run db:seed 2>&1 | tail -30

echo "=== boot webapp ==="
cd /app/apps/webapp && node build/server.js >/tmp/webapp.log 2>&1 &
for i in $(seq 1 90); do
  if curl -sf -o /dev/null http://127.0.0.1:3030/ 2>/dev/null; then echo "UP after ${i}s"; break; fi
  sleep 1
done
echo "--- webapp.log tail ---"; tail -30 /tmp/webapp.log
