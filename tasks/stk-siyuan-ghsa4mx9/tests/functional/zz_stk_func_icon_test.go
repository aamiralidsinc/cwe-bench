package api

// Hidden functional suite for the dynamic-icon endpoint: ordinary text and the template form
// keep rendering, and text a caller supplies stays text in every mode.

import (
	"strings"
	"testing"

	"github.com/siyuan-note/siyuan/kernel/model"
)

func TestFunc_DynamicIconRendersPlainText(t *testing.T) {
	stkNewIconConfig(t)
	for _, content := range []string{"A", "你", "A&B"} {
		recorder := stkIconRequest(t, map[string]string{"type": "8", "content": content})
		body := stkAssertIconServed(t, recorder)
		text := stkIconText(t, body)
		if !contains(text, content) {
			t.Fatalf("text icon lost its content %q: rendered %q", content, text)
		}
		if found := stkActiveSVGContent(t, body); 0 < len(found) {
			t.Fatalf("plain text icon produced active content: %v", found)
		}
	}
}

func TestFunc_DynamicIconRendersTemplateOutput(t *testing.T) {
	f := stkNewIconFixture(t)
	recorder := stkIconRequest(t, map[string]string{
		"type":    "8",
		"content": `.action{.title}`,
		"id":      f.docID,
	})
	body := stkAssertIconServed(t, recorder)
	if text := stkIconText(t, body); !contains(text, stkDocTitle) {
		t.Fatalf("template icon lost its rendered text %q: rendered %q", stkDocTitle, text)
	}
}

// TestFunc_DynamicIconKeepsTextVisibleWhenSettingEnabled: the allow-SVG-script setting governs
// how stored documents are returned; a text icon still displays its text in that mode.
func TestFunc_DynamicIconKeepsTextVisibleWhenSettingEnabled(t *testing.T) {
	stkNewIconConfig(t)
	model.Conf.Editor.AllowSVGScript = true
	for _, content := range []string{"A", "你", "A&B"} {
		recorder := stkIconRequest(t, map[string]string{"type": "8", "content": content})
		body := stkAssertIconServed(t, recorder)
		if text := stkIconText(t, body); !contains(text, content) {
			t.Fatalf("text icon lost its content %q in setting-on mode: rendered %q", content, text)
		}
	}
}

func contains(haystack, needle string) bool {
	return strings.Contains(haystack, needle)
}
