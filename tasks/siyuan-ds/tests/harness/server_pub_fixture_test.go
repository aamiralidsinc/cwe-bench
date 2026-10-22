package server

import (
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"strings"
	"testing"

	"github.com/88250/lute/ast"
	"github.com/88250/lute/parse"
	"github.com/gin-gonic/gin"
	"github.com/siyuan-note/siyuan/kernel/cache"
	"github.com/siyuan-note/siyuan/kernel/conf"
	"github.com/siyuan-note/siyuan/kernel/filesys"
	"github.com/siyuan-note/siyuan/kernel/model"
	"github.com/siyuan-note/siyuan/kernel/treenode"
	"github.com/siyuan-note/siyuan/kernel/util"
)

// pubServerFixture builds a small but real workspace: data directories, installed
// packages, snippet configuration, a block-tree database, a public document and a
// publish-disabled document that reference some of the resources. Globals touched
// by the handlers are saved and restored, so the fixture can be used from several
// independent tests.
type pubServerFixture struct {
	root   string
	boxID  string
	docID  string
	outDir string
}

func newPubServerFixture(t *testing.T) *pubServerFixture {
	t.Helper()
	gin.SetMode(gin.TestMode)

	f := &pubServerFixture{root: t.TempDir()}
	f.boxID = ast.NewNodeID()
	f.docID = ast.NewNodeID()
	f.outDir = filepath.Join(f.root, "outside")

	origData, origTemp := util.DataDir, util.TempDir
	origSnippets, origAppearance := util.SnippetsPath, util.AppearancePath
	origWorkspace, origDBPath := util.WorkspaceDir, util.BlockTreeDBPath
	origConf := model.Conf
	origPublishAccess := model.GetPublishAccess()

	util.WorkspaceDir = f.root
	util.DataDir = filepath.Join(f.root, "data")
	util.TempDir = filepath.Join(f.root, "temp")
	util.SnippetsPath = filepath.Join(util.DataDir, "snippets")
	util.AppearancePath = filepath.Join(f.root, "appearance")
	util.BlockTreeDBPath = filepath.Join(util.TempDir, "blocktree.db")
	model.Conf = model.NewAppConf()
	model.Conf.Bazaar = &conf.Bazaar{Trust: true}
	if err := model.SetPublishAccess(model.PublishAccess{}); err != nil {
		t.Fatalf("reset publish access: %v", err)
	}

	t.Cleanup(func() {
		treenode.CloseDatabase()
		util.DataDir, util.TempDir = origData, origTemp
		util.SnippetsPath, util.AppearancePath = origSnippets, origAppearance
		util.WorkspaceDir, util.BlockTreeDBPath = origWorkspace, origDBPath
		model.Conf = origConf
		_ = model.SetPublishAccess(origPublishAccess)
	})

	for _, dir := range []string{util.DataDir, util.TempDir, util.SnippetsPath, util.AppearancePath} {
		if err := os.MkdirAll(dir, 0755); err != nil {
			t.Fatalf("create fixture dir: %v", err)
		}
	}
	treenode.InitBlockTree(true)
	f.writeStaticResources(t)
	f.writeSnippetConfig(t)
	f.writeReferencingDocuments(t)
	return f
}

func writeFixtureFile(t *testing.T, path, content string) {
	t.Helper()
	if err := os.MkdirAll(filepath.Dir(path), 0755); err != nil {
		t.Fatalf("create %s: %v", filepath.Dir(path), err)
	}
	if err := os.WriteFile(path, []byte(content), 0644); err != nil {
		t.Fatalf("write %s: %v", path, err)
	}
}

func writePackageJSON(t *testing.T, path, name string, disabledInPublish bool) {
	t.Helper()
	disabled := "false"
	if disabledInPublish {
		disabled = "true"
	}
	writeFixtureFile(t, path, `{"name":"`+name+`","version":"1.0.0","minAppVersion":"0.0.1","disabledInPublish":`+disabled+`}`)
}

