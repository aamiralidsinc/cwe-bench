// Package s3test provides helpers shared by the security and functional test
// packages. It starts real `rclone serve ...` processes and drives them over
// the wire as a downstream client would: SigV4-signed S3 requests, HTTP Basic
// auth requests, FTP logins and SSH (sftp) logins. Nothing here calls rclone
// internals - every server is exercised purely over its network protocol on
// localhost.
package s3test

import (
	"bytes"
	"context"
	"crypto/sha256"
	"encoding/binary"
	"encoding/hex"
	"fmt"
	"io"
	"net"
	"net/http"
	"os"
	"os/exec"
	"sync/atomic"
	"testing"
	"time"

	"github.com/aws/aws-sdk-go-v2/aws"
	v4 "github.com/aws/aws-sdk-go-v2/aws/signer/v4"
	"github.com/jlaffaye/ftp"
	"golang.org/x/crypto/bcrypt"
	"golang.org/x/crypto/ssh"
)

// Binaries built into the image / rebuilt from /app by the verifier.
const (
	RcloneBin = "/usr/local/bin/rclone"
	AuthProxy = "/usr/local/bin/authproxy"
	Region    = "us-east-1"
	Service   = "s3"
	unsigned  = "UNSIGNED-PAYLOAD"
	shaHdr    = "X-Amz-Content-Sha256"
)

// S3 auth-proxy credentials (the proxy maps these access key IDs to backends
// and secrets). These mirror the mapping baked into the authproxy helper.
const (
	AliceKey    = "AKIAALICE00000001"
	AliceSecret = "alice-secret-0001"
	BobKey      = "AKIABOB0000000002"
	BobSecret   = "bob-secret-0002"

	// Static-key (non proxy) S3 credentials used by the functional tests.
	StaticKey    = "AKIASTATIC0000001"
	StaticSecret = "static-secret-key-01"

	// An access key ID the proxy does not know.
	UnknownKey = "AKIAHACKER0000009"

	// HTTP single-user basic-auth credentials (`serve http --user/--pass`).
	WebUser = "webuser"
	WebPass = "web-pass-basic-01"

	// HTTP htpasswd-file credentials (`serve http --htpasswd`).
	HtUser = "htuser"
	HtPass = "ht-pass-secret-02"

	// FTP single-user credentials (`serve ftp --user/--pass`).
	FTPUser = "ftpuser"
	FTPPass = "ftp-pass-secret-03"

	// SFTP single-user credentials (`serve sftp --user/--pass`).
	SFTPUser = "sftpuser"
	SFTPPass = "sftp-pass-secret-04"

	// The file every non-S3 backend serves, used to confirm access.
	PubFile    = "pubfile.txt"
	PubContent = "PUBLIC SERVE CONTENT\n"

	// Path of the generated htpasswd file.
	HtpasswdFile = "/data/pub-htpasswd"
)

// PortBase is the first port a server may bind; each package sets its own
// range so leaked processes from one package can't collide with another.
var PortBase int32 = 38100

var portSeq int32

func nextPort() int { return int(PortBase + atomic.AddInt32(&portSeq, 1)) }

// SetupData creates the backing directories, objects and htpasswd file the
// servers serve. Safe to call repeatedly.
func SetupData() error {
	dirs := map[string]map[string]string{
		"/data/alice/alicebucket": {
			"readable.txt":  "ALICE CONFIDENTIAL FILE\n",
			"deletable.txt": "ALICE DELETABLE FILE\n",
		},
		"/data/bob/bobbucket": {
			"bobfile.txt": "BOB CONFIDENTIAL FILE\n",
		},
		"/data/static/staticbucket": {
			"file.txt": "STATIC CONTENT\n",
		},
		// Shared read backend for the http/ftp/sftp servers.
		"/data/pub": {
			PubFile: PubContent,
		},
	}
	for dir, files := range dirs {
		if err := os.MkdirAll(dir, 0o755); err != nil {
			return err
		}
		for name, content := range files {
			if err := os.WriteFile(dir+"/"+name, []byte(content), 0o644); err != nil {
				return err
			}
		}
	}
	// Generate the htpasswd file (bcrypt; supported by rclone's basic auth).
	hash, err := bcrypt.GenerateFromPassword([]byte(HtPass), bcrypt.DefaultCost)
	if err != nil {
		return err
	}
	line := fmt.Sprintf("%s:%s\n", HtUser, string(hash))
	return os.WriteFile(HtpasswdFile, []byte(line), 0o644)
}

