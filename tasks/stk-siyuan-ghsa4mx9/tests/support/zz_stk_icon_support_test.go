package api

// Hidden test support for the dynamic-icon task. Copied into the product package at grade time
// and used only by the TestSec_/TestFunc_ suites. The fixture sets up a small workspace with one
// document block so the icon template form has real data to render, and drives the real
// registered endpoint.

import (
	"net/http"
	"net/http/httptest"
	"net/url"
	"os"
	"path/filepath"
	"strings"
	"testing"

	"github.com/88250/lute/ast"
	"github.com/gin-gonic/gin"
	"github.com/siyuan-note/siyuan/kernel/cache"
	"github.com/siyuan-note/siyuan/kernel/conf"
	"github.com/siyuan-note/siyuan/kernel/filesys"
	"github.com/siyuan-note/siyuan/kernel/model"
	"github.com/siyuan-note/siyuan/kernel/treenode"
	"github.com/siyuan-note/siyuan/kernel/util"
	"golang.org/x/net/html"
)

const stkDocTitle = "STK Doc Title"

// stkNewIconConfig installs an icon configuration with default editor settings and restores the
// process globals when the test ends. It needs no workspace.
func stkNewIconConfig(t *testing.T) {
	t.Helper()
	gin.SetMode(gin.TestMode)
	origConf := model.Conf
	model.Conf = model.NewAppConf()
	model.Conf.Editor = &conf.Editor{}
	t.Cleanup(func() { model.Conf = origConf })
}

type stkIconFixture struct {
	docID string
}

// stkNewIconFixture additionally builds a workspace with one document so the template form of
// the text icon has something to expand.
func stkNewIconFixture(t *testing.T) *stkIconFixture {
	t.Helper()
	stkNewIconConfig(t)

	f := &stkIconFixture{docID: ast.NewNodeID()}
	boxID := ast.NewNodeID()
	root := t.TempDir()
	origData, origTemp, origWorkspace, origDBPath := util.DataDir, util.TempDir, util.WorkspaceDir, util.BlockTreeDBPath

	util.WorkspaceDir = root
	util.DataDir = filepath.Join(root, "data")
	util.TempDir = filepath.Join(root, "temp")
	util.BlockTreeDBPath = filepath.Join(util.TempDir, "blocktree.db")

	t.Cleanup(func() {
		treenode.CloseDatabase()
		util.DataDir, util.TempDir, util.WorkspaceDir, util.BlockTreeDBPath = origData, origTemp, origWorkspace, origDBPath
	})

	for _, dir := range []string{util.DataDir, util.TempDir} {
		if err := os.MkdirAll(dir, 0755); err != nil {
			t.Fatalf("create fixture dir %s: %v", dir, err)
		}
	}
	treenode.InitBlockTree(true)

	tree := treenode.NewTree(boxID, "/"+f.docID+".sy", "/STK Doc", stkDocTitle)
	if _, err := filesys.WriteTree(tree); err != nil {
		t.Fatalf("write document: %v", err)
	}
	if data, err := os.ReadFile(filepath.Join(util.DataDir, boxID, tree.Path)); err == nil {
		cache.SetTreeData(tree.ID, data)
	}
	treenode.UpsertBlockTree(tree)
	return f
}

func stkIconRequest(t *testing.T, params map[string]string) *httptest.ResponseRecorder {
	t.Helper()
	values := url.Values{}
	for k, v := range params {
		values.Set(k, v)
	}
	engine := gin.New()
	engine.Handle(http.MethodGet, "/api/icon/getDynamicIcon", getDynamicIcon)
	recorder := httptest.NewRecorder()
	engine.ServeHTTP(recorder, httptest.NewRequest(http.MethodGet,
		"/api/icon/getDynamicIcon?"+values.Encode(), nil))
	return recorder
}

func stkLocalName(name string) string {
	name = strings.ToLower(strings.TrimSpace(name))
	if idx := strings.LastIndex(name, ":"); 0 <= idx {
		name = name[idx+1:]
	}
	return name
}

func stkSafeDataImage(value string) bool {
	if !strings.HasPrefix(value, "data:") {
		return false
	}
	mediaType := value[len("data:"):]
	if idx := strings.IndexAny(mediaType, ";,"); 0 <= idx {
		mediaType = mediaType[:idx]
	}
	switch strings.TrimSpace(mediaType) {
	case "image/png", "image/jpeg", "image/jpg", "image/gif", "image/webp":
		return true
	}
	return false
}

