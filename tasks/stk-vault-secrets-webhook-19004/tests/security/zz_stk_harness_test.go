// Shared harness for this task's hidden suites. No product identifiers a solver
// would have to guess: only public Kubernetes and annotation surfaces.
package webhook

import (
	"crypto/sha256"
	"encoding/hex"
	"fmt"
	"net"
	"net/http"
	"net/http/httptest"
	"os"
	"strings"
	"sync/atomic"
	"testing"

	authenticationv1 "k8s.io/api/authentication/v1"
	corev1 "k8s.io/api/core/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/runtime"
	"k8s.io/client-go/kubernetes/fake"
	k8stesting "k8s.io/client-go/testing"

	"github.com/spf13/viper"
)

const stkNamespace = "tenant-a"

const (
	stkAddrAnn         = "vault.security.banzaicloud.io/vault-addr"
	stkVaultSkipAnn    = "vault.security.banzaicloud.io/vault-skip-verify"
	stkRegistrySkipAnn = "vault.security.banzaicloud.io/registry-skip-verify"
	stkSAAnn           = "vault.security.banzaicloud.io/vault-serviceaccount"
)

// stkConfig starts every case from the product's own defaults.
func stkConfig(t *testing.T) {
	t.Helper()
	viper.Reset()
	SetConfigDefaults()
	if err := os.Setenv("KUBERNETES_NAMESPACE", "webhook-system"); err != nil {
		t.Fatalf("cannot set namespace: %v", err)
	}
}

// stkLocalHost is a name for this machine that the resolver knows. It is used
// where an address has to look like an operator-configured hostname rather than
// a bare loopback literal.
func stkLocalHost() string {
	if h, err := os.Hostname(); err == nil && h != "" {
		if addrs, err := net.LookupHost(h); err == nil && len(addrs) > 0 {
			return h
		}
	}
	return "127.0.0.1"
}

type stkServer struct {
	srv  *httptest.Server
	hits int32
}

func (s *stkServer) count() int    { return int(atomic.LoadInt32(&s.hits)) }
func (s *stkServer) url() string   { return s.srv.URL }
func (s *stkServer) host() string  { return strings.TrimPrefix(s.srv.URL, "https://") }
func (s *stkServer) addr() string  { return strings.TrimPrefix(strings.TrimPrefix(s.srv.URL, "https://"), "http://") }

func stkServe(t *testing.T, handler http.Handler, secure bool) *stkServer {
	t.Helper()
	s := &stkServer{}
	wrapped := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		atomic.AddInt32(&s.hits, 1)
		handler.ServeHTTP(w, r)
	})
	if secure {
		s.srv = httptest.NewTLSServer(wrapped)
	} else {
		s.srv = httptest.NewServer(wrapped)
	}
	t.Cleanup(s.srv.Close)
	return s
}

// stkVault is a minimal Vault-shaped endpoint: it answers a login and returns
// one KV v2 secret whose value is `value`.
func stkVault(t *testing.T, secure bool, value string) *stkServer {
	t.Helper()
	return stkServe(t, http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		if strings.HasPrefix(r.URL.Path, "/v1/auth") {
			fmt.Fprint(w, `{"auth":{"client_token":"stk-token"}}`)
			return
		}
		fmt.Fprintf(w, `{"data":{"data":{"password":%q},"metadata":{"version":1}},"lease_duration":0}`, value)
	}), secure)
}

// stkVaultNamed is the same endpoint, reachable by this machine's own name, so
// an operator-style address carries a hostname instead of a loopback literal.
func stkVaultNamed(t *testing.T, value string) (*stkServer, string) {
	t.Helper()
	ln, err := net.Listen("tcp", ":0")
	if err != nil {
		t.Fatalf("cannot listen: %v", err)
	}
	s := &stkServer{}
	h := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		atomic.AddInt32(&s.hits, 1)
		w.Header().Set("Content-Type", "application/json")
		if strings.HasPrefix(r.URL.Path, "/v1/auth") {
			fmt.Fprint(w, `{"auth":{"client_token":"stk-token"}}`)
			return
		}
		fmt.Fprintf(w, `{"data":{"data":{"password":%q},"metadata":{"version":1}},"lease_duration":0}`, value)
	})
	srv := &http.Server{Handler: h}
	go func() { _ = srv.Serve(ln) }()
	t.Cleanup(func() { _ = srv.Close() })
	port := ln.Addr().(*net.TCPAddr).Port
	return s, fmt.Sprintf("http://%s:%d", stkLocalHost(), port)
}

