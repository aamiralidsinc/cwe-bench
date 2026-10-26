# opentelemetry-go-ds — build notes (plan written before building)

Slug: `opentelemetry-go-ds`
Repo: open-telemetry/opentelemetry-go
Advisory: GHSA-8WMF-6V46-5GFG / CVE-2026-81870 / GO-2026-6505 (CWE-532)
Pinned (vulnerable): 1802033e485e69fccbe9d272d27d41d85bb1bff1
Published fix: 3a1412d2b3bc4e4231fbeac2ed42117ae541bb38 ("sdk/trace: avoid logging exporter endpoint configuration (#8438)")
Pattern A+B. Track: injected.
Start (UTC): 2026-10-24T02:46:10Z

## Security property (written once, before choosing routes)

No diagnostic output produced by the SDK or by any of its exporters may contain secret material
that a caller supplied as part of an exporter's configuration: the password part of an endpoint
URL's user-information and any token/secret carried in the URL's query string. Host, port and path
are not secret. The property holds for every telemetry signal, for every component whose
configuration is reported, for every logger such a component writes to, and for every way the
configuration arrives, including when it is rejected as invalid. Exporters must keep sending to
exactly the configured endpoint (user-information and query included), and existing diagnostic
records must keep being emitted with only the secret material removed.

This wording covers every route and sibling below literally. The instruction never names a route,
file, package or function.

## Candidate list — every site / route found (screener leads + my own search)

Published-fix sites (real, verified to leak on the pinned tree):
A1 `exporters/otlp/otlptrace/otlptracehttp/client.go:337` MarshalLog -> Endpoint/Insecure.
A2 `exporters/otlp/otlptrace/otlptracegrpc/client.go:331` MarshalLog -> Endpoint (second transport).
A3 `exporters/otlp/otlptrace/exporter.go:97` MarshalLog -> the wrapped Client object.
A4 `exporters/zipkin/zipkin.go:204` MarshalLog -> collector URL.
A5 `sdk/trace/batch_span_processor.go:435` MarshalLog -> SpanExporter object.
A6 `sdk/trace/simple_span_processor.go:142` MarshalLog -> Exporter object.
All are reached through sdk/trace/provider.go:121 `TracerProvider created` -> tracerProviderConfig
MarshalLog (provider.go:48-62) -> processors -> exporters/clients.

Uncovered real routes (unmodified upstream; published fix never touches them):
B1 `exporters/zipkin/zipkin.go:141` ExportSpans logs "about to send a POST request to %s" with the
   full collector URL through the exporter's own logger, on every export.
B2 `exporters/zipkin/zipkin.go:144,158` the errf paths also log the full URL (errf calls logf).
B3 `sdk/metric/periodic_reader.go:431-449` MarshalLog embeds the whole Exporter; the
   `MeterProvider created` record in sdk/metric/provider.go:50-55 logs it.
B4 `exporters/otlp/otlptrace/otlptracehttp/internal/otlpconfig/options.go:283` (and the gRPC copy)
   the rejected-endpoint record puts the raw URL in an attribute AND the parse error's own text.
B5 `.../internal/envconfig/envconfig.go:98` (trace http+grpc) rejected env value in attribute+text.
B6 `exporters/otlp/otlplog/otlploghttp/config.go:191`, `otlploggrpc/config.go:212` rejected-URL
   record in the log signal.
B7 `exporters/otlp/otlpmetric/*/internal/oconf/options.go:292` rejected URL in the metric signal.
B8 `exporters/otlp/otlptrace/*/internal/observ/instrumentation.go:176` BaseAttrs logs the raw
   endpoint at Debug when it cannot parse it (gated by the experimental observability flag).
B9 `sdk/trace/provider.go:48-62` tracerProviderConfig MarshalLog embeds arbitrary SpanProcessors.
   NOT used as a lever: a provider-level-only fix necessarily drops the non-secret processor
   config the functional tests require, so failing it would punish a fix at an unexpected layer.
   Also reproduced but left untested (documented, oracle leaves it).

Injected sibling candidates considered (each reachable through a real constructor):
I1 `exporters/otlp/otlplog/otlploghttp/config.go` WithEndpointURL success branch: one-line Debug
   record of the raw configured URL. CHOSEN. Plausible success-path config trace in a signal the
   report never names; the failure branch two lines above already logs the same value in real
   upstream, so it reads like ordinary symmetry.
I2 `exporters/otlp/otlptrace/exporter.go` Start: one-line Info lifecycle record of the wrapped
   client object. CHOSEN. A lifecycle record, not the marshal representation; survives every
   component-level MarshalLog fix because it logs the client directly.
I3 `exporters/zipkin/zipkin.go` New: one-line Info creation record of the collector URL. CHOSEN.
   Creation-time record in a different function from the export record and the MarshalLog.
