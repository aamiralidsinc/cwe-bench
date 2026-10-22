package api

import (
	"net/http"
	"strings"
	"testing"

	"github.com/siyuan-note/siyuan/kernel/model"
)

// The administrator keeps the complete listings, and readers keep seeing the
// packages and emoji that are published to them.

func TestPubUseAdministratorListingSeesEverything(t *testing.T) {
	f := newPubAPIFixture(t)
	admin := model.RoleAdministrator

	recorder := f.post(admin, "/api/bazaar/getInstalledPlugin", `{"frontend":"desktop"}`)
	if recorder.Code != http.StatusOK {
		t.Fatalf("plugin listing returned %d", recorder.Code)
	}
	for _, name := range []string{"openpkg", "hiddenpkg", "unloadedpkg"} {
		if !strings.Contains(recorder.Body.String(), `"`+name+`"`) {
			t.Fatalf("administrator listing lost plugin %q", name)
		}
	}

	recorder = f.post(admin, "/api/bazaar/getInstalledWidget", `{"frontend":"desktop"}`)
	if recorder.Code != http.StatusOK {
		t.Fatalf("widget listing returned %d", recorder.Code)
	}
	for _, name := range []string{"refpkg", "offpkg", "secretpkg"} {
		if !strings.Contains(recorder.Body.String(), `"`+name+`"`) {
			t.Fatalf("administrator listing lost widget %q", name)
		}
	}

	recorder = f.post(admin, "/api/bazaar/getInstalledTemplate", `{"frontend":"desktop"}`)
	if recorder.Code != http.StatusOK {
		t.Fatalf("template listing returned %d", recorder.Code)
	}
	if !strings.Contains(recorder.Body.String(), `"hiddentpl"`) {
		t.Fatalf("administrator listing lost the installed template")
	}
}

func TestPubUseReaderListingKeepsPublishedPackages(t *testing.T) {
	f := newPubAPIFixture(t)
	reader := model.RoleReader

	recorder := f.post(reader, "/api/bazaar/getInstalledPlugin", `{"frontend":"desktop"}`)
	if recorder.Code != http.StatusOK || !strings.Contains(recorder.Body.String(), `"openpkg"`) {
		t.Fatalf("reader lost a plugin that is published")
	}

	recorder = f.post(reader, "/api/bazaar/getInstalledWidget", `{"frontend":"desktop"}`)
	if recorder.Code != http.StatusOK || !strings.Contains(recorder.Body.String(), `"refpkg"`) {
		t.Fatalf("reader lost a widget that is published")
	}
}

func TestPubUseAdministratorEmojiConfSeesEverything(t *testing.T) {
	f := newPubAPIFixture(t)
	recorder := f.post(model.RoleAdministrator, "/api/system/getEmojiConf", `{}`)
	if recorder.Code != http.StatusOK {
		t.Fatalf("emoji conf returned %d", recorder.Code)
	}
	for _, name := range []string{"refpack/a.png", "refpack/b.png", "offpack/c.png"} {
		if !strings.Contains(recorder.Body.String(), name) {
			t.Fatalf("administrator emoji catalog lost %q", name)
		}
	}
}

func TestPubUseReaderEmojiConfKeepsReferencedEmoji(t *testing.T) {
	f := newPubAPIFixture(t)
	recorder := f.post(model.RoleReader, "/api/system/getEmojiConf", `{}`)
	if recorder.Code != http.StatusOK {
		t.Fatalf("emoji conf returned %d", recorder.Code)
	}
	if !strings.Contains(recorder.Body.String(), "refpack/a.png") {
		t.Fatalf("reader emoji catalog lost an emoji that is published")
	}
}
