package utils_test

import (
	"context"
	"errors"
	"io"
	"net"
	"os"
	"strings"
	"syscall"
	"testing"
	"time"

	providerUtils "github.com/maximhq/bifrost/core/providers/utils"
)

// hiddenFetchReachedNetwork reports whether the error shows that the request
// actually reached the network stack (a dial or protocol failure) instead of
// being refused before any connection was made.
func hiddenFetchReachedNetwork(err error) bool {
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

func hiddenFetchMustRefuse(t *testing.T, rawURL string) {
	t.Helper()
	ctx, cancel := context.WithTimeout(context.Background(), 25*time.Second)
	defer cancel()
	_, _, err := providerUtils.FetchAndEncodeURL(ctx, rawURL)
	if err == nil {
		t.Fatalf("%q was fetched; a resource URL must not reach this destination", rawURL)
	}
	if hiddenFetchReachedNetwork(err) {
		t.Fatalf("%q was not refused before connecting (reached the network: %v)", rawURL, err)
	}
}

func hiddenFetchMustAllow(t *testing.T, rawURL string) {
	t.Helper()
	ctx, cancel := context.WithTimeout(context.Background(), 25*time.Second)
	defer cancel()
	_, _, err := providerUtils.FetchAndEncodeURL(ctx, rawURL)
	if err == nil {
		// A successful fetch is also an allowed target; nothing more to check.
		return
	}
	if !hiddenFetchReachedNetwork(err) {
		t.Fatalf("%q is a public target but the fetch was refused instead of attempted: %v", rawURL, err)
	}
}

// The shared carrier-grade NAT range is reserved and must not be a fetch target.
func TestSec_FetchCGNATRange(t *testing.T) {
	hiddenFetchMustRefuse(t, "http://100.64.0.1:51999/asset.png")
}

func TestSec_FetchCGNATRangeHigh(t *testing.T) {
	hiddenFetchMustRefuse(t, "http://100.127.255.255:51999/asset.png")
}

// A private IPv4 dressed as a 6to4 address is still that private IPv4.
func TestSec_FetchSixToFourWrappedMetadata(t *testing.T) {
	hiddenFetchMustRefuse(t, "http://[2002:a9fe:a9fe::]:51999/asset.png")
}

// A private IPv4 dressed as a NAT64 address is still that private IPv4.
func TestSec_FetchNAT64WrappedMetadata(t *testing.T) {
	hiddenFetchMustRefuse(t, "http://[64:ff9b::a9fe:a9fe]:51999/asset.png")
}

func TestSec_FetchNAT64LocalUseWrappedMetadata(t *testing.T) {
	hiddenFetchMustRefuse(t, "http://[64:ff9b:1:a9fe:a9:fe00::]:51999/asset.png")
}

func TestSec_FetchSixToFourWrappedPrivate(t *testing.T) {
	hiddenFetchMustRefuse(t, "http://[2002:0a00:0001::]:51999/asset.png")
}

// Deprecated IPv6 site-local space is not a public destination.
func TestSec_FetchSiteLocal(t *testing.T) {
	hiddenFetchMustRefuse(t, "http://[fec0::1]:51999/asset.png")
}

// A name that resolves into the reserved range is refused the same way.
func TestSec_FetchResolvedCGNATName(t *testing.T) {
	hiddenFetchMustRefuse(t, "http://hidden-cgnat.test:51999/asset.png")
}

func TestSec_FetchResolvedSixToFourName(t *testing.T) {
	hiddenFetchMustRefuse(t, "http://hidden-six4-internal.test:51999/asset.png")
}
