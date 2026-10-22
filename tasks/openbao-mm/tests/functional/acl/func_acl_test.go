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
}

func funcAclSetup(t *testing.T, policyText string) *funcAclEnv {
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
		"metadata": map[string]string{"k": "alice"},
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
	if _, err := root.Logical().Write("identity/entity-alias", map[string]interface{}{
		"name": "alice", "mount_accessor": auths["userpass/"].Accessor, "canonical_id": entityID,
	}); err != nil {
		t.Fatal(err)
	}

	for _, p := range []string{"secret/alice/data", "secret/literal/p/foo"} {
		if _, err := root.Logical().Write(p, map[string]interface{}{"zip": "zap"}); err != nil {
			t.Logf("root write %s: %v", p, err)
		}
	}

	return &funcAclEnv{root: root, rootTok: root.Token(), entityID: entityID}
}

func (e *funcAclEnv) setMeta(t *testing.T, v string) {
	t.Helper()
	e.root.SetToken(e.rootTok)
	if _, err := e.root.Logical().Write("identity/entity", map[string]interface{}{
		"id": e.entityID, "metadata": map[string]string{"k": v},
	}); err != nil {
		t.Fatal(err)
	}
}

func (e *funcAclEnv) readOK(t *testing.T, path string) bool {
	t.Helper()
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
`)
	e.setMeta(t, "alice")
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
`)
	e.setMeta(t, "p")
	if !e.readOK(t, "secret/literal/p/foo") {
		t.Fatalf("expected the administrator's literal trailing wildcard to keep matching")
	}
}
