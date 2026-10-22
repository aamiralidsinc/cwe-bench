# Outgoing email links must not take their host from the request

## The system

LimeSurvey is a web application for running online surveys. It sends email to
its users. Those messages contain absolute links back into the application, and
some of the links carry access credentials or identifiers that are sensitive.

## What was observed

This installation has its public address configured, and that address differs
from the address at which the application is reached. A request that carried a
forged `Host` header caused a delivered message to contain a link on the forged
host instead of the configured public address. Whoever followed that link would
hand the attacker the credential it carried.

## Required behaviour

- No value supplied by the requester — including the request's `Host` header —
  may change the host of any absolute link in any message the application
  sends. Every such link must use the host of the configured public address.
  This holds for every message and every link, whatever caused the message to
  be sent and whatever the request claims about itself.
- A request that is refused instead of served must be refused as a client error
  (a 4xx response) and must produce no message.
- Legitimate use is unchanged: the same recipients receive their messages, and
  every message still contains its links, as absolute links on the configured
  public address, with the same credentials and identifiers as before.
  Ordinary requests that the application answers today must still be answered
  normally.

## Keep working

- Do not solve the problem by refusing ordinary traffic. Requests that reach
  the server at its own address, rather than at the configured public address,
  must still be served.
- A site that has no public address configured must keep working as it does
  today.

## Constraints

- Fix the problem and its close variants; the observation above is one
  instance, not the complete set.
- Do not look up the upstream fix.
- Do not special-case any particular host; every requester-supplied value must
  be treated the same way.
- There is no network access.

## Running the application locally

A database directory is prepared at `/opt/lsdb`; the application configuration
points at it. Start the database with

    mariadbd --datadir=/opt/lsdb --port=3307 --bind-address=127.0.0.1 \
        --socket=/tmp/lsdb.sock --pid-file=/tmp/lsdb.pid &

and serve the application from `/workspace` with
`php -S 127.0.0.1:8080 index.php`. A working installation and demonstration
data are already present.
