package vtesting

import (
	"strings"
	"testing"
)

// A plain specification with a server URL, a server description, a default and
// an enumerated variable must keep generating exactly what it does today.
func TestFunc_ServerURLConstantsAndTemplating(t *testing.T) {
	spec := baseSpec()
	spec["servers"] = []any{map[string]any{
		"url":         "https://{tenant}.example.com:{port}/api/v1",
		"description": `Primary "production" endpoint at C:\temp`,
		"variables": map[string]any{
			"tenant": map[string]any{"default": "acme"},
			"port":   map[string]any{"default": "8443", "enum": []any{"443", "8443"}},
		},
	}}
	out, err := generate(t, spec, serverURLs())
	if err != nil {
		t.Fatalf("ordinary specification was refused: %v", err)
	}
	f := parseGenerated(t, out)

	// URL templating: the constructor replaces each declared placeholder.
	for _, want := range []string{
		`strings.ReplaceAll(u, "{tenant}", string(tenant))`,
		`strings.ReplaceAll(u, "{port}", string(port))`,
		`if !port.Valid() {`,
		`u := "https://{tenant}.example.com:{port}/api/v1"`,
	} {
		if !strings.Contains(out, want) {
			t.Fatalf("generated constructor no longer contains %q:\n%s", want, out)
		}
	}

	// The human-readable description still appears, with its quotes and
	// backslashes intact, in the generated documentation.
	if !strings.Contains(out, `Primary "production" endpoint at C:\temp`) {
		t.Fatalf("server description was not preserved in the generated output:\n%s", out)
	}

	// The default and the enumerated values are still data with their exact
	// text.
	vals := constValues(t, f)
	for _, want := range []string{"acme", "443", "8443"} {
		if !containsValue(vals, want) {
			t.Fatalf("constant value %q is missing from the generated output:\n%s", want, out)
		}
	}
}

// A placeholder that has no variable entry still becomes a plain string
// parameter and is substituted.
func TestFunc_UndeclaredPlaceholder(t *testing.T) {
	spec := baseSpec()
	spec["servers"] = []any{map[string]any{
		"url": "https://api.example.com/{path}",
	}}
	out, err := generate(t, spec, serverURLs())
	if err != nil {
		t.Fatalf("ordinary specification was refused: %v", err)
	}
	parseGenerated(t, out)
	for _, want := range []string{
		`path string`,
		`strings.ReplaceAll(u, "{path}", path)`,
		`u := "https://api.example.com/{path}"`,
	} {
		if !strings.Contains(out, want) {
			t.Fatalf("generated constructor no longer contains %q:\n%s", want, out)
		}
	}
}

// A server with no variables remains a constant with the exact URL, and its
// description remains the exposed human-readable text.
func TestFunc_ServerURLConstantAndDescriptionConstant(t *testing.T) {
	spec := baseSpec()
	spec["servers"] = []any{map[string]any{
		"url":         "https://api.example.com/v1",
		"description": "Production endpoint",
	}}
	out, err := generate(t, spec, serverURLs())
	if err != nil {
		t.Fatalf("ordinary specification was refused: %v", err)
	}
	f := parseGenerated(t, out)
	vals := constValues(t, f)
	if !containsValue(vals, "https://api.example.com/v1") {
		t.Fatalf("server URL constant lost its exact value:\n%s", out)
	}
	if !containsValue(vals, "Production endpoint") {
		t.Fatalf("server description constant lost its exact value:\n%s", out)
	}
}

// A plain default with spaces keeps its exact text.
func TestFunc_ServerVariableDefaultWithSpaces(t *testing.T) {
	spec := baseSpec()
	spec["servers"] = []any{map[string]any{
		"url": "https://api.example.com/{region}",
		"variables": map[string]any{
			"region": map[string]any{"default": "eu west"},
		},
	}}
	out, err := generate(t, spec, serverURLs())
	if err != nil {
		t.Fatalf("ordinary specification was refused: %v", err)
	}
	f := parseGenerated(t, out)
	if !containsValue(constValues(t, f), "eu west") {
		t.Fatalf("default value was not preserved:\n%s", out)
	}
}

func containsValue(m map[string]string, want string) bool {
	for _, v := range m {
		if v == want {
			return true
		}
	}
	return false
}
