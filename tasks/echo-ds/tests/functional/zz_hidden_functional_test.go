package echo_test

import (
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"

	"github.com/labstack/echo/v5"
	"github.com/labstack/echo/v5/middleware"
)

// hiddenGetHeader is hiddenGet with a request header, used by the authority stub.
func hiddenGetHeader(t *testing.T, e *echo.Echo, target, key, value string) (int, string) {
	t.Helper()
	req := httptest.NewRequest(http.MethodGet, target, nil)
	req.Header.Set(key, value)
	rec := httptest.NewRecorder()
	e.ServeHTTP(rec, req)
	return rec.Code, rec.Body.String()
}

func hiddenWant(t *testing.T, target string, code int, body string, wantCode int, want string) {
	t.Helper()
	if code != wantCode {
		t.Fatalf("GET %s: status %d, want %d (body %q)", target, code, wantCode, body)
	}
	if !strings.Contains(body, want) {
		t.Fatalf("GET %s: body %q does not contain %q", target, body, want)
	}
}

// The reported root static route keeps serving ordinary files, index files and directory
// redirects.
func TestFunc_RootStaticServesLegitimateFiles(t *testing.T) {
	e := echo.New()
	e.StaticFS("/", hiddenFS())
	e.Group("/admin", hiddenAdminOnly).GET("/*", hiddenAdminHandler)

	for target, want := range map[string]string{
		"/index.html":    "PUBLIC-INDEX-7f3a",
		"/docs/a.txt":    "DOC-A-7f3a",
		"/docs/":         "DOCS-INDEX-7f3a",
		"/assets/app.js": "ASSET-JS-7f3a",
	} {
		code, body := hiddenGet(t, e, target)
		hiddenWant(t, target, code, body, http.StatusOK, want)
	}
	code, _ := hiddenGet(t, e, "/docs")
	if code != http.StatusMovedPermanently {
		t.Fatalf("GET /docs: status %d, want a redirect", code)
	}
}

// Static serving installed for the whole application must keep serving files whose names
// contain a literal percent sign, including a name that looks encoded.
func TestFunc_GlobalStaticServesLiteralPercentNames(t *testing.T) {
	e := echo.New()
	e.Use(middleware.StaticWithConfig(middleware.StaticConfig{Filesystem: hiddenFS()}))
	e.Group("/admin", hiddenAdminOnly).GET("/*", hiddenAdminHandler)

	for target, want := range map[string]string{
		"/index.html":      "PUBLIC-INDEX-7f3a",
		"/100%25.txt":      "HUNDRED-PERCENT-7f3a",
		"/foo%2520bar.txt": "LITERAL-PCT20-7f3a",
		"/%252F":           "LITERAL-PCT2F-7f3a",
	} {
		code, body := hiddenGet(t, e, target)
		hiddenWant(t, target, code, body, http.StatusOK, want)
	}
}

// The protected area's access check still decides per request: refusing without authority,
// allowing with it.
func TestFunc_ProtectedRouteStillRequiresAuthority(t *testing.T) {
	rootStatic := echo.New()
	rootStatic.Group("/admin", hiddenAdminOnly).GET("/*", hiddenAdminHandler)
	rootStatic.StaticFS("/", hiddenFS())

	globalStatic := echo.New()
	globalStatic.Use(middleware.StaticWithConfig(middleware.StaticConfig{Filesystem: hiddenFS()}))
	globalStatic.Group("/admin", hiddenAdminOnly).GET("/*", hiddenAdminHandler)

	for name, e := range map[string]*echo.Echo{"root": rootStatic, "global": globalStatic} {
		code, body := hiddenGet(t, e, "/admin/secret.txt")
		if code != http.StatusForbidden {
			t.Fatalf("%s app: GET /admin/secret.txt without authority: status %d, want refusal", name, code)
		}
		if strings.Contains(body, hiddenSecretMarker) {
			t.Fatalf("%s app: GET /admin/secret.txt leaked the protected file", name)
		}
		code, body = hiddenGetHeader(t, e, "/admin/secret.txt", "X-Admin-Token", "granted")
		hiddenWant(t, name+" authorised", code, body, http.StatusOK, "admin-handler")
	}
}

// Static serving mounted on a group keeps working.
func TestFunc_GroupStaticServesLegitimateFiles(t *testing.T) {
	e := echo.New()
	g := e.Group("/files", middleware.StaticWithConfig(middleware.StaticConfig{Filesystem: hiddenFS()}))
	g.GET("/*", func(c *echo.Context) error { return echo.ErrNotFound })

	for target, want := range map[string]string{
		"/files/index.html": "PUBLIC-INDEX-7f3a",
		"/files/docs/a.txt": "DOC-A-7f3a",
		"/files/docs/":      "DOCS-INDEX-7f3a",
		"/files/docs":       "DOCS-INDEX-7f3a",
	} {
		code, body := hiddenGet(t, e, target)
		hiddenWant(t, target, code, body, http.StatusOK, want)
	}
}

// The standard-library-backed file serving keeps working.
func TestFunc_HTTPFileServerServesLegitimateFiles(t *testing.T) {
	e := echo.New()
	e.StaticHTTP("/", http.FS(hiddenFS()))

	for target, want := range map[string]string{
		"/docs/a.txt":  "DOC-A-7f3a",
		"/100%25.txt":  "HUNDRED-PERCENT-7f3a",
		"/assets/app.js": "ASSET-JS-7f3a",
	} {
		code, body := hiddenGet(t, e, target)
		hiddenWant(t, target, code, body, http.StatusOK, want)
	}
}

// The parameter-named file helper keeps decoding ordinary escapes.
func TestFunc_FileParamServesLegitimateFiles(t *testing.T) {
	e := echo.New()
	e.GET("/download/:name", func(c *echo.Context) error { return c.FileParam("name", hiddenFS()) })

	for target, want := range map[string]string{
		"/download/index.html": "PUBLIC-INDEX-7f3a",
		"/download/a%20b.txt":  "SPACE-NAME-7f3a",
	} {
		code, body := hiddenGet(t, e, target)
		hiddenWant(t, target, code, body, http.StatusOK, want)
	}
}

// A router that decodes parameter values keeps handing decoded values to handlers, and static
// files keep being served.
func TestFunc_RouterUnescapedParamsKeepWorking(t *testing.T) {
	e := echo.NewWithConfig(echo.Config{Router: echo.NewRouter(echo.RouterConfig{UnescapePathParamValues: true})})
	e.GET("/echo/:value", func(c *echo.Context) error { return c.String(http.StatusOK, c.Param("value")) })
	e.StaticFS("/", hiddenFS())

	code, body := hiddenGet(t, e, "/echo/a%20b")
	hiddenWant(t, "/echo/a%20b", code, body, http.StatusOK, "a b")

	code, body = hiddenGet(t, e, "/index.html")
	hiddenWant(t, "/index.html", code, body, http.StatusOK, "PUBLIC-INDEX-7f3a")
}

