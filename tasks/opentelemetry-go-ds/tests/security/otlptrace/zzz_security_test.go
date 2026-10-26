package otlptrace_test

import (
	"bytes"
	"context"
	"strings"
	"testing"

	tracepb "go.opentelemetry.io/proto/otlp/trace/v1"

	"github.com/go-logr/logr/funcr"

	"go.opentelemetry.io/otel/exporters/otlp/otlptrace"
	"go.opentelemetry.io/otel/internal/global"
)

const (
	secretPassword = "pw-8f3a1c"
	secretToken    = "tok-5d92be"
	secretEndpoint = "user:" + secretPassword + "@collector.internal:4318?token=" + secretToken
)

type endpointClient struct{}

func (*endpointClient) Start(context.Context) error { return nil }
func (*endpointClient) Stop(context.Context) error  { return nil }
func (*endpointClient) UploadTraces(context.Context, []*tracepb.ResourceSpans) error {
	return nil
}
func (*endpointClient) MarshalLog() any {
	return struct{ Endpoint string }{Endpoint: secretEndpoint}
}

func TestSec_WrapperClientEndpoint(t *testing.T) {
	exp := otlptrace.NewUnstarted(&endpointClient{})
	var buf bytes.Buffer
	logger := funcr.New(func(_, args string) { buf.WriteString(args + "\n") }, funcr.Options{})
	logger.Info("exporter", "config", exp)

	logged := buf.String()
	if strings.Contains(logged, secretPassword) || strings.Contains(logged, secretToken) {
		t.Fatalf("diagnostic output carried wrapped client endpoint credentials: %q", logged)
	}
}

func TestSec_ExporterLifecycleClientEndpoint(t *testing.T) {
	var buf bytes.Buffer
	orig := global.GetLogger()
	global.SetLogger(funcr.New(func(_, args string) { buf.WriteString(args + "\n") }, funcr.Options{Verbosity: 4}))
	t.Cleanup(func() { global.SetLogger(orig) })

	exp := otlptrace.NewUnstarted(&endpointClient{})
	if err := exp.Start(context.Background()); err != nil {
		t.Fatal(err)
	}

	logged := buf.String()
	if strings.Contains(logged, secretPassword) || strings.Contains(logged, secretToken) {
		t.Fatalf("lifecycle diagnostic output carried client endpoint credentials: %q", logged)
	}
}
