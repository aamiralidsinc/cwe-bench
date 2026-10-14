// Package s3test provides helpers shared by the security and functional
// test packages: starting a real `rclone serve s3` process, waiting for it
// to listen, and sending real SigV4-signed S3 HTTP requests to it as a
// downstream S3 client would. Nothing here calls rclone internals - the
// server is driven entirely over HTTP on localhost.
package s3test

import (
	"bytes"
	"context"
	"crypto/sha256"
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
)

// Binaries built into the image / rebuilt from /app by the verifier.
const (
	RcloneBin   = "/usr/local/bin/rclone"
	AuthProxy   = "/usr/local/bin/authproxy"
	Region      = "us-east-1"
	Service     = "s3"
	unsigned    = "UNSIGNED-PAYLOAD"
	shaHdr      = "X-Amz-Content-Sha256"
)

// Access keys the auth proxy knows about and the secrets it maps them to.
// These mirror the mapping baked into the authproxy helper program.
const (
	AliceKey    = "AKIAALICE00000001"
	AliceSecret = "alice-secret-0001"
	BobKey      = "AKIABOB0000000002"
	BobSecret   = "bob-secret-0002"

	// Static-key (non proxy) credentials used by the functional tests.
	StaticKey    = "AKIASTATIC0000001"
	StaticSecret = "static-secret-key-01"

	// An access key ID the proxy does not know.
	UnknownKey = "AKIAHACKER0000009"
)

// PortBase is the first port a server may bind; each package sets its own
// range so leaked processes from one package can't collide with another.
var PortBase int32 = 38100

var portSeq int32

func nextPort() int { return int(PortBase + atomic.AddInt32(&portSeq, 1)) }

// SetupData creates the backing directories and objects the servers serve.
// Safe to call repeatedly.
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
	return nil
}

// Server is a running `rclone serve s3` process.
type Server struct {
	Base   string // e.g. http://127.0.0.1:38101
	cmd    *exec.Cmd
	out    *bytes.Buffer
	exited chan struct{}
}

func startServer(t *testing.T, args []string) *Server {
	t.Helper()
	port := nextPort()
	addr := fmt.Sprintf("127.0.0.1:%d", port)
	full := append([]string{"serve", "s3", "--addr", addr}, args...)
	cmd := exec.Command(RcloneBin, full...)
	var buf bytes.Buffer
	cmd.Stdout = &buf
	cmd.Stderr = &buf
	if err := cmd.Start(); err != nil {
		t.Fatalf("failed to start rclone: %v", err)
	}
	s := &Server{Base: "http://" + addr, cmd: cmd, out: &buf, exited: make(chan struct{})}
	go func() { _ = cmd.Wait(); close(s.exited) }()

	deadline := time.Now().Add(45 * time.Second)
	for time.Now().Before(deadline) {
		select {
		case <-s.exited:
			// Process died before listening (e.g. refused to start).
			t.Fatalf("rclone serve s3 exited before listening on %s\n--- server output ---\n%s",
				addr, buf.String())
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
	t.Fatalf("rclone serve s3 did not start listening on %s\n--- server output ---\n%s",
		addr, buf.String())
	return nil
}

// StartProxyServer starts serve s3 with an auth proxy and no --auth-key.
func StartProxyServer(t *testing.T) *Server {
	return startServer(t, []string{"--auth-proxy", AuthProxy})
}

// StartStaticServer starts serve s3 backed by a local dir with a static
// --auth-key credential (no auth proxy).
func StartStaticServer(t *testing.T) *Server {
	return startServer(t, []string{"/data/static", "--auth-key", StaticKey + "," + StaticSecret})
}

// Stop kills the server process.
func (s *Server) Stop() {
	if s == nil || s.cmd == nil || s.cmd.Process == nil {
		return
	}
	_ = s.cmd.Process.Kill()
	if s.exited != nil {
		<-s.exited // the background goroutine owns Wait()
	}
}

// Output returns the captured server log (for diagnostics).
func (s *Server) Output() string { return s.out.String() }

func sha256hex(b []byte) string {
	h := sha256.Sum256(b)
	return hex.EncodeToString(h[:])
}

// Do sends a SigV4-signed request and returns the status code and body.
// A connection error returns status 0 and the error text, which callers
// treat as a failure (the server must be up and answering).
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