// Server is a running `rclone serve ...` process.
type Server struct {
	Base   string // http base URL, e.g. http://127.0.0.1:38101 (HTTP servers)
	Addr   string // host:port (all servers)
	cmd    *exec.Cmd
	out    *bytes.Buffer
	exited chan struct{}
}

// startRaw runs `rclone <args...>` (args must contain the bound address so the
// caller controls the subcommand) and waits for addr to accept connections.
func startRaw(t *testing.T, addr string, args []string) *Server {
	t.Helper()
	cmd := exec.Command(RcloneBin, args...)
	var buf bytes.Buffer
	cmd.Stdout = &buf
	cmd.Stderr = &buf
	if err := cmd.Start(); err != nil {
		t.Fatalf("failed to start rclone: %v", err)
	}
	s := &Server{Base: "http://" + addr, Addr: addr, cmd: cmd, out: &buf, exited: make(chan struct{})}
	go func() { _ = cmd.Wait(); close(s.exited) }()

	deadline := time.Now().Add(45 * time.Second)
	for time.Now().Before(deadline) {
		select {
		case <-s.exited:
			t.Fatalf("rclone %v exited before listening on %s\n--- server output ---\n%s",
				args, addr, buf.String())
		default:
		}
		if c, err := net.DialTimeout("tcp", addr, 400*time.Millisecond); err == nil {
			_ = c.Close()
			time.Sleep(1 * time.Second) // warmup so the backend is ready
			return s
		}
		time.Sleep(150 * time.Millisecond)
	}
	s.Stop()
	t.Fatalf("rclone %v did not start listening on %s\n--- server output ---\n%s",
		args, addr, buf.String())
	return nil
}

func addr() string { return fmt.Sprintf("127.0.0.1:%d", nextPort()) }

// --- S3 servers (base task) ------------------------------------------------

// StartProxyServer starts serve s3 with an auth proxy and no --auth-key.
func StartProxyServer(t *testing.T) *Server {
	a := addr()
	return startRaw(t, a, []string{"serve", "s3", "--addr", a, "--auth-proxy", AuthProxy})
}

// StartStaticServer starts serve s3 backed by a local dir with a static key.
func StartStaticServer(t *testing.T) *Server {
	a := addr()
	return startRaw(t, a, []string{"serve", "s3", "/data/static", "--addr", a, "--auth-key", StaticKey + "," + StaticSecret})
}

// --- sibling servers --------------------------------------------------------

// StartHTTPBasic starts `serve http` with a single --user/--pass credential.
func StartHTTPBasic(t *testing.T) *Server {
	a := addr()
	return startRaw(t, a, []string{"serve", "http", "/data/pub", "--addr", a, "--user", WebUser, "--pass", WebPass})
}

// StartHTTPHtpasswd starts `serve http` authenticating against an htpasswd file.
func StartHTTPHtpasswd(t *testing.T) *Server {
	a := addr()
	return startRaw(t, a, []string{"serve", "http", "/data/pub", "--addr", a, "--htpasswd", HtpasswdFile})
}

// StartFTP starts `serve ftp` with a single --user/--pass credential.
func StartFTP(t *testing.T) *Server {
	a := addr()
	return startRaw(t, a, []string{"serve", "ftp", "/data/pub", "--addr", a, "--user", FTPUser, "--pass", FTPPass})
}

// StartSFTP starts `serve sftp` with a single --user/--pass credential.
func StartSFTP(t *testing.T) *Server {
	a := addr()
	return startRaw(t, a, []string{"serve", "sftp", "/data/pub", "--addr", a, "--user", SFTPUser, "--pass", SFTPPass})
}

