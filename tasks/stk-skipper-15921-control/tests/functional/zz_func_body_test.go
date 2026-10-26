package opaguard

import (
	"testing"
)

func TestFunc_UnderCapChunkedBodyAllowed(t *testing.T) {
	registry, bundle := StartRegistry(t, PolicyDenyTruncated, guardMaxBody, guardReadBuf)
	url, recorder := StartRoute(t, registry, "opaAuthorizeRequestWithBody", bundle)

	body := FormBody(20)
	resp := Post(t, url, "application/x-www-form-urlencoded", body, true, nil)

	if resp.StatusCode != 200 {
		t.Fatalf("an under-limit streamed body was refused: status %d", resp.StatusCode)
	}
	if hits := recorder.Hits(); hits != 1 {
		t.Fatalf("upstream called %d time(s), want 1", hits)
	}
	if got := recorder.Bodies()[0]; got != body {
		t.Fatalf("upstream received %q, want %q", got, body)
	}
}

func TestFunc_UnderCapKnownLengthAllowed(t *testing.T) {
	registry, bundle := StartRegistry(t, PolicyDenyTruncated, guardMaxBody, guardReadBuf)
	url, recorder := StartRoute(t, registry, "opaAuthorizeRequestWithBody", bundle)

	body := FormBody(20)
	resp := Post(t, url, "application/x-www-form-urlencoded", body, false, nil)

	if resp.StatusCode != 200 {
		t.Fatalf("an under-limit body was refused: status %d", resp.StatusCode)
	}
	if hits := recorder.Hits(); hits != 1 {
		t.Fatalf("upstream called %d time(s), want 1", hits)
	}
	if got := recorder.Bodies()[0]; got != body {
		t.Fatalf("upstream received %q, want %q", got, body)
	}
}

func TestFunc_EmptyBodyAllowed(t *testing.T) {
	registry, bundle := StartRegistry(t, PolicyDenyTruncated, guardMaxBody, guardReadBuf)
	url, recorder := StartRoute(t, registry, "opaAuthorizeRequestWithBody", bundle)

	resp := Post(t, url, "application/x-www-form-urlencoded", "", false, nil)

	if resp.StatusCode != 200 {
		t.Fatalf("an empty body was refused: status %d", resp.StatusCode)
	}
	if hits := recorder.Hits(); hits != 1 {
		t.Fatalf("upstream called %d time(s), want 1", hits)
	}
}

// A body of exactly the configured maximum is not over the limit. A policy
// that does not consult the completeness signal must still let it through and
// the upstream must still receive it in full.
func TestFunc_ExactCapBodyAllowedAndForwarded(t *testing.T) {
	registry, bundle := StartRegistry(t, PolicyAllowAll, guardMaxBody, guardReadBuf)
	url, recorder := StartRoute(t, registry, "opaAuthorizeRequestWithBody", bundle)

	body := FormBody(guardMaxBody)
	resp := Post(t, url, "application/x-www-form-urlencoded", body, false, nil)

	if resp.StatusCode != 200 {
		t.Fatalf("a body of exactly the configured maximum was refused: status %d", resp.StatusCode)
	}
	if hits := recorder.Hits(); hits != 1 {
		t.Fatalf("upstream called %d time(s), want 1", hits)
	}
	if got := recorder.Bodies()[0]; got != body {
		t.Fatalf("upstream received %d bytes, want %d", len(got), len(body))
	}
}

// Even when the policy allows a request whose body was cut, the upstream must
// receive the whole body, not the prefix the policy was shown.
func TestFunc_TruncatedBodyStillForwardedWhenAllowed(t *testing.T) {
	registry, bundle := StartRegistry(t, PolicyAllowAll, guardMaxBody, guardReadBuf)
	url, recorder := StartRoute(t, registry, "opaAuthorizeRequestWithBody", bundle)

	body := FormBody(2 * guardMaxBody)
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
