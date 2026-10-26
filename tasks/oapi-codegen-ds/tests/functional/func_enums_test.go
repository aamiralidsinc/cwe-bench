package vtesting

import (
	"strings"
	"testing"
)

// Ordinary string enum values keep their exact text and their validation
// method.
func TestFunc_SchemaEnumValues(t *testing.T) {
	spec := baseSpec()
	spec["components"] = map[string]any{
		"schemas": map[string]any{
			"Colour": map[string]any{
				"type": "string",
				"enum": []any{"alpha", "beta value", "gamma"},
			},
		},
	}
	out, err := generate(t, spec, modelsOnly())
	if err != nil {
		t.Fatalf("ordinary specification was refused: %v", err)
	}
	f := parseGenerated(t, out)
	vals := constValues(t, f)
	for _, want := range []string{"alpha", "beta value", "gamma"} {
		if !containsValue(vals, want) {
			t.Fatalf("enum value %q is missing from the generated output:\n%s", want, out)
		}
	}
	if !strings.Contains(out, "func (e Colour) Valid() bool {") {
		t.Fatalf("enum validation method is missing:\n%s", out)
	}
}

// Numeric enums are still emitted as bare numeric values.
func TestFunc_SchemaEnumNumeric(t *testing.T) {
	spec := baseSpec()
	spec["components"] = map[string]any{
		"schemas": map[string]any{
			"Level": map[string]any{
				"type": "integer",
				"enum": []any{1, 2, 3},
			},
		},
	}
	out, err := generate(t, spec, modelsOnly())
	if err != nil {
		t.Fatalf("ordinary specification was refused: %v", err)
	}
	parseGenerated(t, out)
	for _, want := range []string{"Level = 1", "Level = 2", "Level = 3"} {
		if !strings.Contains(out, want) {
			t.Fatalf("numeric enum constant %q is missing:\n%s", want, out)
		}
	}
}