// Stop kills the server process.
func (s *Server) Stop() {
	if s == nil || s.cmd == nil || s.cmd.Process == nil {
		return
	}
	_ = s.cmd.Process.Kill()
	if s.exited != nil {
		<-s.exited
	}
}

// Output returns the captured server log (for diagnostics).
func (s *Server) Output() string { return s.out.String() }

func sha256hex(b []byte) string {
	h := sha256.Sum256(b)
	return hex.EncodeToString(h[:])
}

// --- S3 SigV4 client --------------------------------------------------------

// Do sends a SigV4-signed request and returns the status code and body.
func Do(base, method, path, key, secret string, body []byte) (int, string) {
	var r io.Reader
	payloadHash := unsigned
	if body != nil {
		r = bytes.NewReader(body)
		payloadHash = sha256hex(body)
	}
	req, err := http.NewRequest(method, base+path, r)
	if err != nil {
		return 0, "newrequest: " + err.Error()
	}
	req.Header.Set(shaHdr, payloadHash)
	creds := aws.Credentials{AccessKeyID: key, SecretAccessKey: secret}
	signer := v4.NewSigner()
	if err := signer.SignHTTP(context.Background(), creds, req, payloadHash, Service, Region, time.Now()); err != nil {
		return 0, "sign: " + err.Error()
	}
	return send(req)
}

// DoNoAuth sends an unsigned request (no Authorization header at all).
func DoNoAuth(base, method, path string) (int, string) {
	req, err := http.NewRequest(method, base+path, nil)
	if err != nil {
		return 0, "newrequest: " + err.Error()
	}
	return send(req)
}

// --- HTTP Basic-auth client -------------------------------------------------

// DoBasic sends an HTTP request with Basic authentication.
func DoBasic(base, method, path, user, pass string) (int, string) {
	req, err := http.NewRequest(method, base+path, nil)
	if err != nil {
		return 0, "newrequest: " + err.Error()
	}
	req.SetBasicAuth(user, pass)
	return send(req)
}

func send(req *http.Request) (int, string) {
	client := &http.Client{Timeout: 30 * time.Second}
	resp, err := client.Do(req)
	if err != nil {
		return 0, "do: " + err.Error()
	}
	defer resp.Body.Close()
	b, _ := io.ReadAll(resp.Body)
	return resp.StatusCode, string(b)
}

// --- FTP client -------------------------------------------------------------

// FTPLogin dials the FTP control connection and attempts to authenticate.
// It returns nil only if the server accepted the credentials.
func FTPLogin(addr, user, pass string) error {
	c, err := ftp.Dial(addr, ftp.DialWithTimeout(15*time.Second))
	if err != nil {
		return fmt.Errorf("dial: %w", err)
	}
	defer func() { _ = c.Quit() }()
	return c.Login(user, pass)
}

// --- SFTP (SSH) client ------------------------------------------------------

// SFTPAuth performs an SSH handshake and password authentication against the
// sftp server. It returns nil only if authentication succeeded.
func SFTPAuth(addr, user, pass string) error {
	cfg := &ssh.ClientConfig{
		User:            user,
		Auth:            []ssh.AuthMethod{ssh.Password(pass)},
		HostKeyCallback: ssh.InsecureIgnoreHostKey(),
		Timeout:         15 * time.Second,
	}
	c, err := ssh.Dial("tcp", addr, cfg)
	if err != nil {
		return err
	}
	_ = c.Close()
	return nil
}

// --- write-path clients (added 2026-10-16) ----------------------------------
// A fix must keep serving correctly authenticated clients for every operation,
// not only reads. These upload, read back and delete a file over the real
// protocol; the tests check the side effect in the backing directory.

// WaitFile polls path until it holds want (present) or no longer exists
// (!present), for up to 10 s. It returns the last observed state on timeout.
func WaitFile(path string, want []byte, present bool) error {
	deadline := time.Now().Add(10 * time.Second)
	for {
		b, err := os.ReadFile(path)
		switch {
		case present && err == nil && bytes.Equal(b, want):
			return nil
		case !present && os.IsNotExist(err):
			return nil
		}
		if time.Now().After(deadline) {
			if present {
				return fmt.Errorf("%s: want %q, got %q (err %v)", path, want, b, err)
			}
			return fmt.Errorf("%s still exists (content %q)", path, b)
		}
		time.Sleep(200 * time.Millisecond)
	}
}

