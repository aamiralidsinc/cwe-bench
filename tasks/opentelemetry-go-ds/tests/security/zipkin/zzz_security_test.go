package zipkin_test

import (
	"bytes"
	"context"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"

	"github.com/go-logr/logr/funcr"

	"go.opentelemetry.io/otel/exporters/zipkin"
	"go.opentelemetry.io/otel/internal/global"
	"go.opentelemetry.io/otel/sdk/trace/tracetest"
)

const (
	secretPassword = "pw-8f3a1c"
	secretToken    = "tok-5d92be"
)

func secretCollectorURL(base string) string {
	return strings.Replace(base, "://", "://user:"+secretPassword+"@", 1) +
		"/api/v2/spans?token=" + secretToken
}

func TestSec_ZipkinMarshalLogURL(t *testing.T) {
	exp, err := zipkin.New(secretCollectorURL("http://zipkin.internal:9411"))
	if err != nil {
		t.Fatal(err)
	}
	var buf bytes.Buffer
	logger := funcr.New(func(_, args string) { buf.WriteString(args + "\n") }, funcr.Options{})
	logger.Info("exporter", "config", exp)

	logged := buf.String()
	if strings.Contains(logged, secretPassword) || strings.Contains(logged, secretToken) {
		t.Fatalf("diagnostic output carried collector URL credentials: %q", logged)
	}
}

func TestSec_ZipkinExportLogURL(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, _ *http.Request) {
		w.WriteHeader(http.StatusAccepted)
	}))
	defer srv.Close()

	var buf bytes.Buffer
	logger := funcr.New(func(_, args string) { buf.WriteString(args + "\n") }, funcr.Options{})
	exp, err := zipkin.New(secretCollectorURL(srv.URL), zipkin.WithLogr(logger))
	if err != nil {
		t.Fatal(err)
	}
	spans := tracetest.SpanStubs{{Name: "security-span"}}.Snapshots()
	if err := exp.ExportSpans(context.Background(), spans); err != nil {
		t.Fatal(err)
	}

	logged := buf.String()
	if strings.Contains(logged, secretPassword) || strings.Contains(logged, secretToken) {
		t.Fatalf("export diagnostic output carried collector URL credentials: %q", logged)
	}
}

func TestSec_ZipkinCreationLogURL(t *testing.T) {
	var buf bytes.Buffer
	orig := global.GetLogger()
	global.SetLogger(funcr.New(func(_, args string) { buf.WriteString(args + "\n") }, funcr.Options{Verbosity: 4}))
	t.Cleanup(func() { global.SetLogger(orig) })

	if _, err := zipkin.New(secretCollectorURL("http://zipkin.internal:9411")); err != nil {
		t.Fatal(err)
	}

	logged := buf.String()
	if strings.Contains(logged, secretPassword) || strings.Contains(logged, secretToken) {
		t.Fatalf("creation diagnostic output carried collector URL credentials: %q", logged)
	}
}
