package otlploghttp_test

import (
	"bytes"
	"context"
	"strings"
	"testing"

	"github.com/go-logr/logr/funcr"

	"go.opentelemetry.io/otel/exporters/otlp/otlplog/otlploghttp"
	"go.opentelemetry.io/otel/internal/global"
)

const (
	secretPassword = "pw-8f3a1c"
	secretToken    = "tok-5d92be"
)

func TestSec_LogSignalEndpointRecord(t *testing.T) {
	var buf bytes.Buffer
	orig := global.GetLogger()
	global.SetLogger(funcr.New(func(_, args string) { buf.WriteString(args + "\n") }, funcr.Options{Verbosity: 8}))
	t.Cleanup(func() { global.SetLogger(orig) })

	exp, err := otlploghttp.New(
		context.Background(),
		otlploghttp.WithEndpointURL(
			"https://user:"+secretPassword+"@collector.internal:4318/v1/logs?token="+secretToken,
		),
	)
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { _ = exp.Shutdown(context.Background()) })

	logged := buf.String()
	if logged == "" {
		t.Fatal("no diagnostic record was emitted for the configured endpoint")
	}
	if strings.Contains(logged, secretPassword) || strings.Contains(logged, secretToken) {
		t.Fatalf("log-signal diagnostic output carried endpoint credentials: %q", logged)
	}
}
