package fbhttp

import (
	"net/http"
	"path/filepath"
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
