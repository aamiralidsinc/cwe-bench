package policy

import (
	"testing"

	"github.com/openbao/openbao/api/v2"
	credUserpass "github.com/openbao/openbao/builtin/credential/userpass"
	vaulthttp "github.com/openbao/openbao/http"
	"github.com/openbao/openbao/sdk/v2/logical"
	"github.com/openbao/openbao/vault"
)

// Hidden behavioural tests. Each drives a real authenticated HTTP request
// through a token whose access-control policy substitutes identity metadata
// into its path pattern.

type secAclEnv struct {
	root     *api.Client
	rootTok  string
	entityID string
	accessor string
	aliasID  string
}

func secAclSetup(t *testing.T, policyText string) *secAclEnv {
	t.Helper()
	coreConfig := &vault.CoreConfig{
		CredentialBackends: map[string]logical.Factory{
			"userpass": credUserpass.Factory,
		},
	}
	cluster := vault.NewTestCluster(t, coreConfig, &vault.TestClusterOptions{
		HandlerFunc: vaulthttp.Handler,
		NumCores:    1,
	})
	cluster.Start()
	t.Cleanup(cluster.Cleanup)
	vault.TestWaitActive(t, cluster.Cores[0].Core)
	root := cluster.Cores[0].Client

	if err := root.Sys().PutPolicy("tmpl", policyText); err != nil {
		t.Fatal(err)
	}
	resp, err := root.Logical().Write("identity/entity", map[string]interface{}{
		"name":     "victim",
		"policies": []string{"tmpl"},
		"metadata": map[string]string{"k": "placeholder"},
	})
	if err != nil {
		t.Fatal(err)
	}
	entityID := resp.Data["id"].(string)

	if err := root.Sys().EnableAuth("userpass", "userpass", ""); err != nil {
		t.Fatal(err)
	}
	if _, err := root.Logical().Write("auth/userpass/users/alice", map[string]interface{}{
		"password": "test", "policies": "tmpl",
	}); err != nil {
		t.Fatal(err)
	}
	auths, _ := root.Sys().ListAuth()
	aliasResp, err := root.Logical().Write("identity/entity-alias", map[string]interface{}{
		"name": "alice", "mount_accessor": auths["userpass/"].Accessor, "canonical_id": entityID,
	})
	if err != nil {
		t.Fatal(err)
	}

	return &secAclEnv{
		root: root, rootTok: root.Token(), entityID: entityID,
		accessor: auths["userpass/"].Accessor, aliasID: aliasResp.Data["id"].(string),
	}
}

// writeSecret stores a value at the given path with the root token.
func (e *secAclEnv) writeSecret(t *testing.T, path string) {
	t.Helper()
	e.root.SetToken(e.rootTok)
	if _, err := e.root.Logical().Write(path, map[string]interface{}{"zip": "zap"}); err != nil {
		t.Fatalf("root write %s: %v", path, err)
	}
}

func (e *secAclEnv) setMeta(t *testing.T, v string) {
	t.Helper()
	e.root.SetToken(e.rootTok)
	if _, err := e.root.Logical().Write("identity/entity", map[string]interface{}{
		"id": e.entityID, "metadata": map[string]string{"k": v},
	}); err != nil {
		t.Fatal(err)
	}
}

func (e *secAclEnv) login(t *testing.T) *api.Client {
	t.Helper()
	e.root.SetToken(e.rootTok)
	secret, err := e.root.Logical().Write("auth/userpass/login/alice", map[string]interface{}{"password": "test"})
	if err != nil {
		t.Fatal(err)
	}
	c, err := e.root.Clone()
	if err != nil {
		t.Fatal(err)
	}
	c.SetToken(secret.Auth.ClientToken)
	return c
}

func (e *secAclEnv) readAllowed(t *testing.T, path string) bool {
	t.Helper()
	u := e.login(t)
	_, err := u.Logical().Read(path)
	return err == nil
}

// A substituted value that is a one-segment wildcard widens the written path.
func TestSec_ACLPlusSegmentWildcard(t *testing.T) {
	e := secAclSetup(t, `
path "secret/{{identity.entity.metadata.k}}/data" {
  capabilities = ["read"]
}
`)
	e.writeSecret(t, "secret/anything/data")
	e.setMeta(t, "+")
	if e.readAllowed(t, "secret/anything/data") {
		t.Fatalf("secret read outside the written path pattern")
	}
}

// A substituted trailing glob widens the written path.
func TestSec_ACLStarTrailingGlob(t *testing.T) {
	e := secAclSetup(t, `
path "secret/data/{{identity.entity.metadata.k}}" {
  capabilities = ["read"]
}
`)
	e.writeSecret(t, "secret/data/anything")
	e.setMeta(t, "*")
	if e.readAllowed(t, "secret/data/anything") {
		t.Fatalf("secret read outside the written path pattern")
	}
}

// A substituted slash spans path segments.
func TestSec_ACLSlashSpansSegments(t *testing.T) {
	e := secAclSetup(t, `
path "secret/{{identity.entity.metadata.k}}/cfg" {
  capabilities = ["read"]
}
`)
	e.writeSecret(t, "secret/alice/extra/cfg")
	e.setMeta(t, "alice/extra")
	if e.readAllowed(t, "secret/alice/extra/cfg") {
		t.Fatalf("secret read outside the written path pattern")
	}
}

