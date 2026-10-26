package webhook

import (
	"context"
	"log/slog"
	"testing"

	corev1 "k8s.io/api/core/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"

	"github.com/slok/kubewebhook/v2/pkg/model"
	"github.com/spf13/viper"
)

// The operator's own Vault address keeps working, including on a local or
// private network address.
func TestFunc_OperatorVaultAddressIsUsed(t *testing.T) {
	stkConfig(t)
	srv := stkVault(t, false, "operator-value")
	viper.Set("vault_addr", srv.url())

	mw, err := NewMutatingWebhook(slog.New(slog.DiscardHandler), stkTenantClient(t))
	if err != nil {
		t.Fatalf("cannot build the webhook: %v", err)
	}

	obj := stkSecretConfigMap(map[string]string{stkSAAnn: "default"})
	if _, err = mw.VaultSecretsMutator(context.Background(), &model.AdmissionReview{Namespace: stkNamespace}, obj); err != nil {
		t.Fatalf("the operator's own Vault address stopped working: %v", err)
	}
	if got := obj.Data["DB_PASSWORD"]; got != "operator-value" {
		t.Fatalf("the value was not read from the operator's Vault: got %q", got)
	}
}

// An object that asks for the address the operator already configured is not
// changing anything and keeps working.
func TestFunc_ObjectRepeatingOperatorAddressStillWorks(t *testing.T) {
	stkConfig(t)
	_, addr := stkVaultNamed(t, "operator-value")
	viper.Set("vault_addr", addr)

	mw, err := NewMutatingWebhook(slog.New(slog.DiscardHandler), stkTenantClient(t))
	if err != nil {
		t.Fatalf("cannot build the webhook: %v", err)
	}

	obj := stkSecretConfigMap(map[string]string{
		stkAddrAnn: addr,
		stkSAAnn:   "default",
	})
	if _, err = mw.VaultSecretsMutator(context.Background(), &model.AdmissionReview{Namespace: stkNamespace}, obj); err != nil {
		t.Fatalf("an object repeating the operator's address stopped working: %v", err)
	}
	if got := obj.Data["DB_PASSWORD"]; got != "operator-value" {
		t.Fatalf("the value was not read from the operator's Vault: got %q", got)
	}
}

// The operator can enable skipping of certificate verification for the Vault
// connection; that keeps working.
func TestFunc_OperatorVaultSkipVerifyStillApplies(t *testing.T) {
	stkConfig(t)
	srv := stkVault(t, true, "operator-value")
	viper.Set("vault_addr", srv.url())
	viper.Set("vault_skip_verify", true)

	mw, err := NewMutatingWebhook(slog.New(slog.DiscardHandler), stkTenantClient(t))
	if err != nil {
		t.Fatalf("cannot build the webhook: %v", err)
	}

	obj := stkSecretConfigMap(map[string]string{stkSAAnn: "default"})
	if _, err = mw.VaultSecretsMutator(context.Background(), &model.AdmissionReview{Namespace: stkNamespace}, obj); err != nil {
		t.Fatalf("the operator's own skip-verify setting stopped working: %v", err)
	}
	if got := obj.Data["DB_PASSWORD"]; got != "operator-value" {
		t.Fatalf("the value was not read from the operator's Vault: got %q", got)
	}
}

// When the operator has allowed it, an object-supplied setting is honoured.
func TestFunc_ObjectVaultSkipVerifyHonouredWhenOperatorAllows(t *testing.T) {
	stkConfig(t)
	srv := stkVault(t, true, "operator-value")
	viper.Set("vault_addr", srv.url())
	viper.Set("vault_skip_verify", true)

	mw, err := NewMutatingWebhook(slog.New(slog.DiscardHandler), stkTenantClient(t))
	if err != nil {
		t.Fatalf("cannot build the webhook: %v", err)
	}

	obj := stkSecretConfigMap(map[string]string{
		stkVaultSkipAnn: "true",
		stkSAAnn:        "default",
	})
	if _, err = mw.VaultSecretsMutator(context.Background(), &model.AdmissionReview{Namespace: stkNamespace}, obj); err != nil {
		t.Fatalf("an object-supplied setting the operator allows stopped working: %v", err)
	}
	if got := obj.Data["DB_PASSWORD"]; got != "operator-value" {
		t.Fatalf("the value was not read from the operator's Vault: got %q", got)
	}
}

