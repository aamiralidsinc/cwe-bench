package otlptracehttp_test

import (
	"bytes"
	"context"
	"io"
	"net/http"
	"net/http/httptest"
	"net/url"
	"strings"
	"testing"

	"github.com/go-logr/logr/funcr"

	"go.opentelemetry.io/otel/exporters/otlp/otlptrace"
	"go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracehttp"
	"go.opentelemetry.io/otel/internal/global"
	"go.opentelemetry.io/otel/sdk/trace/tracetest"
)

func TestFunc_HTTPExportReachesCollector(t *testing.T) {
	var gotMethod, gotPath, gotContentType string
	var gotBody []byte
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		gotMethod = r.Method
		gotPath = r.URL.Path
		gotContentType = r.Header.Get("Content-Type")
		gotBody, _ = io.ReadAll(r.Body)
		w.WriteHeader(http.StatusOK)
	}))
	defer srv.Close()

	u, err := url.Parse(srv.URL)
	if err != nil {
		t.Fatal(err)
	}
	client := otlptracehttp.NewClient(
		otlptracehttp.WithEndpoint(u.Host),
		otlptracehttp.WithInsecure(),
	)
	exp, err := otlptrace.New(context.Background(), client)
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { _ = exp.Shutdown(context.Background()) })

	if err := exp.ExportSpans(context.Background(), tracetest.SpanStubs{{Name: "legit-span"}}.Snapshots()); err != nil {
		t.Fatal(err)
	}

	if gotMethod != http.MethodPost {
		t.Fatalf("collector saw method %q", gotMethod)
	}
	if gotPath != "/v1/traces" {
		t.Fatalf("collector saw path %q", gotPath)
	}
	if gotContentType != "application/x-protobuf" {
		t.Fatalf("collector saw content type %q", gotContentType)
	}
	if len(gotBody) == 0 {
		t.Fatal("collector received no request body")
	}
}

func TestFunc_HTTPRejectedEndpointRecordPreserved(t *testing.T) {
	var buf bytes.Buffer
	orig := global.GetLogger()
	global.SetLogger(funcr.New(func(_, args string) { buf.WriteString(args + "\n") }, funcr.Options{}))
	t.Cleanup(func() { global.SetLogger(orig) })

	otlptracehttp.NewClient(
		otlptracehttp.WithEndpointURL("http://collector.internal:4318/%zz"),
		otlptracehttp.WithInsecure(),
	)
	if buf.Len() == 0 {
		t.Fatal("rejected-endpoint diagnostic record was removed entirely")
	}
}

func TestFunc_HTTPReportsKind(t *testing.T) {
	client := otlptracehttp.NewClient(
		otlptracehttp.WithEndpoint("collector.internal:4318"),
		otlptracehttp.WithInsecure(),
	)
	var buf bytes.Buffer
	logger := funcr.New(func(_, args string) { buf.WriteString(args + "\n") }, funcr.Options{})
	logger.Info("client", "config", client)
	if !strings.Contains(buf.String(), "otlptracehttp") {
		t.Fatalf("component kind missing from diagnostic record: %q", buf.String())
	}
}
