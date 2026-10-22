package s3api

// Hidden security tests: table storage authorization for the catalog index,
// batch operations, bucket usage summaries and catalog table creation.

import (
	"encoding/json"
	"net/http"
	"testing"
)

// zzSecuredSeedWithBob adds a second tenant (bob) to the secured seed.
func zzSecuredSeedWithBob(t *testing.T) *zzGateway {
	g := zzSecuredSeed(t)
	g.filer.seedTableBucket("bob-tb", "acct-bob", "")
	g.filer.seedNamespace("bob-tb", "sales", "acct-bob")
	return g
}

// zzSeedStoredTable stores a table entry the way the S3 Tables API lays it out.
func zzSeedStoredTable(f *zzFiler, bucket, ns, name, owner string) {
	md, _ := json.Marshal(map[string]interface{}{
		"name": name, "namespace": ns, "format": "ICEBERG",
		"ownerAccountId": owner, "versionToken": "v1", "metadataVersion": 1,
	})
	f.putDir("/buckets/"+bucket+"/"+ns+"/"+name, map[string][]byte{"s3tables.metadata": md})
}

func zzStoredTableARN(account, bucket, ns, name string) string {
	return "arn:aws:s3tables:us-east-1:" + account + ":bucket/" + bucket + "/table/" + ns + "/" + name
}

// A refused catalog table creation must not leave objects behind.
func TestSecZZCatalogCreateTableLeavesNothing(t *testing.T) {
	g := zzSecuredSeed(t)
	r := g.iceCall(zzBob, http.MethodPost, "/v1/alice-tb/namespaces/sales/tables",
		map[string]interface{}{"name": "intruder"}, nil)
	if zzIs2xx(r.status) {
		t.Fatalf("catalog created a table in another account's bucket: %d %s", r.status, string(r.body))
	}
	if g.filer.exists("/buckets/alice-tb/sales/intruder/metadata/v1.metadata.json") {
		t.Fatalf("a refused catalog create left a metadata file in alice-tb")
	}
	if g.filer.exists("/buckets/alice-tb/sales/intruder") {
		t.Fatalf("a refused catalog create left a table path in alice-tb")
	}
}

// A refused create-on-commit must not write the metadata file or create the
// table path either: the commit protocol can create a table, and a caller who
// may not create it must leave the bucket untouched.
func TestSecZZCatalogCreateOnCommitLeavesNothing(t *testing.T) {
	g := zzSecuredSeed(t)
	r := g.iceCall(zzBob, http.MethodPost, "/v1/alice-tb/namespaces/sales/tables/intruder", map[string]interface{}{
		"identifier":   map[string]interface{}{"namespace": []string{"sales"}, "name": "intruder"},
		"requirements": []map[string]interface{}{{"type": "assert-create"}},
		"updates":      []interface{}{},
	}, nil)
	if zzIs2xx(r.status) {
		t.Fatalf("catalog committed a table into another account's bucket: %d %s", r.status, string(r.body))
	}
	if !zzIs4xx(r.status) {
		t.Fatalf("a refused catalog create-on-commit returned %d, want a client error: %s", r.status, string(r.body))
	}
	if g.filer.exists("/buckets/alice-tb/sales/intruder/metadata/v1.metadata.json") {
		t.Fatalf("a refused catalog create-on-commit left a metadata file in alice-tb")
	}
	if g.filer.exists("/buckets/alice-tb/sales/intruder") {
		t.Fatalf("a refused catalog create-on-commit left a table path in alice-tb")
	}
}

// A refusal on the catalog must be reported as a client error, never as a
// server failure, and must change nothing.
func TestSecZZCatalogRefusalsAreClientErrors(t *testing.T) {
	g := zzSecuredSeedWithTable(t)
	calls := []struct {
		method, path string
		body         interface{}
	}{
		{http.MethodGet, "/v1/alice-tb/namespaces", nil},
		{http.MethodPost, "/v1/alice-tb/namespaces", map[string]interface{}{"namespace": []string{"intruder"}}},
		{http.MethodGet, "/v1/alice-tb/namespaces/sales/tables", nil},
		{http.MethodDelete, "/v1/alice-tb/namespaces/sales/tables/orders", nil},
	}
	for _, c := range calls {
		r := g.iceCall(zzBob, c.method, c.path, c.body, nil)
		if zzIs2xx(r.status) {
			t.Fatalf("%s %s succeeded for a caller who may not act: %d %s", c.method, c.path, r.status, string(r.body))
		}
		if !zzIs4xx(r.status) {
			t.Fatalf("%s %s refused with %d, want a client error: %s", c.method, c.path, r.status, string(r.body))
		}
	}
	if g.filer.hasNamespace("alice-tb", "intruder") {
		t.Fatalf("a refused request created a namespace in alice-tb")
	}
	if !g.filer.exists("/buckets/alice-tb/sales/orders") {
		t.Fatalf("a refused request removed a table in alice-tb")
	}
}

