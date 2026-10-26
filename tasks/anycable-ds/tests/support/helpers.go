package vtests

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/http/httptest"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"sync"
	"testing"
	"time"
)

// captured is one request the telemetry sink received.
type captured struct {
	auth string
	body []byte
}

// sink is a local telemetry endpoint that records what the server sends.
type sink struct {
	server *httptest.Server
	mu     sync.Mutex
	reqs   []captured
}

func newSink(t *testing.T) *sink {
	t.Helper()

	s := &sink{}
	s.server = httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		body, _ := io.ReadAll(r.Body)

		s.mu.Lock()
		s.reqs = append(s.reqs, captured{auth: r.Header.Get("Authorization"), body: body})
		s.mu.Unlock()

		w.WriteHeader(http.StatusOK)
		_, _ = w.Write([]byte(`{}`))
	}))
	t.Cleanup(s.server.Close)

	return s
}

func (s *sink) count() int {
	s.mu.Lock()
	defer s.mu.Unlock()

	return len(s.reqs)
}

func (s *sink) snapshot() []captured {
	s.mu.Lock()
	defer s.mu.Unlock()

	out := make([]captured, len(s.reqs))
	copy(out, s.reqs)

	return out
}

// safeBuf is an io.Writer the server process writes to while the test reads it.
type safeBuf struct {
	mu sync.Mutex
	b  bytes.Buffer
}

func (s *safeBuf) Write(p []byte) (int, error) {
	s.mu.Lock()
	defer s.mu.Unlock()

	return s.b.Write(p)
}

func (s *safeBuf) String() string {
	s.mu.Lock()
	defer s.mu.Unlock()

	return s.b.String()
}

var (
	binOnce sync.Once
	binPath string
	binErr  error
)

// binaryPath builds the anycable-go command once per test process (or reuses ANYCABLE_TEST_BIN).
func binaryPath(t *testing.T) string {
	t.Helper()

	binOnce.Do(func() {
		if p := os.Getenv("ANYCABLE_TEST_BIN"); p != "" {
			if _, err := os.Stat(p); err == nil {
				binPath = p
				return
			}
		}

		dir, err := os.MkdirTemp("", "anycable-bin-")
		if err != nil {
			binErr = err
			return
		}

		binPath = filepath.Join(dir, "anycable-go")

		root := moduleRoot()
		if root == "" {
			binErr = fmt.Errorf("cannot find the module root (go.mod) above %s", dir)
			return
		}

		cmd := exec.Command("go", "build", "-o", binPath, "./cmd/anycable-go")
		cmd.Dir = root
		if out, err := cmd.CombinedOutput(); err != nil {
			binErr = fmt.Errorf("building the server failed: %v\n%s", err, out)
		}
	})

	if binErr != nil {
		t.Fatalf("%v", binErr)
	}

	return binPath
}

func moduleRoot() string {
	dir, err := os.Getwd()
	if err != nil {
		return ""
	}

	for {
		if _, err := os.Stat(filepath.Join(dir, "go.mod")); err == nil {
			return dir
		}

		parent := filepath.Dir(dir)
		if parent == dir {
			return ""
		}

		dir = parent
	}
}

type runOpts struct {
	env  []string // extra NAME=VALUE pairs
	args []string // extra server arguments
}

// newServerCommand builds the server process with a clean environment (never the test process's
// ANYCABLE_* settings).
func newServerCommand(bin string, args []string, extraEnv []string) *exec.Cmd {
	cmd := exec.Command(bin, args...)
	cmd.Env = append([]string{
		"PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
		"HOME=/tmp",
	}, extraEnv...)

	return cmd
}

// runServer starts the real server binary against the sink. It waits until the server has
// initialised (the telemetry sender, when it runs, has already been started at that point) and,
// when wantEvent is set, until at least one request was received. It returns only the requests
// received during this run.
func runServer(t *testing.T, s *sink, opts runOpts, wantEvent bool) []captured {
	t.Helper()

	bin := binaryPath(t)
	start := s.count()

	args := append([]string{"--norpc", "--broadcast_adapter=http", "--port=0"}, opts.args...)
	env := append([]string{"ANYCABLE_TELEMETRY_URL=" + s.server.URL}, opts.env...)
	cmd := newServerCommand(bin, args, env)

	buf := &safeBuf{}
	cmd.Stdout = buf
	cmd.Stderr = buf

	if err := cmd.Start(); err != nil {
		t.Fatalf("starting the server failed: %v", err)
	}

	defer func() {
		_ = cmd.Process.Kill()
		_ = cmd.Wait()
	}()

	readyBy := time.Now().Add(30 * time.Second)
	ready := false

	for time.Now().Before(readyBy) {
		if strings.Contains(buf.String(), "Handle WebSocket connections") {
			ready = true
			break
		}

		time.Sleep(20 * time.Millisecond)
	}

	if !ready {
		t.Fatalf("the server did not start (args %v); output:\n%s", opts.args, buf.String())
	}

	if wantEvent {
		evBy := time.Now().Add(15 * time.Second)

		for time.Now().Before(evBy) && s.count() == start {
			time.Sleep(20 * time.Millisecond)
		}
	} else {
		// Give a misbehaving build the same window a correct one gets to stay silent.
		time.Sleep(3 * time.Second)
	}

	return s.snapshot()[start:]
}

// bootEvent parses the first boot event among the captured requests.
func bootEvent(t *testing.T, caps []captured) (map[string]any, []byte) {
	t.Helper()

	if len(caps) == 0 {
		t.Fatalf("expected a telemetry request, none was received")
	}

	for _, c := range caps {
		var event map[string]any
		if err := json.Unmarshal(c.body, &event); err != nil {
			continue
		}

		if event["event"] == "boot" {
			return event, c.body
		}
	}

	t.Fatalf("no boot event among %d captured request(s); first body: %s", len(caps), caps[0].body)

	return nil, nil
}

func jsonEqual(a, b any) bool {
	ab, err := json.Marshal(a)
	if err != nil {
		return false
	}

	bb, err := json.Marshal(b)
	if err != nil {
		return false
	}

	return bytes.Equal(ab, bb)
}

// assertSecretInvariant compares three runs: two with an identical configuration (a, a2) and one
// where only a configured secret differs (b). Every field that was stable across a and a2 must be
// unchanged in b: a stable field that moves with the secret is derived from it.
func assertSecretInvariant(t *testing.T, a, a2, b map[string]any, what string) {
	t.Helper()

	changed := []string{}

	for key, value := range a {
		value2, ok := a2[key]
		if !ok || !jsonEqual(value, value2) {
			// The field is not deterministic between identical runs, so a change cannot be
			// attributed to the secret.
			continue
		}

		valueB, ok := b[key]
		if !ok || !jsonEqual(value, valueB) {
			changed = append(changed, fmt.Sprintf("%s (%v -> %v)", key, value, valueB))
		}
	}

	if len(changed) > 0 {
		t.Fatalf("changing only %s changed telemetry payload fields: %s", what, strings.Join(changed, ", "))
	}
}
