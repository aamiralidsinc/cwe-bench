package ssh

import (
	"context"
	"testing"
	"time"

	"github.com/openbao/openbao/sdk/v2/logical"
)

// Hidden behavioural tests. Each drives the real sign entry point with a
// request that carries an entity id, so identity placeholders resolve exactly
// as they do for an authenticated HTTP caller.

const funcSSHPublicKey = `ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDArgK0ilRRfk8E7HIsjz5l3BuxmwpDd8DHRCVfOhbZ4gOSVxjEOOqBwWGjygdboBIZwFXmwDlU6sWX0hBJAgpQz0Cjvbjxtq/NjkvATrYPgnrXUhTaEn2eQO0PsqRNSFH46SK/oJfTp0q8/WgojxWJ2L7FUV8PO8uIk49DzqAqPV7WXU63vFsjx+3WQOX/ILeQvHCvaqs3dWjjzEoDudRWCOdUqcHEOshV9azIzPrXlQVzRV3QAKl6u7pC+/Secorpwt6IHpMKoVPGiR0tMMuNOVH8zrAKzIxPGfy2WmNDpJopbXMTvSOGAqNcp49O4SKOQl9Fzfq2HEevJamKLrMB dummy@example.com
`

func funcSSHBackend(t *testing.T, meta map[string]string) (*backend, logical.Storage) {
	t.Helper()
	config := logical.TestBackendConfig()
	config.StorageView = &logical.InmemStorage{}
	sys, ok := config.System.(*logical.StaticSystemView)
	if !ok {
		t.Fatalf("expected a static system view, got %T", config.System)
	}
	sys.EntityVal = &logical.Entity{ID: "entity-1", Name: "alice", Metadata: meta}
	sys.DefaultLeaseTTLVal = 2 * time.Minute
	sys.MaxLeaseTTLVal = 10 * time.Minute

	b, err := Factory(context.Background(), config)
	if err != nil {
		t.Fatal(err)
	}
	if err := b.Setup(context.Background(), config); err != nil {
		t.Fatal(err)
	}
	if _, err := b.HandleRequest(context.Background(), &logical.Request{
		Operation: logical.UpdateOperation, Path: "config/ca",
		Storage: config.StorageView, MountPoint: "ssh/",
		Data: map[string]interface{}{"generate_signing_key": true},
	}); err != nil {
		t.Fatalf("config/ca: %v", err)
	}
	return b.(*backend), config.StorageView
}

func funcSSHReq(t *testing.T, b *backend, s logical.Storage, path, entityID string, data map[string]interface{}) (*logical.Response, error) {
	t.Helper()
	return b.HandleRequest(context.Background(), &logical.Request{
		Operation:  logical.UpdateOperation,
		Path:       path,
		Storage:    s,
		MountPoint: "ssh/",
		EntityID:   entityID,
		Data:       data,
	})
}

func funcSSHSigned(resp *logical.Response, err error) bool {
	if err != nil || resp == nil || resp.IsError() {
		return false
	}
	v, ok := resp.Data["signed_key"]
	if !ok {
		return false
	}
	s, ok := v.(string)
	return ok && s != ""
}

// A clean templated allow-list still signs the principal it names.
func TestFunc_SSHUserTemplateLegit(t *testing.T) {
	b, s := funcSSHBackend(t, map[string]string{"u": "alice"})

	if _, err := funcSSHReq(t, b, s, "roles/r", "", map[string]interface{}{
		"key_type":                "ca",
		"allow_user_certificates": true,
		"allowed_users":           "{{identity.entity.metadata.u}}",
		"allowed_users_template":  true,
		"default_user":            "alice",
		"allow_empty_principals":  false,
	}); err != nil {
		t.Fatalf("role write: %v", err)
	}

	resp, err := funcSSHReq(t, b, s, "sign/r", "entity-1", map[string]interface{}{
		"public_key":       funcSSHPublicKey,
		"valid_principals": "alice",
	})
	if !funcSSHSigned(resp, err) {
		t.Fatalf("expected a certificate for the principal the allow-list grants")
	}
}

// A default user filled from identity data keeps working, and its rendered
// value is still checked against the allowed-user list afterwards.
func TestFunc_SSHDefaultUserCommaPreserved(t *testing.T) {
	b, s := funcSSHBackend(t, map[string]string{"u": "alice,bob"})

	if _, err := funcSSHReq(t, b, s, "roles/r", "", map[string]interface{}{
		"key_type":                "ca",
		"allow_user_certificates": true,
		"allowed_users":           "alice,bob",
		"default_user":            "{{identity.entity.metadata.u}}",
		"default_user_template":   true,
		"allow_empty_principals":  false,
	}); err != nil {
		t.Fatalf("role write: %v", err)
	}

	resp, err := funcSSHReq(t, b, s, "sign/r", "entity-1", map[string]interface{}{
		"public_key": funcSSHPublicKey,
	})
	if !funcSSHSigned(resp, err) {
		t.Fatalf("expected a default user rendered from identity data to keep working")
	}
}

