// Package vtesting holds the hidden behavioural tests for the gogs-ds task.
// They drive a real Gogs server process (built from /app) over HTTP and read
// the mail the server sends through a local SMTP sink. The tests never import
// product packages: expected values and checks are computed here.
package vtesting

import (
	"bufio"
	"bytes"
	"database/sql"
	"encoding/json"
	"fmt"
	"io"
	"mime/quotedprintable"
	"net"
	"net/http"
	"net/http/cookiejar"
	"net/mail"
	"net/url"
	"os"
	"os/exec"
	"os/user"
	"path/filepath"
	"regexp"
	"strconv"
	"strings"
	"sync"
	"sync/atomic"
	"testing"
	"time"

	_ "github.com/glebarez/go-sqlite"
)

type testEnv struct {
	bin     string
	workDir string
	cfgPath string
	dbPath  string
	baseURL string
	smtp    *smtpSink
	cmd     *exec.Cmd
	logPath string
}

var env *testEnv

var userSeq int64

type fixtureUser struct {
	name     string
	email    string
	password string
	admin    bool
}

func TestMain(m *testing.M) {
	bin := os.Getenv("GOGS_BIN")
	if bin == "" {
		fmt.Fprintln(os.Stderr, "GOGS_BIN is not set")
		os.Exit(2)
	}

	dir, err := os.MkdirTemp("", "gogs-verify-")
	if err != nil {
		fmt.Fprintf(os.Stderr, "create work directory: %v\n", err)
		os.Exit(2)
	}

	sink, err := startSMTPSink()
	if err != nil {
		fmt.Fprintf(os.Stderr, "start smtp sink: %v\n", err)
		os.Exit(2)
	}

	httpPort := freePort()
	e := &testEnv{
		bin:     bin,
		workDir: dir,
		cfgPath: filepath.Join(dir, "app.ini"),
		dbPath:  filepath.Join(dir, "gogs.db"),
		baseURL: "http://127.0.0.1:" + strconv.Itoa(httpPort),
		smtp:    sink,
		logPath: filepath.Join(dir, "server.log"),
	}
	e.writeConfig(httpPort, sink.port(),
		getenvInt("GOGS_TEST_ACTIVATE_CODE_LIVES", 180),
		getenvInt("GOGS_TEST_RESET_CODE_LIVES", 180))

	// The web server performs the schema migration on start-up, so it has to be
	// running before fixture accounts are created below.
	if err := e.start(); err != nil {
		fmt.Fprintf(os.Stderr, "start server: %v\n", err)
		if b, rerr := os.ReadFile(e.logPath); rerr == nil {
			fmt.Fprintf(os.Stderr, "%s\n", b)
		}
		os.Exit(2)
	}

	fixtures := []fixtureUser{
		{"siteadmin", "siteadmin@example.test", "admin-pass-1", true},
		{"alice", "alice@example.test", "alice-pass-1", false},
		{"bob", "bob@example.test", "bob-pass-1", false},
		{"carol", "carol@example.test", "carol-pass-1", false},
		{"dave", "dave@example.test", "dave-pass-1", false},
		{"erin", "erin@example.test", "erin-pass-1", false},
		{"frank", "frank@example.test", "frank-pass-1", false},
		{"grace", "grace@example.test", "grace-pass-1", false},
	}
	for _, f := range fixtures {
		args := []string{"admin", "create-user", "--config", e.cfgPath,
			"--name", f.name, "--password", f.password, "--email", f.email}
		if f.admin {
			args = append(args, "--admin")
		}
		if out, err := e.runCLI(args...); err != nil {
			fmt.Fprintf(os.Stderr, "create fixture user %s: %v\n%s\n", f.name, err, out)
			os.Exit(2)
		}
	}
	env = e

	code := m.Run()
	e.stop()
	os.Exit(code)
}