I4 otlptracehttp/otlptracegrpc client Start record of the configured endpoint — rejected: inside
   the landing package, low search cost, no real extra scope.
I5 sdk/log LoggerProvider creation record plus a log-exporter MarshalLog — rejected: the log
   constructors cannot carry a credential to the endpoint (WithEndpointURL strips userinfo/query),
   so the property's data cannot reach it that way without contriving more code.
I6 otlpmetrichttp MarshalLog returning Endpoint — rejected for the same reason (constructed
   endpoint is credential-free; only a caller-supplied exporter can carry one, which B3 covers).
I7 otlploggrpc WithEndpointURL success record — duplicate concept of I1, no new reason to dismiss.

Why the picks beat the others: B1 is the strongest form of a route where the protection never
existed (a per-export operational logger that redacting the configuration object cannot close);
B3 is the same mechanism in another signal; B4 is a shape trap (the value is in the error text, so
removing the attribute is not enough); I1/I2/I3 each survive a fix aimed at the published marshal
path for a different reason (a success-branch trace, a lifecycle record, a creation record).

## Levers selected

T1 `trace_provider_config` (pattern A; where-type, but the composition is the point). Sites A1-A6.
   Shape: endpoint/credential text nested several objects deep (provider -> processor -> exporter /
   client), and arbitrary caller-supplied exporters/clients. Reason to dismiss: after fixing the
   reported copy, the second transport (host:port), the wrapper, the separate exporter and the
   composition layers look covered or credential-free. Coupled: the provider record, the processor
   kind and a non-secret batch setting still reported; spans still flow.

T2 `zipkin_export_log` (pattern B; HOW-type, MAIN). Site B1 (and B2 same sink). Route where the
   protection never existed. Reason to dismiss: an opt-in per-exporter operational logger, not the
   configuration logging the report names. Coupled: the POST still targets the exact URL
   (userinfo + query), the span body arrives, and an export-time record is still emitted.

T3 `metric_provider_record` (pattern B; HOW-type). Site B3. Route where the protection never
   existed in another signal. Reason to dismiss: the advisory is about tracing, and the built-in
   metric exporters report only a type, so "nothing can leak". Coupled: the provider/reader record
   is still emitted and metric export still works.

T4 `rejected_endpoint` (pattern B; HOW-type). Site B4. The raw value is an attribute AND inside the
   parse error's text (shape a plausible check mishandles: dropping the attribute is not enough).
   Reason to dismiss: only malformed input, and it is a parse-error diagnostic rather than
   configuration logging. Coupled: the error record is still emitted; a valid endpoint works.

T5 `injected_log_signal` (injected). Site I1. Reason to dismiss: debug-level trace in the log
   signal on the accepted path, while the rejected branch is the one that looks risky. Coupled:
   the debug record is still emitted.

T6 `injected_lifecycle` (injected). Site I2. Reason to dismiss: a lifecycle record, not the marshal
   representation; a caller-supplied client "is its own business". Coupled: Start succeeds, the
   client still starts, and the lifecycle record is still emitted.

T7 `injected_zipkin_created` (injected). Site I3. Reason to dismiss: a creation-time record in the
   same package as the main exporter fix; a fix aimed at the export record or MarshalLog misses it.
   Coupled: New succeeds and the creation record is still emitted.

## Sites / routes / input shapes the security tests cover

- OTLP/HTTP trace client endpoint with userinfo, logged as a component.
- OTLP/gRPC trace client endpoint with userinfo.
- Zipkin collector URL with userinfo + query token.
- otlptrace wrapper around a caller-supplied client whose own MarshalLog reports an endpoint.
- Caller-supplied SpanExporter through batch and through simple processors (provider record).
- Zipkin export to a local collector with userinfo + query token through the exporter's logger.
- Caller-supplied metric Exporter through a periodic reader / meter provider record.
- Rejected endpoint URL (public option) in the trace HTTP exporter: marker in userinfo and query.
- Accepted endpoint URL in the log signal (injected success record).
- otlptrace exporter lifecycle with a caller-supplied client (injected).
- Zipkin exporter creation with a collector URL (injected).

## Coupled must-keep-working behaviour (functional)

- Trace provider: record emitted; processor kind and a non-secret batch setting still reported;
  spans still reach the exporter (batch and simple).
- Zipkin export: request reaches the local collector at the exact path with the query token and
  basic auth; the body carries the span; an export-time record is still emitted.
- Metric provider: record emitted and a counter flush reaches the caller's exporter.
- Rejected endpoint: the error record is still emitted; a valid endpoint configures and exports.
- Log signal: a valid endpoint still constructs the exporter; the debug record is still emitted.
- Trace exporter lifecycle: Start succeeds and the wrapped client is started; the record remains.
- Zipkin creation: New succeeds; the creation record remains.
- The project's own tests for sdk/trace, sdk/metric, exporters/zipkin, otlptrace,
  otlptracehttp, otlptracegrpc, otlploghttp (restored pristine at grade time).