// stkForeignObjectActive reports whether a foreignObject subtree carries something active: a
// script, an event handler, a script-scheme reference, a non-raster data: document, or an
// embedding element. A foreignObject whose content is inert is not executable on its own and is
// therefore not flagged.
func stkForeignObjectActive(n *html.Node) bool {
	for c := n.FirstChild; c != nil; c = c.NextSibling {
		if c.Type == html.ElementNode {
			switch stkLocalName(c.Data) {
			case "script", "iframe", "object", "embed":
				return true
			}
			for _, a := range c.Attr {
				key := strings.ToLower(strings.TrimSpace(a.Key))
				val := strings.ToLower(strings.TrimSpace(a.Val))
				val = strings.TrimLeft(val, "\x00\x09\x0a\x0c\x0d\x20")
				if strings.HasPrefix(key, "on") {
					return true
				}
				switch stkLocalName(key) {
				case "href", "src", "action", "formaction", "poster":
					if strings.HasPrefix(val, "javascript:") || strings.HasPrefix(val, "vbscript:") ||
						strings.HasPrefix(val, "livescript:") || strings.HasPrefix(val, "mocha:") {
						return true
					}
					if strings.HasPrefix(val, "data:") && !stkSafeDataImage(val) {
						return true
					}
				}
			}
		}
		if stkForeignObjectActive(c) {
			return true
		}
	}
	return false
}

// stkActiveSVGContent parses a served document and returns the executable constructs it still
// carries. Escaped text that merely spells a tag name is text, not an element.
func stkActiveSVGContent(t *testing.T, body string) []string {
	t.Helper()
	doc, err := html.Parse(strings.NewReader(body))
	if err != nil {
		t.Fatalf("served document is not parseable: %v", err)
	}
	var found []string
	var walk func(*html.Node)
	walk = func(n *html.Node) {
		for c := n.FirstChild; c != nil; c = c.NextSibling {
			if c.Type == html.ElementNode {
				switch stkLocalName(c.Data) {
				case "script", "iframe", "object", "embed":
					found = append(found, "element:"+stkLocalName(c.Data))
				case "foreignobject":
					if stkForeignObjectActive(c) {
						found = append(found, "element:foreignobject")
					}
				}
				for _, a := range c.Attr {
					key := strings.ToLower(strings.TrimSpace(a.Key))
					val := strings.ToLower(strings.TrimSpace(a.Val))
					val = strings.TrimLeft(val, "\x00\x09\x0a\x0c\x0d\x20")
					if strings.HasPrefix(key, "on") {
						found = append(found, "attribute:"+key)
						continue
					}
					switch stkLocalName(key) {
					case "href", "src", "action", "formaction", "poster":
						if strings.HasPrefix(val, "javascript:") || strings.HasPrefix(val, "vbscript:") ||
							strings.HasPrefix(val, "livescript:") || strings.HasPrefix(val, "mocha:") {
							found = append(found, "url:"+key+"="+val)
						} else if strings.HasPrefix(val, "data:") && !stkSafeDataImage(val) {
							found = append(found, "url:"+key+"="+val)
						}
					case "style":
						if strings.Contains(val, "expression(") || strings.Contains(val, "javascript:") || strings.Contains(val, "vbscript:") {
							found = append(found, "style:"+val)
						}
					}
				}
			}
			walk(c)
		}
	}
	walk(doc)
	return found
}

func stkAssertNeutralised(t *testing.T, recorder *httptest.ResponseRecorder) {
	t.Helper()
	if recorder.Code >= 500 {
		t.Fatalf("request failed with a server error: status %d", recorder.Code)
	}
	if recorder.Code >= 400 && recorder.Code < 500 {
		return // a clean refusal is an acceptable answer
	}
	if recorder.Code != http.StatusOK {
		t.Fatalf("unexpected response status %d", recorder.Code)
	}
	if found := stkActiveSVGContent(t, recorder.Body.String()); 0 < len(found) {
		t.Fatalf("served document still carried active content: %v", found)
	}
}

// stkIconText returns the text the served document displays, ignoring markup.
func stkIconText(t *testing.T, body string) string {
	t.Helper()
	doc, err := html.Parse(strings.NewReader(body))
	if err != nil {
		t.Fatalf("served document is not parseable: %v", err)
	}
	var parts []string
	var walk func(*html.Node)
	walk = func(n *html.Node) {
		if n.Type == html.TextNode {
			parts = append(parts, n.Data)
		}
		for c := n.FirstChild; c != nil; c = c.NextSibling {
			walk(c)
		}
	}
	walk(doc)
	return strings.Join(parts, "")
}

func stkAssertIconServed(t *testing.T, recorder *httptest.ResponseRecorder) string {
	t.Helper()
	if recorder.Code != http.StatusOK {
		t.Fatalf("icon was not served: status %d", recorder.Code)
	}
	if contentType := recorder.Header().Get("Content-Type"); !strings.Contains(contentType, "image/svg+xml") {
		t.Fatalf("icon has unexpected content type %q", contentType)
	}
	return recorder.Body.String()
}
