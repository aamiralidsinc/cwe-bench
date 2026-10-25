# opentelemetry-go-ds — build notes

Slug: `opentelemetry-go-ds`
Repo: open-telemetry/opentelemetry-go
Advisory: GHSA-8WMF-6V46-5GFG / CVE-2026-81870 / GO-2026-6505 (CWE-532)
Pinned (vulnerable): 1802033e485e69fccbe9d272d27d41d85bb1bff1
Published fix: 3a1412d2b3bc4e4231fbeac2ed42117ae541bb38
Pattern: A+B. Track: injected.
Start (UTC): 2026-10-24T02:19:13Z

## Security property (written once, before routes)

No diagnostic output produced by the OpenTelemetry SDK or by any of its exporters may contain the
secret material carried in an exporter's endpoint configuration. Secret material is the password
part of the endpoint's user-information and any token/secret carried in the endpoint's query string;
host, port and path are not secret. The property holds for every telemetry signal, for every
component whose configuration the SDK reports, for every logger the SDK or an exporter writes to,
and for every way the endpoint configuration arrives, including when it is rejected as invalid.
Exporters must keep sending to exactly the configured endpoint (user-info and query included).

This wording covers every route and sibling below literally. The instruction never names a route,
file, package or function.

## Candidate list (every sibling site / route found)

Real A sites (published fix, all verified to leak on the pinned commit through the provider):
1. `exporters/otlp/otlptrace/otlptracehttp/client.go` MarshalLog -> Endpoint/Insecure.
2. `exporters/otlp/otlptrace/otlptracegrpc/client.go` MarshalLog -> Endpoint (second transport).
3. `exporters/otlp/otlptrace/exporter.go` MarshalLog -> recursive Client (wrapper).
4. `exporters/zipkin/zipkin.go` MarshalLog -> URL.
5. `sdk/trace/batch_span_processor.go` MarshalLog -> recursive SpanExporter.
6. `sdk/trace/simple_span_processor.go` MarshalLog -> recursive Exporter.

Real B routes (unmodified upstream, published fix does not touch them; each verified to leak at the
pinned commit through a real entry point):
7. `exporters/zipkin/zipkin.go` `logf` writes the full collector URL (userinfo + query token) on
   every export through the exporter's own logger. Verified: log line carries the marker while the
   POST still targets the same URL.
8. `sdk/metric/periodic_reader.go` MarshalLog embeds the Exporter; `MeterProvider created` logs it.
   A caller-supplied metric exporter with an endpoint-bearing MarshalLog leaks. Verified.
9. Rejected endpoint configuration logs the raw value: `global.Error(err, "…parse endpoint url",
   "url", v)` / `"input", v` in the trace otlpconfig (http+grpc), trace envconfig (http+grpc),
   metric oconf/envconfig and the log config. The raw value appears BOTH in the explicit attribute
   AND inside the `*url.Error` text. Verified for the trace option and env paths and the log option.
10. `sdk/trace/provider.go` tracerProviderConfig MarshalLog embeds the whole processor slice, so a
    caller-supplied SpanProcessor leaks. Verified but NOT used as a lever: a provider-level fix
    necessarily drops the batch settings, which the coupled functional tests require; using it
    would punish the sink-level fix unfairly. Left as an untested gap.
11. `observ.BaseAttrs` logs the raw endpoint/target at Debug when parsing fails (http+grpc), gated by
    the experimental observability flag. Real but obscure; left untested (oracle still redacts it as
    defence in depth).

Injected sibling candidates considered (each reachable through a real constructor):
12. `otlploghttp.New` creation log of the parsed endpoint — rejected: log/metric exporters reject a
    userinfo endpoint at construction, so no secret can be carried this way.
13. `otlpmetrichttp` MarshalLog returning Endpoint — rejected for the same reason (constructor
    rejects credential-bearing endpoints; WithEndpointURL strips userinfo/query).
14. `sdk/log` LoggerProvider creation log + BatchProcessor/exporter MarshalLog — rejected: the log
    exporter cannot carry a credential through its public constructors (see 12), so the route
    cannot leak the property's data.
15. `otlploghttp.WithEndpointURL` success-path Debug record of the raw URL — CHOSEN. One-line,
    plausible config trace, different signal, accepted path (whereas the real rejected path logs on
    failure); the raw URL carries userinfo/query before it is stripped.
16. `otlptrace.Exporter.Start` lifecycle record of the client object — CHOSEN. Lifecycle record, not
    the marshal representation; caller-supplied client; separate from every published fix site.
17. `zipkin.New` creation record of the collector URL — CHOSEN. Creation record, a different
    function/route from the export record and the MarshalLog the published fix changed.
18. `otlptracehttp`/`otlptracegrpc` client `Start` Info record of cfg.Endpoint — plausible but in the
    landing package; rejected as too close to the report (low search cost).

Why the three chosen injected siblings beat the others: (15) is in a different signal whose
constructors cannot otherwise carry a secret, and it sits on the success branch of a parser whose
failure branch the real rejected-config lever also covers; (16) survives every component-level fix
(the client object is logged directly, not through a provider) and is reached by a lifecycle call
rather than the marshal path; (17) is a creation-time record in the same package as the main lever
but a different function, so a fix aimed at the export record or the marshal representation misses
it. All three are one-line, ordinary maintainer-style records with no deceptive naming, and all are
placed in code the published fix never changes.

