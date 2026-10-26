// Security tests: a content body that the site would publish without markup
// conversion must be refused unless the site owner allows its format.
//
// Each test drives a real site build and asserts a non-zero result with none of
// the body published. They fail on the vulnerable tree and pass on a correct
// fix.

package vtesting

import "testing"

// A content file whose body is raw HTML is not published verbatim by default.
func TestSec_HTMLFilePageRefused(t *testing.T) {
	const marker = "hugods-sec-htmlfile"
	files := map[string]string{
		"hugo.toml":           baseConfig,
		"content/page.html":   "---\ntitle: Untrusted\n---\n" + rawBody(marker) + "\n",
		"layouts/home.html":   "home",
		"layouts/single.html": "{{ .Content }}",
	}
	assertRefused(t, files, marker)
}

// The same rule holds for the other HTML file suffix.
func TestSec_HTMFilePageRefused(t *testing.T) {
	const marker = "hugods-sec-htmfile"
	files := map[string]string{
		"hugo.toml":           baseConfig,
		"content/page.htm":    "---\ntitle: Untrusted\n---\n" + rawBody(marker) + "\n",
		"layouts/home.html":   "home",
		"layouts/single.html": "{{ .Content }}",
	}
	assertRefused(t, files, marker)
}

// A body declared as HTML in the page's own configuration is not published
// verbatim by default, even though the file name says markdown.
func TestSec_FrontMatterMarkupRefused(t *testing.T) {
	const marker = "hugods-sec-markup"
	files := map[string]string{
		"hugo.toml":           baseConfig,
		"content/page.md":     "---\ntitle: Untrusted\nmarkup: html\n---\n" + rawBody(marker) + "\n",
		"layouts/home.html":   "home",
		"layouts/single.html": "{{ .Content }}",
	}
	assertRefused(t, files, marker)
}

// The default refusal survives a site that configures an unrelated security
// setting: the site owner has not allowed any content format.
func TestSec_DefaultDenyWithSecurityConfig(t *testing.T) {
	const marker = "hugods-sec-default"
	files := map[string]string{
		"hugo.toml": baseConfig + `
[security]
enableInlineShortcodes = true
`,
		"content/page.html":   "---\ntitle: Untrusted\n---\n" + rawBody(marker) + "\n",
		"layouts/home.html":   "home",
		"layouts/single.html": "{{ .Content }}",
	}
	assertRefused(t, files, marker)
}
