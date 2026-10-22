package s3api

// Hidden security tests: table storage authorization through the S3 Tables API
// and the Iceberg REST catalog of a SeaweedFS gateway.

import (
	"net/http"
	"testing"

	"github.com/seaweedfs/seaweedfs/weed/s3api/s3err"
)

// zzSecuredSeed: a gateway with identities configured, alice owning "alice-tb"
// (namespace "sales") and "alice-locked" (a bucket policy denying everyone).
func zzSecuredSeed(t *testing.T) *zzGateway {
	g := zzNewGateway(t, nil, true, nil)
	g.filer.seedTableBucket("alice-tb", "acct-alice", "")
	g.filer.seedNamespace("alice-tb", "sales", "acct-alice")
	g.filer.seedTableBucket("alice-locked", "acct-alice", zzDenyAllPolicy)
	g.filer.seedTableBucket("alice-empty", "acct-alice", "")
	return g
}

func zzExpectRefused(t *testing.T, r zzResp, what string) {
	t.Helper()
	if !zzIs4xx(r.status) {
		t.Fatalf("%s: expected a client error (4xx), got %d: %s", what, r.status, string(r.body))
	}
}

// ---- identities that belong to the administrative account without admin permissions

func TestSecZZAdminAccountMemberCannotReadOthersBucket(t *testing.T) {
	g := zzSecuredSeed(t)
	r := g.tablesCall(zzCarol, "GetTableBucket", map[string]string{"tableBucketARN": zzBucketARN("alice-tb")}, nil)
	zzExpectRefused(t, r, "GetTableBucket by a non-admin member of the admin account")
}

func TestSecZZAdminAccountMemberCannotDeleteOthersBucket(t *testing.T) {
	g := zzSecuredSeed(t)
	r := g.tablesCall(zzCarol, "DeleteTableBucket", map[string]string{"tableBucketARN": zzBucketARN("alice-empty")}, nil)
	zzExpectRefused(t, r, "DeleteTableBucket by a non-admin member of the admin account")
	if !g.filer.isTableBucket("alice-empty") {
		t.Fatalf("alice-empty was deleted")
	}
}

func TestSecZZAdminAccountMemberSubjectToBucketPolicy(t *testing.T) {
	g := zzSecuredSeed(t)
	r := g.tablesCall(zzCarol, "GetTableBucket", map[string]string{"tableBucketARN": zzBucketARN("alice-locked")}, nil)
	zzExpectRefused(t, r, "GetTableBucket on a deny-all bucket by a non-admin member of the admin account")
}

func TestSecZZUnknownAccountIdentityCannotDeleteOthersBucket(t *testing.T) {
	g := zzSecuredSeed(t)
	r := g.tablesCall(zzDave, "DeleteTableBucket", map[string]string{"tableBucketARN": zzBucketARN("alice-empty")}, nil)
	zzExpectRefused(t, r, "DeleteTableBucket by an identity whose configured account does not exist")
	if !g.filer.isTableBucket("alice-empty") {
		t.Fatalf("alice-empty was deleted")
	}
}

func TestSecZZUnknownAccountIdentityCannotListOthersBuckets(t *testing.T) {
	g := zzSecuredSeed(t)
	r := g.tablesCall(zzDave, "ListTableBuckets", map[string]interface{}{}, nil)
	if zzIs2xx(r.status) && zzContains(zzListedBuckets(t, r), "alice-tb") {
		t.Fatalf("ListTableBuckets showed alice-tb to an identity with no table permissions")
	}
	if !zzIs2xx(r.status) && !zzIs4xx(r.status) {
		t.Fatalf("ListTableBuckets failed with %d", r.status)
	}
}

// ---- an authenticated user of another account, with no table permissions

func TestSecZZOtherUserCannotGetBucket(t *testing.T) {
	g := zzSecuredSeed(t)
	r := g.tablesCall(zzBob, "GetTableBucket", map[string]string{"tableBucketARN": zzBucketARN("alice-tb")}, nil)
	zzExpectRefused(t, r, "GetTableBucket by another account's user")
}

func TestSecZZOtherUserListDoesNotShowBucket(t *testing.T) {
	g := zzSecuredSeed(t)
	r := g.tablesCall(zzBob, "ListTableBuckets", map[string]interface{}{}, nil)
	if zzIs2xx(r.status) && zzContains(zzListedBuckets(t, r), "alice-tb") {
		t.Fatalf("ListTableBuckets showed alice-tb to another account's user")
	}
	if !zzIs2xx(r.status) && !zzIs4xx(r.status) {
		t.Fatalf("ListTableBuckets failed with %d", r.status)
	}
}

