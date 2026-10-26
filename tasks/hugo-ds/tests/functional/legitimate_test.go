// Functional tests: legitimate builds keep working exactly as they do today.
// They pass on both the vulnerable and the fixed tree.

package vtesting

import (
	"fmt"
	"strings"
	"testing"
)

// An ordinary markdown page is converted, as always.
func TestFunc_MarkdownPageRenders(t *testing.T) {
	files := map[string]string{
		"hugo.toml":           baseConfig,
		"content/page.md":     "---\ntitle: Hello\n---\n**bold**\n",
		"layouts/home.html":   "home",
		"layouts/single.html": "{{ .Content }}",
	}
	res := assertBuilds(t, files)
	assertPublished(t, res, "page/index.html", "<strong>bold</strong>")
}

// A site owner who lists content formats under [security] allowContent gets the
// HTML body published exactly as before.
func TestFunc_AllowedHTMLPageRenders(t *testing.T) {
	const body = "<p>allowed-html-body</p>"
	files := map[string]string{
		"hugo.toml": baseConfig + `
[security]
allowContent = ['.*']
`,
		"content/page.html":   "---\ntitle: Allowed\n---\n" + body + "\n",
		"layouts/home.html":   "home",
		"layouts/single.html": "{{ .Content }}",
	}
	res := assertBuilds(t, files)
	assertPublished(t, res, "page/index.html", body)
}

// The same allowance restores a body declared with markup in front matter.
func TestFunc_AllowedFrontMatterMarkupRenders(t *testing.T) {
	const body = "<p>allowed-markup-body</p>"
	files := map[string]string{
		"hugo.toml": baseConfig + `
[security]
allowContent = ['.*']
`,
		"content/page.md":     "---\ntitle: Allowed\nmarkup: html\n---\n" + body + "\n",
		"layouts/home.html":   "home",
		"layouts/single.html": "{{ .Content }}",
	}
	res := assertBuilds(t, files)
	assertPublished(t, res, "page/index.html", body)
}

// The allowance also restores a site-declared content format whose subtype is
// HTML.
func TestFunc_AllowedCustomHTMLMediaTypeRenders(t *testing.T) {
	const body = "<p>allowed-custom-html-body</p>"
	files := map[string]string{
		"hugo.toml": customHTMLConfig + `
[security]
allowContent = ['.*']
`,
		"content/page.ahtml":  "---\ntitle: Allowed\n---\n" + body + "\n",
		"layouts/home.html":   "home",
		"layouts/single.html": "{{ .Content }}",
	}
	res := assertBuilds(t, files)
	assertPublished(t, res, "page/index.html", body)
}

// The allowance restores an HTML resource added by a content adapter.
func TestFunc_AllowedAdapterResourcePublishes(t *testing.T) {
	const body = "<p>allowed-resource-body</p>"
	files := map[string]string{
		"hugo.toml": baseConfig + `
[security]
allowContent = ['.*']
`,
		"content/docs/_content.gotmpl": `{{ .AddPage (dict "path" "p1" "title" "P1" "content" (dict "value" "hello" "mediaType" "text/markdown")) }}` +
			"\n" + `{{ .AddResource (dict "path" "p1/pic.html" "content" (dict "value" "` + body + `" "mediaType" "text/html")) }}` + "\n",
		"layouts/home.html":   "home",
		"layouts/list.html":   "list",
		"layouts/single.html": "{{ .Content }}{{ range .Resources }}LINK[{{ .RelPermalink }}]{{ end }}",
	}
	res := assertBuilds(t, files)
	assertPublished(t, res, "docs/p1/pic.html", body)
}

// The allowance restores a body whose format was chosen by shared page
// configuration.
func TestFunc_AllowedCascadedMarkupRenders(t *testing.T) {
	const body = "<p>allowed-cascade-body</p>"
	files := map[string]string{
		"hugo.toml": baseConfig + `
[security]
allowContent = ['.*']
`,
		"content/s/_index.md": `---
title: Section
cascade:
  markup: html
---
section body
`,
		"content/s/p.md":      "---\ntitle: Child\n---\n" + body + "\n",
		"layouts/home.html":   "home",
		"layouts/list.html":   "list",
		"layouts/single.html": "{{ .Content }}",
	}
	res := assertBuilds(t, files)
	assertPublished(t, res, "s/p/index.html", body)
}

