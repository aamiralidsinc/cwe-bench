package s3api

// Hidden functional tests: legitimate table storage use through the S3 Tables
// API and the Iceberg REST catalog keeps working.

import (
	"net/http"
	"testing"
)

func zzExpectOK(t *testing.T, r zzResp, what string) {
	t.Helper()
	if !zzIs2xx(r.status) {
		t.Fatalf("%s: expected success, got %d: %s", what, r.status, string(r.body))
	}
}

func zzFuncSeed(t *testing.T) *zzGateway {
	g := zzNewGateway(t, nil, true, nil)
	g.filer.seedTableBucket("alice-tb", "acct-alice", "")
	g.filer.seedNamespace("alice-tb", "sales", "acct-alice")
	g.filer.seedTableBucket("alice-old", "acct-alice", "")
	g.filer.seedTableBucket("bob-tb", "acct-bob", "")
	return g
}

func TestFuncZZOwnerListsOwnBuckets(t *testing.T) {
	g := zzFuncSeed(t)
	r := g.tablesCall(zzAlice, "ListTableBuckets", map[string]interface{}{}, nil)
	zzExpectOK(t, r, "ListTableBuckets by the owner")
	names := zzListedBuckets(t, r)
	if !zzContains(names, "alice-tb") || !zzContains(names, "alice-old") {
		t.Fatalf("owner does not see her own buckets: %v", names)
	}
	r = g.tablesCall(zzBob, "ListTableBuckets", map[string]interface{}{}, nil)
	zzExpectOK(t, r, "ListTableBuckets by bob")
	if !zzContains(zzListedBuckets(t, r), "bob-tb") {
		t.Fatalf("bob does not see his own bucket")
	}
}

func TestFuncZZOwnerGetsAndDeletesOwnBucket(t *testing.T) {
	g := zzFuncSeed(t)
	r := g.tablesCall(zzAlice, "GetTableBucket", map[string]string{"tableBucketARN": zzBucketARN("alice-tb")}, nil)
	zzExpectOK(t, r, "GetTableBucket by the owner")
	if r.json(t)["name"] != "alice-tb" {
		t.Fatalf("unexpected GetTableBucket response: %s", string(r.body))
	}
	r = g.tablesCall(zzAlice, "DeleteTableBucket", map[string]string{"tableBucketARN": zzBucketARN("alice-old")}, nil)
	zzExpectOK(t, r, "DeleteTableBucket by the owner")
	if g.filer.isTableBucket("alice-old") {
		t.Fatalf("alice-old still exists after its owner deleted it")
	}
}

func TestFuncZZOwnerCreatesBucketNamespaceAndTable(t *testing.T) {
	g := zzFuncSeed(t)
	r := g.tablesCall(zzAlice, "CreateTableBucket", map[string]string{"name": "alice-new"}, nil)
	zzExpectOK(t, r, "CreateTableBucket by a user allowed to create table buckets")
	if owner := g.filer.bucketOwner("alice-new"); owner != "acct-alice" {
		t.Fatalf("new bucket owner = %q, want acct-alice", owner)
	}
	r = g.tablesCall(zzAlice, "CreateNamespace", map[string]interface{}{
		"tableBucketARN": zzBucketARN("alice-tb"), "namespace": []string{"marketing"}}, nil)
	zzExpectOK(t, r, "CreateNamespace by the owner")
	if !g.filer.hasNamespace("alice-tb", "marketing") {
		t.Fatalf("namespace not created")
	}
	r = g.tablesCall(zzAlice, "CreateTable", map[string]interface{}{
		"tableBucketARN": zzBucketARN("alice-tb"), "namespace": []string{"sales"},
		"name": "orders", "format": "ICEBERG"}, nil)
	zzExpectOK(t, r, "CreateTable by the owner")
	if !g.filer.exists("/buckets/alice-tb/sales/orders") {
		t.Fatalf("table not created")
	}
}

