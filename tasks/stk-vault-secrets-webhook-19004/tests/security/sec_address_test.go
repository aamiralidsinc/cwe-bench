package webhook

import (
	"context"
	"log/slog"
	"testing"

	"github.com/slok/kubewebhook/v2/pkg/model"
	"github.com/spf13/viper"
)

// An object must not be able to move the webhook's own Vault connection to an
// address the operator did not configure.
func TestSec_ObjectVaultAddressCannotRedirectTheWebhook(t *testing.T) {
	stkConfig(t)
	operator := stkVault(t, false, "operator-value")
	hostile := stkVault(t, false, "object-value")
	viper.Set("vault_addr", operator.url())

	mw, err := NewMutatingWebhook(slog.New(slog.DiscardHandler), stkTenantClient(t))
	if err != nil {
		t.Fatalf("cannot build the webhook: %v", err)
	}

	obj := stkSecretConfigMap(map[string]string{
		stkAddrAnn: hostile.url(),
		stkSAAnn:   "default",
	})
	if _, err = mw.VaultSecretsMutator(context.Background(), &model.AdmissionReview{Namespace: stkNamespace}, obj); err == nil {
		t.Fatalf("a workload object redirected the webhook's Vault connection to its own address")
	}
	if n := hostile.count(); n != 0 {
		t.Fatalf("the webhook opened %d connection(s) to the object-supplied address", n)
	}
	if got := obj.Data["DB_PASSWORD"]; got != "vault:secret/data/team/app#password" {
		t.Fatalf("the refused object was modified: password became %q", got)
	}
}
