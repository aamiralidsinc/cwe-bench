package policy

import (
	"testing"

	"github.com/openbao/openbao/api/v2"
	credUserpass "github.com/openbao/openbao/builtin/credential/userpass"
	vaulthttp "github.com/openbao/openbao/http"
	"github.com/openbao/openbao/sdk/v2/logical"
	"github.com/openbao/openbao/vault"
)

// Hidden behavioural tests. Each drives a real authenticated HTTP read through
// a token whose access-control policy substitutes identity metadata into its
// path pattern.

type funcAclEnv struct {
	root     *api.Client
	rootTok  string
	entityID string
	accessor string
	aliasID  string
}

func funcAclSetup(t *testing.T, policyText string, meta string) *funcAclEnv {
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
		"metadata": map[string]string{"k": meta},
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

	return &funcAclEnv{
		root: root, rootTok: root.Token(), entityID: entityID,
		accessor: auths["userpass/"].Accessor, aliasID: aliasResp.Data["id"].(string),
	}
}

func (e *funcAclEnv) writeSecret(t *testing.T, path string) {
	t.Helper()
	e.root.SetToken(e.rootTok)
	if _, err := e.root.Logical().Write(path, map[string]interface{}{"zip": "zap"}); err != nil {
		t.Fatalf("root write %s: %v", path, err)
	}
}

func (e *funcAclEnv) readOK(t *testing.T, path string) bool {
	t.Helper()
	e.root.SetToken(e.rootTok)
	secret, err := e.root.Logical().Write("auth/userpass/login/alice", map[string]interface{}{"password": "test"})
	if err != nil {
		t.Fatal(err)
	}
	u, err := e.root.Clone()
	if err != nil {
		t.Fatal(err)
	}
	u.SetToken(secret.Auth.ClientToken)
	_, err = u.Logical().Read(path)
	return err == nil
}

// A clean substituted value still grants the path it names.
func TestFunc_ACLLegitimateSubstitution(t *testing.T) {
	e := funcAclSetup(t, `
path "secret/{{identity.entity.metadata.k}}/data" {
  capabilities = ["read"]
}
`, "alice")
	e.writeSecret(t, "secret/alice/data")
	if !e.readOK(t, "secret/alice/data") {
		t.Fatalf("expected a clean substituted path to be readable")
	}
}

// A literal wildcard written into the policy text by an administrator keeps
// working next to a placeholder.
func TestFunc_ACLLiteralGlobInPolicyText(t *testing.T) {
	e := funcAclSetup(t, `
path "secret/literal/{{identity.entity.metadata.k}}/*" {
  capabilities = ["read"]
}
`, "p")
	e.writeSecret(t, "secret/literal/p/foo")
	if !e.readOK(t, "secret/literal/p/foo") {
		t.Fatalf("expected the administrator's literal trailing wildcard to keep matching")
	}
}

// A clean substituted value that is a single ordinary path segment still
// works in a policy that spans several segments.
func TestFunc_ACLMultiSegmentPolicy(t *testing.T) {
	e := funcAclSetup(t, `
path "secret/{{identity.entity.metadata.k}}/cfg" {
  capabilities = ["read"]
}
`, "alice")
	e.writeSecret(t, "secret/alice/cfg")
	if !e.readOK(t, "secret/alice/cfg") {
		t.Fatalf("expected a clean substituted path segment to keep matching")
	}
}

// putPolicy replaces the templated policy, for tests whose placeholder names an
// accessor or group id that exists only after setup.
func (e *funcAclEnv) putPolicy(t *testing.T, policyText string) {
	t.Helper()
	e.root.SetToken(e.rootTok)
	if err := e.root.Sys().PutPolicy("tmpl", policyText); err != nil {
		t.Fatal(err)
	}
}

// A clean entity name still grants the path it names.
func TestFunc_ACLEntityNameLegit(t *testing.T) {
	e := funcAclSetup(t, `
path "secret/{{identity.entity.name}}/data" {
  capabilities = ["read"]
}
`, "alice")
	e.writeSecret(t, "secret/victim/data")
	if !e.readOK(t, "secret/victim/data") {
		t.Fatalf("expected a clean substituted entity name to be readable")
	}
}

// Clean alias values, a name on a second linked auth mount and metadata on the
// login alias, still grant the paths they name.
func TestFunc_ACLAliasValuesLegit(t *testing.T) {
	e := funcAclSetup(t, `
path "secret/data/placeholder" {
  capabilities = ["read"]
}
`, "alice")
	e.root.SetToken(e.rootTok)
	if err := e.root.Sys().EnableAuth("corp", "userpass", ""); err != nil {
		t.Fatal(err)
	}
	auths, _ := e.root.Sys().ListAuth()
	corp := auths["corp/"].Accessor
	if _, err := e.root.Logical().Write("identity/entity-alias", map[string]interface{}{
		"name": "alice.smith", "mount_accessor": corp, "canonical_id": e.entityID,
	}); err != nil {
		t.Fatal(err)
	}
	if _, err := e.root.Logical().Write("identity/entity-alias", map[string]interface{}{
		"id": e.aliasID, "custom_metadata": map[string]string{"team": "platform"},
	}); err != nil {
		t.Fatal(err)
	}
	e.putPolicy(t, `
path "secret/users/{{identity.entity.aliases.`+corp+`.name}}/data" {
  capabilities = ["read"]
}
path "secret/teams/{{identity.entity.aliases.`+e.accessor+`.custom_metadata.team}}/cfg" {
  capabilities = ["read"]
}
`)
	e.writeSecret(t, "secret/users/alice.smith/data")
	e.writeSecret(t, "secret/teams/platform/cfg")
	if !e.readOK(t, "secret/users/alice.smith/data") {
		t.Fatalf("expected a clean substituted alias name to be readable")
	}
	if !e.readOK(t, "secret/teams/platform/cfg") {
		t.Fatalf("expected a clean substituted alias metadata value to be readable")
	}
}

// Clean group values, its name and its metadata, still grant the paths they name.
func TestFunc_ACLGroupValuesLegit(t *testing.T) {
	e := funcAclSetup(t, `
path "secret/data/placeholder" {
  capabilities = ["read"]
}
`, "alice")
	e.root.SetToken(e.rootTok)
	resp, err := e.root.Logical().Write("identity/group", map[string]interface{}{
		"name": "eng", "member_entity_ids": []string{e.entityID},
		"metadata": map[string]string{"env": "staging"},
	})
	if err != nil {
		t.Fatal(err)
	}
	gid := resp.Data["id"].(string)
	e.putPolicy(t, `
path "secret/groups/{{identity.groups.ids.`+gid+`.name}}/data" {
  capabilities = ["read"]
}
path "secret/envs/{{identity.groups.ids.`+gid+`.metadata.env}}/*" {
  capabilities = ["read"]
}
`)
	e.writeSecret(t, "secret/groups/eng/data")
	e.writeSecret(t, "secret/envs/staging/db")
	if !e.readOK(t, "secret/groups/eng/data") {
		t.Fatalf("expected a clean substituted group name to be readable")
	}
	if !e.readOK(t, "secret/envs/staging/db") {
		t.Fatalf("expected a clean substituted group metadata value to be readable")
	}
}
