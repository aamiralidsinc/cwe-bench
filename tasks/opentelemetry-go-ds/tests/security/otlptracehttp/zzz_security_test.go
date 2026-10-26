package otlptracehttp_test

import (
	"bytes"
	"strings"
	"testing"

	"github.com/go-logr/logr/funcr"

	"go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracehttp"
	"go.opentelemetry.io/otel/internal/global"
)

const (
	secretPassword = "pw-8f3a1c"
	secretToken    = "tok-5d92be"
)

func TestSec_HTTPClientEndpoint(t *testing.T) {
	client := otlptracehttp.NewClient(
		otlptracehttp.WithEndpoint("user:"+secretPassword+"@collector.internal:4318"),
		otlptracehttp.WithInsecure(),
	)
	var buf bytes.Buffer
	logger := funcr.New(func(_, args string) { buf.WriteString(args + "\n") }, funcr.Options{})
	logger.Info("client", "config", client)

	logged := buf.String()
	if strings.Contains(logged, secretPassword) || strings.Contains(logged, secretToken) {
		t.Fatalf("diagnostic output carried endpoint credentials: %q", logged)
	}
}

func TestSec_HTTPRejectedEndpoint(t *testing.T) {
	var buf bytes.Buffer
	orig := global.GetLogger()
	global.SetLogger(funcr.New(func(_, args string) { buf.WriteString(args + "\n") }, funcr.Options{}))
	t.Cleanup(func() { global.SetLogger(orig) })

	// A malformed URL whose raw value still carries user-information and a query token.
	otlptracehttp.NewClient(
		otlptracehttp.WithEndpointURL(
			"http://user:"+secretPassword+"@collector.internal:4318/%zz?token="+secretToken,
		),
		otlptracehttp.WithInsecure(),
	)

	logged := buf.String()
	if logged == "" {
		t.Fatal("no diagnostic record was emitted for the rejected endpoint")
	}
	if strings.Contains(logged, secretPassword) || strings.Contains(logged, secretToken) {
		t.Fatalf("rejected-endpoint diagnostic output carried credentials: %q", logged)
	}
}