// A slash in the substituted value expands one segment into several, even
// next to a literal trailing wildcard written by the administrator.
func TestSec_ACLSlashBesideLiteralWildcard(t *testing.T) {
	e := secAclSetup(t, `
path "secret/literal/{{identity.entity.metadata.k}}/*" {
  capabilities = ["read"]
}
`)
	e.writeSecret(t, "secret/literal/p/evil/foo")
	e.setMeta(t, "p/evil")
	if e.readAllowed(t, "secret/literal/p/evil/foo") {
		t.Fatalf("secret read outside the written path pattern")
	}
}

// putPolicy replaces the templated policy, for tests whose placeholder names an
// accessor or group id that exists only after setup.
func (e *secAclEnv) putPolicy(t *testing.T, policyText string) {
	t.Helper()
	e.root.SetToken(e.rootTok)
	if err := e.root.Sys().PutPolicy("tmpl", policyText); err != nil {
		t.Fatal(err)
	}
}

// addGroup makes the caller's entity a member of a new group and returns its id.
func (e *secAclEnv) addGroup(t *testing.T, name string, meta map[string]string) string {
	t.Helper()
	e.root.SetToken(e.rootTok)
	resp, err := e.root.Logical().Write("identity/group", map[string]interface{}{
		"name": name, "member_entity_ids": []string{e.entityID}, "metadata": meta,
	})
	if err != nil {
		t.Fatal(err)
	}
	return resp.Data["id"].(string)
}

// A substituted entity name that is a one-segment wildcard widens the written path.
func TestSec_ACLEntityNameWildcard(t *testing.T) {
	e := secAclSetup(t, `
path "secret/{{identity.entity.name}}/data" {
  capabilities = ["read"]
}
`)
	e.writeSecret(t, "secret/anything/data")
	e.root.SetToken(e.rootTok)
	if _, err := e.root.Logical().Write("identity/entity", map[string]interface{}{
		"id": e.entityID, "name": "+",
	}); err != nil {
		t.Fatal(err)
	}
	if e.readAllowed(t, "secret/anything/data") {
		t.Fatalf("secret read outside the written path pattern")
	}
}

// A substituted alias name that is a trailing glob widens the written path.
// The alias lives on a second auth mount that is linked to the same entity.
func TestSec_ACLAliasNameGlob(t *testing.T) {
	e := secAclSetup(t, `
path "secret/data/placeholder" {
  capabilities = ["read"]
}
`)
	e.root.SetToken(e.rootTok)
	if err := e.root.Sys().EnableAuth("corp", "userpass", ""); err != nil {
		t.Fatal(err)
	}
	auths, _ := e.root.Sys().ListAuth()
	corp := auths["corp/"].Accessor
	if _, err := e.root.Logical().Write("identity/entity-alias", map[string]interface{}{
		"name": "*", "mount_accessor": corp, "canonical_id": e.entityID,
	}); err != nil {
		t.Fatal(err)
	}
	e.putPolicy(t, `
path "secret/data/{{identity.entity.aliases.`+corp+`.name}}" {
  capabilities = ["read"]
}
`)
	e.writeSecret(t, "secret/data/anything")
	if e.readAllowed(t, "secret/data/anything") {
		t.Fatalf("secret read outside the written path pattern")
	}
}

// A substituted alias metadata value containing a slash spans path segments.
func TestSec_ACLAliasMetadataSlash(t *testing.T) {
	e := secAclSetup(t, `
path "secret/data/placeholder" {
  capabilities = ["read"]
}
`)
	e.root.SetToken(e.rootTok)
	if _, err := e.root.Logical().Write("identity/entity-alias", map[string]interface{}{
		"id": e.aliasID, "custom_metadata": map[string]string{"k": "alice/extra"},
	}); err != nil {
		t.Fatal(err)
	}
	e.putPolicy(t, `
path "secret/{{identity.entity.aliases.`+e.accessor+`.custom_metadata.k}}/cfg" {
  capabilities = ["read"]
}
`)
	e.writeSecret(t, "secret/alice/extra/cfg")
	if e.readAllowed(t, "secret/alice/extra/cfg") {
		t.Fatalf("secret read outside the written path pattern")
	}
}

// A substituted group name that is a one-segment wildcard widens the written path.
func TestSec_ACLGroupNameWildcard(t *testing.T) {
	e := secAclSetup(t, `
path "secret/data/placeholder" {
  capabilities = ["read"]
}
`)
	gid := e.addGroup(t, "+", nil)
	e.putPolicy(t, `
path "secret/{{identity.groups.ids.`+gid+`.name}}/data" {
  capabilities = ["read"]
}
`)
	e.writeSecret(t, "secret/anything/data")
	if e.readAllowed(t, "secret/anything/data") {
		t.Fatalf("secret read outside the written path pattern")
	}
}

// A substituted group metadata value that is a trailing glob widens the written path.
func TestSec_ACLGroupMetadataGlob(t *testing.T) {
	e := secAclSetup(t, `
path "secret/data/placeholder" {
  capabilities = ["read"]
}
`)
	gid := e.addGroup(t, "eng", map[string]string{"k": "*"})
	e.putPolicy(t, `
path "secret/data/{{identity.groups.ids.`+gid+`.metadata.k}}" {
  capabilities = ["read"]
}
`)
	e.writeSecret(t, "secret/data/anything")
	if e.readAllowed(t, "secret/data/anything") {
		t.Fatalf("secret read outside the written path pattern")
	}
}
