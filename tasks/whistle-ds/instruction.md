# Local debugging proxy: host files and saved data reachable without proof

## System

This project is a local developer debugging tool. A background service and an
operator-facing control surface talk to each other over a small internal
interface. The service holds the tool's saved data and can read files on the
host, and an operator can configure login for the control surface. The control
surface already relies on a specific, existing contract for proving to the
service that a request comes from the tool itself; keep that contract rather
than inventing a new one.

## Observed impact

With login configured, a caller that presented no credentials could still make
the tool return a file from the host, and a caller unknown to the tool could
make the background service return its saved data and change data on disk.

## Required property

The background service must act only on requests that prove they come from the
tool itself. Any other request must be refused, and must never cause a file on
the host to be read or its contents returned, must never create or change
anything on disk, and must never return the tool's saved data — whatever the
request asks for.

When login is configured, an unauthenticated request to the control surface
must not cause a file on the host to be read or its contents returned, however
the file is designated and whatever the request supplies. Such a request is
refused.

A credential that is present but wrong is treated exactly like one that is
absent.

## What must keep working

Every existing feature keeps working exactly as it does today for properly
authenticated operators and for the tool's components talking to one another.
A caller entitled to a file on the host or to the tool's saved data still
receives it, including by a full path and by an identifier the tool issued,
and every normal operation on the tool's saved data still succeeds for that
caller. Nothing the control surface deliberately serves without login is
affected.

"Refused" means the request ends in a client error, with no requested data in
the response and no change on disk.

These are examples, not the full set: the property holds for every operation
either interface exposes and for any value a caller might send. Fix the
reported problem and its close variants; do not special-case a particular
path, item, request or feature. Keep legitimate, authorized use working. Do
not look up the upstream project's own fix for this issue; solve it from this
repository. There is no network access.
