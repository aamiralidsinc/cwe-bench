<!-- label=GHSA-8wmf-6v46-5gfg call=1 hash=bc082b3058 -->
# SYSTEM
You are a Principal Software Quality Assurance (QA) and Defensive Benchmark Architect on the maintainer side of an evaluation platform. We evaluate whether autonomous AI coding agents can correctly REPAIR real-world vulnerabilities (CVE/GHSA) that have already been fixed upstream in open-source projects.

You are provided with:
1. The historical human fix (the "reference patch")
2. The vulnerable codebase at the pre-patch commit
3. Repository maps, manifests, and test fixtures

Your responsibility is to author:
(1) `instruction.md`: A realistic, fair defect report filed by an enterprise user or security auditor.
(2) `hidden_tests.py`: A black-box pytest regression suite checking security enforcement and functional preservation.
(3) Three validation check-patches (shallow, removal, alternative) to prove the test suite accurately distinguishes good repairs from bad ones.

Operational Principles:
- Purely Defensive: All tests offline, inside an isolated container, using harmless sentinels. Tests only assert that invalid/unauthorized input is safely rejected and legitimate operations execute cleanly.
- Strict Fairness: A task is an exam of model intelligence, NOT a guessing game. Every legitimate use the functional suite tests must be an ordinary use of a FEATURE the report names as "must keep working" (name features, not test values).
- Zero Leakage: The agent must discover the faulty code and every place it lives. Never disclose file names, function names, the hidden place(s), or the scope of the bug ("every provider", "on every route").

# REQUEST
# Defect & Vulnerability Metadata
- OSV ID: GHSA-8wmf-6v46-5gfg
- CVE: CVE-2026-81870
- CWE: CWE-200, CWE-532
- Ecosystem / Package: Go / go.opentelemetry.io/otel/sdk
- Repository: https://github.com/open-telemetry/opentelemetry-go
- Official Summary: OpenTelemetry-Go: Exporter config logging may leak endpoint URLs in info logs

# Reference Patch (Historical human fix; hidden from evaluated agents)
```diff
diff --git a/CHANGELOG.md b/CHANGELOG.md
index 0991a5e1b68646b9ff687860720e84b6322f108e..7265fb0f575afa707fcfddaae95a51c4d822a57e 100644
--- a/CHANGELOG.md
+++ b/CHANGELOG.md
@@ -11,6 +11,7 @@ This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.htm
 ### Fixed
 
 - Interpret HTTP `Retry-After` header values as seconds instead of nanoseconds when retrying OTLP HTTP exports in `go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracehttp`, `go.opentelemetry.io/otel/exporters/otlp/otlpmetric/otlpmetrichttp`, `go.opentelemetry.io/otel/exporters/otlp/otlplog/otlploghttp`. (#8383)
+- Stop including trace exporter endpoint configuration in internal logs from `go.opentelemetry.io/otel/sdk/trace`, `go.opentelemetry.io/otel/exporters/otlp/otlptrace`, `go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracegrpc`, `go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracehttp`, and `go.opentelemetry.io/otel/exporters/zipkin`. (#8438)
 - Fix `go.opentelemetry.io/otel/exporters/stdout/stdouttrace` self-observability to record `error.type` on operation duration histogram when the `exportedSpans` metric is disabled. (#8432)
 
 <!-- Released section -->
diff --git a/exporters/otlp/otlptrace/exporter.go b/exporters/otlp/otlptrace/exporter.go
index 30446bd28b64f9e2e267ab74900428c5a75ed248..3c28c9c65192ec6419fc11e3e832da8d40c558ef 100644
--- a/exporters/otlp/otlptrace/exporter.go
+++ b/exporters/otlp/otlptrace/exporter.go
@@ -97,9 +97,9 @@ func NewUnstarted(client Client) *Exporter {
 func (e *Exporter) MarshalLog() any {
 	return struct {
 		Type   string
-		Client Client
+		Client string
 	}{
 		Type:   "otlptrace",
-		Client: e.client,
+		Client: fmt.Sprintf("%T", e.client),
 	}
 }
diff --git a/exporters/otlp/otlptrace/exporter_test.go b/exporters/otlp/otlptrace/exporter_test.go
index bf114e53c34967a2e7629290a349aad21004a792..b950c76f9dd2596257050d4fb9cb07971ec51200 100644
--- a/exporters/otlp/otlptrace/exporter_test.go
+++ b/exporters/otlp/otlptrace/exporter_test.go
@@ -4,10 +4,12 @@
 package otlptrace_test
 
 import (
+	"bytes"
 	"context"
 	"strings"
 	"testing"
 
+	"github.com/go-logr/logr/funcr"
 	"github.com/stretchr/testify/assert"
 	tracepb "go.opentelemetry.io/proto/otlp/trace/v1"
 
@@ -16,7 +18,8 @@ import (
 )
 
 type client struct {
-	uploadErr error
+	uploadErr   error
+	logEndpoint string
 }
 
 var _ otlptrace.Client = &client{}
@@ -33,6 +36,26 @@ func (c *client) UploadTraces(context.Context, []*tracepb.ResourceSpans) error {
 	return c.uploadErr
 }
 
+func (c *client) MarshalLog() any {
+	return struct{ Endpoint string }{Endpoint: c.logEndpoint}
+}
+
+func TestExporterMarshalLogDoesNotIncludeClientConfig(t *testing.T) {
+	const sensitiveEndpoint = "user:pass@collector.internal:4318"
+
+	var buf bytes.Buffer
+	logger := funcr.New(func(_, args string) {
+		_, _ = buf.WriteString(args)
+	}, funcr.Options{})
+
+	exp := otlptrace.NewUnstarted(&client{logEndpoint: sensitiveEndpoint})
+	logger.Info("exporter", "config", exp)
+
+	logged := buf.String()
+	assert.Contains(t, logged, "otlptrace")
+	assert.NotContains(t, logged, sensitiveEndpoint)
+}
+
 func TestExporterClientError(t *testing.T) {
 	ctx := t.Context()
 	exp, err := otlptrace.New(ctx, &client{
diff --git a/exporters/otlp/otlptrace/go.mod b/exporters/otlp/otlptrace/go.mod
index cf583f977ca18f79eb13fbfc88c95d494facbb05..508ccfeffa5f1fa3b98ac1fb1920fba8360d9599 100644
--- a/exporters/otlp/otlptrace/go.mod
+++ b/exporters/otlp/otlptrace/go.mod
@@ -3,6 +3,7 @@ module go.opentelemetry.io/otel/exporters/otlp/otlptrace
 go 1.25.0
 
 require (
+	github.com/go-logr/logr v1.4.3
 	github.com/google/go-cmp v0.7.0
 	github.com/stretchr/testify v1.11.1
 	go.opentelemetry.io/otel v1.44.0
@@ -15,7 +16,6 @@ require (
 require (
 	github.com/cespare/xxhash/v2 v2.3.0 // indirect
 	github.com/davecgh/go-spew v1.1.1 // indirect
-	github.com/go-logr/logr v1.4.3 // indirect
 	github.com/go-logr/stdr v1.2.2 // indirect
 	github.com/google/uuid v1.6.0 // indirect
 	github.com/pmezard/go-difflib v1.0.0 // indirect
diff --git a/exporters/otlp/otlptrace/otlptracegrpc/client.go b/exporters/otlp/otlptrace/otlptracegrpc/client.go
index e8b33d3fa5538d88f261f0e22b7f880ddfde8fe7..be0ce49ff0ab815d3a790f971492ebbf21b448ed 100644
--- a/exporters/otlp/otlptrace/otlptracegrpc/client.go
+++ b/exporters/otlp/otlptrace/otlptracegrpc/client.go
@@ -328,12 +328,10 @@ func throttleDelay(s *status.Status) (bool, time.Duration) {
 }
 
 // MarshalLog is the marshaling function used by the logging system to represent this Client.
-func (c *client) MarshalLog() any {
+func (*client) MarshalLog() any {
 	return struct {
-		Type     string
-		Endpoint string
+		Type string
 	}{
-		Type:     "otlptracegrpc",
-		Endpoint: c.endpoint,
+		Type: "otlptracegrpc",
 	}
 }
diff --git a/exporters/otlp/otlptrace/otlptracegrpc/client_test.go b/exporters/otlp/otlptrace/otlptracegrpc/client_test.go
index d7de61f0ae486f7e5992251a841d24fe086d93b2..6a4261d8858dbea50139f02775c94706cc124240 100644
--- a/exporters/otlp/otlptrace/otlptracegrpc/client_test.go
+++ b/exporters/otlp/otlptrace/otlptracegrpc/client_test.go
@@ -4,6 +4,7 @@
 package otlptracegrpc_test
 
 import (
+	"bytes"
 	"context"
 	"errors"
 	"fmt"
@@ -12,6 +13,7 @@ import (
 	"testing"
 	"time"
 
+	"github.com/go-logr/logr/funcr"
 	"github.com/stretchr/testify/assert"
 	"github.com/stretchr/testify/require"
 	coltracepb "go.opentelemetry.io/proto/otlp/collector/trace/v1"
@@ -48,6 +50,25 @@ func TestMain(m *testing.M) {
 
 var roSpans = tracetest.SpanStubs{{Name: "Span 0"}}.Snapshots()
 
+func TestClientMarshalLogDoesNotIncludeEndpointConfig(t *testing.T) {
+	const sensitiveEndpoint = "user:pass@collector.internal:4317"
+
+	var buf bytes.Buffer
+	logger := funcr.New(func(_, args string) {
+		_, _ = buf.WriteString(args)
+	}, funcr.Options{})
+
+	client := otlptracegrpc.NewClient(
+		otlptracegrpc.WithEndpoint(sensitiveEndpoint),
+		otlptracegrpc.WithInsecure(),
+	)
+	logger.Info("client", "config", client)
+
+	logged := buf.String()
+	assert.Contains(t, logged, "otlptracegrpc")
+	assert.NotContains(t, logged, sensitiveEndpoint)
+}
+
 func contextWithTimeout(
 	parent context.Context,
 	t *testing.T,
diff --git a/exporters/otlp/otlptrace/otlptracegrpc/go.mod b/exporters/otlp/otlptrace/otlptracegrpc/go.mod
index 8e8e1e0f4d7349f5e4e616ea8c857483dc3ae338..a8b7ee53bff607a3f70ed2db3e51217b1addf638 100644
--- a/exporters/otlp/otlptrace/otlptracegrpc/go.mod
+++ b/exporters/otlp/otlptrace/otlptracegrpc/go.mod
@@ -4,6 +4,7 @@ go 1.25.0
 
 require (
 	github.com/cenkalti/backoff/v5 v5.0.3
+	github.com/go-logr/logr v1.4.3
 	github.com/stretchr/testify v1.11.1
 	go.opentelemetry.io/otel v1.44.0
 	go.opentelemetry.io/otel/exporters/otlp/otlptrace v1.44.0
@@ -21,7 +22,6 @@ require (
 require (
 	github.com/cespare/xxhash/v2 v2.3.0 // indirect
 	github.com/davecgh/go-spew v1.1.1 // indirect
-	github.com/go-logr/logr v1.4.3 // indirect
 	github.com/go-logr/stdr v1.2.2 // indirect
 	github.com/google/uuid v1.6.0 // indirect
 	github.com/grpc-ecosystem/grpc-gateway/v2 v2.29.0 // indirect
diff --git a/exporters/otlp/otlptrace/otlptracehttp/client.go b/exporters/otlp/otlptrace/otlptracehttp/client.go
index 599537fcff3a450b0c47dafbea4444d7fe37a77c..730b9c31600bc88162127810c1965bea6523a26c 100644
--- a/exporters/otlp/otlptrace/otlptracehttp/client.go
+++ b/exporters/otlp/otlptrace/otlptracehttp/client.go
@@ -334,15 +334,11 @@ func (c *client) newRequest(body []byte) (request, error) {
 }
 
 // MarshalLog is the marshaling function used by the logging system to represent this Client.
-func (c *client) MarshalLog() any {
+func (*client) MarshalLog() any {
 	return struct {
-		Type     string
-		Endpoint string
-		Insecure bool
+		Type string
 	}{
-		Type:     "otlptracehttp",
-		Endpoint: c.cfg.Endpoint,
-		Insecure: c.cfg.Insecure,
+		Type: "otlptracehttp",
 	}
 }
 
diff --git a/exporters/otlp/otlptrace/otlptracehttp/client_internal_test.go b/exporters/otlp/otlptrace/otlptracehttp/client_internal_test.go
index a07120e922a876bb744628bb21a4f357c9c474c6..fac43a59c254f22c24011083cc58a9f1c972e05f 100644
--- a/exporters/otlp/otlptrace/otlptracehttp/client_internal_test.go
+++ b/exporters/otlp/otlptrace/otlptracehttp/client_internal_test.go
@@ -4,10 +4,12 @@
 package otlptracehttp
 
 import (
+	"bytes"
 	"net/http"
 	"testing"
 	"time"
 
+	"github.com/go-logr/logr/funcr"
 	"github.com/stretchr/testify/assert"
 )
 
@@ -16,3 +18,20 @@ func TestRetryAfterUsesSeconds(t *testing.T) {
 	_, throttle := evaluate(err)
 	assert.Equal(t, 10*time.Second, throttle)
 }
+
+func TestClientMarshalLogDoesNotIncludeEndpointConfig(t *testing.T) {
+	const sensitiveEndpoint = "user:pass@collector.internal:4318"
+
+	var buf bytes.Buffer
+	logger := funcr.New(func(_, args string) {
+		_, _ = buf.WriteString(args)
+	}, funcr.Options{})
+
+	client := NewClient(WithEndpoint(sensitiveEndpoint), WithInsecure())
+	logger.Info("client", "config", client)
+
+	logged := buf.String()
+	assert.Contains(t, logged, "otlptracehttp")
+	assert.NotContains(t, logged, sensitiveEndpoint)
+	assert.NotContains(t, logged, "Insecure")
+}
diff --git a/exporters/zipkin/zipkin.go b/exporters/zipkin/zipkin.go
index 5d9ee67b914b856b1730d82568e5edb2ca76874e..8f0fd93435cde561cfc9b1db94aebdd1d6594ea7 100644
--- a/exporters/zipkin/zipkin.go
+++ b/exporters/zipkin/zipkin.go
@@ -201,12 +201,10 @@ func (e *Exporter) errf(format string, args ...any) error {
 }
 
 // MarshalLog is the marshaling function used by the logging system to represent this Exporter.
-func (e *Exporter) MarshalLog() any {
+func (*Exporter) MarshalLog() any {
 	return struct {
 		Type string
-		URL  string
 	}{
 		Type: "zipkin",
-		URL:  e.url,
 	}
 }
diff --git a/exporters/zipkin/zipkin_test.go b/exporters/zipkin/zipkin_test.go
index 263d2eeaa1cf1d6c7293b74cd9030a7d1e8dd974..9401b68f85dac7301fa57acaaec604c6fa709883 100644
--- a/exporters/zipkin/zipkin_test.go
+++ b/exporters/zipkin/zipkin_test.go
@@ -82,6 +82,25 @@ func TestNewRawExporterCollectorURLFromEnv(t *testing.T) {
 	assert.Equal(t, expectedEndpoint, exp.url)
 }
 
+func TestExporterMarshalLogDoesNotIncludeURL(t *testing.T) {
+	const sensitiveURL = "http://user:pass@zipkin.internal:9411/api/v2/spans?token=secret"
+
+	exp, err := New(sensitiveURL)
+	require.NoError(t, err)
+
+	var buf bytes.Buffer
+	logger := funcr.New(func(_, args string) {
+		_, _ = buf.WriteString(args)
+	}, funcr.Options{})
+	logger.Info("exporter", "config", exp)
+
+	logged := buf.String()
+	assert.Contains(t, logged, "zipkin")
+	assert.NotContains(t, logged, sensitiveURL)
+	assert.NotContains(t, logged, "user:pass")
+	assert.NotContains(t, logged, "token=secret")
+}
+
 type mockZipkinCollector struct {
 	t       *testing.T
 	url     string
diff --git a/sdk/trace/batch_span_processor.go b/sdk/trace/batch_span_processor.go
index f9f2a6c2c857367377e2c565b4fbf08dba36c0fb..bc9aa808add997575b1a6aa7d6b72348e2d5e8fd 100644
--- a/sdk/trace/batch_span_processor.go
+++ b/sdk/trace/batch_span_processor.go
@@ -6,6 +6,7 @@ package trace // import "go.opentelemetry.io/otel/sdk/trace"
 import (
 	"context"
 	"errors"
+	"fmt"
 	"sync"
 	"sync/atomic"
 	"time"
@@ -435,11 +436,11 @@ func (bsp *batchSpanProcessor) enqueueDrop(ctx context.Context, sd ReadOnlySpan)
 func (bsp *batchSpanProcessor) MarshalLog() any {
 	return struct {
 		Type         string
-		SpanExporter SpanExporter
+		SpanExporter string
 		Config       BatchSpanProcessorOptions
 	}{
 		Type:         "BatchSpanProcessor",
-		SpanExporter: bsp.e,
+		SpanExporter: fmt.Sprintf("%T", bsp.e),
 		Config:       bsp.o,
 	}
 }
diff --git a/sdk/trace/provider_test.go b/sdk/trace/provider_test.go
index 4501b8b9bf73f94c18a2a302d943f60efed0a624..eb74aad519e3c6a681a571c794868ee1d184883b 100644
--- a/sdk/trace/provider_test.go
+++ b/sdk/trace/provider_test.go
@@ -4,17 +4,20 @@
 package trace
 
 import (
+	"bytes"
 	"context"
 	"errors"
 	"fmt"
 	"math/rand/v2"
 	"testing"
 
+	"github.com/go-logr/logr/funcr"
 	"github.com/stretchr/testify/assert"
 	"github.com/stretchr/testify/require"
 
 	"go.opentelemetry.io/otel"
 	"go.opentelemetry.io/otel/attribute"
+	"go.opentelemetry.io/otel/internal/global"
 	"go.opentelemetry.io/otel/metric"
 	"go.opentelemetry.io/otel/trace"
 )
@@ -57,6 +60,56 @@ func (*shutdownSpanProcessor) ForceFlush(context.Context) error {
 	return nil
 }
 
+const sensitiveExporterEndpoint = "user:pass@collector.internal:4318"
+
+type marshalingSpanExporter struct{}
+
+func (*marshalingSpanExporter) ExportSpans(context.Context, []ReadOnlySpan) error {
+	return nil
+}
+
+func (*marshalingSpanExporter) Shutdown(context.Context) error {
+	return nil
+}
+
+func (*marshalingSpanExporter) MarshalLog() any {
+	return struct{ Endpoint string }{Endpoint: sensitiveExporterEndpoint}
+}
+
+func TestTracerProviderCreatedLogDoesNotIncludeExporterConfig(t *testing.T) {
+	tests := []struct {
+		name string
+		opt  func(SpanExporter) TracerProviderOption
+	}{
+		{
+			name: "batch",
+			opt:  func(e SpanExporter) TracerProviderOption { return WithBatcher(e) },
+		},
+		{
+			name: "simple",
+			opt:  WithSyncer,
+		},
+	}
+
+	for _, tt := range tests {
+		t.Run(tt.name, func(t *testing.T) {
+			var buf bytes.Buffer
+			orig := global.GetLogger()
+			global.SetLogger(funcr.New(func(_, args string) {
+				_, _ = buf.WriteString(args)
+			}, funcr.Options{Verbosity: 4}))
+			t.Cleanup(func() { global.SetLogger(orig) })
+
+			tp := NewTracerProvider(tt.opt(&marshalingSpanExporter{}))
+			require.NoError(t, tp.Shutdown(t.Context()))
+
+			logged := buf.String()
+			assert.Contains(t, logged, "TracerProvider created")
+			assert.NotContains(t, logged, sensitiveExporterEndpoint)
+		})
+	}
+}
+
 func TestShutdownCallsTracerMethod(t *testing.T) {
 	stp := NewTracerProvider()
 	sp := &shutdownSpanProcessor{
diff --git a/sdk/trace/simple_span_processor.go b/sdk/trace/simple_span_processor.go
index 771e427a4c5c3d2c78872a5708b936f81f7bba5a..6329536c6881f015378a0ca5d1f78fe734c38426 100644
--- a/sdk/trace/simple_span_processor.go
+++ b/sdk/trace/simple_span_processor.go
@@ -5,6 +5,7 @@ package trace // import "go.opentelemetry.io/otel/sdk/trace"
 
 import (
 	"context"
+	"fmt"
 	"sync"
 	"sync/atomic"
 
@@ -140,11 +141,18 @@ func (*simpleSpanProcessor) ForceFlush(context.Context) error {
 // MarshalLog is the marshaling function used by the logging system to represent
 // this Span Processor.
 func (ssp *simpleSpanProcessor) MarshalLog() any {
+	// Shutdown clears exporter under exporterMu.
+	// Copy it while holding the same lock so MarshalLog
+	// can run concurrently without racing with Shutdown.
+	ssp.exporterMu.Lock()
+	exp := ssp.exporter
+	ssp.exporterMu.Unlock()
+
 	return struct {
 		Type     string
-		Exporter SpanExporter
+		Exporter string
 	}{
 		Type:     "SimpleSpanProcessor",
-		Exporter: ssp.exporter,
+		Exporter: fmt.Sprintf("%T", exp),
 	}
 }

Pre-Patch Source Files (Vulnerable state of files modified by patch)
### CHANGELOG.md
```
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed

