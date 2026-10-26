package vtesting

import (
	"encoding/json"
	"os"
	"path/filepath"
	"regexp"
	"strings"
	"testing"

	"github.com/prebid/openrtb/v20/openrtb2"
	"github.com/prebid/prebid-server/v4/adapters"
	"github.com/prebid/prebid-server/v4/config"
)

// Endpoint returns the configured endpoint template for a bidder, exactly as the
// server loads it from its bundled bidder configuration.
func Endpoint(t *testing.T, bidder string) string {
	t.Helper()
	path := filepath.Join("..", "static", "bidder-info", bidder+".yaml")
	raw, err := os.ReadFile(path)
	if err != nil {
		t.Fatalf("read bidder config %s: %v", path, err)
	}
	re := regexp.MustCompile(`(?m)^endpoint:\s*(.+?)\s*$`)
	m := re.FindStringSubmatch(string(raw))
	if m == nil {
		t.Fatalf("no endpoint in %s", path)
	}
	ep := strings.TrimSpace(m[1])
	ep = strings.Trim(ep, `"'`)
	return ep
}

// BidRequest builds the smallest request each adapter accepts, carrying the given
// bidder parameters at imp.ext.bidder (the location the exchange hands adapters).
func BidRequest(params map[string]interface{}) *openrtb2.BidRequest {
	w, h := int64(300), int64(250)
	ext, err := json.Marshal(map[string]interface{}{"bidder": params})
	if err != nil {
		panic(err)
	}
	return &openrtb2.BidRequest{
		ID:   "test-request",
		TMax: 1000,
		Site: &openrtb2.Site{
			Page:      "https://example.com/page",
			Publisher: &openrtb2.Publisher{ID: "pub-1"},
		},
		Device: &openrtb2.Device{UA: "test-agent", IP: "203.0.113.9", Language: "en"},
		Imp: []openrtb2.Imp{{
			ID:     "imp-1",
			Banner: &openrtb2.Banner{W: &w, H: &h},
			Ext:    ext,
		}},
	}
}

type Factory func(config.Adapter) (adapters.Bidder, error)

// Requests builds the adapter from its own configured endpoint and runs the
// outbound-request construction the exchange performs.
func Requests(t *testing.T, bidder string, factory Factory, params map[string]interface{}) ([]*adapters.RequestData, []error) {
	t.Helper()
	bid, err := factory(config.Adapter{Endpoint: Endpoint(t, bidder)})
	if err != nil {
		t.Fatalf("%s: build adapter: %v", bidder, err)
	}
	return bid.MakeRequests(BidRequest(params), &adapters.ExtraRequestInfo{})
}

// Uris returns the destinations of the constructed requests.
func Uris(reqs []*adapters.RequestData) []string {
	out := make([]string, 0, len(reqs))
	for _, r := range reqs {
		out = append(out, r.Uri)
	}
	return out
}

// Refused asserts the construction produced a client-visible error and no
// outbound request at all.
func Refused(t *testing.T, reqs []*adapters.RequestData, errs []error) {
	t.Helper()
	if len(reqs) != 0 {
		t.Fatalf("an outbound request was constructed for a refused value: %v", Uris(reqs))
	}
	if len(errs) == 0 {
		t.Fatalf("no refusal error was returned")
	}
}

// WantsUri asserts exactly one outbound request with the expected destination.
func WantsUri(t *testing.T, reqs []*adapters.RequestData, errs []error, want string) {
	t.Helper()
	if len(errs) != 0 {
		t.Fatalf("unexpected errors: %v", errs)
	}
	if len(reqs) != 1 {
		t.Fatalf("expected 1 outbound request, got %d", len(reqs))
	}
	if reqs[0].Uri != want {
		t.Fatalf("destination = %q, want %q", reqs[0].Uri, want)
	}
}

func copyParams(base map[string]interface{}, changes map[string]interface{}) map[string]interface{} {
	out := make(map[string]interface{}, len(base)+len(changes))
	for k, v := range base {
		out[k] = v
	}
	for k, v := range changes {
		out[k] = v
	}
	return out
}
