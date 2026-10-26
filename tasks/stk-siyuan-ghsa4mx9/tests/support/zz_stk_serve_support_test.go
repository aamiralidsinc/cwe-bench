package server

// Hidden test support for the SVG-serving task. Copied into the product package at grade time
// and used only by the TestSec_/TestFunc_ suites. The fixture builds a small workspace on disk,
// restores every global it touches, and drives the real registered gin routes with a role on the
// context (the same value the authentication layer sets for a real request).

import (
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"strings"
	"testing"

	"github.com/gin-gonic/gin"
	"github.com/siyuan-note/siyuan/kernel/conf"
	"github.com/siyuan-note/siyuan/kernel/model"
	"github.com/siyuan-note/siyuan/kernel/util"
	"golang.org/x/net/html"
)

// A document that tries every active-content shape at once. Plain markers stay behind so the
// functional side can check that a legitimate document is still delivered.
const stkActiveSVGDocument = `<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 10 10" onload="alert('root')">
  <script>alert('script')</script>
  <a href="javascript:alert('href')"><text>one</text></a>
  <a xlink:href="javascript:alert('xlink')"><text>two</text></a>
  <a href="data:text/xml,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20onload%3D%22alert(1)%22%2F%3E"><text>three</text></a>
  <image href="data:application/xml,%3Csvg%2F%3E"/>
  <foreignObject><body xmlns="http://www.w3.org/1999/xhtml"><img src="x" onerror="alert('img')"/></body></foreignObject>
  <svg xmlns:svg="http://www.w3.org/2000/svg"><svg:script>alert('ns')</svg:script></svg>
  <text id="safe">STK_SAFE_MARKER</text>
</svg>`

// A document that uses only non-executable SVG features.
const stkLegitSVGDocument = `<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:svg="http://www.w3.org/2000/svg" viewBox="0 0 10 10">
  <style>.stk-cls{fill:red}</style>
  <a href="https://example.com/page"><text class="stk-cls">STK_LINK_MARKER</text></a>
  <a xlink:href="https://example.com/other"><text>STK_XLINK_MARKER</text></a>
  <svg:rect x="0" y="0" width="1" height="1" id="STK_NS_MARKER"/>
  <image href="data:image/png;base64,STKPNG"/>
  <text>STK_TEXT_MARKER</text>
</svg>`

type stkSVGFixture struct {
	root string
}

func stkNewSVGFixture(t *testing.T) *stkSVGFixture {
	t.Helper()
	gin.SetMode(gin.TestMode)
	f := &stkSVGFixture{root: t.TempDir()}

	origData, origTemp, origHistory, origWorkspace := util.DataDir, util.TempDir, util.HistoryDir, util.WorkspaceDir
	origConf := model.Conf

	util.WorkspaceDir = f.root
	util.DataDir = filepath.Join(f.root, "data")
	util.TempDir = filepath.Join(f.root, "temp")
	util.HistoryDir = filepath.Join(f.root, "history")
	model.Conf = model.NewAppConf()
	model.Conf.Editor = &conf.Editor{}

	t.Cleanup(func() {
		util.DataDir, util.TempDir, util.HistoryDir, util.WorkspaceDir = origData, origTemp, origHistory, origWorkspace
		model.Conf = origConf
	})

	for _, dir := range []string{
		filepath.Join(util.DataDir, "assets"),
		filepath.Join(util.DataDir, "emojis", "stkpack"),
		util.HistoryDir,
		filepath.Join(util.TempDir, "repo", "diff"),
	} {
		if err := os.MkdirAll(dir, 0755); err != nil {
			t.Fatalf("create fixture dir %s: %v", dir, err)
		}
	}
	return f
}

func stkWriteFile(t *testing.T, path, content string) {
	t.Helper()
	if err := os.MkdirAll(filepath.Dir(path), 0755); err != nil {
		t.Fatalf("create %s: %v", filepath.Dir(path), err)
	}
	if err := os.WriteFile(path, []byte(content), 0644); err != nil {
		t.Fatalf("write %s: %v", path, err)
	}
}

func (f *stkSVGFixture) writeAsset(t *testing.T, name, content string) {
	stkWriteFile(t, filepath.Join(util.DataDir, "assets", name), content)
}

func (f *stkSVGFixture) writeEmoji(t *testing.T, name, content string) {
	stkWriteFile(t, filepath.Join(util.DataDir, "emojis", "stkpack", name), content)
}

func (f *stkSVGFixture) writeHistory(t *testing.T, name, content string) {
	stkWriteFile(t, filepath.Join(util.HistoryDir, name), content)
}

func (f *stkSVGFixture) writeRepoDiff(t *testing.T, name, content string) {
	stkWriteFile(t, filepath.Join(util.TempDir, "repo", "diff", name), content)
}

// request builds the engine through the same constructor the production server uses, so every
// middleware production installs is active here too, then registers the routes under test. The
// role setter is appended after that chain because the authentication middleware would otherwise
// leave the visitor role it derives from the request.
func (f *stkSVGFixture) request(role model.Role, method, target string) *httptest.ResponseRecorder {
	engine := newGinServer("stk-test-cookie-key")
	engine.Use(func(c *gin.Context) {
		c.Set(model.RoleContextKey, role)
		c.Next()
	})
	serveAssets(engine)
	serveEmojis(engine)
	serveRepoDiff(engine)
	recorder := httptest.NewRecorder()
	engine.ServeHTTP(recorder, httptest.NewRequest(method, target, nil))
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
// carries. Text that merely spells a tag name is text, not an element, so a document that
// neutralises markup by escaping it is accepted.
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

func stkAssertServed(t *testing.T, recorder *httptest.ResponseRecorder) {
	t.Helper()
	if recorder.Code != http.StatusOK {
		t.Fatalf("request was not served: status %d", recorder.Code)
	}
}

func stkAssertBodyContains(t *testing.T, recorder *httptest.ResponseRecorder, markers ...string) {
	t.Helper()
	stkAssertServed(t, recorder)
	body := recorder.Body.String()
	for _, marker := range markers {
		if !strings.Contains(body, marker) {
			t.Fatalf("served document lost %q", marker)
		}
	}
}

func stkAssertBodyEquals(t *testing.T, recorder *httptest.ResponseRecorder, want string) {
	t.Helper()
	stkAssertServed(t, recorder)
	if got := recorder.Body.String(); got != want {
		t.Fatalf("served file changed: got %q want %q", got, want)
	}
}
