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

func hiddenFuncFetchReachedNetwork(err error) bool {
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

func hiddenFuncFetchMustAttempt(t *testing.T, rawURL string) {
	t.Helper()
	ctx, cancel := context.WithTimeout(context.Background(), 25*time.Second)
	defer cancel()
	_, _, err := providerUtils.FetchAndEncodeURL(ctx, rawURL)
	if err == nil {
		return
	}
	if !hiddenFuncFetchReachedNetwork(err) {
		t.Fatalf("%q is a legitimate public target but was refused: %v", rawURL, err)
	}
}

// A public IPv4 carried inside a 6to4 address is still a public IPv4.
func TestFunc_FetchAllowsSixToFourPublic(t *testing.T) {
	hiddenFuncFetchMustAttempt(t, "http://[2002:0808:0808::]:51999/asset.png")
}

// A public IPv4 carried inside a NAT64 address is still a public IPv4.
func TestFunc_FetchAllowsNAT64Public(t *testing.T) {
	hiddenFuncFetchMustAttempt(t, "http://[64:ff9b::808:808]:51999/asset.png")
}

func TestFunc_FetchAllowsNAT64LocalUsePublic(t *testing.T) {
	hiddenFuncFetchMustAttempt(t, "http://[64:ff9b:1:808:808:0:0:0]:51999/asset.png")
}

// The address just outside the reserved shared range is a normal public address.
func TestFunc_FetchAllowsPublicNeighbourOfReservedRange(t *testing.T) {
	hiddenFuncFetchMustAttempt(t, "http://100.128.0.1:51999/asset.png")
}

func TestFunc_FetchAllowsOrdinaryPublic(t *testing.T) {
	hiddenFuncFetchMustAttempt(t, "http://8.8.8.8:51999/asset.png")
}

func TestFunc_FetchAllowsOrdinaryPublicIPv6(t *testing.T) {
	hiddenFuncFetchMustAttempt(t, "http://[2606:4700:4700::1111]:51999/asset.png")
}

// Unsupported schemes keep being refused for the reason they always were.
func TestFunc_FetchStillRejectsUnsupportedScheme(t *testing.T) {
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()
	_, _, err := providerUtils.FetchAndEncodeURL(ctx, "file:///etc/hostname")
	if err == nil {
		t.Fatal("a non-http scheme must still be refused")
	}
	if hiddenFuncFetchReachedNetwork(err) {
		t.Fatalf("a non-http scheme must be refused before connecting, got %v", err)
	}
}
