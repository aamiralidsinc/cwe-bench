package vtesting

import "testing"

func enumSpec(value string) map[string]any {
	spec := baseSpec()
	spec["components"] = map[string]any{
		"schemas": map[string]any{
			"Colour": map[string]any{
				"type": "string",
				"enum": []any{value},
			},
		},
	}
	return spec
}

// An allowed string value in a schema must not be able to terminate the
// generated constant block and declare code after it.
func TestSec_SchemaEnumValueBreakout(t *testing.T) {
	value := "red\"\n)\nvar " + injectSentinel + " = 1\nconst (\n_ = \""
	assertNoInjection(t, enumSpec(value), modelsOnly())
}
