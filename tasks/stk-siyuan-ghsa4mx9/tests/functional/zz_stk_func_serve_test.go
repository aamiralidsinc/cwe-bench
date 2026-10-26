package server

// Hidden functional suite: documents that carry no executable content keep being delivered
// unchanged, files that are not images are untouched, and the documented "allow SVG scripts"
// setting keeps returning documents verbatim.

import (
	"net/http"
	"testing"

	"github.com/siyuan-note/siyuan/kernel/model"
)

func TestFunc_EmojiSvgKeepsNonExecutableContent(t *testing.T) {
	f := stkNewSVGFixture(t)
	f.writeEmoji(t, "legit.svg", stkLegitSVGDocument)
	stkAssertBodyContains(t, f.request(model.RoleReader, http.MethodGet, "/emojis/stkpack/legit.svg"),
		`href="https://example.com/page"`, `xlink:href="https://example.com/other"`,
		"STK_XLINK_MARKER", "STK_NS_MARKER", "data:image/png;base64,STKPNG", ".stk-cls{fill:red}", "STK_TEXT_MARKER")
}

func TestFunc_HistorySvgKeepsNonExecutableContent(t *testing.T) {
	f := stkNewSVGFixture(t)
	f.writeHistory(t, "20260304120000/legit.svg", stkLegitSVGDocument)
	stkAssertBodyContains(t, f.request(model.RoleAdministrator, http.MethodGet, "/history/20260304120000/legit.svg"),
		`href="https://example.com/page"`, `xlink:href="https://example.com/other"`,
		"STK_XLINK_MARKER", "STK_NS_MARKER", "data:image/png;base64,STKPNG", ".stk-cls{fill:red}", "STK_TEXT_MARKER")
}

func TestFunc_RepoDiffSvgKeepsNonExecutableContent(t *testing.T) {
	f := stkNewSVGFixture(t)
	f.writeRepoDiff(t, "20260304120000/legit.svg", stkLegitSVGDocument)
	stkAssertBodyContains(t, f.request(model.RoleAdministrator, http.MethodGet, "/repo/diff/20260304120000/legit.svg"),
		`href="https://example.com/page"`, `xlink:href="https://example.com/other"`,
		"STK_XLINK_MARKER", "STK_NS_MARKER", "data:image/png;base64,STKPNG", ".stk-cls{fill:red}", "STK_TEXT_MARKER")
}

func TestFunc_AssetSvgKeepsNonExecutableContent(t *testing.T) {
	f := stkNewSVGFixture(t)
	f.writeAsset(t, "legit.svg", stkLegitSVGDocument)
	stkAssertBodyContains(t, f.request(model.RoleReader, http.MethodGet, "/assets/legit.svg"),
		`href="https://example.com/page"`, `xlink:href="https://example.com/other"`,
		"STK_XLINK_MARKER", "STK_NS_MARKER", "data:image/png;base64,STKPNG", ".stk-cls{fill:red}", "STK_TEXT_MARKER")
}

func TestFunc_NonSvgFilesServedUnchanged(t *testing.T) {
	f := stkNewSVGFixture(t)
	f.writeEmoji(t, "note.png", "STK_EMOJI_PNG_BYTES")
	f.writeHistory(t, "20260304120000/note.txt", "STK_HISTORY_TEXT")
	f.writeRepoDiff(t, "20260304120000/note.json", `{"stk":"diff"}`)
	stkAssertBodyEquals(t, f.request(model.RoleReader, http.MethodGet, "/emojis/stkpack/note.png"), "STK_EMOJI_PNG_BYTES")
	stkAssertBodyEquals(t, f.request(model.RoleAdministrator, http.MethodGet, "/history/20260304120000/note.txt"), "STK_HISTORY_TEXT")
	stkAssertBodyEquals(t, f.request(model.RoleAdministrator, http.MethodGet, "/repo/diff/20260304120000/note.json"), `{"stk":"diff"}`)
}

func TestFunc_SvgScriptsServedWhenSettingEnabled(t *testing.T) {
	f := stkNewSVGFixture(t)
	f.writeEmoji(t, "scripted.svg", stkActiveSVGDocument)
	f.writeAsset(t, "scripted.svg", stkActiveSVGDocument)
	model.Conf.Editor.AllowSVGScript = true

	stkAssertBodyContains(t, f.request(model.RoleReader, http.MethodGet, "/emojis/stkpack/scripted.svg"),
		"<script>alert('script')</script>", "onload=")
	stkAssertBodyContains(t, f.request(model.RoleReader, http.MethodGet, "/assets/scripted.svg"),
		"<script>alert('script')</script>", "onload=")
}
