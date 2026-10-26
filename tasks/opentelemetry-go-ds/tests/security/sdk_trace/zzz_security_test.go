package trace_test

import (
	"bytes"
	"context"
	"strings"
	"testing"

	"github.com/go-logr/logr/funcr"

	"go.opentelemetry.io/otel/internal/global"
	sdktrace "go.opentelemetry.io/otel/sdk/trace"
)

const (
	secretPassword = "pw-8f3a1c"
	secretToken    = "tok-5d92be"
	secretEndpoint = "user:" + secretPassword + "@collector.internal:4318?token=" + secretToken
)

type endpointExporter struct{}

func (*endpointExporter) ExportSpans(context.Context, []sdktrace.ReadOnlySpan) error {
	return nil
}
func (*endpointExporter) Shutdown(context.Context) error { return nil }
func (*endpointExporter) MarshalLog() any {
	return struct{ Endpoint string }{Endpoint: secretEndpoint}
}

func captureProviderLog(t *testing.T, opt func(sdktrace.SpanExporter) sdktrace.TracerProviderOption) string {
	t.Helper()
	var buf bytes.Buffer
	orig := global.GetLogger()
	global.SetLogger(funcr.New(func(_, args string) {
		buf.WriteString(args + "\n")
	}, funcr.Options{Verbosity: 4}))
	t.Cleanup(func() { global.SetLogger(orig) })
	tp := sdktrace.NewTracerProvider(opt(&endpointExporter{}))
	t.Cleanup(func() { _ = tp.Shutdown(context.Background()) })
	return buf.String()
}

func TestSec_TraceProviderBatchExporterEndpoint(t *testing.T) {
	logged := captureProviderLog(t, func(e sdktrace.SpanExporter) sdktrace.TracerProviderOption {
		return sdktrace.WithBatcher(e, sdktrace.WithMaxQueueSize(4242))
	})
	if strings.Contains(logged, secretPassword) || strings.Contains(logged, secretToken) {
		t.Fatalf("diagnostic output carried exporter endpoint credentials: %q", logged)
	}
}

func TestSec_TraceProviderSimpleExporterEndpoint(t *testing.T) {
	logged := captureProviderLog(t, sdktrace.WithSyncer)
	if strings.Contains(logged, secretPassword) || strings.Contains(logged, secretToken) {
		t.Fatalf("diagnostic output carried exporter endpoint credentials: %q", logged)
	}
}