func (f *pubServerFixture) writeStaticResources(t *testing.T) {
	t.Helper()

	writeFixtureFile(t, filepath.Join(util.DataDir, "templates", "tprivate.md"), "TEMPLATE_MARKER")
	writeFixtureFile(t, filepath.Join(util.TempDir, "export", "artifact.txt"), "EXPORT_MARKER")
	writeFixtureFile(t, filepath.Join(util.TempDir, "export", "temp", "artifact2.txt"), "EXPORT_TEMP_MARKER")

	widgets := filepath.Join(util.DataDir, "widgets")
	writeFixtureFile(t, filepath.Join(widgets, "refpkg", "index.html"), "WIDGET_REF_MARKER")
	writeFixtureFile(t, filepath.Join(widgets, "refpkg", "main.js"), "WIDGET_REF_MARKER")
	writePackageJSON(t, filepath.Join(widgets, "refpkg", "widget.json"), "refpkg", false)
	writeFixtureFile(t, filepath.Join(widgets, "secretpkg", "index.html"), "WIDGET_UNREF_MARKER")
	writeFixtureFile(t, filepath.Join(widgets, "secretpkg", "main.js"), "WIDGET_UNREF_MARKER")
	writePackageJSON(t, filepath.Join(widgets, "secretpkg", "widget.json"), "secretpkg", false)
	writeFixtureFile(t, filepath.Join(widgets, "offpkg", "index.html"), "WIDGET_DISABLED_MARKER")
	writeFixtureFile(t, filepath.Join(widgets, "offpkg", "main.js"), "WIDGET_DISABLED_MARKER")
	writePackageJSON(t, filepath.Join(widgets, "offpkg", "widget.json"), "offpkg", true)

	// A widget referenced only by the publish-disabled document must not count as
	// referenced for a reader.
	writeFixtureFile(t, filepath.Join(widgets, "hiddenrefpkg", "index.html"), "WIDGET_HIDDENREF_MARKER")
	writeFixtureFile(t, filepath.Join(widgets, "hiddenrefpkg", "main.js"), "WIDGET_HIDDENREF_MARKER")
	writePackageJSON(t, filepath.Join(widgets, "hiddenrefpkg", "widget.json"), "hiddenrefpkg", false)

	// The same widget is referenced through an absolute loopback URL and through
	// an HTML block, rather than a root-relative widget node.
	writeFixtureFile(t, filepath.Join(widgets, "locpkg", "index.html"), "WIDGET_LOCAL_MARKER")
	writeFixtureFile(t, filepath.Join(widgets, "locpkg", "main.js"), "WIDGET_LOCAL_MARKER")
	writePackageJSON(t, filepath.Join(widgets, "locpkg", "widget.json"), "locpkg", false)
	writeFixtureFile(t, filepath.Join(widgets, "htmlpkg", "index.html"), "WIDGET_HTML_MARKER")
	writeFixtureFile(t, filepath.Join(widgets, "htmlpkg", "main.js"), "WIDGET_HTML_MARKER")
	writePackageJSON(t, filepath.Join(widgets, "htmlpkg", "widget.json"), "htmlpkg", false)

	// A package whose top-level directory is a symlink is a supported install
	// layout; a symlink nested inside a package must not escape it.
	external := filepath.Join(f.root, "external", "sympkg")
	writeFixtureFile(t, filepath.Join(external, "index.html"), "WIDGET_SYMLINK_MARKER")
	writeFixtureFile(t, filepath.Join(external, "main.js"), "WIDGET_SYMLINK_MARKER")
	writePackageJSON(t, filepath.Join(external, "widget.json"), "sympkg", false)
	if err := os.Symlink(external, filepath.Join(widgets, "sympkg")); err != nil {
		t.Fatalf("create package symlink: %v", err)
	}
	writeFixtureFile(t, filepath.Join(widgets, "linkedpkg", "index.html"), "WIDGET_LINK_MARKER")
	writeFixtureFile(t, filepath.Join(widgets, "linkedpkg", "main.js"), "WIDGET_LINK_MARKER")
	writePackageJSON(t, filepath.Join(widgets, "linkedpkg", "widget.json"), "linkedpkg", false)
	writeFixtureFile(t, filepath.Join(f.outDir, "gone.txt"), "OUTSIDE_MARKER")
	if err := os.Symlink(f.outDir, filepath.Join(widgets, "linkedpkg", "escape")); err != nil {
		t.Fatalf("create nested symlink: %v", err)
	}

	emojis := filepath.Join(util.DataDir, "emojis")
	writeFixtureFile(t, filepath.Join(emojis, "refpack", "a.png"), "EMOJI_REF_MARKER")
	writeFixtureFile(t, filepath.Join(emojis, "refpack", "b.png"), "EMOJI_UNREF_MARKER")
	writeFixtureFile(t, filepath.Join(emojis, "offpack", "c.png"), "EMOJI_OFFPACK_MARKER")
	writeFixtureFile(t, filepath.Join(emojis, "refpack", "d.png"), "EMOJI_ESCAPED_MARKER")
	writeFixtureFile(t, filepath.Join(emojis, "nestedpack", "sub", "f.png"), "EMOJI_NESTED_MARKER")
	writeFixtureFile(t, filepath.Join(emojis, "nestedpack", "h.png"), "EMOJI_HIDDENREF_MARKER")
	writeFixtureFile(t, filepath.Join(util.AppearancePath, "emojis", "conf.json"), "[]")

	plugins := filepath.Join(util.DataDir, "plugins")
	writeFixtureFile(t, filepath.Join(plugins, "openpkg", "index.js"), "PLUGIN_OPEN_MARKER")
	writePackageJSON(t, filepath.Join(plugins, "openpkg", "plugin.json"), "openpkg", false)
	writeFixtureFile(t, filepath.Join(plugins, "hiddenpkg", "index.js"), "PLUGIN_HIDDEN_MARKER")
	writePackageJSON(t, filepath.Join(plugins, "hiddenpkg", "plugin.json"), "hiddenpkg", true)
	writeFixtureFile(t, filepath.Join(plugins, "unloadedpkg", "index.js"), "PLUGIN_UNLOADED_MARKER")
	writePackageJSON(t, filepath.Join(plugins, "unloadedpkg", "plugin.json"), "unloadedpkg", false)
	writeFixtureFile(t, filepath.Join(util.DataDir, "storage", "petal", "petals.json"),
		`[{"name":"openpkg","enabled":true},{"name":"hiddenpkg","enabled":true}]`)

	writeFixtureFile(t, filepath.Join(util.SnippetsPath, "allowed.css"), "ALLOWED_SNIPPET_MARKER")
	writeFixtureFile(t, filepath.Join(util.SnippetsPath, "hidden.js"), "HIDDEN_SNIPPET_MARKER")
	writeFixtureFile(t, filepath.Join(util.SnippetsPath, "fallback.css"), "FALLBACK_SNIPPET_MARKER")
}

