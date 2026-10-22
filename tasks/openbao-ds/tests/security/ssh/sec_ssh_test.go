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

const secSSHPublicKey = `ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDArgK0ilRRfk8E7HIsjz5l3BuxmwpDd8DHRCVfOhbZ4gOSVxjEOOqBwWGjygdboBIZwFXmwDlU6sWX0hBJAgpQz0Cjvbjxtq/NjkvATrYPgnrXUhTaEn2eQO0PsqRNSFH46SK/oJfTp0q8/WgojxWJ2L7FUV8PO8uIk49DzqAqPV7WXU63vFsjx+3WQOX/ILeQvHCvaqs3dWjjzEoDudRWCOdUqcHEOshV9azIzPrXlQVzRV3QAKl6u7pC+/Secorpwt6IHpMKoVPGiR0tMMuNOVH8zrAKzIxPGfy2WmNDpJopbXMTvSOGAqNcp49O4SKOQl9Fzfq2HEevJamKLrMB dummy@example.com
`

func secSSHBackend(t *testing.T, meta map[string]string) (*backend, logical.Storage) {
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

func secSSHReq(t *testing.T, b *backend, s logical.Storage, path, entityID string, data map[string]interface{}) (*logical.Response, error) {
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

func secSSHSigned(resp *logical.Response, err error) bool {
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

// A substituted list separator widens the allowed-user match.
func TestSec_SSHUserCommaInjection(t *testing.T) {
	b, s := secSSHBackend(t, map[string]string{"u": "alice,root"})

	if _, err := secSSHReq(t, b, s, "roles/r", "", map[string]interface{}{
		"key_type":                "ca",
		"allow_user_certificates": true,
		"allowed_users":           "{{identity.entity.metadata.u}}",
		"allowed_users_template":  true,
		"default_user":            "alice",
		"allow_empty_principals":  false,
	}); err != nil {
		t.Fatalf("role write: %v", err)
	}

	resp, err := secSSHReq(t, b, s, "sign/r", "entity-1", map[string]interface{}{
		"public_key":       secSSHPublicKey,
		"valid_principals": "root",
	})
	if secSSHSigned(resp, err) {
		t.Fatalf("certificate signed for a principal the written allow-list never named")
	}
}

// A substituted list separator widens the allowed-domain match.
func TestSec_SSHDomainCommaInjection(t *testing.T) {
	b, s := secSSHBackend(t, map[string]string{"d": "alice,evil.com"})

	if _, err := secSSHReq(t, b, s, "roles/r", "", map[string]interface{}{
		"key_type":                 "ca",
		"allow_host_certificates":  true,
		"allowed_domains":          "{{identity.entity.metadata.d}}",
		"allowed_domains_template": true,
		"allow_bare_domains":       true,
	}); err != nil {
		t.Fatalf("role write: %v", err)
	}

	resp, err := secSSHReq(t, b, s, "sign/r", "entity-1", map[string]interface{}{
		"public_key":       secSSHPublicKey,
		"valid_principals": "evil.com",
		"cert_type":        "host",
	})
	if secSSHSigned(resp, err) {
		t.Fatalf("certificate signed for a host the written allow-list never named")
	}
}

// A substituted value containing a glob star widens the host-domain match.
func TestSec_SSHHostGlobInjection(t *testing.T) {
	b, s := secSSHBackend(t, map[string]string{"d": "*.example.com"})

	if _, err := secSSHReq(t, b, s, "roles/r", "", map[string]interface{}{
		"key_type":                 "ca",
		"allow_host_certificates":  true,
		"allow_glob_domains":       true,
		"allow_bare_domains":       true,
		"allowed_domains":          "{{identity.entity.metadata.d}}",
		"allowed_domains_template": true,
	}); err != nil {
		t.Fatalf("role write: %v", err)
	}

	resp, err := secSSHReq(t, b, s, "sign/r", "entity-1", map[string]interface{}{
		"public_key":       secSSHPublicKey,
		"valid_principals": "evil.example.com",
		"cert_type":        "host",
	})
	if secSSHSigned(resp, err) {
		t.Fatalf("certificate signed for a host the written allow-list never named")
	}
}

// secSSHSetIdentity replaces the caller's identity: its entity name, one alias
// on an auth mount, and the groups it belongs to.
func secSSHSetIdentity(t *testing.T, b *backend, entityName string, alias *logical.Alias, groups []*logical.Group) {
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

// A substituted alias name carrying a list separator widens the allowed-user match.
func TestSec_SSHAliasNameCommaInjection(t *testing.T) {
	b, s := secSSHBackend(t, nil)
	secSSHSetIdentity(t, b, "alice", &logical.Alias{
		MountAccessor: "auth_userpass_1", MountType: "userpass", Name: "alice,root",
	}, nil)

	if _, err := secSSHReq(t, b, s, "roles/r", "", map[string]interface{}{
		"key_type":                "ca",
		"allow_user_certificates": true,
		"allowed_users":           "{{identity.entity.aliases.auth_userpass_1.name}}",
		"allowed_users_template":  true,
		"default_user":            "alice",
		"allow_empty_principals":  false,
	}); err != nil {
		t.Fatalf("role write: %v", err)
	}

	resp, err := secSSHReq(t, b, s, "sign/r", "entity-1", map[string]interface{}{
		"public_key":       secSSHPublicKey,
		"valid_principals": "root",
	})
	if secSSHSigned(resp, err) {
		t.Fatalf("certificate signed for a principal the written allow-list never named")
	}
}

// A substituted group metadata value carrying a list separator widens the allowed-domain match.
func TestSec_SSHGroupMetadataCommaInjection(t *testing.T) {
	b, s := secSSHBackend(t, nil)
	secSSHSetIdentity(t, b, "alice", nil, []*logical.Group{
		{ID: "group-1", Name: "eng", Metadata: map[string]string{"d": "alice,evil.com"}},
	})

	if _, err := secSSHReq(t, b, s, "roles/r", "", map[string]interface{}{
		"key_type":                 "ca",
		"allow_host_certificates":  true,
		"allowed_domains":          "{{identity.groups.ids.group-1.metadata.d}}",
		"allowed_domains_template": true,
		"allow_bare_domains":       true,
	}); err != nil {
		t.Fatalf("role write: %v", err)
	}

	resp, err := secSSHReq(t, b, s, "sign/r", "entity-1", map[string]interface{}{
		"public_key":       secSSHPublicKey,
		"valid_principals": "evil.com",
		"cert_type":        "host",
	})
	if secSSHSigned(resp, err) {
		t.Fatalf("certificate signed for a host the written allow-list never named")
	}
}

// A substituted entity name containing a glob star widens the host-domain match.
func TestSec_SSHEntityNameHostGlob(t *testing.T) {
	b, s := secSSHBackend(t, nil)
	secSSHSetIdentity(t, b, "*.example.com", nil, nil)

	if _, err := secSSHReq(t, b, s, "roles/r", "", map[string]interface{}{
		"key_type":                 "ca",
		"allow_host_certificates":  true,
		"allow_glob_domains":       true,
		"allow_bare_domains":       true,
		"allowed_domains":          "{{identity.entity.name}}",
		"allowed_domains_template": true,
	}); err != nil {
		t.Fatalf("role write: %v", err)
	}

	resp, err := secSSHReq(t, b, s, "sign/r", "entity-1", map[string]interface{}{
		"public_key":       secSSHPublicKey,
		"valid_principals": "evil.example.com",
		"cert_type":        "host",
	})
	if secSSHSigned(resp, err) {
		t.Fatalf("certificate signed for a host the written allow-list never named")
	}
}
