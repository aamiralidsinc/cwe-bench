package fbhttp

import (
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"strings"
	"testing"

	"github.com/filebrowser/filebrowser/v2/diskcache"
	"github.com/filebrowser/filebrowser/v2/users"
)

func zzRequireOK(t *testing.T, rec *httptest.ResponseRecorder, what string) {
	t.Helper()
	if rec.Code < 200 || rec.Code > 299 {
		t.Fatalf("%s: expected success, got status %d (body %q)", what, rec.Code, strings.TrimSpace(rec.Body.String()))
	}
}

// A brand-new file (with no existing ancestor chain) is still creatable.
func TestFunc_CreateNewFile(t *testing.T) {
	e := zzNewEnv(t, users.Permissions{Create: true, Modify: true})
	rec := e.req(resourcePostHandler(diskcache.NewNoOp()), http.MethodPost, "/fresh/deep/new.txt", "hello", nil)
	zzRequireOK(t, rec, "creating a new file")
	zzRequireFile(t, filepath.Join(e.scope, "fresh", "deep", "new.txt"), "hello", "creating a new file")
}

// Overwriting through a link whose target stays inside the scope keeps working.
func TestFunc_OverwriteThroughInScopeLink(t *testing.T) {
	e := zzNewEnv(t, users.Permissions{Create: true, Modify: true})
	e.write("real.txt", "old")
	e.link(filepath.Join(e.scope, "real.txt"), filepath.Join(e.scope, "alias.txt"))

	rec := e.req(resourcePostHandler(diskcache.NewNoOp()), http.MethodPost, "/alias.txt?override=true", "new", nil)
	zzRequireOK(t, rec, "overwrite through an in-scope link")
	zzRequireFile(t, filepath.Join(e.scope, "real.txt"), "new", "overwrite through an in-scope link")
}

// A dangling link whose target is inside the scope is a legitimate way to
// create a new in-scope file; it must keep working.
func TestFunc_DanglingLinkToInScopeTarget(t *testing.T) {
	e := zzNewEnv(t, users.Permissions{Create: true, Modify: true})
	e.link(filepath.Join(e.scope, "not-yet.txt"), filepath.Join(e.scope, "alias"))

	rec := e.req(resourcePostHandler(diskcache.NewNoOp()), http.MethodPost, "/alias?override=true", "inside", nil)
	zzRequireOK(t, rec, "dangling link with an in-scope target")
	zzRequireFile(t, filepath.Join(e.scope, "not-yet.txt"), "inside", "dangling link with an in-scope target")
}

// Ordinary directory creation keeps working.
func TestFunc_Mkdir(t *testing.T) {
	e := zzNewEnv(t, users.Permissions{Create: true})
	rec := e.req(resourcePostHandler(diskcache.NewNoOp()), http.MethodPost, "/one/two/", "", nil)
	zzRequireOK(t, rec, "creating a directory")
	if info, err := os.Stat(filepath.Join(e.scope, "one", "two")); err != nil || !info.IsDir() {
		t.Fatalf("creating a directory: not created (%v)", err)
	}
}

// Creating a directory through a link that stays inside the scope keeps
// working.
func TestFunc_MkdirThroughInScopeLink(t *testing.T) {
	e := zzNewEnv(t, users.Permissions{Create: true})
	e.mkdir("real")
	e.link(filepath.Join(e.scope, "real"), filepath.Join(e.scope, "linkdir"))

	rec := e.req(resourcePostHandler(diskcache.NewNoOp()), http.MethodPost, "/linkdir/newdir/", "", nil)
	zzRequireOK(t, rec, "directory creation through an in-scope link")
	if info, err := os.Stat(filepath.Join(e.scope, "real", "newdir")); err != nil || !info.IsDir() {
		t.Fatalf("directory creation through an in-scope link: not created (%v)", err)
	}
}

// Copying a whole directory keeps working.
func TestFunc_CopyDirectory(t *testing.T) {
	e := zzNewEnv(t, users.Permissions{Create: true, Modify: true})
	e.write("src/file.txt", "one")
	e.write("src/sub/nested.txt", "two")

	rec := e.req(resourcePatchHandler(diskcache.NewNoOp()), http.MethodPatch, "/src?action=copy&destination=/dst", "", nil)
	zzRequireOK(t, rec, "copying a directory")
	zzRequireFile(t, filepath.Join(e.scope, "dst", "file.txt"), "one", "copying a directory")
	zzRequireFile(t, filepath.Join(e.scope, "dst", "sub", "nested.txt"), "two", "copying a directory")
}

// Copying into a destination that already holds an in-scope link to an
// in-scope file keeps working (the link is followed inside the scope).
func TestFunc_CopyThroughInScopeDestinationLink(t *testing.T) {
	e := zzNewEnv(t, users.Permissions{Create: true, Modify: true})
	e.write("src/file.txt", "fresh")
	e.mkdir("dst/real")
	e.write("dst/real/file.txt", "old")
	e.link(filepath.Join(e.scope, "dst", "real", "file.txt"), filepath.Join(e.scope, "dst", "file.txt"))

	rec := e.req(resourcePatchHandler(diskcache.NewNoOp()), http.MethodPatch, "/src?action=copy&destination=/dst&override=true", "", nil)
	zzRequireOK(t, rec, "copy through an in-scope destination link")
	zzRequireFile(t, filepath.Join(e.scope, "dst", "real", "file.txt"), "fresh", "copy through an in-scope destination link")
}

// Ordinary recursive listing keeps working.
func TestFunc_RecursiveListing(t *testing.T) {
	e := zzNewEnv(t, users.Permissions{Create: true, Modify: true})
	e.write("tree/sub/leaf.txt", "x")

	rec := e.req(resourceGetRecursiveHandler, http.MethodGet, "/tree", "", nil)
	zzRequireOK(t, rec, "recursive listing")
	if !strings.Contains(rec.Body.String(), "leaf.txt") {
		t.Fatalf("recursive listing did not include an in-scope entry: status %d body %q",
			rec.Code, strings.TrimSpace(rec.Body.String()))
	}
}

// Recursive listing through an in-scope link keeps working.
func TestFunc_RecursiveListingThroughInScopeLink(t *testing.T) {
	e := zzNewEnv(t, users.Permissions{Create: true, Modify: true})
	e.write("real/sub/leaf.txt", "x")
	e.link(filepath.Join(e.scope, "real"), filepath.Join(e.scope, "link"))

	rec := e.req(resourceGetRecursiveHandler, http.MethodGet, "/link/sub", "", nil)
	zzRequireOK(t, rec, "recursive listing through an in-scope link")
	if !strings.Contains(rec.Body.String(), "leaf.txt") {
		t.Fatalf("recursive listing through an in-scope link did not include an in-scope entry: status %d body %q",
			rec.Code, strings.TrimSpace(rec.Body.String()))
	}
}

// A scoped user can still upload a new file through the resumable endpoint.
func TestFunc_TusCreate(t *testing.T) {
	e := zzNewEnv(t, users.Permissions{Create: true, Modify: true})
	cache := newMemoryUploadCache()
	t.Cleanup(cache.Close)

	rec := e.req(tusPostHandler(cache), http.MethodPost, "/upload.bin", "", map[string]string{"Upload-Length": "5"})
	zzRequireOK(t, rec, "resumable upload creation")
	if info, err := os.Stat(filepath.Join(e.scope, "upload.bin")); err != nil || info.IsDir() {
		t.Fatalf("resumable upload creation: file not created (%v)", err)
	}
}
