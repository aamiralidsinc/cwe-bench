package opaguard

import (
	"testing"
)

func TestSec_ServeResponseChunkedOversizedBodyDenied(t *testing.T) {
	registry, bundle := StartRegistry(t, PolicyServeResponse, guardMaxBody, guardReadBuf)
	url, _ := StartRoute(t, registry, "opaServeResponseWithReqBody", bundle)

	resp := Post(t, url, "application/x-www-form-urlencoded", FormBody(2*guardMaxBody), true, nil)

	if resp.StatusCode < 400 {
		t.Fatalf("cut body was evaluated as complete on the serve-response route: status %d", resp.StatusCode)
	}
}

func TestSec_ServeResponseUnknownContentTypeOversizedBodyDenied(t *testing.T) {
	registry, bundle := StartRegistry(t, PolicyServeResponse, guardMaxBody, guardReadBuf)
	url, _ := StartRoute(t, registry, "opaServeResponseWithReqBody", bundle)

	resp := Post(t, url, "application/octet-stream", FormBody(2*guardMaxBody), false, nil)

	if resp.StatusCode < 400 {
		t.Fatalf("cut body was evaluated as complete on the serve-response route: status %d", resp.StatusCode)
	}
}
