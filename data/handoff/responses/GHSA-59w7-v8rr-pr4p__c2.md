<hidden_tests_py>
import os
import pathlib
import subprocess

import pytest

REPO = os.environ["REPO_ROOT"]
PKG = pathlib.Path("vault/external_tests/zzhidden")
SRC = PKG / "zz_hidden_identity_test.go"

GO = r'''package zzhidden

import (
	"crypto/ed25519"
	"crypto/rand"
	"encoding/pem"
	"testing"

	"github.com/openbao/openbao/api/v2"
	credUserpass "github.com/openbao/openbao/builtin/credential/userpass"
	"github.com/openbao/openbao/builtin/logical/pki"
	sshbe "github.com/openbao/openbao/builtin/logical/ssh"
	vaulthttp "github.com/openbao/openbao/http"
	"github.com/openbao/openbao/sdk/v2/logical"
	"github.com/openbao/openbao/vault"
	gossh "golang.org/x/crypto/ssh"
)

func rootClient(t *testing.T, backends map[string]logical.Factory) *api.Client {
	t.Helper()
	cfg := &vault.CoreConfig{
		CredentialBackends: map[string]logical.Factory{
			"userpass": credUserpass.Factory,
		},
	}
	if len(backends) > 0 {
		cfg.LogicalBackends = backends
	}
	cluster := vault.NewTestCluster(t, cfg, &vault.TestClusterOptions{
		HandlerFunc: vaulthttp.Handler,
		NumCores:    1,
	})
	cluster.Start()
	t.Cleanup(cluster.Cleanup)
	vault.TestWaitActive(t, cluster.Cores[0].Core)
	return cluster.Cores[0].Client
}

func userToken(t *testing.T, client *api.Client, policy, rules string, meta map[string]string) string {
	t.Helper()
	if err := client.Sys().PutPolicy(policy, rules); err != nil {
		t.Fatal(err)
	}
	if err := client.Sys().EnableAuthWithOptions("userpass", &api.EnableAuthOptions{Type: "userpass"}); err != nil {
		t.Fatal(err)
	}
	if _, err := client.Logical().Write("auth/userpass/users/member", map[string]interface{}{
		"password": "testpassword",
		"policies": policy,
	}); err != nil {
		t.Fatal(err)
	}
	secret, err := client.Logical().Write("auth/userpass/login/member", map[string]interface{}{
		"password": "testpassword",
	})
	if err != nil || secret == nil || secret.Auth == nil || secret.Auth.EntityID == "" {
		t.Fatalf("login: %v", err)
	}
	if meta != nil {
		if _, err := client.Logical().Write("identity/entity/id/"+secret.Auth.EntityID, map[string]interface{}{
			"metadata": meta,
		}); err != nil {
			t.Fatal(err)
		}
	}
	return secret.Auth.ClientToken
}

func rejectOtherFolder(t *testing.T, client *api.Client, token, folder string) {
	t.Helper()
	existing := "secret/" + folder + "/notes"
	if _, err := client.Logical().Write(existing, map[string]interface{}{"note": "theirs"}); err != nil {
		t.Fatal(err)
	}
	client.SetToken(token)
	if _, err := client.Logical().Write("secret/"+folder+"/new", map[string]interface{}{"note": "x"}); err == nil {
		t.Fatal("create outside the named folder was allowed")
	}
	if _, err := client.Logical().Write(existing, map[string]interface{}{"note": "changed"}); err == nil {
		t.Fatal("update outside the named folder was allowed")
	}
}

func mountPKI(t *testing.T, client *api.Client) {
	t.Helper()
	if err := client.Sys().Mount("pki", &api.MountInput{
		Type: "pki",
		Config: api.MountConfigInput{
			DefaultLeaseTTL: "16h",
			MaxLeaseTTL:     "60h",
		},
	}); err != nil {
		t.Fatal(err)
	}
	if _, err := client.Logical().Write("pki/root/generate/internal", map[string]interface{}{
		"ttl":         "40h",
		"common_name": "example.com",
	}); err != nil {
		t.Fatal(err)
	}
}

func keypair(t *testing.T) (string, string) {
	t.Helper()
	_, priv, err := ed25519.GenerateKey(rand.Reader)
	if err != nil {
		t.Fatal(err)
	}
	signer, err := gossh.NewSignerFromKey(priv)
	if err != nil {
		t.Fatal(err)
	}
	block, err := gossh.MarshalPrivateKey(priv, "hidden")
	if err != nil {
		t.Fatal(err)
	}
	return string(gossh.MarshalAuthorizedKey(signer.PublicKey())), string(pem.EncodeToMemory(block))
}

func mountSSH(t *testing.T, client *api.Client, pub, priv string) {
	t.Helper()
	if err := client.Sys().Mount("ssh", &api.MountInput{
		Type: "ssh",
		Config: api.MountConfigInput{
			DefaultLeaseTTL: "16h",
			MaxLeaseTTL:     "60h",
		},
	}); err != nil {
		t.Fatal(err)
	}
	if _, err := client.Logical().Write("ssh/config/ca", map[string]interface{}{
		"public_key":  pub,
		"private_key": priv,
	}); err != nil {
		t.Fatal(err)
	}
}

func writeRole(t *testing.T, client *api.Client, path string, data map[string]interface{}) {
	t.Helper()
	if _, err := client.Logical().Write(path, data); err != nil {
		t.Fatalf("role %s: %v", path, err)
	}
}

func TestSecurityPolicyAsterisk(t *testing.T) {
	client := rootClient(t, nil)
	token := userToken(t, client, "team", `
path "secret/{{identity.entity.metadata.team}}" {
  capabilities = ["create", "read", "update"]
}
`, map[string]string{"team": "*"})
	rejectOtherFolder(t, client, token, "blueteam")
}

func TestSecurityPolicyPlus(t *testing.T) {
	client := rootClient(t, nil)
	token := userToken(t, client, "team", `
path "secret/{{identity.entity.metadata.team}}/*" {
  capabilities = ["create", "read", "update"]
}
`, map[string]string{"team": "+"})
	rejectOtherFolder(t, client, token, "otherteam")
}

func TestSecurityFilledNameGlob(t *testing.T) {
	client := rootClient(t, map[string]logical.Factory{"pki": pki.Factory})
	mountPKI(t, client)
	writeRole(t, client, "pki/roles/test", map[string]interface{}{
		"allowed_domains":          []string{"{{identity.entity.metadata.domains}}"},
		"allowed_domains_template": true,
		"allow_glob_domains":       true,
	})
	token := userToken(t, client, "issue", `
path "pki/issue/*" {
  capabilities = ["update"]
}
`, map[string]string{"domains": "*.example.com"})
	client.SetToken(token)
	if _, err := client.Logical().Write("pki/issue/test", map[string]interface{}{
		"common_name": "other.example.com",
	}); err == nil {
		t.Fatal("filled name granted a certificate the operator did not write")
	}
}

func TestSecurityFilledURIGlob(t *testing.T) {
	client := rootClient(t, map[string]logical.Factory{"pki": pki.Factory})
	mountPKI(t, client)
	writeRole(t, client, "pki/roles/test", map[string]interface{}{
		"allowed_uri_sans":          []string{"{{identity.entity.metadata.sans}}"},
		"allowed_uri_sans_template": true,
		"require_cn":                false,
	})
	token := userToken(t, client, "issue", `
path "pki/issue/*" {
  capabilities = ["update"]
}
`, map[string]string{"sans": "spiffe://domain/users/*"})
	client.SetToken(token)
	if _, err := client.Logical().Write("pki/issue/test", map[string]interface{}{
		"uri_sans": "spiffe://domain/users/other",
	}); err == nil {
		t.Fatal("filled name granted a certificate the operator did not write")
	}
}

func TestSecurityFilledNameExtraUser(t *testing.T) {
	client := rootClient(t, map[string]logical.Factory{"ssh": sshbe.Factory})
	caPub, caPriv := keypair(t)
	userPub, _ := keypair(t)
	mountSSH(t, client, caPub, caPriv)
	writeRole(t, client, "ssh/roles/test", map[string]interface{}{
		"key_type":               "ca",
		"allow_user_certificates": true,
		"allowed_users":          "{{identity.entity.metadata.user}}",
		"allowed_users_template": true,
	})
	token := userToken(t, client, "sign", `
path "ssh/sign/*" {
  capabilities = ["update"]
}
`, map[string]string{"user": "alice,bob"})
	client.SetToken(token)
	if _, err := client.Logical().Write("ssh/sign/test", map[string]interface{}{
		"public_key":       userPub,
		"cert_type":        "user",
		"valid_principals": "bob",
	}); err == nil {
		t.Fatal("filled name granted a user the operator did not write")
	}
}

func TestSecurityFilledNameExtraHost(t *testing.T) {
	client := rootClient(t, map[string]logical.Factory{"ssh": sshbe.Factory})
	caPub, caPriv := keypair(t)
	userPub, _ := keypair(t)
	mountSSH(t, client, caPub, caPriv)
	writeRole(t, client, "ssh/roles/test", map[string]interface{}{
		"key_type":                 "ca",
		"allow_host_certificates":  true,
		"allow_bare_domains":       true,
		"allowed_domains":          "{{identity.entity.metadata.host}}",
		"allowed_domains_template": true,
	})
	token := userToken(t, client, "sign", `
path "ssh/sign/*" {
  capabilities = ["update"]
}
`, map[string]string{"host": "good.example,evil.example"})
	client.SetToken(token)
	if _, err := client.Logical().Write("ssh/sign/test", map[string]interface{}{
		"public_key":       userPub,
		"cert_type":        "host",
		"valid_principals": "evil.example",
	}); err == nil {
		t.Fatal("filled name granted a host the operator did not write")
	}
}

func TestFunctionalOrdinaryFolder(t *testing.T) {
	client := rootClient(t, nil)
	token := userToken(t, client, "team", `
path "secret/{{identity.entity.metadata.team}}/*" {
  capabilities = ["create", "read", "update"]
}
`, map[string]string{"team": "red"})
	client.SetToken(token)
	if _, err := client.Logical().Write("secret/red/item", map[string]interface{}{"note": "one"}); err != nil {
		t.Fatalf("create: %v", err)
	}
	sec, err := client.Logical().Read("secret/red/item")
	if err != nil || sec == nil || sec.Data["note"] != "one" {
		t.Fatalf("read: %v %#v", err, sec)
	}
	if _, err := client.Logical().Write("secret/red/item", map[string]interface{}{"note": "two"}); err != nil {
		t.Fatalf("update: %v", err)
	}
	sec, err = client.Logical().Read("secret/red/item")
	if err != nil || sec == nil || sec.Data["note"] != "two" {
		t.Fatalf("read after update: %v %#v", err, sec)
	}
	if _, err := client.Logical().Write("secret/blue/item", map[string]interface{}{"note": "x"}); err == nil {
		t.Fatal("ordinary name granted another folder")
	}
}

func TestFunctionalOperatorWildcard(t *testing.T) {
	client := rootClient(t, nil)
	token := userToken(t, client, "team", `
path "secret/published/*" {
  capabilities = ["create", "read", "update"]
}
`, nil)
	client.SetToken(token)
	if _, err := client.Logical().Write("secret/published/item", map[string]interface{}{"note": "ok"}); err != nil {
		t.Fatalf("operator wildcard: %v", err)
	}
	sec, err := client.Logical().Read("secret/published/item")
	if err != nil || sec == nil || sec.Data["note"] != "ok" {
		t.Fatalf("operator wildcard read: %v %#v", err, sec)
	}
}

func TestFunctionalUntouchedPath(t *testing.T) {
	client := rootClient(t, nil)
	token := userToken(t, client, "team", `
path "secret/kept" {
  capabilities = ["create", "read", "update"]
}
path "secret/{{identity.entity.metadata.team}}/*" {
  capabilities = ["create", "read", "update"]
}
`, map[string]string{"team": "+"})
	client.SetToken(token)
	if _, err := client.Logical().Write("secret/kept", map[string]interface{}{"note": "stay"}); err != nil {
		t.Fatalf("untouched path: %v", err)
	}
	sec, err := client.Logical().Read("secret/kept")
	if err != nil || sec == nil || sec.Data["note"] != "stay" {
		t.Fatalf("untouched read: %v %#v", err, sec)
	}
}

func TestFunctionalOrdinaryCertificate(t *testing.T) {
	client := rootClient(t, map[string]logical.Factory{"pki": pki.Factory})
	mountPKI(t, client)
	writeRole(t, client, "pki/roles/test", map[string]interface{}{
		"allowed_domains":          []string{"{{identity.entity.metadata.cn}}"},
		"allowed_domains_template": true,
		"allow_bare_domains":       true,
	})
	token := userToken(t, client, "issue", `
path "pki/issue/*" {
  capabilities = ["update"]
}
`, map[string]string{"cn": "app.example.com"})
	client.SetToken(token)
	if _, err := client.Logical().Write("pki/issue/test", map[string]interface{}{
		"common_name": "app.example.com",
	}); err != nil {
		t.Fatalf("ordinary certificate name: %v", err)
	}
	if _, err := client.Logical().Write("pki/issue/test", map[string]interface{}{
		"common_name": "other.example.com",
	}); err == nil {
		t.Fatal("ordinary name granted a different certificate")
	}
}

func TestFunctionalOrdinarySSHUser(t *testing.T) {
	client := rootClient(t, map[string]logical.Factory{"ssh": sshbe.Factory})
	caPub, caPriv := keypair(t)
	userPub, _ := keypair(t)
	mountSSH(t, client, caPub, caPriv)
	writeRole(t, client, "ssh/roles/test", map[string]interface{}{
		"key_type":               "ca",
		"allow_user_certificates": true,
		"allowed_users":          "{{identity.entity.metadata.user}}",
		"allowed_users_template": true,
	})
	token := userToken(t, client, "sign", `
path "ssh/sign/*" {
  capabilities = ["update"]
}
`, map[string]string{"user": "alice"})
	client.SetToken(token)
	if _, err := client.Logical().Write("ssh/sign/test", map[string]interface{}{
		"public_key":       userPub,
		"cert_type":        "user",
		"valid_principals": "alice",
	}); err != nil {
		t.Fatalf("ordinary ssh user: %v", err)
	}
	if _, err := client.Logical().Write("ssh/sign/test", map[string]interface{}{
		"public_key":       userPub,
		"cert_type":        "user",
		"valid_principals": "carol",
	}); err == nil {
		t.Fatal("ordinary name granted a different user")
	}
}

func TestFunctionalOperatorPattern(t *testing.T) {
	client := rootClient(t, map[string]logical.Factory{
		"pki": pki.Factory,
		"ssh": sshbe.Factory,
	})
	mountPKI(t, client)
	writeRole(t, client, "pki/roles/test", map[string]interface{}{
		"allowed_domains":    []string{"*.corp.example"},
		"allow_glob_domains": true,
	})
	caPub, caPriv := keypair(t)
	userPub, _ := keypair(t)
	mountSSH(t, client, caPub, caPriv)
	writeRole(t, client, "ssh/roles/test", map[string]interface{}{
		"key_type":                "ca",
		"allow_user_certificates": true,
		"allowed_users":           "alice,bob",
	})
	token := userToken(t, client, "caller", `
path "pki/issue/*" {
  capabilities = ["update"]
}
path "ssh/sign/*" {
  capabilities = ["update"]
}
`, nil)
	client.SetToken(token)
	if _, err := client.Logical().Write("pki/issue/test", map[string]interface{}{
		"common_name": "web.corp.example",
	}); err != nil {
		t.Fatalf("operator glob: %v", err)
	}
	if _, err := client.Logical().Write("pki/issue/test", map[string]interface{}{
		"common_name": "web.other.example",
	}); err == nil {
		t.Fatal("operator glob matched a different name")
	}
	if _, err := client.Logical().Write("ssh/sign/test", map[string]interface{}{
		"public_key":       userPub,
		"cert_type":        "user",
		"valid_principals": "bob",
	}); err != nil {
		t.Fatalf("operator name list: %v", err)
	}
	if _, err := client.Logical().Write("ssh/sign/test", map[string]interface{}{
		"public_key":       userPub,
		"cert_type":        "user",
		"valid_principals": "carol",
	}); err == nil {
		t.Fatal("operator name list granted a name that was not written")
	}
}
'''