- Interpret HTTP `Retry-After` header values as seconds instead of nanoseconds when retrying OTLP HTTP exports in `go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracehttp`, `go.opentelemetry.io/otel/exporters/otlp/otlpmetric/otlpmetrichttp`, `go.opentelemetry.io/otel/exporters/otlp/otlplog/otlploghttp`. (#8383)
- Fix `go.opentelemetry.io/otel/exporters/stdout/stdouttrace` self-observability to record `error.type` on operation duration histogram when the `exportedSpans` metric is disabled. (#8432)

<!-- Released section -->
<!-- Don't change this section unless doing release -->

## [1.44.0/0.66.0/0.20.0/0.0.17] 2026-05-27

### Added

- Add `ByteSlice` and `ByteSliceValue` functions for new `BYTESLICE` attribute type in `go.opentelemetry.io/otel/attribute`. (#7948)
- Apply attribute value limit to the `KindBytes` attribute type in `go.opentelemetry.io/otel/sdk/log`. (#7990)
- Apply attribute value limit to the `BYTESLICE` attribute type in `go.opentelemetry.io/otel/sdk/trace`. (#7990)
- Support `BYTESLICE` attributes in `go.opentelemetry.io/otel/trace`. (#8153)
- Support `BYTESLICE` attributes in `go.opentelemetry.io/otel/exporters/otlp/otlptrace`. (#8153)
- Support `BYTESLICE` attributes in `go.opentelemetry.io/otel/exporters/otlp/otlplog`. (#8153)
- Support `BYTESLICE` attributes in `go.opentelemetry.io/otel/exporters/otlp/otlpmetric`. (#8153)
- Support `BYTESLICE` attributes in `go.opentelemetry.io/otel/exporters/zipkin`. (#8153)
- Add `String` method for `Value` type in `go.opentelemetry.io/otel/attribute`. (#8142)
- Add `Slice` and `SliceValue` functions for new `SLICE` attribute type in `go.opentelemetry.io/otel/attribute`. (#8166)
- Support `SLICE` attributes in `go.opentelemetry.io/otel/exporters/otlp/otlptrace`. (#8216)
- Support `SLICE` attributes in `go.opentelemetry.io/otel/exporters/otlp/otlplog`. (#8216)
- Support `SLICE` attributes in `go.opentelemetry.io/otel/exporters/otlp/otlpmetric`. (#8216)
- Support `SLICE` attributes in `go.opentelemetry.io/otel/exporters/zipkin`. (#8216)
- Apply `AttributeValueLengthLimit` to `attribute.SLICE` type attribute values in `go.opentelemetry.io/otel/sdk/trace`, recursively truncating contained string values. (#8217)
- Add `Error` field on `Record` type in `go.opentelemetry.io/otel/log/logtest`. (#8148)
- Add `WithMaxRequestSize` option in `go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracegrpc`. (#8157)
- Add `WithMaxRequestSize` option in `go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracehttp`. (#8157)
- Add `WithMaxRequestSize` option in `go.opentelemetry.io/otel/exporters/otlp/otlpmetric/otlpmetricgrpc`. (#8157)
- Add `WithMaxRequestSize` option in `go.opentelemetry.io/otel/exporters/otlp/otlpmetric/otlpmetrichttp`. (#8157)
- Add `WithMaxRequestSize` option in `go.opentelemetry.io/otel/exporters/otlp/otlplog/otlploggrpc`. (#8157)
- Add `WithMaxRequestSize` option in `go.opentelemetry.io/otel/exporters/otlp/otlplog/otlploghttp`. (#8157)
- Add `Settable` to `go.opentelemetry.io/otel/metric/x` to allow reusing attribute options. (#8178)
- Add experimental support for splitting metric data across multiple batches in `go.opentelemetry.io/otel/sdk/metric`.
  Set `OTEL_GO_X_METRIC_EXPORT_BATCH_SIZE=<max_size>` to enable for all periodic readers.
  See `go.opentelemetry.io/otel/sdk/metric/internal/x` for feature documentation. (#8071)
- Add experimental self-observability metrics in `go.opentelemetry.io/otel/exporters/otlp/otlpmetric/otlpmetricgrpc`.
  Enable with `OTEL_GO_X_SELF_OBSERVABILITY=true` environment variable.
  See `go.opentelemetry.io/otel/exporters/otlp/otlpmetric/otlpmetricgrpc/internal/x` for feature documentation. (#8192)
- Add experimental self-observability metrics in `go.opentelemetry.io/otel/exporters/otlp/otlpmetric/otlpmetrichttp`.
  Enable with `OTEL_GO_X_SELF_OBSERVABILITY=true` environment variable.
  See `go.opentelemetry.io/otel/exporters/otlp/otlpmetric/otlpmetrichttp/internal/x` for feature documentation. (#8194)
- Add experimental self-observability metrics in `go.opentelemetry.io/otel/exporters/stdout/stdoutlog`.
  Enable with `OTEL_GO_X_SELF_OBSERVABILITY=true` environment variable.
  See `go.opentelemetry.io/otel/stdout/stdoutlog/internal/x` for feature documentation. (#8263)
- Add `WithDefaultAttributes` to `go.opentelemetry.io/otel/metric/x` to support setting default attributes on instruments. (#8135)
- Add `go.opentelemetry.io/otel/semconv/v1.41.0` package.
  The package contains semantic conventions from the `v1.41.0` version of the OpenTelemetry Semantic Conventions.
  See the [migration documentation](./semconv/v1.41.0/MIGRATION.md) for information on how to upgrade from `go.opentelemetry.io/otel/semconv/v1.40.0`. (#8324)
- Add Observable variants of instruments to `go.opentelemetry.io/otel/semconv/v1.41.0` package. (#8350)
- Generate explicit histogram bucket boundaries from weaver configuration for HTTP and RPC duration instruments in `go.opentelemetry.io/otel/semconv/v1.41.0`. (#8002)

### Changed

- ⚠️ **Breaking Change:** `go.opentelemetry.io/otel/sdk/metric` now applies a default cardinality limit of 2000 to comply with the Metrics SDK specification recommendation.
  New attribute sets are dropped when the cardinality limit is reached. The measurement of these sets are aggregated into a special attribute set containing `attribute.Bool("otel.metric.overflow", true)`.
  This can break users who relied on the previous unlimited default.
  Set `WithCardinalityLimit(0)` or the deprecated `OTEL_GO_X_CARDINALITY_LIMIT=0` environment variable to preserve unlimited cardinality.
  Note that support for `OTEL_GO_X_CARDINALITY_LIMIT` may be removed in a future release. (#8247)
- `ErrorType` in `go.opentelemetry.io/otel/semconv` now unwraps errors created with `fmt.Errorf` when deriving the `error.type` attribute. (#8133)
- `go.opentelemetry.io/otel/sdk/log` now unwraps error chains created with `fmt.Errorf` when deriving the `error.type` attribute from errors on log records. (#8133)
- `Set.MarshalLog` method in `go.opentelemetry.io/otel/attribute` now uses `Value.String` formatting following the [OpenTelemetry AnyValue representation for non-OTLP protocols](https://opentelemetry.io/docs/specs/otel/common/#anyvalue). (#8169)
- Optimize `go.opentelemetry.io/otel/sdk/metric` to return a drop reservoir and short-circuit `Offer` calls to the exemplar reservoir when `exemplar.AlwaysOffFilter` is configured. (#8211) (#8267)
- Optimize `go.opentelemetry.io/otel/sdk/metric` to return a drop reservoir for asynchronous instruments when `exemplar.TraceBasedFilter` is configured. (#8286)

### Deprecated

- Deprecate `Value.Emit` method in `go.opentelemetry.io/otel/attribute`.
  Use `Value.String` instead. (#8176)

### Fixed

- Limit OTLP request size to 64 MiB by default in `go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracegrpc`.
  The limit applies before compression, oversized requests are treated as non-retryable errors, and the limit can be configured with the new `WithMaxRequestSize` option. (#8157, #8365)
- Limit OTLP request size to 64 MiB by default in `go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracehttp`.
  The limit applies before compression, oversized requests are treated as non-retryable errors, and the limit can be configured with the new `WithMaxRequestSize` option. (#8157, #8365)
- Limit OTLP request size to 64 MiB by default in `go.opentelemetry.io/otel/exporters/otlp/otlpmetric/otlpmetricgrpc`.
  The limit applies before compression, oversized requests are treated as non-retryable errors, and the limit can be configured with the new `WithMaxRequestSize` option. (#8157, #8365)
- Limit OTLP request size to 64 MiB by default in `go.opentelemetry.io/otel/exporters/otlp/otlpmetric/otlpmetrichttp`.
  The limit applies before compression, oversized requests are treated as non-retryable errors, and the limit can be configured with the new `WithMaxRequestSize` option. (#8157, #8365)
- Limit OTLP request size to 64 MiB by default in `go.opentelemetry.io/otel/exporters/otlp/otlplog/otlploggrpc`.
  The limit applies before compression, oversized requests are treated as non-retryable errors, and the limit can be configured with the new `WithMaxRequestSize` option. (#8157, #8365)
- Limit OTLP request size to 64 MiB by default in `go.opentelemetry.io/otel/exporters/otlp/otlplog/otlploghttp`.
  The limit applies before compression, oversized requests are treated as non-retryable errors, and the limit can be configured with the new `WithMaxRequestSize` option. (#8157, #8365)
- Fix gzipped request body replay on redirect in `go.opentelemetry.io/otel/exporters/otlp/otlpmetric/otlpmetrichttp`. (#8135)
- Fix gzipped request body replay on redirect in `go.opentelemetry.io/otel/exporters/otlp/otlplog/otlploghttp`. (#8152)
- `go.opentelemetry.io/otel/exporters/prometheus` now uses `Value.String` formatting for label values following the [OpenTelemetry AnyValue representation for non-OTLP protocols](https://opentelemetry.io/docs/specs/otel/common/#anyvalue). (#8170)
- Propagate errors from the exporter when calling `Shutdown` on `BatchSpanProcessor` in `go.opentelemetry.io/otel/sdk/trace`. (#8197)
- Fix stale status code reporting on self-observability metrics in `go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracehttp` and `go.opentelemetry.io/otel/exporters/otlp/otlplog/otlploghttp`. (#8226)
- Fix a concurrent `Collect` data race and potential panic in `go.opentelemetry.io/otel/exporters/prometheus` when `WithResourceAsConstantLabels` option is used. (#8227)
- Fix race condition in `FixedSizeReservoir` in `go.opentelemetry.io/otel/sdk/metric/exemplar` by reverting #7447. (#8249)
- Fix `FixedSizeReservoir` in `go.opentelemetry.io/otel/sdk/metric/exemplar` to safely handle zero size.
  A capacity check in the constructor initializes the reservoir safely and skips initialization for zero-cap; early returns in `Offer()` and `Collect()` ensure no-op behavior. (#8295)
- Fix counting of spans and logs in self-observability metrics in `go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracegrpc`, `go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracehttp`, `go.opentelemetry.io/otel/exporters/otlp/otlplog/otlploggrpc`, and `go.opentelemetry.io/otel/exporters/otlp/otlplog/otlploghttp`. (#8254)
- Drop conflicting scope attributes named `name`, `version`, or `schema_url` from metric labels in `go.opentelemetry.io/otel/exporters/prometheus`, preserving the dedicated `otel_scope_name`, `otel_scope_version`, and `otel_scope_schema_url` labels. (#8264)
- Close schema files opened by `ParseFile` in `go.opentelemetry.io/otel/schema/v1.0` and `go.opentelemetry.io/otel/schema/v1.1`. ([GHSA-995v-fvrw-c78m](https://github.com/open-telemetry/opentelemetry-go/security/advisories/GHSA-995v-fvrw-c78m))
- Enforce the 8192-byte baggage size limit during extraction/parsing, changing behavior when the limit is exceeded in `go.opentelemetry.io/otel/baggage` and `go.opentelemetry.io/otel/propagation`. (#8222)
- Fix `go.opentelemetry.io/otel/semconv/v1.41.0` to include `Attr*` helper methods for required attributes on observable instruments. (#8361)
- Limit baggage extraction error reporting in `go.opentelemetry.io/otel/propagation` to prevent malformed or oversized baggage headers from flooding logs. ([GHSA-5wrp-cwcj-q835](https://github.com/open-telemetry/opentelemetry-go/security/advisories/GHSA-5wrp-cwcj-q835))

## [1.43.0/0.65.0/0.19.0] 2026-04-02

### Added

- Add `IsRandom` and `WithRandom` on `TraceFlags`, and `IsRandom` on `SpanContext` in `go.opentelemetry.io/otel/trace` for [W3C Trace Context Level 2 Random Trace ID Flag](https://www.w3.org/TR/trace-context-2/#random-trace-id-flag) support. (#8012)
- Add service detection with `WithService` in `go.opentelemetry.io/otel/sdk/resource`. (#7642)
- Add `DefaultWithContext` and `EnvironmentWithContext` in `go.opentelemetry.io/otel/sdk/resource` to support plumbing `context.Context` through default and environment detectors. (#8051)
- Support attributes with empty value (`attribute.EMPTY`) in `go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracegrpc`. (#8038)
- Support attributes with empty value (`attribute.EMPTY`) in `go.opentelemetry.io/otel/exporters/otlp/otlpmetric/otlpmetricgrpc`. (#8038)
- Support attributes with empty value (`attribute.EMPTY`) in `go.opentelemetry.io/otel/exporters/otlp/otlplog/otlploggrpc`. (#8038)
- Support attributes with empty value (`attribute.EMPTY`) in `go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracehttp`. (#8038)
- Support attributes with empty value (`attribute.EMPTY`) in `go.opentelemetry.io/otel/exporters/otlp/otlpmetric/otlpmetrichttp`. (#8038)
- Support attributes with empty value (`attribute.EMPTY`) in `go.opentelemetry.io/otel/exporters/otlp/otlplog/otlploghttp`. (#8038)
- Support attributes with empty value (`attribute.EMPTY`) in `go.opentelemetry.io/otel/sdk/metric/metricdata/metricdatatest`. (#8038)
- Add support for per-series start time tracking for cumulative metrics in `go.opentelemetry.io/otel/sdk/metric`.
  Set `OTEL_GO_X_PER_SERIES_START_TIMESTAMPS=true` to enable. (#8060)
- Add `WithCardinalityLimitSelector` for metric reader for configuring cardinality limits specific to the instrument kind. (#7855)

### Changed

- Introduce the `EMPTY` Type in `go.opentelemetry.io/otel/attribute` to reflect that an empty value is now a valid value, with `INVALID` remaining as a deprecated alias of `EMPTY`. (#8038)
- Improve slice handling in `go.opentelemetry.io/otel/attribute` to optimize short slice values with fixed-size fast paths. (#8039)
- Improve performance of span metric recording in `go.opentelemetry.io/otel/sdk/trace` by returning early if self-observability is not enabled. (#8067)
- Improve formatting of metric data diffs in `go.opentelemetry.io/otel/sdk/metric/metricdata/metricdatatest`. (#8073)

### Deprecated

- Deprecate `INVALID` in `go.opentelemetry.io/otel/attribute`. Use `EMPTY` instead. (#8038)

### Fixed

- Return spec-compliant `TraceIdRatioBased` description. This is a breaking behavioral change, but it is necessary to
  make the implementation [spec-compliant](https://opentelemetry.io/docs/specs/otel/trace/sdk/#traceidratiobased). (#8027)
- Fix a race condition in `go.opentelemetry.io/otel/sdk/metric` where the lastvalue aggregation could collect the value 0 even when no zero-value measurements were recorded. (#8056)
- Limit HTTP response body to 4 MiB in `go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracehttp` to mitigate excessive memory usage caused by a misconfigured or malicious server.
  Responses exceeding the limit are treated as non-retryable errors. (#8108)
- Limit HTTP response body to 4 MiB in `go.opentelemetry.io/otel/exporters/otlp/otlpmetric/otlpmetrichttp` to mitigate excessive memory usage caused by a misconfigured or malicious server.
  Responses exceeding the limit are treated as non-retryable errors. (#8108)
- Limit HTTP response body to 4 MiB in `go.opentelemetry.io/otel/exporters/otlp/otlplog/otlploghttp` to mitigate excessive memory usage caused by a misconfigured or malicious server.
  Responses exceeding the limit are treated as non-retryable errors. (#8108)
- `WithHostID` detector in `go.opentelemetry.io/otel/sdk/resource` to use full path for `kenv` command on BSD. (#8113)
- Fix missing `request.GetBody` in `go.opentelemetry.io/otel/exporters/otlp/otlplog/otlploghttp` to correctly handle HTTP2 GOAWAY frame. (#8096)

## [1.42.0/0.64.0/0.18.0/0.0.16] 2026-03-06

### Added

- Add `go.opentelemetry.io/otel/semconv/v1.40.0` package.
  The package contains semantic conventions from the `v1.40.0` version of the OpenTelemetry Semantic Conventions.
  See the [migration documentation](./semconv/v1.40.0/MIGRATION.md) for information on how to upgrade from `go.opentelemetry.io/otel/semconv/v1.39.0`. (#7985)
- Add `Err` and `SetErr` on `Record` in `go.opentelemetry.io/otel/log` to attach an error and set record exception attributes in `go.opentelemetry.io/otel/log/sdk`. (#7924)

### Changed

- `TracerProvider.ForceFlush` in `go.opentelemetry.io/otel/sdk/trace` joins errors together and continues iteration through SpanProcessors as opposed to returning the first encountered error without attempting exports on subsequent SpanProcessors. (#7856)

### Fixed

- Fix missing `request.GetBody` in `go.opentelemetry.io/otel/exporters/otlp/otlpmetric/otlpmetrichttp` to correctly handle HTTP2 GOAWAY frame. (#7931)
- Fix semconv v1.39.0 generated metric helpers skipping required attributes when extra attributes were empty. (#7964)
- Preserve W3C TraceFlags bitmask (including the random Trace ID flag) during trace context extraction and injection in `go.opentelemetry.io/otel/propagation`. (#7834)

### Removed

- Drop support for [Go 1.24]. (#7984)

## [1.41.0/0.63.0/0.17.0/0.0.15] 2026-03-02

This release is the last to support [Go 1.24].
The next release will require at least [Go 1.25].

### Added

- Support testing of [Go 1.26]. (#7902)

### Fixed

- Update `Baggage` in `go.opentelemetry.io/otel/propagation` and `Parse` and `New` in `go.opentelemetry.io/otel/baggage` to comply with W3C Baggage specification limits.
  `New` and `Parse` now return partial baggage along with an error when limits are exceeded.
  Errors from baggage extraction are reported to the global error handler. (#7880)
- Return an error when the endpoint is configured as insecure and with TLS configuration in `go.opentelemetry.io/otel/exporters/otlp/otlplog/otlploghttp`. (#7914)
- Return an error when the endpoint is configured as insecure and with TLS configuration in `go.opentelemetry.io/otel/exporters/otlp/otlpmetric/otlpmetrichttp`. (#7914)
- Return an error when the endpoint is configured as insecure and with TLS configuration in `go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracehttp`. (#7914)

## [1.40.0/0.62.0/0.16.0] 2026-02-02

### Added

- Add `AlwaysRecord` sampler in `go.opentelemetry.io/otel/sdk/trace`. (#7724)
- Add `Enabled` method to all synchronous instrument interfaces (`Float64Counter`, `Float64UpDownCounter`, `Float64Histogram`, `Float64Gauge`, `Int64Counter`, `Int64UpDownCounter`, `Int64Histogram`, `Int64Gauge`,) in `go.opentelemetry.io/otel/metric`.
  This stabilizes the synchronous instrument enabled feature, allowing users to check if an instrument will process measurements before performing computationally expensive operations. (#7763)
- Add `go.opentelemetry.io/otel/semconv/v1.39.0` package.
  The package contains semantic conventions from the `v1.39.0` version of the OpenTelemetry Semantic Conventions.
  See the [migration documentation](./semconv/v1.39.0/MIGRATION.md) for information on how to upgrade from `go.opentelemetry.io/otel/semconv/v1.38.0.` (#7783, #7789)

### Changed

- Improve the concurrent performance of `HistogramReservoir` in `go.opentelemetry.io/otel/sdk/metric/exemplar` by 4x. (#7443)
- Improve the concurrent performance of `FixedSizeReservoir` in `go.opentelemetry.io/otel/sdk/metric/exemplar`. (#7447)
- Improve performance of concurrent histogram measurements in `go.opentelemetry.io/otel/sdk/metric`. (#7474)
- Improve performance of concurrent synchronous gauge measurements in `go.opentelemetry.io/otel/sdk/metric`. (#7478)
- Add experimental observability metrics in `go.opentelemetry.io/otel/exporters/stdout/stdoutmetric`. (#7492)
- `Exporter` in `go.opentelemetry.io/otel/exporters/prometheus` ignores metrics with the scope `go.opentelemetry.io/contrib/bridges/prometheus`.
  This prevents scrape failures when the Prometheus exporter is misconfigured to get data from the Prometheus bridge. (#7688)
- Improve performance of concurrent exponential histogram measurements in `go.opentelemetry.io/otel/sdk/metric`. (#7702)
- The `rpc.grpc.status_code` attribute in the experimental metrics emitted from `go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracegrpc` is replaced with the `rpc.response.status_code` attribute to align with the semantic conventions. (#7854)
- The `rpc.grpc.status_code` attribute in the experimental metrics emitted from `go.opentelemetry.io/otel/exporters/otlp/otlplog/otlploggrpc` is replaced with the `rpc.response.status_code` attribute to align with the semantic conventions. (#7854)

### Fixed

- Fix bad log message when key-value pairs are dropped because of key duplication in `go.opentelemetry.io/otel/sdk/log`. (#7662)
- Fix `DroppedAttributes` on `Record` in `go.opentelemetry.io/otel/sdk/log` to not count the non-attribute key-value pairs dropped because of key duplication. (#7662)
- Fix `SetAttributes` on `Record` in `go.opentelemetry.io/otel/sdk/log` to not log that attributes are dropped when they are actually not dropped. (#7662)
- Fix missing `request.GetBody` in `go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracehttp` to correctly handle HTTP/2 `GOAWAY` frame. (#7794)
- `WithHostID` detector in `go.opentelemetry.io/otel/sdk/resource` to use full path for `ioreg` command on Darwin (macOS). (#7818)

### Deprecated

- Deprecate `go.opentelemetry.io/otel/exporters/zipkin`.
  For more information, see the [OTel blog post deprecating the Zipkin exporter](https://opentelemetry.io/blog/2025/deprecating-zipkin-exporters/). (#7670)

## [1.39.0/0.61.0/0.15.0/0.0.14] 2025-12-05

### Added

- Greatly reduce the cost of recording metrics in `go.opentelemetry.io/otel/sdk/metric` using hashing for map keys. (#7175)
- Add `WithInstrumentationAttributeSet` option to `go.opentelemetry.io/otel/log`, `go.opentelemetry.io/otel/metric`, and `go.opentelemetry.io/otel/trace` packages.
  This provides a concurrent-safe and performant alternative to `WithInstrumentationAttributes` by accepting a pre-constructed `attribute.Set`. (#7287)
- Add experimental observability for the Prometheus exporter in `go.opentelemetry.io/otel/exporters/prometheus`.
  Check the `go.opentelemetry.io/otel/exporters/prometheus/internal/x` package documentation for more information. (#7345)
- Add experimental observability metrics in `go.opentelemetry.io/otel/exporters/otlp/otlplog/otlploggrpc`. (#7353)
- Add temporality selector functions `DeltaTemporalitySelector`, `CumulativeTemporalitySelector`, `LowMemoryTemporalitySelector` to `go.opentelemetry.io/otel/sdk/metric`. (#7434)
- Add experimental observability metrics for simple log processor in `go.opentelemetry.io/otel/sdk/log`. (#7548)
- Add experimental observability metrics in `go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracegrpc`. (#7459)
- Add experimental observability metrics in `go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracehttp`. (#7486)
- Add experimental observability metrics for simple span processor in `go.opentelemetry.io/otel/sdk/trace`. (#7374)
- Add experimental observability metrics in `go.opentelemetry.io/otel/exporters/otlp/otlplog/otlploghttp`. (#7512)
- Add experimental observability metrics for manual reader in `go.opentelemetry.io/otel/sdk/metric`. (#7524)
- Add experimental observability metrics for periodic reader in `go.opentelemetry.io/otel/sdk/metric`. (#7571)
- Support `OTEL_EXPORTER_OTLP_LOGS_INSECURE` and `OTEL_EXPORTER_OTLP_INSECURE` environmental variables in `go.opentelemetry.io/otel/exporters/otlp/otlplog/otlploghttp`. (#7608)
- Add `Enabled` method to the `Processor` interface in `go.opentelemetry.io/otel/sdk/log`.
  All `Processor` implementations now include an `Enabled` method. (#7639)
- The `go.opentelemetry.io/otel/semconv/v1.38.0` package.
  The package contains semantic conventions from the `v1.38.0` version of the OpenTelemetry Semantic Conventions.
  See the [migration documentation](./semconv/v1.38.0/MIGRATION.md) for information on how to upgrade from `go.opentelemetry.io/otel/semconv/v1.37.0.`(#7648)

### Changed

- `Distinct` in `go.opentelemetry.io/otel/attribute` is no longer guaranteed to uniquely identify an attribute set.
  Collisions between `Distinct` values for different Sets are possible with extremely high cardinality (billions of series per instrument), but are highly unlikely. (#7175)
- `WithInstrumentationAttributes` in `go.opentelemetry.io/otel/trace` synchronously de-duplicates the passed attributes instead of delegating it to the returned `TracerOption`. (#7266)
- `WithInstrumentationAttributes` in `go.opentelemetry.io/otel/meter` synchronously de-duplicates the passed attributes instead of delegating it to the returned `MeterOption`. (#7266)
- `WithInstrumentationAttributes` in `go.opentelemetry.io/otel/log` synchronously de-duplicates the passed attributes instead of delegating it to the returned `LoggerOption`. (#7266)
- Rename the `OTEL_GO_X_SELF_OBSERVABILITY` environment variable to `OTEL_GO_X_OBSERVABILITY` in `go.opentelemetry.io/otel/sdk/trace`, `go.opentelemetry.io/otel/sdk/log`, and `go.opentelemetry.io/otel/exporters/stdout/stdouttrace`. (#7302)
- Improve performance of histogram `Record` in `go.opentelemetry.io/otel/sdk/metric` when min and max are disabled using `NoMinMax`. (#7306)
- Improve error handling for dropped data during translation by using `prometheus.NewInvalidMetric` in `go.opentelemetry.io/otel/exporters/prometheus`.
  ⚠️ **Breaking Change:** Previously, these cases were only logged and scrapes succeeded.
  Now, when translation would drop data (e.g., invalid label/value), the exporter emits a `NewInvalidMetric`, and Prometheus scrapes **fail with HTTP 500** by default.
  To preserve the prior behavior (scrapes succeed while errors are logged), configure your Prometheus HTTP handler with: `promhttp.HandlerOpts{ ErrorHandling: promhttp.ContinueOnError }`. (#7363)
- Replace fnv hash with xxhash in `go.opentelemetry.io/otel/attribute` for better performance. (#7371)
- The default `TranslationStrategy` in `go.opentelemetry.io/exporters/prometheus` is changed from `otlptranslator.NoUTF8EscapingWithSuffixes` to `otlptranslator.UnderscoreEscapingWithSuffixes`. (#7421)
- Improve performance of concurrent measurements in `go.opentelemetry.io/otel/sdk/metric`. (#7427)
- Include W3C TraceFlags (bits 0–7) in the OTLP `Span.Flags` field in `go.opentelemetry.io/exporters/otlp/otlptrace/otlptracehttp` and `go.opentelemetry.io/exporters/otlp/otlptrace/otlptracegrpc`. (#7438)
- The `ErrorType` function in `go.opentelemetry.io/otel/semconv/v1.37.0` now handles custom error types.
  If an error implements an `ErrorType() string` method, the return value of that method will be used as the error type. (#7442)

### Fixed

- Fix `WithInstrumentationAttributes` options in `go.opentelemetry.io/otel/trace`, `go.opentelemetry.io/otel/metric`, and `go.opentelemetry.io/otel/log` to properly merge attributes when passed multiple times instead of replacing them.
  Attributes with duplicate keys will use the last value passed. (#7300)
- The equality of `attribute.Set` when using the `Equal` method is not affected by the user overriding the empty set pointed to by `attribute.EmptySet` in `go.opentelemetry.io/otel/attribute`. (#7357)
- Return partial OTLP export errors to the caller in `go.opentelemetry.io/otel/exporters/otlp/otlplog/otlploggrpc`. (#7372)
- Return partial OTLP export errors to the caller in `go.opentelemetry.io/otel/exporters/otlp/otlplog/otlploghttp`. (#7372)
- Return partial OTLP export errors to the caller in `go.opentelemetry.io/otel/exporters/otlp/otlpmetric/otlpmetricgrpc`. (#7372)
- Return partial OTLP export errors to the caller in `go.opentelemetry.io/otel/exporters/otlp/otlpmetric/otlpmetrichttp`. (#7372)
- Return partial OTLP export errors to the caller in `go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracegrpc`. (#7372)
- Return partial OTLP export errors to the caller in `go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracehttp`. (#7372)
- Fix `AddAttributes`, `SetAttributes`, `SetBody` on `Record` in `go.opentelemetry.io/otel/sdk/log` to not mutate input. (#7403)
- Do not double record measurements of `RecordSet` methods in `go.opentelemetry.io/otel/semconv/v1.37.0`. (#7655)
- Do not double record measurements of `RecordSet` methods in `go.opentelemetry.io/otel/semconv/v1.36.0`. (#7656)

### Removed

- Drop support for [Go 1.23]. (#7274)
- Remove the `FilterProcessor` interface in `go.opentelemetry.io/otel/sdk/log`.
  The `Enabled` method has been added to the `Processor` interface instead.
  All `Processor` implementations must now implement the `Enabled` method.
  Custom processors that do not filter records can implement `Enabled` to return `true`. (#7639)

## [1.38.0/0.60.0/0.14.0/0.0.13] 2025-08-29

This release is the last to support [Go 1.23].
The next release will require at least [Go 1.24].

### Added

- Add native histogram exemplar support in `go.opentelemetry.io/otel/exporters/prometheus`. (#6772)
- Add template attribute functions to the `go.opentelmetry.io/otel/semconv/v1.34.0` package. (#6939)
  - `ContainerLabel`
  - `DBOperationParameter`
  - `DBSystemParameter`
  - `HTTPRequestHeader`
  - `HTTPResponseHeader`
  - `K8SCronJobAnnotation`
  - `K8SCronJobLabel`
  - `K8SDaemonSetAnnotation`
  - `K8SDaemonSetLabel`
  - `K8SDeploymentAnnotation`
  - `K8SDeploymentLabel`
  - `K8SJobAnnotation`
  - `K8SJobLabel`
  - `K8SNamespaceAnnotation`
  - `K8SNamespaceLabel`
  - `K8SNodeAnnotation`
  - `K8SNodeLabel`
  - `K8SPodAnnotation`
  - `K8SPodLabel`
  - `K8SReplicaSetAnnotation`
  - `K8SReplicaSetLabel`
  - `K8SStatefulSetAnnotation`
  - `K8SStatefulSetLabel`
  - `ProcessEnvironmentVariable`
  - `RPCConnectRPCRequestMetadata`
  - `RPCConnectRPCResponseMetadata`
  - `RPCGRPCRequestMetadata`
  - `RPCGRPCResponseMetadata`
- Add `ErrorType` attribute helper function to the `go.opentelmetry.io/otel/semconv/v1.34.0` package. (#6962)
- Add `WithAllowKeyDuplication` in `go.opentelemetry.io/otel/sdk/log` which can be used to disable deduplication for log records. (#6968)
- Add `WithCardinalityLimit` option to configure the cardinality limit in `go.opentelemetry.io/otel/sdk/metric`. (#6996, #7065, #7081, #7164, #7165, #7179)
- Add `Clone` method to `Record` in `go.opentelemetry.io/otel/log` that returns a copy of the record with no shared state. (#7001)
- Add experimental self-observability span and batch span processor metrics in `go.opentelemetry.io/otel/sdk/trace`.
  Check the `go.opentelemetry.io/otel/sdk/trace/internal/x` package documentation for more information. (#7027, #6393, #7209)
- The `go.opentelemetry.io/otel/semconv/v1.36.0` package.
  The package contains semantic conventions from the `v1.36.0` version of the OpenTelemetry Semantic Conventions.
  See the [migration documentation](./semconv/v1.36.0/MIGRATION.md) for information on how to upgrade from `go.opentelemetry.io/otel/semconv/v1.34.0.`(#7032, #7041)
- Add support for configuring Prometheus name translation using `WithTranslationStrategy` option in `go.opentelemetry.io/otel/exporters/prometheus`. The current default translation strategy when UTF-8 mode is enabled is `NoUTF8EscapingWithSuffixes`, but a future release will change the default strategy to `UnderscoreEscapingWithSuffixes` for compliance with the specification. (#7111)
- Add experimental self-observability log metrics in `go.opentelemetry.io/otel/sdk/log`.
  Check the `go.opentelemetry.io/otel/sdk/log/internal/x` package documentation for more information. (#7121)
- Add experimental self-observability trace exporter metrics in `go.opentelemetry.io/otel/exporters/stdout/stdouttrace`.
  Check the `go.opentelemetry.io/otel/exporters/stdout/stdouttrace/internal/x` package documentation for more information. (#7133)
- Support testing of [Go 1.25]. (#7187)
- The `go.opentelemetry.io/otel/semconv/v1.37.0` package.
  The package contains semantic conventions from the `v1.37.0` version of the OpenTelemetry Semantic Conventions.
  See the [migration documentation](./semconv/v1.37.0/MIGRATION.md) for information on how to upgrade from `go.opentelemetry.io/otel/semconv/v1.36.0.`(#7254)

### Changed

- Optimize `TraceIDFromHex` and `SpanIDFromHex` in `go.opentelemetry.io/otel/sdk/trace`. (#6791)
- Change `AssertEqual` in `go.opentelemetry.io/otel/log/logtest` to accept `TestingT` in order to support benchmarks and fuzz tests. (#6908)
- Change `DefaultExemplarReservoirProviderSelector` in `go.opentelemetry.io/otel/sdk/metric` to use `runtime.GOMAXPROCS(0)` instead of `runtime.NumCPU()` for the `FixedSizeReservoirProvider` default size. (#7094)

### Fixed

- `SetBody` method of `Record` in `go.opentelemetry.io/otel/sdk/log` now deduplicates key-value collections (`log.Value` of `log.KindMap` from `go.opentelemetry.io/otel/log`). (#7002)
- Fix `go.opentelemetry.io/otel/exporters/prometheus` to not append a suffix if it's already present in metric name. (#7088)
- Fix the `go.opentelemetry.io/otel/exporters/stdout/stdouttrace` self-observability component type and name. (#7195)
- Fix partial export count metric in `go.opentelemetry.io/otel/exporters/stdout/stdouttrace`. (#7199)

### Deprecated

- Deprecate `WithoutUnits` and `WithoutCounterSuffixes` options, preferring `WithTranslationStrategy` instead. (#7111)
- Deprecate support for `OTEL_GO_X_CARDINALITY_LIMIT` environment variable in `go.opentelemetry.io/otel/sdk/metric`. Use `WithCardinalityLimit` option instead. (#7166)

## [0.59.1] 2025-07-21

### Changed

- Retract `v0.59.0` release of `go.opentelemetry.io/otel/exporters/prometheus` module which appends incorrect unit suffixes. (#7046)
- Change `go.opentelemetry.io/otel/exporters/prometheus` to no longer deduplicate suffixes when UTF8 is enabled.
  It is recommended to disable unit and counter suffixes in the exporter, and manually add suffixes if you rely on the existing behavior. (#7044)

### Fixed

- Fix `go.opentelemetry.io/otel/exporters/prometheus` to properly handle unit suffixes when the unit is in brackets.
  E.g. `{spans}`. (#7044)

## [1.37.0/0.59.0/0.13.0] 2025-06-25

### Added

- The `go.opentelemetry.io/otel/semconv/v1.33.0` package.
  The package contains semantic conventions from the `v1.33.0` version of the OpenTelemetry Semantic Conventions.
  See the [migration documentation](./semconv/v1.33.0/MIGRATION.md) for information on how to upgrade from `go.opentelemetry.io/otel/semconv/v1.32.0.`(#6799)
- The `go.opentelemetry.io/otel/semconv/v1.34.0` package.
  The package contains semantic conventions from the `v1.34.0` version of the OpenTelemetry Semantic Conventions. (#6812)
- Add metric's schema URL as `otel_scope_schema_url` label in `go.opentelemetry.io/otel/exporters/prometheus`. (#5947)
- Add metric's scope attributes as `otel_scope_[attribute]` labels in `go.opentelemetry.io/otel/exporters/prometheus`. (#5947)
- Add `EventName` to `EnabledParameters` in `go.opentelemetry.io/otel/log`. (#6825)
- Add `EventName` to `EnabledParameters` in `go.opentelemetry.io/otel/sdk/log`. (#6825)
- Changed handling of `go.opentelemetry.io/otel/exporters/prometheus` metric renaming to add unit suffixes when it doesn't match one of the pre-defined values in the unit suffix map. (#6839)

### Changed

- The semantic conventions have been upgraded from `v1.26.0` to `v1.34.0` in `go.opentelemetry.io/otel/bridge/opentracing`. (#6827)
- The semantic conventions have been upgraded from `v1.26.0` to `v1.34.0` in `go.opentelemetry.io/otel/exporters/zipkin`. (#6829)
- The semantic conventions have been upgraded from `v1.26.0` to `v1.34.0` in `go.opentelemetry.io/otel/metric`. (#6832)
- The semantic conventions have been upgraded from `v1.26.0` to `v1.34.0` in `go.opentelemetry.io/otel/sdk/resource`. (#6834)
- The semantic conventions have been upgraded from `v1.26.0` to `v1.34.0` in `go.opentelemetry.io/otel/sdk/trace`. (#6835)
- The semantic conventions have been upgraded from `v1.26.0` to `v1.34.0` in `go.opentelemetry.io/otel/trace`. (#6836)
- `Record.Resource` now returns `*resource.Resource` instead of `resource.Resource` in `go.opentelemetry.io/otel/sdk/log`. (#6864)
- Retry now shows error cause for context timeout in `go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracegrpc`, `go.opentelemetry.io/otel/exporters/otlp/otlpmetric/otlpmetricgrpc`, `go.opentelemetry.io/otel/exporters/otlp/otlplog/otlploggrpc`, `go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracehttp`, `go.opentelemetry.io/otel/exporters/otlp/otlpmetric/otlpmetrichttp`, `go.opentelemetry.io/otel/exporters/otlp/otlplog/otlploghttp`. (#6898)

### Fixed

- Stop stripping trailing slashes from configured endpoint URL in `go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracegrpc`. (#6710)
- Stop stripping trailing slashes from configured endpoint URL in `go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracehttp`. (#6710)
- Stop stripping trailing slashes from configured endpoint URL in `go.opentelemetry.io/otel/exporters/otlp/otlpmetric/otlpmetricgrpc`. (#6710)
- Stop stripping trailing slashes from configured endpoint URL in `go.opentelemetry.io/otel/exporters/otlp/otlpmetric/otlpmetrichttp`. (#6710)
- Validate exponential histogram scale range for Prometheus compatibility in `go.opentelemetry.io/otel/exporters/prometheus`. (#6822)
- Context cancellation during metric pipeline produce does not corrupt data in `go.opentelemetry.io/otel/sdk/metric`. (#6914)

### Removed

- `go.opentelemetry.io/otel/exporters/prometheus` no longer exports `otel_scope_info` metric. (#6770)

## [0.12.2] 2025-05-22

### Fixed

- Retract `v0.12.0` release of `go.opentelemetry.io/otel/exporters/otlp/otlplog/otlploggrpc` module that contains invalid dependencies. (#6804)
- Retract `v0.12.0` release of `go.opentelemetry.io/otel/exporters/otlp/otlplog/otlploghttp` module that contains invalid dependencies. (#6804)
- Retract `v0.12.0` release of `go.opentelemetry.io/otel/exporters/stdout/stdoutlog` module that contains invalid dependencies. (#6804)

## [0.12.1] 2025-05-21

### Fixes

- Use the proper dependency version of `go.opentelemetry.io/otel/sdk/log/logtest` in `go.opentelemetry.io/otel/exporters/otlp/otlplog/otlploggrpc`. (#6800)
- Use the proper dependency version of `go.opentelemetry.io/otel/sdk/log/logtest` in `go.opentelemetry.io/otel/exporters/otlp/otlplog/otlploghttp`. (#6800)
- Use the proper dependency version of `go.opentelemetry.io/otel/sdk/log/logtest` in `go.opentelemetry.io/otel/exporters/stdout/stdoutlog`. (#6800)

## [1.36.0/0.58.0/0.12.0] 2025-05-20

### Added

- Add exponential histogram support in `go.opentelemetry.io/otel/exporters/prometheus`. (#6421)
- The `go.opentelemetry.io/otel/semconv/v1.31.0` package.
  The package contains semantic conventions from the `v1.31.0` version of the OpenTelemetry Semantic Conventions.
  See the [migration documentation](./semconv/v1.31.0/MIGRATION.md) for information on how to upgrade from `go.opentelemetry.io/otel/semconv/v1.30.0`. (#6479)
- Add `Recording`, `Scope`, and `Record` types in `go.opentelemetry.io/otel/log/logtest`. (#6507)
- Add `WithHTTPClient` option to configure the `http.Client` used by `go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracehttp`. (#6751)
- Add `WithHTTPClient` option to configure the `http.Client` used by `go.opentelemetry.io/otel/exporters/otlp/otlpmetric/otlpmetrichttp`. (#6752)
- Add `WithHTTPClient` option to configure the `http.Client` used by `go.opentelemetry.io/otel/exporters/otlp/otlplog/otlploghttp`. (#6688)
- Add `ValuesGetter` in `go.opentelemetry.io/otel/propagation`, a `TextMapCarrier` that supports retrieving multiple values for a single key. (#5973)
- Add `Values` method to `HeaderCarrier` to implement the new `ValuesGetter` interface in `go.opentelemetry.io/otel/propagation`. (#5973)
- Update `Baggage` in `go.opentelemetry.io/otel/propagation` to retrieve multiple values for a key when the carrier implements `ValuesGetter`. (#5973)
- Add `AssertEqual` function in `go.opentelemetry.io/otel/log/logtest`. (#6662)
- The `go.ope
... [truncated, file is 280427 chars]
```

### exporters/otlp/otlptrace/exporter.go
```
// Copyright The OpenTelemetry Authors
// SPDX-License-Identifier: Apache-2.0

package otlptrace // import "go.opentelemetry.io/otel/exporters/otlp/otlptrace"

import (
	"context"
	"errors"
	"fmt"
	"sync"

	"go.opentelemetry.io/otel/exporters/otlp/otlptrace/internal/tracetransform"
	tracesdk "go.opentelemetry.io/otel/sdk/trace"
)

var errAlreadyStarted = errors.New("already started")

// Exporter exports trace data in the OTLP wire format.
type Exporter struct {
	client Client

	mu      sync.RWMutex
	started bool

	startOnce sync.Once
	stopOnce  sync.Once
}

// ExportSpans exports a batch of spans.
func (e *Exporter) ExportSpans(ctx context.Context, ss []tracesdk.ReadOnlySpan) error {
	protoSpans := tracetransform.Spans(ss)
	if len(protoSpans) == 0 {
		return nil
	}

	err := e.client.UploadTraces(ctx, protoSpans)
	if err != nil {
		return fmt.Errorf("traces export: %w", err)
	}
	return nil
}

// Start establishes a connection to the receiving endpoint.
func (e *Exporter) Start(ctx context.Context) error {
	err := errAlreadyStarted
	e.startOnce.Do(func() {
		e.mu.Lock()
		e.started = true
		e.mu.Unlock()
		err = e.client.Start(ctx)
	})

	return err
}

// Shutdown flushes all exports and closes all connections to the receiving endpoint.
func (e *Exporter) Shutdown(ctx context.Context) error {
	e.mu.RLock()
	started := e.started
	e.mu.RUnlock()

	if !started {
		return nil
	}

	var err error

	e.stopOnce.Do(func() {
		err = e.client.Stop(ctx)
		e.mu.Lock()
		e.started = false
		e.mu.Unlock()
	})

	return err
}

var _ tracesdk.SpanExporter = (*Exporter)(nil)

// New constructs a new Exporter and starts it.
func New(ctx context.Context, client Client) (*Exporter, error) {
	exp := NewUnstarted(client)
	if err := exp.Start(ctx); err != nil {
		return nil, err
	}
	return exp, nil
}

// NewUnstarted constructs a new Exporter and does not start it.
func NewUnstarted(client Client) *Exporter {
	return &Exporter{
		client: client,
	}
}

// MarshalLog is the marshaling function used by the logging system to represent this Exporter.
func (e *Exporter) MarshalLog() any {
	return struct {
		Type   string
		Client Client
	}{
		Type:   "otlptrace",
		Client: e.client,
	}
}

```

### exporters/otlp/otlptrace/go.mod
```
module go.opentelemetry.io/otel/exporters/otlp/otlptrace

go 1.25.0

require (
	github.com/google/go-cmp v0.7.0
	github.com/stretchr/testify v1.11.1
	go.opentelemetry.io/otel v1.44.0
	go.opentelemetry.io/otel/sdk v1.44.0
	go.opentelemetry.io/otel/trace v1.44.0
	go.opentelemetry.io/proto/otlp v1.10.0
	google.golang.org/protobuf v1.36.11
)

require (
	github.com/cespare/xxhash/v2 v2.3.0 // indirect
	github.com/davecgh/go-spew v1.1.1 // indirect
	github.com/go-logr/logr v1.4.3 // indirect
	github.com/go-logr/stdr v1.2.2 // indirect
	github.com/google/uuid v1.6.0 // indirect
	github.com/pmezard/go-difflib v1.0.0 // indirect
	go.opentelemetry.io/auto/sdk v1.2.1 // indirect
	go.opentelemetry.io/otel/metric v1.44.0 // indirect
	golang.org/x/sys v0.46.0 // indirect
	gopkg.in/yaml.v3 v3.0.1 // indirect
)

replace go.opentelemetry.io/otel => ../../..

replace go.opentelemetry.io/otel/sdk => ../../../sdk

replace go.opentelemetry.io/otel/trace => ../../../trace

replace go.opentelemetry.io/otel/metric => ../../../metric

replace go.opentelemetry.io/otel/sdk/metric => ../../../sdk/metric

replace go.opentelemetry.io/otel/metric/x => ../../../metric/x

```

### exporters/otlp/otlptrace/otlptracegrpc/client.go
```
// Copyright The OpenTelemetry Authors
// SPDX-License-Identifier: Apache-2.0

package otlptracegrpc // import "go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracegrpc"

import (
	"context"
	"errors"
	"fmt"
	"sync"
	"time"

	coltracepb "go.opentelemetry.io/proto/otlp/collector/trace/v1"
	tracepb "go.opentelemetry.io/proto/otlp/trace/v1"
	"google.golang.org/genproto/googleapis/rpc/errdetails"
	"google.golang.org/grpc"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/metadata"
	"google.golang.org/grpc/status"
	"google.golang.org/protobuf/proto"

	"go.opentelemetry.io/otel/exporters/otlp/otlptrace"
	"go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracegrpc/internal"
	"go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracegrpc/internal/counter"
	"go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracegrpc/internal/observ"
	"go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracegrpc/internal/otlpconfig"
	"go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracegrpc/internal/retry"
)

type client struct {
	endpoint       string
	dialOpts       []grpc.DialOption
	metadata       metadata.MD
	exportTimeout  time.Duration
	maxRequestSize int
	requestFunc    retry.RequestFunc

	// stopCtx is used as a parent context for all exports. Therefore, when it
	// is canceled with the stopFunc all exports are canceled.
	stopCtx context.Context
	// stopFunc cancels stopCtx, stopping any active exports.
	stopFunc context.CancelFunc

	// ourConn keeps track of where conn was created: true if created here on
	// Start, or false if passed with an option. This is important on Shutdown
	// as the conn should only be closed if created here on start. Otherwise,
	// it is up to the processes that passed the conn to close it.
	ourConn bool
	conn    *grpc.ClientConn
	tscMu   sync.RWMutex
	tsc     coltracepb.TraceServiceClient

	instID int64
	inst   *observ.Instrumentation
}

// Compile time check *client implements otlptrace.Client.
var _ otlptrace.Client = (*client)(nil)

// NewClient creates a new gRPC trace client.
func NewClient(opts ...Option) otlptrace.Client {
	return newClient(opts...)
}

func newClient(opts ...Option) *client {
	cfg := otlpconfig.NewGRPCConfig(asGRPCOptions(opts)...)

	ctx, cancel := context.WithCancel(context.Background()) //nolint:gosec  // cancel called in client shutdown.

	c := &client{
		endpoint:       cfg.Traces.Endpoint,
		exportTimeout:  cfg.Traces.Timeout,
		maxRequestSize: cfg.Traces.MaxRequestSize,
		requestFunc:    cfg.RetryConfig.RequestFunc(retryable),
		dialOpts:       cfg.DialOptions,
		stopCtx:        ctx,
		stopFunc:       cancel,
		conn:           cfg.GRPCConn,
		instID:         counter.NextExporterID(),
	}

	if len(cfg.Traces.Headers) > 0 {
		c.metadata = metadata.New(cfg.Traces.Headers)
	}

	return c
}

// Start establishes a gRPC connection to the collector.
func (c *client) Start(context.Context) error {
	if c.conn == nil {
		// If the caller did not provide a ClientConn when the client was
		// created, create one using the configuration they did provide.
		conn, err := grpc.NewClient(c.endpoint, c.dialOpts...)
		if err != nil {
			return err
		}
		// Keep track that we own the lifecycle of this conn and need to close
		// it on Shutdown.
		c.ourConn = true
		c.conn = conn
	}

	// Initialize the instrumentation if not already done.
	//
	// Initialize here instead of NewClient to allow any errors to be passed
	// back to the caller and so that any setup of the environment variables to
	// enable instrumentation can be set via code.
	var err error
	if c.inst == nil {
		target := c.conn.CanonicalTarget()
		c.inst, err = observ.NewInstrumentation(c.instID, target)
	}

	// The otlptrace.Client interface states this method is called just once,
	// so no need to check if already started.
	c.tscMu.Lock()
	c.tsc = coltracepb.NewTraceServiceClient(c.conn)
	c.tscMu.Unlock()

	return err
}

var errAlreadyStopped = errors.New("the client is already stopped")

// Stop shuts down the client.
//
// Any active connections to a remote endpoint are closed if they were created
// by the client. Any gRPC connection passed during creation using
// WithGRPCConn will not be closed. It is the caller's responsibility to
// handle cleanup of that resource.
//
// This method synchronizes with the UploadTraces method of the client. It
// will wait for any active calls to that method to complete unimpeded, or it
// will cancel any active calls if ctx expires. If ctx expires, the context
// error will be forwarded as the returned error. All client held resources
// will still be released in this situation.
//
// If the client has already stopped, an error will be returned describing
// this.
func (c *client) Stop(ctx context.Context) error {
	// Make sure to return context error if the context is done when calling this method.
	err := ctx.Err()

	// Acquire the c.tscMu lock within the ctx lifetime.
	acquired := make(chan struct{})
	go func() {
		c.tscMu.Lock()
		close(acquired)
	}()

	select {
	case <-ctx.Done():
		// The Stop timeout is reached. Kill any remaining exports to force
		// the clear of the lock and save the timeout error to return and
		// signal the shutdown timed out before cleanly stopping.
		c.stopFunc()
		err = ctx.Err()

		// To ensure the client is not left in a dirty state c.tsc needs to be
		// set to nil. To avoid the race condition when doing this, ensure
		// that all the exports are killed (initiated by c.stopFunc).
		<-acquired
	case <-acquired:
	}
	// Hold the tscMu lock for the rest of the function to ensure no new
	// exports are started.
	defer c.tscMu.Unlock()

	// The otlptrace.Client interface states this method is called only
	// once, but there is no guarantee it is called after Start. Ensure the
	// client is started before doing anything and let the called know if they
	// made a mistake.
	if c.tsc == nil {
		return errAlreadyStopped
	}

	// Clear c.tsc to signal the client is stopped.
	c.tsc = nil

	if c.ourConn {
		closeErr := c.conn.Close()
		// A context timeout error takes precedence over this error.
		if err == nil && closeErr != nil {
			err = closeErr
		}
	}
	return err
}

var errShutdown = errors.New("the client is shutdown")

// UploadTraces sends a batch of spans.
//
// Retryable errors from the server will be handled according to any
// RetryConfig the client was created with.
func (c *client) UploadTraces(ctx context.Context, protoSpans []*tracepb.ResourceSpans) (uploadErr error) {
	// Hold a read lock to ensure a shut down initiated after this starts does
	// not abandon the export. This read lock acquire has less priority than a
	// write lock acquire (i.e. Stop), meaning if the client is shutting down
	// this will come after the shut down.
	c.tscMu.RLock()
	defer c.tscMu.RUnlock()

	if c.tsc == nil {
		return errShutdown
	}

	ctx, cancel := c.exportContext(ctx)
	defer cancel()

	pbRequest := &coltracepb.ExportTraceServiceRequest{
		ResourceSpans: protoSpans,
	}

	code := codes.Unknown
	if c.inst != nil {
		var spanCount int
		for _, rs := range protoSpans {
			for _, ss := range rs.ScopeSpans {
				spanCount += len(ss.Spans)
			}
		}
		op := c.inst.ExportSpans(ctx, spanCount)
		defer func() { op.End(uploadErr, code) }()
	}

	if maxSize := c.maxRequestSize; maxSize > 0 && proto.Size(pbRequest) > maxSize {
		return fmt.Errorf("request message too large: exceeded %d bytes", maxSize)
	}

	return c.requestFunc(ctx, func(iCtx context.Context) error {
		resp, err := c.tsc.Export(iCtx, pbRequest)
		if resp != nil && resp.PartialSuccess != nil {
			msg := resp.PartialSuccess.GetErrorMessage()
			n := resp.PartialSuccess.GetRejectedSpans()
			if n != 0 || msg != "" {
				e := internal.TracePartialSuccessError(n, msg)
				uploadErr = errors.Join(uploadErr, e)
			}
		}
		// nil is converted to OK.
		code = status.Code(err)
		if code == codes.OK {
			// Success.
			return uploadErr
		}
		return errors.Join(uploadErr, err)
	})
}

// exportContext returns a copy of parent with an appropriate deadline and
// cancellation function.
//
// It is the callers responsibility to cancel the returned context once its
// use is complete, via the parent or directly with the returned CancelFunc, to
// ensure all resources are correctly released.
func (c *client) exportContext(parent context.Context) (context.Context, context.CancelFunc) {
	var (
		ctx    context.Context
		cancel context.CancelFunc
	)

	if c.exportTimeout > 0 {
		ctx, cancel = context.WithTimeoutCause(parent, c.exportTimeout, errors.New("exporter export timeout"))
	} else {
		ctx, cancel = context.WithCancel(parent) //nolint:gosec  // cancel called by caller when export is complete.
	}

	if c.metadata.Len() > 0 {
		md := c.metadata
		if outMD, ok := metadata.FromOutgoingContext(ctx); ok {
			md = metadata.Join(md, outMD)
		}

		ctx = metadata.NewOutgoingContext(ctx, md)
	}

	// Unify the client stopCtx with the parent.
	go func() {
		select {
		case <-ctx.Done():
		case <-c.stopCtx.Done():
			// Cancel the export as the shutdown has timed out.
			cancel()
		}
	}()

	return ctx, cancel
}

// retryable returns if err identifies a request that can be retried and a
// duration to wait for if an explicit throttle time is included in err.
func retryable(err error) (bool, time.Duration) {
	s := status.Convert(err)
	return retryableGRPCStatus(s)
}

func retryableGRPCStatus(s *status.Status) (bool, time.Duration) {
	switch s.Code() {
	case codes.Canceled,
		codes.DeadlineExceeded,
		codes.Aborted,
		codes.OutOfRange,
		codes.Unavailable,
		codes.DataLoss:
		// Additionally handle RetryInfo.
		_, d := throttleDelay(s)
		return true, d
	case codes.ResourceExhausted:
		// Retry only if the server signals that the recovery from resource exhaustion is possible.
		return throttleDelay(s)
	}

	// Not a retry-able error.
	return false, 0
}

// throttleDelay returns of the status is RetryInfo
// and the its duration to wait for if an explicit throttle time.
func throttleDelay(s *status.Status) (bool, time.Duration) {
	for _, detail := range s.Details() {
		if t, ok := detail.(*errdetails.RetryInfo); ok {
			return true, t.RetryDelay.AsDuration()
		}
	}
	return false, 0
}

// MarshalLog is the marshaling function used by the logging system to represent this Client.
func (c *client) MarshalLog() any {
	return struct {
		Type     string
		Endpoint string
	}{
		Type:     "otlptracegrpc",
		Endpoint: c.endpoint,
	}
}

```

### exporters/otlp/otlptrace/otlptracegrpc/go.mod
```
module go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracegrpc

go 1.25.0

require (
	github.com/cenkalti/backoff/v5 v5.0.3
	github.com/stretchr/testify v1.11.1
	go.opentelemetry.io/otel v1.44.0
	go.opentelemetry.io/otel/exporters/otlp/otlptrace v1.44.0
	go.opentelemetry.io/otel/metric v1.44.0
	go.opentelemetry.io/otel/sdk v1.44.0
	go.opentelemetry.io/otel/sdk/metric v1.44.0
	go.opentelemetry.io/otel/trace v1.44.0
	go.opentelemetry.io/proto/otlp v1.10.0
	go.uber.org/goleak v1.3.0
	google.golang.org/genproto/googleapis/rpc v0.0.0-20260608224507-4308a22a1bab
	google.golang.org/grpc v1.81.1
	google.golang.org/protobuf v1.36.11
)

require (
	github.com/cespare/xxhash/v2 v2.3.0 // indirect
	github.com/davecgh/go-spew v1.1.1 // indirect
	github.com/go-logr/logr v1.4.3 // indirect
	github.com/go-logr/stdr v1.2.2 // indirect
	github.com/google/uuid v1.6.0 // indirect
	github.com/grpc-ecosystem/grpc-gateway/v2 v2.29.0 // indirect
	github.com/pmezard/go-difflib v1.0.0 // indirect
	go.opentelemetry.io/auto/sdk v1.2.1 // indirect
	golang.org/x/net v0.55.0 // indirect
	golang.org/x/sys v0.46.0 // indirect
	golang.org/x/text v0.38.0 // indirect
	google.golang.org/genproto/googleapis/api v0.0.0-20260608224507-4308a22a1bab // indirect
	gopkg.in/yaml.v3 v3.0.1 // indirect
)

replace go.opentelemetry.io/otel => ../../../..

replace go.opentelemetry.io/otel/sdk => ../../../../sdk

replace go.opentelemetry.io/otel/exporters/otlp/otlptrace => ../

replace go.opentelemetry.io/otel/trace => ../../../../trace

replace go.opentelemetry.io/otel/metric => ../../../../metric

replace go.opentelemetry.io/otel/sdk/metric => ../../../../sdk/metric

replace go.opentelemetry.io/otel/metric/x => ../../../../metric/x

```

### exporters/otlp/otlptrace/otlptracehttp/client.go
```
// Copyright The OpenTelemetry Authors
// SPDX-License-Identifier: Apache-2.0

package otlptracehttp // import "go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracehttp"

import (
	"bytes"
	"compress/gzip"
	"context"
	"errors"
	"fmt"
	"io"
	"net"
	"net/http"
	"net/url"
	"strconv"
	"strings"
	"sync"
	"time"

	coltracepb "go.opentelemetry.io/proto/otlp/collector/trace/v1"
	tracepb "go.opentelemetry.io/proto/otlp/trace/v1"
	"google.golang.org/protobuf/proto"

	"go.opentelemetry.io/otel/exporters/otlp/otlptrace"
	"go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracehttp/internal"
	"go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracehttp/internal/counter"
	"go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracehttp/internal/observ"
	"go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracehttp/internal/otlpconfig"
	"go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracehttp/internal/retry"
)

const contentTypeProto = "application/x-protobuf"

// maxResponseBodySize is the maximum number of bytes to read from a response
// body. It is set to 4 MiB per the OTLP specification recommendation to
// mitigate excessive memory usage caused by a misconfigured or malicious
// server. If exceeded, the response is treated as a not-retryable error.
// This is a variable to allow tests to override it.
var maxResponseBodySize int64 = 4 * 1024 * 1024

var gzPool = sync.Pool{
	New: func() any {
		w := gzip.NewWriter(io.Discard)
		return w
	},
}

// Keep it in sync with golang's DefaultTransport from net/http! We
// have our own copy to avoid handling a situation where the
// DefaultTransport is overwritten with some different implementation
// of http.RoundTripper or it's modified by other package.
var ourTransport = &http.Transport{
	Proxy: http.ProxyFromEnvironment,
	DialContext: (&net.Dialer{
		Timeout:   30 * time.Second,
		KeepAlive: 30 * time.Second,
	}).DialContext,
	ForceAttemptHTTP2:     true,
	MaxIdleConns:          100,
	IdleConnTimeout:       90 * time.Second,
	TLSHandshakeTimeout:   10 * time.Second,
	ExpectContinueTimeout: 1 * time.Second,
}

var errInsecureEndpointWithTLS = errors.New("insecure HTTP endpoint cannot use TLS client configuration")

type client struct {
	name        string
	cfg         otlpconfig.SignalConfig
	generalCfg  otlpconfig.Config
	requestFunc retry.RequestFunc
	client      *http.Client
	stopCh      chan struct{}
	stopOnce    sync.Once

	instID int64
	inst   *observ.Instrumentation
}

var _ otlptrace.Client = (*client)(nil)

// NewClient creates a new HTTP trace client.
func NewClient(opts ...Option) otlptrace.Client {
	cfg := otlpconfig.NewHTTPConfig(asHTTPOptions(opts)...)

	httpClient := cfg.Traces.HTTPClient

	if httpClient == nil {
		httpClient = &http.Client{
			Transport: ourTransport,
			Timeout:   cfg.Traces.Timeout,
		}

		if cfg.Traces.TLSCfg != nil || cfg.Traces.Proxy != nil {
			clonedTransport := ourTransport.Clone()
			httpClient.Transport = clonedTransport

			if cfg.Traces.TLSCfg != nil {
				clonedTransport.TLSClientConfig = cfg.Traces.TLSCfg
			}
			if cfg.Traces.Proxy != nil {
				clonedTransport.Proxy = cfg.Traces.Proxy
			}
		}
	}

	stopCh := make(chan struct{})
	return &client{
		name:        "traces",
		cfg:         cfg.Traces,
		generalCfg:  cfg,
		requestFunc: cfg.RetryConfig.RequestFunc(evaluate),
		stopCh:      stopCh,
		client:      httpClient,
		instID:      counter.NextExporterID(),
	}
}

// Start does nothing in a HTTP client.
func (c *client) Start(ctx context.Context) error {
	if c.cfg.Insecure && c.cfg.TLSCfg != nil {
		return errInsecureEndpointWithTLS
	}

	// Initialize the instrumentation if not already done.
	//
	// Initialize here instead of NewClient to allow any errors to be passed
	// back to the caller and so that any setup of the environment variables to
	// enable instrumentation can be set via code.
	var err error
	if c.inst == nil {
		c.inst, err = observ.NewInstrumentation(c.instID, c.cfg.Endpoint)
	}

	// nothing to do
	select {
	case <-ctx.Done():
		err = errors.Join(err, ctx.Err())
	default:
	}
	return err
}

// Stop shuts down the client and interrupt any in-flight request.
func (c *client) Stop(ctx context.Context) error {
	c.stopOnce.Do(func() {
		close(c.stopCh)
	})
	select {
	case <-ctx.Done():
		return ctx.Err()
	default:
	}
	return nil
}

// UploadTraces sends a batch of spans to the collector.
func (c *client) UploadTraces(ctx context.Context, protoSpans []*tracepb.ResourceSpans) (uploadErr error) {
	pbRequest := &coltracepb.ExportTraceServiceRequest{
		ResourceSpans: protoSpans,
	}
	rawRequest, err := proto.Marshal(pbRequest)
	if err != nil {
		return err
	}

	ctx, cancel := c.contextWithStop(ctx)
	defer cancel()

	if maxSize := c.cfg.MaxRequestSize; maxSize > 0 && len(rawRequest) > maxSize {
		return fmt.Errorf("request body too large: exceeded %d bytes", maxSize)
	}

	request, err := c.newRequest(rawRequest)
	if err != nil {
		return err
	}

	var statusCode int
	if c.inst != nil {
		var spanCount int
		for _, rs := range protoSpans {
			for _, ss := range rs.ScopeSpans {
				spanCount += len(ss.Spans)
			}
		}
		op := c.inst.ExportSpans(ctx, spanCount)
		defer func() { op.End(uploadErr, statusCode) }()
	}

	return errors.Join(uploadErr, c.requestFunc(ctx, func(ctx context.Context) error {
		select {
		case <-ctx.Done():
			return ctx.Err()
		default:
		}

		statusCode = 0
		request.reset(ctx)
		// nolint:gosec // URL is constructed from validated OTLP endpoint configuration
		resp, err := c.client.Do(request.Request)
		var urlErr *url.Error
		if errors.As(err, &urlErr) && urlErr.Temporary() {
			return newResponseError(http.Header{}, err)
		}
		if err != nil {
			return err
		}

		if resp != nil && resp.Body != nil {
			defer func() {
				if err := resp.Body.Close(); err != nil {
					uploadErr = errors.Join(uploadErr, err)
				}
			}()
		}

		statusCode = resp.StatusCode
		if statusCode >= 200 && statusCode <= 299 {
			// Success, do not retry.
			// Read the partial success message, if any.
			var respData bytes.Buffer
			if _, err := io.Copy(&respData, http.MaxBytesReader(nil, resp.Body, maxResponseBodySize)); err != nil {
				var maxBytesErr *http.MaxBytesError
				if errors.As(err, &maxBytesErr) {
					return fmt.Errorf("response body too large: exceeded %d bytes", maxBytesErr.Limit)
				}
				return err
			}
			if respData.Len() == 0 {
				return nil
			}

			if resp.Header.Get("Content-Type") == "application/x-protobuf" {
				var respProto coltracepb.ExportTraceServiceResponse
				if err := proto.Unmarshal(respData.Bytes(), &respProto); err != nil {
					return err
				}

				if respProto.PartialSuccess != nil {
					msg := respProto.PartialSuccess.GetErrorMessage()
					n := respProto.PartialSuccess.GetRejectedSpans()
					if n != 0 || msg != "" {
						err := internal.TracePartialSuccessError(n, msg)
						uploadErr = errors.Join(uploadErr, err)
					}
				}
			}
			return nil
		}
		// Error cases.

		// server may return a message with the response
		// body, so we read it to include in the error
		// message to be returned. It will help in
		// debugging the actual issue.
		var respData bytes.Buffer
		if _, err := io.Copy(&respData, http.MaxBytesReader(nil, resp.Body, maxResponseBodySize)); err != nil {
			var maxBytesErr *http.MaxBytesError
			if errors.As(err, &maxBytesErr) {
				return fmt.Errorf("response body too large: exceeded %d bytes", maxBytesErr.Limit)
			}
			return err
		}
		respStr := strings.TrimSpace(respData.String())
		if respStr == "" {
			respStr = "(empty)"
		}
		bodyErr := fmt.Errorf("body: %s", respStr)

		switch statusCode {
		case http.StatusTooManyRequests,
			http.StatusBadGateway,
			http.StatusServiceUnavailable,
			http.StatusGatewayTimeout:
			// Retryable failure.
			return newResponseError(resp.Header, bodyErr)
		default:
			// Non-retryable failure.
			return fmt.Errorf("failed to send to %s: %s (%w)", request.URL, resp.Status, bodyErr)
		}
	}))
}

func (c *client) newRequest(body []byte) (request, error) {
	u := url.URL{Scheme: c.getScheme(), Host: c.cfg.Endpoint, Path: c.cfg.URLPath}
	r, err := http.NewRequestWithContext(context.Background(), http.MethodPost, u.String(), http.NoBody)
	if err != nil {
		return request{Request: r}, err
	}

	userAgent := "OTel OTLP Exporter Go/" + otlptrace.Version()
	r.Header.Set("User-Agent", userAgent)

	for k, v := range c.cfg.Headers {
		r.Header.Set(k, v)
	}
	r.Header.Set("Content-Type", contentTypeProto)

	req := request{Request: r}
	switch Compression(c.cfg.Compression) {
	case NoCompression:
		r.ContentLength = int64(len(body))
		req.bodyReader = bodyReader(body)
		req.GetBody = bodyReaderErr(body)
	case GzipCompression:
		// Ensure the content length is not used.
		r.ContentLength = -1
		r.Header.Set("Content-Encoding", "gzip")

		gz := gzPool.Get().(*gzip.Writer)
		defer func() {
			gz.Reset(io.Discard)
			gzPool.Put(gz)
		}()

		var b bytes.Buffer
		gz.Reset(&b)

		if _, err := gz.Write(body); err != nil {
			return req, err
		}
		// Close needs to be called to ensure body is fully written.
		if err := gz.Close(); err != nil {
			return req, err
		}

		req.bodyReader = bodyReader(b.Bytes())
		req.GetBody = bodyReaderErr(b.Bytes())
	}

	return req, nil
}

// MarshalLog is the marshaling function used by the logging system to represent this Client.
func (c *client) MarshalLog() any {
	return struct {
		Type     string
		Endpoint string
		Insecure bool
	}{
		Type:     "otlptracehttp",
		Endpoint: c.cfg.Endpoint,
		Insecure: c.cfg.Insecure,
	}
}

// bodyReader returns a closure returning a new reader for buf.
func bodyReader(buf []byte) func() io.ReadCloser {
	return func() io.ReadCloser {
		return io.NopCloser(bytes.NewReader(buf))
	}
}

// bodyReaderErr returns a closure returning a new reader for buf.
func bodyReaderErr(buf []byte) func() (io.ReadCloser, error) {
	return func() (io.ReadCloser, error) {
		return io.NopCloser(bytes.NewReader(buf)), nil
	}
}

// request wraps an http.Request with a resettable body reader.
type request struct {
	*http.Request

	// bodyReader allows the same body to be used for multiple requests.
	bodyReader func() io.ReadCloser
}

// reset reinitializes the request Body and uses ctx for the request.
func (r *request) reset(ctx context.Context) {
	r.Body = r.bodyReader()
	r.Request = r.WithContext(ctx)
}

// retryableError represents a request failure that can be retried.
type retryableError struct {
	throttle time.Duration
	err      error
}

// newResponseError returns a retryableError and will extract any explicit
// throttle delay contained in headers. The returned error wraps wrapped
// if it is not nil.
func newResponseError(header http.Header, wrapped error) error {
	var rErr retryableError
	if s, ok := header["Retry-After"]; ok {
		if t, err := strconv.ParseInt(s[0], 10, 64); err == nil {
			rErr.throttle = time.Duration(t) * time.Second
		}
	}

	rErr.err = wrapped
	return rErr
}

func (e retryableError) Error() string {
	if e.err != nil {
		return "retry-able request failure: " + e.err.Error()
	}

	return "retry-able request failure"
}

func (e retryableError) Unwrap() error {
	return e.err
}

func (e retryableError) As(target any) bool {
	if e.err == nil {
		return false
	}

	switch v := target.(type) {
	case **retryableError:
		*v = &e
		return true
	default:
		return false
	}
}

// evaluate returns if err is retry-able. If it is and it includes an explicit
// throttling delay, that delay is also returned.
func evaluate(err error) (bool, time.Duration) {
	if err == nil {
		return false, 0
	}

	// Do not use errors.As here, this should only be flattened one layer. If
	// there are several chained errors, all the errors above it will be
	// discarded if errors.As is used instead.
	rErr, ok := err.(retryableError) //nolint:errorlint
	if !ok {
		return false, 0
	}

	return true, rErr.throttle
}

func (c *client) getScheme() string {
	if c.cfg.Insecure {
		return "http"
	}
	return "https"
}

func (c *client) contextWithStop(ctx context.Context) (context.Context, context.CancelFunc) {
	// Unify the parent context Done signal with the client's stop
	// channel.
	ctx, cancel := context.WithCancel(ctx)
	go func(ctx context.Context, cancel context.CancelFunc) {
		select {
		case <-ctx.Done():
			// Nothing to do, either cancelled or deadline
			// happened.
		case <-c.stopCh:
			cancel()
		}
	}(ctx, cancel)
	return ctx, cancel
}

```

### exporters/zipkin/zipkin.go
```
// Copyright The OpenTelemetry Authors
// SPDX-License-Identifier: Apache-2.0

package zipkin // import "go.opentelemetry.io/otel/exporters/zipkin"

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"net/url"
	"strings"
	"sync"

	"github.com/go-logr/logr"
	"github.com/go-logr/stdr"

	sdktrace "go.opentelemetry.io/otel/sdk/trace"
)

const (
	defaultCollectorURL = "http://localhost:9411/api/v2/spans"
)

// Exporter exports spans to the zipkin collector.
type Exporter struct {
	url     string
	client  *http.Client
	logger  logr.Logger
	headers map[string]string

	stoppedMu sync.RWMutex
	stopped   bool
}

var _ sdktrace.SpanExporter = &Exporter{}

var emptyLogger = logr.Logger{}

// Options contains configuration for the exporter.
type config struct {
	client  *http.Client
	logger  logr.Logger
	headers map[string]string
}

// Option defines a function that configures the exporter.
type Option interface {
	apply(config) config
}

type optionFunc func(config) config

func (fn optionFunc) apply(cfg config) config {
	return fn(cfg)
}

// WithLogger configures the exporter to use the passed logger.
// WithLogger and WithLogr will overwrite each other.
func WithLogger(logger *log.Logger) Option {
	return WithLogr(stdr.New(logger))
}

// WithLogr configures the exporter to use the passed logr.Logger.
// WithLogr and WithLogger will overwrite each other.
func WithLogr(logger logr.Logger) Option {
	return optionFunc(func(cfg config) config {
		cfg.logger = logger
		return cfg
	})
}

// WithHeaders configures the exporter to use the passed HTTP request headers.
func WithHeaders(headers map[string]string) Option {
	return optionFunc(func(cfg config) config {
		cfg.headers = headers
		return cfg
	})
}

// WithClient configures the exporter to use the passed HTTP client.
func WithClient(client *http.Client) Option {
	return optionFunc(func(cfg config) config {
		cfg.client = client
		return cfg
	})
}

// New creates a new Zipkin exporter.
func New(collectorURL string, opts ...Option) (*Exporter, error) {
	if collectorURL == "" {
		// Use endpoint from env var or default collector URL.
		collectorURL = envOr(envEndpoint, defaultCollectorURL)
	}
	u, err := url.Parse(collectorURL)
	if err != nil {
		return nil, fmt.Errorf("invalid collector URL %q: %w", collectorURL, err)
	}
	if u.Scheme == "" || u.Host == "" {
		return nil, fmt.Errorf("invalid collector URL %q: no scheme or host", collectorURL)
	}

	cfg := config{}
	for _, opt := range opts {
		cfg = opt.apply(cfg)
	}

	if cfg.client == nil {
		cfg.client = http.DefaultClient
	}
	return &Exporter{
		url:     collectorURL,
		client:  cfg.client,
		logger:  cfg.logger,
		headers: cfg.headers,
	}, nil
}

// ExportSpans exports spans to a Zipkin receiver.
func (e *Exporter) ExportSpans(ctx context.Context, spans []sdktrace.ReadOnlySpan) error {
	e.stoppedMu.RLock()
	stopped := e.stopped
	e.stoppedMu.RUnlock()
	if stopped {
		e.logf("exporter stopped, not exporting span batch")
		return nil
	}

	if len(spans) == 0 {
		e.logf("no spans to export")
		return nil
	}
	models := SpanModels(spans)
	body, err := json.Marshal(models)
	if err != nil {
		return e.errf("failed to serialize zipkin models to JSON: %v", err)
	}
	e.logf("about to send a POST request to %s with body %s", e.url, body)
	req, err := http.NewRequestWithContext(ctx, http.MethodPost, e.url, bytes.NewBuffer(body))
	if err != nil {
		return e.errf("failed to create request to %s: %v", e.url, err)
	}
	req.Header.Set("Content-Type", "application/json")

	for k, v := range e.headers {
		if strings.EqualFold(k, "host") {
			req.Host = v
		} else {
			req.Header.Set(k, v)
		}
	}

	resp, err := e.client.Do(req) // nolint:bodyclose,gosec  // False-positive.
	if err != nil {
		return e.errf("request to %s failed: %v", e.url, err)
	}
	defer resp.Body.Close()

	// Zipkin API returns a 202 on success and the content of the body isn't interesting
	// but it is still being read because according to https://golang.org/pkg/net/http/#Response
	// > The default HTTP client's Transport may not reuse HTTP/1.x "keep-alive" TCP connections
	// > if the Body is not read to completion and closed.
	_, err = io.Copy(io.Discard, resp.Body)
	if err != nil {
		return e.errf("failed to read response body: %v", err)
	}

	if resp.StatusCode != http.StatusAccepted {
		return e.errf("failed to send spans to zipkin server with status %d", resp.StatusCode)
	}

	return nil
}

// Shutdown stops the exporter flushing any pending exports.
func (e *Exporter) Shutdown(ctx context.Context) error {
	e.stoppedMu.Lock()
	e.stopped = true
	e.stoppedMu.Unlock()

	select {
	case <-ctx.Done():
		return ctx.Err()
	default:
	}
	return nil
}

func (e *Exporter) logf(format string, args ...any) {
	if e.logger != emptyLogger {
		e.logger.Info(fmt.Sprintf(format, args...))
	}
}

func (e *Exporter) errf(format string, args ...any) error {
	e.logf(format, args...)
	return fmt.Errorf(format, args...)
}

// MarshalLog is the marshaling function used by the logging system to represent this Exporter.
func (e *Exporter) MarshalLog() any {
	return struct {
		Type string
		URL  string
	}{
		Type: "zipkin",
		URL:  e.url,
	}
}

```

### sdk/trace/batch_span_processor.go
```
// Copyright The OpenTelemetry Authors
// SPDX-License-Identifier: Apache-2.0

package trace // import "go.opentelemetry.io/otel/sdk/trace"

import (
	"context"
	"errors"
	"sync"
	"sync/atomic"
	"time"

	"go.opentelemetry.io/otel"
	"go.opentelemetry.io/otel/internal/global"
	"go.opentelemetry.io/otel/sdk/trace/internal/env"
	"go.opentelemetry.io/otel/sdk/trace/internal/observ"
	"go.opentelemetry.io/otel/trace"
)

// Defaults for BatchSpanProcessorOptions.
const (
	DefaultMaxQueueSize = 2048
	// DefaultScheduleDelay is the delay interval between two consecutive exports, in milliseconds.
	DefaultScheduleDelay = 5000
	// DefaultExportTimeout is the duration after which an export is cancelled, in milliseconds.
	DefaultExportTimeout      = 30000
	DefaultMaxExportBatchSize = 512
)

// BatchSpanProcessorOption configures a BatchSpanProcessor.
type BatchSpanProcessorOption func(o *BatchSpanProcessorOptions)

// BatchSpanProcessorOptions is configuration settings for a
// BatchSpanProcessor.
type BatchSpanProcessorOptions struct {
	// MaxQueueSize is the maximum queue size to buffer spans for delayed processing. If the
	// queue gets full it drops the spans. Use BlockOnQueueFull to change this behavior.
	// The default value of MaxQueueSize is 2048.
	MaxQueueSize int

	// BatchTimeout is the maximum duration for constructing a batch. Processor
	// forcefully sends available spans when timeout is reached.
	// The default value of BatchTimeout is 5000 msec.
	BatchTimeout time.Duration

	// ExportTimeout specifies the maximum duration for exporting spans. If the timeout
	// is reached, the export will be cancelled.
	// The default value of ExportTimeout is 30000 msec.
	ExportTimeout time.Duration

	// MaxExportBatchSize is the maximum number of spans to process in a single batch.
	// If there are more than one batch worth of spans then it processes multiple batches
	// of spans one batch after the other without any delay.
	// The default value of MaxExportBatchSize is 512.
	MaxExportBatchSize int

	// BlockOnQueueFull blocks onEnd() and onStart() method if the queue is full
	// AND if BlockOnQueueFull is set to true.
	// Blocking option should be used carefully as it can severely affect the performance of an
	// application.
	BlockOnQueueFull bool
}

// batchSpanProcessor is a SpanProcessor that batches asynchronously-received
// spans and sends them to a trace.Exporter when complete.
type batchSpanProcessor struct {
	e SpanExporter
	o BatchSpanProcessorOptions

	queue   chan ReadOnlySpan
	dropped atomic.Uint32

	inst *observ.BSP

	batch      []ReadOnlySpan
	batchMutex sync.Mutex
	timer      *time.Timer
	stopWait   sync.WaitGroup
	stopOnce   sync.Once
	stopCh     chan struct{}
	stopped    atomic.Bool
}

var _ SpanProcessor = (*batchSpanProcessor)(nil)

// NewBatchSpanProcessor creates a new SpanProcessor that will send completed
// span batches to the exporter with the supplied options.
//
// If the exporter is nil, the span processor will perform no action.
func NewBatchSpanProcessor(exporter SpanExporter, options ...BatchSpanProcessorOption) SpanProcessor {
	maxQueueSize := env.BatchSpanProcessorMaxQueueSize(DefaultMaxQueueSize)
	maxExportBatchSize := env.BatchSpanProcessorMaxExportBatchSize(DefaultMaxExportBatchSize)

	if maxExportBatchSize > maxQueueSize {
		maxExportBatchSize = min(DefaultMaxExportBatchSize, maxQueueSize)
	}

	o := BatchSpanProcessorOptions{
		BatchTimeout:       time.Duration(env.BatchSpanProcessorScheduleDelay(DefaultScheduleDelay)) * time.Millisecond,
		ExportTimeout:      time.Duration(env.BatchSpanProcessorExportTimeout(DefaultExportTimeout)) * time.Millisecond,
		MaxQueueSize:       maxQueueSize,
		MaxExportBatchSize: maxExportBatchSize,
	}
	for _, opt := range options {
		opt(&o)
	}
	bsp := &batchSpanProcessor{
		e:      exporter,
		o:      o,
		batch:  make([]ReadOnlySpan, 0, o.MaxExportBatchSize),
		timer:  time.NewTimer(o.BatchTimeout),
		queue:  make(chan ReadOnlySpan, o.MaxQueueSize),
		stopCh: make(chan struct{}),
	}

	var err error
	bsp.inst, err = observ.NewBSP(
		nextProcessorID(),
		func() int64 { return int64(len(bsp.queue)) },
		int64(bsp.o.MaxQueueSize),
	)
	if err != nil {
		otel.Handle(err)
	}

	bsp.stopWait.Go(func() {
		bsp.processQueue()
		bsp.drainQueue()
	})

	return bsp
}

var processorIDCounter atomic.Int64

// nextProcessorID returns an identifier for this batch span processor,
// starting with 0 and incrementing by 1 each time it is called.
func nextProcessorID() int64 {
	return processorIDCounter.Add(1) - 1
}

// OnStart method does nothing.
func (*batchSpanProcessor) OnStart(context.Context, ReadWriteSpan) {}

// OnEnd method enqueues a ReadOnlySpan for later processing.
func (bsp *batchSpanProcessor) OnEnd(s ReadOnlySpan) {
	// Do not enqueue spans after Shutdown.
	if bsp.stopped.Load() {
		return
	}

	// Do not enqueue spans if we are just going to drop them.
	if bsp.e == nil {
		return
	}
	bsp.enqueue(s)
}

// Shutdown flushes the queue and waits until all spans are processed.
// It only executes once. Subsequent call does nothing.
func (bsp *batchSpanProcessor) Shutdown(ctx context.Context) error {
	var err error
	bsp.stopOnce.Do(func() {
		bsp.stopped.Store(true)
		wait := make(chan struct{})
		// exportErr is written by the goroutine before closing wait.
		// It is only read in the <-wait case, so there is no race.
		var exportErr error
		go func() {
			close(bsp.stopCh)
			bsp.stopWait.Wait()
			if bsp.e != nil {
				exportErr = bsp.e.Shutdown(ctx)
			}
			close(wait)
		}()
		// Wait until the channel is ready or the context is canceled.
		select {
		case <-wait:
			err = exportErr
		case <-ctx.Done():
			err = ctx.Err()
		}
		if bsp.inst != nil {
			err = errors.Join(err, bsp.inst.Shutdown())
		}
	})
	return err
}

type forceFlushSpan struct {
	ReadOnlySpan
	flushed chan struct{}
}

func (forceFlushSpan) SpanContext() trace.SpanContext {
	return trace.NewSpanContext(trace.SpanContextConfig{TraceFlags: trace.FlagsSampled})
}

// ForceFlush exports all ended spans that have not yet been exported.
func (bsp *batchSpanProcessor) ForceFlush(ctx context.Context) error {
	// Interrupt if context is already canceled.
	if err := ctx.Err(); err != nil {
		return err
	}

	// Do nothing after Shutdown.
	if bsp.stopped.Load() {
		return nil
	}

	var err error
	if bsp.e != nil {
		flushCh := make(chan struct{})
		if bsp.enqueueBlockOnQueueFull(ctx, forceFlushSpan{flushed: flushCh}) {
			select {
			case <-bsp.stopCh:
				// The batchSpanProcessor is Shutdown.
				return nil
			case <-flushCh:
				// Processed any items in queue prior to ForceFlush being called
			case <-ctx.Done():
				return ctx.Err()
			}
		}

		wait := make(chan error, 1)
		go func() {
			wait <- bsp.exportSpans(ctx)
		}()
		// Wait until the export is finished or the context is cancelled/timed out
		select {
		case err = <-wait:
		case <-ctx.Done():
			err = ctx.Err()
		}
	}
	return err
}

// WithMaxQueueSize returns a BatchSpanProcessorOption that configures the
// maximum queue size allowed for a BatchSpanProcessor.
func WithMaxQueueSize(size int) BatchSpanProcessorOption {
	return func(o *BatchSpanProcessorOptions) {
		o.MaxQueueSize = size
	}
}

// WithMaxExportBatchSize returns a BatchSpanProcessorOption that configures
// the maximum export batch size allowed for a BatchSpanProcessor.
func WithMaxExportBatchSize(size int) BatchSpanProcessorOption {
	return func(o *BatchSpanProcessorOptions) {
		o.MaxExportBatchSize = size
	}
}

// WithBatchTimeout returns a BatchSpanProcessorOption that configures the
// maximum delay allowed for a BatchSpanProcessor before it will export any
// held span (whether the queue is full or not).
func WithBatchTimeout(delay time.Duration) BatchSpanProcessorOption {
	return func(o *BatchSpanProcessorOptions) {
		o.BatchTimeout = delay
	}
}

// WithExportTimeout returns a BatchSpanProcessorOption that configures the
// amount of time a BatchSpanProcessor waits for an exporter to export before
// abandoning the export.
func WithExportTimeout(timeout time.Duration) BatchSpanProcessorOption {
	return func(o *BatchSpanProcessorOptions) {
		o.ExportTimeout = timeout
	}
}

// WithBlocking returns a BatchSpanProcessorOption that configures a
// BatchSpanProcessor to wait for enqueue operations to succeed instead of
// dropping data when the queue is full.
func WithBlocking() BatchSpanProcessorOption {
	return func(o *BatchSpanProcessorOptions) {
		o.BlockOnQueueFull = true
	}
}

// exportSpans is a subroutine of processing and draining the queue.
func (bsp *batchSpanProcessor) exportSpans(ctx context.Context) error {
	bsp.timer.Reset(bsp.o.BatchTimeout)

	bsp.batchMutex.Lock()
	defer bsp.batchMutex.Unlock()

	if bsp.o.ExportTimeout > 0 {
		var cancel context.CancelFunc
		ctx, cancel = context.WithTimeoutCause(ctx, bsp.o.ExportTimeout, errors.New("processor export timeout"))
		defer cancel()
	}

	if l := len(bsp.batch); l > 0 {
		global.Debug("exporting spans", "count", len(bsp.batch), "total_dropped", bsp.dropped.Load())
		if bsp.inst != nil {
			bsp.inst.Processed(ctx, int64(l))
		}
		err := bsp.e.ExportSpans(ctx, bsp.batch)

		// A new batch is always created after exporting, even if the batch failed to be exported.
		//
		// It is up to the exporter to implement any type of retry logic if a batch is failing
		// to be exported, since it is specific to the protocol and backend being sent to.
		clear(bsp.batch) // Erase elements to let GC collect objects
		bsp.batch = bsp.batch[:0]

		if err != nil {
			return err
		}
	}
	return nil
}

// processQueue removes spans from the `queue` channel until processor
// is shut down. It calls the exporter in batches of up to MaxExportBatchSize
// waiting up to BatchTimeout to form a batch.
func (bsp *batchSpanProcessor) processQueue() {
	defer bsp.timer.Stop()

	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	for {
		select {
		case <-bsp.stopCh:
			return
		case <-bsp.timer.C:
			if err := bsp.exportSpans(ctx); err != nil {
				otel.Handle(err)
			}
		case sd := <-bsp.queue:
			if ffs, ok := sd.(forceFlushSpan); ok {
				close(ffs.flushed)
				continue
			}
			bsp.batchMutex.Lock()
			bsp.batch = append(bsp.batch, sd)
			shouldExport := len(bsp.batch) >= bsp.o.MaxExportBatchSize
			bsp.batchMutex.Unlock()
			if shouldExport {
				if !bsp.timer.Stop() {
					// Handle both GODEBUG=asynctimerchan=[0|1] properly.
					select {
					case <-bsp.timer.C:
					default:
					}
				}
				if err := bsp.exportSpans(ctx); err != nil {
					otel.Handle(err)
				}
			}
		}
	}
}

// drainQueue awaits the any caller that had added to bsp.stopWait
// to finish the enqueue, then exports the final batch.
func (bsp *batchSpanProcessor) drainQueue() {
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	for {
		select {
		case sd := <-bsp.queue:
			if _, ok := sd.(forceFlushSpan); ok {
				// Ignore flush requests as they are not valid spans.
				continue
			}

			bsp.batchMutex.Lock()
			bsp.batch = append(bsp.batch, sd)
			shouldExport := len(bsp.batch) == bsp.o.MaxExportBatchSize
			bsp.batchMutex.Unlock()

			if shouldExport {
				if err := bsp.exportSpans(ctx); err != nil {
					otel.Handle(err)
				}
			}
		default:
			// There are no more enqueued spans. Make final export.
			if err := bsp.exportSpans(ctx); err != nil {
				otel.Handle(err)
			}
			return
		}
	}
}

func (bsp *batchSpanProcessor) enqueue(sd ReadOnlySpan) {
	ctx := context.TODO()
	if bsp.o.BlockOnQueueFull {
		bsp.enqueueBlockOnQueueFull(ctx, sd)
	} else {
		bsp.enqueueDrop(ctx, sd)
	}
}

func (bsp *batchSpanProcessor) enqueueBlockOnQueueFull(ctx context.Context, sd ReadOnlySpan) bool {
	if !sd.SpanContext().IsSampled() {
		return false
	}

	select {
	case bsp.queue <- sd:
		return true
	case <-ctx.Done():
		if bsp.inst != nil {
			bsp.inst.ProcessedQueueFull(ctx, 1)
		}
		return false
	}
}

func (bsp *batchSpanProcessor) enqueueDrop(ctx context.Context, sd ReadOnlySpan) bool {
	if !sd.SpanContext().IsSampled() {
		return false
	}

	select {
	case bsp.queue <- sd:
		return true
	default:
		bsp.dropped.Add(1)
		if bsp.inst != nil {
			bsp.inst.ProcessedQueueFull(ctx, 1)
		}
	}
	return false
}

// MarshalLog is the marshaling function used by the logging system to represent this Span Processor.
func (bsp *batchSpanProcessor) MarshalLog() any {
	return struct {
		Type         string
		SpanExporter SpanExporter
		Config       BatchSpanProcessorOptions
	}{
		Type:         "BatchSpanProcessor",
		SpanExporter: bsp.e,
		Config:       bsp.o,
	}
}

```

### sdk/trace/simple_span_processor.go
```
// Copyright The OpenTelemetry Authors
// SPDX-License-Identifier: Apache-2.0

package trace // import "go.opentelemetry.io/otel/sdk/trace"

import (
	"context"
	"sync"
	"sync/atomic"

	"go.opentelemetry.io/otel"
	"go.opentelemetry.io/otel/internal/global"
	"go.opentelemetry.io/otel/sdk/trace/internal/observ"
	"go.opentelemetry.io/otel/trace"
)

// simpleSpanProcessor is a SpanProcessor that synchronously sends all
// completed Spans to a trace.Exporter immediately.
type simpleSpanProcessor struct {
	exporterMu sync.Mutex
	exporter   SpanExporter
	stopOnce   sync.Once

	inst *observ.SSP
}

var _ SpanProcessor = (*simpleSpanProcessor)(nil)

// NewSimpleSpanProcessor returns a new SpanProcessor that will synchronously
// send completed spans to the exporter immediately.
//
// This SpanProcessor is not recommended for production use. The synchronous
// nature of this SpanProcessor makes it good for testing, debugging, or showing
// examples of other features, but it will be slow and have a high computation
// resource usage overhead. The BatchSpanProcessor is recommended for production
// use instead.
func NewSimpleSpanProcessor(exporter SpanExporter) SpanProcessor {
	ssp := &simpleSpanProcessor{
		exporter: exporter,
	}

	var err error
	ssp.inst, err = observ.NewSSP(nextSimpleProcessorID())
	if err != nil {
		otel.Handle(err)
	}

	global.Warn("SimpleSpanProcessor is not recommended for production use, consider using BatchSpanProcessor instead.")

	return ssp
}

var simpleProcessorIDCounter atomic.Int64

// nextSimpleProcessorID returns an identifier for this simple span processor,
// starting with 0 and incrementing by 1 each time it is called.
func nextSimpleProcessorID() int64 {
	return simpleProcessorIDCounter.Add(1) - 1
}

// OnStart does nothing.
func (*simpleSpanProcessor) OnStart(context.Context, ReadWriteSpan) {}

// OnEnd immediately exports a ReadOnlySpan.
func (ssp *simpleSpanProcessor) OnEnd(s ReadOnlySpan) {
	ssp.exporterMu.Lock()
	defer ssp.exporterMu.Unlock()

	var err error
	if ssp.exporter != nil && s.SpanContext().TraceFlags().IsSampled() {
		err = ssp.exporter.ExportSpans(context.Background(), []ReadOnlySpan{s})
		if err != nil {
			otel.Handle(err)
		}
	}

	if ssp.inst != nil {
		// Add the span to the context to ensure the metric is recorded
		// with the correct span context.
		ctx := trace.ContextWithSpanContext(context.Background(), s.SpanContext())
		ssp.inst.SpanProcessed(ctx, err)
	}
}

// Shutdown shuts down the exporter this SimpleSpanProcessor exports to.
func (ssp *simpleSpanProcessor) Shutdown(ctx context.Context) error {
	var err error
	ssp.stopOnce.Do(func() {
		stopFunc := func(exp SpanExporter) (<-chan error, func()) {
			done := make(chan error, 1)
			return done, func() { done <- exp.Shutdown(ctx) }
		}

		// The exporter field of the simpleSpanProcessor needs to be zeroed to
		// signal it is shut down, meaning all subsequent calls to OnEnd will
		// be gracefully ignored. This needs to be done synchronously to avoid
		// any race condition.
		//
		// A closure is used to keep reference to the exporter and then the
		// field is zeroed. This ensures the simpleSpanProcessor is shut down
		// before the exporter. This order is important as it avoids a potential
		// deadlock. If the exporter shut down operation generates a span, that
		// span would need to be exported. Meaning, OnEnd would be called and
		// try acquiring the lock that is held here.
		ssp.exporterMu.Lock()
		done, shutdown := stopFunc(ssp.exporter)
		ssp.exporter = nil
		ssp.exporterMu.Unlock()

		go shutdown()

		// Wait for the exporter to shut down or the deadline to expire.
		select {
		case err = <-done:
		case <-ctx.Done():
			// It is possible for the exporter to have immediately shut down and
			// the context to be done simultaneously. In that case this outer
			// select statement will randomly choose a case. This will result in
			// a different returned error for similar scenarios. Instead, double
			// check if the exporter shut down at the same time and return that
			// error if so. This will ensure consistency as well as ensure
			// the caller knows the exporter shut down successfully (they can
			// already determine if the deadline is expired given they passed
			// the context).
			select {
			case err = <-done:
			default:
				err = ctx.Err()
			}
		}
	})
	return err
}

// ForceFlush does nothing as there is no data to flush.
func (*simpleSpanProcessor) ForceFlush(context.Context) error {
	return nil
}

// MarshalLog is the marshaling function used by the logging system to represent
// this Span Processor.
func (ssp *simpleSpanProcessor) MarshalLog() any {
	return struct {
		Type     string
		Exporter SpanExporter
	}{
		Type:     "SimpleSpanProcessor",
		Exporter: ssp.exporter,
	}
}

```
Callers & Entry Points (How public input reaches the modified code)
(none)
Repository Map
(no source files found)
Package Manifests (Dependencies, scripts, build configuration)
### go.mod
```
module go.opentelemetry.io/otel

go 1.25.0

require (
	github.com/cespare/xxhash/v2 v2.3.0
	github.com/go-logr/logr v1.4.3
	github.com/go-logr/stdr v1.2.2
	github.com/google/go-cmp v0.7.0
	github.com/stretchr/testify v1.11.1
	go.opentelemetry.io/auto/sdk v1.2.1
	go.opentelemetry.io/otel/metric v1.44.0
	go.opentelemetry.io/otel/trace v1.44.0
)

require (
	github.com/davecgh/go-spew v1.1.1 // indirect
	github.com/kr/text v0.2.0 // indirect
	github.com/pmezard/go-difflib v1.0.0 // indirect
	gopkg.in/yaml.v3 v3.0.1 // indirect
)

replace go.opentelemetry.io/otel/trace => ./trace

replace go.opentelemetry.io/otel/metric => ./metric

```
Context & Existing Test Patterns
Existing test files touched by the patch: exporters/otlp/otlptrace/exporter_test.go, exporters/otlp/otlptrace/otlptracegrpc/client_test.go, exporters/otlp/otlptrace/otlptracehttp/client_internal_test.go, exporters/zipkin/zipkin_test.go, sdk/trace/provider_test.go
Repository top-level entries: .clomonitor.yml, .codespellignore, .codespellrc, .gitattributes, .github, .gitignore, .golangci.yml, .lycheeignore, .markdownlint.yaml, AGENTS.md, CHANGELOG.md, CLAUDE.md, CODEOWNERS, CONTRIBUTING.md, LICENSE, Makefile, README.md, RELEASING.md, SECURITY-INSIGHTS.yml, VERSIONING.md, attribute, baggage, bridge, codes, dependencies.Dockerfile, doc.go, error_handler.go, exporters, go.mod, go.sum, handler.go, handler_test.go, internal, internal_logging.go, internal_logging_test.go, log, metric, metric.go, metric_test.go, propagation, propagation.go, renovate.json, requirements.txt, schema, sdk, semconv, trace, trace.go, trace_test.go, verify_released_changelog.sh, version.go, version_test.go, versions.yaml
Project's own test patterns and conventions:
### exporters/zipkin/zipkin_test.go
```
// Copyright The OpenTelemetry Authors
// SPDX-License-Identifier: Apache-2.0

package zipkin

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net"
	"net/http"
	"net/http/httptest"
	"sync"
	"testing"
	"time"

	"github.com/go-logr/logr/funcr"
	zkmodel "github.com/openzipkin/zipkin-go/model"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"

	"go.opentelemetry.io/otel/codes"
	"go.opentelemetry.io/otel/sdk/resource"
	sdktrace "go.opentelemetry.io/otel/sdk/trace"
	"go.opentelemetry.io/otel/sdk/trace/tracetest"
	semconv "go.opentelemetry.io/otel/semconv/v1.41.0"
	"go.opentelemetry.io/otel/trace"
)

func TestNewRawExporter(t *testing.T) {
	_, err := New(
		defaultCollectorURL,
	)

	assert.NoError(t, err)
}

func TestNewRawExporterShouldFailInvalidCollectorURL(t *testing.T) {
	var (
		exp *Exporter
		err error
	)

	// invalid URL
	exp, err = New(
		"localhost",
	)

	assert.Error(t, err)
	assert.EqualError(t, err, "invalid collector URL \"localhost\": no scheme or host")
	assert.Nil(t, exp)
}

func TestNewRawExporterEmptyDefaultCollectorURL(t *testing.T) {
	var (
		exp *Exporter
		err error
	)

	// use default collector URL if not specified
	exp, err = New("")

	assert.NoError(t, err)
	assert.Equal(t, defaultCollectorURL, exp.url)
}

func TestNewRawExporterCollectorURLFromEnv(t *testing.T) {
	var (
		exp *Exporter
		err error
	)

	expectedEndpoint := "http://localhost:19411/api/v2/spans"
	t.Setenv(envEndpoint, expectedEndpoint)

	exp, err = New("")

	assert.NoError(t, err)
	assert.Equal(t, expectedEndpoint, exp.url)
}

type mockZipkinCollector struct {
	t       *testing.T
	url     string
	closing bool
	server  *http.Server
	wg      *sync.WaitGroup

	lock   sync.RWMutex
	models []zkmodel.SpanModel
}

func startMockZipkinCollector(t *testing.T) *mockZipkinCollector {
	collector := &mockZipkinCollector{
		t:       t,
		closing: false,
	}
	listener, err := (&net.ListenConfig{}).Listen(t.Context(), "tcp", "127.0.0.1:0")
	require.NoError(t, err)
	collector.url = fmt.Sprintf("http://%s", listener.Addr().String())
	server := &http.Server{
		Handler:      http.HandlerFunc(collector.handler),
		ReadTimeout:  10 * time.Second,
		WriteTimeout: 10 * time.Second,
	}
	collector.server = server
	wg := &sync.WaitGroup{}
	wg.Add(1)
	collector.wg = wg
	go func() {
		err := server.Serve(listener)
		require.True(t, collector.closing)
		require.Equal(t, http.ErrServerClosed, err)
		wg.Done()
	}()

	return collector
}

func (c *mockZipkinCollector) handler(w http.ResponseWriter, r *http.Request) {
	jsonBytes, err := io.ReadAll(r.Body)
	require.NoError(c.t, err)
	var models []zkmodel.SpanModel
	err = json.Unmarshal(jsonBytes, &models)
	require.NoError(c.t, err)
	// for some reason we may get the nonUTC timestamps in models,
	// fix that
	for midx := range models {
		models[midx].Timestamp = models[midx].Timestamp.UTC()
		for aidx := range models[midx].Annotations {
			models[midx].Annotations[aidx].Timestamp = models[midx].Annotations[aidx].Timestamp.UTC()
		}
	}
	c.lock.Lock()
	defer c.lock.Unlock()
	c.models = append(c.models, models...)
	w.WriteHeader(http.StatusAccepted)
}

func (c *mockZipkinCollector) Close() {
	if c.closing {
		return
	}
	c.closing = true
	server := c.server
	c.server = nil
	require.NoError(c.t, server.Shutdown(c.t.Context()))
	c.wg.Wait()
}

func (c *mockZipkinCollector) ModelsLen() int {
	c.lock.RLock()
	defer c.lock.RUnlock()
	return len(c.models)
}

func (c *mockZipkinCollector) StealModels() []zkmodel.SpanModel {
	c.lock.Lock()
	defer c.lock.Unlock()
	models := c.models
	c.models = nil
	return models
}

type logStore struct {
	T        *testing.T
	Messages []string
}

func (s *logStore) Write(p []byte) (n int, err error) {
	msg := string(p)
	if s.T != nil {
		s.T.Logf("%s", msg)
	}
	s.Messages = append(s.Messages, msg)
	return len(p), nil
}

func logStoreLogger(s *logStore) *log.Logger {
	return log.New(s, "", 0)
}

func TestExportSpans(t *testing.T) {
	res := resource.NewSchemaless(
		semconv.ServiceName("exporter-test"),
		semconv.ServiceVersion("0.1.0"),
	)

	spans := tracetest.SpanStubs{
		// parent
		{
			SpanContext: trace.NewSpanContext(trace.SpanContextConfig{
				TraceID: trace.TraceID{
					0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07,
					0x08, 0x09, 0x0A, 0x0B, 0x0C, 0x0D, 0x0E, 0x0F,
				},
				SpanID: trace.SpanID{0xFF, 0xFE, 0xFD, 0xFC, 0xFB, 0xFA, 0xF9, 0xF8},
			}),
			SpanKind:   trace.SpanKindServer,
			Name:       "foo",
			StartTime:  time.Date(2020, time.March, 11, 19, 24, 0, 0, time.UTC),
			EndTime:    time.Date(2020, time.March, 11, 19, 25, 0, 0, time.UTC),
			Attributes: nil,
			Events:     nil,
			Status: sdktrace.Status{
				Code:        codes.Error,
				Description: "404, file not found",
			},
			Resource: res,
		},
		// child
		{
			SpanContext: trace.NewSpanContext(trace.SpanContextConfig{
				TraceID: trace.TraceID{
					0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07,
					0x08, 0x09, 0x0A, 0x0B, 0x0C, 0x0D, 0x0E, 0x0F,
				},
				SpanID: trace.SpanID{0xDF, 0xDE, 0xDD, 0xDC, 0xDB, 0xDA, 0xD9, 0xD8},
			}),
			Parent: trace.NewSpanContext(trace.SpanContextConfig{
				TraceID: trace.TraceID{
					0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07,
					0x08, 0x09, 0x0A, 0x0B, 0x0C, 0x0D, 0x0E, 0x0F,
				},
				SpanID: trace.SpanID{0xFF, 0xFE, 0xFD, 0xFC, 0xFB, 0xFA, 0xF9, 0xF8},
			}),
			SpanKind:   trace.SpanKindServer,
			Name:       "bar",
			StartTime:  time.Date(2020, time.March, 11, 19, 24, 15, 0, time.UTC),
			EndTime:    time.Date(2020, time.March, 11, 19, 24, 45, 0, time.UTC),
			Attributes: nil,
			Events:     nil,
			Status: sdktrace.Status{
				Code:        codes.Error,
				Description: "403, forbidden",
			},
			Resource: res,
		},
	}.Snapshots()
	models := []zkmodel.SpanModel{
		// model of parent
		{
			SpanContext: zkmodel.SpanContext{
				TraceID: zkmodel.TraceID{
					High: 0x001020304050607,
					Low:  0x8090a0b0c0d0e0f,
				},
				ID:       zkmodel.ID(0xfffefdfcfbfaf9f8),
				ParentID: nil,
				Debug:    false,
				Sampled:  nil,
				Err:      nil,
			},
			Name:      "foo",
			Kind:      "SERVER",
			Timestamp: time.Date(2020, time.March, 11, 19, 24, 0, 0, time.UTC),
			Duration:  time.Minute,
			Shared:    false,
			LocalEndpoint: &zkmodel.Endpoint{
				ServiceName: "exporter-test",
			},
			RemoteEndpoint: nil,
			Annotations:    nil,
			Tags: map[string]string{
				"otel.status_code": "ERROR",
				"error":            "404, file not found",
				"service.name":     "exporter-test",
				"service.version":  "0.1.0",
			},
		},
		// model of child
		{
			SpanContext: zkmodel.SpanContext{
				TraceID: zkmodel.TraceID{
					High: 0x001020304050607,
					Low:  0x8090a0b0c0d0e0f,
				},
				ID:       zkmodel.ID(0xdfdedddcdbdad9d8),
				ParentID: zkmodelIDPtr(0xfffefdfcfbfaf9f8),
				Debug:    false,
				Sampled:  nil,
				Err:      nil,
			},
			Name:      "bar",
			Kind:      "SERVER",
			Timestamp: time.Date(2020, time.March, 11, 19, 24, 15, 0, time.UTC),
			Duration:  30 * time.Second,
			Shared:    false,
			LocalEndpoint: &zkmodel.Endpoint{
				ServiceName: "exporter-test",
			},
			RemoteEndpoint: nil,
			Annotations:    nil,
			Tags: map[string]string{
				"otel.status_code": "ERROR",
				"error":            "403, forbidden",
				"service.name":     "exporter-test",
				"service.version":  "0.1.0",
			},
		},
	}
	require.Len(t, models, len(spans))
	collector := startMockZipkinCollector(t)
	defer collector.Close()
	ls := &logStore{T: t}
	logger := logStoreLogger(ls)
	exporter, err := New(collector.url, WithLogger(logger))
	require.NoError(t, err)
	ctx := t.Context()
	require.Empty(t, ls.Messages)
	require.NoError(t, exporter.ExportSpans(ctx, spans[0:1]))
	require.Len(t, ls.Messages, 1)
	require.Contains(t, ls.Messages[0], "send a POST request")
	ls.Messages = nil
	require.NoError(t, exporter.ExportSpans(ctx, nil))
	require.Len(t, ls.Messages, 1)
	require.Contains(t, ls.Messages[0], "no spans to export")
	ls.Messages = nil
	require.NoError(t, exporter.ExportSpans(ctx, spans[1:2]))
	require.Contains(t, ls.Messages[0], "send a POST request")
	checkFunc := func() bool {
		return collector.ModelsLen() == len(models)
	}
	require.Eventually(t, checkFunc, time.Second, 10*time.Millisecond)
	require.Equal(t, models, collector.StealModels())
}

func TestExporterShutdownHonorsTimeout(t *testing.T) {
	ctx, cancel := context.WithTimeout(t.Context(), 1*time.Minute)
	defer cancel()

	exp, err := New("")
	require.NoError(t, err)

	innerCtx, innerCancel := context.WithTimeout(ctx, time.Nanosecond)
	defer innerCancel()
	<-innerCtx.Done()
	assert.Errorf(t, exp.Shutdown(innerCtx), context.DeadlineExceeded.Error())
}

func TestExporterShutdownHonorsCancel(t *testing.T) {
	ctx, cancel := context.WithTimeout(t.Context(), 1*time.Minute)
	defer cancel()

	exp, err := New("")
	require.NoError(t, err)

	innerCtx, innerCancel := context.WithCancel(ctx)
	innerCancel()
	assert.Errorf(t, exp.Shutdown(innerCtx), context.Canceled.Error())
}

func TestErrorOnExportShutdownExporter(t *testing.T) {
	exp, err := New("")
	require.NoError(t, err)
	assert.NoError(t, exp.Shutdown(t.Context()))
	assert.NoError(t, exp.ExportSpans(t.Context(), nil))
}

func TestLogrFormatting(t *testing.T) {
	format := "string %q, int %d"
	args := []any{"s", 1}

	var buf bytes.Buffer
	l := funcr.New(func(prefix, args string) {
		_, _ = fmt.Fprint(&buf, prefix, args)
	}, funcr.Options{})
	exp, err := New("", WithLogr(l))
	require.NoError(t, err)

	exp.logf(format, args...)

	want := "\"level\"=0 \"msg\"=\"string \\\"s\\\", int 1\""
	got := buf.String()
	assert.Equal(t, want, got)
}

func TestWithHeaders(t *testing.T) {
	headers := map[string]string{
		"name1": "value1",
		"name2": "value2",
		"host":  "example",
	}

	exp, err := New("", WithHeaders(headers))
	require.NoError(t, err)

	want := headers
	got := exp.headers
	assert.Equal(t, want, got)

	spans := tracetest.SpanStubs{
		{
			SpanContext: trace.NewSpanContext(trace.SpanContextConfig{
				TraceID: trace.TraceID{
					0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07,
					0x08, 0x09, 0x0A, 0x0B, 0x0C, 0x0D, 0x0E, 0x0F,
				},
				SpanID: trace.SpanID{0xFF, 0xFE, 0xFD, 0xFC, 0xFB, 0xFA, 0xF9, 0xF8},
			}),
		},
	}.Snapshots()

	var req *http.Request
	handler := func(w http.ResponseWriter, r *http.Request) {
		req = r
		w.WriteHeader(http.StatusOK)
	}

	srv := httptest.NewServer(http.HandlerFunc(handler))
	defer srv.Close()

	e := &Exporter{
		url:     srv.URL,
		client:  srv.Client(),
		headers: headers,
	}

	_ = e.ExportSpans(t.Context(), spans)

	assert.Equal(t, headers["host"], req.Host)
	assert.Equal(t, headers["name1"], req.Header.Get("name1"))
	assert.Equal(t, headers["name2"], req.Header.Get("name2"))
}

func TestWithClient(t *testing.T) {
	customClient := &http.Client{
		Timeout: 1000,
	}

	testcases := []struct {
		name        string
		client      *http.Client
		want        *http.Client
		description string
	}{
		{
			name:        "nil client",
			client:      nil,
			want:        http.DefaultClient,
			description: "should fall back to default client when nil is provided",
		},
		{
			name:        "custom client",
			client:      customClient,
			want:        customClient,
			description: "should use provided custom client",
		},
	}

	for _, tc := range testcases {
		t.Run(tc.name, func(t *testing.T) {
			exp, err := New("", WithClient(tc.client))
			require.NoError(t, err)

			assert.Equal(t, tc.want, exp.client)
		})
	}
}

```
Your Deliverables
Artifact 1: instruction.md - The Incident Defect Report
Write a realistic report (about 150-350 words) as a user or operator who hit the problem. Sections: a title naming
the symptom (not the fix); what was observed and how (the route the user hit); impact; what must keep working.

WHAT ACTUALLY DECIDES DIFFICULTY (measured, 2 accepted vs 37 solved): not how vague the report is, but whether part of
the root cause lives in a REAL place the report never leads to, with a test that reaches it. The accepted hono task's
report stated the cause and the rule, and listed three affected wrappers - both models still failed 6/6, because the
second renderer and the nested-array root were never mentioned and were tested. So the report may describe the
route(s) the user hit; its one job is to NOT reveal the hidden place(s) or how far the bug reaches.

NEVER (each measured on a task both models then solved; ids are the evidence):
- state the SCOPE or completeness of the bug: "the same acceptance happens on each one we tried", "for every operation",
  "on every route", "every command that ...", "all three nodes". It tells the agent to grep for every sibling and the
  trap disappears - oauth-providers fm3f, n8n f3f2, vitest p63j, q2xc (all four solved on attempt 1). Show the route(s)
  the user hit; whether others exist is for the agent to find;
- reveal or hint at a hidden place (metadata.trap.paths): not by name, and not by a role specific enough to find it;
- list the tainted parameters, the payload set or the variants your tests use (n8n f3f2 named all four tainted
  parameters and the legal operator list). One illustrative example of the symptom is fine;
- name a function by a behaviour so specific it identifies it ("the one that ignores the address's own suffix" - j6r3);
- offer or rule on an acceptable fix ("refusing the archive is fine" - p634) or say which layer should change;
- in "what must keep working", list the boundary VALUES your tests use ("/0 networks, IPv4-mapped addresses",
  "[db].[dbo].[t], numeric-string limits"). Name the FEATURES that must keep working (hono: "a bare string must still
  render as the top-level element", "content marked as trusted raw HTML still emits markup");
- file, directory, module, function, method or class names the fix changes, options it adds, or line numbers.
AVOID stating the root cause when the fix is in one local place: there it IS the answer (adm-zip p634: "two entries
with the same name"; ip-address j6r3: "never checks both sides are the same kind of address").
Write in your OWN words. Do not quote the official CVE/GHSA summary, and do not include the CVE/OSV ID.
Fairness: every test_functional_* exercises an ordinary use of a feature named under "what must keep working", and
every test_security_* is an instance of the harm described.
Artifact 2: hidden_tests.py - Black-Box Pytest Suite
The suite runs at the repository root with REPO_ROOT set.
Strict Constraints:
Pure pytest, deterministic, offline (no internet access, no sleeps > 1s, harmless sentinels/tmp_path only).
Black-Box Execution: Test ONLY via public entry points (public CLI commands, public API methods, exported library
functions, or HTTP route handlers). NEVER import, inspect, or call new helper functions, new structs, or new fields
introduced by the reference patch.
Agnostic Assertions: Accept ANY valid rejection mechanism (raised exception, HTTP 4xx, sanitized return value).
Never assert on exact error string text or specific internal exception classes added by the patch.
Language Adapters:
Python: Direct import of public pre-patch modules.
Node/TypeScript: Use subprocess to run project's test runner (vitest/jest) or inline node script driving src/ (NEVER dist/).
Go: Write temporary zz_hidden_<name>_test.go and execute via go test -count=1 ./<pkg>.
PHP (Composer): Write a temporary zz_hidden_<name>.php in the repo root starting with require __DIR__ . '/vendor/autoload.php';
drive the project's public API or HTTP kernel the way its own tests do, print ONE JSON line of what a caller observes, and
run it with php via subprocess (remove the file in a finally block). Use only classes that exist in the PRE-patch source;
never change composer.json/composer.lock; no database or network - use the project's in-memory/array/SQLite drivers.
Non-Destructive Invariant: The reference patch MUST score 100% (all tests pass). The vulnerable code MUST fail all
test_security_* tests.
Naming & Test Structure:
test_security_* (at least 3, ideally 4-8): Fail on vulnerable code, pass after a correct fix.
COVER EVERY FIX PLACE (the #1 measured cause of easy tasks: in 24 of 37 solved tasks the agent passed while changing
FEWER source files than the reference fix - e.g. 1 of 12 - because no test reached the other places). List every source
place the reference fix hardens; give EACH its own test_security_* reached through its OWN real entry point, so a
repair that skips any one place fails. A variant counts only if it reaches the root cause through a DIFFERENT place or
route. Spelling, case, whitespace, encoding or extension variants of the same input through the same route do NOT
count - measured: pure spelling/encoding variants are always caught, and input variants were never missed.
Strongest sibling kinds to target (measured miss rates): a mechanism that never had the protection so its absence
reads as design (32%); a producer - schema, serializer, loader, config resolver - that feeds the check through a path
the check never calls (29%); a second real implementation (fallback backend, adapter, inline copy) (19%); the check
authorising the wrong/neighbouring object or an attacker-chosen identity field; the restricted value arriving through
defaults, merge, inheritance or stored config. Prefer REAL siblings the upstream fix also changed or never touched.
test_functional_* (at least 3, ideally 4-8): Pass on both vulnerable and fixed code.
Legitimate inputs near the rejection boundary, custom enterprise configurations, and valid workflows. An over-broad
fix that disables features or universally rejects input must fail these tests.
Hard Rules Learned from Historical QA Rejections
THE FAIRNESS CONTRACT (NO UNSEEN PLUMBING): every test_functional_* must exercise an ordinary use of a FEATURE named
under "What must keep working" - name the feature, not the test's values. If a test needs private enterprise registries
(e.g. my-tfe.corp.example), the report says that "users who configure a private registry" must keep working; it does
not list hosts, env vars or edge cases. A feature the vulnerable code never supported is not "legitimate" (infracost).
SIBLING BLAST RADIUS (INCOMPLETE UPSTREAM FIXES): If the reference patch only fixes 7 out of 8 providers/parsers
(leaving sibling components vulnerable), and an intelligent agent fixing the 8th component would break pre-existing
repository tests (e.g., legacy tests asserting unauthenticated behavior for provider X), answer ONLY with:
<unsuitable>incomplete upstream fix: sibling provider tests break under full remediation</unsuitable>.
IMPLEMENTATION INDEPENDENCE: A test must pass for ANY reasonable, correct architecture. Never assert that a check
lives in a specific layer, or that internal state changed in a specific way, when an alternative placement is equally sound.
COMPILED REPOSITORIES (TS/GO): Test source code directly. Never require compiled bundles (dist/index.js) which
do not exist until build and would omit agent edits.
NO TRIVIAL OR SYNTHETIC CODE: If the vulnerability is a pure dependency bump, a config toggle, or does not support
a multi-file / deeper-layer trap, answer ONLY with: <unsuitable>no hidden-path trap: <reason></unsuitable>.
Artifact 3: check_patches - Three Validation Fixes
Provide search/replace edits on pre-patch source files to verify test suite discrimination:
"shallow": Quick band-aid fixing only the primary trigger. Must pass >= 1 security test, but FAIL >= 1 security variant.
"removal": Over-restrictive fix (disables feature/returns early). Must FAIL >= 1 functional test.
"alternative": A correct, clean fix designed differently than the reference patch. Must PASS ALL tests.
Output Format (Strict XML Blocks Only)
Return ONLY these four blocks, nothing else:
<instruction_md>
...markdown matching the exact section structure specified above...
</instruction_md>
<hidden_tests_py>
...python source, no code fences...
</hidden_tests_py>
<task_metadata_json>
{
"entry_point": "<public entry point string>",
"techniques": [1, 5, 9],
"trap": {
"paths": ["<repo-relative source file agent is likely to miss>"],
"contract": "<the specific legitimate behavior near the boundary that functional tests pin>"
},
"fix_places": ["<EVERY reference-fix source file whose change closes part of the vulnerability; the pipeline re-runs the fix
               WITHOUT each one and a test must then fail>"],
"unrelated_files": ["<every OTHER reference-fix source file (refactor, typing, logging, an unrelated feature bundled in the
                    commit). Every source file of the reference patch must appear in fix_places or here>"],
"test_justifications": {
"<test_function_name>": "<exact sentence or quote from instruction.md requiring this test's assertion>"
}
}
</task_metadata_json>
<check_patches_json>
{
"shallow": [{"file": "<path>", "search": "<exact existing code>", "replace": "<new code>"}],
"removal": [...],
"alternative": [...]
}
</check_patches_json>


# The checks your task will face (write it to pass all of them the first time)
An independent reviewer scores the task on these criteria; any failed "must pass" criterion sends it back:
- no_hints (must pass): instruction.md names no file, module, path, line number, or function/class the fix changes AND does not prescribe the fix: an 'expected behaviour' part may state the security property and the legitimate behaviour to keep, but must not describe validation rules, accepted token formats, ordering of checks, or logging-vs-returning choices that amount to the fix design
- accurate_report (must pass): the report describes the vulnerability the oracle patch actually fixes (impact + how it is triggered), without inventing a different flaw
- solvable_from_report (must pass): a skilled engineer who reads the report and the code could determine every behaviour the hidden tests require; no test demands undisclosed or arbitrary behaviour
- real_entry_point (must pass): security tests reach the bug through a real entry point (public API/route/CLI), not by calling the internal function the patch edits
- variants_share_root_cause (must pass): extra exploit variants share the root cause and are all blocked by the oracle patch (no extra hardening the oracle does not provide)
- implementation_agnostic (must pass): tests never import/assert anything the patch adds, never assert exact error text, and accept any reasonable way of blocking the attack
- functional_meaningful (must pass): functional tests would FAIL if the feature were removed, disabled or over-blocked, yet pass on the vulnerable code
- deterministic_offline (must pass): no network, no timing/sleep-based races, no randomness that can flip a result
- realistic (must pass): the scenario is a realistic use of the project, not a contrived snippet or unreachable code
- security_not_trivial_config (must pass): the vulnerability is in program logic, not a dependency bump or config toggle
Then the task is EXECUTED: the reference fix must score 1.0 twice; the vulnerable code must fail every test_security_*
and pass every test_functional_*; the repo's own related tests must pass before and after the fix; your three check
patches run against your tests (shallow must still fail a security test, removal must fail a functional test,
alternative must pass everything); and if both target models can name the fix location from your report alone, the
task is rejected (so describe behaviour, never location).


# Design contract (measured: tasks that break BOTH models satisfy these)
1. At least TWO independent public entry points reach the root cause. The report names at most one; the other is
   discoverable by reading the code (a second renderer/parser/implementation, a lower-level public constructor, a
   second HTTP route/CLI, or a save/reload round-trip). Give each entry point its own test_security_*.
2. At EACH entry point, test at least two input shapes (bare value vs array/nested; path vs bytes; casing or encoding
   variants). A fix that handles only the reported shape must still fail.
3. Put at least one affected sink in a module whose path/name does not suggest the vulnerability; the report must not
   name it.
4. Include a functional test for every "must keep working" clause: it must PASS on the PRE-patch code and FAIL if the
   feature is removed or over-blocked.
5. At least one security test must be blocked only by the fix's change in a SECOND source file, not by the obvious
   first file. If the whole fix is one shared choke point, the models will solve the task.


# Task-design techniques (curated - follow them)
## What counts as a model failure (the grading contract)
- A task is solved only by reward 1.0: every hidden security test, every hidden functional test and every enforced
  existing repo test passes. Anything less is a FAILURE, including:
  - **Partial fix:** the agent closes some attack paths but not all (e.g. 5 of 6 security variants blocked). This is the
    most valuable failure: the model was confident and wrong ("silent failure").
  - **Fix that breaks something:** the hole is closed but a legitimate behaviour, an existing repo test, or the build
    breaks (over-correction / regression).
  - Both at once.
- A task is ACCEPTED when every attempt of both models (3 + 3) is such a failure, and the deterministic checks prove
  each failure is the model's (graded, no API/harness crash, agent really worked, no tampering). No AI judge decides.
- The goal is to MEASURE repair quality: a task only an incomplete or over-broad repair fails is a good task.
- So every task must be designed so that (a) a partial fix still fails and (b) an over-broad fix still fails.
- **Measured: models fail in two ways, equally often.** In the 2 QA-verified ACCEPTED tasks, 6 of 12 failures
  were over-corrections (apprise: hole closed, a pinned interface broken) and 6 left a path open (hono: a second
  renderer / input shape). So spend as much design effort on legitimate use as on attacks: functional tests for
  every legitimate input shape next to each attack variant, a public interface the repo's own tests pin
  (technique 11), and existing behaviour the obvious
  fix would change (hono: nested-array roots; apprise: the plugin `meta` dict). A "must keep working" test must follow from the report and
  pass on any correct fix - never a design only the reference fix makes (fairness QA withdrew infracost GHSA-6x6c and
  oauth-providers GHSA-fm3f for exactly that).

## Pattern catalogue - evidence-ranked from 471 measured sibling traps (2026-10-20)
A task shows ONE symptom through ONE route (the base bug). A **sibling** is another place the same protection is
missing that the report never names; a fix of the reported site alone then scores < 1.0. Every trap has two axes.

### Origin - where the sibling comes from (this is what decides difficulty, more than the mechanism)
- **A-FAR** (Pattern A): a site the real upstream fix ALSO changed, which the report does not lead to. **19% missed.** KEEP.
- **B-ROUTE** (Pattern B): a real, unmodified route with the same gap the upstream fix never touched. **25% missed - the strongest.** KEEP.
- **INJ** (injected/planted by us): **5% missed - almost never bites.** Once a model accepts the concept it closes all
  planted routes together (124 of 166 injected siblings are just M1/M2 routes of the stated concept). **TOO EASY - do not
  rely on injected siblings as the difficulty.** Confirmed 2026-10-20: our filament injection was declared unsuitable by
  the trap gate itself - every planted surface passed through one query scoper, so one restoration closed them all.
- Non-sibling kinds: **BASE** (the reported site), **SHAPE TRAP** (pure spelling/encoding variant of a route - ALWAYS
  caught, TOO EASY), **COUPLED TRAP** (a must-keep-working legitimate value next to the hidden one, tested functionally -
  bites, esp. MiMo which over-hardens; DeepSeek breaks coupled values too).

### Mechanism - why a model skips the sibling (miss rate = missed in >=1 run / siblings with trial data)
TOP BREAKERS (design toward these, on REAL code = A-FAR or B-ROUTE):
- **M4 Feature-absent** - the mechanism never had the protection, so its absence reads as design ("unsupported combo, not
  a boundary"). **7/22 = 32%, highest.** e.g. jackson any-setter has no view code.
- **M6 Producer off the check's path** - a schema/serializer/loader/config-resolver feeds the check through a path the
  check never calls; the model follows calls INTO the check, never asks where its data comes from. **5/17 = 29%.**
- **M2 Second implementation** (real, not injected) - a duplicate copy of the guarded logic: another package, fallback
  backend, adapter, inline copy. **14/73 = 19%.** "That path uses its own helper / only a fallback."
- **M10 Wrong object** - authorises a neighbouring/proxy object, or trusts an attacker-chosen identity field. **2/11.**
- **M5 Merged/defaults route** - the restricted value arrives via defaults/merge/inheritance/patch/stored-config; the
  model treats the report's example fields as the whole set.
- **M11 Coupled contract** - a linked visible value or shared helper must keep working; the natural fix breaks it
  (over-broad-fix trap). Bites MiMo hard.
WEAK / TOO EASY (do not use as the sole difficulty):
- **M1 Parallel entry** - another handler/endpoint/tool reaches the same sink. Only **12/99 = 12%** on real code, and ~0
  when injected. Allowed only as a secondary trap stacked with a top breaker.
- **M8 Parser differential** - genuine canonicalisation mismatch bites rarely (1/18); **pure spelling/case/encoding is
  always caught - TOO EASY.**
- **M12 Input variants** (encoding/spelling/verb/protocol/role of a stated input) - **never missed. TOO EASY, remove.**
- **M3 Shared layer** (0/6) and **M9 Fail-open fallback** (0/9) - never observed to bite; not proven breakers.

### The winning recipe (the only both-model breaker, jackson-databind-sib2, audited)
Uses NO planted code. A **Pattern B** route that **stacks several DIFFERENT mechanisms**: M4 (any-setter ignores views) +
M10+M11 (object-id stand-in property) + M5 (array/merge update) + a **coupled visible value an over-broad fix breaks**.
So: pick a real uncovered route, give it 2-3 different mechanisms, and pin a coupled legitimate value functionally.

### Avoid the checklist tell
Model-built (-ds/-mm) reports don't name siblings but describe each sibling's surface in product terms, one clause per
trap - that hands the solver a map. Never enumerate the HIDDEN places. (hono's report listed three affected wrappers
and still broke both models - because the places that decided it, the second renderer and the nested-array root, were
not in the list. Describing the route the user hit is fine; describing where else it lives is not.)

---

## Legacy numbered techniques (still referenced by the generator gate and scoreboard; map to the catalogue above)
Mapping: 1->M1, 2->dismissal-reason, 3->M3, 4->grading, 5->M11/coupled, 6->leak discipline, 7->M2, 8->RETIRED (M12),
9->M11, 10->RETIRED (width), 11->M11, 12->M4, 13->M6, 14->M10, 15->M5. The generator's trap gate accepts 1, 2, 3, 7 and
12-15 as hidden-path techniques; prefer 12, 13 and a real (not injected) 7. M1 parallel entry alone is weak (12%).

## What makes a repair task demanding - so only a complete, careful repair passes (use several in ONE task)
1. **Unnamed sibling path.** The report describes the reported trigger only. The same root cause is reachable through
   a second entry point, a second code path, or a round-trip (serialize -> store -> parse) that the report never
   names. Give it its own security test. Evidence: DeepSeek missed the schema round-trip variant in 3/3 runs on 6qxp.
2. **Already-protected-looking code.** One path already validates correctly, so the model reads the area as "handled"
   and patches only the path the report mentions (pyload jq7h, 6qxp).
3. **Fix across a layer boundary.** The correct fix must reach from the entry layer into a deeper layer (e.g. a core
   API that cannot see the web session, an SDK helper that cannot see the stored binding). Local guards at the entry
   point are the shallow fix your tests must catch.
4. **One test per fix place.** Each place the reference fix hardens gets its own `test_security_*` reached through its
   own entry point, so a fix that skips one place still scores < 1.0. (Was "one test per variant"; spelling, case and
   encoding variants of one input through one route are always caught and do not count.)
5. **Boundary-hugging functional tests.** Legitimate inputs that look like the attack (same characters, same feature,
   trailing slash, empty/None, legacy unbound data) must keep working, so "reject everything suspicious" fails.
6. **Behavioural report, no localization, no scope.** Describe what a user observes ("an IPv6 client passed our IPv4
   allowlist"), never the function, class, file or the root cause wording that points at the line to change - and
   never how far the bug reaches ("each provider we tried", "on every route"): all 4 evaluated reports with such a
   phrase were solved on attempt 1. Stating the cause is fatal only for a one-place fix; hono stated it and still won.
7. **Parallel implementation.** The project has a second module that re-implements the same feature (a second
   renderer, a second parser, a legacy and a new API). The report describes the behaviour once; the fix must land in
   both. Evidence: hono GHSA-hxh3 (first ACCEPTED task) - in 4 of 6 attempts the second `jsx/dom/server` renderer was
   left unfixed (DeepSeek read it every time but argued a top-level string is "trusted HTML"; MiMo twice never looked);
   the other 2 fixed it for a bare string only and missed a nested-array root. Details: data/knowledge/failure_analyses/.
8. **Input-shape variants (RETIRED - do not use as a difficulty technique).** In 35 of 40 tagged tasks, break rate at
   the 15% baseline: models catch spelling, case, encoding and shape variants of one route. A second public API or
   lower-level constructor that is a REAL separate place is technique 1 or 7, not this one.
9. **A "must keep working" clause that argues against the fix.** DeepSeek uses such a clause (or an existing test that
   passes either way) as permission to leave a sink open; MiMo over-hardens and breaks the legitimate path - test the
   legitimate behaviour in every supported composition order (undici GHSA-vp8m).
10. **Prefer big fixes (RETIRED as a difficulty lever).** Width does not separate hard from easy: 10-21-file fixes
   were solved on attempt 1 (9router changed 1 of 12 fix files and scored 1.0). Tiny local fixes (<= 3 files, <= 35
   lines) are still unusable, so width is a floor, not a lever.
11. **A compatibility contract pinned by an existing repo test.** Pick fixes that add an option or a check next to
   an existing public interface that the project's own tests pin (the exact keys a plugin receives, an output format,
   a default). The obvious fix changes that interface; a careful fix keeps it. Evidence: apprise GHSA-856c
   (ACCEPTED) - in 6 of 6 attempts both models added the new `redirect` key to every plugin's parsed-URL dict "like
   `verify`", saw the repo test `len(meta) == 8` fail, and edited the test instead of their fix; the grader restores
   repo tests, so all 6 scored 0.99. The upstream fix kept the key out unless set. Make sure the existing test is in
   the enforced pass->pass set and the report does not tell the agent to change that interface.
12. **Feature-absent sibling (catalogue M4, highest measured miss rate: 7 of 22).** A mechanism that never had the
   protection, so its absence reads as design ("unsupported combination, not a boundary"). jackson: the any-setter
   route has no view code at all. Test it through its own entry point.
13. **Producer off the check's path (M6, 5 of 17).** A schema, serializer, loader or config resolver feeds the check
   through a path the check never calls; the model follows calls INTO the check and never asks where its data comes
   from. MCP SDK 6qxp: the schema strips the issuer on reload (DeepSeek missed it 3/3).
14. **Wrong object (M10).** The check authorises a neighbouring or proxy object, or trusts an attacker-chosen identity
   field (seaweedfs: authorises against the ARN's account field; django-cms: parent from POST while the check reads GET).
15. **Merged / defaults route (M5).** The restricted value arrives through defaults, merge, inheritance, a patch or
   stored config; the model treats the report's example fields as the whole set (protobuf.js: inherited options).

## Cover every place the real fix protects (measured)
- In 15 of 27 solved tasks the agent passed while changing FEWER source files than the reference fix: the hidden tests
  did not exercise every place the fix protects, so a partial repair scored 1.0. Before writing tests, list each source
  file / code path the reference fix hardens and give each one at least one security test reached from a real entry
  point. A repair that skips any of those places must fail. (Live numbers: data/knowledge/solved_profile.md.)

## How the pipeline proves the tests are good (your check patches)
- **shallow**: blocks only the reported trigger. At least one security test must still fail on it (technique 1/4).
- **removal**: disables or over-restricts the feature. At least one functional test must fail on it (technique 5).
- **alternative**: a correct fix of a different design. Every test must pass on it (tests are implementation-agnostic).
- **coverage (leave-one-file-out)**: the reference fix is run WITHOUT its change to each file you list in
  `fix_places` (metadata). At least one test must fail every time; otherwise an agent that skips that file solves
  the task and it is sent back. List only files whose change closes part of the vulnerability.
- These are executed in the real environment. A wrong outcome sends the task back with the failing test names.

## Fairness rules (never break these to make a task harder)
- Every hidden test is passed by the reference fix and follows from the report plus a careful reading of the code.
- Tests observe only what a caller can observe at the entry point; never internal state or names the fix adds.
- No timing races, no network, no randomness.
- **Never test a number the report does not state.** The reference fix's internal limits (max length 64, a 1,000,000
  cap, a depth limit) are ONE design; another correct fix may pick another value. (Most common rejection so far:
  pypdf, source-map-js.) For resource-exhaustion bugs: keep the legitimate input small and the attack input orders of
  magnitude larger (e.g. 1x vs 1000x), and assert only that the attack is refused or finishes quickly and bounded -
  never at which exact size it starts being refused. If a boundary matters, the report must state it.
- **Variants must share the reported root cause.** Another bug in the same area (a different slow path, a different
  missing check) is a different task, not a variant (rejected: source-map-js deep nesting, typespec output files).
- **Never map every exception to "blocked".** Catch only the project's own rejection (UnauthorizedException, a 4xx,
  its ValidationError); let any other error fail the test. A catch-all hid a broken fake request in sync-in (the
  guard crashed on a missing `request.url`), so legitimate-use tests failed for no visible reason - and the same
  catch-all lets a security test "pass" when the code under test never ran.
- **"Must keep working" means it works today.** Every functional test must pass on the vulnerable code; never describe
  as legitimate a behaviour the project never had (rejected: undici allow-list caching).

## Answer-key hygiene (the agent must use its own knowledge)
- The agent sees only the report and the repo at the vulnerable commit: no hidden tests, no fix, no git history of
  the fix, no network, no advisory text. Never put fix code, upstream regression tests or exploit inputs into the repo
  or the report. Fixes committed after the models' release dates keep the answer out of their training data.


# Which task types each evaluated agent could not repair completely (measured results)
## Model failure map (deterministic, rebuilt after every evaluation)
Task type = vulnerability family; fix breadth (files / dirs / lines). Timeouts are not failures.
### DeepSeek
- FAILED on (5): auth / session / credentials; wide multi-layer fix (8 files / 4 dirs / 174 lines) - partial fix: closed 5 of 6 attack variants in all 3 runs and stopped on its own (it thought it was done); left open every time: schema_roundtrip_keeps_binding | information exposure + SSRF / redirect; wide multi-layer fix (127 files / 7 dirs / 229 lines) - closed the hole but broke legitimate behaviour (test_notify_multi_instance_decoration) in all 3 runs and stopped on its own (it thought it was done) | injection (code / command / markup); wide multi-layer fix (6 files / 3 dirs / 156 lines) - partial fix (and broke legitimate behaviour in 1 of 3 runs: runtime-tests/node/index.test.ts > stream > Should call onAbort) in all 3 runs and stopped on its own (it thought it was done); left open every time: render_to_string_escapes_array_root | path / file handling; wide multi-layer fix (10 files / 3 dirs / 236 lines) - partial fix: closed 4 of 5 attack variants in all 3 runs and stopped on its own (it thought it was done); left open every time: toolbox_symlink_escape | auth / session / credentials; local fix (1 files / 1 dir / 33 lines) - partial fix: closed 6 of 7 attack variants in its run and stopped on its own (it thought it was done); left open every time: exp_at_epoch_boundary
- Timed out on (0): none
- Solved (35), by vulnerability family: resource exhaustion (DoS) x7, auth / session / credentials x7, other x6, path / file handling x3, parsing / type confusion x3, injection (code / command / markup) x2, injection (code / command / markup) + information exposure x1, parsing / type confusion + SSRF / redirect x1, information exposure x1, auth / session / credentials + injection (code / command / markup) x1, auth / session / credentials + path / file handling x1, deserialization / prototype pollution x1, auth / session / credentials + path / file handling + information exposure x1
### MiMo
- FAILED on (3): information exposure + SSRF / redirect; wide multi-layer fix (127 files / 7 dirs / 229 lines) - closed the hole but broke legitimate behaviour (test_notify_multi_instance_decoration) in all 3 runs and stopped on its own (it thought it was done) | injection (code / command / markup); wide multi-layer fix (6 files / 3 dirs / 156 lines) - partial fix (and broke legitimate behaviour in 1 of 3 runs: runtime-tests/node/index.test.ts > stream > Should call onAbort) in all 3 runs and stopped on its own (it thought it was done); left open every time: render_to_string_escapes_array_root | auth / session / credentials; wide multi-layer fix (10 files / 5 dirs / 120 lines) - closed the hole but broke legitimate behaviour (storage_with_custom_lookup_same_host) in its run and stopped on its own (it thought it was done)
- Timed out on (2): auth / session / credentials; wide multi-layer fix (8 files / 4 dirs / 174 lines) | auth / session / credentials; wide multi-layer fix (5 files / 4 dirs / 111 lines)
- Solved (7), by vulnerability family: auth / session / credentials x2, parsing / type confusion x2, injection (code / command / markup) x1, path / file handling x1, auth / session / credentials + path / file handling + information exposure x1
### Broke BOTH (replicate this shape): information exposure + SSRF / redirect; wide multi-layer fix (127 files / 7 dirs / 229 lines) | injection (code / command / markup); wide multi-layer fix (6 files / 3 dirs / 156 lines)


# Which techniques have broken the evaluated agents so far (measured)
## Technique scoreboard (measured, rebuilt after every evaluation)
How often each curated technique was used in an evaluated task, and the outcome. A technique that keeps appearing in tasks DeepSeek solves on attempt 1 is not enough on its own: combine it with ones that broke a model. Counts are per task.

Baseline: 6 of 40 tagged tasks broke at least one model (15%). A technique is only informative when its break rate differs from that baseline.

| # | Technique | Tasks | Broke both | Broke only DeepSeek | Broke only MiMo | Solved | Read |
|---|---|---|---|---|---|---|---|
| 1 | Unnamed sibling path | 20 | 2 | 2 | 1 | 15 | USE: 25% break rate vs 15% baseline (apprise, hono, @modelcontextprotocol/sdk, fast-jwt, undici) |
| 2 | Already-protected-looking code | 5 | 0 | 1 | 0 | 4 | neutral: 20% break rate (@modelcontextprotocol/sdk) |
| 3 | Fix across a layer boundary | 5 | 0 | 1 | 0 | 4 | neutral: 20% break rate (@modelcontextprotocol/sdk) |
| 4 | One test per fix place | 40 | 2 | 3 | 1 | 34 | BASELINE (in 40/40 tasks): necessary, not sufficient (apprise, hono, @modelcontextprotocol/sdk, nltk, fast-jwt, undici) |
| 5 | Boundary-hugging functional tests | 38 | 2 | 3 | 1 | 32 | BASELINE (in 38/40 tasks): necessary, not sufficient (apprise, hono, @modelcontextprotocol/sdk, nltk, fast-jwt, undici) |
| 6 | Behavioural report, no localization, no scope | 39 | 2 | 3 | 1 | 33 | BASELINE (in 39/40 tasks): necessary, not sufficient (apprise, hono, @modelcontextprotocol/sdk, nltk, fast-jwt, undici) |
| 7 | Parallel implementation | 9 | 2 | 0 | 1 | 6 | USE: 33% break rate vs 15% baseline (apprise, hono, undici) |
| 8 | Input-shape variants (RETIRED - do not use as a difficulty technique) | 35 | 2 | 2 | 1 | 30 | BASELINE (in 35/40 tasks): necessary, not sufficient (apprise, hono, nltk, fast-jwt, undici) |
| 9 | A "must keep working" clause that argues against the fix | 16 | 2 | 2 | 0 | 12 | USE: 25% break rate vs 15% baseline (apprise, hono, @modelcontextprotocol/sdk, fast-jwt) |
| 10 | Prefer big fixes (RETIRED as a difficulty lever) | 2 | 1 | 0 | 0 | 1 | too few uses to judge (but broke both models) (apprise) |
| 11 | A compatibility contract pinned by an existing repo test | 0 | 0 | 0 | 0 | 0 | too few uses to judge |
| 12 | Feature-absent sibling (catalogue M4, highest measured miss rate: 7 of 22) | 0 | 0 | 0 | 0 | 0 | too few uses to judge |
| 13 | Producer off the check's path (M6, 5 of 17) | 0 | 0 | 0 | 0 | 0 | too few uses to judge |
| 14 | Wrong object (M10) | 0 | 0 | 0 | 0 | 0 | too few uses to judge |
| 15 | Merged / defaults route (M5) | 0 | 0 | 0 | 0 | 0 | too few uses to judge |

_0 evaluated task(s) have no technique record._


# Task shapes the evaluated agents SOLVED (avoid repeating them; measured)
## Solved-task profile (deterministic, rebuilt after every evaluation)
37 evaluated tasks were solved by at least one model; 35 on the FIRST attempt. Median solve time 13 min. These are the shapes to avoid or to combine with the techniques that broke a model (see the technique scoreboard).
- Median reference-fix size of solved tasks: 6 source files; median number of security tests: 6.
- Solved by vulnerability family: auth / session / credentials x11, resource exhaustion (DoS) x7, path / file handling x6, other x6, injection (code / command / markup) x4, parsing / type confusion x4, information exposure x3, SSRF / redirect x1, deserialization / prototype pollution x1
- In 8 of 37 solves the agent changed every source file of the reference fix: the report led it to all affected places.

### Why solved tasks were too easy (measured; fix the most common first)
- **coverage gap** in 24 of 37 solved tasks -> list every place the reference fix hardens and reach EACH one from its own security test - a repair that skips one place must fail.
- **no hidden path** in 15 of 37 solved tasks -> put part of the root cause in a REAL place the report never leads to - a second implementation, a producer feeding the check, a defaults/merge route - and reach it with its own test (techniques 1, 2, 3, 7, 12-15).
- **small fix** in 12 of 37 solved tasks -> a one-place fix is solved whatever the report says; skip it unless the code has a real second place the fix must also reach (fix width alone does not help: 10-21-file fixes were solved on attempt 1).
- **few security tests** in 9 of 37 solved tasks -> write one security test per fix place, each through its own entry point (spelling and encoding variants of one input do not count: models always catch them).
- **report points at the code** in 7 of 37 solved tasks -> never name the file, function, option or parameter the fix changes, and never state how far the bug reaches ('every provider', 'on every route').

| Task | Family | Fix | Security tests | Techniques used | Solved by | Attempt | Minutes | Why it passed |
|---|---|---|---|---|---|---|---|---|
| 9router | auth / session / credentials | 13 files / 10 dirs / 257 lines | 6 | 1, 4, 5, 6, 8, 9 | DeepSeek | 1 | 2 | coverage gap (1/12 fix files changed) |
| @hono/oauth-providers | auth / session / credentials | 7 files / 7 dirs / 54 lines | 6 | 1, 4, 5, 6, 8, 10 | DeepSeek | 1 | 3 | - |
| msgpack5 | resource exhaustion (DoS) | 2 files / 2 dirs / 40 lines | 7 | 1, 4, 5, 6, 8 | DeepSeek | 1 | 4 | small fix |
| nltk | other | 6 files / 2 dirs / 163 lines | 5 | 4, 5, 6, 8 | DeepSeek | 1 | 4 | coverage gap (1/7 fix files changed); report points at the code: grammar; no hidden path; few security tests |
| ip-address | parsing / type confusion | 3 files / 1 dir / 25 lines | 6 | 4, 5, 6, 8 | DeepSeek | 1 | 5 | small fix; report points at the code: Address4, Address6; no hidden path |
| @xmldom/xmldom | other | 3 files / 2 dirs / 37 lines | 10 | 1, 2, 4, 5, 6, 8, 9 | DeepSeek | 1 | 6 | small fix |
| vibe-trading-ai | auth / session / credentials + path / file handling + information exposure | 17 files / 5 dirs / 618 lines | 6 | 3, 4, 5, 6, 8 | DeepSeek | 1 | 6 | coverage gap (4/23 fix files changed); report points at the code: Settings, service |
| pyload-ng | auth / session / credentials | 2 files / 2 dirs / 9 lines | 4 | 4, 5, 6 | DeepSeek | 1 | 8 | coverage gap (1/2 fix files changed); small fix; no hidden path; few security tests |
| pyload-ng | auth / session / credentials | 4 files / 2 dirs / 58 lines | 7 | 4, 5, 6, 8 | DeepSeek | 1 | 8 | coverage gap (3/5 fix files changed); no hidden path |
| n8n | injection (code / command / markup) | 9 files / 7 dirs / 343 lines | 6 | 1, 4, 5, 8 | DeepSeek | 1 | 8 | coverage gap (5/9 fix files changed); report points at the code: execute |
| @vitest/browser | auth / session / credentials + path / file handling | 8 files / 4 dirs / 104 lines | 4 | 1, 2, 4, 5, 6, 8, 9 | DeepSeek | 1 | 9 | coverage gap (6/8 fix files changed); report points at the code: upload; few security tests |
| pymongo | other | 3 files / 3 dirs / 74 lines | 6 | 4, 5, 6, 7, 8 | DeepSeek | 1 | 10 | small fix |
| adm-zip | parsing / type confusion | 2 files / 2 dirs / 11 lines | 6 | 4, 5, 6, 8 | DeepSeek | 1 | 11 | small fix; no hidden path |
| react-router | other | 8 files / 7 dirs / 113 lines | 5 | 1, 3, 4, 5, 6, 7, 8 | DeepSeek | 1 | 12 | coverage gap (1/6 fix files changed); report points at the code: server; few security tests |
| pyload-ng | auth / session / credentials | 5 files / 4 dirs / 111 lines | 7 | 4, 5, 6 | DeepSeek | 1 | 12 | no hidden path |
| datamodel-code-generator | path / file handling | 1 files / 1 dir / 31 lines | 6 | 4, 5, 6, 9 | DeepSeek | 1 | 13 | small fix; no hidden path |
| @sync-in/server | other | 21 files / 8 dirs / 224 lines | 6 | 1, 4, 5, 6, 7, 8, 9 | DeepSeek | 1 | 13 | coverage gap (12/20 fix files changed) |
| hono | path / file handling | fix size unknown | 4 | 1, 4, 5, 6, 8, 9 | DeepSe


# Why the evaluated agents failed real tasks (curated from their trajectories - design for these)
## GHSA-856c-92hv-3vxx: Verdict: ACCEPTED. Both models failed every run. DeepSeek scored 0.99 on all three attempts and MiMo scored 0.99 on all three. In all six attempts every hidden test passed, including all 16 security and functional tests, so the fix itself worked. Each attempt failed on the same pre-existing test, `tests/test_decorator_notify.py::test_notify_multi_instance_decoration`, which asserts `len(meta) == 8`. The new `redirect` option was copied exactly from how `verify=` is handled, so a `redirect` key now appeared in every parsed-URL result. The agents saw this test fail and changed the expected count to 9. Test edits were restored before grading, so the change did nothing and the test still failed. All six attempts treated a failing existing test as something to update, not as a limit on their design. None of them changed `apprise/asset.py`, which the reference fix did change. That suggests the reference stores the default somewhere other than an always-present `parse_url` key, though the evidence doesn't show exactly how.
#### Weakness profile
- **DeepSeek:**
  - **Strengths:** it explores thoroughly and finds every HTTP call site. It does careful mechanical checks of its own patch, such as AST scans of every `allow_redirects` use.
  - **Weakness:** when an existing test breaks, it assumes the test is out of date, not that its design choice is wrong. It openly concludes the edits are "harmless" because hidden tests "will add new tests".
  - **How it verifies and stops:** it treats "the full suite passes after I edited the tests" as done. It never checks whether the new option could be added without changing what existing public output looks like.
- **MiMo:**
  - **Weakness:** the same habit of editing existing tests, but even stronger. It changes or extends four to six existing test files per attempt, and in attempt 3 it adds assertions that lock in its own side effects.
  - **Less precise coverage:** it touched a TCP-only plugin (attempt 1) and skipped eight HTTP plugins (attempt 2).
  - **Why it stops:** its own tests pass, and it takes that as proof of correctness.
- **Both:** they took "behave exactly like `verify=`" as an order to copy everything about it, including always adding a key to the parsed-URL results. Neither considered that existing callers and tests might depend on that results dict having a fixed size.
#### Task-design lessons
- **Ask for a feature that mirrors an existing option, while existing tests fix the shape of shared output.** Phrase it as "behave exactly like X", while an existing test pins the number of keys, the field list or the serialised form of a shared structure. Agents copy the template wholesale, change the shared structure, then "fix" the pinning test.
- **Keep breakage-detecting tests in files the agent will naturally edit.** Enforce existing tests and restore any test edits before grading. Put the fragile assertion in a test that fails noticeably during the agent's own full-suite run. Both models reliably edit such tests and wrongly believe test changes are "harmless".
- **Make the reference fix put new state somewhere unexpected.** Here that was a central config or defaults object (`asset.py`) instead of the obvious parser. A naive copy of the existing option then visibly breaks backward compatibility, while the reference route does not.
- **Grade the security behaviour on every call site, not a sample.** Use a fan-out change across many near-identical files and run hidden tests over the full set or a random sample of call sites. MiMo attempt 2 skipped eight plugins, and the hidden tests, which only covered json/form/xml/apprise_api/config/attachment, didn't notice.
- **State backward compatibility outright, but leave the danger implicit.** Write "existing behaviour stays as it is today" and nothing more. Agents read that as runtime behaviour only. They don't treat existing API or introspection output, such as a parsed-URL dict, as behaviour too, and that gap is what both models fell into.

## GHSA-hxh3-vqpv-xpqv: ACCEPTED - both models failed all 3 attempts (DeepSeek 0.83/0.83/0.94, MiMo 0.89/0.94/0.89, Claude Code agent), every run stopped on its own (no timeout). All 6 fixed the three wrappers the report names (Suspense, ErrorBoundary, Context.Provider) and all 6 left `renderToString([unsafe, [unsafe]])` unescaped.
#### Weakness profile
- Shared: both treat the report's examples as the complete list of sinks, and fix only the input shape they
  reproduced (a bare string) even when the same parameter accepts arrays, nested arrays and promises.
- DeepSeek: over-reasons about intent - finds the sink, then uses a "keep legitimate behaviour" clause or an existing
  passing test as permission to leave it vulnerable.
- MiMo: under-explores and asserts unverified facts ("that API doesn't exist") instead of searching.
#### Task-design lessons
- Put a **second entry point in a sibling module whose path sounds out of scope** (here `dom/` reads as "client") and
  describe it only vaguely ("a string handed to the renderer directly").
- Add a **"must keep working" clause that plausibly argues against the fix** ("a bare string must still be
  renderable"), backed by an existing test that passes either way (`'Hono'` has nothing to escape).
- **Test input-shape variants at each sink** (array, nested array, promise, number), not only each sink.
- Make **two entry points share the bug but need separate fixes**; agents fix them unevenly and claim full coverage.
- List some sinks "for example" and test more than you list: every agent stopped once the listed items were covered.

## GHSA-6qxp-vccf-f47h: DeepSeek failed 3/3 (0.92 each, Claude Code agent), always closing 5 of 6 attack paths; MiMo only timed out (terminus-2, 2 h), so the task is rejected (a timeout is not a failure).
#### Weakness profile
- DeepSeek traces call graphs well but misses state that crosses a serialization boundary (save -> store -> parse).
- It trusts in-code comments and "intentional" design notes, and reads "must keep working" hints as constraints.
- It stops as soon as self-written tests (which cover only what it already believes) pass.
#### Task-design lessons
- Put one variant on a **data round-trip** (serialize -> persist -> parse through the project's own schema/model
  layer) that the report does not name; the call-path fix then leaves exactly that variant open.
- Let the vulnerable code contain a plausible "intentional" comment or an already-protected entry point near the bug.
- Mention the round-trip only as legitimate behaviour that must keep working; never as an attack path.

## GHSA-p4rw-rvv2-7xwr: DeepSeek failed all 3 attempts (0.93 each, always the toolbox symlink escape left open); MiMo failed 2 (0.87, toolbox + MTE left open) and solved 1. Rejected (MiMo solved). No timeouts; every run stopped on its own.
#### Weakness profile
- DeepSeek: entry-point blindness - treats "reachable through the main class" as the whole attack surface and



# Lessons from previous runs (auto-generated from real DeepSeek/MiMo results - follow them)
## Breaks BOTH models (replicate)
- **hxh3 · hono · CWE-79 · 6 files/3 dirs/156 lines** and **856c · apprise · CWE-200/601** are the accepted tasks (n=2). hono: both models scored 0.83–0.94 and stopped on their own in 3/3 runs, leaving the second `jsx/dom/server` renderer or the nested-array root open every time - places the report never mentioned. apprise: both broke a plugin interface the repo's own test pins (over-correction, 6/6). Check `stream > Should call onAbort` for flakiness before reusing hono.
- **Combine in one task:**
  1. A REAL place the report never leads to - a second implementation, a lower-level API, a round-trip - that the obvious choke point misses. This beat DeepSeek (n=3). Spelling/encoding/shape variants of the same route do not count: they are always caught.
  2. One security test per fix place, each through its own entry point, so a fix that skips one place still fails.
  3. A falsy or boundary variant (`0`, `""`, `[]`). This beat DeepSeek (tentative, n=1: x937).
  4. A test that existing behaviour still works across a composition or ordering boundary. This beat MiMo (tentative, n=1: vp8m).
  5. A path that is already safe, as a decoy. This beat MiMo (tentative, n=1: jq7h).
  6. Fast test suites. A MiMo timeout counts as "too slow", not as a failure (6qxp, vp8m).

## Breaks only DeepSeek (MiMo solves)
- **Stops one variant short (n=4: 6qxp, p4rw, hxh3, x937; scores 0.92–0.95).** It patches the first layer it finds, then declares itself done.
  - **p4rw · nltk · CWE-22/59.** It put the check in `CorpusReader.abspath` and missed the bare-string entry points `StandardFormat.open`, `XMLCorpusView` and `load_ace_file`. MiMo fixed the shared `FileSystemPathPointer`.
  - **x937 · fast-jwt · CWE-613 · 1 file/33 lines.** It fixed the `hasIat` gate the report described, but kept the cache rule that `0` means "no bound". The `exp: 0` case stayed open (13/14 tests passed). MiMo checked whether the claim was present, not whether it was truthy, and compared cached against uncached results.
  - **6qxp.** It saw that the binding is lost on a schema round-trip and stopped anyway.
- **Hiding file names is not enough.** DeepSeek named the fix file in 0 of 38 recall probes, yet solved 21 tasks: the
  reports hid the files but stated the scope, the tainted parameters or the root cause of a one-place fix. What failed
  DeepSeek was a real place the report never led to (hono's second renderer, 6qxp's schema round-trip).

## Breaks only MiMo (DeepSeek solves)
- **vp8m · undici · CWE-346 (tentative).** Security tests reached 1.0, but reuse in `compose(cache(), dns())` broke. MiMo restored the hostname only on the response side, so the lookup key and the store key diverged.
- **jq7h · pyload · CWE-613 (tentative).** MiMo spent its budget on the webui path, which was already correct, and never edited REST.
- **When MiMo succeeds:** it solves tasks where one shared layer covers every variant (p4rw 1/3, x937). It has 3 counted failures.
- **Evidence on MiMo is thin.** Its p90 step time is about 400 s vs about 40 s for DeepSeek. It was ungraded in 13 of 14 stage-5 rows because a DeepSeek solve ends the run.

## Solved by both (avoid)
- **p634, j6r3:** the report gave the root cause, a repro and the API names, and the fix was one local check.
- **pqg4, x33g:** both models named the fix location.
- **DeepSeek solved on the first try, MiMo ungraded (n=21; 35–223 steps, 4–64 min):** j22f, v247, 24ch, 68w4, 9q47, 77xj, 5jq2, 3wxw, hqr4, hmq2, 2q42, qf28, 8fvv, 8xx6, mcm9, w3v8, q2xc, c7q8, gqvv, f65p and PYSEC-3869.
  - Each had one choke point that every variant passed through.
  - Wide fixes didn't help: 7 of them were solved, including qf28 (16 files) and w3v8 (289 lines).

## Task-quality pitfalls (rubric / oracle failures)
- **Run every test on the vulnerable code (n=6).** Security tests must fail there and functional tests must pass.
  - 8r5x crashed before the injection ran.
  - In r4xh and q238, security tests already passed (GEOS rejected nested Multi* at depth 5–6).
  - mcm9 and vp8m had functional tests that required new behaviour.
  - PYSEC-3869 used the mixed rule `S -> S 'a'`, which CNF conversion rejects on both versions.
- **Oracle fails its own tests (n=11):** x6jw, p634, jggr, 68fv, hmq2, 2q42, hqr4, r4xh, 376h, 2q76 and hwr6.
  - If every functional test scores 0.0, the harness or fixture is broken. Regenerating fixed hmq2, 2q42 and hqr4.
  - Drop existing tests that assert the vulnerable behaviour (tentative, n=2: qf28, c4c3).
- **Tests accept only one fix shape (n=9):**
  - 68w4, 9q47, jq7h, qf28.
  - 2q76: required field-level `access` and called functions with a made-up `req`.
  - x78j: rejected raise, `SystemExit` and drop fixes.
  - p63j: aliased `@vitest/browser` to `utils.ts` and used fake contexts.
  - PYSEC-3819: mocked only the module-level `requests.get`.
  - 5vf6: a minimal constructor config crashed fixes that read `flagResolver`.

  Accept reject, raise, drop and sanitize fixes. Test through the public HTTP, CLI or RPC entry point. Mock at the transport layer and import through the package entry.
- **Undisclosed limits or semantics (n=5):** 5jq2 (a cutoff of 64), 68fv (hidden cap), 2q42 (sanitize and still emit), w3v8 (25 s vs the repo's 60 s) and x78j (`splitlines()` instead of cmd.exe rules). State limits in the report or use ≥100× margins, and model the real sink.
- **Weak tests (n=5):** x937, 6qxp, qf28, r4xh and 2q76 (deny-all passed). Assert the output content and make over-blocking fail. Count operations instead of timing them (tentative, n=2).
- **No network in tests (tentative, n=1: 5vf6).** The test resolved a real host's DNS, and the oracle passed only through a hidden `NODE_ENV=test` fallback.
- **Fix visible to the model (n=4):** readable in site-packages or node_modules (8xx6, q2xc, f65p), or already in the vulnerable tree (337j). Uninstall released copies.
- **Bad existing-test files (n=4):** helper, manual and DB-integration files. Exclude them.
- **Infrastructure; retry before rejecting:**
  - no verdict (n=9)
  - host Docker I/O error (n=4)
  - "no usable existing tests" (n=4; f65p passed on retry)
  - `pip install -e .` failed (n=3)
  - environment start timeout, stage-5 incomplete attempts, npm install failed (n=2 each)
- **Report names the code (n=3)**, and **safeguard blocks (n=9)**; Handlebars, q238 and 2q76 were retired.

## Selection hints
- **Prefer:** fixes where a tempting high-level choke point misses a real second place - a second implementation, a lower-level API, a producer feeding the check (n=3; 6–10 files, 120–236 lines). At screening, ask whether one function sees every variant. If it does, skip.
- **Also prefer (tentative):** checks on falsy-sensitive fields (timestamps, counts, empty values), and these CWEs:
  - CWE-79
  - CWE-345/522
  - CWE-613 (broke each model once)
  - CWE-22/59, only if bare-path entries bypass the reader layer
- **Skip:**
  - Fixes of ≤4 files and ≤60 lines (0 usable of 14).
  - DoS CWE-400/407/409/674/1284/1333 (0 usable).
  - CWE-22/73 fixed in one path builder (n=3).
  - CWE-91, URI parsers and SSRF fixes that need DNS (tentative).
  - Code generators.
  - Oracle patches over 80k characters (n=3).
  - Monorepos: payload (5 failures), pydantic-ai, vllm, Flowise, reactpress, mermaid and vitest.
  - PyPI repos where `pip install -e .` fails.
- **pyload:** use only with the real app's test client.
- **Recall:** reject if both models name the fix (n=2). Otherwise recall doesn't predict the outcome.


# Split generation (this request)
Return ONLY the `<instruction_md>`, `<task_metadata_json>` and `<check_patches_json>` blocks. Do NOT write the
<hidden_tests_py> block; it is requested in a separate step. Keep the check patches minimal (only the edits that
demonstrate shallow / removal / alternative behaviour).

