package otlploghttp_test

import (
	"bytes"
	"context"
	"testing"

	"github.com/go-logr/logr/funcr"

	"go.opentelemetry.io/otel/exporters/otlp/otlplog/otlploghttp"
	"go.opentelemetry.io/otel/internal/global"
)

func TestFunc_LogExporterConfiguresAndReports(t *testing.T) {
	var buf bytes.Buffer
	orig := global.GetLogger()
	global.SetLogger(funcr.New(func(_, args string) { buf.WriteString(args + "\n") }, funcr.Options{Verbosity: 8}))
	t.Cleanup(func() { global.SetLogger(orig) })

	exp, err := otlploghttp.New(
		context.Background(),
		otlploghttp.WithEndpointURL("http://collector.internal:4318/v1/logs"),
	)
	if err != nil {
		t.Fatal(err)
	}
	if err := exp.Shutdown(context.Background()); err != nil {
		t.Fatal(err)
	}
	if buf.Len() == 0 {
		t.Fatal("endpoint-configuration diagnostic record was removed entirely")
	}
}