func ftpSession(addr, user, pass string) (*ftp.ServerConn, error) {
	c, err := ftp.Dial(addr, ftp.DialWithTimeout(15*time.Second))
	if err != nil {
		return nil, fmt.Errorf("dial: %w", err)
	}
	if err := c.Login(user, pass); err != nil {
		_ = c.Quit()
		return nil, fmt.Errorf("login: %w", err)
	}
	return c, nil
}

// FTPPut logs in and uploads data as name.
func FTPPut(addr, user, pass, name string, data []byte) error {
	c, err := ftpSession(addr, user, pass)
	if err != nil {
		return err
	}
	defer func() { _ = c.Quit() }()
	return c.Stor(name, bytes.NewReader(data))
}

// FTPGet logs in and downloads name.
func FTPGet(addr, user, pass, name string) ([]byte, error) {
	c, err := ftpSession(addr, user, pass)
	if err != nil {
		return nil, err
	}
	defer func() { _ = c.Quit() }()
	r, err := c.Retr(name)
	if err != nil {
		return nil, err
	}
	defer func() { _ = r.Close() }()
	return io.ReadAll(r)
}

// FTPDelete logs in and deletes name.
func FTPDelete(addr, user, pass, name string) error {
	c, err := ftpSession(addr, user, pass)
	if err != nil {
		return err
	}
	defer func() { _ = c.Quit() }()
	return c.Delete(name)
}

// Minimal SFTP (protocol version 3) client over an SSH "sftp" subsystem.
const (
	fxpInit, fxpVersion, fxpOpen, fxpClose, fxpRead, fxpWrite = 1, 2, 3, 4, 5, 6
	fxpOpendir, fxpReaddir, fxpRemove                         = 11, 12, 13
	fxpStatus, fxpHandle, fxpData, fxpName                    = 101, 102, 103, 104
	fxfRead, fxfWrite, fxfCreat, fxfTrunc                     = 0x01, 0x02, 0x08, 0x10
	fxOK, fxEOF                                               = 0, 1
)

type sftpConn struct {
	c  *ssh.Client
	s  *ssh.Session
	w  io.WriteCloser
	r  io.Reader
	id uint32
}

func u32(v uint32) []byte { return binary.BigEndian.AppendUint32(nil, v) }
func sstr(b []byte) []byte { return append(u32(uint32(len(b))), b...) }

func sftpDial(addr, user, pass string) (*sftpConn, error) {
	cfg := &ssh.ClientConfig{
		User:            user,
		Auth:            []ssh.AuthMethod{ssh.Password(pass)},
		HostKeyCallback: ssh.InsecureIgnoreHostKey(),
		Timeout:         15 * time.Second,
	}
	c, err := ssh.Dial("tcp", addr, cfg)
	if err != nil {
		return nil, err
	}
	s, err := c.NewSession()
	if err != nil {
		_ = c.Close()
		return nil, err
	}
	w, err1 := s.StdinPipe()
	r, err2 := s.StdoutPipe()
	if err1 != nil || err2 != nil {
		_ = c.Close()
		return nil, fmt.Errorf("pipes: %v %v", err1, err2)
	}
	if err := s.RequestSubsystem("sftp"); err != nil {
		_ = c.Close()
		return nil, fmt.Errorf("sftp subsystem: %w", err)
	}
	sc := &sftpConn{c: c, s: s, w: w, r: r}
	if err := sc.send(fxpInit, u32(3)); err != nil {
		sc.Close()
		return nil, err
	}
	typ, _, err := sc.recv()
	if err != nil || typ != fxpVersion {
		sc.Close()
		return nil, fmt.Errorf("sftp init: type %d, err %v", typ, err)
	}
	return sc, nil
}

