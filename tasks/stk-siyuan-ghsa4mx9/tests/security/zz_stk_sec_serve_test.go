package server

// Hidden security suite: every route that hands a stored document to a client as an SVG image
// must deliver it without executable content. Each case goes through the real registered route
// with the role the route expects.

import (
	"net/http"
	"testing"

	"github.com/siyuan-note/siyuan/kernel/model"
)

func TestSec_EmojiSvgActiveContentNeutralised(t *testing.T) {
	f := stkNewSVGFixture(t)
	f.writeEmoji(t, "evil.svg", stkActiveSVGDocument)
	stkAssertNeutralised(t, f.request(model.RoleReader, http.MethodGet, "/emojis/stkpack/evil.svg"))
}

func TestSec_HistorySvgActiveContentNeutralised(t *testing.T) {
	f := stkNewSVGFixture(t)
	f.writeHistory(t, "20260304120000/snapshot.svg", stkActiveSVGDocument)
	stkAssertNeutralised(t, f.request(model.RoleAdministrator, http.MethodGet, "/history/20260304120000/snapshot.svg"))
}

func TestSec_RepoDiffSvgActiveContentNeutralised(t *testing.T) {
	f := stkNewSVGFixture(t)
	f.writeRepoDiff(t, "20260304120000/diff.svg", stkActiveSVGDocument)
	stkAssertNeutralised(t, f.request(model.RoleAdministrator, http.MethodGet, "/repo/diff/20260304120000/diff.svg"))
}

func TestSec_AssetSvgActiveContentNeutralised(t *testing.T) {
	f := stkNewSVGFixture(t)
	f.writeAsset(t, "evil.svg", stkActiveSVGDocument)
	stkAssertNeutralised(t, f.request(model.RoleReader, http.MethodGet, "/assets/evil.svg"))
}