func getenvInt(key string, def int) int {
	if v := os.Getenv(key); v != "" {
		if n, err := strconv.Atoi(v); err == nil {
			return n
		}
	}
	return def
}

func freePort() int {
	ln, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		panic("find free port: " + err.Error())
	}
	defer ln.Close()
	return ln.Addr().(*net.TCPAddr).Port
}

func (e *testEnv) writeConfig(httpPort, smtpPort, activateLives, resetLives int) {
	runUser := "root"
	if u, err := user.Current(); err == nil && u.Username != "" {
		runUser = u.Username
	}
	cfg := fmt.Sprintf(`BRAND_NAME = Gogs
RUN_USER = %s
RUN_MODE = prod

[server]
PROTOCOL = http
HTTP_ADDR = 127.0.0.1
HTTP_PORT = %d
EXTERNAL_URL = http://127.0.0.1:%d/
DISABLE_SSH = true
OFFLINE_MODE = true

[database]
TYPE = sqlite3
PATH = %s

[security]
INSTALL_LOCK = true
SECRET_KEY = verification-secret-key
COOKIE_SECURE = false

[email]
ENABLED = true
HOST = 127.0.0.1:%d
FROM = noreply@example.test
USER =
PASSWORD =
USE_PLAIN_TEXT = true

[auth]
ACTIVATE_CODE_LIVES = %d
RESET_PASSWORD_CODE_LIVES = %d
REQUIRE_EMAIL_CONFIRMATION = true
ENABLE_REGISTRATION_CAPTCHA = false
DISABLE_REGISTRATION = false

[repository]
ROOT = %s
`, runUser, httpPort, httpPort, e.dbPath, smtpPort, activateLives, resetLives,
		filepath.Join(e.workDir, "repos"))
	if err := os.WriteFile(e.cfgPath, []byte(cfg), 0o600); err != nil {
		panic("write config: " + err.Error())
	}
}

func (e *testEnv) runCLI(args ...string) (string, error) {
	cmd := exec.Command(e.bin, args...)
	cmd.Env = append(os.Environ(), "GOGS_WORK_DIR="+e.workDir)
	out, err := cmd.CombinedOutput()
	return string(out), err
}

func (e *testEnv) start() error {
	f, err := os.Create(e.logPath)
	if err != nil {
		return err
	}
	e.cmd = exec.Command(e.bin, "web", "--config", e.cfgPath)
	e.cmd.Env = append(os.Environ(), "GOGS_WORK_DIR="+e.workDir)
	e.cmd.Stdout = f
	e.cmd.Stderr = f
	if err := e.cmd.Start(); err != nil {
		return err
	}

	deadline := time.Now().Add(60 * time.Second)
	for time.Now().Before(deadline) {
		resp, err := http.Get(e.baseURL + "/api/web/user/sign-in")
		if err == nil {
			resp.Body.Close()
			if resp.StatusCode == http.StatusOK {
				return nil
			}
		}
		time.Sleep(100 * time.Millisecond)
	}
	return fmt.Errorf("server did not become ready at %s", e.baseURL)
}

func (e *testEnv) stop() {
	if e.cmd != nil && e.cmd.Process != nil {
		_ = e.cmd.Process.Kill()
		_, _ = e.cmd.Process.Wait()
	}
	if e.smtp != nil {
		e.smtp.close()
	}
}

// --- HTTP helpers -----------------------------------------------------------

func newClient() *http.Client {
	jar, _ := cookiejar.New(nil)
	return &http.Client{Jar: jar, Timeout: 30 * time.Second}
}

func (e *testEnv) do(t *testing.T, c *http.Client, method, path string, body []byte, contentType string) (int, []byte) {
	t.Helper()
	var rdr io.Reader
	if body != nil {
		rdr = bytes.NewReader(body)
	}
	req, err := http.NewRequest(method, e.baseURL+path, rdr)
	if err != nil {
		t.Fatalf("new request %s %s: %v", method, path, err)
	}
	if contentType != "" {
		req.Header.Set("Content-Type", contentType)
	}
	resp, err := c.Do(req)
	if err != nil {
		t.Fatalf("%s %s: %v", method, path, err)
	}
	defer resp.Body.Close()
	out, _ := io.ReadAll(resp.Body)
	return resp.StatusCode, out
}

