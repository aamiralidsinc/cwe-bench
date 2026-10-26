package zipkin_test

import (
	"bytes"
	"context"
	"io"
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
	collectorUser     = "collector-user"
	collectorPassword = "collector-pass"
	collectorToken    = "collector-token"
)

func TestFunc_ZipkinExportTargetPreserved(t *testing.T) {
	var gotPath, gotQuery, gotAuth, gotBody string
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		gotPath = r.URL.Path
		gotQuery = r.URL.RawQuery
		gotAuth = r.Header.Get("Authorization")
		b, _ := io.ReadAll(r.Body)
		gotBody = string(b)
		w.WriteHeader(http.StatusAccepted)
	}))
	defer srv.Close()

	collectorURL := strings.Replace(srv.URL, "://",
		"://"+collectorUser+":"+collectorPassword+"@", 1) +
		"/api/v2/spans?token=" + collectorToken

	var buf bytes.Buffer
	logger := funcr.New(func(_, args string) { buf.WriteString(args + "\n") }, funcr.Options{})
	exp, err := zipkin.New(collectorURL, zipkin.WithLogr(logger))
	if err != nil {
		t.Fatal(err)
	}

	spans := tracetest.SpanStubs{{Name: "legit-span"}}.Snapshots()
	if err := exp.ExportSpans(context.Background(), spans); err != nil {
		t.Fatal(err)
	}

	if gotPath != "/api/v2/spans" {
		t.Fatalf("collector saw path %q", gotPath)
	}
	if gotQuery != "token="+collectorToken {
		t.Fatalf("collector saw query %q", gotQuery)
	}
	if !strings.HasPrefix(gotAuth, "Basic ") {
		t.Fatalf("collector saw no basic authorization: %q", gotAuth)
	}
	if !strings.Contains(gotBody, "legit-span") {
		t.Fatalf("collector body did not carry the span: %q", gotBody)
	}
	if buf.Len() == 0 {
		t.Fatal("export diagnostic record was removed entirely")
	}
}

func TestFunc_ZipkinCreationRecordPreserved(t *testing.T) {
	var buf bytes.Buffer
	orig := global.GetLogger()
	global.SetLogger(funcr.New(func(_, args string) { buf.WriteString(args + "\n") }, funcr.Options{Verbosity: 4}))
	t.Cleanup(func() { global.SetLogger(orig) })

	if _, err := zipkin.New("http://zipkin.internal:9411/api/v2/spans"); err != nil {
		t.Fatal(err)
	}
	if buf.Len() == 0 {
		t.Fatal("creation diagnostic record was removed entirely")
	}
}
