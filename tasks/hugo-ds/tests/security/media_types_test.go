// Security test for the format identity: a content format whose subtype is HTML
// is still emitted without conversion, whatever the rest of its media type name
// says.

package vtesting

import "testing"

const customHTMLConfig = baseConfig + `
[mediaTypes]
  [mediaTypes."application/html"]
    suffixes = ["ahtml"]
[contentTypes]
  "text/asciidoc" = {}
  "text/markdown" = {}
  "text/org" = {}
  "text/pandoc" = {}
  "text/rst" = {}
  "text/html" = {}
  "application/html" = {}
`

// A page in a content format that the site declares itself, whose subtype is
// HTML, is refused by default just like text/html.
func TestSec_CustomHTMLMediaTypeRefused(t *testing.T) {
	const marker = "hugods-sec-customtype"
	files := map[string]string{
		"hugo.toml":           customHTMLConfig,
		"content/page.ahtml":  "---\ntitle: Untrusted\n---\n" + rawBody(marker) + "\n",
		"layouts/home.html":   "home",
		"layouts/single.html": "{{ .Content }}",
	}
	assertRefused(t, files, marker)
}