func TestSecZZOtherUserCannotDeleteBucket(t *testing.T) {
	g := zzSecuredSeed(t)
	r := g.tablesCall(zzBob, "DeleteTableBucket", map[string]string{"tableBucketARN": zzBucketARN("alice-empty")}, nil)
	zzExpectRefused(t, r, "DeleteTableBucket by another account's user")
	if !g.filer.isTableBucket("alice-empty") {
		t.Fatalf("alice-empty was deleted")
	}
}

func TestSecZZOtherUserCannotCreateNamespace(t *testing.T) {
	g := zzSecuredSeed(t)
	r := g.tablesCall(zzBob, "CreateNamespace", map[string]interface{}{
		"tableBucketARN": zzBucketARN("alice-tb"), "namespace": []string{"intruder"}}, nil)
	zzExpectRefused(t, r, "CreateNamespace by another account's user")
	if g.filer.hasNamespace("alice-tb", "intruder") {
		t.Fatalf("namespace was created in alice-tb")
	}
}

func TestSecZZOtherUserCannotPutBucketPolicy(t *testing.T) {
	g := zzSecuredSeed(t)
	policy := `{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":"*","Action":"s3tables:*","Resource":"*"}]}`
	r := g.tablesCall(zzBob, "PutTableBucketPolicy", map[string]string{
		"tableBucketARN": zzBucketARN("alice-tb"), "resourcePolicy": policy}, nil)
	zzExpectRefused(t, r, "PutTableBucketPolicy by another account's user")
	if g.filer.bucketPolicy("alice-tb") != "" {
		t.Fatalf("bucket policy of alice-tb was changed")
	}
}

func TestSecZZOtherUserCannotCreateTable(t *testing.T) {
	g := zzSecuredSeed(t)
	r := g.tablesCall(zzBob, "CreateTable", map[string]interface{}{
		"tableBucketARN": zzBucketARN("alice-tb"), "namespace": []string{"sales"},
		"name": "intruder", "format": "ICEBERG"}, nil)
	zzExpectRefused(t, r, "CreateTable by another account's user")
	if g.filer.exists("/buckets/alice-tb/sales/intruder") {
		t.Fatalf("table was created in alice-tb")
	}
}

// zzSecuredSeedWithTable adds, through the API as the owner, a table "orders"
// in alice-tb/sales and a tag on alice-tb.
func zzSecuredSeedWithTable(t *testing.T) *zzGateway {
	g := zzSecuredSeed(t)
	r := g.tablesCall(zzAlice, "CreateTable", map[string]interface{}{
		"tableBucketARN": zzBucketARN("alice-tb"), "namespace": []string{"sales"},
		"name": "orders", "format": "ICEBERG"}, nil)
	if !zzIs2xx(r.status) || !g.filer.exists("/buckets/alice-tb/sales/orders") {
		t.Fatalf("setup: owner CreateTable failed: %d %s", r.status, string(r.body))
	}
	r = g.tablesCall(zzAlice, "TagResource", map[string]interface{}{
		"resourceArn": zzBucketARN("alice-tb"), "tags": map[string]string{"costcenter": "cc-4711"}}, nil)
	if !zzIs2xx(r.status) {
		t.Fatalf("setup: owner TagResource failed: %d %s", r.status, string(r.body))
	}
	return g
}

func zzBucketTags(g *zzGateway) string {
	v, _ := g.filer.extended("/buckets/alice-tb", "s3tables.tags")
	return string(v)
}

func TestSecZZOtherUserCannotGetTable(t *testing.T) {
	g := zzSecuredSeedWithTable(t)
	r := g.tablesCall(zzBob, "GetTable", map[string]interface{}{
		"tableBucketARN": zzBucketARN("alice-tb"), "namespace": []string{"sales"}, "name": "orders"}, nil)
	zzExpectRefused(t, r, "GetTable by another account's user")
}

func TestSecZZOtherUserCannotDeleteTable(t *testing.T) {
	g := zzSecuredSeedWithTable(t)
	r := g.tablesCall(zzBob, "DeleteTable", map[string]interface{}{
		"tableBucketARN": zzBucketARN("alice-tb"), "namespace": []string{"sales"}, "name": "orders"}, nil)
	zzExpectRefused(t, r, "DeleteTable by another account's user")
	if !g.filer.exists("/buckets/alice-tb/sales/orders") {
		t.Fatalf("table orders was deleted")
	}
}

func TestSecZZOtherUserCannotListBucketTags(t *testing.T) {
	g := zzSecuredSeedWithTable(t)
	r := g.tablesCall(zzBob, "ListTagsForResource", map[string]string{"resourceArn": zzBucketARN("alice-tb")}, nil)
	zzExpectRefused(t, r, "ListTagsForResource by another account's user")
	if zzHas(r.body, "cc-4711") {
		t.Fatalf("ListTagsForResource revealed alice-tb tags: %s", string(r.body))
	}
}