func TestFuncZZOwnerManagesBucketPolicy(t *testing.T) {
	g := zzFuncSeed(t)
	policy := `{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":"acct-bob","Action":"s3tables:GetTableBucket","Resource":"*"}]}`
	r := g.tablesCall(zzAlice, "PutTableBucketPolicy", map[string]string{
		"tableBucketARN": zzBucketARN("alice-tb"), "resourcePolicy": policy}, nil)
	zzExpectOK(t, r, "PutTableBucketPolicy by the owner")
	if g.filer.bucketPolicy("alice-tb") == "" {
		t.Fatalf("policy not stored")
	}
	r = g.tablesCall(zzAlice, "GetTableBucketPolicy", map[string]string{"tableBucketARN": zzBucketARN("alice-tb")}, nil)
	zzExpectOK(t, r, "GetTableBucketPolicy by the owner")
}

func TestFuncZZAdminsManageAnyBucket(t *testing.T) {
	for name, u := range map[string]zzUser{
		"Admin": zzRoot, "star": zzOpsStar, "s3-wildcard": zzOpsS3, "s3tables-wildcard": zzOpsTables,
	} {
		t.Run(name, func(t *testing.T) {
			g := zzFuncSeed(t)
			r := g.tablesCall(u, "GetTableBucket", map[string]string{"tableBucketARN": zzBucketARN("alice-tb")}, nil)
			zzExpectOK(t, r, "GetTableBucket by an administrator")
			r = g.tablesCall(u, "ListTableBuckets", map[string]interface{}{}, nil)
			zzExpectOK(t, r, "ListTableBuckets by an administrator")
			if names := zzListedBuckets(t, r); !zzContains(names, "alice-tb") || !zzContains(names, "bob-tb") {
				t.Fatalf("administrator does not see every bucket: %v", names)
			}
			r = g.tablesCall(u, "CreateNamespace", map[string]interface{}{
				"tableBucketARN": zzBucketARN("alice-tb"), "namespace": []string{"ops"}}, nil)
			zzExpectOK(t, r, "CreateNamespace by an administrator")
			r = g.tablesCall(u, "DeleteTableBucket", map[string]string{"tableBucketARN": zzBucketARN("bob-tb")}, nil)
			zzExpectOK(t, r, "DeleteTableBucket by an administrator")
			if g.filer.isTableBucket("bob-tb") {
				t.Fatalf("bob-tb still exists")
			}
		})
	}
}

func TestFuncZZAdminsBypassBucketPolicy(t *testing.T) {
	g := zzFuncSeed(t)
	g.filer.seedTableBucket("alice-locked", "acct-alice", zzDenyAllPolicy)
	r := g.tablesCall(zzRoot, "GetTableBucket", map[string]string{"tableBucketARN": zzBucketARN("alice-locked")}, nil)
	zzExpectOK(t, r, "GetTableBucket by an administrator on a deny-all bucket")
	r = g.tablesCall(zzAlice, "GetTableBucket", map[string]string{"tableBucketARN": zzBucketARN("alice-locked")}, nil)
	zzExpectOK(t, r, "GetTableBucket by the owner on a deny-all bucket")
}

func TestFuncZZExplicitTablePermissionGrantsAccess(t *testing.T) {
	g := zzFuncSeed(t)
	r := g.tablesCall(zzFrank, "GetTableBucket", map[string]string{"tableBucketARN": zzBucketARN("alice-tb")}, nil)
	zzExpectOK(t, r, "GetTableBucket by a user granted s3tables:GetTableBucket")
	r = g.tablesCall(zzFrank, "ListTableBuckets", map[string]interface{}{}, nil)
	zzExpectOK(t, r, "ListTableBuckets by a user granted table read permissions")
	if !zzContains(zzListedBuckets(t, r), "alice-tb") {
		t.Fatalf("user granted s3tables:GetTableBucket does not see alice-tb")
	}
}

func TestFuncZZBucketPolicyGrantsAccess(t *testing.T) {
	g := zzFuncSeed(t)
	g.filer.seedTableBucket("alice-shared", "acct-alice",
		`{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":"acct-bob","Action":["s3tables:GetTableBucket","s3tables:CreateNamespace"],"Resource":"*"}]}`)
	r := g.tablesCall(zzBob, "GetTableBucket", map[string]string{"tableBucketARN": zzBucketARN("alice-shared")}, nil)
	zzExpectOK(t, r, "GetTableBucket granted by the bucket policy")
	r = g.tablesCall(zzBob, "CreateNamespace", map[string]interface{}{
		"tableBucketARN": zzBucketARN("alice-shared"), "namespace": []string{"shared"}}, nil)
	zzExpectOK(t, r, "CreateNamespace granted by the bucket policy")
	if !g.filer.hasNamespace("alice-shared", "shared") {
		t.Fatalf("namespace not created")
	}
}

