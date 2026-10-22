package dash

// Hidden functional tests: the admin console manages table buckets of any account.

import (
	"bytes"
	"context"
	"net/http"
	"net/http/httptest"
	"net/url"
	"strings"
	"testing"
	"time"
)

const zzConsoleARNPrefix = "arn:aws:s3tables:us-east-1:000000000000:bucket/"

// zzConsole is the admin console as `weed admin` builds it, pointed at the test filer.
func zzConsole(t *testing.T, f *zzFiler) *AdminServer {
	t.Helper()
	s := NewAdminServer("127.0.0.1:1", nil, "", 0)
	if s.bgCancel != nil {
		t.Cleanup(s.bgCancel)
	}
	s.cachedFilers = []string{string(f.addr)}
	s.lastFilerUpdate = time.Now()
	s.filerCacheExpiration = time.Hour
	return s
}

func zzConsoleCall(t *testing.T, h http.HandlerFunc, method, target, body string) *httptest.ResponseRecorder {
	t.Helper()
	req := httptest.NewRequest(method, target, bytes.NewReader([]byte(body)))
	if body != "" {
		req.Header.Set("Content-Type", "application/json")
	}
	rec := httptest.NewRecorder()
	h(rec, req)
	return rec
}

func TestFuncZZAdminConsoleManagesAnyAccountsBucket(t *testing.T) {
	f := zzStartFiler(t)
	f.seedTableBucket("alice-tb", "acct-alice", "")
	f.seedNamespace("alice-tb", "sales", "acct-alice")
	f.seedTableBucket("alice-empty", "acct-alice", "")
	s := zzConsole(t, f)

	data, err := s.GetS3TablesNamespacesData(context.Background(), zzConsoleARNPrefix+"alice-tb")
	if err != nil {
		t.Fatalf("console list namespaces of another account's bucket: %v", err)
	}
	found := false
	for _, ns := range data.Namespaces {
		if strings.Join(ns.Namespace, ".") == "sales" {
			found = true
		}
	}
	if !found {
		t.Fatalf("console namespace listing misses sales: %+v", data.Namespaces)
	}

	rec := zzConsoleCall(t, s.CreateS3TablesNamespace, http.MethodPost, "/api/s3tables/namespaces",
		`{"bucket_arn":"`+zzConsoleARNPrefix+`alice-tb","name":"ops"}`)
	if rec.Code >= 300 {
		t.Fatalf("console create namespace in another account's bucket: %d %s", rec.Code, rec.Body.String())
	}
	if !f.hasNamespace("alice-tb", "ops") {
		t.Fatalf("namespace ops not created")
	}

	rec = zzConsoleCall(t, s.DeleteS3TablesBucket, http.MethodDelete,
		"/api/s3tables/buckets?bucket="+url.QueryEscape(zzConsoleARNPrefix+"alice-empty"), "")
	if rec.Code >= 300 {
		t.Fatalf("console delete another account's bucket: %d %s", rec.Code, rec.Body.String())
	}
	if f.isTableBucket("alice-empty") {
		t.Fatalf("alice-empty still exists")
	}
}

func TestFuncZZAdminConsoleCreatesBucketForAccount(t *testing.T) {
	f := zzStartFiler(t)
	s := zzConsole(t, f)
	rec := zzConsoleCall(t, s.CreateS3TablesBucket, http.MethodPost, "/api/s3tables/buckets",
		`{"name":"carol-tb","owner":"acct-carol"}`)
	if rec.Code >= 300 {
		t.Fatalf("console create bucket for an account: %d %s", rec.Code, rec.Body.String())
	}
	if owner := f.bucketOwner("carol-tb"); owner != "acct-carol" {
		t.Fatalf("bucket owner = %q, want acct-carol", owner)
	}
}
