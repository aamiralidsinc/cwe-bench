package otlptrace_test

import (
	"bytes"
	"context"
	"strings"
	"sync"
	"testing"

	tracepb "go.opentelemetry.io/proto/otlp/trace/v1"

	"github.com/go-logr/logr/funcr"

	"go.opentelemetry.io/otel/exporters/otlp/otlptrace"
	"go.opentelemetry.io/otel/internal/global"
	"go.opentelemetry.io/otel/sdk/trace/tracetest"
)

type recordingClient struct {
	mu       sync.Mutex
	started  bool
	uploaded int
}

func (c *recordingClient) Start(context.Context) error {
	c.mu.Lock()
	c.started = true
	c.mu.Unlock()
	return nil
}
func (*recordingClient) Stop(context.Context) error { return nil }
func (c *recordingClient) UploadTraces(_ context.Context, spans []*tracepb.ResourceSpans) error {
	c.mu.Lock()
	c.uploaded += len(spans)
	c.mu.Unlock()
	return nil
}
func (c *recordingClient) stats() (bool, int) {
	c.mu.Lock()
	defer c.mu.Unlock()
	return c.started, c.uploaded
}

func TestFunc_WrapperStartAndExport(t *testing.T) {
	var buf bytes.Buffer
	orig := global.GetLogger()
	global.SetLogger(funcr.New(func(_, args string) { buf.WriteString(args + "\n") }, funcr.Options{Verbosity: 4}))
	t.Cleanup(func() { global.SetLogger(orig) })

	client := &recordingClient{}
	exp := otlptrace.NewUnstarted(client)
	if err := exp.Start(context.Background()); err != nil {
		t.Fatal(err)
	}
	if err := exp.ExportSpans(context.Background(), tracetest.SpanStubs{{Name: "legit-span"}}.Snapshots()); err != nil {
		t.Fatal(err)
	}

	started, uploaded := client.stats()
	if !started {
		t.Fatal("wrapped client was not started")
	}
	if uploaded == 0 {
		t.Fatal("export did not reach the wrapped client")
	}
	if buf.Len() == 0 {
		t.Fatal("lifecycle diagnostic record was removed entirely")
	}
}

func TestFunc_WrapperReportsKind(t *testing.T) {
	exp := otlptrace.NewUnstarted(&recordingClient{})
	var buf bytes.Buffer
	logger := funcr.New(func(_, args string) { buf.WriteString(args + "\n") }, funcr.Options{})
	logger.Info("exporter", "config", exp)
	if !strings.Contains(buf.String(), "otlptrace") {
		t.Fatalf("component kind missing from diagnostic record: %q", buf.String())
	}
}
