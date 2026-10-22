package s3api

// Hidden functional tests: legitimate use of the catalog index, batch deletes,
// bucket usage summaries and catalog table creation.

import (
	"net/http"
	"testing"
)

func TestFuncZZOwnerReadsBucketUsage(t *testing.T) {
	g := zzSecuredSeedWithBob(t)
	r := g.tablesCall(zzAlice, "GetTableBucketUsage", map[string]string{
		"tableBucketARN": "arn:aws:s3tables:us-east-1:acct-alice:bucket/alice-tb"}, nil)
	if !zzIs2xx(r.status) {
		t.Fatalf("owner GetTableBucketUsage failed: %d %s", r.status, string(r.body))
	}
	if !zzHas(r.body, "acct-alice") {
		t.Fatalf("usage response misses the bucket owner: %s", string(r.body))
	}
}

func TestFuncZZOwnerReadsOwnBucketUsage(t *testing.T) {
	g := zzSecuredSeedWithBob(t)
	r := g.tablesCall(zzBob, "GetTableBucketUsage", map[string]string{
		"tableBucketARN": "arn:aws:s3tables:us-east-1:acct-bob:bucket/bob-tb"}, nil)
	if !zzIs2xx(r.status) {
		t.Fatalf("owner GetTableBucketUsage on own bucket failed: %d %s", r.status, string(r.body))
	}
}

func TestFuncZZOwnerBatchDeletesOwnTables(t *testing.T) {
	g := zzSecuredSeedWithBob(t)
	zzSeedStoredTable(g.filer, "bob-tb", "sales", "mine", "acct-bob")
	zzSeedStoredTable(g.filer, "bob-tb", "sales", "mine2", "acct-bob")
	r := g.tablesCall(zzBob, "BatchDeleteTables", map[string]interface{}{"tables": []string{
		zzStoredTableARN("acct-bob", "bob-tb", "sales", "mine"),
		zzStoredTableARN("acct-bob", "bob-tb", "sales", "mine2"),
	}}, nil)
	if !zzIs2xx(r.status) {
		t.Fatalf("owner batch delete failed: %d %s", r.status, string(r.body))
	}
	if g.filer.exists("/buckets/bob-tb/sales/mine") || g.filer.exists("/buckets/bob-tb/sales/mine2") {
		t.Fatalf("owner batch delete left tables behind")
	}
}

func TestFuncZZOwnerCatalogIndexListsOwnTables(t *testing.T) {
	g := zzSecuredSeed(t)
	zzSeedStoredTable(g.filer, "alice-tb", "sales", "orders", "acct-alice")
	r := g.iceCall(zzAlice, http.MethodGet, "/v1/alice-tb/tables", nil, nil)
	if !zzIs2xx(r.status) {
		t.Fatalf("owner catalog index failed: %d %s", r.status, string(r.body))
	}
	if !zzHas(r.body, "orders") {
		t.Fatalf("owner catalog index misses own table: %s", string(r.body))
	}
}

func TestFuncZZOwnerCreatesTableOnCommitThroughCatalog(t *testing.T) {
	g := zzSecuredSeed(t)
	r := g.iceCall(zzAlice, http.MethodPost, "/v1/alice-tb/namespaces/sales/tables/fresh", map[string]interface{}{
		"identifier":   map[string]interface{}{"namespace": []string{"sales"}, "name": "fresh"},
		"requirements": []map[string]interface{}{{"type": "assert-create"}},
		"updates":      []interface{}{},
	}, nil)
	if !zzIs2xx(r.status) {
		t.Fatalf("owner create-on-commit failed: %d %s", r.status, string(r.body))
	}
	if !g.filer.exists("/buckets/alice-tb/sales/fresh/metadata/v1.metadata.json") {
		t.Fatalf("owner create-on-commit did not store metadata")
	}
	if !g.filer.exists("/buckets/alice-tb/sales/fresh") {
		t.Fatalf("owner create-on-commit did not register the table")
	}
}

func TestFuncZZOwnerCreatesTableThroughCatalog(t *testing.T) {
	g := zzSecuredSeed(t)
	r := g.iceCall(zzAlice, http.MethodPost, "/v1/alice-tb/namespaces/sales/tables",
		map[string]interface{}{"name": "fresh"}, nil)
	if !zzIs2xx(r.status) {
		t.Fatalf("owner catalog CreateTable failed: %d %s", r.status, string(r.body))
	}
	if !g.filer.exists("/buckets/alice-tb/sales/fresh/metadata/v1.metadata.json") {
		t.Fatalf("owner catalog CreateTable did not store metadata")
	}
	if !g.filer.exists("/buckets/alice-tb/sales/fresh") {
		t.Fatalf("owner catalog CreateTable did not register the table")
	}
}