func (e *testEnv) postJSON(t *testing.T, c *http.Client, path string, v any) (int, []byte) {
	t.Helper()
	body, err := json.Marshal(v)
	if err != nil {
		t.Fatalf("marshal body: %v", err)
	}
	return e.do(t, c, http.MethodPost, path, body, "application/json")
}

func (e *testEnv) postForm(t *testing.T, c *http.Client, path string, v url.Values) (int, []byte) {
	t.Helper()
	return e.do(t, c, http.MethodPost, path, []byte(v.Encode()), "application/x-www-form-urlencoded")
}

func (e *testEnv) get(t *testing.T, c *http.Client, path string) (int, []byte) {
	t.Helper()
	return e.do(t, c, http.MethodGet, path, nil, "")
}

func (e *testEnv) signIn(t *testing.T, c *http.Client, username, password string) int {
	t.Helper()
	status, _ := e.postJSON(t, c, "/api/web/user/sign-in", map[string]string{
		"username": username,
		"password": password,
	})
	return status
}

func (e *testEnv) mustSignIn(t *testing.T, c *http.Client, username, password string) {
	t.Helper()
	if status := e.signIn(t, c, username, password); status != http.StatusOK {
		t.Fatalf("sign-in for %q failed with status %d", username, status)
	}
}

func (e *testEnv) uniqueUser(prefix string) (name, email string) {
	n := atomic.AddInt64(&userSeq, 1)
	name = fmt.Sprintf("%s%d", prefix, n)
	return name, name + "@example.test"
}

func (e *testEnv) signUp(t *testing.T, c *http.Client, name, email, password string) {
	t.Helper()
	status, body := e.postJSON(t, c, "/api/web/user/sign-up", map[string]string{
		"userName": name,
		"email":    email,
		"password": password,
	})
	if status != http.StatusOK {
		t.Fatalf("sign-up for %q returned %d: %s", name, status, body)
	}
}

func (e *testEnv) requestReset(t *testing.T, c *http.Client, email string) {
	t.Helper()
	status, body := e.postJSON(t, c, "/api/web/user/reset-password", map[string]string{"email": email})
	if status != http.StatusOK {
		t.Fatalf("reset request for %q returned %d: %s", email, status, body)
	}
}

func (e *testEnv) resetComplete(t *testing.T, c *http.Client, code, password string) int {
	t.Helper()
	status, _ := e.postJSON(t, c, "/api/web/user/reset-password/complete", map[string]string{
		"code":     code,
		"password": password,
	})
	return status
}

func (e *testEnv) activateComplete(t *testing.T, c *http.Client, code string) int {
	t.Helper()
	status, _ := e.postJSON(t, c, "/api/web/user/activate/complete", map[string]string{"code": code})
	return status
}

func (e *testEnv) probeCode(t *testing.T, c *http.Client, code string) bool {
	t.Helper()
	status, body := e.get(t, c, "/api/web/user/reset-password?code="+url.QueryEscape(code))
	if status != http.StatusOK {
		t.Fatalf("validity probe returned %d: %s", status, body)
	}
	var out struct {
		Valid bool `json:"valid"`
	}
	if err := json.Unmarshal(body, &out); err != nil {
		t.Fatalf("decode validity probe response %q: %v", body, err)
	}
	return out.Valid
}

func (e *testEnv) adminResetLink(t *testing.T, c *http.Client, username string) {
	t.Helper()
	id := e.userID(t, username)
	status, body := e.do(t, c, http.MethodPost,
		fmt.Sprintf("/admin/users/%d/reset_password_link", id), nil, "")
	if status != http.StatusOK {
		t.Fatalf("administrator reset link for %q returned %d: %s", username, status, body)
	}
}