func (sc *sftpConn) Close() { _ = sc.s.Close(); _ = sc.c.Close() }

func (sc *sftpConn) send(typ byte, payload []byte) error {
	pkt := append(u32(uint32(1+len(payload))), typ)
	_, err := sc.w.Write(append(pkt, payload...))
	return err
}

func (sc *sftpConn) recv() (byte, []byte, error) {
	var hdr [5]byte
	if _, err := io.ReadFull(sc.r, hdr[:]); err != nil {
		return 0, nil, err
	}
	n := binary.BigEndian.Uint32(hdr[:4])
	if n < 1 || n > 1<<24 {
		return 0, nil, fmt.Errorf("bad sftp packet length %d", n)
	}
	body := make([]byte, n-1)
	if _, err := io.ReadFull(sc.r, body); err != nil {
		return 0, nil, err
	}
	return hdr[4], body, nil
}

// call sends one request and returns the reply type and the reply after its id.
func (sc *sftpConn) call(typ byte, args ...[]byte) (byte, []byte, error) {
	sc.id++
	payload := u32(sc.id)
	for _, a := range args {
		payload = append(payload, a...)
	}
	if err := sc.send(typ, payload); err != nil {
		return 0, nil, err
	}
	rt, body, err := sc.recv()
	if err != nil {
		return 0, nil, err
	}
	if len(body) < 4 || binary.BigEndian.Uint32(body[:4]) != sc.id {
		return 0, nil, fmt.Errorf("sftp reply id mismatch")
	}
	return rt, body[4:], nil
}

func sftpStatus(rt byte, body []byte) (uint32, error) {
	if rt != fxpStatus || len(body) < 4 {
		return 0, fmt.Errorf("unexpected sftp reply type %d", rt)
	}
	code := binary.BigEndian.Uint32(body[:4])
	if code != fxOK {
		return code, fmt.Errorf("sftp status %d: %q", code, body[4:])
	}
	return code, nil
}

func sftpString(body []byte) ([]byte, error) {
	if len(body) < 4 {
		return nil, fmt.Errorf("short sftp string")
	}
	n := binary.BigEndian.Uint32(body[:4])
	if int(n) > len(body)-4 {
		return nil, fmt.Errorf("short sftp string")
	}
	return body[4 : 4+n], nil
}

func (sc *sftpConn) open(name string, flags uint32) ([]byte, error) {
	rt, body, err := sc.call(fxpOpen, sstr([]byte(name)), u32(flags), u32(0))
	if err != nil {
		return nil, err
	}
	if rt != fxpHandle {
		_, err := sftpStatus(rt, body)
		return nil, fmt.Errorf("open %s refused: %v", name, err)
	}
	return sftpString(body)
}

func (sc *sftpConn) closeHandle(h []byte) error {
	rt, body, err := sc.call(fxpClose, sstr(h))
	if err != nil {
		return err
	}
	_, err = sftpStatus(rt, body)
	return err
}

// SFTPPut authenticates and uploads data as name.
func SFTPPut(addr, user, pass, name string, data []byte) error {
	sc, err := sftpDial(addr, user, pass)
	if err != nil {
		return err
	}
	defer sc.Close()
	h, err := sc.open(name, fxfWrite|fxfCreat|fxfTrunc)
	if err != nil {
		return err
	}
	rt, body, err := sc.call(fxpWrite, sstr(h), binary.BigEndian.AppendUint64(nil, 0), sstr(data))
	if err != nil {
		return err
	}
	if _, err := sftpStatus(rt, body); err != nil {
		return fmt.Errorf("write: %w", err)
	}
	return sc.closeHandle(h)
}