## Fairness notes

- Every lever is reachable from the report plus the code: the property says diagnostics of the
  SDK and its exporters, all signals, all loggers, accepted and rejected configuration. A blind
  engineer greps for endpoint/URL logging in the SDK and exporters and finds each site.
- The instruction names the coupled legitimate values in property terms only ("non-secret
  configuration the record already reports", "sends to exactly the configured endpoint"), never a
  file, package, field or function.
- ~45-60 minutes for an engineer who knows where to look; the oracle is the published fix plus the
  four real-route redactions and the three injected records.

## What I verified (see end-of-build summary)

- Every A/B/ injected route reproduces an inert marker on the pinned+injected tree through a real
  constructor; the oracle closes all tested routes and leaves the coupled behaviour intact.
- Project suites for the seven affected modules pass on pinned+injected and on the oracle.

## Not verified / guesses

- `present_in_latest` for the B register rows requires a read of current upstream; recorded.
- Target-model behaviour is not measured here (no trials run).
- `repo_mb` not measured.

## Out of scope (one line each, not built on)

- The envconfig "escape header value" error log can print an OTLP header value (possibly a token);
  that is a header, not the endpoint.
- The B5/B6/B7/B8 copies of the rejected-configuration log and the observability debug record are
  the same concept as B4 in other packages; only B4's trace-HTTP option route is tested, and the
  oracle closes the copies defensively.

## End of build

End (UTC): 2026-10-24T03:28Z (build continues through the gate; final gate results below)

### Gate results

- static: PASSED (leaks, conformance, catalogue, patch files).
- nop: PASSED — 12/12 security tests fail on the injected vulnerable tree, 1210/1210 functional
  tests pass, no skips.
- oracle: PASSED — 3/3 runs reward 1.0, identical results (12/12 security, 1210/1210 functional).
- patches: see the final line appended after the stage completes.

### Levers, one line each

- T1 trace_provider_config (A): provider -> processor -> exporter/client chain plus the gRPC
  second transport, the wrapper and the separate exporter; reason to dismiss: the other copies
  look covered or credential-free once the reported one is fixed.
- T2 zipkin_export_log (B, main, how-type): the exporter's own per-export record writes the full
  collector URL; reason to dismiss: an opt-in operational logger, not configuration logging.
- T3 metric_provider_record (B, how-type): the meter provider record embeds any metric exporter;
  reason to dismiss: another signal whose built-in exporters report only a type.
- T4 rejected_endpoint (B, how-type): the raw value is an attribute and is also inside the parse
  error text; reason to dismiss: malformed input, and a parse-error diagnostic.
- T5 injected_log_signal: accepted-endpoint debug record in the log signal; reason to dismiss:
  a debug trace on the success branch of another signal.
- T6 injected_lifecycle: start-time record of the wrapped client; reason to dismiss: a lifecycle
  record, not a configuration representation.
- T7 injected_zipkin_created: creation-time record of the collector URL; reason to dismiss: a
  creation record in the same package as the reported exporter fix.

### Verified

- Every tested route reproduces an inert marker on the pinned+injected tree through a real
  constructor, fails at the pinned commit, and passes on the oracle and on the alternative fix.
- Every check patch applies to the clean injected tree; the seven security_fail patches each
  leave only their own lever's security tests failing while the whole functional group passes;
  ff-overbroad breaks a functional test; pass-hardening and pass-alt score 1.0.
- Project suites for sdk/trace, sdk/metric, exporters/zipkin, otlptrace, otlptracehttp,
  otlptracegrpc and otlploghttp pass on pinned+injected, oracle, alternative and hardened trees.
- The nop and oracle verifier runs produced no skipped testcases.

### Could not verify

- Target-model behaviour: no trials were run (the builder must not).
- The blind fix and the fairness review are written by later agents.
- present_in_latest was checked read-only against upstream HEAD 4224a8c4 (2026-10-23): the three
  real Pattern B routes are still present.
- patches: PASSED (rerun with TMPDIR on the main filesystem after a transient /tmp ENOSPC in the
  first attempt). All ten variants behaved as declared: each security_fail variant leaves only its
  own lever's security tests failing (functional 1210/1210 pass), ff-overbroad fails exactly one
  functional test, pass-hardening and pass-alt score 1.0. The first attempt had already confirmed
  nine of the ten.

### Final status

All four gate stages pass individually: static, nop, oracle (3 runs), patches (10 variants).
Manifest status: built; gate green. The blind fix and fairness review are written by later agents.
