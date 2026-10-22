package pki

import (
	"context"
	"testing"

	"github.com/openbao/openbao/sdk/v2/logical"
)

// Hidden behavioural tests. Each drives the real issue entry point with a
// request that carries an entity id, so identity placeholders resolve exactly
// as they do for an authenticated HTTP caller.

func funcPKIHandle(t *testing.T, b *backend, s logical.Storage, path, entityID string, data map[string]interface{}) (*logical.Response, error) {
	t.Helper()
	return b.HandleRequest(context.Background(), &logical.Request{
		Operation:  logical.UpdateOperation,
		Path:       path,
		Storage:    s,
		MountPoint: "pki/",
		EntityID:   entityID,
		Data:       data,
	})
}

func funcPKIIssued(resp *logical.Response, err error) bool {
	if err != nil || resp == nil || resp.IsError() {
		return false
	}
	v, ok := resp.Data["certificate"]
	if !ok {
		return false
	}
	s, ok := v.(string)
	return ok && s != ""
}

func funcPKISetup(t *testing.T, meta map[string]string) (*backend, logical.Storage) {
	t.Helper()
	b, s := CreateBackendWithStorage(t)
	sys, ok := b.System().(*logical.StaticSystemView)
	if !ok {
		t.Fatalf("expected a static system view, got %T", b.System())
	}
	sys.EntityVal = &logical.Entity{ID: "entity-1", Name: "alice", Metadata: meta}
	if _, err := funcPKIHandle(t, b, s, "root/generate/internal", "", map[string]interface{}{
		"ttl": "40h", "common_name": "example.com",
	}); err != nil {
		t.Fatalf("root generate: %v", err)
	}
	return b, s
}

// A clean templated URI SAN still issues.
func TestFunc_PKIUriTemplateLegit(t *testing.T) {
	b, s := funcPKISetup(t, map[string]string{"sans": "spiffe://d/users/alice"})

	if _, err := funcPKIHandle(t, b, s, "roles/t", "", map[string]interface{}{
		"allowed_uri_sans":          []string{"{{identity.entity.metadata.sans}}"},
		"allowed_uri_sans_template": true,
		"require_cn":                false,
		"allow_any_name":            true,
	}); err != nil {
		t.Fatalf("role write: %v", err)
	}

	resp, err := funcPKIHandle(t, b, s, "issue/t", "entity-1", map[string]interface{}{
		"uri_sans": "spiffe://d/users/alice",
	})
	if !funcPKIIssued(resp, err) {
		t.Fatalf("expected a certificate for the name the allow-list grants")
	}
}

// An administrator's literal glob domain still matches.
func TestFunc_PKIStaticGlobDomains(t *testing.T) {
	b, s := funcPKISetup(t, nil)

	if _, err := funcPKIHandle(t, b, s, "roles/t", "", map[string]interface{}{
		"allowed_domains":          []string{"*.example.com"},
		"allowed_domains_template": false,
		"allow_glob_domains":       true,
		"allow_bare_domains":       true,
	}); err != nil {
		t.Fatalf("role write: %v", err)
	}

	resp, err := funcPKIHandle(t, b, s, "issue/t", "entity-1", map[string]interface{}{
		"common_name": "host.example.com",
	})
	if !funcPKIIssued(resp, err) {
		t.Fatalf("expected an administrator's literal glob domain to keep matching")
	}
}

// An administrator's literal glob in the user-id allow-list still matches.
func TestFunc_PKIStaticUserIdGlob(t *testing.T) {
	b, s := funcPKISetup(t, nil)

	if _, err := funcPKIHandle(t, b, s, "roles/t", "", map[string]interface{}{
		"allowed_user_ids":          []string{"dev*"},
		"allowed_user_ids_template": false,
		"require_cn":                false,
		"allow_any_name":            true,
	}); err != nil {
		t.Fatalf("role write: %v", err)
	}

	resp, err := funcPKIHandle(t, b, s, "issue/t", "entity-1", map[string]interface{}{
		"common_name": "foobar",
		"user_ids":    "dev1234",
	})
	if !funcPKIIssued(resp, err) {
		t.Fatalf("expected an administrator's literal glob user id to keep matching")
	}
}

