package passtlsclientcert

import (
	"crypto/ecdsa"
	"crypto/elliptic"
	"crypto/rand"
	"crypto/tls"
	"crypto/x509"
	"crypto/x509/pkix"
	"io"
	"math/big"
	"net/http"
	"net/http/httptest"
	"strings"
	"sync"
	"testing"
	"time"

	"github.com/traefik/traefik/v2/pkg/config/dynamic"
)

// zzBackend records what reached the backend behind the middleware under test.
type zzBackend struct {
	mu      sync.Mutex
	reached bool
	header  http.Header
}

func (b *zzBackend) ServeHTTP(rw http.ResponseWriter, req *http.Request) {
	b.mu.Lock()
	b.reached = true
	b.header = req.Header.Clone()
	b.mu.Unlock()
	rw.WriteHeader(http.StatusOK)
}

func (b *zzBackend) seen() (bool, http.Header) {
	b.mu.Lock()
	defer b.mu.Unlock()
	return b.reached, b.header
}

// zzSameName reports whether a backend that ignores case and reads '_' as '-' sees both names as one header.
func zzSameName(a, b string) bool {
	return strings.EqualFold(strings.ReplaceAll(a, "_", "-"), strings.ReplaceAll(b, "_", "-"))
}

// zzValuesAs returns every value the backend received under any spelling of name.
func zzValuesAs(h http.Header, name string) []string {
	var out []string
	for key, values := range h {
		if zzSameName(key, name) {
			out = append(out, values...)
		}
	}
	return out
}

// zzClientCert creates a self-signed client certificate with the given common name.
func zzClientCert(t *testing.T, cn string) tls.Certificate {
	t.Helper()
	key, err := ecdsa.GenerateKey(elliptic.P256(), rand.Reader)
	if err != nil {
		t.Fatal(err)
	}
	tmpl := &x509.Certificate{
		SerialNumber: big.NewInt(4242),
		Subject:      pkix.Name{CommonName: cn},
		NotBefore:    time.Now().Add(-time.Hour),
		NotAfter:     time.Now().Add(time.Hour),
		KeyUsage:     x509.KeyUsageDigitalSignature,
		ExtKeyUsage:  []x509.ExtKeyUsage{x509.ExtKeyUsageClientAuth},
	}
	der, err := x509.CreateCertificate(rand.Reader, tmpl, tmpl, &key.PublicKey, key)
	if err != nil {
		t.Fatal(err)
	}
	leaf, err := x509.ParseCertificate(der)
	if err != nil {
		t.Fatal(err)
	}
	return tls.Certificate{Certificate: [][]byte{der}, PrivateKey: key, Leaf: leaf}
}

// zzServeTLS serves the middleware over HTTPS with mutual TLS, sends one request presenting cert with the
// given extra header lines (names exactly as given) and returns the status and the backend.
func zzServeTLS(t *testing.T, config dynamic.PassTLSClientCert, cert tls.Certificate, headers [][2]string) (int, *zzBackend) {
	t.Helper()
	backend := &zzBackend{}
	m, err := New(t.Context(), backend, config, "zz-passtls")
	if err != nil {
		t.Fatal(err)
	}
	srv := httptest.NewUnstartedServer(m)
	srv.TLS = &tls.Config{ClientAuth: tls.RequireAnyClientCert}
	srv.StartTLS()
	t.Cleanup(srv.Close)

	client := srv.Client()
	client.Transport.(*http.Transport).TLSClientConfig.Certificates = []tls.Certificate{cert}

	req, _ := http.NewRequest(http.MethodGet, srv.URL+"/", nil)
	for _, h := range headers {
		req.Header[h[0]] = append(req.Header[h[0]], h[1])
	}
	res, err := client.Do(req)
	if err != nil {
		t.Fatalf("request failed: %v", err)
	}
	_, _ = io.Copy(io.Discard, res.Body)
	_ = res.Body.Close()
	return res.StatusCode, backend
}

// zzAssertNotSpoofed: the attack is blocked when the request was refused with a client error before
// reaching the backend, or when the backend received no value carrying the marker under any spelling of name.
func zzAssertNotSpoofed(t *testing.T, status int, b *zzBackend, name, marker string) {
	t.Helper()
	reached, header := b.seen()
	if !reached {
		if status < 400 || status > 499 {
			t.Fatalf("request did not reach the backend but got status %d (want a client error)", status)
		}
		return
	}
	for _, v := range zzValuesAs(header, name) {
		if strings.Contains(v, marker) {
			t.Fatalf("backend received the client-supplied value %q as %s (headers: %v)", v, name, header)
		}
	}
}