// The operator can enable skipping of certificate verification for image
// configuration fetches; that keeps working.
func TestFunc_OperatorRegistrySkipVerifyStillApplies(t *testing.T) {
	stkConfig(t)
	_, image := stkRegistry(t, true)
	viper.Set("registry_skip_verify", true)

	mw, err := NewMutatingWebhook(slog.New(slog.DiscardHandler), stkTenantClient(t))
	if err != nil {
		t.Fatalf("cannot build the webhook: %v", err)
	}

	pod := stkVaultPod(nil, image)
	if _, err = mw.VaultSecretsMutator(context.Background(), &model.AdmissionReview{Namespace: stkNamespace}, pod); err != nil {
		t.Fatalf("the operator's own registry setting stopped working: %v", err)
	}
	if cmd := pod.Spec.Containers[0].Command; len(cmd) == 0 || cmd[0] != "/vault/vault-env" {
		t.Fatalf("the pod was not mutated with the image configuration: %v", cmd)
	}
}

// When the operator has allowed it, an object-supplied registry setting is honoured.
func TestFunc_ObjectRegistrySkipVerifyHonouredWhenOperatorAllows(t *testing.T) {
	stkConfig(t)
	_, image := stkRegistry(t, true)
	viper.Set("registry_skip_verify", true)

	mw, err := NewMutatingWebhook(slog.New(slog.DiscardHandler), stkTenantClient(t))
	if err != nil {
		t.Fatalf("cannot build the webhook: %v", err)
	}

	pod := stkVaultPod(map[string]string{stkRegistrySkipAnn: "true"}, image)
	if _, err = mw.VaultSecretsMutator(context.Background(), &model.AdmissionReview{Namespace: stkNamespace}, pod); err != nil {
		t.Fatalf("an object-supplied registry setting the operator allows stopped working: %v", err)
	}
	if cmd := pod.Spec.Containers[0].Command; len(cmd) == 0 || cmd[0] != "/vault/vault-env" {
		t.Fatalf("the pod was not mutated with the image configuration: %v", cmd)
	}
}

// With no operator opt-in, an image configuration fetch still verifies the
// certificate it is given.
func TestFunc_RegistryVerificationStaysOnByDefault(t *testing.T) {
	stkConfig(t)
	_, image := stkRegistry(t, true)

	mw, err := NewMutatingWebhook(slog.New(slog.DiscardHandler), stkTenantClient(t))
	if err != nil {
		t.Fatalf("cannot build the webhook: %v", err)
	}

	pod := stkVaultPod(nil, image)
	if _, err = mw.VaultSecretsMutator(context.Background(), &model.AdmissionReview{Namespace: stkNamespace}, pod); err == nil {
		t.Fatalf("an unverified registry certificate was accepted without an operator opt-in")
	}
}

// Objects that reference nothing in Vault are left exactly as they are.
func TestFunc_ObjectWithoutVaultReferencesIsUntouched(t *testing.T) {
	stkConfig(t)
	srv := stkVault(t, false, "operator-value")
	viper.Set("vault_addr", srv.url())

	mw, err := NewMutatingWebhook(slog.New(slog.DiscardHandler), stkTenantClient(t))
	if err != nil {
		t.Fatalf("cannot build the webhook: %v", err)
	}

	obj := &corev1.ConfigMap{
		ObjectMeta: metav1.ObjectMeta{Name: "plain", Namespace: stkNamespace},
		Data:       map[string]string{"GREETING": "hello"},
	}
	if _, err = mw.VaultSecretsMutator(context.Background(), &model.AdmissionReview{Namespace: stkNamespace}, obj); err != nil {
		t.Fatalf("a plain object was refused: %v", err)
	}
	if len(obj.Data) != 1 || obj.Data["GREETING"] != "hello" {
		t.Fatalf("a plain object was modified: %v", obj.Data)
	}
	if n := srv.count(); n != 0 {
		t.Fatalf("a plain object caused %d Vault request(s)", n)
	}
}
