package webhook

import (
	"context"
	"log/slog"
	"testing"

	corev1 "k8s.io/api/core/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/client-go/kubernetes/fake"

	"github.com/slok/kubewebhook/v2/pkg/model"
	"github.com/spf13/viper"
)

// Refusing an object-supplied address must leave nothing behind: in particular
// no credential is minted for the service account the object names.
func TestSec_RefusedAddressHasNoOtherEffect(t *testing.T) {
	stkConfig(t)
	operator := stkVault(t, false, "operator-value")
	hostile := stkVault(t, false, "object-value")
	viper.Set("vault_addr", operator.url())

	cs := fake.NewClientset(&corev1.ServiceAccount{
		ObjectMeta: metav1.ObjectMeta{Name: "tenant-sa", Namespace: stkNamespace},
	})
	stkTokenReactor(cs)

	mw, err := NewMutatingWebhook(slog.New(slog.DiscardHandler), cs)
	if err != nil {
		t.Fatalf("cannot build the webhook: %v", err)
	}

	obj := stkSecretConfigMap(map[string]string{
		stkAddrAnn: hostile.url(),
		stkSAAnn:   "tenant-sa",
	})
	if _, err = mw.VaultSecretsMutator(context.Background(), &model.AdmissionReview{Namespace: stkNamespace}, obj); err == nil {
		t.Fatalf("a workload object redirected the webhook's Vault connection to its own address")
	}
	if n := stkTokenMints(cs); n != 0 {
		t.Fatalf("the webhook minted %d service account token(s) for a request it then refused", n)
	}
	if n := hostile.count(); n != 0 {
		t.Fatalf("the webhook opened %d connection(s) to the object-supplied address", n)
	}
}
