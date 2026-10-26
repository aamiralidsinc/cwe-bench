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

func hiddenLoaderReachedNetwork(err error) bool {
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

func hiddenCatalog(t *testing.T, pricingURL, paramsURL string) *ModelCatalog {
	t.Helper()
	return &ModelCatalog{
		logger:             bifrost.NewDefaultLogger(schemas.LogLevelError),
		pricingURL:         pricingURL,
		modelParametersURL: paramsURL,
	}
}

func hiddenRedirectServer(t *testing.T, target string) *httptest.Server {
	t.Helper()
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		http.Redirect(w, r, target, http.StatusFound)
	}))
	t.Cleanup(srv.Close)
	return srv
}

func hiddenMustRefuse(t *testing.T, err error, what string) {
	t.Helper()
	if err == nil {
		t.Fatalf("%s was fetched; this destination must not be reached", what)
	}
	if hiddenLoaderReachedNetwork(err) {
		t.Fatalf("%s was not refused before connecting (reached the network: %v)", what, err)
	}
}

// A destination reached after the first hop of a configured endpoint is
// checked too: the redirect target is an internal IPv4 carried in a NAT64 form.
func TestSec_PricingRedirectToWrappedInternal(t *testing.T) {
	srv := hiddenRedirectServer(t, "http://[64:ff9b::a9fe:a9fe]:51999/pricing.json")
	mc := hiddenCatalog(t, srv.URL, "")
	ctx, cancel := context.WithTimeout(context.Background(), 25*time.Second)
	defer cancel()
	_, err := mc.loadPricingFromURL(ctx)
	hiddenMustRefuse(t, err, "a pricing endpoint redirecting to an internal address")
}

func TestSec_ModelParametersRedirectToWrappedInternal(t *testing.T) {
	srv := hiddenRedirectServer(t, "http://[2002:0a00:0001::]:51999/params.json")
	mc := hiddenCatalog(t, "", srv.URL)
	ctx, cancel := context.WithTimeout(context.Background(), 25*time.Second)
	defer cancel()
	_, err := mc.loadModelParametersFromURL(ctx)
	hiddenMustRefuse(t, err, "a model-parameters endpoint redirecting to an internal address")
}

// The configured endpoint itself may already be such an address.
func TestSec_PricingConfiguredWrappedInternal(t *testing.T) {
	mc := hiddenCatalog(t, "http://[64:ff9b:1:a9fe:a9:fe00::]:51999/pricing.json", "")
	ctx, cancel := context.WithTimeout(context.Background(), 25*time.Second)
	defer cancel()
	_, err := mc.loadPricingFromURL(ctx)
	hiddenMustRefuse(t, err, "a pricing endpoint naming an internal address")
}

func TestSec_ModelParametersConfiguredWrappedInternal(t *testing.T) {
	mc := hiddenCatalog(t, "", "http://[fec0::1]:51999/params.json")
	ctx, cancel := context.WithTimeout(context.Background(), 25*time.Second)
	defer cancel()
	_, err := mc.loadModelParametersFromURL(ctx)
	hiddenMustRefuse(t, err, "a model-parameters endpoint naming an internal address")
}
