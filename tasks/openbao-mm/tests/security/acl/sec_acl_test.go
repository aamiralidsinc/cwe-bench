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

type aclEnv struct {
	root     *api.Client
	rootTok  string
	entityID string
}

func secACLSetup(t *testing.T, policyText string) *aclEnv {
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
	if _, err := root.Logical().Write("identity/entity-alias", map[string]interface{}{
		"name": "alice", "mount_accessor": auths["userpass/"].Accessor, "canonical_id": entityID,
	}); err != nil {
		t.Fatal(err)
	}

	// Secret that a widened match would reach.
	root.SetToken(root.Token())
	if _, err := root.Logical().Write("secret/alice/data", map[string]interface{}{"zip": "zap"}); err != nil {
		t.Logf("root write: %v", err)
	}

	return &aclEnv{root: root, rootTok: root.Token(), entityID: entityID}
}

func (e *aclEnv) setMeta(t *testing.T, v string) {
	t.Helper()
	e.root.SetToken(e.rootTok)
	if _, err := e.root.Logical().Write("identity/entity", map[string]interface{}{
		"id": e.entityID, "metadata": map[string]string{"k": v},
	}); err != nil {
		t.Fatal(err)
	}
}

func (e *aclEnv) login(t *testing.T) *api.Client {
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

func (e *aclEnv) readAllowed(t *testing.T, path string) bool {
	t.Helper()
	u := e.login(t)
	_, err := u.Logical().Read(path)
	return err == nil
}

const secAclPolicyPlus = `
path "secret/{{identity.entity.metadata.k}}/data" {
  capabilities = ["read"]
}
`

const secAclPolicyStar = `
path "secret/data/{{identity.entity.metadata.k}}" {
  capabilities = ["read"]
}
`

const secAclPolicySpan = `
path "secret/{{identity.entity.metadata.k}}/cfg" {
  capabilities = ["read"]
}
`

func TestSec_ACLPlusSegmentWildcard(t *testing.T) {
	e := secACLSetup(t, secAclPolicyPlus)
	e.setMeta(t, "+")
	if e.readAllowed(t, "secret/anything/data") {
		t.Fatalf("secret read outside the written path pattern")
	}
}

func TestSec_ACLStarTrailingGlob(t *testing.T) {
	e := secACLSetup(t, secAclPolicyStar)
	e.setMeta(t, "*")
	if e.readAllowed(t, "secret/data/anything") {
		t.Fatalf("secret read outside the written path pattern")
	}
}

func TestSec_ACLSlashSpansSegments(t *testing.T) {
	e := secACLSetup(t, secAclPolicySpan)
	e.setMeta(t, "alice/extra")
	if e.readAllowed(t, "secret/alice/extra/cfg") {
		t.Fatalf("secret read outside the written path pattern")
	}
}

func TestSec_ACLSlashPlus(t *testing.T) {
	// A slash in the substituted value expands one path segment into several,
	// even next to a literal trailing wildcard written by the administrator.
	e := secACLSetup(t, `
path "secret/literal/{{identity.entity.metadata.k}}/*" {
  capabilities = ["read"]
}
`)
	if _, err := e.root.Logical().Write("secret/literal/p/evil/foo", map[string]interface{}{"zip": "zap"}); err != nil {
		t.Logf("root write: %v", err)
	}
	e.setMeta(t, "p/evil")
	if e.readAllowed(t, "secret/literal/p/evil/foo") {
		t.Fatalf("secret read outside the written path pattern")
	}
}
