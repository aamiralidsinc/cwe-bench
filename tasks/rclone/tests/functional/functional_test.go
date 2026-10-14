// Package functional holds the feature tests. They assert the serve s3 auth
// feature keeps working after a fix: a correctly authenticated client is
// served, and the server stays up and refuses bad credentials with a proper
// 403 rather than being disabled or refusing to start. A fix that over-blocks
// (e.g. refuses to run the auth-proxy mode, or tears the server down) fails
// these because the server is then not answering.
package functional

import (
	"net/http"
	"os"
	"strings"
	"testing"

	"rclones3harness/s3test"
)

var (
	static *s3test.Server
	proxy  *s3test.Server
)

func TestMain(m *testing.M) {
	s3test.PortBase = 38200
	if err := s3test.SetupData(); err != nil {
		panic(err)
	}
	code := m.Run()
	if static != nil {
		static.Stop()
	}
	if proxy != nil {
		proxy.Stop()
	}
	os.Exit(code)
}

func staticServer(t *testing.T) *s3test.Server {
	if static == nil {
		static = s3test.StartStaticServer(t)
	}
	return static
}

func proxyServer(t *testing.T) *s3test.Server {
	if proxy == nil {
		proxy = s3test.StartProxyServer(t)
	}
	return proxy
}

// 1. A correctly signed static-key client is served its bucket listing. This
//    is the positive case: serving must keep working.
func TestStaticKeyCorrectIsServed(t *testing.T) {
	s := staticServer(t)
	code, body := s3test.Do(s.Base, "GET", "/", s3test.StaticKey, s3test.StaticSecret, nil)
	if code != http.StatusOK {
		t.Fatalf("legitimate static-key request was not served: HTTP %d, body=%q", code, body)
	}
	if !strings.Contains(body, "ListAllMyBucketsResult") {
		t.Fatalf("expected a bucket listing, got: %q", body)
	}
}

// 2. A static-key client with the wrong secret is refused (auth still works).
func TestStaticKeyWrongSecretRefused(t *testing.T) {
	s := staticServer(t)
	code, body := s3test.Do(s.Base, "GET", "/", s3test.StaticKey, "wrong-secret", nil)
	if code != http.StatusForbidden {
		t.Fatalf("wrong static secret should be refused with 403, got HTTP %d, body=%q", code, body)
	}
}

// 3. Auth-proxy mode must stay available and refuse a known access key ID
//    signed with the wrong (non-empty) secret.
func TestProxyWrongSecretRefused(t *testing.T) {
	s := proxyServer(t)
	code, body := s3test.Do(s.Base, "GET", "/", s3test.AliceKey, "not-the-real-secret", nil)
	if code != http.StatusForbidden {
		t.Fatalf("wrong proxy secret should be refused with 403, got HTTP %d, body=%q", code, body)
	}
}

// 4. Auth-proxy mode refuses a request with no credentials at all: the server
//    must answer with a 4xx client error (not serve it, and not be down).
func TestProxyNoAuthRefused(t *testing.T) {
	s := proxyServer(t)
	code, body := s3test.DoNoAuth(s.Base, "GET", "/")
	if code < 400 || code >= 500 {
		t.Fatalf("unauthenticated request should be refused with a 4xx error, got HTTP %d, body=%q", code, body)
	}
	if strings.Contains(body, "ListAllMyBucketsResult") {
		t.Fatalf("unauthenticated request was served a bucket listing: %q", body)
	}
}

// 5. Auth-proxy mode refuses an access key ID the proxy does not know.
func TestProxyUnknownKeyRefused(t *testing.T) {
	s := proxyServer(t)
	code, body := s3test.Do(s.Base, "GET", "/", s3test.UnknownKey, "some-secret", nil)
	if code != http.StatusForbidden {
		t.Fatalf("unknown access key ID should be refused with 403, got HTTP %d, body=%q", code, body)
	}
}
