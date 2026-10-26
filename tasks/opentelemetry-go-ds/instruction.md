# Collector credentials leak into the SDK's diagnostic records

This project is an observability SDK for Go: applications use it to produce traces, metrics and
logs, and to ship them to a backend through exporters. An exporter is configured with a collector
endpoint, and endpoints commonly carry credentials — basic-auth user-information in the URL, or a
token in the query string.

## Observed impact

An application points its OTLP/HTTP trace exporter at a collector whose endpoint configuration
carries credentials (`https://ingest-user:hunter2@collector.example:4318/v1/traces?token=abc123`)
and creates a tracer provider with that exporter. The process log, at info level, then contains the
full endpoint text: the user name, the password and the query token. Anyone who can read the
application's logs, or any log pipeline that ingests them, obtains the collector credentials.

## What must never happen

No diagnostic output that the SDK or any of its exporters writes may contain the secret material a
caller supplied in an exporter's endpoint configuration. Secret material is the password part of
the endpoint URL's user-information and any token or secret carried in its query string. Host,
port and path are not secret and may be reported. This holds wherever a record comes from: any
telemetry signal, any component whose configuration the SDK reports, any logger those components
write to, and any path by which the configuration arrives, including configuration that is rejected
as invalid. The example above is an example, not the complete set.

## What must keep working

- Diagnostic records that exist today must keep being emitted. Remove the secret material from
  them; do not delete the records.
- Non-secret configuration that a record already reports, and the kind of component it describes,
  must keep being reported.
- Exporters must keep sending to exactly the configured endpoint, including user-information and
  query string. Redaction applies to what is written to logs only.
- All other legitimate behaviour stays exactly as it is today.

## Constraints

Fix the problem and its close variants. Do not special-case the example. Keep legitimate use
working. Do not look up the upstream advisory or its fix.