// A bucket usage summary must be scoped to the bucket's recorded owner, not to
// an account identifier the caller puts in the request.
func TestSecZZUsageIgnoresCallerSuppliedOwner(t *testing.T) {
	g := zzSecuredSeed(t)
	forged := "arn:aws:s3tables:us-east-1:acct-bob:bucket/alice-tb"
	r := g.tablesCall(zzBob, "GetTableBucketUsage", map[string]string{"tableBucketARN": forged}, nil)
	if zzIs2xx(r.status) {
		t.Fatalf("bucket usage was served to a caller who claimed the bucket by ARN: %d %s", r.status, string(r.body))
	}
	if zzHas(r.body, "acct-alice") || zzHas(r.body, `"namespaceCount"`) {
		t.Fatalf("bucket usage of another account was disclosed: %s", string(r.body))
	}
}

// A batch delete must not act on a table the caller may not delete just
// because another table in the same batch was allowed.
func TestSecZZBatchDeleteChecksEveryTable(t *testing.T) {
	g := zzSecuredSeedWithBob(t)
	zzSeedStoredTable(g.filer, "bob-tb", "sales", "mine", "acct-bob")
	zzSeedStoredTable(g.filer, "alice-tb", "sales", "orders", "acct-alice")
	r := g.tablesCall(zzBob, "BatchDeleteTables", map[string]interface{}{"tables": []string{
		zzStoredTableARN("acct-bob", "bob-tb", "sales", "mine"),
		zzStoredTableARN("acct-alice", "alice-tb", "sales", "orders"),
	}}, nil)
	if !g.filer.exists("/buckets/alice-tb/sales/orders") {
		t.Fatalf("batch delete removed another account's table: %d %s", r.status, string(r.body))
	}
	if !g.filer.exists("/buckets/bob-tb/sales/mine") {
		t.Fatalf("a refused batch delete removed the caller's own table")
	}
}

// The catalog table index must not reveal tables the caller cannot read.
func TestSecZZCatalogIndexHidesOtherTables(t *testing.T) {
	g := zzSecuredSeed(t)
	zzSeedStoredTable(g.filer, "alice-tb", "sales", "orders", "acct-alice")
	r := g.iceCall(zzBob, http.MethodGet, "/v1/alice-tb/tables", nil, nil)
	if zzIs2xx(r.status) && zzHas(r.body, "orders") {
		t.Fatalf("catalog index listed another account's table: %d %s", r.status, string(r.body))
	}
	if !zzIs2xx(r.status) && !zzIs4xx(r.status) {
		t.Fatalf("catalog index failed with %d", r.status)
	}
}

// On an open-by-default catalog, a caller the authenticator reports by name is
// still authenticated and must not fall open.
func TestSecZZCatalogNameOnlyCallerOnOpenDefaultIsEnforced(t *testing.T) {
	auth := &zzTokenAuth{names: map[string]string{"tok-bob": "bob"}, defaultAllow: true}
	g := zzNewGateway(t, nil, false, auth)
	g.filer.seedTableBucket("alice-tb", "acct-alice", "")
	g.filer.seedNamespace("alice-tb", "sales", "acct-alice")
	hdr := map[string]string{"X-Zz-Token": "tok-bob"}
	r := g.iceCall(zzAnon, http.MethodPost, "/v1/alice-tb/namespaces",
		map[string]interface{}{"namespace": []string{"intruder"}}, hdr)
	if zzIs2xx(r.status) || g.filer.hasNamespace("alice-tb", "intruder") {
		t.Fatalf("an open-by-default catalog let a name-only caller act as an owner: %d %s", r.status, string(r.body))
	}
}