func TestSecZZOtherUserCannotTagBucket(t *testing.T) {
	g := zzSecuredSeedWithTable(t)
	before := zzBucketTags(g)
	r := g.tablesCall(zzBob, "TagResource", map[string]interface{}{
		"resourceArn": zzBucketARN("alice-tb"), "tags": map[string]string{"costcenter": "intruder"}}, nil)
	zzExpectRefused(t, r, "TagResource by another account's user")
	if after := zzBucketTags(g); after != before {
		t.Fatalf("tags of alice-tb changed: %s -> %s", before, after)
	}
}

// ---- the Iceberg REST catalog of the same gateway

func TestSecZZCatalogOtherUserCannotListNamespaces(t *testing.T) {
	g := zzSecuredSeed(t)
	r := g.iceCall(zzBob, http.MethodGet, "/v1/alice-tb/namespaces", nil, nil)
	if zzIs2xx(r.status) || zzHas(r.body, "sales") {
		t.Fatalf("catalog listed alice-tb namespaces to another account's user: %d %s", r.status, string(r.body))
	}
}

func TestSecZZCatalogOtherUserCannotCreateNamespace(t *testing.T) {
	g := zzSecuredSeed(t)
	r := g.iceCall(zzBob, http.MethodPost, "/v1/alice-tb/namespaces", map[string]interface{}{"namespace": []string{"intruder"}}, nil)
	if zzIs2xx(r.status) || g.filer.hasNamespace("alice-tb", "intruder") {
		t.Fatalf("catalog let another account's user create a namespace in alice-tb: %d %s", r.status, string(r.body))
	}
}

func TestSecZZCatalogAdminAccountMemberCannotCreateNamespace(t *testing.T) {
	g := zzSecuredSeed(t)
	r := g.iceCall(zzCarol, http.MethodPost, "/v1/alice-tb/namespaces", map[string]interface{}{"namespace": []string{"intruder"}}, nil)
	if zzIs2xx(r.status) || g.filer.hasNamespace("alice-tb", "intruder") {
		t.Fatalf("catalog let a non-admin member of the admin account create a namespace in alice-tb: %d %s", r.status, string(r.body))
	}
}

// zzTokenAuth is an embedding's own authenticator: a bearer-style token names
// the caller. It reports only the caller's name, or a full identity when one
// is configured for the token.
type zzTokenAuth struct {
	names        map[string]string
	identities   map[string]interface{}
	defaultAllow bool
}

func (a *zzTokenAuth) AuthenticateRequest(r *http.Request) (string, interface{}, s3err.ErrorCode) {
	tok := r.Header.Get("X-Zz-Token")
	name, ok := a.names[tok]
	if !ok {
		return "", nil, s3err.ErrAccessDenied
	}
	return name, a.identities[tok], s3err.ErrNone
}

func (a *zzTokenAuth) DefaultAllow() bool { return a.defaultAllow }

type zzIdpAccount struct{ Id string }

// zzIdpIdentity is the identity shape an identity-provider backed authenticator returns.
type zzIdpIdentity struct {
	Name    string
	Account *zzIdpAccount
	Actions []string
	Claims  map[string]interface{}
}

func TestSecZZCatalogNameOnlyCallerIsEnforced(t *testing.T) {
	auth := &zzTokenAuth{names: map[string]string{"tok-bob": "bob"}, defaultAllow: false}
	g := zzNewGateway(t, nil, false, auth)
	g.filer.seedTableBucket("alice-tb", "acct-alice", "")
	g.filer.seedNamespace("alice-tb", "sales", "acct-alice")
	hdr := map[string]string{"X-Zz-Token": "tok-bob"}

	r := g.iceCall(zzAnon, http.MethodGet, "/v1/alice-tb/namespaces", nil, hdr)
	if zzIs2xx(r.status) || zzHas(r.body, "sales") {
		t.Fatalf("catalog listed alice-tb namespaces to another user: %d %s", r.status, string(r.body))
	}
	r = g.iceCall(zzAnon, http.MethodPost, "/v1/alice-tb/namespaces", map[string]interface{}{"namespace": []string{"intruder"}}, hdr)
	if zzIs2xx(r.status) || g.filer.hasNamespace("alice-tb", "intruder") {
		t.Fatalf("catalog let another user create a namespace in alice-tb: %d %s", r.status, string(r.body))
	}
}

