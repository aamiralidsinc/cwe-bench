package modelcatalog

import (
	"context"
	"errors"
	"io"
	"net"
	"net/http"
	"net/http/httptest"
	"os"
	"strings"
	"syscall"
	"testing"
	"time"

	bifrost "github.com/maximhq/bifrost/core"
	"github.com/maximhq/bifrost/core/schemas"
)

func hiddenFuncLoaderReachedNetwork(err error) bool {
	if err == nil {
		return false
	}
	for _, target := range []error{
		io.EOF, io.ErrUnexpectedEOF,
		syscall.ENETUNREACH, syscall.EHOSTUNREACH, syscall.ECONNREFUSED,
		syscall.ECONNRESET, syscall.EPIPE, syscall.EACCES,
	} {
		if errors.Is(err, target) {
			return true
		}
	}
	var opErr *net.OpError
	if errors.As(err, &opErr) && opErr.Timeout() {
		return true
	}
	if os.IsTimeout(err) {
		return true
	}
	msg := strings.ToLower(err.Error())
	for _, marker := range []string{
		"network is unreachable", "no route to host", "connection refused",
		"connection reset", "broken pipe", "i/o timeout", "timed out", "empty reply",
		"non-2xx status", "eof",
	} {
		if strings.Contains(msg, marker) {
			return true
		}
	}
	return false
}

func hiddenFuncCatalog(t *testing.T, pricingURL, paramsURL string) *ModelCatalog {
	t.Helper()
	return &ModelCatalog{
		logger:             bifrost.NewDefaultLogger(schemas.LogLevelError),
		pricingURL:         pricingURL,
		modelParametersURL: paramsURL,
	}
}

func hiddenFuncLocalIPv4(t *testing.T) string {
	t.Helper()
	addrs, err := net.InterfaceAddrs()
	if err != nil {
		t.Fatalf("cannot list local addresses: %v", err)
	}
	for _, addr := range addrs {
		ipNet, ok := addr.(*net.IPNet)
		if !ok || ipNet.IP.IsLoopback() {
			continue
		}
		if v4 := ipNet.IP.To4(); v4 != nil {
			return v4.String()
		}
	}
	t.Fatal("the environment has no non-loopback IPv4 address to test with")
	return ""
}

func hiddenJSONServer(t *testing.T, addr string) *httptest.Server {
	t.Helper()
	srv := httptest.NewUnstartedServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		_, _ = w.Write([]byte(`{}`))
	}))
	ln, err := net.Listen("tcp", addr)
	if err != nil {
		t.Fatalf("cannot listen for the endpoint server: %v", err)
	}
	srv.Listener.Close()
	srv.Listener = ln
	srv.Start()
	t.Cleanup(srv.Close)
	return srv
}

// file:// endpoints keep working exactly as before.
func TestFunc_PricingFileURLWorks(t *testing.T) {
	path := t.TempDir() + "/pricing.json"
	if err := os.WriteFile(path, []byte(`{}`), 0o600); err != nil {
		t.Fatal(err)
	}
	mc := hiddenFuncCatalog(t, "file://"+path, "")
	ctx, cancel := context.WithTimeout(context.Background(), 20*time.Second)
	defer cancel()
	if _, err := mc.loadPricingFromURL(ctx); err != nil {
		t.Fatalf("file:// pricing must keep working: %v", err)
	}
}

func TestFunc_ModelParametersFileURLWorks(t *testing.T) {
	path := t.TempDir() + "/params.json"
	if err := os.WriteFile(path, []byte(`{}`), 0o600); err != nil {
		t.Fatal(err)
	}
	mc := hiddenFuncCatalog(t, "", "file://"+path)
	ctx, cancel := context.WithTimeout(context.Background(), 20*time.Second)
	defer cancel()
	if _, err := mc.loadModelParametersFromURL(ctx); err != nil {
		t.Fatalf("file:// model parameters must keep working: %v", err)
	}
}

// A locally hosted endpoint keeps working.
func TestFunc_PricingLoopbackWorks(t *testing.T) {
	srv := hiddenJSONServer(t, "127.0.0.1:0")
	mc := hiddenFuncCatalog(t, srv.URL, "")
	ctx, cancel := context.WithTimeout(context.Background(), 20*time.Second)
	defer cancel()
	if _, err := mc.loadPricingFromURL(ctx); err != nil {
		t.Fatalf("a loopback pricing endpoint must keep working: %v", err)
	}
}

// A private-LAN hosted endpoint keeps working (the opt-in the product documents).
func TestFunc_PricingPrivateLANWorks(t *testing.T) {
	ip := hiddenFuncLocalIPv4(t)
	srv := hiddenJSONServer(t, net.JoinHostPort(ip, "0"))
	mc := hiddenFuncCatalog(t, srv.URL, "")
	ctx, cancel := context.WithTimeout(context.Background(), 20*time.Second)
	defer cancel()
	if _, err := mc.loadPricingFromURL(ctx); err != nil {
		t.Fatalf("a private-LAN pricing endpoint must keep working: %v", err)
	}
}

// A public IPv4 carried inside a NAT64 form is still a public destination.
func TestFunc_PricingPublicWrappedRedirectAllowed(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		http.Redirect(w, r, "http://[64:ff9b::808:808]:51999/pricing.json", http.StatusFound)
	}))
	t.Cleanup(srv.Close)
	mc := hiddenFuncCatalog(t, srv.URL, "")
	ctx, cancel := context.WithTimeout(context.Background(), 25*time.Second)
	defer cancel()
	_, err := mc.loadPricingFromURL(ctx)
	if err == nil {
		return
	}
	if !hiddenFuncLoaderReachedNetwork(err) {
		t.Fatalf("a public redirect target was refused instead of fetched: %v", err)
	}
}
