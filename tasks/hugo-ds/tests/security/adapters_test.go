// Security tests for bodies supplied through the content adapter, which are
// published by the site when a template links them.

package vtesting

import "testing"


// A page added by a content adapter with an HTML body is refused by default.
func TestSec_ContentAdapterPageRefused(t *testing.T) {
	const marker = "hugods-sec-adapterpage"
	files := map[string]string{
		"hugo.toml": baseConfig,
		"content/_content.gotmpl": `{{ .AddPage (dict "path" "p1" "title" "Untrusted" "content" (dict "value" "` +
			rawBody(marker) + `" "mediaType" "text/html")) }}` + "\n",
		"layouts/home.html":   "home",
		"layouts/list.html":   "list",
		"layouts/single.html": "{{ .Content }}",
	}
	assertRefused(t, files, marker)
}

// A resource added by a content adapter whose body is declared HTML is refused
// by default, and none of it is published.
func TestSec_AdapterResourceDeclaredHTMLRefused(t *testing.T) {
	const marker = "hugods-sec-resdeclared"
	files := map[string]string{
		"hugo.toml": baseConfig,
		"content/docs/_content.gotmpl": `{{ .AddPage (dict "path" "p1" "title" "P1" "content" (dict "value" "hello" "mediaType" "text/markdown")) }}` +
			"\n" + `{{ .AddResource (dict "path" "p1/pic.html" "content" (dict "value" "` + rawBody(marker) + `" "mediaType" "text/html")) }}` + "\n",
		"layouts/home.html":   "home",
		"layouts/list.html":   "list",
		"layouts/single.html": "{{ .Content }}{{ range .Resources }}LINK[{{ .RelPermalink }}]{{ end }}",
	}
	assertRefused(t, files, marker)
}

// The same resource shape without a declared media type: the format comes from
// the target path.
func TestSec_AdapterResourceHTMLSuffixRefused(t *testing.T) {
	const marker = "hugods-sec-ressuffix"
	files := map[string]string{
		"hugo.toml": baseConfig,
		"content/docs/_content.gotmpl": `{{ .AddPage (dict "path" "p1" "title" "P1" "content" (dict "value" "hello" "mediaType" "text/markdown")) }}` +
			"\n" + `{{ .AddResource (dict "path" "p1/pic.html" "content" (dict "value" "` + rawBody(marker) + `")) }}` + "\n",
		"layouts/home.html":   "home",
		"layouts/list.html":   "list",
		"layouts/single.html": "{{ .Content }}{{ range .Resources }}LINK[{{ .RelPermalink }}]{{ end }}",
	}
	assertRefused(t, files, marker)
}

// The other HTML suffix, again resolved from the target path.
func TestSec_AdapterResourceHTMSuffixRefused(t *testing.T) {
	const marker = "hugods-sec-reshtmsuffix"
	files := map[string]string{
		"hugo.toml": baseConfig,
		"content/docs/_content.gotmpl": `{{ .AddPage (dict "path" "p1" "title" "P1" "content" (dict "value" "hello" "mediaType" "text/markdown")) }}` +
			"\n" + `{{ .AddResource (dict "path" "p1/pic.htm" "content" (dict "value" "` + rawBody(marker) + `")) }}` + "\n",
		"layouts/home.html":   "home",
		"layouts/list.html":   "list",
		"layouts/single.html": "{{ .Content }}{{ range .Resources }}LINK[{{ .RelPermalink }}]{{ end }}",
	}
	assertRefused(t, files, marker)
}