func TestSecZZCatalogProviderUsernameDoesNotMakeAdmin(t *testing.T) {
	auth := &zzTokenAuth{
		names: map[string]string{"tok-mallory": "mallory"},
		identities: map[string]interface{}{"tok-mallory": &zzIdpIdentity{
			Name: "mallory", Account: &zzIdpAccount{Id: "acct-mallory"}, Actions: []string{"Read"},
			Claims: map[string]interface{}{"preferred_username": "admin"},
		}},
	}
	g := zzNewGateway(t, nil, false, auth)
	g.filer.seedTableBucket("alice-locked", "acct-alice", zzDenyAllPolicy)
	g.filer.seedNamespace("alice-locked", "sales", "acct-alice")
	hdr := map[string]string{"X-Zz-Token": "tok-mallory"}

	r := g.iceCall(zzAnon, http.MethodPost, "/v1/alice-locked/namespaces", map[string]interface{}{"namespace": []string{"intruder"}}, hdr)
	if zzIs2xx(r.status) || g.filer.hasNamespace("alice-locked", "intruder") {
		t.Fatalf("an identity whose provider username is 'admin' acted as administrator: %d %s", r.status, string(r.body))
	}
}

func TestSecZZCatalogNameOnlyAdminIsEnforced(t *testing.T) {
	auth := &zzTokenAuth{names: map[string]string{"tok-admin": "admin"}, defaultAllow: false}
	g := zzNewGateway(t, nil, false, auth)
	g.filer.seedTableBucket("alice-locked", "acct-alice", zzDenyAllPolicy)
	g.filer.seedNamespace("alice-locked", "sales", "acct-alice")
	hdr := map[string]string{"X-Zz-Token": "tok-admin"}

	r := g.iceCall(zzAnon, http.MethodPost, "/v1/alice-locked/namespaces", map[string]interface{}{"namespace": []string{"intruder"}}, hdr)
	if zzIs2xx(r.status) || g.filer.hasNamespace("alice-locked", "intruder") {
		t.Fatalf("a caller reported only by the name 'admin' acted as administrator: %d %s", r.status, string(r.body))
	}
}

func TestSecZZCatalogProviderSubjectDoesNotMakeAdmin(t *testing.T) {
	auth := &zzTokenAuth{
		names: map[string]string{"tok-trent": "trent"},
		identities: map[string]interface{}{"tok-trent": &zzIdpIdentity{
			Name: "trent", Account: &zzIdpAccount{Id: "acct-trent"}, Actions: []string{"Read"},
			Claims: map[string]interface{}{"sub": "admin"},
		}},
	}
	g := zzNewGateway(t, nil, false, auth)
	g.filer.seedTableBucket("alice-locked", "acct-alice", zzDenyAllPolicy)
	g.filer.seedNamespace("alice-locked", "sales", "acct-alice")
	hdr := map[string]string{"X-Zz-Token": "tok-trent"}

	r := g.iceCall(zzAnon, http.MethodPost, "/v1/alice-locked/namespaces", map[string]interface{}{"namespace": []string{"intruder"}}, hdr)
	if zzIs2xx(r.status) || g.filer.hasNamespace("alice-locked", "intruder") {
		t.Fatalf("an identity whose provider subject is 'admin' acted as administrator: %d %s", r.status, string(r.body))
	}
}

// ---- requests without credentials on a server with no identities configured

func TestSecZZUnauthenticatedRequestCannotClaimAdmin(t *testing.T) {
	g := zzNewGateway(t, nil, false, nil)
	g.filer.seedTableBucket("alice-locked", "acct-alice", zzDenyAllPolicy)
	r := g.tablesCall(zzAnon, "DeleteTableBucket", map[string]string{"tableBucketARN": zzBucketARN("alice-locked")},
		map[string]string{"S3-Account-Id": "admin"})
	zzExpectRefused(t, r, "DeleteTableBucket on a deny-all bucket without credentials")
	if !g.filer.isTableBucket("alice-locked") {
		t.Fatalf("alice-locked was deleted")
	}
}

func TestSecZZUnauthenticatedRequestCannotClaimOwner(t *testing.T) {
	g := zzNewGateway(t, nil, false, nil)
	g.filer.seedTableBucket("alice-locked", "acct-alice", zzDenyAllPolicy)
	r := g.tablesCall(zzAnon, "DeleteTableBucket", map[string]string{"tableBucketARN": zzBucketARN("alice-locked")},
		map[string]string{"S3-Account-Id": "acct-alice"})
	zzExpectRefused(t, r, "DeleteTableBucket on a deny-all bucket without credentials")
	if !g.filer.isTableBucket("alice-locked") {
		t.Fatalf("alice-locked was deleted")
	}
}
