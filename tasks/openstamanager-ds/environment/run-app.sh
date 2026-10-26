#!/usr/bin/env bash
# Start a local instance of the application for manual checks (no root required):
#   /opt/osm/run-app.sh            start the database and the web server
#   /opt/osm/run-app.sh stop       stop both
# Then browse http://127.0.0.1:8099/ . Accounts: admin / testpass (administrator),
# clerk / testpass (ordinary user).
set -u

HOME_DIR=${HOME:-/home/agent}
DATADIR=${OSM_DB_DIR:-$HOME_DIR/osm-db}
SOCK=$HOME_DIR/osm.sock
PIDFILE=$HOME_DIR/osm.pid
PORT=3307
WEBPORT=8099
ROOT=${OSM_APP_DIR:-/workspace}

stop() {
    pkill -f "php .* -S 127.0.0.1:$WEBPORT" 2>/dev/null || true
    pkill -f "mysqld .*--datadir=$DATADIR" 2>/dev/null || true
}

if [ "${1:-start}" = "stop" ]; then
    stop
    exit 0
fi

stop
sleep 1
mkdir -p "${TMPDIR:-/tmp}"

start_db() {
    mysqld --no-defaults --datadir="$DATADIR" --socket="$SOCK" --pid-file="$PIDFILE" --port="$PORT" \
        --bind-address=127.0.0.1 --skip-log-bin --sql-mode='' --innodb-flush-log-at-trx-commit=0 \
        --tmpdir="${TMPDIR:-/tmp}" \
        >/tmp/osm-db.log 2>&1 &
    for _ in $(seq 1 90); do
        mysqladmin --socket="$SOCK" -uroot ping >/dev/null 2>&1 && return 0
        sleep 1
    done
    return 1
}

mysqladmin --socket="$SOCK" -uroot ping >/dev/null 2>&1 || {
    if [ ! -d "$DATADIR/mysql" ]; then
        mkdir -p "$DATADIR"
        mysqld --no-defaults --initialize-insecure --datadir="$DATADIR" >/tmp/osm-db-init.log 2>&1 || {
            echo "database initialisation failed, see /tmp/osm-db-init.log" >&2
            exit 1
        }
        start_db || { echo "database did not start, see /tmp/osm-db.log" >&2; exit 1; }
        mysql --socket="$SOCK" -uroot -e "CREATE DATABASE osm DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;"
        zcat /opt/osm/seed.sql.gz | mysql --socket="$SOCK" -uroot osm
    else
        start_db || { echo "database did not start, see /tmp/osm-db.log" >&2; exit 1; }
    fi
}

cat > "$ROOT/config.inc.php" <<'PHPCONF'
<?php
$db_host = '127.0.0.1';
$db_username = 'root';
$db_password = '';
$db_name = 'osm';
$port = '3307';
$theme = 'default';
$redirectHTTPS = false;
$disableCSRF = true;
$debug = false;
$api_development = false;
$disable_hooks = false;
$maintenance_ip = '';
$HTMLWrapper = null;
$HTMLHandlers = [];
$HTMLManagers = [];
$lang = 'it_IT';
PHPCONF

mkdir -p "$ROOT/files/temp" "$ROOT/logs"
chmod -R u+rwX "$ROOT/files" "$ROOT/logs" 2>/dev/null || true

cd "$ROOT" || exit 1
nohup php -d display_errors=0 -d log_errors=1 -S 127.0.0.1:$WEBPORT -t "$ROOT" >/tmp/osm-web.log 2>&1 &
sleep 2
echo "application on http://127.0.0.1:$WEBPORT/ (log: /tmp/osm-web.log)"
echo "accounts: admin / testpass , clerk / testpass"
