#!/bin/bash
# Build-time helper: prepare a ready-to-run local database in the image.
set -euo pipefail
DATADIR=/opt/lsdb
SOCK=/run/mysqld/lsdb.sock
mkdir -p "$DATADIR" /run/mysqld
chown -R mysql:mysql "$DATADIR" /run/mysqld
mariadb-install-db --user=mysql --datadir="$DATADIR" --auth-root-authentication-method=normal >/tmp/db-init.log 2>&1
nohup mariadbd --user=mysql --datadir="$DATADIR" --socket="$SOCK" --port=3307 \
    --bind-address=127.0.0.1 --pid-file=/run/mysqld/lsdb.pid >/tmp/db-run.log 2>&1 &
for _ in $(seq 1 60); do
    if mysqladmin --socket="$SOCK" ping >/dev/null 2>&1; then break; fi
    sleep 1
done
mysql --socket="$SOCK" -uroot -e "
CREATE DATABASE limesurvey DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'limesurvey'@'127.0.0.1' IDENTIFIED BY 'lspass';
GRANT ALL ON limesurvey.* TO 'limesurvey'@'127.0.0.1';
FLUSH PRIVILEGES;"
cd /workspace
cp /opt/app-config.php application/config/config.php
php application/commands/console.php install admin password "Site Admin" admin@example.org
php application/commands/console.php importsurvey tests/data/surveys/limesurvey_survey_186734.lss:en
php /opt/demo-data.php 186734
mysqladmin --socket="$SOCK" -uroot shutdown || true
sleep 2
