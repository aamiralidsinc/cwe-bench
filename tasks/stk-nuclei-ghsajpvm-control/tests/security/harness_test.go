package security

import (
	"context"
	"crypto/rand"
	"encoding/hex"
	"io"
	"net/http"
	"net/http/httptest"
	"net/url"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"sync"
	"testing"
	"time"
)

// harness_test.go contains the local target server and the runner used by the
// security tests. Everything is local to 127.0.0.1: no test reaches the
// network and no test needs the fix commit.

type recordedRequest struct {
	Method string
	URI    string
	Path   string
	Query  url.Values
	Header http.Header
	Body   string
}

type recorder struct {
	mu   sync.Mutex
	reqs []recordedRequest
}

func (r *recorder) add(req recordedRequest) {
	r.mu.Lock()
	r.reqs = append(r.reqs, req)
	r.mu.Unlock()
}

func (r *recorder) all() []recordedRequest {
	r.mu.Lock()
	defer r.mu.Unlock()
	out := make([]recordedRequest, len(r.reqs))
	copy(out, r.reqs)
	return out
}

// rawRequests renders every received request as method + target + headers + body.
// Substring checks over this text catch a value in any request part.
func (r *recorder) rawRequests() []string {
	var out []string
	for _, req := range r.all() {
		var b strings.Builder
		b.WriteString(req.Method)
		b.WriteString(" ")
		b.WriteString(req.URI)
		b.WriteString("\n")
		for k, values := range req.Header {
			b.WriteString(k)
			b.WriteString(": ")
			b.WriteString(strings.Join(values, ", "))
			b.WriteString("\n")
		}
		b.WriteString("\n")
		b.WriteString(req.Body)
		out = append(out, b.String())
	}
	return out
}

// newTarget starts a local target. probe bodies are keyed by path prefix.
func newTarget(t *testing.T, bodies map[string]string) (*httptest.Server, *recorder) {
	t.Helper()
	rec := &recorder{}
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		body, _ := io.ReadAll(io.LimitReader(r.Body, 1<<20))
		parsed, _ := url.ParseRequestURI(r.URL.RequestURI())
		req := recordedRequest{
			Method: r.Method,
			URI:    r.URL.RequestURI(),
			Path:   r.URL.Path,
			Header: r.Header.Clone(),
			Body:   string(body),
		}
		if parsed != nil {
			req.Query = parsed.Query()
		}
		rec.add(req)

		for prefix, response := range bodies {
			if strings.HasPrefix(r.URL.Path, prefix) {
				w.Header().Set("Content-Type", "text/plain")
				_, _ = io.WriteString(w, response)
				return
			}
		}
		_, _ = io.WriteString(w, "ok")
	}))
	t.Cleanup(server.Close)
	return server, rec
}

func nucleiBinary() string {
	if bin := os.Getenv("NUCLEI_BIN"); bin != "" {
		return bin
	}
	return "/workspace/nuclei"
}

// runNuclei writes the template to a temporary directory and runs the scanner
// against target. The canary environment value is exported for -env-vars tests.
func runNuclei(t *testing.T, templateText, target, canary string, args ...string) (string, int) {
	t.Helper()
	dir := t.TempDir()
	templatePath := filepath.Join(dir, "template.yaml")
	if err := os.WriteFile(templatePath, []byte(templateText), 0o644); err != nil {
		t.Fatalf("could not write template: %v", err)
	}

	ctx, cancel := context.WithTimeout(context.Background(), 120*time.Second)
	defer cancel()

	base := []string{
		"-t", templatePath,
		"-u", target,
		"-duc", "-nc", "-silent", "-ni",
		"-timeout", "10",
		"-retries", "0",
	}
	cmd := exec.CommandContext(ctx, nucleiBinary(), append(base, args...)...)
	cmd.Env = append(os.Environ(),
		"DISABLE_CLOUD_UPLOAD=true",
		"DISABLE_CLOUD_UPLOAD_WRN=true",
		"NUCLEI_CANARY="+canary,
	)
	out, err := cmd.CombinedOutput()
	code := 0
	if err != nil {
		if exitErr, ok := err.(*exec.ExitError); ok {
			code = exitErr.ExitCode()
		} else {
			code = -1
		}
	}
	if ctx.Err() != nil {
		t.Fatalf("scanner did not finish: %v\noutput:\n%s", ctx.Err(), out)
	}
	return string(out), code
}

func randomCanary(t *testing.T) string {
	t.Helper()
	buf := make([]byte, 16)
	if _, err := rand.Read(buf); err != nil {
		t.Fatalf("could not create canary: %v", err)
	}
	return "canary" + hex.EncodeToString(buf)
}

// requireNotDelivered fails when any request that reached the target carries
// the canary value. It does not require a particular refusal form: a request
// that is refused never reaches the target at all.
func requireNotDelivered(t *testing.T, rec *recorder, canary string) {
	t.Helper()
	for _, raw := range rec.rawRequests() {
		if strings.Contains(raw, canary) {
			t.Fatalf("canary value reached the target; request was:\n%s", raw)
		}
	}
}

// requireLiteralWhenSent checks that, if a request to path whose query
// parameter is named name was delivered, its value is exactly want. A correct
// fix may also refuse to send it, in which case no such request exists.
func requireLiteralWhenSent(t *testing.T, rec *recorder, path, name, want string) {
	t.Helper()
	for _, req := range rec.all() {
		if req.Path != path || req.Query == nil {
			continue
		}
		value, ok := req.Query[name]
		if !ok {
			continue
		}
		if len(value) != 1 || value[0] != want {
			t.Fatalf("query parameter %q was delivered as %q; want the literal %q (or no request)", name, value, want)
		}
	}
}

func requireFirstStep(t *testing.T, rec *recorder, path string) {
	t.Helper()
	for _, req := range rec.all() {
		if req.Path == path {
			return
		}
	}
	t.Fatalf("no request reached %s; the scan did not exercise the first step", path)
}
