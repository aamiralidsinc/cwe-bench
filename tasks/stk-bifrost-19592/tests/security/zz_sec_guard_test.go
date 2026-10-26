package utils_test

import (
	"errors"
	"io"
	"net"
	"os"
	"strings"
	"syscall"
	"testing"
	"time"

	providerUtils "github.com/maximhq/bifrost/core/providers/utils"
	"github.com/valyala/fasthttp"
)

func hiddenGuardReachedNetwork(err error) bool {
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

func hiddenGuardMustRefuse(t *testing.T, addr string) {
	t.Helper()
	client := &fasthttp.Client{ReadTimeout: 3 * time.Second}
	providerUtils.ConfigureDialer(client, false)
	conn, err := client.Dial(addr)
	if conn != nil {
		_ = conn.Close()
	}
	if err == nil {
		t.Fatalf("%q was dialed; this destination must be refused before connecting", addr)
	}
	if hiddenGuardReachedNetwork(err) {
		t.Fatalf("%q was not refused before connecting (reached the network: %v)", addr, err)
	}
}

// A private IPv4 carried inside a 6to4 address must be treated as private at
// dial time for provider traffic.
func TestSec_GuardSixToFourWrappedPrivate(t *testing.T) {
	hiddenGuardMustRefuse(t, "[2002:0a00:0001::]:51999")
}

func TestSec_GuardNAT64WrappedMetadata(t *testing.T) {
	hiddenGuardMustRefuse(t, "[64:ff9b::a9fe:a9fe]:51999")
}

func TestSec_GuardNAT64LocalUseWrappedMetadata(t *testing.T) {
	hiddenGuardMustRefuse(t, "[64:ff9b:1:a9fe:a9:fe00::]:51999")
}

// Deprecated IPv6 site-local space is not a public destination.
func TestSec_GuardSiteLocal(t *testing.T) {
	hiddenGuardMustRefuse(t, "[fec0::1]:51999")
}
