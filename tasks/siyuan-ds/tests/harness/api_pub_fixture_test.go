package api

import (
	"bytes"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"testing"

	"github.com/88250/lute/ast"
	"github.com/gin-gonic/gin"
	"github.com/siyuan-note/siyuan/kernel/cache"
	"github.com/siyuan-note/siyuan/kernel/conf"
	"github.com/siyuan-note/siyuan/kernel/filesys"
	"github.com/siyuan-note/siyuan/kernel/model"
	"github.com/siyuan-note/siyuan/kernel/treenode"
	"github.com/siyuan-note/siyuan/kernel/util"
)

// pubAPIFixture builds the data the marketplace listing and appearance APIs read,
// including a document that references one widget and one custom emoji.
type pubAPIFixture struct {
	root  string
	boxID string
	docID string
}

func newPubAPIFixture(t *testing.T) *pubAPIFixture {
	t.Helper()
	gin.SetMode(gin.TestMode)

	f := &pubAPIFixture{root: t.TempDir()}
	f.boxID = ast.NewNodeID()
	f.docID = ast.NewNodeID()

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
	f.writePackages(t)
	f.writeReferencingDocument(t)
	return f
}

func writeAPIFixtureFile(t *testing.T, path, content string) {
	t.Helper()
	if err := os.MkdirAll(filepath.Dir(path), 0755); err != nil {
		t.Fatalf("create %s: %v", filepath.Dir(path), err)
	}
	if err := os.WriteFile(path, []byte(content), 0644); err != nil {
		t.Fatalf("write %s: %v", path, err)
	}
}

func writeAPIPackage(t *testing.T, kind, name, jsonName string, disabledInPublish bool) {
	t.Helper()
	disabled := "false"
	if disabledInPublish {
		disabled = "true"
	}
	writeAPIFixtureFile(t, filepath.Join(util.DataDir, kind, name, jsonName),
		`{"name":"`+name+`","version":"1.0.0","minAppVersion":"0.0.1","disabledInPublish":`+disabled+`}`)
	writeAPIFixtureFile(t, filepath.Join(util.DataDir, kind, name, "index.js"), "content")
}

func (f *pubAPIFixture) writePackages(t *testing.T) {
	t.Helper()
	writeAPIPackage(t, "plugins", "openpkg", "plugin.json", false)
	writeAPIPackage(t, "plugins", "hiddenpkg", "plugin.json", true)
	writeAPIPackage(t, "plugins", "unloadedpkg", "plugin.json", false)
	writeAPIFixtureFile(t, filepath.Join(util.DataDir, "storage", "petal", "petals.json"),
		`[{"name":"openpkg","enabled":true},{"name":"hiddenpkg","enabled":true}]`)

	writeAPIPackage(t, "widgets", "refpkg", "widget.json", false)
	writeAPIPackage(t, "widgets", "offpkg", "widget.json", true)
	writeAPIPackage(t, "widgets", "secretpkg", "widget.json", false)

	// Template package state is irrelevant: no template is published at all.
	writeAPIPackage(t, "templates", "hiddentpl", "template.json", true)

	writeAPIFixtureFile(t, filepath.Join(util.AppearancePath, "emojis", "conf.json"), "[]")
	writeAPIFixtureFile(t, filepath.Join(util.DataDir, "emojis", "refpack", "a.png"), "a")
	writeAPIFixtureFile(t, filepath.Join(util.DataDir, "emojis", "refpack", "b.png"), "b")
	writeAPIFixtureFile(t, filepath.Join(util.DataDir, "emojis", "offpack", "c.png"), "c")
}

func (f *pubAPIFixture) writeReferencingDocument(t *testing.T) {
	t.Helper()
	tree := treenode.NewTree(f.boxID, "/"+f.docID+".sy", "/Doc", "Doc")
	appendNode := func(node *ast.Node) {
		node.ID = ast.NewNodeID()
		node.SetIALAttr("id", node.ID)
		node.SetIALAttr("updated", node.ID[:14])
		tree.Root.AppendChild(node)
	}
	appendNode(&ast.Node{Type: ast.NodeWidget, Tokens: []byte(`<iframe src="/widgets/refpkg/"></iframe>`)})
	appendNode(&ast.Node{Type: ast.NodeWidget, Tokens: []byte(`<iframe src="/widgets/offpkg/"></iframe>`)})
	appendNode(&ast.Node{Type: ast.NodeEmojiImg, Tokens: []byte(`<img class="emoji" src="/emojis/refpack/a.png">`)})

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

func (f *pubAPIFixture) engine(role model.Role) *gin.Engine {
	engine := gin.New()
	engine.Use(func(c *gin.Context) {
		c.Set(model.RoleContextKey, role)
		c.Next()
	})
	engine.POST("/api/bazaar/getInstalledPlugin", model.CheckAuth, getInstalledPlugin)
	engine.POST("/api/bazaar/getInstalledWidget", model.CheckAuth, getInstalledWidget)
	engine.POST("/api/bazaar/getInstalledTemplate", model.CheckAuth, getInstalledTemplate)
	engine.POST("/api/system/getEmojiConf", model.CheckAuth, getEmojiConf)
	return engine
}

func (f *pubAPIFixture) post(role model.Role, target, body string) *httptest.ResponseRecorder {
	recorder := httptest.NewRecorder()
	f.engine(role).ServeHTTP(recorder, httptest.NewRequest(http.MethodPost, target, bytes.NewBufferString(body)))
	return recorder
}
