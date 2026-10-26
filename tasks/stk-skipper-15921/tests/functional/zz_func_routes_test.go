package opaguard

import (
	"io"
	"testing"
)

func TestFunc_ServeResponseUnderCapAllowed(t *testing.T) {
	registry, bundle := StartRegistry(t, PolicyServeResponse, guardMaxBody, guardReadBuf)
	url, _ := StartRoute(t, registry, "opaServeResponseWithReqBody", bundle)

	resp := Post(t, url, "application/x-www-form-urlencoded", FormBody(20), true, nil)

	if resp.StatusCode != 200 {
		t.Fatalf("an under-limit body was refused on the serve-response route: status %d", resp.StatusCode)
	}
	served, err := io.ReadAll(resp.Body)
	if err != nil {
		t.Fatalf("read served body: %v", err)
	}
	if string(served) != "served" {
		t.Fatalf("served body %q, want %q", served, "served")
	}
}

func TestFunc_BodyPrefixUnderPrefixAllowed(t *testing.T) {
	registry, bundle := StartRegistry(t, PolicyDenyTruncated, guardMaxBody, guardReadBuf)
	url, recorder := StartRoute(t, registry, "opaAuthorizeRequestBodyPrefix", bundle)

	body := FormBody(4096)
	resp := Post(t, url, "application/x-www-form-urlencoded", body, true, nil)

	if resp.StatusCode != 200 {
		t.Fatalf("a body within the evaluated prefix was refused: status %d", resp.StatusCode)
	}
	if hits := recorder.Hits(); hits != 1 {
		t.Fatalf("upstream called %d time(s), want 1", hits)
	}
	if got := recorder.Bodies()[0]; got != body {
		t.Fatalf("upstream received %d bytes, want %d", len(got), len(body))
	}
}

func TestFunc_BodyPrefixOverPrefixAllowedAndForwarded(t *testing.T) {
	registry, bundle := StartRegistry(t, PolicyAllowAll, guardMaxBody, guardReadBuf)
	url, recorder := StartRoute(t, registry, "opaAuthorizeRequestBodyPrefix", bundle)

	body := FormBody(oversizedPrefix)
	resp := Post(t, url, "application/x-www-form-urlencoded", body, true, nil)

	if resp.StatusCode != 200 {
		t.Fatalf("allowed request was refused: status %d", resp.StatusCode)
	}
	if hits := recorder.Hits(); hits != 1 {
		t.Fatalf("upstream called %d time(s), want 1", hits)
	}
	if got := recorder.Bodies()[0]; got != body {
		t.Fatalf("upstream received %d bytes, want %d", len(got), len(body))
	}
}
