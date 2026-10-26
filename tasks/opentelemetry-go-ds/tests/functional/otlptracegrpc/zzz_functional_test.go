package otlptracegrpc_test

import (
	"bytes"
	"context"
	"strings"
	"testing"
	"time"

	"github.com/go-logr/logr/funcr"

	"go.opentelemetry.io/otel/exporters/otlp/otlptrace"
	"go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracegrpc"
)

func TestFunc_GRPCClientStartsAndReportsKind(t *testing.T) {
	client := otlptracegrpc.NewClient(
		otlptracegrpc.WithEndpoint("127.0.0.1:4317"),
		otlptracegrpc.WithInsecure(),
	)
	exp := otlptrace.NewUnstarted(client)
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()
	if err := exp.Start(ctx); err != nil {
		t.Fatal(err)
	}
	if err := exp.Shutdown(ctx); err != nil {
		t.Fatal(err)
	}

	var buf bytes.Buffer
	logger := funcr.New(func(_, args string) { buf.WriteString(args + "\n") }, funcr.Options{})
	logger.Info("client", "config", client)
	if !strings.Contains(buf.String(), "otlptracegrpc") {
		t.Fatalf("component kind missing from diagnostic record: %q", buf.String())
	}
}