// A literal star in the allowed-user list still means "any".
func TestFunc_SSHStaticStarAllowsAny(t *testing.T) {
	b, s := funcSSHBackend(t, nil)

	if _, err := funcSSHReq(t, b, s, "roles/r", "", map[string]interface{}{
		"key_type":                "ca",
		"allow_user_certificates": true,
		"allowed_users":           "*",
		"default_user":            "alice",
		"allow_empty_principals":  false,
	}); err != nil {
		t.Fatalf("role write: %v", err)
	}

	resp, err := funcSSHReq(t, b, s, "sign/r", "entity-1", map[string]interface{}{
		"public_key":       funcSSHPublicKey,
		"valid_principals": "root",
	})
	if !funcSSHSigned(resp, err) {
		t.Fatalf("expected a literal star allow-list to keep allowing any principal")
	}
}

// An administrator's literal glob domain still matches host certificates.
func TestFunc_SSHHostStaticGlobDomains(t *testing.T) {
	b, s := funcSSHBackend(t, nil)

	if _, err := funcSSHReq(t, b, s, "roles/r", "", map[string]interface{}{
		"key_type":                "ca",
		"allow_host_certificates": true,
		"allow_glob_domains":      true,
		"allow_bare_domains":      true,
		"allowed_domains":         "*.example.com",
	}); err != nil {
		t.Fatalf("role write: %v", err)
	}

	resp, err := funcSSHReq(t, b, s, "sign/r", "entity-1", map[string]interface{}{
		"public_key":       funcSSHPublicKey,
		"valid_principals": "host.example.com",
		"cert_type":        "host",
	})
	if !funcSSHSigned(resp, err) {
		t.Fatalf("expected an administrator's literal glob domain to keep matching")
	}
}

// funcSSHSetIdentity replaces the caller's identity: its entity name, one alias
// on an auth mount, and the groups it belongs to.
func funcSSHSetIdentity(t *testing.T, b *backend, entityName string, alias *logical.Alias, groups []*logical.Group) {
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

// A clean allowed user taken from an alias name still signs that principal.
func TestFunc_SSHAliasNameLegit(t *testing.T) {
	b, s := funcSSHBackend(t, nil)
	funcSSHSetIdentity(t, b, "alice", &logical.Alias{
		MountAccessor: "auth_userpass_1", MountType: "userpass", Name: "alice",
	}, nil)

	if _, err := funcSSHReq(t, b, s, "roles/r", "", map[string]interface{}{
		"key_type":                "ca",
		"allow_user_certificates": true,
		"allowed_users":           "{{identity.entity.aliases.auth_userpass_1.name}}",
		"allowed_users_template":  true,
		"default_user":            "alice",
		"allow_empty_principals":  false,
	}); err != nil {
		t.Fatalf("role write: %v", err)
	}

	resp, err := funcSSHReq(t, b, s, "sign/r", "entity-1", map[string]interface{}{
		"public_key":       funcSSHPublicKey,
		"valid_principals": "alice",
	})
	if !funcSSHSigned(resp, err) {
		t.Fatalf("expected a certificate for the principal the allow-list grants")
	}
}

// A clean allowed host taken from group metadata still signs that host.
func TestFunc_SSHGroupMetadataDomainLegit(t *testing.T) {
	b, s := funcSSHBackend(t, nil)
	funcSSHSetIdentity(t, b, "alice", nil, []*logical.Group{
		{ID: "group-1", Name: "eng", Metadata: map[string]string{"d": "host.example.com"}},
	})

	if _, err := funcSSHReq(t, b, s, "roles/r", "", map[string]interface{}{
		"key_type":                 "ca",
		"allow_host_certificates":  true,
		"allowed_domains":          "{{identity.groups.ids.group-1.metadata.d}}",
		"allowed_domains_template": true,
		"allow_bare_domains":       true,
	}); err != nil {
		t.Fatalf("role write: %v", err)
	}

	resp, err := funcSSHReq(t, b, s, "sign/r", "entity-1", map[string]interface{}{
		"public_key":       funcSSHPublicKey,
		"valid_principals": "host.example.com",
		"cert_type":        "host",
	})
	if !funcSSHSigned(resp, err) {
		t.Fatalf("expected a certificate for the host the allow-list grants")
	}
}

// A clean allowed host taken from the entity name still signs that host, also
// on a role that enables domain globs.
func TestFunc_SSHEntityNameHostLegit(t *testing.T) {
	b, s := funcSSHBackend(t, nil)
	funcSSHSetIdentity(t, b, "web01.example.com", nil, nil)

	if _, err := funcSSHReq(t, b, s, "roles/r", "", map[string]interface{}{
		"key_type":                 "ca",
		"allow_host_certificates":  true,
		"allow_glob_domains":       true,
		"allow_bare_domains":       true,
		"allowed_domains":          "{{identity.entity.name}}",
		"allowed_domains_template": true,
	}); err != nil {
		t.Fatalf("role write: %v", err)
	}

	resp, err := funcSSHReq(t, b, s, "sign/r", "entity-1", map[string]interface{}{
		"public_key":       funcSSHPublicKey,
		"valid_principals": "web01.example.com",
		"cert_type":        "host",
	})
	if !funcSSHSigned(resp, err) {
		t.Fatalf("expected a certificate for the host the allow-list grants")
	}
}
