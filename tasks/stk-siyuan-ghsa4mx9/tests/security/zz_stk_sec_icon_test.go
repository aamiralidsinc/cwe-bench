package api

// Hidden security suite for the dynamic-icon endpoint. The endpoint is reachable without an
// account; whatever a caller puts in the text value must never come back as executable markup.

import (
	"testing"

	"github.com/siyuan-note/siyuan/kernel/model"
)

func TestSec_DynamicIconDropsEventHandlerAttribute(t *testing.T) {
	stkNewIconConfig(t)
	recorder := stkIconRequest(t, map[string]string{
		"type":    "8",
		"content": `</text><image href="x" onerror="alert(1)"/><text>`,
	})
	stkAssertNeutralised(t, recorder)
}

func TestSec_DynamicIconDropsScriptHref(t *testing.T) {
	stkNewIconConfig(t)
	recorder := stkIconRequest(t, map[string]string{
		"type":    "8",
		"content": `</text><a href="javascript:alert(1)">click</a><text>`,
	})
	stkAssertNeutralised(t, recorder)
}

func TestSec_DynamicIconDropsMarkupDataHref(t *testing.T) {
	stkNewIconConfig(t)
	recorder := stkIconRequest(t, map[string]string{
		"type": "8",
		"content": `</text>` +
			`<a href="data:text/xml,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20onload%3D%22alert(1)%22%2F%3E">one</a>` +
			`<a href="data:application/xml,%3Csvg%2F%3E">two</a><text>`,
	})
	stkAssertNeutralised(t, recorder)
}

func TestSec_DynamicIconDropsActiveElements(t *testing.T) {
	stkNewIconConfig(t)
	recorder := stkIconRequest(t, map[string]string{
		"type": "8",
		"content": `</text><iframe src="x"></iframe><object data="x"></object><embed src="x"/>` +
			`<foreignObject><body xmlns="http://www.w3.org/1999/xhtml"><img src="x" onerror="alert(1)"></body></foreignObject><text>`,
	})
	stkAssertNeutralised(t, recorder)
}

func TestSec_DynamicIconDropsPrefixedScriptElement(t *testing.T) {
	stkNewIconConfig(t)
	recorder := stkIconRequest(t, map[string]string{
		"type":    "8",
		"content": `</text><svg xmlns:svg="http://www.w3.org/2000/svg"><svg:script>alert(1)</svg:script></svg><text>`,
	})
	stkAssertNeutralised(t, recorder)
}

// TestSec_DynamicIconNeutralisesCallerTextWhenSettingEnabled: the allow-SVG-script setting
// governs how stored documents are returned, not text a caller supplies to the icon API, so
// caller text stays content in that mode too.
func TestSec_DynamicIconNeutralisesCallerTextWhenSettingEnabled(t *testing.T) {
	stkNewIconConfig(t)
	model.Conf.Editor.AllowSVGScript = true
	recorder := stkIconRequest(t, map[string]string{
		"type":    "8",
		"content": `</text><script>alert(1)</script><text>`,
	})
	stkAssertNeutralised(t, recorder)
}
