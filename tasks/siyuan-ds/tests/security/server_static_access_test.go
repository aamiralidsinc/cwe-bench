package server

import (
	"net/http"
	"testing"

	"github.com/siyuan-note/siyuan/kernel/model"
)

// The publish access rules for static resources: a reader may only receive
// templates, exported artifacts, snippets, plugins, widgets and custom emoji
// files that the workspace owner published. Each case goes through the real
// registered route with the reader role on the context (the publish proxy sets
// the same role for every proxied request).

func TestPubAccessTemplateRefusedToReader(t *testing.T) {
	f := newPubServerFixture(t)
	assertRefused(t, f.request(model.RoleReader, http.MethodGet, "/templates/tprivate.md"), "TEMPLATE_MARKER")
}

func TestPubAccessTemplateHeadRefusedToReader(t *testing.T) {
	f := newPubServerFixture(t)
	assertRefused(t, f.request(model.RoleReader, http.MethodHead, "/templates/tprivate.md"), "")
}

func TestPubAccessExportArtifactRefusedToReader(t *testing.T) {
	f := newPubServerFixture(t)
	assertRefused(t, f.request(model.RoleReader, http.MethodGet, "/export/artifact.txt"), "EXPORT_MARKER")
	assertRefused(t, f.request(model.RoleReader, http.MethodGet, "/export/temp/artifact2.txt"), "EXPORT_TEMP_MARKER")
}

func TestPubAccessUnreferencedWidgetRefusedToReader(t *testing.T) {
	f := newPubServerFixture(t)
	assertRefused(t, f.request(model.RoleReader, http.MethodGet, "/widgets/secretpkg/"), "WIDGET_UNREF_MARKER")
	assertRefused(t, f.request(model.RoleReader, http.MethodHead, "/widgets/secretpkg/"), "")
}

func TestPubAccessPublishDisabledWidgetRefusedToReader(t *testing.T) {
	f := newPubServerFixture(t)
	assertRefused(t, f.request(model.RoleReader, http.MethodGet, "/widgets/offpkg/index.html"), "WIDGET_DISABLED_MARKER")
}

func TestPubAccessUnreferencedEmojiRefusedToReader(t *testing.T) {
	f := newPubServerFixture(t)
	assertRefused(t, f.request(model.RoleReader, http.MethodGet, "/emojis/refpack/b.png"), "EMOJI_UNREF_MARKER")
	assertRefused(t, f.request(model.RoleReader, http.MethodGet, "/emojis/offpack/c.png"), "EMOJI_OFFPACK_MARKER")
	assertRefused(t, f.request(model.RoleReader, http.MethodHead, "/emojis/refpack/b.png"), "")
}

func TestPubAccessHiddenDocumentResourcesRefusedToReader(t *testing.T) {
	f := newPubServerFixture(t)
	assertRefused(t, f.request(model.RoleReader, http.MethodGet, "/widgets/hiddenrefpkg/"), "WIDGET_HIDDENREF_MARKER")
	assertRefused(t, f.request(model.RoleReader, http.MethodGet, "/emojis/nestedpack/h.png"), "EMOJI_HIDDENREF_MARKER")
}

func TestPubAccessPublishDisabledPluginRefusedToReader(t *testing.T) {
	f := newPubServerFixture(t)
	assertRefused(t, f.request(model.RoleReader, http.MethodGet, "/plugins/hiddenpkg/index.js"), "PLUGIN_HIDDEN_MARKER")
	assertRefused(t, f.request(model.RoleReader, http.MethodHead, "/plugins/hiddenpkg/index.js"), "")
}

func TestPubAccessUnloadedPluginRefusedToReader(t *testing.T) {
	f := newPubServerFixture(t)
	assertRefused(t, f.request(model.RoleReader, http.MethodGet, "/plugins/unloadedpkg/index.js"), "PLUGIN_UNLOADED_MARKER")
	assertRefused(t, f.request(model.RoleReader, http.MethodHead, "/plugins/unloadedpkg/index.js"), "")
}

func TestPubAccessPublishDisabledSnippetRefusedToReader(t *testing.T) {
	f := newPubServerFixture(t)
	assertRefused(t, f.request(model.RoleReader, http.MethodGet, "/snippets/hidden.js"), "HIDDEN_SNIPPET_MARKER")
}

func TestPubAccessFilesystemSnippetRefusedToReader(t *testing.T) {
	f := newPubServerFixture(t)
	assertRefused(t, f.request(model.RoleReader, http.MethodGet, "/snippets/fallback.css"), "FALLBACK_SNIPPET_MARKER")
}

func TestPubAccessNestedSymlinkEscapeRefusedToReader(t *testing.T) {
	f := newPubServerFixture(t)
	assertRefused(t, f.request(model.RoleReader, http.MethodGet, "/widgets/linkedpkg/escape/gone.txt"), "OUTSIDE_MARKER")
}

func TestPubAccessNormalizedPathRefusedToReader(t *testing.T) {
	f := newPubServerFixture(t)
	// A non-canonical spelling must not be authorized on the package named by
	// its first segment and then resolved to a different, unpublished one.
	assertRefused(t, f.request(model.RoleReader, http.MethodGet, "/plugins/openpkg/../hiddenpkg/index.js"), "PLUGIN_HIDDEN_MARKER")
	assertRefused(t, f.request(model.RoleReader, http.MethodGet, "/emojis/refpack/../offpack/c.png"), "EMOJI_OFFPACK_MARKER")
}

func TestPubAccessPreviewResolverRefusedToReader(t *testing.T) {
	f := newPubServerFixture(t)
	assertRefused(t, f.request(model.RoleReader, http.MethodGet, "/publish-preview/templates/tprivate.md"), "TEMPLATE_MARKER")
	assertRefused(t, f.request(model.RoleReader, http.MethodGet, "/publish-preview/snippets/hidden.js"), "HIDDEN_SNIPPET_MARKER")
	assertRefused(t, f.request(model.RoleReader, http.MethodGet, "/publish-preview/snippets/fallback.css"), "FALLBACK_SNIPPET_MARKER")
	assertRefused(t, f.request(model.RoleReader, http.MethodGet, "/publish-preview/widgets/secretpkg/main.js"), "WIDGET_UNREF_MARKER")
	assertRefused(t, f.request(model.RoleReader, http.MethodGet, "/publish-preview/emojis/refpack/b.png"), "EMOJI_UNREF_MARKER")
	assertRefused(t, f.request(model.RoleReader, http.MethodGet, "/publish-preview/plugins/hiddenpkg/index.js"), "PLUGIN_HIDDEN_MARKER")
}

func TestPubAccessSnippetPreviewRefusedToReader(t *testing.T) {
	f := newPubServerFixture(t)
	assertRefused(t, f.request(model.RoleReader, http.MethodGet, "/snippet-preview?name=hidden&type=js"), "HIDDEN_SNIPPET_MARKER")
}

func TestPubAccessSnippetTypeMismatchRefusedToReader(t *testing.T) {
	f := newPubServerFixture(t)
	assertRefused(t, f.request(model.RoleReader, http.MethodGet, "/snippets/dual.css"), "DUAL_CSS_MARKER")
	assertRefused(t, f.request(model.RoleReader, http.MethodGet, "/snippet-preview?name=dual&type=css"), "DUAL_CSS_MARKER")
}