func (f *pubServerFixture) writeSnippetConfig(t *testing.T) {
	t.Helper()
	err := model.SetSnippet([]*conf.Snippet{
		{Name: "allowed", Type: "css", Content: "ALLOWED_SNIPPET_MARKER"},
		{Name: "hidden", Type: "js", Content: "HIDDEN_SNIPPET_MARKER", DisabledInPublish: true},
		// One name is configured twice, with different publish switches: the
		// publish state belongs to the snippet entry, so the type must match too.
		{Name: "dual", Type: "js", Content: "DUAL_JS_MARKER"},
		{Name: "dual", Type: "css", Content: "DUAL_CSS_MARKER", DisabledInPublish: true},
	})
	if err != nil {
		t.Fatalf("write snippet config: %v", err)
	}
}

func (f *pubServerFixture) writeReferencingDocuments(t *testing.T) {
	t.Helper()
	appendNodes := func(tree *parse.Tree, nodes []*ast.Node) {
		for _, node := range nodes {
			node.ID = ast.NewNodeID()
			node.SetIALAttr("id", node.ID)
			node.SetIALAttr("updated", node.ID[:14])
			tree.Root.AppendChild(node)
		}
	}
	writeTree := func(tree *parse.Tree) {
		if _, err := filesys.WriteTree(tree); err != nil {
			t.Fatalf("write document: %v", err)
		}
		if data, err := os.ReadFile(filepath.Join(util.DataDir, f.boxID, tree.Path)); err == nil {
			// Prime the kernel tree cache with the bytes just written so the access
			// check parses the same document without triggering an offline reindex.
			cache.SetTreeDataInBox(tree.ID, f.boxID, data)
		}
		treenode.UpsertBlockTree(tree)
	}

	publicTree := treenode.NewTree(f.boxID, "/"+f.docID+".sy", "/Doc", "Doc")
	appendNodes(publicTree, []*ast.Node{
		{Type: ast.NodeWidget, Tokens: []byte(`<iframe src="/widgets/refpkg/"></iframe>`)},
		{Type: ast.NodeWidget, Tokens: []byte(`<iframe src="/widgets/offpkg/"></iframe>`)},
		{Type: ast.NodeWidget, Tokens: []byte(`<iframe src="/widgets/sympkg/"></iframe>`)},
		{Type: ast.NodeWidget, Tokens: []byte(`<iframe src="/widgets/linkedpkg/"></iframe>`)},
		{Type: ast.NodeEmojiImg, Tokens: []byte(`<img class="emoji" src="/emojis/refpack/a.png">`)},
		{Type: ast.NodeIFrame, Tokens: []byte(`<iframe src="http://127.0.0.1:6806/widgets/locpkg/"></iframe>`)},
		{Type: ast.NodeHTMLBlock, Tokens: []byte(`<div><iframe src="/widgets/htmlpkg/"></iframe></div>`)},
		{Type: ast.NodeEmojiImg, Tokens: []byte(`<img class="emoji" src="/emojis/refpack/d.png?w=1&amp;h=1">`)},
		{Type: ast.NodeEmojiImg, Tokens: []byte(`<img class="emoji" src="/emojis/nestedpack/sub/f.png">`)},
	})
	writeTree(publicTree)

	// A second document is withheld from publishing. The resources it references
	// are therefore not available to a reader even though they exist and are not
	// themselves marked as excluded.
	hiddenDocID := ast.NewNodeID()
	hiddenTree := treenode.NewTree(f.boxID, "/"+hiddenDocID+".sy", "/Hidden", "Hidden")
	appendNodes(hiddenTree, []*ast.Node{
		{Type: ast.NodeWidget, Tokens: []byte(`<iframe src="/widgets/hiddenrefpkg/"></iframe>`)},
		{Type: ast.NodeEmojiImg, Tokens: []byte(`<img class="emoji" src="/emojis/nestedpack/h.png">`)},
	})
	writeTree(hiddenTree)

	if err := model.SetPublishAccess(model.PublishAccess{
		{ID: hiddenDocID, Visible: false, Disable: true},
	}); err != nil {
		t.Fatalf("set publish access: %v", err)
	}
}