@pytest.fixture(scope="module", autouse=True)
def _hidden_go_test():
    dest = pathlib.Path(REPO) / SRC
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(GO)
    try:
        yield
    finally:
        dest.unlink(missing_ok=True)
        try:
            dest.parent.rmdir()
        except OSError:
            pass


def _run(name):
    proc = subprocess.run(
        ["go", "test", "-count=1", "-timeout", "600s", "-run", "^" + name + "$", "./" + PKG.as_posix()],
        cwd=REPO,
        capture_output=True,
        text=True,
        timeout=900,
    )
    if proc.returncode != 0:
        pytest.fail(name + "\n" + proc.stdout + "\n" + proc.stderr)


def test_security_policy_asterisk_metadata():
    _run("TestSecurityPolicyAsterisk")


def test_security_policy_plus_metadata():
    _run("TestSecurityPolicyPlus")


def test_security_filled_name_glob():
    _run("TestSecurityFilledNameGlob")


def test_security_filled_uri_glob():
    _run("TestSecurityFilledURIGlob")


def test_security_filled_name_extra_user():
    _run("TestSecurityFilledNameExtraUser")


def test_security_filled_name_extra_host():
    _run("TestSecurityFilledNameExtraHost")


def test_functional_ordinary_metadata_folder():
    _run("TestFunctionalOrdinaryFolder")


def test_functional_operator_typed_wildcard():
    _run("TestFunctionalOperatorWildcard")


def test_functional_untouched_path_beside_widening_value():
    _run("TestFunctionalUntouchedPath")


def test_functional_ordinary_filled_certificate_name():
    _run("TestFunctionalOrdinaryCertificate")


def test_functional_ordinary_filled_ssh_user():
    _run("TestFunctionalOrdinarySSHUser")


def test_functional_operator_typed_pattern():
    _run("TestFunctionalOperatorPattern")
</hidden_tests_py>
