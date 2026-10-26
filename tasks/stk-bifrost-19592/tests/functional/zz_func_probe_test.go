package handlers

import (
	"errors"
	"fmt"
	"io"
	"net"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"strings"
	"syscall"
	"testing"
)

func hiddenFuncProbeReachedNetwork(err error) bool {
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

func hiddenFuncProbeIPv4(t *testing.T) string {
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

func hiddenReachableServer(t *testing.T, addr string) *httptest.Server {
	t.Helper()
	srv := httptest.NewUnstartedServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		fmt.Fprint(w, "ok")
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

// A local endpoint is still reported reachable.
func TestFunc_ProbeLoopbackReachable(t *testing.T) {
	addr, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatalf("cannot start a local listener: %v", err)
	}
	port := addr.Addr().(*net.TCPAddr).Port
	addr.Close()
	srv := hiddenReachableServer(t, fmt.Sprintf("127.0.0.1:%d", port))
	if err := checkURLAccessibility(srv.URL); err != nil {
		t.Fatalf("a local endpoint must be reported reachable: %v", err)
	}
}

// A private-LAN endpoint is still reported reachable (the documented opt-in).
func TestFunc_ProbePrivateLANReachable(t *testing.T) {
	srv := hiddenReachableServer(t, net.JoinHostPort(hiddenFuncProbeIPv4(t), "0"))
	if err := checkURLAccessibility(srv.URL); err != nil {
		t.Fatalf("a private-LAN endpoint must be reported reachable: %v", err)
	}
}

// file:// endpoints keep working exactly as before.
func TestFunc_ProbeFileWorks(t *testing.T) {
	path := filepath.Join(t.TempDir(), "pricing.json")
	if err := os.WriteFile(path, []byte(`{}`), 0o600); err != nil {
		t.Fatal(err)
	}
	if err := checkURLAccessibility("file://" + path); err != nil {
		t.Fatalf("a local file endpoint must keep working: %v", err)
	}
}

// A public IPv4 carried inside a NAT64 form is still a public destination.
func TestFunc_ProbePublicWrappedRedirectAllowed(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		http.Redirect(w, r, "http://[64:ff9b::808:808]:51999/pricing.json", http.StatusFound)
	}))
	t.Cleanup(srv.Close)
	err := checkURLAccessibility(srv.URL + "/pricing.json")
	if err == nil {
		return
	}
	if !hiddenFuncProbeReachedNetwork(err) {
		t.Fatalf("a public redirect target was refused instead of probed: %v", err)
	}
}
