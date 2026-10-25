# Dashboard starts without a login after credentials were configured

The ESPHome Device Builder is a local web application for creating, editing and flashing firmware
for ESPHome devices. It serves a web UI plus an HTTP and WebSocket API on a configurable port, and
it can require a login: an operator configures a dashboard user name and password, and clients then
authenticate with HTTP Basic credentials or with a session token the dashboard issues after a
successful login. With no credentials configured the dashboard is deliberately open, which is the
normal single-user installation.

An operator who has been running the dashboard for a while keeps the environment they have always
used:

```bash
USERNAME=ops PASSWORD='<the password they have always used>' esphome-device-builder ~/esphome-configs
```

The dashboard starts, logs that it is running without authentication, and any client that can reach
the port gets the managed device inventory with no credentials at all:

```bash
curl http://dashboard-host:6052/devices
```

The old variable names are no longer consulted; only the renamed `ESPHOME_USERNAME` /
`ESPHOME_PASSWORD` variables and the command-line flags count. A configuration that still uses the
old names silently yields an unauthenticated dashboard.

## What must hold

Whenever a complete user-name/password pair is configured through any supported source, every
client-facing surface that reads or changes dashboard-managed data must require authentication, and
no request may reach such a surface without valid credentials. No credential configuration may
leave the dashboard serving unprotected: a configuration that supplies only part of a pair must
stop startup with a clear error and a non-zero exit instead of serving. A user name that the
operating system supplies by itself is not a configured credential; it must neither turn protection
on nor block a startup that has no credentials at all.

The old variable names remain supported as a fallback, and the renamed variables and the
command-line flags keep precedence over them. Authentication is HTTP Basic or a session token
issued by the dashboard, as today; a refused request gets a 4xx response and no data.

Everything that works today keeps working exactly as today: a dashboard with no credentials stays
open and usable, and a correctly supplied pair still logs clients in.

The example above is one instance, not the whole set: a complete pair supplied in any supported way
must be honoured everywhere.

Fix the problem and its close variants. Do not look up an upstream fix, and do not special-case the
example.
