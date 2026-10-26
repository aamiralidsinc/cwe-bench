package vtesting

// Shared harness for the behavioural suites: it starts the real mail server binary on
// loopback ports and drives it only through its public HTTP surface.

import (
	"bufio"
	"bytes"
	"encoding/base64"
	"encoding/json"
	"fmt"
	"io"
	"net"
	"net/http"
	"net/url"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"sync"
	"syscall"
	"testing"
	"time"

	"github.com/gorilla/websocket"
	"golang.org/x/crypto/bcrypt"
)

const zzSendBody = `{"From":{"Email":"sender@example.com","Name":"Sender"},` +
	`"To":[{"Email":"recipient@example.com","Name":"Recipient"}],` +
	`"Subject":"hidden-suite message","Text":"hidden-suite body"}`

const zzForeign = "http://attacker.example"

// zzOptions configures one daemon instance.
type zzOptions struct {
	APICORS   string
	Webroot   string
	UIAuth    bool
	RelayPort int
}

// zzDaemon is a running instance of the product binary.
type zzDaemon struct {
	t    *testing.T
	cmd  *exec.Cmd
	base string // http://127.0.0.1:<port>
	log  *bytes.Buffer
}

// zzBinary returns the path of the built product binary.
func zzBinary() string {
	if p := os.Getenv("MAILPIT_BIN"); p != "" {
		return p
	}
	return "/workspace/.htests/mailpit"
}

func zzFreePort(t *testing.T) int {
	t.Helper()
	ln, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatalf("free port: %v", err)
	}
	defer func() { _ = ln.Close() }()
	return ln.Addr().(*net.TCPAddr).Port
}

// zzStartDaemon starts one server instance and waits until it answers a health probe.
func zzStartDaemon(t *testing.T, o zzOptions) *zzDaemon {
	t.Helper()
	bin := zzBinary()
	if _, err := os.Stat(bin); err != nil {
		t.Fatalf("product binary %s is missing: %v", bin, err)
	}

	var last string
	for attempt := 0; attempt < 3; attempt++ {
		dir := t.TempDir()
		httpPort, smtpPort := zzFreePort(t), zzFreePort(t)

		args := []string{
			"--listen", fmt.Sprintf("127.0.0.1:%d", httpPort),
			"--smtp", fmt.Sprintf("127.0.0.1:%d", smtpPort),
			"--pop3", "",
			"--database", filepath.Join(dir, "mailpit.db"),
			"--disable-version-check",
			"--quiet",
		}
		if o.Webroot != "" {
			args = append(args, "--webroot", o.Webroot)
		}
		if o.APICORS != "" {
			args = append(args, "--api-cors", o.APICORS)
		}

		env := append(os.Environ(), "MP_DISABLE_VERSION_CHECK=1")
		if o.UIAuth {
			hash, err := bcrypt.GenerateFromPassword([]byte("ui-secret"), bcrypt.DefaultCost)
			if err != nil {
				t.Fatalf("bcrypt: %v", err)
			}
			env = append(env, "MP_UI_AUTH=ui-user:"+string(hash))
		}
		if o.RelayPort != 0 {
			env = append(env, "MP_SMTP_RELAY_HOST=127.0.0.1",
				fmt.Sprintf("MP_SMTP_RELAY_PORT=%d", o.RelayPort))
		}

		log := &bytes.Buffer{}
		cmd := exec.Command(bin, args...)
		cmd.Env = env
		cmd.Dir = dir
		cmd.Stdout = log
		cmd.Stderr = log
		if err := cmd.Start(); err != nil {
			t.Fatalf("start product: %v", err)
		}

		d := &zzDaemon{
			t:    t,
			cmd:  cmd,
			base: fmt.Sprintf("http://127.0.0.1:%d", httpPort),
			log:  log,
		}
		webroot := o.Webroot
		if webroot == "" {
			webroot = "/"
		}
		probe := d.base + webroot + "livez"
		client := &http.Client{Timeout: 2 * time.Second}
		deadline := time.Now().Add(15 * time.Second)
		ready := false
		for time.Now().Before(deadline) {
			resp, err := client.Get(probe)
			if err == nil {
				_ = resp.Body.Close()
				if resp.StatusCode == http.StatusOK {
					ready = true
					break
				}
			}
			if !zzProcessAlive(cmd) {
				break
			}
			time.Sleep(50 * time.Millisecond)
		}
		if ready {
			t.Cleanup(d.stop)
			return d
		}
		_ = cmd.Process.Kill()
		_, _ = cmd.Process.Wait()
		last = log.String()
	}
	t.Fatalf("product did not become ready: %s", last)
	return nil
}

func zzProcessAlive(cmd *exec.Cmd) bool {
	// On Linux, signal 0 reports whether the process still exists.
	return cmd.Process.Signal(syscall.Signal(0)) == nil
}

func (d *zzDaemon) stop() {
	if d.cmd.Process != nil {
		_ = d.cmd.Process.Kill()
		_, _ = d.cmd.Process.Wait()
	}
}

