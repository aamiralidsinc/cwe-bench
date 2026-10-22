package pki

import (
	"context"
	"testing"

	"github.com/openbao/openbao/sdk/v2/logical"
)

func funcPKIHandle(t *testing.T, b *backend, s logical.Storage, path, entityID string, data map[string]interface{}) (*logical.Response, error) {
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

// A clean substituted value in a URI allow-list still issues.
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
		t.Fatalf("expected a certificate for the caller's own URI, got err=%v respErr=%v", err, respErr(resp))
	}
}

// A literal glob written into the role by an administrator keeps working.
func TestFunc_PKIStaticGlobDomains(t *testing.T) {
	b, s := funcPKISetup(t, map[string]string{"dom": "unused"})

	if _, err := funcPKIHandle(t, b, s, "roles/t", "", map[string]interface{}{
		"allowed_domains":    []string{"*.example.com"},
		"allow_glob_domains": true,
		"allow_bare_domains": true,
	}); err != nil {
		t.Fatalf("role write: %v", err)
	}

	resp, err := funcPKIHandle(t, b, s, "issue/t", "entity-1", map[string]interface{}{
		"common_name": "evil.example.com",
	})
	if !funcPKIIssued(resp, err) {
		t.Fatalf("expected a certificate under the administrator's literal glob, got err=%v respErr=%v", err, respErr(resp))
	}
}

// A literal glob written into a serial allow-list keeps working.
func TestFunc_PKISerialStaticGlob(t *testing.T) {
	b, s := funcPKISetup(t, map[string]string{"ser": "unused"})

	if _, err := funcPKIHandle(t, b, s, "roles/t", "", map[string]interface{}{
		"allowed_serial_numbers": []string{"f00*"},
		"allow_any_name":         true,
		"require_cn":             false,
	}); err != nil {
		t.Fatalf("role write: %v", err)
	}

	resp, err := funcPKIHandle(t, b, s, "issue/t", "entity-1", map[string]interface{}{
		"common_name":   "foobar",
		"serial_number": "f00deadbeef",
	})
	if !funcPKIIssued(resp, err) {
		t.Fatalf("expected a certificate under the administrator's literal glob, got err=%v respErr=%v", err, respErr(resp))
	}
}

func respErr(resp *logical.Response) string {
	if resp == nil {
		return ""
	}
	if e, ok := resp.Data["error"]; ok {
		if s, ok := e.(string); ok {
			return s
		}
	}
	return ""
}
