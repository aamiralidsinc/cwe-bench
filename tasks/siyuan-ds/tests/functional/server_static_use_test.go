package server

import (
	"net/http"
	"strings"
	"testing"

	"github.com/siyuan-note/siyuan/kernel/model"
)

// Published pages must keep working, and the administrator keeps unrestricted
// access to everything.

func TestPubUsePublishedResourcesServedToReader(t *testing.T) {
	f := newPubServerFixture(t)
	assertServed(t, f.request(model.RoleReader, http.MethodGet, "/widgets/refpkg/"), "WIDGET_REF_MARKER")
	assertServed(t, f.request(model.RoleReader, http.MethodGet, "/emojis/refpack/a.png"), "EMOJI_REF_MARKER")
	assertServed(t, f.request(model.RoleReader, http.MethodGet, "/snippets/allowed.css"), "ALLOWED_SNIPPET_MARKER")
	assertServed(t, f.request(model.RoleReader, http.MethodGet, "/plugins/openpkg/index.js"), "PLUGIN_OPEN_MARKER")
}

func TestPubUseDirectoryRequestServesIndex(t *testing.T) {
	f := newPubServerFixture(t)
	assertServed(t, f.request(model.RoleReader, http.MethodGet, "/widgets/refpkg/"), "WIDGET_REF_MARKER")
}

func TestPubUseSymlinkedPackageDirectoryServed(t *testing.T) {
	f := newPubServerFixture(t)
	assertServed(t, f.request(model.RoleReader, http.MethodGet, "/widgets/sympkg/"), "WIDGET_SYMLINK_MARKER")
}

func TestPubUseShapedReferencesServedToReader(t *testing.T) {
	f := newPubServerFixture(t)
	// References written as an absolute loopback URL, an HTML block, an
	// HTML-escaped attribute value and a nested emoji directory all name a
	// resource the reader may receive.
	assertServed(t, f.request(model.RoleReader, http.MethodGet, "/widgets/locpkg/"), "WIDGET_LOCAL_MARKER")
	assertServed(t, f.request(model.RoleReader, http.MethodGet, "/widgets/htmlpkg/"), "WIDGET_HTML_MARKER")
	assertServed(t, f.request(model.RoleReader, http.MethodGet, "/emojis/refpack/d.png"), "EMOJI_ESCAPED_MARKER")
	assertServed(t, f.request(model.RoleReader, http.MethodGet, "/emojis/nestedpack/sub/f.png"), "EMOJI_NESTED_MARKER")
}

func TestPubUseSnippetTypeMatchServed(t *testing.T) {
	f := newPubServerFixture(t)
	assertServed(t, f.request(model.RoleReader, http.MethodGet, "/snippets/dual.js"), "DUAL_JS_MARKER")
	assertServed(t, f.request(model.RoleReader, http.MethodGet, "/snippet-preview?name=dual&type=js"), "DUAL_JS_MARKER")
}

func TestPubUseAdministratorKeepsStaticAccess(t *testing.T) {
	f := newPubServerFixture(t)
	admin := model.RoleAdministrator
	assertServed(t, f.request(admin, http.MethodGet, "/templates/tprivate.md"), "TEMPLATE_MARKER")
	assertServed(t, f.request(admin, http.MethodGet, "/export/artifact.txt"), "EXPORT_MARKER")
	assertServed(t, f.request(admin, http.MethodGet, "/export/temp/artifact2.txt"), "EXPORT_TEMP_MARKER")
	assertServed(t, f.request(admin, http.MethodGet, "/snippets/fallback.css"), "FALLBACK_SNIPPET_MARKER")
	assertServed(t, f.request(admin, http.MethodGet, "/snippets/hidden.js"), "HIDDEN_SNIPPET_MARKER")
	assertServed(t, f.request(admin, http.MethodGet, "/widgets/offpkg/"), "WIDGET_DISABLED_MARKER")
	assertServed(t, f.request(admin, http.MethodGet, "/widgets/hiddenrefpkg/"), "WIDGET_HIDDENREF_MARKER")
	assertServed(t, f.request(admin, http.MethodGet, "/emojis/refpack/b.png"), "EMOJI_UNREF_MARKER")
	assertServed(t, f.request(admin, http.MethodGet, "/emojis/nestedpack/h.png"), "EMOJI_HIDDENREF_MARKER")
	assertServed(t, f.request(admin, http.MethodGet, "/snippets/dual.css"), "DUAL_CSS_MARKER")
	assertServed(t, f.request(admin, http.MethodGet, "/plugins/hiddenpkg/index.js"), "PLUGIN_HIDDEN_MARKER")
}

func TestPubUsePreviewResolverServesPublishedResources(t *testing.T) {
	f := newPubServerFixture(t)
	assertServed(t, f.request(model.RoleReader, http.MethodGet, "/publish-preview/widgets/refpkg/main.js"), "WIDGET_REF_MARKER")
	assertServed(t, f.request(model.RoleReader, http.MethodGet, "/publish-preview/emojis/refpack/a.png"), "EMOJI_REF_MARKER")
	assertServed(t, f.request(model.RoleReader, http.MethodGet, "/publish-preview/snippets/allowed.css"), "ALLOWED_SNIPPET_MARKER")
	assertServed(t, f.request(model.RoleReader, http.MethodGet, "/publish-preview/plugins/openpkg/index.js"), "PLUGIN_OPEN_MARKER")
}

func TestPubUseSnippetPreviewServesEnabledSnippet(t *testing.T) {
	f := newPubServerFixture(t)
	assertServed(t, f.request(model.RoleReader, http.MethodGet, "/snippet-preview?name=allowed&type=css"), "ALLOWED_SNIPPET_MARKER")
}

func TestPubUseAdministratorKeepsPreviewAccess(t *testing.T) {
	f := newPubServerFixture(t)
	admin := model.RoleAdministrator
	assertServed(t, f.request(admin, http.MethodGet, "/publish-preview/templates/tprivate.md"), "TEMPLATE_MARKER")
	assertServed(t, f.request(admin, http.MethodGet, "/snippet-preview?name=hidden&type=js"), "HIDDEN_SNIPPET_MARKER")
	assertServed(t, f.request(admin, http.MethodGet, "/publish-preview/widgets/hiddenrefpkg/main.js"), "WIDGET_HIDDENREF_MARKER")
}

func TestPubUseTraversalStaysRefused(t *testing.T) {
	f := newPubServerFixture(t)
	// A path spelling that climbs out of a served directory must stay refused;
	// the request may be redirected or rejected, but it must never hand back the
	// protected template body.
	for _, target := range []string{
		"/snippets/%2e%2e/templates/tprivate.md",
		"/widgets/%2e%2e/templates/tprivate.md",
		"/plugins/%2e%2e/templates/tprivate.md",
		"/emojis/%2e%2e/templates/tprivate.md",
	} {
		recorder := f.request(model.RoleReader, http.MethodGet, target)
		if strings.Contains(recorder.Body.String(), "TEMPLATE_MARKER") {
			t.Fatalf("traversal request %q served a protected template", target)
		}
	}
}