// SFTPGet authenticates and downloads name.
func SFTPGet(addr, user, pass, name string) ([]byte, error) {
	sc, err := sftpDial(addr, user, pass)
	if err != nil {
		return nil, err
	}
	defer sc.Close()
	h, err := sc.open(name, fxfRead)
	if err != nil {
		return nil, err
	}
	var out []byte
	for {
		rt, body, err := sc.call(fxpRead, sstr(h), binary.BigEndian.AppendUint64(nil, uint64(len(out))), u32(32768))
		if err != nil {
			return nil, err
		}
		if rt == fxpData {
			chunk, err := sftpString(body)
			if err != nil {
				return nil, err
			}
			out = append(out, chunk...)
			continue
		}
		if rt == fxpStatus && len(body) >= 4 && binary.BigEndian.Uint32(body[:4]) == fxEOF {
			break
		}
		_, err = sftpStatus(rt, body)
		return nil, fmt.Errorf("read: %v", err)
	}
	return out, sc.closeHandle(h)
}

// SFTPRemove authenticates and deletes name.
func SFTPRemove(addr, user, pass, name string) error {
	sc, err := sftpDial(addr, user, pass)
	if err != nil {
		return err
	}
	defer sc.Close()
	rt, body, err := sc.call(fxpRemove, sstr([]byte(name)))
	if err != nil {
		return err
	}
	_, err = sftpStatus(rt, body)
	return err
}

// FTPList logs in and returns the names in the served root directory.
func FTPList(addr, user, pass string) ([]string, error) {
	c, err := ftpSession(addr, user, pass)
	if err != nil {
		return nil, err
	}
	defer func() { _ = c.Quit() }()
	entries, err := c.List("/")
	if err != nil {
		return nil, err
	}
	var names []string
	for _, e := range entries {
		names = append(names, e.Name)
	}
	return names, nil
}

// skipAttrs returns the bytes after an SFTP v3 ATTRS structure.
func skipAttrs(b []byte) ([]byte, error) {
	if len(b) < 4 {
		return nil, fmt.Errorf("short attrs")
	}
	flags := binary.BigEndian.Uint32(b[:4])
	n := 4
	if flags&0x1 != 0 {
		n += 8
	}
	if flags&0x2 != 0 {
		n += 8
	}
	if flags&0x4 != 0 {
		n += 4
	}
	if flags&0x8 != 0 {
		n += 8
	}
	if len(b) < n {
		return nil, fmt.Errorf("short attrs")
	}
	b = b[n:]
	if flags&0x80000000 != 0 {
		if len(b) < 4 {
			return nil, fmt.Errorf("short attrs")
		}
		cnt := binary.BigEndian.Uint32(b[:4])
		b = b[4:]
		for i := uint32(0); i < 2*cnt; i++ {
			str, err := sftpString(b)
			if err != nil {
				return nil, err
			}
			b = b[4+len(str):]
		}
	}
	return b, nil
}

// SFTPList authenticates and returns the names in directory dir.
func SFTPList(addr, user, pass, dir string) ([]string, error) {
	sc, err := sftpDial(addr, user, pass)
	if err != nil {
		return nil, err
	}
	defer sc.Close()
	rt, body, err := sc.call(fxpOpendir, sstr([]byte(dir)))
	if err != nil {
		return nil, err
	}
	if rt != fxpHandle {
		_, err := sftpStatus(rt, body)
		return nil, fmt.Errorf("opendir %s refused: %v", dir, err)
	}
	h, err := sftpString(body)
	if err != nil {
		return nil, err
	}
	var names []string
	for {
		rt, body, err := sc.call(fxpReaddir, sstr(h))
		if err != nil {
			return nil, err
		}
		if rt == fxpStatus && len(body) >= 4 && binary.BigEndian.Uint32(body[:4]) == fxEOF {
			break
		}
		if rt != fxpName || len(body) < 4 {
			_, err = sftpStatus(rt, body)
			return nil, fmt.Errorf("readdir: %v", err)
		}
		cnt := binary.BigEndian.Uint32(body[:4])
		b := body[4:]
		for i := uint32(0); i < cnt; i++ {
			name, err := sftpString(b)
			if err != nil {
				return nil, err
			}
			b = b[4+len(name):]
			long, err := sftpString(b)
			if err != nil {
				return nil, err
			}
			b = b[4+len(long):]
			if b, err = skipAttrs(b); err != nil {
				return nil, err
			}
			names = append(names, string(name))
		}
	}
	return names, sc.closeHandle(h)
}
