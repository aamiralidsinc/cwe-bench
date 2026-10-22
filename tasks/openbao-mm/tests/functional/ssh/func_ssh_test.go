package ssh

import (
	"context"
	"testing"
	"time"

	"github.com/openbao/openbao/sdk/v2/logical"
)

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

// A clean substituted value in the allowed-user list still signs.
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
		t.Fatalf("expected a certificate for the caller's own principal, got err=%v", err)
	}
}

// A default user filled from identity data is still used even when the
// substituted value contains a list separator; the result is re-checked.
func TestFunc_SSHDefaultUserCommaPreserved(t *testing.T) {
	b, s := funcSSHBackend(t, map[string]string{"u": "alice,alice"})

	if _, err := funcSSHReq(t, b, s, "roles/r", "", map[string]interface{}{
		"key_type":                "ca",
		"allow_user_certificates": true,
		"allowed_users":           "alice",
		"default_user":            "{{identity.entity.metadata.u}}",
		"default_user_template":   true,
		"allow_empty_principals":  false,
	}); err != nil {
		t.Fatalf("role write: %v", err)
	}

	resp, err := funcSSHReq(t, b, s, "sign/r", "entity-1", map[string]interface{}{
		"public_key":       funcSSHPublicKey,
		"valid_principals": "alice",
	})
	if !funcSSHSigned(resp, err) {
		t.Fatalf("expected a certificate when the default user still matches the allow-list, got err=%v", err)
	}
}

// A literal star written into the allowed-user list by an administrator still
// means "any user".
func TestFunc_SSHStaticStarAllowsAny(t *testing.T) {
	b, s := funcSSHBackend(t, map[string]string{"u": "unused"})

	if _, err := funcSSHReq(t, b, s, "roles/r", "", map[string]interface{}{
		"key_type":                "ca",
		"allow_user_certificates": true,
		"allowed_users":           "*",
		"allow_empty_principals":  false,
	}); err != nil {
		t.Fatalf("role write: %v", err)
	}

	resp, err := funcSSHReq(t, b, s, "sign/r", "entity-1", map[string]interface{}{
		"public_key":       funcSSHPublicKey,
		"valid_principals": "randomuser",
	})
	if !funcSSHSigned(resp, err) {
		t.Fatalf("expected a certificate under the administrator's literal star, got err=%v", err)
	}
}
