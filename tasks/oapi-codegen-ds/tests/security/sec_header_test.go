package vtesting

import "testing"

// The document's own title and description are emitted in the generated file's
// preamble. Neither may break out of its comment.
func TestSec_DocumentTitleCommentBreakout(t *testing.T) {
	spec := baseSpec()
	spec["info"] = map[string]any{
		"title":   "Sample API\nvar " + injectSentinel + " = 1\n//",
		"version": "1.0.0",
	}
	assertNoInjection(t, spec, modelsOnly())
}

func TestSec_DocumentDescriptionCommentBreakout(t *testing.T) {
	spec := baseSpec()
	spec["info"] = map[string]any{
		"title":       "Sample API",
		"version":     "1.0.0",
		"description": "A sample\nvar " + injectSentinel + " = 1\n//",
	}
	assertNoInjection(t, spec, modelsOnly())
}
