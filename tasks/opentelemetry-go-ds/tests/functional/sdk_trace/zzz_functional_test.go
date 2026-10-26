package trace_test

import (
	"bytes"
	"context"
	"strings"
	"sync"
	"testing"

	"github.com/go-logr/logr/funcr"

	"go.opentelemetry.io/otel/internal/global"
	sdktrace "go.opentelemetry.io/otel/sdk/trace"
)

type recordingExporter struct {
	mu    sync.Mutex
	spans int
}

func (e *recordingExporter) ExportSpans(_ context.Context, s []sdktrace.ReadOnlySpan) error {
	e.mu.Lock()
	e.spans += len(s)
	e.mu.Unlock()
	return nil
}
func (*recordingExporter) Shutdown(context.Context) error { return nil }
func (e *recordingExporter) count() int {
	e.mu.Lock()
	defer e.mu.Unlock()
	return e.spans
}

func captureInfo(t *testing.T) *bytes.Buffer {
	t.Helper()
	buf := &bytes.Buffer{}
	orig := global.GetLogger()
	global.SetLogger(funcr.New(func(_, args string) {
		buf.WriteString(args + "\n")
	}, funcr.Options{Verbosity: 4}))
	t.Cleanup(func() { global.SetLogger(orig) })
	return buf
}

func TestFunc_BatchProviderReportsAndExports(t *testing.T) {
	logged := captureInfo(t)
	exp := &recordingExporter{}
	tp := sdktrace.NewTracerProvider(sdktrace.WithBatcher(exp, sdktrace.WithMaxQueueSize(4242)))

	_, span := tp.Tracer("functional").Start(context.Background(), "work")
	span.End()
	if err := tp.ForceFlush(context.Background()); err != nil {
		t.Fatal(err)
	}
	if err := tp.Shutdown(context.Background()); err != nil {
		t.Fatal(err)
	}

	if exp.count() == 0 {
		t.Fatal("batch pipeline did not deliver spans to the exporter")
	}
	out := logged.String()
	for _, want := range []string{"TracerProvider created", "BatchSpanProcessor", "4242"} {
		if !strings.Contains(out, want) {
			t.Fatalf("provider record lost %q: %q", want, out)
		}
	}
}

func TestFunc_SimpleProviderReportsAndExports(t *testing.T) {
	logged := captureInfo(t)
	exp := &recordingExporter{}
	tp := sdktrace.NewTracerProvider(sdktrace.WithSyncer(exp))

	_, span := tp.Tracer("functional").Start(context.Background(), "work")
	span.End()
	if err := tp.Shutdown(context.Background()); err != nil {
		t.Fatal(err)
	}

	if exp.count() == 0 {
		t.Fatal("simple pipeline did not deliver spans to the exporter")
	}
	if out := logged.String(); !strings.Contains(out, "SimpleSpanProcessor") {
		t.Fatalf("provider record lost the processor kind: %q", out)
	}
}