func (e *testEnv) legacyReset(t *testing.T, c *http.Client, code, password string) int {
	t.Helper()
	status, _ := e.postForm(t, c, "/user/reset_password", url.Values{
		"code":     {code},
		"password": {password},
	})
	return status
}

func (e *testEnv) requestAccountDeletion(t *testing.T, email string) {
	t.Helper()
	status, body := e.postForm(t, newClient(), "/user/delete_account", url.Values{"email": {email}})
	if status != http.StatusOK {
		t.Fatalf("account deletion request for %q returned %d: %s", email, status, body)
	}
}

func (e *testEnv) completeAccountDeletion(t *testing.T, code string) int {
	t.Helper()
	status, _ := e.postForm(t, newClient(), "/user/delete_account/complete", url.Values{"code": {code}})
	return status
}

func (e *testEnv) adminAPIResetLink(t *testing.T, c *http.Client, username string) {
	t.Helper()
	status, body := e.do(t, c, http.MethodPost,
		"/api/v1/admin/users/"+url.PathEscape(username)+"/reset-password", nil, "")
	if status != http.StatusOK {
		t.Fatalf("administrator API reset link for %q returned %d: %s", username, status, body)
	}
}

// --- Database helpers (test bookkeeping only) -------------------------------

func (e *testEnv) openDB(t *testing.T) *sql.DB {
	t.Helper()
	db, err := sql.Open("sqlite", "file:"+e.dbPath+"?mode=ro&_pragma=busy_timeout(5000)")
	if err != nil {
		t.Fatalf("open database: %v", err)
	}
	return db
}

func (e *testEnv) userID(t *testing.T, name string) int64 {
	t.Helper()
	db := e.openDB(t)
	defer db.Close()
	var id int64
	if err := db.QueryRow("SELECT id FROM user WHERE lower_name = ?", strings.ToLower(name)).Scan(&id); err != nil {
		t.Fatalf("look up user %q: %v", name, err)
	}
	return id
}

func (e *testEnv) passwdHash(t *testing.T, name string) string {
	t.Helper()
	db := e.openDB(t)
	defer db.Close()
	var hash string
	if err := db.QueryRow("SELECT passwd FROM user WHERE lower_name = ?", strings.ToLower(name)).Scan(&hash); err != nil {
		t.Fatalf("read password hash for %q: %v", name, err)
	}
	return hash
}

func (e *testEnv) userExists(t *testing.T, name string) bool {
	t.Helper()
	db := e.openDB(t)
	defer db.Close()
	var n int
	if err := db.QueryRow("SELECT COUNT(1) FROM user WHERE lower_name = ?", strings.ToLower(name)).Scan(&n); err != nil {
		t.Fatalf("count user %q: %v", name, err)
	}
	return n > 0
}

func (e *testEnv) rands(t *testing.T, name string) string {
	t.Helper()
	db := e.openDB(t)
	defer db.Close()
	var rands string
	if err := db.QueryRow("SELECT rands FROM user WHERE lower_name = ?", strings.ToLower(name)).Scan(&rands); err != nil {
		t.Fatalf("read rands for %q: %v", name, err)
	}
	return rands
}

// --- SMTP sink and mail parsing ---------------------------------------------

type smtpMessage struct {
	rcpts []string
	raw   string
}

type smtpSink struct {
	ln   net.Listener
	mu   sync.Mutex
	msgs []*smtpMessage
}

func startSMTPSink() (*smtpSink, error) {
	ln, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		return nil, err
	}
	s := &smtpSink{ln: ln}
	go s.serve()
	return s, nil
}

func (s *smtpSink) port() int { return s.ln.Addr().(*net.TCPAddr).Port }

func (s *smtpSink) close() { _ = s.ln.Close() }