func TestFuncZZAnonymousKeepsOpenDefault(t *testing.T) {
	g := zzFuncSeed(t)
	r := g.tablesCall(zzAnon, "GetTableBucket", map[string]string{"tableBucketARN": zzBucketARN("alice-tb")}, nil)
	zzExpectOK(t, r, "GetTableBucket without credentials (anonymous identity configured)")
	r = g.tablesCall(zzAnon, "ListTableBuckets", map[string]interface{}{}, nil)
	zzExpectOK(t, r, "ListTableBuckets without credentials")
	if !zzContains(zzListedBuckets(t, r), "alice-tb") {
		t.Fatalf("anonymous listing no longer shows alice-tb")
	}
	g.filer.seedTableBucket("alice-locked", "acct-alice", zzDenyAllPolicy)
	r = g.tablesCall(zzAnon, "GetTableBucket", map[string]string{"tableBucketARN": zzBucketARN("alice-locked")}, nil)
	if zzIs2xx(r.status) {
		t.Fatalf("bucket policy deny no longer applies to anonymous requests")
	}
}

func TestFuncZZNoIdentitiesServerIsOpen(t *testing.T) {
	g := zzNewGateway(t, nil, false, nil)
	r := g.tablesCall(zzAnon, "CreateTableBucket", map[string]string{"name": "open-tb"}, nil)
	zzExpectOK(t, r, "CreateTableBucket on a server with no identities")
	r = g.tablesCall(zzAnon, "ListTableBuckets", map[string]interface{}{}, nil)
	zzExpectOK(t, r, "ListTableBuckets on a server with no identities")
	if !zzContains(zzListedBuckets(t, r), "open-tb") {
		t.Fatalf("open-tb not listed")
	}
	r = g.tablesCall(zzAnon, "CreateNamespace", map[string]interface{}{
		"tableBucketARN": zzBucketARN("open-tb"), "namespace": []string{"raw"}}, nil)
	zzExpectOK(t, r, "CreateNamespace on a server with no identities")
	g.filer.seedTableBucket("legacy-tb", "acct-alice", "")
	r = g.tablesCall(zzAnon, "GetTableBucket", map[string]string{"tableBucketARN": zzBucketARN("legacy-tb")}, nil)
	zzExpectOK(t, r, "GetTableBucket of a bucket with no policy on a server with no identities")
	r = g.tablesCall(zzAnon, "DeleteTableBucket", map[string]string{"tableBucketARN": zzBucketARN("legacy-tb")}, nil)
	zzExpectOK(t, r, "DeleteTableBucket of a bucket with no policy on a server with no identities")
}

func TestFuncZZNoIdentitiesServerHonoursDeny(t *testing.T) {
	g := zzNewGateway(t, nil, false, nil)
	g.filer.seedTableBucket("alice-locked", "acct-alice", zzDenyAllPolicy)
	r := g.tablesCall(zzAnon, "DeleteTableBucket", map[string]string{"tableBucketARN": zzBucketARN("alice-locked")}, nil)
	if zzIs2xx(r.status) || !g.filer.isTableBucket("alice-locked") {
		t.Fatalf("deny policy not honoured without credentials: %d", r.status)
	}
}

// ---- Iceberg REST catalog

func TestFuncZZCatalogOwnerWorks(t *testing.T) {
	g := zzFuncSeed(t)
	r := g.iceCall(zzAlice, http.MethodGet, "/v1/alice-tb/namespaces", nil, nil)
	zzExpectOK(t, r, "catalog ListNamespaces by the owner")
	if !zzHas(r.body, "sales") {
		t.Fatalf("owner's namespace missing: %s", string(r.body))
	}
	r = g.iceCall(zzAlice, http.MethodPost, "/v1/alice-tb/namespaces", map[string]interface{}{"namespace": []string{"finance"}}, nil)
	zzExpectOK(t, r, "catalog CreateNamespace by the owner")
	if !g.filer.hasNamespace("alice-tb", "finance") {
		t.Fatalf("namespace not created")
	}
	r = g.iceCall(zzAlice, http.MethodGet, "/v1/alice-tb/namespaces/finance", nil, nil)
	zzExpectOK(t, r, "catalog GetNamespace by the owner")
}

