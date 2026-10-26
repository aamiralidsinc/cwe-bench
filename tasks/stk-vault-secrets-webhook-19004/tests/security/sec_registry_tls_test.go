package webhook

import (
	"context"
	"log/slog"
	"testing"

	"github.com/slok/kubewebhook/v2/pkg/model"
	"github.com/spf13/viper"
)

// The same rule on the webhook's other outbound connection: an object must not
// be able to make it trust an unverified certificate.
func TestSec_ObjectCannotWeakenRegistryCertificateVerification(t *testing.T) {
	stkConfig(t)
	srv, image := stkRegistry(t, true)
	viper.Set("registry_skip_verify", false)

	mw, err := NewMutatingWebhook(slog.New(slog.DiscardHandler), stkTenantClient(t))
	if err != nil {
		t.Fatalf("cannot build the webhook: %v", err)
	}

	pod := stkVaultPod(map[string]string{stkRegistrySkipAnn: "true"}, image)
	if _, err = mw.VaultSecretsMutator(context.Background(), &model.AdmissionReview{Namespace: stkNamespace}, pod); err == nil {
		t.Fatalf("a workload object made the webhook accept an unverified certificate on its own registry connection")
	}
	if n := srv.count(); n != 0 {
		t.Fatalf("the webhook completed %d request(s) over an unverified registry connection", n)
	}
	if cmd := pod.Spec.Containers[0].Command; len(cmd) != 0 {
		t.Fatalf("the refused pod was mutated: command became %v", cmd)
	}
}
