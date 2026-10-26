package fbhttp

import (
	"net/http"
	"os"
	"path/filepath"
	"strings"
	"testing"

	"github.com/filebrowser/filebrowser/v2/diskcache"
	"github.com/filebrowser/filebrowser/v2/users"
)

// Uploading to a dangling link whose target is outside the scope must not
// create that target.
func TestSec_DanglingLinkUploadPost(t *testing.T) {
	e := zzNewEnv(t, users.Permissions{Create: true, Modify: true})
	target := filepath.Join(e.outside, "created.txt")
	e.link(target, filepath.Join(e.scope, "evil"))

	rec := e.req(resourcePostHandler(diskcache.NewNoOp()), http.MethodPost, "/evil?override=true", "attacker-data", nil)
	zzRequireClientError(t, rec, "upload through a dangling link")
	zzRequireNoFile(t, target, "upload through a dangling link")
}

// The same create-through-a-dangling-link escape on the resumable upload
// endpoint.
func TestSec_DanglingLinkTusCreate(t *testing.T) {
	e := zzNewEnv(t, users.Permissions{Create: true, Modify: true})
	target := filepath.Join(e.outside, "created-tus.txt")
	e.link(target, filepath.Join(e.scope, "evil"))

	cache := newMemoryUploadCache()
	t.Cleanup(cache.Close)
	rec := e.req(tusPostHandler(cache), http.MethodPost, "/evil?override=true", "",
		map[string]string{"Upload-Length": "12"})
	zzRequireClientError(t, rec, "resumable upload through a dangling link")
	zzRequireNoFile(t, target, "resumable upload through a dangling link")
}

// A dangling link target that walks through a symlinked directory and then
// back out: the lexical spelling of the target looks in-scope, where it really
// resolves does not.
func TestSec_DanglingLinkTargetThroughSymlinkedComponent(t *testing.T) {
	e := zzNewEnv(t, users.Permissions{Create: true, Modify: true})
	e.link(e.outside, filepath.Join(e.scope, "m"))
	outsideTarget := filepath.Join(filepath.Dir(e.outside), "dotdot-absolute.txt")
	e.link(e.scope+"/m/../dotdot-absolute.txt", filepath.Join(e.scope, "evil"))

	rec := e.req(resourcePostHandler(diskcache.NewNoOp()), http.MethodPost, "/evil?override=true", "attacker-data", nil)
	zzRequireClientError(t, rec, "upload through a dangling link target with a symlinked component")
	zzRequireNoFile(t, outsideTarget, "upload through a dangling link target with a symlinked component")
}

// The same, with a relative link target.
func TestSec_DanglingLinkRelativeTargetThroughSymlinkedComponent(t *testing.T) {
	e := zzNewEnv(t, users.Permissions{Create: true, Modify: true})
	e.link(e.outside, filepath.Join(e.scope, "m"))
	outsideTarget := filepath.Join(filepath.Dir(e.outside), "dotdot-relative.txt")
	e.link("m/../dotdot-relative.txt", filepath.Join(e.scope, "evil"))

	rec := e.req(resourcePostHandler(diskcache.NewNoOp()), http.MethodPost, "/evil?override=true", "attacker-data", nil)
	zzRequireClientError(t, rec, "upload through a relative dangling link target with a symlinked component")
	zzRequireNoFile(t, outsideTarget, "upload through a relative dangling link target with a symlinked component")
}

// A directory creation request is a write too: it must not create the
// directory outside the scope through an escaping directory link.
func TestSec_MkdirThroughEscapingLink(t *testing.T) {
	e := zzNewEnv(t, users.Permissions{Create: true})
	e.link(e.outside, filepath.Join(e.scope, "linkdir"))

	rec := e.req(resourcePostHandler(diskcache.NewNoOp()), http.MethodPost, "/linkdir/newdir/", "", nil)
	zzRequireClientError(t, rec, "directory creation through an escaping directory link")
	zzRequireNoFile(t, filepath.Join(e.outside, "newdir"), "directory creation through an escaping directory link")
}

// Copying into a destination tree whose child is an escaping link must not
// overwrite the link's target.
func TestSec_CopyOverwritesThroughEscapingDestinationLink(t *testing.T) {
	e := zzNewEnv(t, users.Permissions{Create: true, Modify: true})
	e.write("src/file.txt", "copied-data")
	e.mkdir("dst")
	victim := filepath.Join(e.outside, "victim.txt")
	if err := os.WriteFile(victim, []byte("original-data"), 0o644); err != nil {
		t.Fatal(err)
	}
	e.link(victim, filepath.Join(e.scope, "dst", "file.txt"))

	rec := e.req(resourcePatchHandler(diskcache.NewNoOp()), http.MethodPatch,
		"/src?action=copy&destination=/dst&override=true", "", nil)
	zzRequireClientError(t, rec, "copy through an escaping destination link")
	zzRequireFile(t, victim, "original-data", "copy through an escaping destination link")
}

// A recursive listing must not emit anything that lives outside the scope,
// including when the requested root is reached through an escaping directory
// link.
func TestSec_RecursiveListingThroughEscapingLink(t *testing.T) {
	e := zzNewEnv(t, users.Permissions{Create: true, Modify: true})
	if err := os.MkdirAll(filepath.Join(e.outside, "sub"), 0o755); err != nil {
		t.Fatal(err)
	}
	leaked := "out-of-scope-name.txt"
	if err := os.WriteFile(filepath.Join(e.outside, "sub", leaked), []byte("x"), 0o644); err != nil {
		t.Fatal(err)
	}
	e.link(e.outside, filepath.Join(e.scope, "link"))

	rec := e.req(resourceGetRecursiveHandler, http.MethodGet, "/link/sub", "", nil)
	if strings.Contains(rec.Body.String(), leaked) {
		t.Fatalf("recursive listing disclosed an out-of-scope entry (status %d, body %q)",
			rec.Code, strings.TrimSpace(rec.Body.String()))
	}
	if rec.Code >= 200 && rec.Code < 300 && strings.Contains(rec.Body.String(), "sub") {
		t.Fatalf("recursive listing returned entries for an out-of-scope root (status %d, body %q)",
			rec.Code, strings.TrimSpace(rec.Body.String()))
	}
}
