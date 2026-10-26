package echo_test

import (
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
	"testing/fstest"

	"github.com/labstack/echo/v5"
	"github.com/labstack/echo/v5/middleware"
)

const hiddenSecretMarker = "SECRET-ADMIN-7f3a"

// hiddenFS is the fixture every case resolves against. The admin file is the protected object;
// the other entries are legitimate content that must keep working.
func hiddenFS() fstest.MapFS {
	return fstest.MapFS{
		"index.html":       {Data: []byte("PUBLIC-INDEX-7f3a")},
		"docs/a.txt":       {Data: []byte("DOC-A-7f3a")},
		"docs/index.html":  {Data: []byte("DOCS-INDEX-7f3a")},
		"assets/app.js":    {Data: []byte("ASSET-JS-7f3a")},
		"admin/secret.txt": {Data: []byte(hiddenSecretMarker)},
		"100%.txt":         {Data: []byte("HUNDRED-PERCENT-7f3a")},
		"foo%20bar.txt":    {Data: []byte("LITERAL-PCT20-7f3a")},
		"%2F":              {Data: []byte("LITERAL-PCT2F-7f3a")},
		"a b.txt":          {Data: []byte("SPACE-NAME-7f3a")},
	}
}

// hiddenAdminOnly is the access check for the protected area: it answers per request, so a
// request that carries no authority is refused while an authorised one reaches the handler.
func hiddenAdminOnly(next echo.HandlerFunc) echo.HandlerFunc {
	return func(c *echo.Context) error {
		if c.Request().Header.Get("X-Admin-Token") != "granted" {
			return c.String(http.StatusForbidden, "denied")
		}
		return next(c)
	}
}

func hiddenAdminHandler(c *echo.Context) error { return c.String(http.StatusOK, "admin-handler") }

func hiddenGet(t *testing.T, e *echo.Echo, target string) (int, string) {
	t.Helper()
	req := httptest.NewRequest(http.MethodGet, target, nil)
	rec := httptest.NewRecorder()
	e.ServeHTTP(rec, req)
	return rec.Code, rec.Body.String()
}

// hiddenAssertBlocked requires a client error and no protected content.
func hiddenAssertBlocked(t *testing.T, target string, code int, body string) {
	t.Helper()
	if strings.Contains(body, hiddenSecretMarker) {
		t.Fatalf("GET %s returned the protected file content (status %d)", target, code)
	}
	if code < 400 || code >= 500 {
		t.Fatalf("GET %s was not refused with a client error (status %d, body %q)", target, code, body)
	}
}

// The report's own entry point: the root static route of an application that also protects an
// admin area with route-level middleware.
func TestSec_RootStaticEncodedSeparatorIsNotServed(t *testing.T) {
	e := echo.New()
	e.Group("/admin", hiddenAdminOnly).GET("/*", hiddenAdminHandler)
	e.StaticFS("/", hiddenFS())
	for _, target := range []string{"/admin%2Fsecret.txt", "/admin%2fsecret.txt"} {
		code, body := hiddenGet(t, e, target)
		hiddenAssertBlocked(t, target, code, body)
	}
}

// The same static serving mounted on a group of its own.
func TestSec_GroupStaticMiddlewareEncodedSeparatorIsNotServed(t *testing.T) {
	e := echo.New()
	g := e.Group("/files", middleware.StaticWithConfig(middleware.StaticConfig{Filesystem: hiddenFS()}))
	g.GET("/*", func(c *echo.Context) error { return echo.ErrNotFound })
	for _, target := range []string{"/files/admin%2Fsecret.txt", "/files/admin%2fsecret.txt"} {
		code, body := hiddenGet(t, e, target)
		hiddenAssertBlocked(t, target, code, body)
	}
}

// Static serving installed for the whole application, next to a protected route group.
func TestSec_GlobalStaticMiddlewareEncodedSeparatorIsNotServed(t *testing.T) {
	e := echo.New()
	e.Use(middleware.StaticWithConfig(middleware.StaticConfig{Filesystem: hiddenFS()}))
	e.Group("/admin", hiddenAdminOnly).GET("/*", hiddenAdminHandler)
	for _, target := range []string{"/admin%2Fsecret.txt", "/admin%2fsecret.txt"} {
		code, body := hiddenGet(t, e, target)
		hiddenAssertBlocked(t, target, code, body)
	}
}

// A router that hands already-decoded parameter values to handlers.
func TestSec_RouterUnescapedParamEncodedSeparatorIsNotServed(t *testing.T) {
	e := echo.NewWithConfig(echo.Config{Router: echo.NewRouter(echo.RouterConfig{UnescapePathParamValues: true})})
	e.Group("/admin", hiddenAdminOnly).GET("/*", hiddenAdminHandler)
	e.StaticFS("/", hiddenFS())
	for _, target := range []string{"/admin%2Fsecret.txt", "/admin%2fsecret.txt"} {
		code, body := hiddenGet(t, e, target)
		hiddenAssertBlocked(t, target, code, body)
	}
}

// File serving delegated to the standard library's file server.
func TestSec_HTTPFileServerEncodedSeparatorIsNotServed(t *testing.T) {
	e := echo.New()
	e.Group("/admin", hiddenAdminOnly).GET("/*", hiddenAdminHandler)
	e.StaticHTTP("/", http.FS(hiddenFS()))
	for _, target := range []string{"/admin%2Fsecret.txt", "/admin%2fsecret.txt"} {
		code, body := hiddenGet(t, e, target)
		hiddenAssertBlocked(t, target, code, body)
	}
}

// A handler that serves the file named by a route parameter.
func TestSec_FileParamEncodedSeparatorIsNotServed(t *testing.T) {
	e := echo.New()
	e.Group("/admin", hiddenAdminOnly).GET("/*", hiddenAdminHandler)
	e.GET("/download/:name", func(c *echo.Context) error { return c.FileParam("name", hiddenFS()) })
	for _, target := range []string{"/download/admin%2Fsecret.txt", "/download/admin%2fsecret.txt"} {
		code, body := hiddenGet(t, e, target)
		hiddenAssertBlocked(t, target, code, body)
	}
}