// zzOrigin returns the daemon's own origin.
func (d *zzDaemon) zzOrigin() string { return d.base }

// zzWSURL builds a websocket URL for a request path.
func (d *zzDaemon) zzWSURL(path string) string {
	u, err := url.Parse(d.base)
	if err != nil {
		d.t.Fatalf("parse daemon url: %v", err)
	}
	return "ws://" + u.Host + path
}

// zzDo performs one HTTP request.
func (d *zzDaemon) zzDo(method, path, body, origin string, headers map[string]string) (*http.Response, []byte, error) {
	var rdr io.Reader
	if body != "" {
		rdr = strings.NewReader(body)
	}
	req, err := http.NewRequest(method, d.base+path, rdr)
	if err != nil {
		return nil, nil, err
	}
	if origin != "" {
		req.Header.Set("Origin", origin)
	}
	for k, v := range headers {
		req.Header.Set(k, v)
	}
	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		return nil, nil, err
	}
	defer func() { _ = resp.Body.Close() }()
	data, err := io.ReadAll(resp.Body)
	return resp, data, err
}

// zzDialWS performs a websocket handshake with an optional Origin and basic credentials.
func (d *zzDaemon) zzDialWS(path, origin, user, pass string) (*websocket.Conn, *http.Response, error) {
	h := http.Header{}
	if origin != "" {
		h.Set("Origin", origin)
	}
	if user != "" || pass != "" {
		h.Set("Authorization", "Basic "+base64.StdEncoding.EncodeToString([]byte(user+":"+pass)))
	}
	dialer := websocket.Dialer{HandshakeTimeout: 10 * time.Second}
	return dialer.Dial(d.zzWSURL(path), h)
}

// zzTotal returns the mailbox's total message count.
func (d *zzDaemon) zzTotal() uint64 {
	d.t.Helper()
	resp, data, err := d.zzDo("GET", "/api/v1/messages", "", "", nil)
	if err != nil {
		d.t.Fatalf("message summary: %v", err)
	}
	if resp.StatusCode != http.StatusOK {
		d.t.Fatalf("message summary: status %d", resp.StatusCode)
	}
	var m struct{ Total uint64 }
	if err := json.Unmarshal(bytes.TrimSpace(data), &m); err != nil {
		d.t.Fatalf("message summary is not JSON: %v", err)
	}
	return m.Total
}

// zzRequireBlocked asserts a request was answered with a client error.
func zzRequireBlocked(t *testing.T, resp *http.Response, err error, what string) {
	t.Helper()
	if err != nil {
		t.Fatalf("%s: request failed instead of being refused: %v", what, err)
	}
	if resp.StatusCode < 400 || resp.StatusCode >= 500 {
		t.Fatalf("%s: expected a client error refusal, got status %d", what, resp.StatusCode)
	}
}

// zzRequireOK asserts a request succeeded.
func zzRequireOK(t *testing.T, resp *http.Response, err error, what string) {
	t.Helper()
	if err != nil {
		t.Fatalf("%s: request failed: %v", what, err)
	}
	if resp.StatusCode != http.StatusOK {
		t.Fatalf("%s: expected status 200, got %d", what, resp.StatusCode)
	}
}

// zzSMTP is a minimal SMTP sink that records completed message transfers.
type zzSMTP struct {
	ln    net.Listener
	mu    sync.Mutex
	count int
}

func zzStartSMTP(t *testing.T) *zzSMTP {
	t.Helper()
	ln, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatalf("smtp sink listen: %v", err)
	}
	s := &zzSMTP{ln: ln}
	go s.serve()
	return s
}

func (s *zzSMTP) port() int { return s.ln.Addr().(*net.TCPAddr).Port }

func (s *zzSMTP) received() int {
	s.mu.Lock()
	defer s.mu.Unlock()
	return s.count
}

func (s *zzSMTP) close() { _ = s.ln.Close() }

func (s *zzSMTP) serve() {
	for {
		c, err := s.ln.Accept()
		if err != nil {
			return
		}
		go s.handle(c)
	}
}

func (s *zzSMTP) handle(c net.Conn) {
	defer func() { _ = c.Close() }()
	r := bufio.NewReader(c)
	say := func(line string) { _, _ = fmt.Fprintf(c, "%s\r\n", line) }
	say("220 test-sink")
	inData := false
	for {
		line, err := r.ReadString('\n')
		if err != nil {
			return
		}
		cmd := strings.ToUpper(strings.TrimSpace(line))
		if inData {
			if cmd == "." {
				inData = false
				s.mu.Lock()
				s.count++
				s.mu.Unlock()
				say("250 queued")
			}
			continue
		}
		switch {
		case strings.HasPrefix(cmd, "EHLO"), strings.HasPrefix(cmd, "HELO"):
			say("250-test-sink")
			say("250 OK")
		case strings.HasPrefix(cmd, "DATA"):
			inData = true
			say("354 send data")
		case strings.HasPrefix(cmd, "QUIT"):
			say("221 bye")
			return
		default:
			say("250 OK")
		}
	}
}