func (f *pubServerFixture) engine(role model.Role) *gin.Engine {
	engine := gin.New()
	engine.Use(func(c *gin.Context) {
		c.Set(model.RoleContextKey, role)
		c.Next()
	})
	serveTemplates(engine)
	serveExport(engine)
	serveWidgets(engine)
	servePlugins(engine)
	serveEmojis(engine)
	serveSnippets(engine)
	serveSnippetPreview(engine)
	servePublishPreview(engine)
	return engine
}

func (f *pubServerFixture) request(role model.Role, method, target string) *httptest.ResponseRecorder {
	recorder := httptest.NewRecorder()
	f.engine(role).ServeHTTP(recorder, httptest.NewRequest(method, target, nil))
	return recorder
}

func assertRefused(t *testing.T, recorder *httptest.ResponseRecorder, marker string) {
	t.Helper()
	if recorder.Code < 400 || recorder.Code >= 500 {
		t.Fatalf("request was not refused with a client error: status %d", recorder.Code)
	}
	if marker != "" && strings.Contains(recorder.Body.String(), marker) {
		t.Fatalf("refused response still carried the protected body")
	}
}

func assertServed(t *testing.T, recorder *httptest.ResponseRecorder, marker string) {
	t.Helper()
	if recorder.Code != http.StatusOK {
		t.Fatalf("request did not serve the resource: status %d", recorder.Code)
	}
	if marker != "" && !strings.Contains(recorder.Body.String(), marker) {
		t.Fatalf("response did not carry the expected content")
	}
}
