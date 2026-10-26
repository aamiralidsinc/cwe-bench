package vtesting

import (
	"testing"
)

// A line break in the human-readable server description must not escape the
// generated documentation comment of a server URL that has no variables.
func TestSec_ServerURLDescriptionNewlineConstantForm(t *testing.T) {
	spec := baseSpec()
	spec["servers"] = []any{map[string]any{
		"url":         "https://api.example.com/v1",
		"description": "primary endpoint\nvar " + injectSentinel + " = 1\n//",
	}}
	assertNoInjection(t, spec, serverURLs())
}

// The same text in the variable-bearing form must not escape either.
func TestSec_ServerURLDescriptionNewlineFunctionForm(t *testing.T) {
	spec := baseSpec()
	spec["servers"] = []any{map[string]any{
		"url":         "https://{tenant}.example.com/v1",
		"description": "tenant endpoint\nvar " + injectSentinel + " = 1\n//",
		"variables": map[string]any{
			"tenant": map[string]any{"default": "acme"},
		},
	}}
	assertNoInjection(t, spec, serverURLs())
}

// A backslash immediately before a double quote must not defeat the escaping
// of a URL emitted as a string literal.
func TestSec_ServerURLQuoteConstantForm(t *testing.T) {
	spec := baseSpec()
	spec["servers"] = []any{map[string]any{
		"url": "https://api.example.com/v1\"; var " + injectSentinel + " = 1; var _ = \"",
	}}
	assertNoInjection(t, spec, serverURLs())
}

// The URL literal inside the variable-bearing constructor takes the same shape.
func TestSec_ServerURLQuoteFunctionForm(t *testing.T) {
	spec := baseSpec()
	spec["servers"] = []any{map[string]any{
		"url": "https://{tenant}.example.com/v1\"; var " + injectSentinel + " = 1; var _ = \"",
		"variables": map[string]any{
			"tenant": map[string]any{"default": "acme"},
		},
	}}
	assertNoInjection(t, spec, serverURLs())
}

// A default value for a plain (non-enumerated) server variable is emitted as a
// string literal too, and must not be able to break out of it.
func TestSec_ServerVariableDefaultQuote(t *testing.T) {
	spec := baseSpec()
	spec["servers"] = []any{map[string]any{
		"url": "https://api.example.com/{region}/v1",
		"variables": map[string]any{
			"region": map[string]any{"default": "eu\"; var " + injectSentinel + " = 1; var _ = \""},
		},
	}}
	assertNoInjection(t, spec, serverURLs())
}
