#!/bin/sh
# Local transport: append the raw message to a file the tests can inspect.
mkdir -p /tmp/lsmail
umask 000
cat >> "/tmp/lsmail/$(date +%s%N)-$$.eml"