var stkRegistryConfig = []byte(`{"architecture":"amd64","os":"linux","config":{"Entrypoint":["/app-entry"],"Cmd":["serve"]},"rootfs":{"type":"layers","diff_ids":[]}}`)

// stkRegistry is a minimal OCI distribution endpoint serving one image.
func stkRegistry(t *testing.T, secure bool) (*stkServer, string) {
	t.Helper()
	sum := sha256.Sum256(stkRegistryConfig)
	configDigest := "sha256:" + hex.EncodeToString(sum[:])
	manifest := fmt.Sprintf(`{"schemaVersion":2,"mediaType":"application/vnd.docker.distribution.manifest.v2+json","config":{"mediaType":"application/vnd.docker.container.image.v1+json","size":%d,"digest":%q},"layers":[]}`, len(stkRegistryConfig), configDigest)
	msum := sha256.Sum256([]byte(manifest))
	manifestDigest := "sha256:" + hex.EncodeToString(msum[:])

	s := stkServe(t, http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		switch {
		case r.URL.Path == "/v2" || r.URL.Path == "/v2/":
			w.WriteHeader(http.StatusOK)
			fmt.Fprint(w, "{}")
		case strings.Contains(r.URL.Path, "/manifests/"):
			w.Header().Set("Content-Type", "application/vnd.docker.distribution.manifest.v2+json")
			w.Header().Set("Docker-Content-Digest", manifestDigest)
			w.WriteHeader(http.StatusOK)
			fmt.Fprint(w, manifest)
		case strings.Contains(r.URL.Path, "/blobs/"):
			w.WriteHeader(http.StatusOK)
			_, _ = w.Write(stkRegistryConfig)
		default:
			w.WriteHeader(http.StatusNotFound)
		}
	}), secure)
	return s, s.host() + "/team/app:1.0"
}

// stkTenantClient is a clientset holding the tenant's default service account.
func stkTenantClient(t *testing.T) *fake.Clientset {
	t.Helper()
	return fake.NewClientset(
		&corev1.ServiceAccount{
			ObjectMeta: metav1.ObjectMeta{Name: "default", Namespace: stkNamespace},
			Secrets:    []corev1.ObjectReference{{Name: "default-token"}},
		},
		&corev1.Secret{
			ObjectMeta: metav1.ObjectMeta{Name: "default-token", Namespace: stkNamespace},
			Data:       map[string][]byte{"token": []byte("stk-sa-token")},
			Type:       corev1.SecretTypeServiceAccountToken,
		},
	)
}

// stkTokenMints counts service-account token creations recorded by a clientset.
func stkTokenMints(cs *fake.Clientset) int {
	n := 0
	for _, a := range cs.Actions() {
		if a.GetVerb() == "create" && a.GetResource().Resource == "serviceaccounts" && a.GetSubresource() == "token" {
			n++
		}
	}
	return n
}

// stkTokenReactor lets the token-mint path complete without a real API server.
func stkTokenReactor(cs *fake.Clientset) {
	cs.PrependReactor("create", "serviceaccounts", func(action k8stesting.Action) (bool, runtime.Object, error) {
		if action.GetSubresource() != "token" {
			return false, nil, nil
		}
		out := &authenticationv1.TokenRequest{}
		out.Status.Token = "stk-minted-token"
		return true, out, nil
	})
}

func stkSecretConfigMap(annotations map[string]string) *corev1.ConfigMap {
	return &corev1.ConfigMap{
		ObjectMeta: metav1.ObjectMeta{Name: "tenant-config", Namespace: stkNamespace, Annotations: annotations},
		Data:       map[string]string{"DB_PASSWORD": "vault:secret/data/team/app#password"},
	}
}

func stkVaultPod(annotations map[string]string, image string) *corev1.Pod {
	return &corev1.Pod{
		ObjectMeta: metav1.ObjectMeta{Name: "tenant-pod", Namespace: stkNamespace, Annotations: annotations},
		Spec: corev1.PodSpec{
			Containers: []corev1.Container{{
				Name:  "app",
				Image: image,
				Env:   []corev1.EnvVar{{Name: "DB_PASSWORD", Value: "vault:secret/data/team/app#password"}},
			}},
		},
	}
}
