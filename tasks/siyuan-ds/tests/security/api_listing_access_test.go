package api

import (
	"encoding/json"
	"net/http"
	"strings"
	"testing"

	"github.com/siyuan-note/siyuan/kernel/model"
)

// Metadata endpoints must follow the same publish rules as the files they
// describe: a reader may not learn about packages or emoji that are not
// published to them.

func TestPubAccessReaderPluginListingFiltered(t *testing.T) {
	f := newPubAPIFixture(t)
	recorder := f.post(model.RoleReader, "/api/bazaar/getInstalledPlugin", `{"frontend":"desktop"}`)
	if recorder.Code != http.StatusOK {
		t.Fatalf("listing returned %d", recorder.Code)
	}
	body := recorder.Body.String()
	if strings.Contains(body, `"hiddenpkg"`) || strings.Contains(body, `"unloadedpkg"`) {
		t.Fatalf("reader listing exposed a plugin that is not published")
	}
	if !strings.Contains(body, `"openpkg"`) {
		t.Fatalf("reader listing lost a plugin that is published")
	}
}

func TestPubAccessReaderWidgetListingFiltered(t *testing.T) {
	f := newPubAPIFixture(t)
	recorder := f.post(model.RoleReader, "/api/bazaar/getInstalledWidget", `{"frontend":"desktop"}`)
	if recorder.Code != http.StatusOK {
		t.Fatalf("listing returned %d", recorder.Code)
	}
	body := recorder.Body.String()
	if strings.Contains(body, `"secretpkg"`) || strings.Contains(body, `"offpkg"`) {
		t.Fatalf("reader listing exposed a widget that is not published")
	}
	if !strings.Contains(body, `"refpkg"`) {
		t.Fatalf("reader listing lost a widget that is published")
	}
}

func TestPubAccessReaderTemplateListingFiltered(t *testing.T) {
	f := newPubAPIFixture(t)
	recorder := f.post(model.RoleReader, "/api/bazaar/getInstalledTemplate", `{"frontend":"desktop"}`)
	if recorder.Code != http.StatusOK {
		t.Fatalf("template listing returned %d", recorder.Code)
	}
	var result struct {
		Code int `json:"code"`
		Data struct {
			Packages []struct {
				Name string `json:"name"`
			} `json:"packages"`
		} `json:"data"`
	}
	if err := json.Unmarshal(recorder.Body.Bytes(), &result); err != nil {
		t.Fatalf("template listing is not valid JSON: %v", err)
	}
	if result.Code != 0 {
		t.Fatalf("template listing returned result code %d", result.Code)
	}
	if len(result.Data.Packages) != 0 {
		t.Fatalf("reader template listing described %d packages", len(result.Data.Packages))
	}
	if strings.Contains(recorder.Body.String(), `"hiddentpl"`) {
		t.Fatalf("reader listing exposed a template")
	}
}

func TestPubAccessReaderEmojiConfFiltered(t *testing.T) {
	f := newPubAPIFixture(t)
	recorder := f.post(model.RoleReader, "/api/system/getEmojiConf", `{}`)
	if recorder.Code != http.StatusOK {
		t.Fatalf("emoji conf returned %d", recorder.Code)
	}
	body := recorder.Body.String()
	if strings.Contains(body, "refpack/b.png") || strings.Contains(body, "offpack/c.png") {
		t.Fatalf("reader emoji catalog exposed emoji that are not published")
	}
	if !strings.Contains(body, "refpack/a.png") {
		t.Fatalf("reader emoji catalog lost an emoji that is published")
	}
}
