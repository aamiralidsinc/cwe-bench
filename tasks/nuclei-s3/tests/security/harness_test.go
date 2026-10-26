package security

import (
	"context"
	"crypto/rand"
	"encoding/hex"
	"fmt"
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

// harness_test.go contains the local target server and the scanner runner used
// by the security tests. Everything is local to a loopback address: no test
// reaches the network.

type targetResponse struct {
	Body    string
	Headers map[string]string
}

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

// newTarget starts a local target. Responses are keyed by path.
func newTarget(t *testing.T, responses map[string]targetResponse) (*httptest.Server, *recorder) {
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

		response, ok := responses[r.URL.Path]
		if !ok {
			response = targetResponse{Body: "ok"}
		}
		for key, value := range response.Headers {
			w.Header().Set(key, value)
		}
		w.Header().Set("Content-Type", "text/plain")
		_, _ = io.WriteString(w, response.Body)
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
// against target. The canary environment value is exported for -env-vars runs.
func runNuclei(t *testing.T, templateText, target, canary string, args ...string) (string, int) {
	t.Helper()
	dir := t.TempDir()
	templatePath := filepath.Join(dir, "template.yaml")
	if err := os.WriteFile(templatePath, []byte(templateText), 0o644); err != nil {
		t.Fatalf("could not write template: %v", err)
	}
	home := filepath.Join(dir, "home")
	if err := os.Mkdir(home, 0o755); err != nil {
		t.Fatalf("could not create home: %v", err)
	}

	ctx, cancel := context.WithTimeout(context.Background(), 60*time.Second)
	defer cancel()

	base := []string{
		"-t", templatePath,
		"-u", target,
		"-duc", "-nc", "-silent", "-ni",
		"-timeout", "5",
		"-retries", "0",
	}
	cmd := exec.CommandContext(ctx, nucleiBinary(), append(base, args...)...)
	cmd.Env = []string{
		"PATH=/usr/local/bin:/usr/bin:/bin",
		"HOME=" + home,
		"TMPDIR=" + dir,
		"LANG=C.UTF-8",
		"LC_ALL=C.UTF-8",
		"TZ=UTC",
		"DISABLE_CLOUD_UPLOAD=true",
		"DISCORD_WEBHOOK_URL=",
		"SLACK_WEBHOOK_URL=",
		"NUCLEI_CANARY=" + canary,
	}
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

// requireNotDelivered fails when a request that reached the target carries the
// canary value in any request part. It does not require a particular refusal
// form: a request that is refused never reaches the target at all.
func requireNotDelivered(t *testing.T, rec *recorder, canary string) {
	t.Helper()
	for _, req := range rec.all() {
		candidates := []string{req.URI, req.Body}
		for k, values := range req.Header {
			candidates = append(candidates, k)
			candidates = append(candidates, values...)
		}
		if req.Query != nil {
			for k, values := range req.Query {
				candidates = append(candidates, k)
				candidates = append(candidates, values...)
			}
		}
		for _, candidate := range candidates {
			decoded, _ := url.QueryUnescape(candidate)
			if strings.Contains(candidate, canary) || strings.Contains(decoded, canary) {
				t.Fatalf("canary value reached the target in %q; full request:\n%s", candidate, req.URI)
			}
		}
	}
}

// requireNoFinding fails when the scanner reported a result for templateID.
func requireNoFinding(t *testing.T, output, templateID string) {
	t.Helper()
	if countFindings(output, templateID) != 0 {
		t.Fatalf("scanner reported a finding for %s although the response must not match; output:\n%s", templateID, output)
	}
}

func countFindings(output, templateID string) int {
	needle := fmt.Sprintf(`"template-id":%q`, templateID)
	count := 0
	for _, line := range strings.Split(output, "\n") {
		line = strings.TrimSpace(line)
		if strings.HasPrefix(line, "{") && strings.Contains(line, needle) {
			count++
		}
	}
	return count
}

// requireFirstStep fails unless the scan actually reached the first step.
func requireFirstStep(t *testing.T, rec *recorder, path string) {
	t.Helper()
	for _, req := range rec.all() {
		if req.Path == path {
			return
		}
	}
	t.Fatalf("no request reached %s; the scan did not exercise the first step", path)
}

// requireLiteralWhenSent checks that, if a request to path was delivered with
// the named query parameter, its value is exactly want. A correct fix may also
// refuse to send the request, in which case no such request exists.
func requireLiteralWhenSent(t *testing.T, rec *recorder, path, name, want string) {
	t.Helper()
	for _, req := range rec.all() {
		if req.Path != path || req.Query == nil {
			continue
		}
		values, ok := req.Query[name]
		if !ok {
			continue
		}
		if len(values) != 1 || values[0] != want {
			t.Fatalf("query parameter %q was delivered as %q; want the literal %q (or no request)", name, values, want)
		}
	}
}

// requireSent fails unless some request to path carried a non-empty value for
// the named query parameter.
func requireSent(t *testing.T, rec *recorder, path, name string) string {
	t.Helper()
	for _, req := range rec.all() {
		if req.Path != path || req.Query == nil {
			continue
		}
		values, ok := req.Query[name]
		if !ok || len(values) == 0 {
			continue
		}
		return values[0]
	}
	t.Fatalf("no request to %s carried query parameter %q", path, name)
	return ""
}