func (s *smtpSink) serve() {
	for {
		conn, err := s.ln.Accept()
		if err != nil {
			return
		}
		go s.handle(conn)
	}
}

var rcptRE = regexp.MustCompile(`<([^>]+)>`)

func (s *smtpSink) handle(conn net.Conn) {
	defer conn.Close()
	reader := bufio.NewReader(conn)
	writer := bufio.NewWriter(conn)
	write := func(line string) {
		_, _ = writer.WriteString(line + "\r\n")
		_ = writer.Flush()
	}
	write("220 sink ESMTP")

	var data bool
	var buf strings.Builder
	var rcpts []string
	for {
		line, err := reader.ReadString('\n')
		if err != nil {
			return
		}
		line = strings.TrimRight(line, "\r\n")
		if data {
			if line == "." {
				data = false
				s.mu.Lock()
				s.msgs = append(s.msgs, &smtpMessage{rcpts: append([]string(nil), rcpts...), raw: buf.String()})
				s.mu.Unlock()
				rcpts = nil
				buf.Reset()
				write("250 ok")
				continue
			}
			buf.WriteString(line + "\n")
			continue
		}
		upper := strings.ToUpper(line)
		switch {
		case strings.HasPrefix(upper, "EHLO"), strings.HasPrefix(upper, "HELO"):
			write("250-sink")
			write("250 8BITMIME")
		case strings.HasPrefix(upper, "MAIL"):
			write("250 ok")
		case strings.HasPrefix(upper, "RCPT"):
			if m := rcptRE.FindStringSubmatch(line); m != nil {
				rcpts = append(rcpts, strings.ToLower(m[1]))
			}
			write("250 ok")
		case strings.HasPrefix(upper, "DATA"):
			write("354 go")
			data = true
		case strings.HasPrefix(upper, "QUIT"):
			write("221 bye")
			return
		default:
			write("250 ok")
		}
	}
}

func (m *smtpMessage) body() string {
	parsed, err := mail.ReadMessage(strings.NewReader(m.raw))
	if err != nil {
		return m.raw
	}
	raw, _ := io.ReadAll(parsed.Body)
	cte := strings.ToLower(strings.TrimSpace(parsed.Header.Get("Content-Transfer-Encoding")))
	if strings.Contains(cte, "quoted-printable") {
		decoded, err := io.ReadAll(quotedprintable.NewReader(bytes.NewReader(raw)))
		if err == nil {
			raw = decoded
		}
	}
	return string(raw)
}

// mailCode waits for a mail sent to addr whose body contains marker and
// returns the time-limited code in its link.
func (e *testEnv) mailCode(t *testing.T, addr, marker string) string {
	t.Helper()
	deadline := time.Now().Add(30 * time.Second)
	for time.Now().Before(deadline) {
		e.smtp.mu.Lock()
		msgs := append([]*smtpMessage(nil), e.smtp.msgs...)
		e.smtp.mu.Unlock()
		for i := len(msgs) - 1; i >= 0; i-- {
			m := msgs[i]
			match := false
			for _, r := range m.rcpts {
				if strings.EqualFold(r, addr) {
					match = true
					break
				}
			}
			if !match {
				continue
			}
			body := m.body()
			if !strings.Contains(body, marker) {
				continue
			}
			if code := extractCode(body); code != "" {
				return code
			}
		}
		time.Sleep(100 * time.Millisecond)
	}
	t.Fatalf("no %s mail for %q arrived", marker, addr)
	return ""
}

var codeRE = regexp.MustCompile(`code=([0-9a-fA-F]{20,})`)

func extractCode(body string) string {
	if m := codeRE.FindStringSubmatch(body); m != nil {
		return m[1]
	}
	return ""
}

const (
	activateMarker = "user/activate?code="
	resetMarker    = "user/reset-password?code="
	deleteMarker   = "user/delete_account/complete?code="
)
