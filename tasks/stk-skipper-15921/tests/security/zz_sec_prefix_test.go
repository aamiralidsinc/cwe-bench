package opaguard

import (
	"testing"
)

func TestSec_BodyPrefixOversizedBodyDenied(t *testing.T) {
	registry, bundle := StartRegistry(t, PolicyDenyTruncated, guardMaxBody, guardReadBuf)
	url, recorder := StartRoute(t, registry, "opaAuthorizeRequestBodyPrefix", bundle)

	resp := Post(t, url, "application/x-www-form-urlencoded", FormBody(oversizedPrefix), true, nil)

	if resp.StatusCode < 400 {
		t.Fatalf("a body larger than the evaluated prefix was presented to the policy as complete: status %d", resp.StatusCode)
	}
	if hits := recorder.Hits(); hits != 0 {
		t.Fatalf("refused request reached the upstream %d time(s)", hits)
	}
}
