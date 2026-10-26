// Package vtesting holds the hidden behavioural tests for the hugo-ds task.
//
// The tests drive the real command-line entry point, a site build, against a
// throwaway site tree written from the fixture in each test. They import no
// product package: every expected value is computed here, and each test cleans
// up after itself with t.TempDir.
package vtesting

import (
	"os"
	"os/exec"
	"path/filepath"
	"sort"
	"strings"
	"testing"
)

// siteResult is one completed site build.
type siteResult struct {
	exit   int
	output string
	pub    map[string]string // relative slash path -> file content
}

// baseConfig is the site configuration shared by most fixtures: a static site
// with the outputs that would only add noise switched off.
const baseConfig = `baseURL = "https://example.org/"
disableKinds = ["taxonomy", "term", "rss", "sitemap", "robotsTXT", "404"]
`

func writeSite(t *testing.T, files map[string]string) string {
	t.Helper()
	dir := t.TempDir()
	for name, body := range files {
		p := filepath.Join(dir, filepath.FromSlash(name))
		if err := os.MkdirAll(filepath.Dir(p), 0o755); err != nil {
			t.Fatalf("create %s: %v", name, err)
		}
		if err := os.WriteFile(p, []byte(body), 0o644); err != nil {
			t.Fatalf("write %s: %v", name, err)
		}
	}
	return dir
}

func readTree(root string) map[string]string {
	out := map[string]string{}
	filepath.Walk(root, func(p string, info os.FileInfo, err error) error {
		if err != nil || info == nil || info.IsDir() {
			return nil
		}
		b, err := os.ReadFile(p)
		if err != nil {
			return nil
		}
		rel, err := filepath.Rel(root, p)
		if err != nil {
			return nil
		}
		out[filepath.ToSlash(rel)] = string(b)
		return nil
	})
	return out
}

// runHugo builds the fixture site with the binary under test and returns the
// exit status and every file published under the destination directory.
func runHugo(t *testing.T, files map[string]string) *siteResult {
	t.Helper()
	bin := os.Getenv("HUGO_BIN")
	if bin == "" {
		t.Fatal("HUGO_BIN is not set")
	}
	dir := writeSite(t, files)
	pub := filepath.Join(dir, "public")
	cmd := exec.Command(bin,
		"--source", dir,
		"--destination", pub,
		"--cacheDir", filepath.Join(dir, ".cache"),
		"--noBuildLock",
		"--quiet",
	)
	cmd.Dir = dir
	cmd.Env = append(os.Environ(), "TZ=UTC")
	out, err := cmd.CombinedOutput()
	res := &siteResult{output: string(out), pub: map[string]string{}}
	if err != nil {
		exitErr, ok := err.(*exec.ExitError)
		if !ok {
			t.Fatalf("run the site build: %v", err)
		}
		res.exit = exitErr.ExitCode()
	}
	res.pub = readTree(pub)
	return res
}

// paths lists the published files, for failure messages.
func (r *siteResult) paths() []string {
	var ps []string
	for p := range r.pub {
		ps = append(ps, p)
	}
	sort.Strings(ps)
	return ps
}

// publishesMarker reports whether any published file still contains exactly the
// raw body given to the builder.
func (r *siteResult) publishesMarker(marker string) bool {
	for _, body := range r.pub {
		if strings.Contains(body, marker) {
			return true
		}
	}
	return false
}

// assertRefused asserts that a site build containing a body that would be
// published without conversion is refused and that none of the body reaches the
// published site. It accepts any non-zero build result, never one exact status.
func assertRefused(t *testing.T, files map[string]string, marker string) {
	t.Helper()
	res := runHugo(t, files)
	if res.exit == 0 {
		t.Fatalf("the build accepted a raw HTML content body and published the site; published files: %v", res.paths())
	}
	if res.publishesMarker(marker) {
		t.Fatalf("the refused build still published the content body")
	}
}

// assertBuilds asserts that a site build succeeds and returns the result.
func assertBuilds(t *testing.T, files map[string]string) *siteResult {
	t.Helper()
	res := runHugo(t, files)
	if res.exit != 0 {
		t.Fatalf("the site build failed (exit %d): %s", res.exit, strings.TrimSpace(res.output))
	}
	return res
}

// assertPublished asserts that a published file exists and contains want.
func assertPublished(t *testing.T, res *siteResult, path, want string) {
	t.Helper()
	body, ok := res.pub[path]
	if !ok {
		t.Fatalf("expected published file %q; published files: %v", path, res.paths())
	}
	if !strings.Contains(body, want) {
		t.Fatalf("published file %q does not contain %q; got: %q", path, want, body)
	}
}

// rawBody is a harmless marker body: it is inert text, but a browser would
// treat it as markup if it were published without conversion.
func rawBody(marker string) string {
	return "<script>/*" + marker + "*/</script>"
}
