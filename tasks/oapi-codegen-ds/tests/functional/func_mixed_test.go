package vtesting

import (
	"strings"
	"testing"
)

// A realistic document still generates in full: models, an enum, a client and
// server-URL helpers.
func TestFunc_FullDocumentGeneration(t *testing.T) {
	spec := map[string]any{
		"openapi": "3.0.3",
		"info":    map[string]any{"title": "Pets", "version": "1.0.0", "description": "Pet store"},
		"servers": []any{map[string]any{
			"url":         "https://api.example.com/{version}",
			"description": "Public endpoint",
			"variables":   map[string]any{"version": map[string]any{"default": "v1", "enum": []any{"v1", "v2"}}},
		}},
		"paths": map[string]any{
			"/pets": map[string]any{
				"get": map[string]any{
					"operationId": "ListPets",
					"responses": map[string]any{
						"200": map[string]any{
							"description": "ok",
							"content": map[string]any{
								"application/json": map[string]any{"schema": map[string]any{
									"type": "array",
									"items": map[string]any{"$ref": "#/components/schemas/Pet"},
								}},
							},
						},
					},
				},
			},
		},
		"components": map[string]any{
			"schemas": map[string]any{
				"Pet": map[string]any{
					"type": "object",
					"properties": map[string]any{
						"name": map[string]any{"type": "string"},
						"kind": map[string]any{"type": "string", "enum": []any{"cat", "dog"}},
					},
				},
			},
		},
	}
	opts := serverURLs()
	opts.Generate.Client = true
	out, err := generate(t, spec, opts)
	if err != nil {
		t.Fatalf("realistic specification was refused: %v", err)
	}
	parseGenerated(t, out)
	for _, want := range []string{"type Pet struct", "func (e PetKind) Valid() bool", "type Client struct", "func NewClient("} {
		if !strings.Contains(out, want) {
			t.Fatalf("realistic document lost %q:\n%s", want, out)
		}
	}
}
