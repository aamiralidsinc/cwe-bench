package vtesting

import "testing"

// A server's human-readable description is also exposed as generated data.
// Text containing a backslash before a quote must not become code there.
func TestSec_ServerDescriptionConstantBreakout(t *testing.T) {
	spec := baseSpec()
	spec["servers"] = []any{map[string]any{
		"url":         "https://api.example.com/v1",
		"description": "primary endpoint\\\"; var " + injectSentinel + " = 1; //",
	}}
	assertNoInjection(t, spec, serverURLs())
}
