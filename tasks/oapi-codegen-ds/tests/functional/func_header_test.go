package vtesting

import (
	"strings"
	"testing"
)

// The document's title and description still appear in the generated file,
// with their ordinary punctuation intact.
func TestFunc_DocumentInfoPreserved(t *testing.T) {
	spec := baseSpec()
	spec["info"] = map[string]any{
		"title":       `Petstore "Public" API`,
		"version":     "1.0.0",
		"description": `A sample API at C:\docs for pet owners`,
	}
	out, err := generate(t, spec, modelsOnly())
	if err != nil {
		t.Fatalf("ordinary specification was refused: %v", err)
	}
	parseGenerated(t, out)
	if !strings.Contains(out, `Petstore "Public" API`) {
		t.Fatalf("document title was not preserved:\n%s", out)
	}
	if !strings.Contains(out, `A sample API at C:\docs for pet owners`) {
		t.Fatalf("document description was not preserved:\n%s", out)
	}
}
