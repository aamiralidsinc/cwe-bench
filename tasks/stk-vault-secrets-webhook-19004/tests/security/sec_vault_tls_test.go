package webhook

import (
	"context"
	"log/slog"
	"testing"

	"github.com/slok/kubewebhook/v2/pkg/model"
	"github.com/spf13/viper"
)

// An object must not be able to make the webhook's own Vault client accept an
// unverified certificate when the operator has not allowed that.
func TestSec_ObjectCannotWeakenVaultCertificateVerification(t *testing.T) {
	stkConfig(t)
	srv := stkVault(t, true, "object-value")
	viper.Set("vault_addr", srv.url())
	viper.Set("vault_skip_verify", false)

	mw, err := NewMutatingWebhook(slog.New(slog.DiscardHandler), stkTenantClient(t))
	if err != nil {
		t.Fatalf("cannot build the webhook: %v", err)
	}

	obj := stkSecretConfigMap(map[string]string{
		stkVaultSkipAnn: "true",
		stkSAAnn:        "default",
	})
	if _, err = mw.VaultSecretsMutator(context.Background(), &model.AdmissionReview{Namespace: stkNamespace}, obj); err == nil {
		t.Fatalf("a workload object made the webhook accept an unverified certificate for its own Vault connection")
	}
	if n := srv.count(); n != 0 {
		t.Fatalf("the webhook completed %d request(s) over an unverified connection", n)
	}
	if got := obj.Data["DB_PASSWORD"]; got != "vault:secret/data/team/app#password" {
		t.Fatalf("the refused object was modified: password became %q", got)
	}
}