// A clean templated user id still issues.
func TestFunc_PKIUserIdTemplateLegit(t *testing.T) {
	b, s := funcPKISetup(t, map[string]string{"uid": "alice"})

	if _, err := funcPKIHandle(t, b, s, "roles/t", "", map[string]interface{}{
		"allowed_user_ids":          []string{"{{identity.entity.metadata.uid}}"},
		"allowed_user_ids_template": true,
		"require_cn":                false,
		"allow_any_name":            true,
	}); err != nil {
		t.Fatalf("role write: %v", err)
	}

	resp, err := funcPKIHandle(t, b, s, "issue/t", "entity-1", map[string]interface{}{
		"common_name": "foobar",
		"user_ids":    "alice",
	})
	if !funcPKIIssued(resp, err) {
		t.Fatalf("expected a certificate for the user id the allow-list grants")
	}
}

// funcPKISetIdentity replaces the caller's identity: its entity name, one alias
// on an auth mount, and the groups it belongs to.
func funcPKISetIdentity(t *testing.T, b *backend, entityName string, alias *logical.Alias, groups []*logical.Group) {
	t.Helper()
	sys, ok := b.System().(*logical.StaticSystemView)
	if !ok {
		t.Fatalf("expected a static system view, got %T", b.System())
	}
	ent := &logical.Entity{ID: "entity-1", Name: entityName, Metadata: map[string]string{}}
	if alias != nil {
		ent.Aliases = []*logical.Alias{alias}
	}
	sys.EntityVal = ent
	sys.GroupsVal = groups
}

// A clean templated URI SAN taken from alias metadata still issues.
func TestFunc_PKIAliasMetadataUriLegit(t *testing.T) {
	b, s := funcPKISetup(t, nil)
	funcPKISetIdentity(t, b, "alice", &logical.Alias{
		MountAccessor: "auth_userpass_1", MountType: "userpass", Name: "alice",
		Metadata: map[string]string{"sans": "spiffe://d/users/alice"},
	}, nil)

	if _, err := funcPKIHandle(t, b, s, "roles/t", "", map[string]interface{}{
		"allowed_uri_sans":          []string{"{{identity.entity.aliases.auth_userpass_1.metadata.sans}}"},
		"allowed_uri_sans_template": true,
		"require_cn":                false,
		"allow_any_name":            true,
	}); err != nil {
		t.Fatalf("role write: %v", err)
	}

	resp, err := funcPKIHandle(t, b, s, "issue/t", "entity-1", map[string]interface{}{
		"uri_sans": "spiffe://d/users/alice",
	})
	if !funcPKIIssued(resp, err) {
		t.Fatalf("expected a certificate for the URI the allow-list grants")
	}
}

// A clean templated domain taken from a group name still issues, also on a
// role that enables domain globs.
func TestFunc_PKIGroupNameDomainLegit(t *testing.T) {
	b, s := funcPKISetup(t, nil)
	funcPKISetIdentity(t, b, "alice", nil, []*logical.Group{
		{ID: "group-1", Name: "eng.example.com", Metadata: map[string]string{}},
	})

	if _, err := funcPKIHandle(t, b, s, "roles/t", "", map[string]interface{}{
		"allowed_domains":          []string{"{{identity.groups.ids.group-1.name}}"},
		"allowed_domains_template": true,
		"allow_glob_domains":       true,
		"allow_bare_domains":       true,
	}); err != nil {
		t.Fatalf("role write: %v", err)
	}

	resp, err := funcPKIHandle(t, b, s, "issue/t", "entity-1", map[string]interface{}{
		"common_name": "eng.example.com",
	})
	if !funcPKIIssued(resp, err) {
		t.Fatalf("expected a certificate for the name the allow-list grants")
	}
}

// A clean templated user id taken from the entity name still issues.
func TestFunc_PKIEntityNameUserIdLegit(t *testing.T) {
	b, s := funcPKISetup(t, nil)
	funcPKISetIdentity(t, b, "alice", nil, nil)

	if _, err := funcPKIHandle(t, b, s, "roles/t", "", map[string]interface{}{
		"allowed_user_ids":          []string{"{{identity.entity.name}}"},
		"allowed_user_ids_template": true,
		"require_cn":                false,
		"allow_any_name":            true,
	}); err != nil {
		t.Fatalf("role write: %v", err)
	}

	resp, err := funcPKIHandle(t, b, s, "issue/t", "entity-1", map[string]interface{}{
		"common_name": "foobar",
		"user_ids":    "alice",
	})
	if !funcPKIIssued(resp, err) {
		t.Fatalf("expected a certificate for the user id the allow-list grants")
	}
}
