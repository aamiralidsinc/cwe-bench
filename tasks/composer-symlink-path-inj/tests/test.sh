#!/bin/bash
# Verifier entry point. Runs the hidden tests against whatever is in /app and
# writes JUnit XML into /logs/verifier/{security,functional}/, then scores.
# Never trust test files inside /app: the agent could have edited them. Run
# only the copies under /tests.

# Stop the agent before grading. On an agent timeout Harbor stops waiting for the agent but
# does not kill it inside this shared container; in round 1 it kept editing /app while the
# tests ran (15 runs). Kill every Claude Code process first. Do not remove this block.
for _p in /proc/[0-9]*; do
  case "$(tr '\0' ' ' < "$_p/cmdline" 2>/dev/null)" in
    claude\ *|*/claude\ *|*@anthropic-ai/claude-code*) kill -9 "${_p#/proc/}" 2>/dev/null || true ;;
  esac
done
sleep 1
set -uo pipefail
mkdir -p /logs/verifier/security /logs/verifier/functional
rm -f /logs/verifier/reward.* /logs/verifier/results.json

# --- EDIT: run the two groups. Each command must write JUnit XML. Do not let a
# --- failure in one group stop the other (no `set -e`).
PHPUNIT="vendor/bin/simple-phpunit --do-not-cache-result"

# Drop pristine hidden tests into the project test tree so the project autoloader and
# bootstrap resolve (Composer\Test\ -> tests/Composer/Test/). The agent only edits /app/src.
mkdir -p /app/tests/Composer/Test/Security /app/tests/Composer/Test/Functional
cp /tests/security/*.php   /app/tests/Composer/Test/Security/
cp /tests/functional/*.php /app/tests/Composer/Test/Functional/

cd /app

# Hidden behavioural tests, each driving a real public install/download entry point.
$PHPUNIT --log-junit /logs/verifier/security/results.xml   tests/Composer/Test/Security
$PHPUNIT --log-junit /logs/verifier/functional/results.xml tests/Composer/Test/Functional

# The project's own tests for the affected area, from pristine copies shipped under /tests
# (the agent may have edited /app). They exercise the agent's product edits, not edited tests.
cp /tests/functional/project/BinaryInstallerTest.php /app/tests/Composer/Test/Installer/BinaryInstallerTest.php
cp /tests/functional/project/FileDownloaderTest.php  /app/tests/Composer/Test/Downloader/FileDownloaderTest.php
$PHPUNIT --log-junit /logs/verifier/functional/project_binary.xml   tests/Composer/Test/Installer/BinaryInstallerTest.php
$PHPUNIT --log-junit /logs/verifier/functional/project_download.xml tests/Composer/Test/Downloader/FileDownloaderTest.php

python3 /tests/score.py