func TestFuncZZCatalogAdminWorks(t *testing.T) {
	g := zzFuncSeed(t)
	r := g.iceCall(zzRoot, http.MethodGet, "/v1/alice-tb/namespaces", nil, nil)
	zzExpectOK(t, r, "catalog ListNamespaces by an administrator")
	r = g.iceCall(zzRoot, http.MethodPost, "/v1/bob-tb/namespaces", map[string]interface{}{"namespace": []string{"audit"}}, nil)
	zzExpectOK(t, r, "catalog CreateNamespace by an administrator")
}

func TestFuncZZCatalogExplicitPermission(t *testing.T) {
	g := zzFuncSeed(t)
	r := g.iceCall(zzFrank, http.MethodGet, "/v1/alice-tb/namespaces", nil, nil)
	zzExpectOK(t, r, "catalog ListNamespaces by a user granted s3tables:ListNamespaces")
}

func TestFuncZZCatalogNoIdentitiesServerIsOpen(t *testing.T) {
	g := zzNewGateway(t, nil, false, nil)
	g.filer.seedTableBucket("warehouse", "000000000000", "")
	r := g.iceCall(zzAnon, http.MethodPost, "/v1/warehouse/namespaces", map[string]interface{}{"namespace": []string{"raw"}}, nil)
	zzExpectOK(t, r, "catalog CreateNamespace on a server with no identities")
	r = g.iceCall(zzAnon, http.MethodGet, "/v1/namespaces", nil, nil)
	zzExpectOK(t, r, "catalog ListNamespaces (default warehouse) on a server with no identities")
	if !zzHas(r.body, "raw") {
		t.Fatalf("namespace missing: %s", string(r.body))
	}
}

func TestFuncZZCatalogEmbeddedAuthenticatorOwner(t *testing.T) {
	auth := &zzTokenAuth{names: map[string]string{"tok-nina": "nina"}, defaultAllow: false}
	g := zzNewGateway(t, nil, false, auth)
	g.filer.seedTableBucket("nina-tb", "nina", "")
	g.filer.seedNamespace("nina-tb", "lake", "nina")
	hdr := map[string]string{"X-Zz-Token": "tok-nina"}
	r := g.iceCall(zzAnon, http.MethodGet, "/v1/nina-tb/namespaces", nil, hdr)
	zzExpectOK(t, r, "catalog ListNamespaces by the owner (embedded authenticator)")
	if !zzHas(r.body, "lake") {
		t.Fatalf("owner's namespace missing: %s", string(r.body))
	}
	r = g.iceCall(zzAnon, http.MethodPost, "/v1/nina-tb/namespaces", map[string]interface{}{"namespace": []string{"pond"}}, hdr)
	zzExpectOK(t, r, "catalog CreateNamespace by the owner (embedded authenticator)")
	r = g.iceCall(zzAnon, http.MethodGet, "/v1/nina-tb/namespaces", nil, nil)
	if zzIs2xx(r.status) {
		t.Fatalf("secured embedded catalog served a request without credentials")
	}
}

func TestFuncZZCatalogEmbeddedAuthenticatorOpenDefault(t *testing.T) {
	auth := &zzTokenAuth{names: map[string]string{}, defaultAllow: true}
	g := zzNewGateway(t, nil, false, auth)
	g.filer.seedTableBucket("nina-tb", "nina", "")
	g.filer.seedNamespace("nina-tb", "lake", "nina")
	r := g.iceCall(zzAnon, http.MethodGet, "/v1/nina-tb/namespaces", nil, nil)
	zzExpectOK(t, r, "catalog ListNamespaces without credentials (open-by-default authenticator)")
	if !zzHas(r.body, "lake") {
		t.Fatalf("namespace missing: %s", string(r.body))
	}
}
