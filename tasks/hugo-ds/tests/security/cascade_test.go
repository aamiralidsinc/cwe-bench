// Security test for a content format chosen through shared page configuration
// rather than by the file itself.

package vtesting

import "testing"

// A section can set page configuration that applies to its descendants. A body
// whose format is chosen that way is refused by default, like any other.
func TestSec_CascadedMarkupRefused(t *testing.T) {
	const marker = "hugods-sec-cascade"
	files := map[string]string{
		"hugo.toml": baseConfig,
		"content/s/_index.md": `---
title: Section
cascade:
  markup: html
---
section body
`,
		"content/s/p.md":      "---\ntitle: Child\n---\n" + rawBody(marker) + "\n",
		"layouts/home.html":   "home",
		"layouts/list.html":   "list",
		"layouts/single.html": "{{ .Content }}",
	}
	assertRefused(t, files, marker)
}