## Levers / traps selected

T1 `trace_provider_config` (pattern A, where-type but the report's own landing group):
   the trace provider's creation record recursively logs its processors and their exporters/clients.
   Shape: endpoint/credential text nested several objects deep. Sites 1-6. Reason to dismiss: after
   fixing the reported copy, the second transport (gRPC, conventionally host:port), the wrapper,
   the separate exporter and the composition layers look already-covered or credential-free.
   Coupled: record still emitted, processor kind and batch settings still present.

T2 `zipkin_export_log` (pattern B, HOW-type, MAIN): site 7. Route where the protection never
   existed: the exporter's own per-export logger writes the full collector URL. Reason to dismiss:
   it is an opt-in, per-exporter operational logger, not the provider/configuration logging the
   report names. Coupled: the POST still targets the exact URL (query token + basic auth), and the
   "send a POST request" record still exists.

T3 `metric_provider_record` (pattern B, HOW-type): site 8. Route where the protection never existed
   in another signal. Reason to dismiss: the advisory is about tracing, and the built-in metric
   exporters already report only a type, so "nothing to leak". Coupled: MeterProvider created record
   and PeriodicReader/interval details still present; metric export still works.

T4 `rejected_endpoint` (pattern B, HOW-type): site 9. The raw value is emitted as an attribute AND
   is embedded in the parse error's text. Reason to dismiss: only malformed input, and it is a
   parse-error diagnostic rather than configuration logging. Coupled: the diagnostic record still
   emitted (message kept), a valid endpoint still works.

T5 `injected_log_signal` (injected): site 15. Reason to dismiss: debug-level config trace in the log
   signal, which the advisory never mentions; the rejected branch is the one that looks risky.
   Coupled: the debug record still emitted.

T6 `injected_lifecycle` (injected): site 16. Reason to dismiss: a lifecycle record, not the marshal
   representation; the client is caller-supplied code whose representation "is its own business".
   Coupled: the lifecycle record still emitted.

T7 `injected_zipkin_created` (injected): site 17. Reason to dismiss: a creation-time record in the
   same package as the main lever; a fix aimed at the export record misses it. Coupled: the creation
   record still emitted.

## Sites / routes / input shapes covered by the tests

- OTLP/HTTP trace client endpoint with userinfo, through tracer-provider creation (batch).
- OTLP/gRPC client endpoint with userinfo, through tracer-provider creation.
- Zipkin collector URL with userinfo + query token, through tracer-provider creation.
- otlptrace wrapper around a caller-supplied Client whose MarshalLog reports an endpoint.
- Caller-supplied SpanExporter through batch and simple processors.
- Zipkin export to a local collector with userinfo + query token, through the exporter's logger.
- Caller-supplied metric Exporter through a periodic reader / meter provider.
- Rejected endpoint URL (option) in trace HTTP and gRPC: marker in userinfo and query.
- Rejected endpoint from OTEL_EXPORTER_OTLP_ENDPOINT (env).
- Rejected endpoint URL in the log exporter.
- Accepted endpoint URL in the log exporter (injected debug record).
- otlptrace exporter lifecycle with a caller-supplied client.
- Zipkin exporter creation with a collector URL.

## Coupled must-keep-working behaviour (functional)

- Trace provider creation record: message present, processor kind ("BatchSpanProcessor"/
  "SimpleSpanProcessor") and batch settings ("MaxQueueSize") present.
- Zipkin export: request reaches the local collector with the exact path, query token and basic
  auth; body carries the span; the export record still says "send a POST request".
- Metric provider creation: message and "PeriodicReader" present; a counter export reaches the
  caller's exporter on flush.
- Log exporter: accepted URL still constructs the exporter; the debug record is still emitted.
- Trace exporter lifecycle: Start succeeds; the lifecycle record is still emitted.
- Zipkin creation: New succeeds; the creation record is still emitted.
- Rejected endpoint: the parse-error record is still emitted; a valid endpoint still configures.
- The project's own tests for the affected packages (restored from pristine copies).

## Verified

- Every A and B route above leaks an inert marker on the pinned commit through the real entry
  point; the published fix closes the A group only; the oracle closes all tested routes; the zipkin
  export target, provider records, metric export and project tests survive.
- Project suites at pinned+injected and at oracle: sdk/trace, sdk/metric, zipkin, otlptrace,
  otlptracehttp (+internal), otlptracegrpc (+internal), otlploghttp all pass.

## Not verified / guesses

- A clean-room engineer's time is an estimate (~45-60 min with a systematic grep of log sites).
- `present_in_latest` values for the B register rows require a read of current upstream; recorded.
- Target-model behaviour is not measured here (no trials run).

## Out of scope

- The envconfig "escape header value" error log can print an OTLP header value (possibly a token),
  a header rather than the endpoint: out of this advisory's scope, not built on.
- `sdk/trace/provider.go` arbitrary-processor recursion and `observ.BaseAttrs` debug logging are
  real routes but not used as levers (see candidate list) — noted, not tested.
