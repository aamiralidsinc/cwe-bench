package opaguard

import (
	"testing"
)

// The advisory's own route: a body-based authorization decision on a request
// whose body was cut at the configured maximum.
const (
	guardMaxBody = 32
	guardReadBuf = 16
)

func TestSec_ChunkedOversizedBodyDenied(t *testing.T) {
	registry, bundle := StartRegistry(t, PolicyDenyTruncated, guardMaxBody, guardReadBuf)
	url, recorder := StartRoute(t, registry, "opaAuthorizeRequestWithBody", bundle)

	resp := Post(t, url, "application/x-www-form-urlencoded", FormBody(2*guardMaxBody), true, nil)

	if resp.StatusCode < 400 {
		t.Fatalf("a body cut at the configured maximum was presented to the policy as complete: status %d", resp.StatusCode)
	}
	if hits := recorder.Hits(); hits != 0 {
		t.Fatalf("refused request reached the upstream %d time(s)", hits)
	}
}

func TestSec_UnknownContentTypeOversizedBodyDenied(t *testing.T) {
	registry, bundle := StartRegistry(t, PolicyDenyTruncated, guardMaxBody, guardReadBuf)
	url, recorder := StartRoute(t, registry, "opaAuthorizeRequestWithBody", bundle)

	// Declared length, but a media type the engine does not parse: nothing but
	// the completeness signal can tell the policy the body was cut.
	resp := Post(t, url, "application/octet-stream", FormBody(2*guardMaxBody), false, nil)

	if resp.StatusCode < 400 {
		t.Fatalf("cut body was presented to the policy as complete: status %d", resp.StatusCode)
	}
	if hits := recorder.Hits(); hits != 0 {
		t.Fatalf("refused request reached the upstream %d time(s)", hits)
	}
}

func TestSec_ClientSuppliedCompletenessIgnored(t *testing.T) {
	registry, bundle := StartRegistry(t, PolicyDenyTruncated, guardMaxBody, guardReadBuf)
	url, recorder := StartRoute(t, registry, "opaAuthorizeRequestWithBody", bundle)

	resp := Post(t, url, "application/x-www-form-urlencoded", FormBody(2*guardMaxBody), true,
		map[string]string{"x-envoy-auth-partial-body": "false"})

	if resp.StatusCode < 400 {
		t.Fatalf("a client-supplied completeness value overrode the real one: status %d", resp.StatusCode)
	}
	if hits := recorder.Hits(); hits != 0 {
		t.Fatalf("refused request reached the upstream %d time(s)", hits)
	}
}