// Content that is not raw HTML keeps building and publishing without any
// allowance: a plain text resource added by a content adapter.
func TestFunc_AdapterPlainResourcePublishes(t *testing.T) {
	const body = "plain-resource-body"
	files := map[string]string{
		"hugo.toml": baseConfig,
		"content/docs/_content.gotmpl": `{{ .AddPage (dict "path" "p1" "title" "P1" "content" (dict "value" "hello" "mediaType" "text/markdown")) }}` +
			"\n" + `{{ .AddResource (dict "path" "p1/data.txt" "content" (dict "value" "` + body + `" "mediaType" "text/plain")) }}` + "\n",
		"layouts/home.html":   "home",
		"layouts/list.html":   "list",
		"layouts/single.html": "{{ .Content }}{{ range .Resources }}LINK[{{ .RelPermalink }}]{{ end }}",
	}
	res := assertBuilds(t, files)
	assertPublished(t, res, "docs/p1/data.txt", body)
}

// An HTML resource produced by the site's own template is not a content body and
// keeps publishing.
func TestFunc_TemplateGeneratedHTMLResourcePublishes(t *testing.T) {
	const body = "<p>generated-by-template</p>"
	files := map[string]string{
		"hugo.toml":         baseConfig,
		"content/page.md":   "---\ntitle: P\n---\nbody\n",
		"layouts/home.html": "home",
		"layouts/single.html": `{{ $r := resources.FromString "generated.html" "` + body + `" }}GEN[{{ $r.RelPermalink }}]`,
	}
	res := assertBuilds(t, files)
	assertPublished(t, res, "generated.html", body)
}

// String rendering inside an allowed HTML page keeps mapping its markup to
// markdown, as it does today.
func TestFunc_RenderStringOnAllowedHTMLPage(t *testing.T) {
	files := map[string]string{
		"hugo.toml": baseConfig + `
[security]
allowContent = ['.*']
`,
		"content/page.html":   "---\ntitle: Allowed\n---\n<p>body</p>\n",
		"layouts/home.html":   "home",
		"layouts/single.html": `{{ .Content }}RS[{{ .RenderString "**bold**" }}]`,
	}
	res := assertBuilds(t, files)
	assertPublished(t, res, "page/index.html", "RS[<strong>bold</strong>]")
}

// A site with many ordinary pages, next to one allowed HTML body, keeps
// building.
func TestFunc_ManyPagesBuild(t *testing.T) {
	files := map[string]string{
		"hugo.toml": baseConfig + `
[security]
allowContent = ['.*']
`,
		"layouts/home.html":   "home",
		"layouts/single.html": "{{ .Content }}",
		"content/allowed.html": "---\ntitle: Allowed\n---\n<p>large-site-allowed</p>\n",
	}
	for i := 0; i < 60; i++ {
		files[fmt.Sprintf("content/p%02d.md", i)] = fmt.Sprintf("---\ntitle: Page %d\n---\n**page-%02d**\n", i, i)
	}
	res := assertBuilds(t, files)
	assertPublished(t, res, "p42/index.html", "<strong>page-42</strong>")
	assertPublished(t, res, "allowed/index.html", "large-site-allowed")
}

// Other security settings in the same configuration section keep working.
func TestFunc_OtherSecuritySettingsWork(t *testing.T) {
	files := map[string]string{
		"hugo.toml": baseConfig + `
[security]
enableInlineShortcodes = true
[security.exec]
allow = ['^go$']
`,
		"content/page.md":     "---\ntitle: P\n---\n*italic*\n",
		"layouts/home.html":   "home",
		"layouts/single.html": "{{ .Content }}",
	}
	res := assertBuilds(t, files)
	assertPublished(t, res, "page/index.html", "<em>italic</em>")
}

// The generated index pages of a site with no HTML content are unaffected.
func TestFunc_OrdinarySiteIndexesBuild(t *testing.T) {
	files := map[string]string{
		"hugo.toml":           baseConfig,
		"content/a.md":        "---\ntitle: A\n---\nalpha\n",
		"content/b.md":        "---\ntitle: B\n---\nbeta\n",
		"layouts/home.html":   "{{ range .Site.RegularPages }}P[{{ .Title }}]{{ end }}",
		"layouts/list.html":   "list",
		"layouts/single.html": "{{ .Content }}",
	}
	res := assertBuilds(t, files)
	body := res.pub["index.html"]
	if !strings.Contains(body, "P[A]") || !strings.Contains(body, "P[B]") {
		t.Fatalf("home page did not list the ordinary pages; got: %q", body)
	}
}
