package pki

import (
	"context"
	"testing"

	"github.com/openbao/openbao/sdk/v2/logical"
)

// Hidden behavioural tests. Each drives the real issue entry point with a
// request that carries an entity id, so identity placeholders resolve exactly
// as they do for an authenticated HTTP caller.

func secPKIHandle(t *testing.T, b *backend, s logical.Storage, path, entityID string, data map[string]interface{}) (*logical.Response, error) {
	t.Helper()
	resp, err := b.HandleRequest(context.Background(), &logical.Request{
		Operation:  logical.UpdateOperation,
		Path:       path,
		Storage:    s,
		MountPoint: "pki/",
		EntityID:   entityID,
		Data:       data,
	})
	return resp, err
}

func secPKISucceeded(resp *logical.Response, err error, sideEffectKey string) bool {
	if err != nil {
		return false
	}
	if resp == nil {
		return false
	}
	if resp.IsError() {
		return false
	}
	if sideEffectKey != "" {
		if v, ok := resp.Data[sideEffectKey]; ok {
			if s, ok := v.(string); ok && s != "" {
				return true
			}
		}
		return false
	}
	return true
}

func secPKISetup(t *testing.T, meta map[string]string) (*backend, logical.Storage) {
	t.Helper()
	b, s := CreateBackendWithStorage(t)
	sys, ok := b.System().(*logical.StaticSystemView)
	if !ok {
		t.Fatalf("expected a static system view, got %T", b.System())
	}
	sys.EntityVal = &logical.Entity{ID: "entity-1", Name: "alice", Metadata: meta}
	if _, err := secPKIHandle(t, b, s, "root/generate/internal", "", map[string]interface{}{
		"ttl": "40h", "common_name": "example.com",
	}); err != nil {
		t.Fatalf("root generate: %v", err)
	}
	return b, s
}

// A substituted value containing a glob star widens the allowed-URI match.
func TestSec_PKIUriGlobInjection(t *testing.T) {
	b, s := secPKISetup(t, map[string]string{"sans": "spiffe://d/users/*"})

	if _, err := secPKIHandle(t, b, s, "roles/t", "", map[string]interface{}{
		"allowed_uri_sans":          []string{"{{identity.entity.metadata.sans}}"},
		"allowed_uri_sans_template": true,
		"require_cn":                false,
		"allow_any_name":            true,
	}); err != nil {
		t.Fatalf("role write: %v", err)
	}

	resp, err := secPKIHandle(t, b, s, "issue/t", "entity-1", map[string]interface{}{
		"uri_sans": "spiffe://d/users/attacker",
	})
	if secPKISucceeded(resp, err, "certificate") {
		t.Fatalf("certificate issued for a URI the written allow-list never named")
	}
}

// A substituted value containing a glob star widens the allowed-domain match.
func TestSec_PKIDomainGlobInjection(t *testing.T) {
	b, s := secPKISetup(t, map[string]string{"dom": "*.example.com"})

	if _, err := secPKIHandle(t, b, s, "roles/t", "", map[string]interface{}{
		"allowed_domains":          []string{"{{identity.entity.metadata.dom}}"},
		"allowed_domains_template": true,
		"allow_glob_domains":       true,
		"allow_bare_domains":       true,
	}); err != nil {
		t.Fatalf("role write: %v", err)
	}

	resp, err := secPKIHandle(t, b, s, "issue/t", "entity-1", map[string]interface{}{
		"common_name": "evil.example.com",
	})
	if secPKISucceeded(resp, err, "certificate") {
		t.Fatalf("certificate issued for a name the written allow-list never named")
	}
}

// A substituted value containing a glob star widens a serial-number allow-list.
func TestSec_PKISerialGlobInjection(t *testing.T) {
	b, s := secPKISetup(t, map[string]string{"ser": "f00*"})

	if _, err := secPKIHandle(t, b, s, "roles/t", "", map[string]interface{}{
		"allowed_serial_numbers":          []string{"{{identity.entity.metadata.ser}}"},
		"allowed_serial_numbers_template": true,
		"allow_any_name":                  true,
		"require_cn":                      false,
	}); err != nil {
		t.Fatalf("role write: %v", err)
	}

	resp, err := secPKIHandle(t, b, s, "issue/t", "entity-1", map[string]interface{}{
		"common_name":   "foobar",
		"serial_number": "f00deadbeef",
	})
	if secPKISucceeded(resp, err, "certificate") {
		t.Fatalf("certificate issued for a serial the written allow-list never named")
	}
}
