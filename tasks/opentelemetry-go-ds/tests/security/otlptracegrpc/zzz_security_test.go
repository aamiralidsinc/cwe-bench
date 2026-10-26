package otlptracegrpc_test

import (
	"bytes"
	"strings"
	"testing"

	"github.com/go-logr/logr/funcr"

	"go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracegrpc"
)

const (
	secretPassword = "pw-8f3a1c"
	secretToken    = "tok-5d92be"
)

func TestSec_GRPCClientEndpoint(t *testing.T) {
	client := otlptracegrpc.NewClient(
		otlptracegrpc.WithEndpoint("user:"+secretPassword+"@collector.internal:4317?token="+secretToken),
		otlptracegrpc.WithInsecure(),
	)
	var buf bytes.Buffer
	logger := funcr.New(func(_, args string) { buf.WriteString(args + "\n") }, funcr.Options{})
	logger.Info("client", "config", client)

	logged := buf.String()
	if strings.Contains(logged, secretPassword) || strings.Contains(logged, secretToken) {
		t.Fatalf("diagnostic output carried endpoint credentials: %q", logged)
	}
}
