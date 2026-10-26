package handlers

import (
	"errors"
	"io"
	"net"
	"net/http"
	"net/http/httptest"
	"os"
	"strings"
	"syscall"
	"testing"
)

func hiddenProbeReachedNetwork(err error) bool {
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

func hiddenProbeMustRefuse(t *testing.T, rawURL string) {
	t.Helper()
	err := checkURLAccessibility(rawURL)
	if err == nil {
		t.Fatalf("%q was reported reachable; this destination must not be contacted", rawURL)
	}
	if hiddenProbeReachedNetwork(err) {
		t.Fatalf("%q was not refused before connecting (reached the network: %v)", rawURL, err)
	}
}

func TestSec_ProbeWrappedMetadata(t *testing.T) {
	hiddenProbeMustRefuse(t, "http://[64:ff9b::a9fe:a9fe]:51999/pricing.json")
}

func TestSec_ProbeWrappedPrivate(t *testing.T) {
	hiddenProbeMustRefuse(t, "http://[2002:0a00:0001::]:51999/pricing.json")
}

func TestSec_ProbeSiteLocal(t *testing.T) {
	hiddenProbeMustRefuse(t, "http://[fec0::1]:51999/pricing.json")
}

// A reachability check follows the endpoint; the destination it lands on is
// checked too.
func TestSec_ProbeRedirectToWrappedInternal(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		http.Redirect(w, r, "http://[64:ff9b:1:a9fe:a9:fe00::]:51999/pricing.json", http.StatusFound)
	}))
	t.Cleanup(srv.Close)
	hiddenProbeMustRefuse(t, srv.URL+"/pricing.json")
}
