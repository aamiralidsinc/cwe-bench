package vtesting

import "testing"

func responseTypeSpec(content map[string]any) map[string]any {
	spec := baseSpec()
	spec["paths"] = map[string]any{
		"/pets": map[string]any{
			"get": map[string]any{
				"operationId": "ListPets",
				"responses": map[string]any{
					"200": map[string]any{
						"description": "ok",
						"content":     content,
					},
				},
			},
		},
	}
	return spec
}

// A media type name from the specification is emitted into the generated
// client's response dispatch as a string literal. A backslash before a quote
// must not let it break out of that literal.
func TestSec_ResponseContentTypeQuote(t *testing.T) {
	schema := map[string]any{"schema": map[string]any{
		"type":       "object",
		"properties": map[string]any{"id": map[string]any{"type": "string"}},
	}}
	hostile := "application/vnd.b+json; x=\"\\\": var " + injectSentinel + " = 1 ; //\""
	spec := responseTypeSpec(map[string]any{
		"application/vnd.a+json": schema,
		hostile:                  schema,
	})
	assertNoInjection(t, spec, clientAndModels())
}
